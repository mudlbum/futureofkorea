#!/usr/bin/env python3
"""
Commentary posts — responding to someone else's reporting, lawfully.

The model is the one used by every serious opinion desk: point at a story, quote
a short passage with attribution, then say something the original did not. What
makes that lawful is not the link — attribution is a courtesy, not a licence —
it is that the quote is minimal, the commentary is substantial and original, and
the new work does not substitute for reading the original.

This module encodes those conditions as rules the build enforces, so the
protection does not depend on anyone remembering it at 7am.

Front matter
------------
commentary:
  source_title:  "Headline as published"
  source_outlet: "The outlet's name"
  source_url:    "https://..."          # absolute, links out
  source_date:   2026-08-12
  quote:         "A short verbatim passage."   # <= MAX_QUOTE_WORDS
  quote_context: "what the passage was describing"   # your framing, optional

Rules enforced (see check())
----------------------------
1.  Exactly one quoted passage per article. Quoting a source repeatedly across a
    piece reconstructs it — the thing that turns fair use into infringement.
2.  The quote is at most MAX_QUOTE_WORDS words.
3.  Attribution is complete: outlet, title and an absolute URL.
4.  The article carries at least MIN_ORIGINAL_WORDS of its own prose, so the
    commentary clearly dominates the quotation rather than framing it.
5.  The headline may not simply restate the source headline — a near-duplicate
    title is the clearest signal that nothing was added.

None of this makes a bad-faith rewrite lawful. It makes a good-faith commentary
verifiably good-faith.
"""
from __future__ import annotations

import datetime as dt
import re

MAX_QUOTE_WORDS = 40
MIN_ORIGINAL_WORDS = 1200
TITLE_OVERLAP_LIMIT = 0.7          # share of source-headline words reused

ABSOLUTE = re.compile(r"^https?://", re.I)
REQUIRED = ("source_title", "source_outlet", "source_url", "quote")


def words(text: str) -> int:
    return len(re.findall(r"[\w'’-]+", text or ""))


def _norm(text: str) -> set[str]:
    return {w.lower() for w in re.findall(r"[\w'’-]+", text or "") if len(w) > 3}


def check(post: dict, body_words: int) -> list[str]:
    """Return a list of problems. Empty means the post is publishable."""
    c = post.get("commentary")
    if not c:
        return []
    problems: list[str] = []

    if not isinstance(c, dict):
        return ["commentary: must be a mapping"]

    for field in REQUIRED:
        if not str(c.get(field) or "").strip():
            problems.append(f"commentary.{field} is required")

    url = str(c.get("source_url") or "")
    if url and not ABSOLUTE.match(url):
        problems.append(f"commentary.source_url must be absolute: {url!r}")

    quote = str(c.get("quote") or "")
    qw = words(quote)
    if qw > MAX_QUOTE_WORDS:
        problems.append(
            f"commentary.quote is {qw} words — the limit is {MAX_QUOTE_WORDS}. "
            "Quote less and say more.")
    if quote.count("…") > 2 or quote.count("...") > 2:
        problems.append(
            "commentary.quote is stitched from several passages. Quote one "
            "continuous sentence, not a reassembled paragraph.")

    if body_words < MIN_ORIGINAL_WORDS:
        problems.append(
            f"commentary post has ~{body_words} words of its own — at least "
            f"{MIN_ORIGINAL_WORDS} are required so the commentary clearly "
            "dominates the quotation.")

    src_title, own_title = str(c.get("source_title") or ""), str(post.get("title") or "")
    a, b = _norm(src_title), _norm(own_title)
    if a and b:
        overlap = len(a & b) / len(a)
        if overlap > TITLE_OVERLAP_LIMIT:
            problems.append(
                f"headline reuses {overlap:.0%} of the source headline — write your "
                "own angle, not theirs.")

    return problems


def render(post: dict, esc) -> str:
    """The 'responding to' block placed above the article body."""
    c = post.get("commentary")
    if not c:
        return ""
    when = c.get("source_date")
    if isinstance(when, (dt.date, dt.datetime)):
        when = when.strftime("%d %B %Y").lstrip("0")
    meta = " · ".join(filter(None, [esc(c.get("source_outlet", "")), esc(when or "")]))
    context = c.get("quote_context")

    return f"""<aside class="responding" aria-labelledby="responding-h">
  <p class="responding-k" id="responding-h">Responding to</p>
  <p class="responding-title">
    <a href="{esc(c['source_url'])}" rel="nofollow noopener" target="_blank">
      {esc(c['source_title'])}</a></p>
  <p class="responding-meta muted small">{meta}</p>
  <blockquote class="responding-quote" cite="{esc(c['source_url'])}">
    <p>{esc(c['quote'])}</p>
    <footer>— <cite>{esc(c.get('source_outlet', ''))}</cite></footer>
  </blockquote>
  {f'<p class="responding-context muted small">{esc(context)}</p>' if context else ''}
  <p class="responding-note muted small">Quoted briefly for comment and criticism.
  The analysis below is our own; read the original in full at the link above.</p>
</aside>"""


def jsonld(post: dict) -> dict:
    """schema.org citation so the relationship is machine-readable, not implied."""
    c = post.get("commentary")
    if not c:
        return {}
    return {
        "citation": {
            "@type": "NewsArticle",
            "headline": c.get("source_title", ""),
            "url": c.get("source_url", ""),
            "publisher": {"@type": "Organization", "name": c.get("source_outlet", "")},
        },
        "isBasedOn": c.get("source_url", ""),
    }
