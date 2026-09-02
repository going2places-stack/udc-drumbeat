# Setup Status

Date: 2026-09-01

## Completed

- Created Notion database `UDC Evergreen Calendar`.
- Database URL: `https://app.notion.com/p/231e4d25992845e3a610b9f4c65f0357`
- GitHub `NOTION_DATABASE_ID`: `231e4d25992845e3a610b9f4c65f0357`
- Connector data source ID: `f93bccc4-474a-41dc-8c63-f71558e2ff3a`
- Read the local source calendar `UnofficialDC_Love_Content_Calendar.xlsx`.
- Found 38 real content rows in the `Content Calendar` sheet.
- Matched 5 finished quote images in Drive.
- Loaded 5 matched rows into Notion as `Scheduled`, dated 2026-09-02 through 2026-09-06.
- Added the daily GitHub Actions workflow and publishing scripts.

## Blocked By Credentials Or Account UI

- Meta app/system-user token creation still requires Facebook/Meta UI access and Kevin's approval where prompted.
- `META_ACCESS_TOKEN`, `FB_PAGE_ID`, and `IG_USER_ID` are still unknown.
- GitHub CLI is installed, but the local token for `going2places-stack` is invalid, so repo creation, push, and `gh secret set` are blocked until re-authentication.
- `NOTION_TOKEN` is still needed as a GitHub secret for Actions, even though the connected Notion app was sufficient for creating the database/rows in this session.

## Ready Backlog

Ready-to-go scheduled days: 5.

Remaining visual needs: 33 rows.
