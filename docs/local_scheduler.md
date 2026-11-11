# Daily evergreen publisher

Updated and verified: 2026-11-11, America/New_York.

## Schedule and runtime

The Mac is the primary publisher at 09:00 Eastern, with checks at 09:05, 09:15,
and 09:30. Its private runtime is `~/Library/Application Support/UDC Drumbeat`.
The Mac must be awake, signed in, and online. The launchd job was tested using
both a background dry run and an actual two-platform publish on November 11.

Install or update it from the checkout with `bash scripts/install_local_launchd.sh`.
The installer copies code and the private `.env` into Application Support, creates
its own virtual environment, and loads `com.unofficialdc.drumbeat.local-publish`.
The runtime directory is mode 700; `.env` is mode 600 and excluded from git.
Rerun the installer after code or credential changes in the checkout.

The former Documents-based local job failed with macOS `Operation not permitted`
and exit 126. The separate local GitHub-dispatch bridge is now disabled. Neither
job should be restored using the old installer.

GitHub's native schedule is the power-outage backup. It checks at 14:15 and
15:15 UTC and skips checks before 10:00 Eastern. One eligible check is 10:15
in both standard and daylight time. GitHub can delay scheduled execution.

## Calendar and approved content

[UDC Evergreen Calendar](https://www.notion.so/231e4d25992845e3a610b9f4c65f0357)
contains the plan, status, Post URL, and Log (both platform links).

`evergreen_queue.py` maintains today plus 13 future days using the eight existing
approved static images and captions in `data/approved_evergreen.json`. Assets
repeat every eight days; National Mall, Go-Go, and the blossom design are mixed
with the five quote designs. Add approved material to the library and ORDER to
expand the rotation. This does not create new animations or DC Untold episodes.

Only missing dates are filled. Existing planned, posted, skipped, and failed rows
are preserved. Old September rows remain historical. There is no automatic
backlog flood. Calendar rows can be edited in Notion before publication.

The refill also uses a shared daily claim. If a refill times out, inspect Notion
and `refills/YYYY-MM-DD.json` before retrying, because creation may have succeeded.

## Shared duplicate protection and receipts

The `drumbeat-state` branch in `going2places-stack/udc-drumbeat` is the shared
ledger. The local job authenticates with the existing gh login; GitHub uses its
workflow token with contents:write. No access tokens are written into receipts.

- `claims/YYYY-MM-DD.json`: create-only daily publish claim and per-platform URLs.
- `runs/YYYY-MM-DD.json`: latest explicit outcome, check time, and links.
- `refills/YYYY-MM-DD.json`: rolling-calendar maintenance receipt.

Creating the daily claim is atomic. Only the winning runner may call the publishing
APIs. Each verified platform permalink is saved immediately. Both URLs are also
written to Notion's Log; Post URL displays the first one.

The claim is never automatically deleted or reclaimed. If a platform times out,
a receipt cannot be saved, or only one platform succeeds, automated publication
stops for review. This favors avoiding duplicates over blind retries. If GitHub's
shared ledger is unavailable, local publication also stops safely.

Partial retries are disabled, including the old `allow_partial=1` input. To recover,
inspect both platforms and the shared receipt first; reconcile known IDs/URLs and
manually complete only a confirmed missing platform. Do not delete a claim just
because a job failed. A completed claim can repair a failed Notion status update
without posting again.

## Outcomes and notifications

- PUBLISHED: requested platforms returned posts and their links were read back.
- ALREADY_POSTED: prior receipts exist; this run made no new posts.
- NOTHING_SCHEDULED: no calendar row; nonzero exit, not a publishing success.
- FAILED / NEEDS_REVIEW: no full confirmed success; inspect any saved partial URLs.
- DRY_RUN: no publishing, shared-state writes, or calendar writes.

GitHub includes an explicit job summary and downloadable receipt artifact. Local
reports are in the runtime's `runs/`, `posted/`, and `logs/` directories. macOS
notifications are attempted for changed actionable outcomes, subject to notification
settings. Telegram is used only where its credentials are configured. Unchanged
retry reports are suppressed, and ALREADY_POSTED does not send a Telegram alert.

## Checks performed on November 11

Automated tests cover dry-run safety, empty queues, claim collisions, interrupted
publishing, saved platform receipts, Notion failures, notification failures, and
credential redaction. A real shared-ledger collision test rejected the second
runner. Background dry-run exit was 0. Today's live post returned verified
Instagram and Facebook links; the cloud no-duplicate check is recorded in the
Open Brain recovery note.
