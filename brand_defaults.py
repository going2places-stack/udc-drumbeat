"""Shared, case-insensitive brand tags for every evergreen caption."""
REQUIRED_TAGS = ("#UnofficialDC", "#LoveIsTheNorthStar")


def brand_hashtags(value, limit=5):
    tags = list(REQUIRED_TAGS)
    seen = {tag.casefold() for tag in tags}
    for tag in value.split():
        if tag.startswith("#") and tag.casefold() not in seen:
            tags.append(tag)
            seen.add(tag.casefold())
    return " ".join(tags[:limit])
