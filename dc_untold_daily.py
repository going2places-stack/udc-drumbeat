#!/usr/bin/env python3
"""
DC Untold Daily Fact runner.

Runs every day. Each run:
  1. Reads existing facts from the Notion "DC Untold Facts" database (dedupe).
  2. Asks Claude (with web search) for ONE surprising, verifiable DC history fact.
  3. VERIFIES it: fetches the source URL and checks the quoted passage is actually there.
     If verification fails, the fact is saved as "Unverified" and NOTHING is posted.
  4. On posting days only: renders a 1080x1920 fact card, bakes a music bed in with ffmpeg,
     uploads the mp4 to Google Drive (public link = the URL Meta needs), posts it as an
     Instagram Reel and a Facebook Page video, records the result.
  5. Always: writes facts/YYYY-MM-DD.md into the repo (owned record) and a Notion row.
  6. Telegram message on every outcome, including "nothing posted today, here's why."

Kevin never has to act for a post to go out. He acts only to stop one:
  - set a Notion row's Status to "Skipped" before its posting day, or
  - set the repo variable PAUSE=1 to halt all posting (facts still get collected).

Environment (GitHub secrets / variables):
  ANTHROPIC_API_KEY          required
  NOTION_TOKEN               required (same integration as the drumbeat)
  NOTION_FACTS_DB_ID         required (the new DC Untold Facts database)
  META_ACCESS_TOKEN          required for posting (same system-user token as drumbeat)
  IG_USER_ID, FB_PAGE_ID     required for posting
  GDRIVE_SA_JSON             required for posting: full service-account JSON, one secret
  GDRIVE_FOLDER_ID           required for posting: Drive folder the mp4s land in
  TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID   optional
  POST_DAYS                  optional, default "Mon,Wed,Fri"
  PAUSE                      optional, "1" halts posting
  DRY_RUN                    optional, "1" does everything except upload/post/write
  CLAUDE_MODEL               optional, default below (Codex: verify current model id)
"""

import datetime as dt
import json
import os
import re
import subprocess
import sys
import textwrap
import time
import zoneinfo

import requests

# ---------------------------------------------------------------- config

ET = zoneinfo.ZoneInfo("America/New_York")
TODAY = dt.datetime.now(ET).date()
TODAY_S = TODAY.isoformat()

ENV = os.environ.get
DRY = ENV("DRY_RUN", "0") == "1"
RETRY_FAILED = ENV("RETRY_FAILED", "0") == "1"
PAUSED = ENV("PAUSE", "0") == "1"
POST_DAYS = {d.strip()[:3].title() for d in ENV("POST_DAYS", "Mon,Wed,Fri").split(",")}
IS_POST_DAY = TODAY.strftime("%a") in POST_DAYS

MODEL = ENV("CLAUDE_MODEL", "claude-sonnet-5")
NOTION_VERSION = "2022-06-28"
GRAPH = "https://graph.facebook.com/v21.0"

