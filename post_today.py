"""
Unofficial DC - Evergreen Drumbeat Runner

Find today's scheduled row in Notion, publish it to Instagram and Facebook,
mark the row with the result, archive a plain-text copy into posted/, and
optionally ping Telegram.
"""

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from publishing_state import DailyState
from evergreen_queue import ensure_queue

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
FB_PAGE_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip()
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


def safe_error(exc):
    message = str(exc)
    for secret in (META_TOKEN, FB_PAGE_TOKEN, NOTION_TOKEN, TG_TOKEN):
        if secret:
            message = message.replace(secret, "[redacted]")
    return re.sub(r"(?i)(access_token=|bearer\s+)[^&\s]+", r"\1[redacted]", message)[:600]


def rich_text(prop):
    return "".join(item.get("plain_text", "") for item in prop.get("rich_text", []))


def title_text(prop):
    return "".join(item.get("plain_text", "") for item in prop.get("title", []))


def find_todays_row(today):
    payload = {
        "filter": {"property": "Date", "date": {"equals": today.isoformat()}},
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
    if len(results) > 1:
        raise RuntimeError("Multiple calendar rows for today; resolve them before publishing.")
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
    existing_urls = list(dict.fromkeys(
        ([existing_post_url] if existing_post_url else []) +
        re.findall(r"https://(?:www\.)?(?:instagram\.com|facebook\.com)/[^\s,;]+",
                   rich_text(props.get("Log", {})))
    ))

    return {
        "id": page["id"],
        "title": title_text(props.get("Name", {})),
        "image_url": image_url,
        "caption": full_caption,
        "platforms": platforms or ["Instagram", "Facebook"],
        "existing_post_url": existing_post_url,
        "existing_post_urls": existing_urls,
        "status": (props.get("Status", {}).get("select") or {}).get("name"),
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
    return meta_post_with_token(path, data, META_TOKEN)


def meta_post_with_token(path, data, token):
    response = requests.post(f"{GRAPH}/{path}", data={**data, "access_token": token}, timeout=60)
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
            params={"fields": "status_code"},
            headers={"Authorization": f"Bearer {META_TOKEN}"},
            timeout=30,
        ).json()
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") == "ERROR":
            raise RuntimeError(f"IG container error: {status}")
        time.sleep(3)

    published = meta_post(f"{IG_USER_ID}/media_publish", {"creation_id": creation_id})
    media_id = published["id"]
    response = requests.get(
        f"{GRAPH}/{media_id}",
        params={"fields": "permalink"},
        headers={"Authorization": f"Bearer {META_TOKEN}"},
        timeout=30,
    )
    response.raise_for_status()
    info = response.json()
    if not info.get("permalink"):
        raise RuntimeError(f"Instagram published media {media_id}, but permalink verification failed; review before retry.")
    return info["permalink"]


def facebook_page_token():
    # The saved Meta token can be a system-user token, not a Page token.
    token = FB_PAGE_TOKEN or META_TOKEN
    response = requests.get(f"{GRAPH}/me", params={"fields": "id"},
                            headers={"Authorization": f"Bearer {token}"}, timeout=30)
    response.raise_for_status()
    if response.json().get("id") == FB_PAGE_ID:
        return token
    response = requests.get(f"{GRAPH}/me/accounts", params={"fields": "id,access_token", "limit": 100},
                            headers={"Authorization": f"Bearer {token}"}, timeout=30)
    response.raise_for_status()
    for page in response.json().get("data", []):
        if page["id"] == FB_PAGE_ID and page.get("access_token"):
            return page["access_token"]
    raise RuntimeError("Cannot obtain a Facebook Page token for the configured Page.")


def publish_facebook(image_url, caption):
    if not FB_PAGE_ID:
        raise RuntimeError("Missing FB_PAGE_ID")
    token = facebook_page_token()
    if not token:
        raise RuntimeError("Missing FB_PAGE_ACCESS_TOKEN or META_ACCESS_TOKEN")
    result = meta_post_with_token(
        f"{FB_PAGE_ID}/photos",
        {"url": image_url, "caption": caption, "published": "true"},
        token,
    )
    post_id = result.get("post_id") or result.get("id")
    response = requests.get(f"{GRAPH}/{post_id}", params={"fields": "id,permalink_url"},
                            headers={"Authorization": f"Bearer {token}"}, timeout=30)
    response.raise_for_status()
    if not response.json().get("id"):
        raise RuntimeError(f"Facebook returned {post_id}, but read-back failed; review before retry.")
    return response.json().get("permalink_url") or f"https://www.facebook.com/{post_id}"


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
        response = requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": message, "disable_web_page_preview": True},
            timeout=20,
        )
        response.raise_for_status()
    except Exception as exc:
        log(f"telegram failed: {safe_error(exc)}")


def finish(outcome, note, urls=None, code=0, state=None):
    urls = urls or []
    log(f"{outcome}: {note}" + (" | " + ", ".join(urls) if urls else ""))
    day = dt.datetime.now(TZ).date().isoformat()
    result = {"date": day, "outcome": outcome, "note": note, "urls": urls,
              "checked_at": dt.datetime.now(TZ).isoformat()}
    Path("runs").mkdir(exist_ok=True)
    Path(f"runs/{day}.json").write_text(json.dumps(result, indent=2) + "\n")
    summary = f"## Evergreen: {outcome}\n\n{note}\n\n" + "\n".join(f"- {u}" for u in urls) + "\n"
    Path(f"runs/{day}.md").write_text(summary)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as handle:
            handle.write(summary)
    if not DRY_RUN:
        state = state or DailyState(day)
        try:
            changed = state.report(outcome, note, urls)
        except Exception:
            log("Could not update the shared run summary; check the saved platform receipts and local report.")
            changed = False
        if changed and outcome != "ALREADY_POSTED":
            telegram(f"UDC evergreen {outcome} - {day}\n{note}\n" + "\n".join(urls))
            if sys.platform == "darwin":
                try:
                    subprocess.run(["/usr/bin/osascript", "-e",
                        'display notification ' + json.dumps(note[:200]) +
                        ' with title ' + json.dumps("UDC evergreen: " + outcome)],
                        capture_output=True, timeout=10, check=False)
                except (OSError, subprocess.TimeoutExpired):
                    log("Desktop notification unavailable; publishing receipts are still saved.")
    return code


