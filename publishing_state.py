"""Shared, fail-closed daily claims and receipts, separate from the code branch."""
import base64
import datetime as dt
import json
import os
import subprocess

import requests


class DailyState:
    def __init__(self, day):
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            token = subprocess.check_output(
                ["/opt/homebrew/bin/gh", "auth", "token"], text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        self.headers = {"Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"}
        repo = os.environ.get("STATE_REPOSITORY", "going2places-stack/udc-drumbeat")
        self.base = f"https://api.github.com/repos/{repo}/contents/"
        self.branch = "drumbeat-state"
        self.path = f"claims/{day}.json"
        self.day = str(day)
        self.sha = None
        self.data = None

    def read(self, path=None):
        response = requests.get(self.base + (path or self.path), headers=self.headers,
                                params={"ref": self.branch}, timeout=30)
        if response.status_code == 404:
            return None, None
        response.raise_for_status()
        body = response.json()
        return json.loads(base64.b64decode(body["content"])), body["sha"]

    def write(self, path, data, sha=None):
        payload = {"branch": self.branch, "message": f"evergreen {self.day}: {data['outcome']}",
                   "content": base64.b64encode(json.dumps(data, indent=2).encode()).decode()}
        if sha:
            payload["sha"] = sha
        response = requests.put(self.base + path, headers=self.headers, json=payload, timeout=30)
        if response.status_code in (409, 422):
            return None
        response.raise_for_status()
        return response.json()["content"]["sha"]

    def acquire(self, row):
        self.data = {"date": self.day, "page_id": row["id"], "title": row["title"],
                     "outcome": "publishing", "receipts": {},
                     "started_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        self.sha = self.write(self.path, self.data)
        if self.sha:
            return True
        self.data, self.sha = self.read()
        if not self.data:
            raise RuntimeError("Could not acquire or read the shared daily claim; stopped safely.")
        return False

    def checkpoint(self, outcome=None, platform=None, url=None, note=None):
        if platform:
            self.data["receipts"][platform] = url
        if outcome:
            self.data["outcome"] = outcome
        if note:
            self.data["note"] = note
        self.data["updated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        sha = self.write(self.path, self.data, self.sha)
        if not sha:
            raise RuntimeError("Shared receipt changed unexpectedly; do not retry publishing automatically.")
        self.sha = sha

    def report(self, outcome, note, urls):
        path = f"runs/{self.day}.json"
        old, sha = self.read(path)
        data = {"date": self.day, "outcome": outcome, "note": note, "urls": urls}
        # No repeat notifications for unchanged retries or backup runs.
        if old and all(old.get(k) == v for k, v in data.items()):
            return False
        data["checked_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
        return bool(self.write(path, data, sha))
