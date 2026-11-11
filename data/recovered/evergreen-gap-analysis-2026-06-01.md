# UDC Evergreen — Six-Month Gap Analysis

**Date:** 2026-06-01
**Companion files:** `udc-evergreen-six-month-queue-v0-1-2026-06-01.csv` / `.md`
**Purpose:** the honest math on how far the bank is from a true 6-month daily drumbeat, and a sourcing strategy to close the gap without taking on attribution or brand-voice risk.

---

## The math

| | Count |
|---|---|
| Target: 6 months daily (≈30.4 days/mo × 6) | **~182** (round to **180**) |
| Existing productionized rows | 38 |
| New sample-expansion items (this delivery) | 17 |
| **Total in bank today** | **55** |
| **Still needed for full 6 months** | **~125 more** |

So we are at **~31% of a six-month bank.** 55 of ~180.

**Important caveat — daily is the hard version.** If the drumbeat is *daily*, we need ~180 and the gap is ~125. If Kevin would accept a slightly looser cadence (e.g. 5 days/week, ~130 items for 6 months; or daily-with-curated-reuse where strong items reappear once after the 180-day cooldown can't apply), the gap shrinks materially. **Recommend Kevin confirm the cadence before we commit to sourcing 125 net-new items** — that's the single biggest scoping lever.

---

## The attribution-risk reality (why this isn't just "write 125 quotes")

Of the ~18 attributed quotes in the original 38, **10 (56%) were misattributed or unverifiable** and had to be set to Anonymous. Only 8 survived verification. That is the norm, not bad luck: the most-shared "love" quotes online are precisely the ones most likely to be fake (Lao Tzu, Rumi, Buddha, "Plato," "Aristotle" all failed here). Every famous-name quote we add costs real verification time and carries credibility/legal exposure if we get it wrong — and misquoting a beloved author (bell hooks, Maya Angelou) is a brand-trust hit, not just a footnote.

**Conclusion: do not try to close a 125-item gap with celebrity quotes.** The verified-quote lane is the slowest and riskiest. It should be the *smallest* share of the bank.

---

## Recommended sourcing mix for the remaining ~125

| Lane | Share | ~Count | Why |
|---|---|---|---|
| **Original UDC brand lines** (owned) | ~50% | ~62 | Zero attribution risk, fully on-brand, infinitely reusable, where the soul lives. This is UDC's home-field advantage — *our* voice is the moat. |
| **Wordless DC-scene visuals** (neighborhood/culture) | ~30% | ~38 | Zero attribution risk, carries feeling without words, reinforces the "unofficial DC = neighborhoods not monuments" thesis. Production-heavier but reusable as evergreen. |
| **Verified-attribution quotes** | ~15% | ~19 | Adds gravitas and cultural breadth, but each is individually verified against a primary source. Cap it — quality over volume. |
| **Anonymous quotes** (strong lines, unverifiable) | ~5% | ~6 | Use sparingly; only when the line is genuinely excellent and anonymizing is honest. Don't pad with these. |

This mix flips the original 38's ratio (which leaned heavily on celebrity quotes) toward owned + wordless — exactly the lanes with no risk and the most brand equity.

---

## How to keep quality high while scaling

1. **Original lines get the soul gate, not a quota.** Draft in batches, but each line must answer "does this carry?" Kill flat ones. Better 62 lines that land than 90 that fill slots. (Pairs with the line-by-line discipline Kevin named for soul-bearing work.)
2. **Verified quotes get individual primary-source proof** — no batch-trusting a quote list. Same standard used here (Latin Library / Stanford King Institute / Academy of American Poets / Internet Archive, not Goodreads/BrainyQuote). Anything aggregator-only → Anonymous or cut.
3. **Wordless visuals stay off the postcard.** Every concept reframes toward neighborhoods, culture, food, music, stoops, murals — and away from monuments/Tidal-Basin/Mall clichés. (See EVG-005 and EVG-051 already doing this.)
4. **Theme diversity tracked via `theme_tag`.** With 180 items the same themes will recur; the `no-back-to-back-same-theme` cooldown plus a theme-tag distribution check prevents the bank from feeling like ten ideas wearing 180 hats.
5. **Tier discipline holds the risk line.** Bias new content to Tier A. Tier B (named people, mission lines, apparel-adjacent) gets a Kevin eye. Tier C (charged topics like EVG-053 gentrification) only with explicit approval — most should simply be cut from an evergreen bank.

---

## Tier distribution target for the full 180

- **Tier A: ~80%** (~145) — the daily drumbeat should be overwhelmingly safe, auto-draftable content so the lane can eventually run with light-touch approval.
- **Tier B: ~18%** (~32) — verified named quotes + mission lines + apparel-adjacent; sprinkled, not stacked.
- **Tier C: ~2% or zero** — evergreen content generally should not be Tier C; charged topics don't belong in an always-on rotation.

---

## Proposed path to 180 (sequencing, not a commitment to publish)

1. **Kevin confirms cadence** (daily vs 5×/week vs daily-with-reuse) — sets the true target and shrinks/keeps the 125 gap.
2. **Kevin reacts to the 17-item sample block** — approve/cut/tweak so we calibrate the Original-line voice before scaling.
3. **Batch 1: ~40 Original UDC lines** drafted to the approved voice + soul gate.
4. **Batch 2: ~38 wordless DC-scene concepts** (visual direction only; assets produced as the scheduler/Daemon path firms up).
5. **Batch 3: ~19 verified quotes**, each individually source-proofed; **~6 anonymous** strong lines.
6. **Theme-balance + cooldown audit** across the full ~180 before anything is called schedule-ready.
7. **Only then**, once a scheduler/account path exists and Kevin approves the lane, do rows move past `Approved / Not Scheduled`.

---

## Bottom line

- **Bank today: 55 / ~180 (~31%).**
- **Gap: ~125 more items** for a strict daily 6-month drumbeat (less if cadence loosens — confirm with Kevin first).
- **Close it mostly with owned Original UDC lines (~50%) and wordless DC-scene visuals (~30%)** — the no-risk, high-equity lanes — and keep verified quotes to a carefully-sourced ~15% with ~5% Anonymous.
- The original 38's 56% misattribution rate is the proof point: lean on what we own and what we can verify, anonymize the rest, and never pad the bank with celebrity quotes we can't stand behind.
