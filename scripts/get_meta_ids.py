#!/usr/bin/env python3
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import urlopen

GRAPH_VERSION = "v21.0"


def get_json(url: str) -> dict:
    with urlopen(url, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    token = os.getenv("META_ACCESS_TOKEN", "").strip()
    if not token:
        print("Missing META_ACCESS_TOKEN", file=sys.stderr)
        return 2

    accounts_url = f"https://graph.facebook.com/{GRAPH_VERSION}/me/accounts?{urlencode({'access_token': token})}"
    accounts = get_json(accounts_url)
    print(json.dumps(accounts, indent=2))

    page_id = os.getenv("FB_PAGE_ID", "").strip()
    if not page_id:
        print("\nSet FB_PAGE_ID to the Unofficial DC Page id above, then rerun to get IG_USER_ID.")
        return 0

    ig_url = f"https://graph.facebook.com/{GRAPH_VERSION}/{page_id}?{urlencode({'fields': 'instagram_business_account', 'access_token': token})}"
    print(json.dumps(get_json(ig_url), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