def main():
    today = dt.datetime.now(TZ).date()
    log(f"Drumbeat run for {today} (dry_run={DRY_RUN})")
    if ALLOW_PARTIAL:
        return finish("NEEDS_REVIEW", "Automatic partial retries are disabled to prevent duplicate posts.", code=1)
    if PLATFORMS_OVERRIDE:
        log(f"Platform override active: {PLATFORMS_OVERRIDE}")

    if not DRY_RUN:
        created = ensure_queue(today, NOTION_DB, NOTION_HEADERS)
        log(f"Rolling calendar checked; {created} entries added.")

    page = find_todays_row(today)
    if not page:
        return finish("NOTHING_SCHEDULED", "No calendar entry for today. Nothing was published.", code=2)

    row = parse_row(page)
    log(f"Found: {row['title']!r} -> {row['platforms']}")
    if row["status"] == "Posted":
        urls = row.get("existing_post_urls") or ([row["existing_post_url"]] if row["existing_post_url"] else [])
        return finish("ALREADY_POSTED" if urls else "NEEDS_REVIEW",
                      "Calendar says Posted; no new publish attempted.", urls, code=0 if urls else 1)
    if row["status"] != "Scheduled":
        return finish("NEEDS_REVIEW", f"Calendar status is {row['status']}; no automatic retry.", code=1)
    if not row["image_url"] or not row["caption"]:
        return finish("FAILED", "Image or caption is missing. Nothing was published.", code=1)
    if not row["platforms"] or set(row["platforms"]) - {"Instagram", "Facebook"}:
        return finish("FAILED", "Unsupported platform in calendar. Nothing was published.", code=1)
    if DRY_RUN:
        return finish("DRY_RUN", f"Validated {row['title']}; publishing and calendar writes disabled.")

    state = DailyState(today)
    if not state.acquire(row):
        if state.data.get("page_id") != row["id"]:
            return finish("NEEDS_REVIEW", "Today's claim belongs to another calendar row. No new publish attempted.",
                          list(state.data.get("receipts", {}).values()), code=1, state=state)
        if state.data.get("outcome") == "posted":
            urls = list(state.data["receipts"].values())
            update_row(row["id"], "Posted", "Recovered shared publishing receipts: " + ", ".join(urls), urls)
            archive(today, row, urls, "Posted")
            return finish("ALREADY_POSTED", "Shared ledger confirms publication; no new posts.", urls, state=state)
        return finish("NEEDS_REVIEW", "A daily claim already exists. Publishing is blocked to avoid duplicates.",
                      list(state.data.get("receipts", {}).values()), code=1, state=state)

    urls = []
    errors = []
    if "Instagram" in row["platforms"]:
        try:
            urls.append(publish_instagram(row["image_url"], row["caption"]))
            state.checkpoint(platform="Instagram", url=urls[-1])
            log(f"Instagram OK: {urls[-1]}")
        except Exception as exc:
            errors.append(f"Instagram: {safe_error(exc)}")
            log(errors[-1])
    # Stop after an uncertain result; the claim stays held for reconciliation.
    if "Facebook" in row["platforms"] and not errors:
        try:
            urls.append(publish_facebook(row["image_url"], row["caption"]))
            state.checkpoint(platform="Facebook", url=urls[-1])
            log(f"Facebook OK: {urls[-1]}")
        except Exception as exc:
            errors.append(f"Facebook: {safe_error(exc)}")
            log(errors[-1])

    all_urls = []
    if row.get("existing_post_url"):
        all_urls.append(row["existing_post_url"])
    for url in urls:
        if url not in all_urls:
            all_urls.append(url)

    status = "Posted" if len(urls) == len(row["platforms"]) and not errors else "Posted (partial)" if all_urls else "Failed"
    note = "; ".join(errors) if errors else "Published " + ", ".join(urls)
    if all_urls:
        note = f"{note}; All known URLs: {', '.join(all_urls)}"
    state.checkpoint(outcome="posted" if status == "Posted" else "needs_review", note=note)
    archive(today, row, all_urls, status, errors)
    try:
        update_row(row["id"], status, note, all_urls)
    except Exception:
        return finish("NEEDS_REVIEW", "Platform receipts saved, but Notion update failed. Do not republish.",
                      all_urls, code=1, state=state)
    return finish("PUBLISHED" if status == "Posted" else "NEEDS_REVIEW", note, all_urls,
                  code=0 if status == "Posted" else 1, state=state)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        # Avoid printing HTTP exception URLs, which can contain access tokens.
        log(f"FAILED: {type(exc).__name__}. Check service access and the shared claim before retrying.")
        try:
            finish("FAILED", f"{type(exc).__name__}; inspect shared claims before retrying.", code=1)
        except Exception:
            log("Could not save shared failure report.")
        sys.exit(1)
