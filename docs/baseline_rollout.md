# Love baseline rollout

Status recorded November 11, 2026, America/New_York.

Review home: https://www.notion.so/41518f4229e98162b9b1ca1c66d977f4

Content bank: https://www.notion.so/c28cf095e085400abaf257f2b893bd0d

Private review folder: https://drive.google.com/drive/folders/1PvVnJcyzlWoVtNyfl93yMbu4zGxL6tEQ

## Prepared

- Thirty original-message drafts in `data/baseline_month.json` and CSV, with eight destination-specific captions. All content and asset approval flags remain false. The new Notion bank's entries are Needs review and have no live calendar dates.
- Three static feed masters, vertical masters, and twelve-second music videos under `assets/generated/2026-11-baseline-review/`. The combined `three-sample-review.mp4` is a 36-second review reel. Sources are generated illustrations, not real business photographs or endorsements.
- `scripts/render_baseline_samples.py` preserves master files and recreates videos using the existing music bed and license record. Videos technically checked: 1080x1920 H.264, AAC 48 kHz stereo, twelve seconds each, full decoding, no clipping. Subjective user review of music and movement is pending.
- `brand_defaults.py` normalizes the default #UnofficialDC and #LoveIsTheNorthStar tags; thirteen upcoming Notion calendar rows were updated.
- Four old quote graphics held pending attribution reconciliation. Seven future calendar rows switched to existing approved wordless DC assets. Refill bypasses held library entries. Historical posts preserved.
- The recovered 55-entry June queue and gap analysis are in `data/recovered/`. They document an incomplete 180-day target, not six months of finished assets.

## Destination limits

Instagram and Facebook Page feeds retain the existing daily local/cloud publisher and shared claims. Story publication is implemented separately in `story_publisher.py` and `scripts/publish_story.py`; it defaults to dry run and requires both content and asset approval. Separate destination claims and actual returned URLs protect against duplicate Story publication. Story read access and unit behavior were tested; live publication and recurring scheduling are not enabled.

TikTok's owner session and LinkedIn Page admin access were confirmed. Threads currently has the Good Word Game account, and YouTube Studio needs sign-in. No additional recurring API publishing connections are configured. See `data/destination_status.json` for observed account details. A signed-in browser alone is not automation.

## Continue

Review the first three samples before expanding the new visual style. Review the month of copy, finish remaining artwork, and preserve license records. Drive review links are private and cannot be used as public media endpoints. After approval, prepare public publishing assets deliberately, pilot each destination with a verified URL, then enable its recurring schedule. Do not retry an uncertain outcome or erase a shared claim without reconciliation.

Tests: `./.venv/bin/python -m unittest discover -s tests -v` (24 passed on November 11).