# Brand defaults. DC Untold uses the navy from the cover art; override via env if needed.
BG = ENV("CARD_BG", "#2B3B6E")
FG = ENV("CARD_FG", "#FFFFFF")
ACCENT = ENV("CARD_ACCENT", "#E95144")
FONT_BOLD = ENV("CARD_FONT_BOLD", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
FONT_REG = ENV("CARD_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
MUSIC = ENV("MUSIC_FILE", "assets/music/bed.mp3")
CLIP_SECONDS = int(ENV("CLIP_SECONDS", "15"))

ANGLES = ["DC UNTOLD", "Did You Know?", "DC Is More Than Politics"]

LOG_LINES = []


def first_existing(*paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return paths[0]


def log(msg):
    line = f"[{dt.datetime.now(ET).strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG_LINES.append(line)


def need(name):
    v = ENV(name)
    if not v:
        raise SystemExit(f"Missing required env: {name}")
    return v


# ---------------------------------------------------------------- notion

def notion_headers():
    return {
        "Authorization": f"Bearer {need('NOTION_TOKEN')}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def rt(s):
    return {"rich_text": [{"text": {"content": (s or "")[:1900]}}]}


def notion_existing_facts(limit=200):
    """Return (titles, tags) already in the facts DB, for dedupe."""
    db = need("NOTION_FACTS_DB_ID")
    url = f"https://api.notion.com/v1/databases/{db}/query"
    titles, tags = [], set()
    payload = {"page_size": 100, "sorts": [{"timestamp": "created_time", "direction": "descending"}]}
    while len(titles) < limit:
        r = requests.post(url, headers=notion_headers(), json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        for page in data.get("results", []):
            p = page["properties"]
            t = "".join(x["plain_text"] for x in p.get("Name", {}).get("title", []))
            if t:
                titles.append(t)
            for o in p.get("Tags", {}).get("multi_select", []):
                tags.add(o["name"].lower())
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return titles, tags


def notion_create_fact(fact, status, post_url=None, extra_log=""):
    db = need("NOTION_FACTS_DB_ID")
    props = {
        "Name": {"title": [{"text": {"content": fact["headline"][:200]}}]},
        "Fact": rt(fact["fact"]),
        "Takeaway": rt(fact.get("takeaway", "")),
        "Angle": {"select": {"name": fact.get("angle") or ANGLES[0]}},
        "Source URL": {"url": fact["source_url"]},
        "Source Quote": rt(fact.get("source_quote", "")),
        "Source Name": rt(fact.get("source_name", "")),
        "Tags": {"multi_select": [{"name": t[:100]} for t in fact.get("tags", [])[:8]]},
        "Era": rt(fact.get("era", "")),
        "Place": rt(fact.get("place", "")),
        "Date": {"date": {"start": TODAY_S}},
        "Access Date": {"date": {"start": TODAY_S}},
        "Status": {"select": {"name": status}},
        "Go Deeper": {"checkbox": False},
        "Log": rt(extra_log or "\n".join(LOG_LINES[-12:])),
    }
    if post_url:
        props["Post URL"] = {"url": post_url}
    if DRY:
        log(f"DRY: would create Notion row [{status}] {fact['headline']}")
        return None
    r = requests.post("https://api.notion.com/v1/pages", headers=notion_headers(),
                      json={"parent": {"database_id": db}, "properties": props}, timeout=30)
    if r.status_code >= 300:
        log(f"Notion create failed: {r.status_code} {r.text[:300]}")
        return None
    return r.json().get("url")


# ---------------------------------------------------------------- research

SYSTEM = """You are the researcher for DC Untold, a Washington, DC history series whose entire
reputation rests on the paper trail. You find ONE surprising, verifiable fact about DC history or
culture per request. Prefer overlooked people, neighborhoods, institutions, art, music, commerce,
traditions, inventions, architecture. Avoid federal-politics trivia and anything on the avoid list.

Hard rules:
- The fact must be supported by a specific, publicly reachable web page (library, archive, museum,
  university, government, established newspaper/magazine, reputable local history org). No Wikipedia
  as the source_url (you may use it to find leads, then cite what it cites).
- source_quote must be a VERBATIM passage of 15-40 words copied exactly from that page, that
  supports the fact. It will be machine-checked against the page. If you cannot find such a passage,
  pick a different fact.
- Never invent quotations, dates, or names. If unsure, choose a fact you are sure of.
- Output ONLY a JSON object, no prose, no markdown fences:
{"headline": "<= 70 chars, no clickbait",
 "fact": "the fact in 1-3 plain sentences, <= 60 words, suitable to display on a card",
 "takeaway": "one plain-language sentence on why it matters",
 "angle": one of ["DC UNTOLD","Did You Know?","DC Is More Than Politics"],
 "source_url": "https://...",
 "source_name": "publisher/archive name",
 "source_quote": "verbatim passage from the page",
 "tags": ["3-6 short subject tags, lowercase"],
 "era": "decade or year range",
 "place": "neighborhood or site in DC, if any"}"""


def research(existing_titles, existing_tags):
    try:
        import anthropic
    except ImportError:
        raise SystemExit("pip install anthropic")
    client = anthropic.Anthropic(api_key=need("ANTHROPIC_API_KEY"))
    avoid = "\n".join(f"- {t}" for t in existing_titles[:120])
    tag_list = ", ".join(sorted(existing_tags))[:1500]
    user = (f"Today is {TODAY_S}. Find one new fact.\n\nAlready covered (do not repeat these subjects):\n"
            f"{avoid or '- (none yet)'}\n\nSubject tags already used (vary away from these): {tag_list or '(none)'}")
    msg = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 8}],
        messages=[{"role": "user", "content": user}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise RuntimeError(f"No JSON in model output: {text[:300]}")
    fact = json.loads(m.group(0))
    for k in ("headline", "fact", "source_url", "source_quote"):
        if not fact.get(k):
            raise RuntimeError(f"Model output missing {k}")
    if fact.get("angle") not in ANGLES:
        fact["angle"] = ANGLES[0]
    return fact


# ---------------------------------------------------------------- verify

def _norm(s):
    s = s.lower()
    s = s.replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"').replace("\u2014", "-").replace("\u2013", "-")
    return re.sub(r"[^a-z0-9 ]+", " ", re.sub(r"\s+", " ", s)).strip()


def verify(fact):
    """Fetch the source and confirm the quote (or most of it) is really on the page."""
    url = fact["source_url"]
    if "wikipedia.org" in url:
        return False, "Wikipedia not accepted as source_url"
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0 (DC Untold research bot)"})
    except Exception as e:
        return False, f"fetch error: {e}"
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    ctype = r.headers.get("content-type", "")
    body = r.text
    if "pdf" in ctype or url.lower().endswith(".pdf"):
        try:
            import io
            from pypdf import PdfReader
            body = " ".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(r.content)).pages)
        except Exception as e:
            return False, f"pdf extract failed: {e}"
    else:
        body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S | re.I)
        body = re.sub(r"<[^>]+>", " ", body)
    page = _norm(body)
    quote = _norm(fact["source_quote"])
    words = quote.split()
    if len(words) < 8:
        return False, "quote too short to verify"
    if quote in page:
        return True, "exact quote found"
    # tolerate small transcription slips: any 8-word window of the quote found verbatim
    for i in range(0, len(words) - 7):
        if " ".join(words[i:i + 8]) in page:
            return True, "8-word window of quote found"
    return False, "quote not found on page"


# ---------------------------------------------------------------- render

def render_card(fact, out_png):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    bold_font = first_existing(
        FONT_BOLD,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    )
    reg_font = first_existing(
        FONT_REG,
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
    )
    f_small = ImageFont.truetype(bold_font, 44)
    f_body = ImageFont.truetype(bold_font, 64)
    f_meta = ImageFont.truetype(reg_font, 34)

    # top label
    d.text((90, 160), "DC UNTOLD", font=f_small, fill=ACCENT)
    d.rectangle([90, 230, 330, 238], fill=ACCENT)
    angle = (fact.get("angle") or "").upper()
    if angle and angle != "DC UNTOLD":
        d.text((90, 270), angle, font=f_meta, fill=FG)

    # body, wrapped by measured pixel width (max 900px), shrinking until it fits the block
    def wrap_px(text, font, max_w):
        lines, cur = [], ""
        for w in text.split():
            trial = (cur + " " + w).strip()
            if d.textlength(trial, font=font) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    body = fact["fact"].strip()
    size = 64
    while size >= 40:
        f_body = ImageFont.truetype(bold_font, size)
        lines = wrap_px(body, f_body, 900)
        line_h = int(size * 1.25)
        if len(lines) * line_h <= 1100:
            break
        size -= 4
    y = 460
    for ln in lines:
        d.text((90, y), ln, font=f_body, fill=FG)
        y += line_h

    # source + footer
    src = (fact.get("source_name") or "").strip()
    if src:
        d.text((90, 1660), "SOURCE", font=f_meta, fill=ACCENT)
        for ln in textwrap.wrap(src, 48)[:2]:
            d.text((90, 1705), ln, font=f_meta, fill=FG)
    d.text((90, 1800), "A production of Unofficial Monument Productions", font=f_meta, fill=FG)
    img.save(out_png)


def render_video(png, out_mp4):
    if not os.path.exists(MUSIC):
        raise SystemExit(f"Music bed not found at {MUSIC}. See assets/music/README.md")
    cmd = ["ffmpeg", "-y", "-loop", "1", "-i", png, "-i", MUSIC,
           "-t", str(CLIP_SECONDS), "-r", "30",
           "-vf", "scale=1080:1920,format=yuv420p",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-c:a", "aac", "-b:a", "128k", "-af", f"afade=t=out:st={CLIP_SECONDS - 2}:d=2",
           "-shortest", "-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True, capture_output=True)


# ---------------------------------------------------------------- drive

def drive_upload_public(path, name):
    """Upload to the Drive folder, make link-readable, return a direct-download URL."""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    info = json.loads(need("GDRIVE_SA_JSON"))
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=["https://www.googleapis.com/auth/drive"])
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    meta = {"name": name, "parents": [need("GDRIVE_FOLDER_ID")]}
    media = MediaFileUpload(path, mimetype="video/mp4", resumable=False)
    f = svc.files().create(body=meta, media_body=media, fields="id", supportsAllDrives=True).execute()
    fid = f["id"]
    svc.permissions().create(fileId=fid, body={"role": "reader", "type": "anyone"},
                             supportsAllDrives=True).execute()
    return fid, f"https://drive.google.com/uc?export=download&id={fid}"


# ---------------------------------------------------------------- meta

def ig_post_reel(video_url, caption):
    tok, ig = need("META_ACCESS_TOKEN"), need("IG_USER_ID")
    r = requests.post(f"{GRAPH}/{ig}/media", data={
        "media_type": "REELS", "video_url": video_url, "caption": caption,
        "share_to_feed": "true", "access_token": tok}, timeout=60)
    r.raise_for_status()
    cid = r.json()["id"]
    for _ in range(40):  # up to ~10 min
        s = requests.get(f"{GRAPH}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=30).json()
        code = s.get("status_code")
        if code == "FINISHED":
            break
        if code == "ERROR":
            raise RuntimeError(f"IG container error: {s}")
        time.sleep(15)
    else:
        raise RuntimeError("IG container never finished")
    r = requests.post(f"{GRAPH}/{ig}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60)
    r.raise_for_status()
    mid = r.json()["id"]
    p = requests.get(f"{GRAPH}/{mid}", params={"fields": "permalink", "access_token": tok}, timeout=30).json()
    return p.get("permalink", f"ig:{mid}")


def fb_post_video(video_url, description):
    tok, page = need("META_ACCESS_TOKEN"), need("FB_PAGE_ID")
    r = requests.post(f"{GRAPH}/{page}/videos", data={
        "file_url": video_url, "description": description, "access_token": tok}, timeout=120)
    r.raise_for_status()
    vid = r.json()["id"]
    return f"https://www.facebook.com/{page}/videos/{vid}"


# ---------------------------------------------------------------- record

def write_repo_record(fact, status, post_urls, verify_note):
    os.makedirs("facts", exist_ok=True)
    path = f"facts/{TODAY_S}.md"
    body = f"""# {fact['headline']}

- Date: {TODAY_S}
- Status: {status}
- Angle: {fact.get('angle')}
- Era: {fact.get('era', '')}
- Place: {fact.get('place', '')}
- Tags: {', '.join(fact.get('tags', []))}

## Fact
{fact['fact']}

## Takeaway
{fact.get('takeaway', '')}

## Source
- {fact.get('source_name', '')}: {fact['source_url']}
- Accessed: {TODAY_S}
- Verification: {verify_note}

> {fact.get('source_quote', '')}

## Posts
{chr(10).join('- ' + u for u in post_urls) or '- (none)'}
"""
    if DRY:
        log(f"DRY: would write {path}")
        return
    with open(path, "w") as f:
        f.write(body)
    log(f"wrote {path}")


def telegram(text):
    tok, chat = ENV("TELEGRAM_BOT_TOKEN"), ENV("TELEGRAM_CHAT_ID")
    if not tok or not chat:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage",
                      json={"chat_id": chat, "text": text[:3900], "disable_web_page_preview": True}, timeout=20)
    except Exception as e:
        log(f"telegram failed: {e}")


def caption_for(fact):
    tags = " ".join("#" + re.sub(r"[^A-Za-z0-9]", "", t.title()) for t in fact.get("tags", [])[:4])
    return (f"{fact['fact']}\n\n{fact.get('takeaway', '')}\n\n"
            f"Source: {fact.get('source_name', '')}\n\n"
            f"#DCUntold #DCHistory #WashingtonDC #UnofficialDC {tags}").strip()


# ---------------------------------------------------------------- main

def main():
    log(f"run start {TODAY_S} dry={DRY} retry_failed={RETRY_FAILED} paused={PAUSED} post_day={IS_POST_DAY}")
    if os.path.exists(f"facts/{TODAY_S}.md"):
        if RETRY_FAILED:
            log("fact record already exists for today; retry_failed=1 so continuing")
        else:
            log("already have a fact for today; exiting")
            return

    titles, tags = notion_existing_facts()
    log(f"{len(titles)} existing facts for dedupe")

    fact = None
    verify_note = ""
    for attempt in range(1, 4):
        fact = research(titles, tags)
        ok, verify_note = verify(fact)
        log(f"attempt {attempt}: {fact['headline']} -> {verify_note}")
        if ok:
            break
        titles.insert(0, fact["headline"])  # don't retry the same subject
    else:
        notion_create_fact(fact, "Unverified", extra_log=f"Could not verify after 3 attempts. Last: {verify_note}")
        write_repo_record(fact, "Unverified", [], verify_note)
        telegram(f"DC Untold: no fact verified today ({TODAY_S}). Last try: {fact['headline']} — {verify_note}. Nothing posted.")
        return

    if not IS_POST_DAY or PAUSED:
        why = "paused" if PAUSED else "not a posting day"
        notion_create_fact(fact, "Ready", extra_log=f"Verified ({verify_note}); {why}")
        write_repo_record(fact, "Ready", [], verify_note)
        telegram(f"DC Untold fact collected ({TODAY_S}), {why}: {fact['headline']}")
        return

    png, mp4 = f"out/{TODAY_S}.png", f"out/{TODAY_S}.mp4"
    os.makedirs("out", exist_ok=True)
    render_card(fact, png)
    render_video(png, mp4)
    log("rendered card + video")

    if DRY:
        notion_create_fact(fact, "Ready")
        write_repo_record(fact, "Ready", [], verify_note)
        log("DRY: skipping upload/post")
        return

    post_urls, errors = [], []
    try:
        _, video_url = drive_upload_public(mp4, f"dc-untold-{TODAY_S}.mp4")
        log(f"uploaded to Drive: {video_url}")
    except Exception as e:
        errors.append(f"drive: {e}")
        log(f"drive failed: {e}")
        video_url = None

    if video_url:
        cap = caption_for(fact)
        for name, fn in (("instagram", ig_post_reel), ("facebook", fb_post_video)):
            try:
                post_urls.append(fn(video_url, cap))
                log(f"{name} posted: {post_urls[-1]}")
            except Exception as e:
                errors.append(f"{name}: {e}")
                log(f"{name} failed: {e}")

    status = "Posted" if post_urls and not errors else ("Posted (partial)" if post_urls else "Failed")
    notion_create_fact(fact, status, post_url=post_urls[0] if post_urls else None,
                       extra_log=("; ".join(errors) or "ok") + f" | verify: {verify_note}")
    write_repo_record(fact, status, post_urls, verify_note)
    telegram(f"DC Untold {status} ({TODAY_S}): {fact['headline']}\n" + "\n".join(post_urls) +
             ("\nErrors: " + "; ".join(errors) if errors else ""))
    if status == "Failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
