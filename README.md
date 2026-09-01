# Unofficial DC — Evergreen Drumbeat Runner

A dumb runner. Every morning it finds today's row in the Notion calendar, posts it to
Instagram + the Unofficial DC Facebook Page, marks the row Posted, saves a copy of the
post into `posted/` in this repo (own the data, rent the tools), and pings Telegram.

No agents. No handoffs. If it fails, the row is marked **Failed** with the reason and
Telegram tells you. Nothing dies silently.

The runner is `scripts/run.py`, wired up as the `.github/workflows/drumbeat.yml`
GitHub Actions workflow. Steps 1, 2, 5, 6, 7 below are already built — what's left is
the Notion database, the content, and the one-time Meta + GitHub setup.

---

## Who does what

**An agent (Claude Code / Cowork) can do:** steps 1, 2, 5, 6, 7.
**Only Kevin can do:** step 3 (Meta token) and step 4 (GitHub secrets) — they require
logging in as you. About 15 minutes total, once.

---

## 1. Notion database — "UDC Evergreen Calendar"

Create a database in the Unofficial DC Open Brain (Operations Layer) with exactly these
properties (names matter — the script reads them by name):

| Property   | Type          | Notes |
|------------|---------------|-------|
| Name       | Title         | short label, e.g. "Day 12 — Baldwin quote" |
| Date       | Date          | the day it should post |
| Image      | Files & media | the finished graphic (upload it here) |
| Caption    | Text          | the post copy |
| Hashtags   | Text          | hashtag set (appended after two line breaks) |
| Platforms  | Multi-select  | options: `Instagram`, `Facebook` (blank = both) |
| Status     | Select        | options: `Scheduled`, `Posted`, `Posted (partial)`, `Failed`, `Skipped` |
| Post URL   | URL           | filled by the runner |
| Log        | Text          | filled by the runner |

Then: Share the database with your Notion integration (••• → Connections → add it).
Copy the database ID from the URL (the 32-char string before `?v=`).

**Kevin's weekly job:** open the calendar view once. Skip a row by setting Status to
`Skipped`. Swap one by editing it. Or touch nothing. Whatever is `Scheduled` on a given
date goes out that morning.

## 2. Load the content

Source: `UnofficialDC_Love_Content_Calendar.xlsx` (Google Drive, built March 2026).
One row per post. Shift dates forward starting from the go-live date. Attach the
finished image to each row. If the sheet only *specifies* the image (Canva prompt,
background note) rather than containing it, the image has to be made first — do a
week's worth at a time in Canva, not the whole run.

## 3. Meta access token (Kevin only)

The Instagram Business account must be linked to the Facebook Page (it is).

1. https://developers.facebook.com → My Apps → Create App → type **Business**.
2. Add product **Instagram** (Instagram API with Facebook Login) and **Facebook Login for Business**.
3. Easiest durable token: **Business Settings → System Users → Add** (Admin) →
   **Assign Assets**: the Facebook Page (full control) and the app →
   **Generate New Token** with scopes:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `pages_manage_posts`, `business_management`.
   System-user tokens don't expire on a 60-day clock.
4. Get IDs: `GET https://graph.facebook.com/v21.0/me/accounts?access_token=TOKEN`
   → the Page's `id` is **FB_PAGE_ID**. Then
   `GET https://graph.facebook.com/v21.0/{FB_PAGE_ID}?fields=instagram_business_account&access_token=TOKEN`
   → that `id` is **IG_USER_ID**.

Note: while the app is in Development mode it can only post for accounts with a role
on the app; that's fine because it's your own accounts. No App Review needed.

## 4. GitHub (Kevin only)

1. This repo (`udc-drumbeat`) is already private with the runner pushed to it.
2. Settings → Secrets and variables → Actions → New repository secret, for each:
   `NOTION_TOKEN`, `NOTION_DATABASE_ID`, `META_ACCESS_TOKEN`, `IG_USER_ID`, `FB_PAGE_ID`,
   and optionally `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (same bot Hermes uses is fine).

## 5. Test without posting

Actions → **UDC Evergreen Drumbeat** → Run workflow → set `dry_run` = `1`.
The log should show it found today's row and printed the caption.

You can also run it locally:

```
pip install -r requirements.txt
NOTION_TOKEN=... NOTION_DATABASE_ID=... python scripts/run.py --dry-run
```

## 6. First real post

Put one row on today's date, Status = Scheduled. Run workflow with `dry_run` = `0`.
Check Instagram, the Facebook Page, the Notion row (Posted + URL), and `posted/YYYY-MM-DD.md`.

## 7. Leave it alone

It fires at 9 AM Eastern daily (the workflow runs at both 13:00 and 14:00 UTC to cover
EDT/EST; whichever run finds the row still `Scheduled` does the posting, the other finds
nothing left to do). Telegram tells you what happened. `posted/` is the permanent record
and can be mirrored to the NAS with one rsync line whenever the NAS is ready — the NAS
is a backup destination, never a dependency.

---

## How it works

`scripts/run.py`:

1. Queries the Notion database for a row with today's `Date` (America/New_York) and
   `Status = Scheduled`.
2. If none, logs it and pings Telegram — exits cleanly.
3. Otherwise builds the caption (`Caption` + two line breaks + `Hashtags`) and posts the
   row's `Image` to each platform in `Platforms` (Instagram via the Content Publishing
   API, Facebook via a Page photo post).
4. Writes the outcome back to the row: `Status` (`Posted` / `Posted (partial)` /
   `Failed`), `Post URL`, `Log`.
5. Saves a Markdown copy of the post to `posted/YYYY-MM-DD.md` and commits it.
6. Sends a Telegram summary either way.

A row with no `Image` attached, a Meta API error, or missing secrets all end in
`Failed` + a Telegram alert with the reason — never a silent no-op.

---

## Next build on the same skeleton

`Creative Queue` runner: same repo, second workflow, reads rows with Status =
`Requested`, calls the Claude API with the brief + Brand Guardian rules, writes 3–4
options back, flips to `Options Ready`, pings Telegram. Unpicked options go to
`Parking Lot`. Don't start it until this one has run two weeks clean.
