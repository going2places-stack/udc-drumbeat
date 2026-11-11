"""Maintain a two-week rotation of the eight existing approved evergreen assets."""
import datetime as dt
import json
from pathlib import Path

import requests

from publishing_state import DailyState

EPOCH = dt.date(2026, 11, 11)
ORDER = ["03-25 Lao Tzu", "03-24 MLK Jr.", "03-28 National Mall Wordless",
         "03-27 Aristotle", "03-29 Rumi", "03-30 Mahatma Gandhi",
         "04-07 Go-Go Drummers Wordless", "04-02 Cherry Blossom Logo Wordless"]


def ensure_queue(today, database_id, headers):
    state = DailyState(today)
    state.path = f"refills/{today}.json"
    if not state.acquire({"id": database_id, "title": "14-day evergreen rotation"}):
        if state.data.get("outcome") != "ready":
            raise RuntimeError("Queue refill is in progress or needs review. Inspect the shared refill receipt.")
        return 0
    end = today + dt.timedelta(days=13)
    response = requests.post(f"https://api.notion.com/v1/databases/{database_id}/query",
        headers=headers, json={"filter": {"and": [
            {"property": "Date", "date": {"on_or_after": today.isoformat()}},
            {"property": "Date", "date": {"on_or_before": end.isoformat()}}
        ]}, "page_size": 100}, timeout=30)
    response.raise_for_status()
    body = response.json()
    if body.get("has_more"):
        raise RuntimeError("More than 100 queue rows in two weeks; resolve calendar duplication.")
    occupied = set()
    for page in body["results"]:
        date = (page["properties"]["Date"].get("date") or {}).get("start", "")[:10]
        if date in occupied:
            raise RuntimeError(f"Multiple calendar entries for {date}; resolve before publishing.")
        occupied.add(date)
    library = {x["name"]: x for x in json.loads(Path("data/approved_evergreen.json").read_text())}
    created = 0
    for offset in range(14):
        date = today + dt.timedelta(days=offset)
        if date.isoformat() in occupied:
            continue
        item = library[ORDER[(date - EPOCH).days % len(ORDER)]]
        def text(value):
            return {"rich_text": [{"text": {"content": value}}]}
        properties = {
            "Name": {"title": [{"text": {"content": f"{date} • {item['name']}"}}]},
            "Date": {"date": {"start": date.isoformat()}},
            "Status": {"select": {"name": "Scheduled"}},
            "Caption": text(item["caption"]), "Hashtags": text(item["hashtags"]),
            "Platforms": {"multi_select": [{"name": "Instagram"}, {"name": "Facebook"}]},
            "Image": {"files": [{"name": item["name"] + ".png", "type": "external",
                                    "external": {"url": item["image_url"]}}]},
            "Log": text("Approved evergreen rotation; target 09:00 America/New_York. Source page: " + item["source_page_id"]),
        }
        # Deliberately no automatic retry after a timeout: creation may have succeeded.
        response = requests.post("https://api.notion.com/v1/pages", headers=headers,
            json={"parent": {"database_id": database_id}, "properties": properties}, timeout=30)
        response.raise_for_status()
        created += 1
    state.checkpoint(outcome="ready", note=f"Queue maintained through {end}; added {created} rows.")
    return created
