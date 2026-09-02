#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

NOTION_VERSION = "2022-06-28"


def headers() -> dict[str, str]:
    token = os.getenv("NOTION_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing NOTION_TOKEN")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def rich_text(value: str) -> dict[str, Any]:
    return {"rich_text": [{"text": {"content": value[:1900]}}]} if value else {"rich_text": []}


def page_payload(database_id: str, row: dict[str, Any]) -> dict[str, Any]:
    image_url = row.get("image_url", "")
    properties: dict[str, Any] = {
        "Name": {"title": [{"text": {"content": row["name"]}}]},
        "Date": {"date": {"start": row["scheduled_date"]}},
        "Caption": rich_text(row.get("caption", "")),
        "Hashtags": rich_text(row.get("hashtags", "")),
        "Platforms": {"multi_select": [{"name": "Instagram"}, {"name": "Facebook"}]},
        "Status": {"select": {"name": "Scheduled"}},
        "Log": rich_text(f"Source row date {row['source_date']}; Drive file {row.get('image_file_id', '')}"),
    }
    if image_url:
        properties["Image"] = {"files": [{"name": row["image_title"], "type": "external", "external": {"url": image_url}}]}
    return {"parent": {"database_id": database_id}, "properties": properties}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/ready_posts.json")
    parser.add_argument("--database-id", default=os.getenv("NOTION_DATABASE_ID", ""))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.database_id:
        print("Missing --database-id or NOTION_DATABASE_ID", file=sys.stderr)
        return 2

    rows = json.loads(Path(args.input).read_text())
    if args.dry_run:
        print(json.dumps([page_payload(args.database_id, row) for row in rows], indent=2))
        return 0

    for row in rows:
        request = Request(
            "https://api.notion.com/v1/pages",
            data=json.dumps(page_payload(args.database_id, row)).encode("utf-8"),
            headers=headers(),
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                response.read()
        except Exception as exc:
            print(exc, file=sys.stderr)
            return 1
        print(f"Created {row['scheduled_date']} {row['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
