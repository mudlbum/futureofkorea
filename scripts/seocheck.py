#!/usr/bin/env python3
"""
Per-article SEO, GEO and AdSense-readiness checks.

Deliberately excludes anything already covered elsewhere in validate.py — title
and meta length, canonical, JSON-LD validity, alt attributes, internal links,
byline, sitewide policy links, duplicate metadata. This module adds only the
checks that were missing, each chosen because it changes whether a page can win
a search result, be quoted by an answer engine, or pass an ad review.

SEO
---
* **Heading structure.** At least two H2s, and no skipped levels (an H2 followed
  by an H4). Search engines and screen readers both use the outline; a broken
  one costs featured-snippet eligibility.
* **Hero alt text must differ from the headline.** Repeating the title tells a
  reader using a screen reader nothing they have not already heard, and gives
  image search no new signal.
* **Slug discipline.** Under 60 characters, no filler words.

GEO (answer-engine optimisation)
--------------------------------
* **Opening paragraph 25–75 words.** The first paragraph is what gets lifted as
  a featured snippet or quoted by an LLM. Under 25 words it carries no answer;
  over 75 it gets truncated mid-thought.
* **FAQ answers at least 40 words.** A one-line answer is not quotable — the
  engine needs a self-contained passage it can lift without the question.

AdSense
-------
* **Ad density.** No more than one unit per 400 words of body prose. Density is
  scored directly by AdSense site quality and indirectly through Core Web Vitals.
* **No ad before 250 words.** An ad above the first substantial block of content
  is the classic "ads exceed content" rejection.

All checks are advisory before `style.enforce_from` and blocking after it, so
the archive is never rewritten retroactively.
"""
from __future__ import annotations

import re

SLUG_STOPWORDS = {"the", "a", "an", "and", "or", "for", "of", "to", "in", "on", "is"}

MIN_H2 = 2
LEAD_MIN, LEAD_MAX = 25, 75
FAQ_MIN_WORDS = 40
WORDS_PER_AD = 400
MIN_WORDS_BEFORE_FIRST_AD = 250
MAX_SLUG_LEN = 60


def _text(html_fragment: str) -> str:
    return re.sub(r"<[^>]+>", " ", html_fragment or "")


def _words(html_fragment: str) -> int:
    return len(re.findall(r"\w+", _text(html_fragment)))


def prose_of(page: str) -> str:
    m = re.search(r'<div class="prose"[^>]*>(.*?)</div>\s*<(?:aside|section|footer)',
                  page, re.S)
    return m.group(1) if m else page


def check(page: str, slug: str) -> list[str]:
    """Return a list of problems for one rendered article page."""
    problems: list[str] = []
    prose = prose_of(page)

    # ── SEO: heading outline ────────────────────────────────────────────────
    levels = [int(n) for n in re.findall(r"<h([2-6])[ >]", prose)]
    if levels.count(2) < MIN_H2:
        problems.append(
            f"only {levels.count(2)} H2 heading(s) — an article needs at least {MIN_H2} "
            "so the outline is legible to readers and to search")
    for a, b in zip(levels, levels[1:]):
        if b > a + 1:
            problems.append(
                f"heading level jumps from H{a} to H{b} — do not skip levels, it breaks "
                "the document outline")
            break

    # ── SEO: hero alt text ──────────────────────────────────────────────────
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
    alt = re.search(r'<img src="/img/[^"]*-hero[^"]*"[^>]*alt="([^"]*)"', page)
    if h1 and alt:
        if _text(h1.group(1)).strip().lower()[:60] == alt.group(1).strip().lower()[:60]:
            problems.append(
                "hero alt text repeats the headline — describe the image instead; "
                "a screen-reader user has already heard the title")
        if not alt.group(1).strip():
            problems.append("hero image has empty alt text")

    # ── SEO: slug ───────────────────────────────────────────────────────────
    if len(slug) > MAX_SLUG_LEN:
        problems.append(f"slug is {len(slug)} characters — keep it under {MAX_SLUG_LEN}")
    filler = [w for w in slug.split("-") if w in SLUG_STOPWORDS]
    if len(filler) > 1:
        problems.append(
            f"slug contains filler words ({', '.join(filler)}) — they add length "
            "without adding a keyword")

    # ── GEO: the opening paragraph is what gets quoted ──────────────────────
    lead = re.search(r"<p>(.*?)</p>", prose, re.S)
    if not lead:
        problems.append("no opening paragraph found")
    else:
        n = _words(lead.group(1))
        if n < LEAD_MIN:
            problems.append(
                f"opening paragraph is {n} words — too short to carry an answer "
                f"(want {LEAD_MIN}-{LEAD_MAX}). This is the passage answer engines lift.")
        elif n > LEAD_MAX:
            problems.append(
                f"opening paragraph is {n} words — it will be truncated mid-thought when "
                f"quoted (want {LEAD_MIN}-{LEAD_MAX}). Put the answer in the first "
                "paragraph and the elaboration in the second.")

    # ── GEO: FAQ answers must stand alone ───────────────────────────────────
    for i, ans in enumerate(re.findall(r'<div class="faq-a">(.*?)</div>', page, re.S), 1):
        n = _words(ans)
        if n < FAQ_MIN_WORDS:
            problems.append(
                f"FAQ answer {i} is {n} words — under {FAQ_MIN_WORDS} it is not a "
                "self-contained passage an answer engine can quote")

    # ── AdSense: density and placement ──────────────────────────────────────
    body_words = _words(prose)
    ads = len(re.findall(r">Advertisement<", page))
    if ads:
        allowed = max(1, body_words // WORDS_PER_AD)
        if ads > allowed:
            problems.append(
                f"{ads} ad units against ~{body_words} words of body — allow one per "
                f"{WORDS_PER_AD} words (max {allowed} here). Density is scored by AdSense "
                "and by Core Web Vitals.")
        first = page.find(">Advertisement<")
        if first != -1:
            before = _words(page[:first])
            if before < MIN_WORDS_BEFORE_FIRST_AD:
                problems.append(
                    f"first ad appears after only ~{before} words — give the reader at "
                    f"least {MIN_WORDS_BEFORE_FIRST_AD} words of content first, or the "
                    "page reads as ads-over-content")

    return problems
