from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "assets" / "generated" / "2026-09-visual-prep"
OUT_DIR = ROOT / "assets" / "generated" / "2026-09-motion-prep"
FFMPEG = "/opt/homebrew/bin/ffmpeg"
W, H = 1080, 1920
FPS = 24
DURATION = 15
FRAMES = FPS * DURATION


@dataclass(frozen=True)
class Spec:
    name: str
    source: Path
    output: Path
    mode: str


SPECS = [
    Spec(
        name="National Mall",
        source=SRC_DIR / "2026-09-08-national-mall-wordless.png",
        output=OUT_DIR / "2026-09-08-national-mall-short-v2.mp4",
        mode="mall",
    ),
    Spec(
        name="Cherry Blossoms",
        source=SRC_DIR / "2026-09-11-cherry-blossom-logo-wordless.png",
        output=OUT_DIR / "2026-09-11-cherry-blossom-logo-short-v2.mp4",
        mode="blossom",
    ),
    Spec(
        name="Go-Go Drummers",
        source=SRC_DIR / "2026-09-16-gogo-drummers-wordless.png",
        output=OUT_DIR / "2026-09-16-gogo-drummers-short-v2.mp4",
        mode="gogo",
    ),
]


def ease(t: float) -> float:
    return 0.5 - 0.5 * math.cos(math.pi * t)


def cover_crop(img: Image.Image, size: tuple[int, int], scale: float = 1.0, ox: float = 0, oy: float = 0) -> Image.Image:
    target_w, target_h = size
    ratio = max(target_w / img.width, target_h / img.height) * scale
    resized = img.resize((round(img.width * ratio), round(img.height * ratio)), Image.Resampling.LANCZOS)
    max_x = max(0, resized.width - target_w)
    max_y = max(0, resized.height - target_h)
    x = int(max_x / 2 + ox * max_x / 2)
    y = int(max_y / 2 + oy * max_y / 2)
    return resized.crop((x, y, x + target_w, y + target_h))


def contain_square(img: Image.Image, size: int, scale: float) -> Image.Image:
    final = round(size * scale)
    return img.resize((final, final), Image.Resampling.LANCZOS)


def draw_heart(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, fill: tuple[int, int, int, int]) -> None:
    pts = []
    for i in range(60):
        a = math.pi * 2 * i / 60
        px = 16 * math.sin(a) ** 3
        py = -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((x + px * size / 32, y + py * size / 32))
    draw.polygon(pts, fill=fill)


def draw_note(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, fill: tuple[int, int, int, int]) -> None:
    stem_h = size * 1.35
    draw.ellipse((x, y, x + size * 0.55, y + size * 0.42), fill=fill)
    draw.rounded_rectangle((x + size * 0.45, y - stem_h, x + size * 0.58, y + size * 0.15), radius=3, fill=fill)
    draw.arc((x + size * 0.48, y - stem_h, x + size * 1.15, y - stem_h * 0.48), 190, 355, fill=fill, width=max(2, round(size * 0.08)))


def overlay_glow(frame: Image.Image, cx: int, cy: int, color: tuple[int, int, int], strength: float) -> None:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for r, alpha in [(440, 18), (280, 28), (150, 42)]:
        a = round(alpha * strength)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*color, a))
    frame.alpha_composite(layer)


def base_frame(src: Image.Image, t: float) -> Image.Image:
    bg = cover_crop(src, (W, H), scale=1.22, ox=-0.55 + 1.1 * t, oy=-0.15 + 0.22 * math.sin(t * math.tau))
    bg = bg.filter(ImageFilter.GaussianBlur(24))
    bg = ImageEnhance.Color(bg).enhance(1.08)
    bg = ImageEnhance.Brightness(bg).enhance(0.72)
    frame = bg.convert("RGBA")

    card_scale = 0.96 + 0.10 * ease(t)
    card = contain_square(src, 1015, card_scale).convert("RGBA")
    card = ImageEnhance.Contrast(card).enhance(1.04)
    x = (W - card.width) // 2 + round(24 * math.sin(t * math.tau * 0.9))
    y = 380 + round(34 * math.sin(t * math.tau * 0.6 + 0.8))

    shadow = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((0, 0, card.width, card.height), radius=42, fill=(0, 0, 0, 82))
    frame.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)), (x + 8, y + 22))
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, card.width, card.height), radius=36, fill=255)
    masked = Image.new("RGBA", card.size, (0, 0, 0, 0))
    masked.paste(card, (0, 0), mask)
    frame.alpha_composite(masked, (x, y))
    return frame


def mall_layer(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    overlay_glow(layer, round(165 + 760 * t), 330, (255, 190, 82), 0.75)
    for i in range(42):
        phase = (t + i * 0.037) % 1
        x = 70 + (i * 223 % 940) + 52 * math.sin(phase * math.tau + i)
        y = 1680 - phase * 1370
        r = 2 + (i % 4)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(255, 218, 140, 70 + (i % 3) * 25))
    return layer


def blossom_layer(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for i in range(80):
        phase = (t * 0.92 + i * 0.017) % 1
        x = (i * 137 % 1180) - 50 + 95 * math.sin(phase * math.tau * 1.4 + i * 0.6)
        y = -130 + phase * 2180
        rx = 10 + (i % 5) * 3
        ry = 5 + (i % 4) * 2
        color = (255, 184 + (i % 3) * 18, 205 + (i % 2) * 22, 108)
        draw.ellipse((x - rx, y - ry, x + rx, y + ry), fill=color)
    shimmer_x = round(170 + 740 * ((t * 1.25) % 1))
    draw.line((shimmer_x, 445, shimmer_x - 210, 1365), fill=(255, 255, 255, 72), width=16)
    return layer.filter(ImageFilter.GaussianBlur(0.35))


def gogo_layer(t: float) -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    pulse = 0.5 + 0.5 * math.sin(t * math.tau * 8)
    for i in range(9):
        r = 60 + i * 46 + pulse * 28
        alpha = max(0, 105 - i * 10)
        draw.ellipse((W / 2 - r, 1160 - r, W / 2 + r, 1160 + r), outline=(230, 36, 48, alpha), width=6)
    for i in range(22):
        phase = (t * 1.6 + i * 0.053) % 1
        x = 90 + (i * 179 % 900) + 42 * math.sin(phase * math.tau)
        y = 1550 - phase * 880
        size = 38 + (i % 4) * 12
        if i % 3 == 0:
            draw_heart(draw, x, y, size, (230, 36, 48, 118))
        else:
            draw_note(draw, x, y, size, (255, 203, 88, 118))
    return layer


def render(spec: Spec) -> None:
    src = Image.open(spec.source).convert("RGB")
    spec.output.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [
            FFMPEG,
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{W}x{H}",
            "-r",
            str(FPS),
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(spec.output),
        ],
        stdin=subprocess.PIPE,
    )
    assert proc.stdin is not None
    for n in range(FRAMES):
        t = n / (FRAMES - 1)
        frame = base_frame(src, t)
        if spec.mode == "mall":
            frame.alpha_composite(mall_layer(t))
        elif spec.mode == "blossom":
            frame.alpha_composite(blossom_layer(t))
        elif spec.mode == "gogo":
            frame.alpha_composite(gogo_layer(t))
        proc.stdin.write(np.asarray(frame.convert("RGB"), dtype=np.uint8).tobytes())
    proc.stdin.close()
    code = proc.wait()
    if code:
        raise RuntimeError(f"ffmpeg failed for {spec.output} with exit code {code}")
    print(spec.output)


def main() -> None:
    for spec in SPECS:
        render(spec)


if __name__ == "__main__":
    main()
