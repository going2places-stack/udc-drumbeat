# UDC Visual Production Rollout

Created: 2026-09-02

## Goal

Keep the daily 9:00 a.m. Eastern scheduler reliable by producing publish-ready static assets first, then upgrading selected animated and wordless concepts into motion posts when the creative toolchain is available.

## Tool Roles

- ChatGPT/ImageGen: create first-pass square stills for wordless visuals, DC-rooted backgrounds, and concept frames for animated posts.
- Adobe Firefly: generate or refine more stylized backgrounds, brand-safe textures, and alternate visual treatments.
- Canva: apply brand-kit consistency, quote-card layouts, resizing, and quick feed polish when a template layer is useful.
- Adobe Express: available in this Codex session for template/design work and PDF export; use when a web-editable design surface is helpful.
- CapCut: assemble motion versions from finished stills, short video clips, or layered assets; use for Reels/Stories rather than the daily static scheduler.

## Recommended Rollout

1. Static-first production
   - Generate or source a square PNG.
   - Review for DC specificity, clean hands/faces, no unwanted text, no watermarks, and correct brand tone.
   - Upload the approved file to `UDC Drumbeat Publish Images`.
   - Add the Notion row only after the image has a public/direct URL.

2. Motion upgrade
   - Use the static image as the poster frame.
   - Create 6-10 seconds of subtle motion: slow push-in, falling petals, glowing hearts, light sweep, or music-note movement.
   - Export from CapCut as MP4 for Reels/Stories or as a square video if feed video is desired.
   - Keep a still PNG fallback in the scheduler.

3. Brand/template pass
   - Use Canva or Adobe Express only when the post needs quote text, logo placement, or a reusable branded layout.
   - Keep wordless visuals mostly wordless; captions carry the message.

## First Static Candidates

| Target Date | Type | Local File | Next Step |
| --- | --- | --- | --- |
| 2026-09-08 | Wordless Visual | `assets/generated/2026-09-visual-prep/2026-09-08-national-mall-wordless.png` | Approved by Kevin and scheduled in Notion |
| 2026-09-11 | Wordless Visual | `assets/generated/2026-09-visual-prep/2026-09-11-cherry-blossom-logo-wordless.png` | Approved by Kevin and scheduled in Notion |
| 2026-09-16 | Wordless Visual | `assets/generated/2026-09-visual-prep/2026-09-16-gogo-drummers-wordless.png` | Approved by Kevin and scheduled in Notion |

## Uploaded Candidate URLs

These files are in the `UDC Drumbeat Publish Images` Drive folder and verified as publicly fetchable `image/png` files.

| Target Date | Drive File ID | Direct Image URL |
| --- | --- | --- |
| 2026-09-08 | `1J9nxxdRd_zrPNp5ITh9uBu9wEl0nsvM8` | `https://drive.google.com/uc?export=download&id=1J9nxxdRd_zrPNp5ITh9uBu9wEl0nsvM8` |
| 2026-09-11 | `14GmXria4gDsSa44VAMyewHDss1cJunVq` | `https://drive.google.com/uc?export=download&id=14GmXria4gDsSa44VAMyewHDss1cJunVq` |
| 2026-09-16 | `1s1dNoe2gz81xuOcGRImna_AVFWjEiBFe` | `https://drive.google.com/uc?export=download&id=1s1dNoe2gz81xuOcGRImna_AVFWjEiBFe` |

## First Motion Exports

These are subtle vertical MP4 motion versions built from the approved stills. They are intended for YouTube Shorts, Instagram/Facebook Reels-style reuse, and future LinkedIn video testing, while the static PNGs remain the reliable daily scheduler fallback.

