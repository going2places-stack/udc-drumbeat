"""Replace future queued, attribution-flagged graphics with approved wordless art.

Reads the source inventory; never changes Posted rows or original source pages.
Use --apply after inspecting the default plan. Captures changed row IDs locally.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    import post_today
    from evergreen_queue import rotation_item
    today = dt.datetime.now(ZoneInfo("America/New_York")).date()
    library = {x["name"]: x for x in json.loads((ROOT / "data/approved_evergreen.json").read_text())}
    response = requests.post(f"https://api.notion.com/v1/databases/{post_today.NOTION_DB}/query",
        headers=post_today.NOTION_HEADERS, json={"filter": {"and": [
            {"property": "Status", "select": {"equals": "Scheduled"}},
            {"property": "Date", "date": {"after": today.isoformat()}}
        ]}, "page_size": 100}, timeout=30)
    response.raise_for_status(); body = response.json()
    if body.get("has_more"): raise RuntimeError("Queue exceeds maintenance limit; stopped.")
    changes = []
    for page in body["results"]:
        props = page["properties"]
        name = post_today.title_text(props["Name"])
        held = next((x for x in library.values() if x.get("editorial_hold") and x["name"] in name), None)
        if not held: continue
        date = dt.date.fromisoformat(props["Date"]["date"]["start"][:10])
        item = rotation_item(date, library)
        change = {"page_id": page["id"], "date": date.isoformat(), "previous": name, "replacement": item["name"]}
        print(json.dumps(change), flush=True); changes.append(change)
        if not args.apply: continue
        def text(value): return {"rich_text": [{"text": {"content": value}}]}
        properties = {
            "Name": {"title": [{"text": {"content": f"{date} • {item['name']}"}}]},
            "Caption": text(item["caption"]), "Hashtags": text(item["hashtags"]),
            "Image": {"files": [{"name": item["name"]+".png", "type": "external", "external": {"url": item["image_url"]}}]},
            "Log": text("Attribution reconciliation: held graphic " + held["name"] +
                        "; retained source page " + held["source_page_id"] +
                        ". Replaced with existing approved wordless artwork pending new baseline review.")
        }
        result = requests.patch(f"https://api.notion.com/v1/pages/{page['id']}",
            headers=post_today.NOTION_HEADERS, json={"properties": properties}, timeout=30)
        result.raise_for_status()
    if args.apply:
        (ROOT / "runs").mkdir(exist_ok=True)
        (ROOT / f"runs/{today}-quote-reconciliation.json").write_text(json.dumps(changes, indent=2)+"\n")
    print(f"{'Applied' if args.apply else 'Planned'} {len(changes)} future-row replacements; no publishing calls.")


if __name__ == "__main__": main()
