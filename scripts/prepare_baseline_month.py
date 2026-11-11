"""Reproducible first-month copy bank; review does not imply scheduling."""
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from brand_defaults import brand_hashtags

ITEMS = [
    ("Love lives next door.", "Neighborhood", "A little neighborly Love belongs in every day.", "Warm brick rowhouses, stoops and welcoming windows.", "New original UDC draft"),
    ("Make room for Love.", "Love reminder", "A little room. A little patience. A little more Love.", "Cobalt and terracotta woven-paper ribbons.", "New original UDC draft"),
    ("A little Love goes a long way.", "Local business", "For the people who open up, show up, and keep the neighborhood going. Love and Support.", "Illustrated corner shop and open door; no real business name.", "New original UDC draft"),
    ("Keep it real. Keep it Love.", "Love reminder", "Just a small reminder to carry into your day.", "Bold warm-red type on charcoal with tactile print grain.", "EVG-032 / existing original"),
    ("Showing up is a kind of Love.", "Community", "The small ways we show up for each other matter.", "Soft overlapping ochre and plum paper shapes.", "Adapted from EVG-037 / original UDC"),
    ("Let kindness set the tone.", "Love reminder", "A softer start can change the whole day. Lead with Love.", "Warm cream, sage and peach wash; generous space.", "New original UDC draft"),
    ("Love your block first.", "Neighborhood", "A wave. An open door. A little Love for the place you call home.", "Evening rowhouse windows, amber and midnight blue.", "EVG-046 / recovered expansion draft"),
    ("There is room for you here.", "Community", "Belonging starts with making room. A little Love from Unofficial DC.", "Layered color arcs opening toward the center.", "New original UDC draft"),
    ("Small gestures. Real Love.", "Love reminder", "It doesn't have to be a grand gesture to mean something.", "Coral and ink-blue hand-printed texture.", "New original UDC draft"),
    ("Carry a little Love with you.", "Love reminder", "Wherever the day takes you, take a little Love along.", "Flowing fabric texture in rust, lilac and cream.", "New original UDC draft"),
    ("Our rhythm. Our city. Our Love.", "Culture", "For the music, the movement, and the people who keep DC feeling like DC.", "Original illustrated neighborhood music scene, no real performers.", "Inspired by EVG-015 / original visual concept"),
    ("Love can be quiet, too.", "Love reminder", "A little patience. A little understanding. A little Love.", "Quiet indigo paper grain and a soft amber wash.", "New original UDC draft"),
    ("Make someone's day a little lighter.", "Community", "A kind word can travel farther than you think. Send a little Love.", "Open pale-yellow and warm-red shapes.", "New original UDC draft"),
    ("My city. Your city. Our city.", "Neighborhood", "Different stories. Shared streets. DC Love.", "Neighborhood brick, painted doors and street-tree textures.", "EVG-040 / recovered expansion draft"),
    ("Love is worth the extra moment.", "Love reminder", "Pause long enough to notice someone. That's a good place to start.", "Slow blue-to-plum color fields and tactile weave.", "New original UDC draft"),
    ("Warmth is something we can give.", "Community", "A small reminder that a little Love can make a place feel different.", "Golden orange and cream letterpress texture.", "New original UDC draft"),
    ("Give your neighborhood some Love.", "Local business", "For the familiar faces behind the counter and the places that feel like ours.", "Fictional neighborhood storefront with flowers, no business endorsement.", "Inspired by EVG-048 / original visual concept"),
    ("More understanding. More Love.", "Love reminder", "We don't have to be the same to treat each other with Love.", "Intersecting teal and terracotta translucent textures.", "New original UDC draft"),
    ("Good things grow with care.", "Love reminder", "A little care, given consistently. That's Love in practice.", "Sage, warm pink and hand-printed organic patterns.", "New original UDC draft"),
    ("Leave a little kindness behind.", "Community", "A warm word. A thoughtful gesture. A little Love that stays.", "Soft peach, charcoal and cream paper marks.", "New original UDC draft"),
    ("For the everyday DC we Love.", "Neighborhood", "The stoops, the corner shops, the familiar faces. Our city, every day.", "Residential corner at dusk; avoid postcard landmarks.", "New original UDC draft"),
    ("Love doesn't need a special occasion.", "Love reminder", "An ordinary day is a good day for a little Love.", "Bold ultramarine and orange woven-paper composition.", "New original UDC draft"),
    ("Choose a little more grace today.", "Love reminder", "For yourself, for your neighbor, for the person whose day you don't know. Love.", "Cream and burgundy flowing fabric texture.", "New original UDC draft"),
    ("A city feels like home through its people.", "Community", "Here's to the people who make the everyday feel familiar. DC Love.", "Original illustrated neighborhood greeting; nonidentifiable adults.", "New original UDC draft"),
    ("Let Love be part of the ordinary.", "Love reminder", "Not just the big moments. The little ones, too.", "Muted lavender, warm coral and tactile paper grain.", "New original UDC draft"),
    ("There is strength in gentleness.", "Love reminder", "A little patience can hold a lot of Love.", "Deep teal, gold and quiet linen texture.", "New original UDC draft"),
    ("Love belongs on every block.", "Neighborhood", "From one neighbor to another. A little Love for all of DC.", "Illustrated rowhouse doors in varied colors and warm window light.", "New original UDC draft"),
    ("Connection starts with a small gesture.", "Community", "A hello is a good place to begin. Lead with Love.", "Two simple color ribbons meeting with generous negative space.", "New original UDC draft"),
    ("A little more heart in the everyday.", "Love reminder", "Nothing complicated. Just a little more Love in how we move through the day.", "Burnt orange and ink-blue screenprint texture.", "New original UDC draft"),
    ("Keep a little Love in the rhythm.", "Culture", "However your day moves, make room for Love along the way.", "Warm abstract rhythm marks inspired by music; no copied performance.", "New original UDC draft"),
]


def build():
    records = []
    for day, (message, theme, caption, visual, source) in enumerate(ITEMS, 1):
        tags = brand_hashtags("#WashingtonDC #DCLove #CommunityLove")
        records.append({
            "content_id": f"UDC-BASE-{day:03d}", "day": day, "message": message,
            "theme": theme, "caption": caption, "hashtags": tags, "source": source,
            "visual_direction": visual, "status": "Needs review", "asset_status": "Needs artwork",
            "target_time": "09:00", "timezone": "America/New_York",
            "content_approval": False, "asset_approval": False,
            "variants": {
                "Instagram": caption + "\n\n" + tags,
                "Facebook": caption + "\n\n" + brand_hashtags("", 2),
                "Threads": message + "\n\n" + caption + "\n\n#UnofficialDC",
                "LinkedIn": caption + "\n\nA small reminder of the Love at the heart of Unofficial DC.\n\n" + brand_hashtags("", 2),
                "TikTok": caption + "\n\n" + tags,
                "YouTube Shorts": {"title": message + " | Unofficial DC", "description": caption + "\n\n" + tags},
                "Instagram Story": message, "Facebook Story": message,
            },
            "assets": {"feed_url": None, "story_image_url": None, "video_url": None},
        })
    return records


if __name__ == "__main__":
    records = build()
    (ROOT / "data/baseline_month.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    with (ROOT / "data/baseline_month.csv").open("w", newline="") as handle:
        keys = ["content_id", "day", "message", "theme", "caption", "hashtags", "source", "status", "asset_status"]
        writer = csv.DictWriter(handle, keys, extrasaction="ignore")
        writer.writeheader(); writer.writerows(records)
    print(f"Prepared {len(records)} distinct original-message drafts. No posts scheduled.")
