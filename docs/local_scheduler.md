# Local 9:00 a.m. Publisher

Created: 2026-09-03

## Purpose

GitHub Actions scheduled workflows are best-effort and can start late. The local publisher makes the Mac the primary clock for the daily Unofficial DC evergreen post, while GitHub Actions remains the cloud fallback.

## How It Works

- `scripts/run_local_publish.sh` loads private secrets from `.env`, runs `post_today.py`, writes logs, and commits/pushes the local `posted/YYYY-MM-DD.md` ledger file after a successful real publish.
- `scripts/install_local_launchd.sh` installs a macOS LaunchAgent.
- launchd tries at 9:00, 9:05, 9:15, and 9:30 a.m. local time.
- Duplicate posts are prevented by Notion: after a row is marked `Posted`, later retry runs find no `Scheduled` row for that date.

## Required Local `.env`

Create `/Users/clawagent/Documents/ChatGPT/UDC - Drumbeat Posts/.env` with:

```bash
NOTION_TOKEN=
NOTION_DATABASE_ID=231e4d25992845e3a610b9f4c65f0357
META_ACCESS_TOKEN=
FB_PAGE_ACCESS_TOKEN=
IG_USER_ID=
FB_PAGE_ID=
DRY_RUN=0
ALLOW_PARTIAL=0
PLATFORMS_OVERRIDE=
```

`FB_PAGE_ACCESS_TOKEN` can be blank if `META_ACCESS_TOKEN` works for Facebook Page publishing too.

## Install

```bash
chmod +x scripts/run_local_publish.sh scripts/install_local_launchd.sh
./scripts/install_local_launchd.sh
```

## Test Without Posting

Set `DRY_RUN=1` in `.env`, then run:

```bash
scripts/run_local_publish.sh
tail -n 80 logs/local-publish.log
```

Set `DRY_RUN=0` again before relying on the live scheduler.

## Operational Notes

- The Mac must be awake and online for exact local publishing.
- If the Mac is asleep at 9:00, launchd may run when it wakes, but that is still best-effort.
- GitHub Actions remains useful as a fallback if the Mac is offline.
- The `posted/` folder is the local ledger for real publishes.
