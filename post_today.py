"""
Unofficial DC - Evergreen Drumbeat Runner

Find today's scheduled row in Notion, publish it to Instagram and Facebook,
mark the row with the result, archive a plain-text copy into posted/, and
optionally ping Telegram.
"""

import datetime as dt
import json
import os
import sys
import time
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("America/New_York")
GRAPH = "https://graph.facebook.com/v21.0"
NOTION_VERSION = "2022-06-28"


def required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


NOTION_TOKEN = required_env("NOTION_TOKEN")
NOTION_DB = required_env("NOTION_DATABASE_ID")
META_TOKEN = os.environ.get("META_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.environ.get("IG_USER_ID", "").strip()
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
TG_CHAT = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
DRY_RUN = os.environ.get("DRY_RUN", "0") == "1"
ALLOW_PARTIAL = os.environ.get("ALLOW_PARTIAL", "0") == "1"
PLATFORMS_OVERRIDE = [
    platform.strip()
    for platform in os.environ.get("PLATFORMS_OVERRIDE", "").split(",")
    if platform.strip()
]

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


def log(message):
    print(f"[{dt.datetime.now(TZ).strftime('%Y-%m-%d %H:%M')}] {message}", flush=True)


def rich_text(prop):
    return "".join(item.get("plain_text", "") for item in prop.get("rich_text", []))


def title_text(prop):
    return "".join(item.get("plain_text", "") for item in prop.get("title", []))


def find_todays_row(today):
    status_filter = {"property": "Status", "select": {"equals": "Scheduled"}}
    if ALLOW_PARTIAL:
        status_filter = {
            "or": [
                {"property": "Status", "select": {"equals": "Scheduled"}},
                {"property": "Status", "select": {"equals": "Posted (partial)"}},
            ]
        }
    payload = {
        "filter": {
            "and": [
                {"property": "Date", "date": {"equals": today.isoformat()}},
                status_filter,
            ]
        },
        "page_size": 5,
    }
    response = requests.post(
        f"https://api.notion.com/v1/databases/{NOTION_DB}/query",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    results = response.json()["results"]
    return results[0] if results else None


def parse_row(page):
    props = page["properties"]
    files = props.get("Image", {}).get("files", [])
    image_url = None
    if files:
        first = files[0]
        image_url = first["file"]["url"] if first["type"] == "file" else first["external"]["url"]

    caption = rich_text(props.get("Caption", {})).strip()
    hashtags = rich_text(props.get("Hashtags", {})).strip()
    platforms = [item["name"] for item in props.get("Platforms", {}).get("multi_select", [])]
    if PLATFORMS_OVERRIDE:
        platforms = PLATFORMS_OVERRIDE
    full_caption = caption + (f"\n\n{hashtags}" if hashtags else "")
    existing_post_url = props.get("Post URL", {}).get("url")

    return {
        "id": page["id"],
        "title": title_text(props.get("Name", {})),
        "image_url": image_url,
        "caption": full_caption,
        "platforms": platforms or ["Instagram", "Facebook"],
        "existing_post_url": existing_post_url,
    }


def update_row(page_id, status, note="", post_urls=None):
    props = {
        "Status": {"select": {"name": status}},
        "Log": {"rich_text": [{"text": {"content": (note or "")[:1900]}}]},
    }
    if post_urls:
        props["Post URL"] = {"url": post_urls[0]}
    response = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=NOTION_HEADERS,
        json={"properties": props},
        timeout=30,
    )
    response.raise_for_status()


def meta_post(path, data):
    if not META_TOKEN:
        raise RuntimeError("Missing META_ACCESS_TOKEN")
    response = requests.post(f"{GRAPH}/{path}", data={**data, "access_token": META_TOKEN}, timeout=60)
    if response.status_code >= 400:
        raise RuntimeError(f"Meta {path} -> {response.status_code}: {response.text[:500]}")
    return response.json()


def publish_instagram(image_url, caption):
    if not IG_USER_ID:
        raise RuntimeError("Missing IG_USER_ID")

    container = meta_post(f"{IG_USER_ID}/media", {"image_url": image_url, "caption": caption})
    creation_id = container["id"]

    for _ in range(10):
        status = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": META_TOKEN},
            timeout=30,
        ).json()
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError(f"IG container error: {status}")
        time.sleep(3)

    published = meta_post(f"{IG_USER_ID}/media_publish", {"creation_id": creation_id})
    media_id = published["id"]
    info = requests.get(
        f"{GRAPH}/{media_id}",
        params={"fields": "permalink", "access_token": META_TOKEN},
        timeout=30,
    ).json()
    return info.get("permalink", f"instagram media {media_id}")


