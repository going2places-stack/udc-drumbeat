#!/usr/bin/env python3
"""
Unofficial DC — Evergreen Drumbeat Runner.

Finds today's row in the Notion "UDC Evergreen Calendar", posts it to
Instagram + the Unofficial DC Facebook Page, marks the row Posted, saves a
copy into posted/, and pings Telegram. See README.md for setup.
"""
import os
import sys
import json
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

NOTION_VERSION = "2022-06-28"
GRAPH_VERSION = "v21.0"
TIMEZONE = "America/New_York"

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")
META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
IG_USER_ID = os.environ.get("IG_USER_ID", "")
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json",
}


def log(msg):
    print(f"[udc-drumbeat] {msg}", flush=True)


def notion_find_todays_row(today):
    """Return the first Scheduled row whose Date matches today, or None."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {
        "filter": {
            "and": [
                {"property": "Date", "date": {"equals": today}},
                {"property": "Status", "select": {"equals": "Scheduled"}},
            ]
        }
    }
    resp = requests.post(url, headers=NOTION_HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None


def _rich_text_to_str(rich_text):
    return "".join(part.get("plain_text", "") for part in rich_text or [])


def parse_row(page):
    props = page["properties"]

    name = ""
    for part in props.get("Name", {}).get("title", []):
        name += part.get("plain_text", "")

    caption = _rich_text_to_str(props.get("Caption", {}).get("rich_text"))
    hashtags = _rich_text_to_str(props.get("Hashtags", {}).get("rich_text"))

    files = props.get("Image", {}).get("files", [])
    image_url = None
    if files:
        f = files[0]
        if f.get("type") == "external":
            image_url = f["external"]["url"]
        elif f.get("type") == "file":
            image_url = f["file"]["url"]

    platforms = [opt["name"] for opt in props.get("Platforms", {}).get("multi_select", [])]
    if not platforms:
        platforms = ["Instagram", "Facebook"]

    return {
        "page_id": page["id"],
        "name": name,
        "caption": caption,
        "hashtags": hashtags,
        "image_url": image_url,
        "platforms": platforms,
    }


def full_caption(row):
    parts = [row["caption"].strip()]
    if row["hashtags"].strip():
        parts.append(row["hashtags"].strip())
    return "\n\n".join(p for p in parts if p)


def post_instagram(row, caption):
    create_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_USER_ID}/media"
    resp = requests.post(
        create_url,
        data={
            "image_url": row["image_url"],
            "caption": caption,
            "access_token": META_ACCESS_TOKEN,
        },
        timeout=60,
    )
    resp.raise_for_status()
    creation_id = resp.json()["id"]

    publish_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{IG_USER_ID}/media_publish"
    resp = requests.post(
        publish_url,
        data={"creation_id": creation_id, "access_token": META_ACCESS_TOKEN},
        timeout=60,
    )
    resp.raise_for_status()
    media_id = resp.json()["id"]

    perma_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{media_id}"
    resp = requests.get(
        perma_url,
        params={"fields": "permalink", "access_token": META_ACCESS_TOKEN},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("permalink", f"https://www.instagram.com/p/{media_id}/")


def post_facebook(row, caption):
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{FB_PAGE_ID}/photos"
    resp = requests.post(
        url,
        data={
            "url": row["image_url"],
            "caption": caption,
            "access_token": META_ACCESS_TOKEN,
        },
        timeout=60,
    )
    resp.raise_for_status()
    result = resp.json()
    post_id = result.get("post_id") or result.get("id")
    return f"https://www.facebook.com/{post_id}"


def notion_update_row(page_id, status, post_url, log_text):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    properties = {
        "Status": {"select": {"name": status}},
        "Log": {"rich_text": [{"text": {"content": log_text[:1900]}}]},
    }
    if post_url:
        properties["Post URL"] = {"url": post_url}
    resp = requests.patch(url, headers=NOTION_HEADERS, json={"properties": properties}, timeout=30)
    resp.raise_for_status()


def save_local_copy(today, row, caption, results):
    os.makedirs("posted", exist_ok=True)
    path = os.path.join("posted", f"{today}.md")
    lines = [
        f"# {row['name']}",
        "",
        f"- Date: {today}",
        f"- Platforms: {', '.join(row['platforms'])}",
        f"- Image: {row['image_url']}",
        "",
        "## Caption",
        "",
        caption,
        "",
        "## Results",
        "",
    ]
    for platform, outcome in results.items():
        lines.append(f"- {platform}: {outcome}")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    return path


def send_telegram(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        log("Telegram not configured, skipping notification.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "disable_web_page_preview": True},
            timeout=15,
        )
    except requests.RequestException as exc:
        log(f"Telegram notification failed: {exc}")


def require_env(names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=os.environ.get("DRY_RUN", "0") == "1")
    args = parser.parse_args()

    require_env(["NOTION_TOKEN", "NOTION_DATABASE_ID"])

    today = datetime.now(ZoneInfo(TIMEZONE)).strftime("%Y-%m-%d")
    log(f"Looking for a Scheduled row on {today} ({TIMEZONE})...")

    page = notion_find_todays_row(today)
    if not page:
        log("No Scheduled row for today. Nothing to do.")
        send_telegram(f"UDC Drumbeat — {today}: no Scheduled row found. Nothing posted.")
        return

    row = parse_row(page)
    caption = full_caption(row)

    log(f"Found row: {row['name']!r} — platforms: {row['platforms']}")

    if args.dry_run:
        log("DRY RUN — not posting to Meta, not writing to Notion.")
        log(f"Caption:\n{caption}")
        log(f"Image URL: {row['image_url']}")
        return

    if not row["image_url"]:
        msg = f"Row {row['name']!r} has no Image attached."
        log(f"ERROR: {msg}")
        notion_update_row(row["page_id"], "Failed", None, msg)
        send_telegram(f"UDC Drumbeat — {today}: FAILED. {msg}")
        sys.exit(1)

    require_env(["META_ACCESS_TOKEN"])
    if "Instagram" in row["platforms"]:
        require_env(["IG_USER_ID"])
    if "Facebook" in row["platforms"]:
        require_env(["FB_PAGE_ID"])

    results = {}
    errors = []

    if "Instagram" in row["platforms"]:
        try:
            results["Instagram"] = post_instagram(row, caption)
            log(f"Posted to Instagram: {results['Instagram']}")
        except requests.RequestException as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            results["Instagram"] = f"FAILED — {detail}"
            errors.append(f"Instagram: {detail}")
            log(f"Instagram post failed: {detail}")

    if "Facebook" in row["platforms"]:
        try:
            results["Facebook"] = post_facebook(row, caption)
            log(f"Posted to Facebook: {results['Facebook']}")
        except requests.RequestException as exc:
            detail = exc.response.text if exc.response is not None else str(exc)
            results["Facebook"] = f"FAILED — {detail}"
            errors.append(f"Facebook: {detail}")
            log(f"Facebook post failed: {detail}")

    successful_urls = [v for v in results.values() if v.startswith("http")]
    post_url = successful_urls[0] if successful_urls else None

    if not errors:
        status = "Posted"
    elif successful_urls:
        status = "Posted (partial)"
    else:
        status = "Failed"

    log_text = "; ".join(f"{k}: {v}" for k, v in results.items())
    notion_update_row(row["page_id"], status, post_url, log_text)

    path = save_local_copy(today, row, caption, results)
    log(f"Saved local copy to {path}")

    summary_lines = [f"UDC Drumbeat — {today}: {status} — {row['name']}"]
    for platform, outcome in results.items():
        summary_lines.append(f"  {platform}: {outcome}")
    send_telegram("\n".join(summary_lines))

    if status == "Failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
