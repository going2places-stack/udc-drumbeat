#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import sys
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

NOTION_VERSION = "2022-06-28"
GRAPH_VERSION = "v21.0"


class ConfigError(RuntimeError):
    pass


def env(name: str, required: bool = True) -> str:
    value = os.getenv(name, "").strip()
    if required and not value:
        raise ConfigError(f"Missing required environment variable: {name}")
    return value


def notion_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {env('NOTION_TOKEN')}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def request_json(method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    headers = kwargs.get("headers", {})
    body = None
    if "json" in kwargs:
        body = json.dumps(kwargs["json"]).encode("utf-8")
    elif "data" in kwargs:
        body = urlencode(kwargs["data"]).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded", **headers}
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc


def text_property(page: dict[str, Any], name: str) -> str:
    prop = page["properties"].get(name, {})
    rich = prop.get("rich_text") or prop.get("title") or []
    return "".join(part.get("plain_text", "") for part in rich).strip()


def select_property(page: dict[str, Any], name: str) -> str:
    value = page["properties"].get(name, {}).get("select")
    return value.get("name", "") if value else ""


def multi_select_property(page: dict[str, Any], name: str) -> list[str]:
    return [item["name"] for item in page["properties"].get(name, {}).get("multi_select", [])]


def file_url_property(page: dict[str, Any], name: str) -> str:
    files = page["properties"].get(name, {}).get("files", [])
    if not files:
        return ""
    first = files[0]
    if first.get("type") == "external":
        return first["external"]["url"]
    if first.get("type") == "file":
        return first["file"]["url"]
    return ""


def query_today(database_id: str, post_date: str) -> list[dict[str, Any]]:
    payload = {
        "filter": {
            "and": [
                {"property": "Date", "date": {"equals": post_date}},
                {"property": "Status", "select": {"equals": "Scheduled"}},
            ]
        },
        "sorts": [{"property": "Date", "direction": "ascending"}],
    }
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    return request_json("POST", url, headers=notion_headers(), json=payload).get("results", [])


def update_page(page_id: str, status: str, log: str, post_url: str = "") -> None:
    properties: dict[str, Any] = {
        "Status": {"select": {"name": status}},
        "Log": {"rich_text": [{"text": {"content": log[:1900]}}]},
    }
    if post_url:
        properties["Post URL"] = {"url": post_url}
    request_json(
        "PATCH",
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=notion_headers(),
        json={"properties": properties},
    )


def publish_instagram(image_url: str, caption: str) -> str:
    token = env("META_ACCESS_TOKEN")
    ig_user_id = env("IG_USER_ID")
    create = request_json(
        "POST",
        f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
    )
    media_id = create["id"]
    published = request_json(
        "POST",
        f"https://graph.facebook.com/{GRAPH_VERSION}/{ig_user_id}/media_publish",
        data={"creation_id": media_id, "access_token": token},
    )
    return published.get("id", media_id)


def publish_facebook(image_url: str, caption: str) -> str:
    token = env("META_ACCESS_TOKEN")
    page_id = env("FB_PAGE_ID")
    published = request_json(
        "POST",
        f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}/photos",
        data={"url": image_url, "caption": caption, "published": "true", "access_token": token},
    )
    return published.get("post_id") or published.get("id", "")


def run(dry_run: bool) -> int:
    post_date = dt.datetime.now(ZoneInfo("America/New_York")).date().isoformat()
    pages = query_today(env("NOTION_DATABASE_ID"), post_date)
    if not pages:
        print(f"No Scheduled rows found for {post_date}.")
        return 0

    for page in pages:
        page_id = page["id"]
        name = text_property(page, "Name")
        caption = "\n\n".join(filter(None, [text_property(page, "Caption"), text_property(page, "Hashtags")]))
        platforms = multi_select_property(page, "Platforms")
        image_url = file_url_property(page, "Image")

        print(f"Found scheduled row: {name}")
        print(caption)

        if not image_url:
            update_page(page_id, "Failed", "Missing Image file URL; skipped publish.")
            continue
        if dry_run:
            print(f"DRY_RUN=1; would publish to {', '.join(platforms)} using {image_url}")
            continue

        successes: list[str] = []
        failures: list[str] = []
        post_url = ""
        if "Instagram" in platforms:
            try:
                ig_id = publish_instagram(image_url, caption)
                successes.append(f"Instagram:{ig_id}")
            except Exception as exc:
                failures.append(f"Instagram:{exc}")
        if "Facebook" in platforms:
            try:
                fb_id = publish_facebook(image_url, caption)
                successes.append(f"Facebook:{fb_id}")
                if fb_id:
                    post_url = f"https://facebook.com/{fb_id}"
            except Exception as exc:
                failures.append(f"Facebook:{exc}")

        status = "Posted" if successes and not failures else "Posted (partial)" if successes else "Failed"
        update_page(page_id, status, json.dumps({"successes": successes, "failures": failures}), post_url)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=os.getenv("DRY_RUN") == "1")
    args = parser.parse_args()
    try:
        return run(args.dry_run)
    except ConfigError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
