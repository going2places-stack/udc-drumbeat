"""Independent Story publishing with create-only per-destination claims.

Does not invoke the feed publisher. New artwork must have explicit asset approval.
Meta's official Python SDK and read-only account probes establish the endpoints.
"""
import time
from urllib.parse import urlparse

import requests

from publishing_state import DailyState

GRAPH = "https://graph.facebook.com/v21.0"


class MetaStories:
    def __init__(self, meta_token, page_token, ig_user_id, page_id):
        self.meta_token, self.page_token = meta_token, page_token
        self.ig_user_id, self.page_id = ig_user_id, page_id

    def get(self, path, token, **params):
        response = requests.get(f"{GRAPH}/{path}", params=params,
            headers={"Authorization": f"Bearer {token}"}, timeout=30)
        response.raise_for_status()
        return response.json()

    def post(self, path, token, **data):
        response = requests.post(f"{GRAPH}/{path}", data=data,
            headers={"Authorization": f"Bearer {token}"}, timeout=60)
        response.raise_for_status()
        return response.json()

    def instagram(self, image_url=None, video_url=None):
        media = {"video_url": video_url} if video_url else {"image_url": image_url}
        container = self.post(f"{self.ig_user_id}/media", self.meta_token,
                              media_type="STORIES", **media)
        ready = False
        for _ in range(30):
            status = self.get(container["id"], self.meta_token, fields="status_code")
            if status.get("status_code") == "FINISHED":
                ready = True; break
            if status.get("status_code") in ("ERROR", "EXPIRED"):
                raise RuntimeError("Instagram Story container failed; review the claim before retrying.")
            time.sleep(3)
        if not ready:
            raise RuntimeError("Instagram Story is not ready. No publish call made.")
        result = self.post(f"{self.ig_user_id}/media_publish", self.meta_token,
                           creation_id=container["id"])
        for _ in range(5):
            stories = self.get(f"{self.ig_user_id}/stories", self.meta_token,
                               fields="id,permalink", limit=100)
            for story in stories.get("data", []):
                if story["id"] == result["id"] and story.get("permalink"):
                    return {"id": story["id"], "url": story["permalink"]}
            time.sleep(2)
        raise RuntimeError("Instagram accepted the Story but read-back is pending. Do not repost.")

    def facebook(self, image_url=None, video_url=None):
        if video_url:
            session = self.post(f"{self.page_id}/video_stories", self.page_token, upload_phase="START")
            upload_url = session["upload_url"]
            if urlparse(upload_url).scheme != "https" or urlparse(upload_url).hostname != "rupload.facebook.com":
                raise RuntimeError("Unexpected Facebook upload destination; stopped before transmitting token.")
            response = requests.post(upload_url, headers={"Authorization": f"OAuth {self.page_token}",
                                                          "file_url": video_url}, timeout=90)
            response.raise_for_status()
            if not response.json().get("success"):
                raise RuntimeError("Facebook Story video upload not confirmed.")
            result = self.post(f"{self.page_id}/video_stories", self.page_token,
                upload_phase="FINISH", video_id=session["video_id"], video_state="PUBLISHED")
            identifiers = {str(session["video_id"]), str(result.get("post_id", ""))}
        else:
            staged = self.post(f"{self.page_id}/photos", self.page_token, url=image_url, published="false")
            result = self.post(f"{self.page_id}/photo_stories", self.page_token, photo_id=staged["id"])
            identifiers = {str(result.get("post_id", ""))}
        for _ in range(15):
            stories = self.get(f"{self.page_id}/stories", self.page_token,
                               fields="post_id,url,status", limit=100)
            for story in stories.get("data", []):
                if str(story.get("post_id")) in identifiers and story.get("status") == "published" and story.get("url"):
                    return {"id": str(story["post_id"]), "url": story["url"]}
            time.sleep(3)
        raise RuntimeError("Facebook accepted the Story but a verified Story URL is pending. Do not repost.")


def publish_destination(day, destination, row, publisher, dry_run=True):
    if destination not in ("instagram-story", "facebook-story"):
        raise ValueError("Unsupported automatic destination")
    if not row.get("asset_approval") or not row.get("content_approval"):
        return {"destination": destination, "outcome": "AWAITING_REVIEW"}
    assets = row.get("assets", {})
    video_url, image_url = assets.get("video_url"), assets.get("story_image_url")
    if not video_url and not image_url:
        return {"destination": destination, "outcome": "MISSING_ASSET"}
    if dry_run:
        return {"destination": destination, "outcome": "DRY_RUN", "content_id": row["content_id"]}
    state = DailyState(day)
    state.path = f"destinations/{day}/{destination}.json"
    if not state.acquire({"id": row["content_id"], "title": row["message"]}):
        return {"destination": destination,
                "outcome": "ALREADY_POSTED" if state.data.get("outcome") == "posted" and state.data.get("page_id") == row["content_id"] else "NEEDS_REVIEW",
                "receipts": state.data.get("receipts", {})}
    try:
        method = publisher.instagram if destination == "instagram-story" else publisher.facebook
        receipt = method(image_url=image_url, video_url=video_url)
        # Persist a real API-returned URL. Never invent a Story permalink.
        state.checkpoint(platform=destination, url=receipt["url"], outcome="posted",
                         note="Verified Story ID: " + receipt["id"] + "; Stories expire on the platform.")
        return {"destination": destination, "outcome": "PUBLISHED", **receipt}
    except Exception as exc:
        state.checkpoint(outcome="needs_review", note=type(exc).__name__ + "; inspect platform before retry.")
        return {"destination": destination, "outcome": "NEEDS_REVIEW", "error_type": type(exc).__name__}
