#!/usr/bin/env python3
"""Review-gated Story CLI. Default is a no-publish check."""
import argparse
import datetime as dt
import json
from pathlib import Path
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("content_id")
    parser.add_argument("--destination", choices=["instagram-story", "facebook-story"], required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    from story_publisher import MetaStories, publish_destination
    import post_today
    row = next(x for x in json.loads((ROOT / "data/baseline_month.json").read_text())
               if x["content_id"] == args.content_id)
    if args.live:
        publisher = MetaStories(post_today.META_TOKEN, post_today.facebook_page_token(),
                                post_today.IG_USER_ID, post_today.FB_PAGE_ID)
    else:
        publisher = None
    result = publish_destination(dt.datetime.now(ZoneInfo("America/New_York")).date(),
                                 args.destination, row, publisher, dry_run=not args.live)
    print(json.dumps(result))
    return 0 if result["outcome"] in ("DRY_RUN", "PUBLISHED", "ALREADY_POSTED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
