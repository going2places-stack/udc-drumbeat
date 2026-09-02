# UDC Cross-Platform Motion Rollout

Created: 2026-09-02

## Goal

Extend the daily Unofficial DC drumbeat from reliable Instagram/Facebook static posts into a durable cross-platform rhythm that includes motion versions for YouTube Shorts and LinkedIn without weakening the current 9:00 a.m. publishing automation.

## Current State

- Instagram and Facebook Page image publishing are live through the Notion calendar and GitHub Actions.
- The daily scheduler runs at 9:00 a.m. Eastern and records platform URLs/errors in the local `posted/` archive.
- The publish-ready Drive folder is `UDC Drumbeat Publish Images`.
- YouTube Studio was inspected read-only. The visible channel is `Unofficial_DC`, channel ID `UCyI3HkQu63XJ24pnXwkqFJQ`, and the dashboard exposes `Create`, `Upload videos`, and `Create post`.
- No YouTube or LinkedIn uploads have been made from this workflow yet.

## First Motion Assets

| Creative | Local File | Drive URL | Role |
| --- | --- | --- | --- |
| National Mall wordless short | `assets/generated/2026-09-motion-prep/2026-09-08-national-mall-short.mp4` | `https://drive.google.com/uc?export=download&id=1wVAlJxxHefrFmN-5AdmaIgcYKM8054D_` | First YouTube Shorts candidate |
| Cherry blossom logo short | `assets/generated/2026-09-motion-prep/2026-09-11-cherry-blossom-logo-short.mp4` | `https://drive.google.com/uc?export=download&id=1kItOr6no7xoB4CBI1XzHByG9rEBtI9_S` | Brand-forward motion candidate |
| Go-go drummers short | `assets/generated/2026-09-motion-prep/2026-09-16-gogo-drummers-short.mp4` | `https://drive.google.com/uc?export=download&id=1z92lHYrc9ODR5yndoqgF-ms6BF1UcN8e` | DC culture motion candidate |

All three exports are 1080x1920 H.264 MP4 files, 30 fps, 12 seconds, and silent.

## Platform Notes

- YouTube Shorts: Official YouTube guidance says square or vertical videos up to three minutes are categorized as Shorts when uploaded after October 15, 2024. These 12-second vertical MP4s fit that format.
- YouTube API: `videos.insert` can upload videos and set metadata, but it requires OAuth and uploaded videos from unverified API projects can be restricted to private viewing until the project passes Google's audit.
- LinkedIn API: Organic posts are supported through the Posts API. Personal posts use `w_member_social`; organization posts use `w_organization_social` and require the authenticated member to have a qualifying company Page role. Video posts require uploading a LinkedIn video asset first, then creating the post with the returned video URN.

## Recommended Next Move

1. Keep Instagram/Facebook static posting exactly as-is for reliability.
2. Manually publish or schedule the first three MP4s in YouTube Studio as a pilot batch, using adapted captions from the matching Instagram/Facebook rows.
3. Pick the LinkedIn destination before building API work: Kevin personal profile or an Unofficial DC organization page.
4. Add columns to the Notion calendar or create a companion ledger for YouTube URL, LinkedIn URL, video asset URL, platform status, and error notes.
5. Only automate YouTube/LinkedIn after one manual pilot proves the captions, cadence, destinations, and ledger shape.

## Needed From Kevin

- Review and approve the three motion MP4s.
- Confirm YouTube destination: `Unofficial_DC` / `UCyI3HkQu63XJ24pnXwkqFJQ`.
- Confirm LinkedIn destination: personal profile or Unofficial DC organization page.
- Choose audio policy: silent, YouTube Audio Library music, licensed ambient track, or voiceover.
- Confirm whether LinkedIn should receive every motion post or only the strongest DC/community pieces.

## Tool Roles

- Local ffmpeg: fast prototype motion exports and reliable format control.
- ChatGPT/ImageGen: generate stills and motion prompt concepts.
- Adobe Express/Firefly: polish brand-safe visual treatments and reusable design surfaces.
- Canva: useful for branded templates if the plugin is installed or used manually.
- CapCut: best for richer motion, music, captions, and platform-native exports when the post needs more than a subtle motion pass.
