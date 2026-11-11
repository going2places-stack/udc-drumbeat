import datetime as dt
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("NOTION_TOKEN", "test-notion-secret")
os.environ.setdefault("NOTION_DATABASE_ID", "test-database")
import post_today as publisher
from publishing_state import DailyState
import evergreen_queue


class PublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.cwd)
        self.addCleanup(self.temp.cleanup)
        self.row = {"id": "row", "title": "Approved item", "caption": "Love",
                    "image_url": "https://example.org/image.png", "status": "Scheduled",
                    "platforms": ["Instagram", "Facebook"], "existing_post_url": None}

    def main_mocks(self):
        return patch.multiple(publisher, ensure_queue=MagicMock(return_value=0),
            find_todays_row=MagicMock(return_value={}),
            parse_row=MagicMock(return_value=self.row), finish=MagicMock(side_effect=lambda *a, **k: k.get("code", 0)),
            archive=MagicMock(), update_row=MagicMock())

    def test_empty_queue_is_failure_not_success(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", False):
            publisher.find_todays_row.return_value = None
            self.assertEqual(publisher.main(), 2)
            self.assertEqual(publisher.finish.call_args.args[0], "NOTHING_SCHEDULED")

    def test_dry_run_missing_image_never_writes_notion(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", True):
            publisher.find_todays_row.return_value = {"id": "row"}
            self.row["image_url"] = None
            self.assertEqual(publisher.main(), 1)
            publisher.update_row.assert_not_called()
            publisher.ensure_queue.assert_not_called()

    def test_dry_run_never_claims_or_publishes(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", True), \
             patch.object(publisher, "DailyState") as state, \
             patch.object(publisher, "publish_instagram") as ig:
            publisher.find_todays_row.return_value = {"id": "row"}
            self.assertEqual(publisher.main(), 0)
            state.assert_not_called()
            ig.assert_not_called()

    def test_losing_claim_never_publishes(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", False), \
             patch.object(publisher, "DailyState") as cls, \
             patch.object(publisher, "publish_instagram") as ig, \
             patch.object(publisher, "publish_facebook") as fb:
            publisher.find_todays_row.return_value = {"id": "row"}
            cls.return_value.acquire.return_value = False
            cls.return_value.data = {"outcome": "publishing", "receipts": {}}
            self.assertEqual(publisher.main(), 1)
            ig.assert_not_called(); fb.assert_not_called()

    def test_uncertain_instagram_stops_facebook_and_blocks_retry(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", False), \
             patch.object(publisher, "DailyState") as cls, \
             patch.object(publisher, "publish_instagram", side_effect=TimeoutError("uncertain")), \
             patch.object(publisher, "publish_facebook") as fb:
            publisher.find_todays_row.return_value = {"id": "row"}
            cls.return_value.acquire.return_value = True
            self.assertEqual(publisher.main(), 1)
            fb.assert_not_called()
            self.assertEqual(cls.return_value.checkpoint.call_args.kwargs["outcome"], "needs_review")

    def test_both_receipts_saved_before_notion(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", False), \
             patch.object(publisher, "DailyState") as cls, \
             patch.object(publisher, "publish_instagram", return_value="https://instagram.com/p/1"), \
             patch.object(publisher, "publish_facebook", return_value="https://facebook.com/1"):
            publisher.find_todays_row.return_value = {"id": "row"}
            self.assertEqual(publisher.main(), 0)
            checkpoints = cls.return_value.checkpoint.call_args_list
            self.assertEqual(checkpoints[0].kwargs["platform"], "Instagram")
            self.assertEqual(checkpoints[1].kwargs["platform"], "Facebook")
            self.assertEqual(checkpoints[2].kwargs["outcome"], "posted")
            self.assertEqual(publisher.finish.call_args.args[0], "PUBLISHED")

    def test_persisted_receipts_reconcile_without_reposting(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", False), \
             patch.object(publisher, "DailyState") as cls, \
             patch.object(publisher, "publish_instagram") as ig:
            publisher.find_todays_row.return_value = {"id": "row"}
            cls.return_value.acquire.return_value = False
            cls.return_value.data = {"page_id": "row", "outcome": "posted", "receipts": {"Instagram": "https://instagram.com/p/1", "Facebook": "https://facebook.com/1"}}
            self.assertEqual(publisher.main(), 0)
            ig.assert_not_called()
            publisher.update_row.assert_called_once()
            self.assertEqual(publisher.finish.call_args.args[0], "ALREADY_POSTED")

    def test_claim_create_conflict_reads_existing_owner(self):
        state = object.__new__(DailyState)
        state.day = "2026-11-11"; state.path = "claims/test.json"
        with patch.object(state, "write", return_value=None) as write, \
             patch.object(state, "read", return_value=({"outcome": "publishing"}, "sha")):
            self.assertFalse(state.acquire(self.row))
            self.assertEqual(len(write.call_args.args), 2)  # create-only, no update SHA

    def test_unchanged_report_does_not_renotify(self):
        state = object.__new__(DailyState); state.day = "2026-11-11"
        old = {"date": state.day, "outcome": "NOTHING_SCHEDULED", "note": "Empty", "urls": []}
        with patch.object(state, "read", return_value=(old, "sha")), patch.object(state, "write") as write:
            self.assertFalse(state.report("NOTHING_SCHEDULED", "Empty", []))
            write.assert_not_called()

    def test_secret_errors_are_redacted(self):
        with patch.object(publisher, "META_TOKEN", "private-value"):
            result = publisher.safe_error(RuntimeError("private-value access_token=other-secret&x=1"))
            self.assertNotIn("private-value", result)
            self.assertNotIn("other-secret", result)

    def test_notion_failure_preserves_both_platform_receipts(self):
        with self.main_mocks(), patch.object(publisher, "DRY_RUN", False), \
             patch.object(publisher, "DailyState") as cls, \
             patch.object(publisher, "publish_instagram", return_value="https://instagram.com/p/1"), \
             patch.object(publisher, "publish_facebook", return_value="https://facebook.com/1"):
            publisher.find_todays_row.return_value = {"id": "row"}
            publisher.update_row.side_effect = TimeoutError("Notion unavailable")
            self.assertEqual(publisher.main(), 1)
            self.assertEqual(cls.return_value.checkpoint.call_args.kwargs["outcome"], "posted")
            publisher.archive.assert_called_once()
            self.assertEqual(publisher.finish.call_args.args[0], "NEEDS_REVIEW")

    def test_failed_desktop_notification_does_not_turn_post_into_failure(self):
        with patch.object(publisher, "DRY_RUN", False), patch.object(publisher.sys, "platform", "darwin"), \
             patch.object(publisher, "telegram"), \
             patch.object(publisher.subprocess, "run", side_effect=publisher.subprocess.TimeoutExpired("osascript", 10)):
            state = MagicMock(); state.report.return_value = True
            self.assertEqual(publisher.finish("PUBLISHED", "Verified", ["https://facebook.com/1"], state=state), 0)

    def test_completed_refill_does_not_create_duplicate_rows(self):
        with patch.object(evergreen_queue, "DailyState") as cls, \
             patch.object(evergreen_queue.requests, "post") as post:
            cls.return_value.acquire.return_value = False
            cls.return_value.data = {"outcome": "ready"}
            self.assertEqual(evergreen_queue.ensure_queue(dt.date(2026, 11, 11), "db", {}), 0)
            post.assert_not_called()

    def test_refill_preserves_existing_dates_and_only_adds_the_gap(self):
        from pathlib import Path
        day = dt.date(2026, 11, 11)
        Path("data").mkdir()
        library = [{"name": name, "caption": "Approved", "hashtags": "#DC", "image_url": "https://example.org/image.png", "source_page_id": "source"} for name in evergreen_queue.ORDER]
        Path("data/approved_evergreen.json").write_text(json.dumps(library))
        response = MagicMock()
        response.json.return_value = {"results": [
            {"properties": {"Date": {"date": {"start": (day + dt.timedelta(days=i)).isoformat()}}}}
            for i in range(13)
        ], "has_more": False}
        with patch.object(evergreen_queue, "DailyState"), \
             patch.object(evergreen_queue.requests, "post", return_value=response) as post:
            self.assertEqual(evergreen_queue.ensure_queue(day, "db", {}), 1)
            self.assertEqual(post.call_count, 2)
            created = post.call_args.kwargs["json"]["properties"]
            self.assertEqual(created["Date"]["date"]["start"], "2026-11-24")
            self.assertEqual(created["Status"]["select"]["name"], "Scheduled")


if __name__ == "__main__":
    unittest.main()
