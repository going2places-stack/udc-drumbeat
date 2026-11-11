import datetime as dt
import unittest
from unittest.mock import MagicMock, patch

from brand_defaults import brand_hashtags
from scripts.prepare_baseline_month import build
from story_publisher import MetaStories, publish_destination
from evergreen_queue import rotation_item


class BaselineTests(unittest.TestCase):
    def test_required_brand_tags_are_unique_and_first(self):
        self.assertEqual(brand_hashtags("#unofficialdc #DCLove #LOVEISTHENORTHSTAR #DCLove"),
                         "#UnofficialDC #LoveIsTheNorthStar #DCLove")
        self.assertEqual(len(brand_hashtags("#a #b #c #d #e").split()), 5)

    def test_month_has_distinct_messages_and_separate_reviews(self):
        rows = build()
        self.assertEqual(len(rows), 30)
        self.assertEqual(len({x["message"].casefold() for x in rows}), 30)
        self.assertTrue(all(not x["asset_approval"] and not x["content_approval"] for x in rows))
        self.assertTrue(all(len(x["variants"]) == 8 for x in rows))

    def row(self):
        return {"content_id": "review-001", "message": "Love lives next door.",
                "asset_approval": True, "content_approval": True,
                "assets": {"video_url": "https://example.org/story.mp4"}}

    def test_unreviewed_art_never_calls_publisher_or_claim(self):
        row = self.row(); row["asset_approval"] = False
        publisher = MagicMock()
        with patch("story_publisher.DailyState") as cls:
            result = publish_destination(dt.date.today(), "instagram-story", row, publisher, dry_run=False)
            self.assertEqual(result["outcome"], "AWAITING_REVIEW")
            cls.assert_not_called(); publisher.instagram.assert_not_called()

    def test_story_dry_run_never_claims_or_posts(self):
        publisher = MagicMock()
        with patch("story_publisher.DailyState") as cls:
            self.assertEqual(publish_destination(dt.date.today(), "facebook-story", self.row(), publisher)["outcome"], "DRY_RUN")
            cls.assert_not_called(); publisher.facebook.assert_not_called()

    def test_existing_story_claim_cannot_republish_or_invoke_feed(self):
        publisher = MagicMock()
        with patch("story_publisher.DailyState") as cls:
            cls.return_value.acquire.return_value = False
            cls.return_value.data = {"page_id": "review-001", "outcome": "posted", "receipts": {"instagram-story": "https://instagram.com/stories/1"}}
            result = publish_destination(dt.date.today(), "instagram-story", self.row(), publisher, dry_run=False)
            self.assertEqual(result["outcome"], "ALREADY_POSTED")
            publisher.instagram.assert_not_called()

    def test_story_failures_hold_claim_for_review(self):
        publisher = MagicMock(); publisher.instagram.side_effect = TimeoutError()
        with patch("story_publisher.DailyState") as cls:
            cls.return_value.acquire.return_value = True
            result = publish_destination(dt.date.today(), "instagram-story", self.row(), publisher, dry_run=False)
            self.assertEqual(result["outcome"], "NEEDS_REVIEW")
            self.assertEqual(cls.return_value.checkpoint.call_args.kwargs["outcome"], "needs_review")

    def test_facebook_receipt_uses_actual_story_url(self):
        publisher = MetaStories("meta", "page", "ig", "fb")
        with patch.object(publisher, "post", side_effect=[{"id": "photo"}, {"post_id": "123"}]), \
             patch.object(publisher, "get", return_value={"data": [
                 {"post_id": "123", "status": "published", "url": "https://facebook.com/stories/real-returned-url"}]}):
            result = publisher.facebook(image_url="https://example.org/story.jpg")
            self.assertEqual(result["url"], "https://facebook.com/stories/real-returned-url")

    def test_video_upload_refuses_unexpected_token_destination(self):
        publisher = MetaStories("meta", "page", "ig", "fb")
        with patch.object(publisher, "post", return_value={"video_id": "1", "upload_url": "https://example.org/token-collector"}), \
             patch("story_publisher.requests.post") as http:
            with self.assertRaises(RuntimeError): publisher.facebook(video_url="https://example.org/story.mp4")
            http.assert_not_called()

    def test_held_quote_graphic_is_not_selected_for_future_refill(self):
        library = {"03-27 Aristotle": {"name": "03-27 Aristotle", "editorial_hold": "Attribution review"},
                   "safe": {"name": "Go-Go Wordless", "caption": "Approved original"}}
        item = rotation_item(dt.date(2026, 11, 14), library)
        self.assertEqual(item["name"], "Go-Go Wordless")

    def test_unapproved_copy_blocks_even_reviewed_art(self):
        row = self.row(); row["content_approval"] = False
        with patch("story_publisher.DailyState") as cls:
            self.assertEqual(publish_destination(dt.date.today(), "instagram-story", row, MagicMock(), dry_run=False)["outcome"], "AWAITING_REVIEW")
            cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