| Target Date | Local File | Drive File ID | Direct Video URL | Specs |
| --- | --- | --- | --- | --- |
| 2026-09-08 | `assets/generated/2026-09-motion-prep/2026-09-08-national-mall-short.mp4` | `1wVAlJxxHefrFmN-5AdmaIgcYKM8054D_` | `https://drive.google.com/uc?export=download&id=1wVAlJxxHefrFmN-5AdmaIgcYKM8054D_` | 1080x1920, H.264, 30 fps, 12s, no audio |
| 2026-09-11 | `assets/generated/2026-09-motion-prep/2026-09-11-cherry-blossom-logo-short.mp4` | `1kItOr6no7xoB4CBI1XzHByG9rEBtI9_S` | `https://drive.google.com/uc?export=download&id=1kItOr6no7xoB4CBI1XzHByG9rEBtI9_S` | 1080x1920, H.264, 30 fps, 12s, no audio |
| 2026-09-16 | `assets/generated/2026-09-motion-prep/2026-09-16-gogo-drummers-short.mp4` | `1z92lHYrc9ODR5yndoqgF-ms6BF1UcN8e` | `https://drive.google.com/uc?export=download&id=1z92lHYrc9ODR5yndoqgF-ms6BF1UcN8e` | 1080x1920, H.264, 30 fps, 12s, no audio |

## Motion Specs For First Three

### 2026-09-08 National Mall

- Motion: slow push-in toward the Washington Monument, subtle sky movement, gentle warm light bloom.
- Duration: 6-8 seconds.
- CapCut notes: add a very light cinematic zoom, no text overlay, keep caption in platform copy.

### 2026-09-11 Cherry Blossoms

- Motion: falling petals, soft parallax between logo and background, light shimmer on the logo edge.
- Duration: 6-8 seconds.
- CapCut notes: use logo as foreground layer if possible; keep the logo sharp and centered.

### 2026-09-16 Go-Go Drummers

- Motion: subtle camera push, pulsing heart/music-note accents, slight rhythmic light movement.
- Duration: 6-10 seconds.
- CapCut notes: keep motion tasteful; avoid making the scene look like a generic concert ad.

## Prompt Pattern

Use this structure for future ChatGPT/ImageGen or Firefly prompts:

```text
Square Instagram/Facebook post visual for Unofficial DC.
Scene: [specific DC place or cultural cue].
Subject: [main visual].
Style: premium editorial, realistic, warm, community-centered.
Composition: square crop, clear focal point, no text unless this is a quote card.
Palette: DC red, navy, white, warm gold, natural skin tones.
Avoid: watermarks, political signs, generic skyline, distorted landmarks, malformed hands, unreadable text.
```

## Scheduling Rule

Do not add generated visuals to the live Notion calendar until they are reviewed, uploaded to the publish-ready Drive folder, and verified as publicly fetchable by Meta.

## Motion Scheduling Rule

Do not auto-post video yet. Use the MP4s as reviewed creative candidates until the YouTube and LinkedIn destinations, captions, audio policy, and API access paths are confirmed.

## Motion V2 Direction

Kevin reviewed the first MP4 batch and correctly flagged that the motion was too subtle. V1 should be treated as superseded. V2 files use stronger, visible motion and are generated by `scripts/generate_motion_v2.py` so the animation style can be tuned and regenerated consistently.

| Target Date | Local File | Drive URL | Specs |
| --- | --- | --- | --- |
| 2026-09-08 | `assets/generated/2026-09-motion-prep/2026-09-08-national-mall-short-v2.mp4` | `https://drive.google.com/file/d/1k-kSKmE_rp_ICT98rpt3KK0kbLlBQQEw/view?usp=drivesdk` | 1080x1920, H.264, 24 fps, 15s, no audio |
| 2026-09-11 | `assets/generated/2026-09-motion-prep/2026-09-11-cherry-blossom-logo-short-v2.mp4` | `https://drive.google.com/file/d/19htPHf8niZBnnuZy_n0vweXt8ck3QibV/view?usp=drivesdk` | 1080x1920, H.264, 24 fps, 15s, no audio |
| 2026-09-16 | `assets/generated/2026-09-motion-prep/2026-09-16-gogo-drummers-short-v2.mp4` | `https://drive.google.com/file/d/1OZyOWonMIFoBriXibf9f2-MgouQnLC66/view?usp=drivesdk` | 1080x1920, H.264, 24 fps, 15s, no audio |
