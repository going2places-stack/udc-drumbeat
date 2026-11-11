# UDC Evergreen Drumbeat

Daily GitHub Actions automation for posting approved Unofficial DC evergreen content to Instagram and Facebook from a Notion queue.

## What Is Wired

- A Notion database named `UDC Evergreen Calendar` was created under `Unofficial DC - Open Brain / 03 - Operations Layer`.
- Database URL: `https://app.notion.com/p/231e4d25992845e3a610b9f4c65f0357`
- Use `231e4d25992845e3a610b9f4c65f0357` for the `NOTION_DATABASE_ID` GitHub secret.
- Data source ID for connector/admin tooling: `f93bccc4-474a-41dc-8c63-f71558e2ff3a`
- The Mac targets 9am Eastern; GitHub is a later cloud fallback. Both use the same atomic daily claim.
- The approved eight-item evergreen rotation keeps 14 days queued in Notion.
- Runs explicitly report PUBLISHED, ALREADY_POSTED, NOTHING_SCHEDULED, or FAILED/NEEDS_REVIEW, with actual platform links where available.

## Required GitHub Secrets

- `NOTION_TOKEN`
- `NOTION_DATABASE_ID` = `231e4d25992845e3a610b9f4c65f0357`
- `META_ACCESS_TOKEN`
- `IG_USER_ID`
- `FB_PAGE_ID`

Optional:

- `FB_PAGE_ACCESS_TOKEN` - use when Facebook Page publishing needs a dedicated Page access token separate from the Instagram publishing token.
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Local Commands

```bash
python -m pip install -r requirements.txt
python scripts/publish_today.py --dry-run
python scripts/import_ready_posts.py --input data/ready_posts.json --dry-run
```

## Local 9:00 a.m. Publisher

Use `bash scripts/install_local_launchd.sh` to install the private runtime outside Documents. See `docs/local_scheduler.md` for schedule, verification, shared ledger, and recovery. The previous local dispatch bridge is disabled. A shared create-only daily claim prevents competing local/cloud publishing; uncertain results stop for review rather than retrying blindly.

## Notes

Meta requires `image_url` values to be reachable by Meta's servers. If images are stored in private Google Drive links, either upload them into Notion as files or use a public/direct image URL before running a real publish.
