"""Render review-only music clips from the generated feed/Story artwork.

Full message -> illustration detail -> full message; immutable image masters.
Run with bundled Python (Pillow + numpy) and local ffmpeg. No external upload.
"""
from pathlib import Path
import json
import math
import subprocess

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/generated/2026-11-baseline-review"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
W, H, FPS, SECONDS = 1080, 1920, 24, 12
SPECS = [("01-neighborhood", 0, .67), ("02-texture", 18, .66), ("03-corner-shop", 40, .65)]


def frame(source, t, detail_y):
    # The authored still has generous 9:16 safe areas. Only the artwork moves.
    full = (1.0 + .025 * math.sin(math.pi * t / SECONDS), .5)
    detail = (1.30 + .05 * max(0, min(1, (t - 4) / 4)), detail_y)
    def view(spec):
        zoom, cy = spec
        scale = max(W / source.width, H / source.height) * zoom
        sw, sh = round(source.width * scale), round(source.height * scale)
        image = source.resize((sw, sh), Image.Resampling.LANCZOS)
        left = (sw - W) // 2
        top = round((sh - H) * cy)
        return image.crop((left, top, left + W, top + H))
    a = view(full)
    if 4 <= t < 8:
        return view(detail)
    # A brief transition into detail and back, authored inside the 12-second clip.
    if 3.5 <= t < 4:
        return Image.blend(a, view(detail), (t - 3.5) / .5)
    if 8 <= t < 8.5:
        return Image.blend(view(detail), a, (t - 8) / .5)
    return a


def run(args):
    subprocess.run([FFMPEG, "-nostdin", "-v", "error", "-y", *map(str, args)],
                   check=True, capture_output=True)


def render(key, audio_offset, detail_y):
    source_path = OUT / (key + "-vertical.png")
    source = Image.open(source_path).convert("RGB")
    picture = OUT / (key + "-picture.mp4")
    result = OUT / (key + "-music-review.mp4")
    command = [FFMPEG, "-nostdin", "-v", "error", "-y", "-f", "rawvideo",
        "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart", str(picture)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for index in range(FPS * SECONDS):
            process.stdin.write(frame(source, index / FPS, detail_y).tobytes())
        process.stdin.close()
        error = process.stderr.read()
        if process.wait(): raise RuntimeError(error.decode()[-1500:])
    except BaseException:
        process.kill(); process.wait(); raise
    audio = OUT / (key + "-music.m4a")
    run(["-ss", audio_offset, "-i", ROOT / "assets/music/bed.mp3", "-af",
         "atrim=duration=12,asetpts=PTS-STARTPTS,afade=t=in:d=0.35,afade=t=out:st=11:d=1,loudnorm=I=-18:TP=-1.5:LRA=7",
         "-ar", "48000", "-ac", "2", "-c:a", "aac", "-b:a", "192k", audio])
    run(["-i", picture, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
         "-c", "copy", "-movflags", "+faststart", result])
    for second in (1, 5, 10):
        frame(source, second, detail_y).save(OUT / f"{key}-frame-{second}.jpg", quality=90)
    print(result, flush=True)
    return result


if __name__ == "__main__":
    outputs = [render(*spec) for spec in SPECS]
    listing = OUT / "review-concat.txt"
    listing.write_text("".join(f"file '{p.name}'\n" for p in outputs))
    run(["-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", "-movflags", "+faststart",
         OUT / "three-sample-review.mp4"])
    contact = Image.new("RGB", (1080, 640), "#181818")
    draw = ImageDraw.Draw(contact)
    for i, (key, _, _) in enumerate(SPECS):
        image = Image.open(OUT / (key + "-feed.png")).convert("RGB")
        image.thumbnail((350, 560), Image.Resampling.LANCZOS)
        contact.paste(image, (i * 360 + (360 - image.width)//2, 45))
        draw.text((i * 360 + 18, 15), f"{i+1:02d}  {key[3:]}", fill="white")
    contact.save(OUT / "sample-contact-sheet.jpg", quality=95)
    (OUT / "render-manifest.json").write_text(json.dumps({
        "review_only": True, "dimensions": [W, H], "fps": FPS, "seconds_per_clip": SECONDS,
        "music": "Calm Documentary Background — Universfield", "music_license": "assets/music/bed-LICENSE.txt",
        "music_offsets_seconds": [s[1] for s in SPECS], "narration": None,
        "visual_provenance": "AI-generated illustrative artwork; not documentary photography",
        "timeline": "0–4s full message; 4–8s closer artwork detail; 8–12s full message. 0.5s dissolves.",
        "outputs": [p.name for p in outputs]}, indent=2)+"\n")
