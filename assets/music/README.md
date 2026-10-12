# Optional music bed

By default, the runner renders silent videos. To add music, put ONE royalty-free track here named
`bed.mp3` (15 seconds or longer; the runner cuts it to CLIP_SECONDS and fades it out).
Put the license next to it as `bed-LICENSE.txt` with:
the track title, the artist, where it was downloaded, the license name, the date, and the
attribution line if the license requires one (if it does, add that line to the caption in
`caption_for()` in dc_untold_daily.py).

Why a file and not the Instagram/TikTok music picker: in-app music only exists when you post by
hand. Anything posted through the API has to carry its own audio.

Pick a track that is cleared for commercial social use with no attribution required if possible.
Do not use a go-go track unless its license is explicit. One track, reused every day, is enough
for version one; swap it later without touching code.