def publish_facebook(image_url, caption):
    if not FB_PAGE_ID:
        raise RuntimeError("Missing FB_PAGE_ID")
    result = meta_post(f"{FB_PAGE_ID}/photos", {"url": image_url, "caption": caption, "published": "true"})
    post_id = result.get("post_id") or result.get("id")
    return f"https://www.facebook.com/{post_id}"


def archive(today, row, urls, status, errors=None):
    errors = errors or []
    os.makedirs("posted", exist_ok=True)
    path = f"posted/{today.isoformat()}.md"
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f"# {today.isoformat()} - {row['title']}\n\n")
        handle.write(f"status: {status}\n")
        handle.write(f"platforms: {', '.join(row['platforms'])}\n")
        for url in urls:
            handle.write(f"url: {url}\n")
        for error in errors:
            handle.write(f"error: {error}\n")
        handle.write(f"\n---\n\n{row['caption']}\n")
    return path


def telegram(message):
    if not (TG_TOKEN and TG_CHAT):
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": message, "disable_web_page_preview": True},
            timeout=20,
        )
    except Exception as exc:
        log(f"telegram failed: {exc}")


def main():
    today = dt.datetime.now(TZ).date()
    log(f"Drumbeat run for {today} (dry_run={DRY_RUN})")
    if ALLOW_PARTIAL:
        log("Including Posted (partial) rows in today's lookup.")
    if PLATFORMS_OVERRIDE:
        log(f"Platform override active: {PLATFORMS_OVERRIDE}")

    page = find_todays_row(today)
    if not page:
        log("No Scheduled row for today. Nothing to do.")
        telegram(f"UDC drumbeat: nothing scheduled for {today}.")
        return 0

    row = parse_row(page)
    log(f"Found: {row['title']!r} -> {row['platforms']}")

    if not row["image_url"]:
        update_row(row["id"], "Failed", "No image attached in the Image field.")
        telegram(f"UDC drumbeat FAILED {today}: no image on '{row['title']}'.")
        return 1
    if not row["caption"]:
        update_row(row["id"], "Failed", "Caption is empty.")
        telegram(f"UDC drumbeat FAILED {today}: empty caption on '{row['title']}'.")
        return 1

    if DRY_RUN:
        log(f"DRY RUN image: {row['image_url']}")
        log(f"DRY RUN caption:\n{row['caption']}")
        return 0

    urls = []
    errors = []
    if "Instagram" in row["platforms"]:
        try:
            urls.append(publish_instagram(row["image_url"], row["caption"]))
            log(f"Instagram OK: {urls[-1]}")
        except Exception as exc:
            errors.append(f"Instagram: {exc}")
            log(errors[-1])
    if "Facebook" in row["platforms"]:
        try:
            urls.append(publish_facebook(row["image_url"], row["caption"]))
            log(f"Facebook OK: {urls[-1]}")
        except Exception as exc:
            errors.append(f"Facebook: {exc}")
            log(errors[-1])

    all_urls = []
    if row.get("existing_post_url"):
        all_urls.append(row["existing_post_url"])
    for url in urls:
        if url not in all_urls:
            all_urls.append(url)

    status = "Posted" if urls and not errors else "Posted (partial)" if all_urls else "Failed"
    note = "; ".join(errors) if errors else "Published " + ", ".join(urls)
    if all_urls:
        note = f"{note}; All known URLs: {', '.join(all_urls)}"
    update_row(row["id"], status, note, all_urls)
    archive(today, row, all_urls, status, errors)

    telegram(
        f"UDC drumbeat {status} - {today}\n{row['title']}\n"
        + "\n".join(urls)
        + ("\n\nErrors: " + "; ".join(errors) if errors else "")
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        log(f"FATAL: {exc}")
        telegram(f"UDC drumbeat FATAL: {exc}")
        sys.exit(1)
