#!/usr/bin/env python3
"""
Weekly backup: copy facts/ and posted/ (the repo's owned records) into a Drive folder.
Idempotent: a file with the same name in the same subfolder is overwritten, not duplicated.
Not on the daily path. If this fails, posting is unaffected.

Env: GDRIVE_SA_JSON (service-account JSON), GDRIVE_MIRROR_FOLDER_ID (target folder, shared
with the service account's email as Editor).
"""
import json
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SRC_DIRS = ["facts", "posted"]


def main():
    info = json.loads(os.environ["GDRIVE_SA_JSON"])
    root = os.environ["GDRIVE_MIRROR_FOLDER_ID"]
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive"])
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)

    def child_folder(name, parent):
        q = f"name = '{name}' and '{parent}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        res = svc.files().list(q=q, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        if res["files"]:
            return res["files"][0]["id"]
        f = svc.files().create(body={"name": name, "parents": [parent],
                                     "mimeType": "application/vnd.google-apps.folder"},
                               fields="id", supportsAllDrives=True).execute()
        return f["id"]

    def existing(name, parent):
        q = f"name = '{name}' and '{parent}' in parents and trashed = false"
        res = svc.files().list(q=q, fields="files(id)", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        return res["files"][0]["id"] if res["files"] else None

    n = 0
    for d in SRC_DIRS:
        if not os.path.isdir(d):
            continue
        folder = child_folder(d, root)
        for fn in sorted(os.listdir(d)):
            path = os.path.join(d, fn)
            if not os.path.isfile(path):
                continue
            media = MediaFileUpload(path, mimetype="text/markdown", resumable=False)
            fid = existing(fn, folder)
            if fid:
                svc.files().update(fileId=fid, media_body=media, supportsAllDrives=True).execute()
            else:
                svc.files().create(body={"name": fn, "parents": [folder]}, media_body=media,
                                   fields="id", supportsAllDrives=True).execute()
            n += 1
    print(f"mirrored {n} files")


if __name__ == "__main__":
    main()
