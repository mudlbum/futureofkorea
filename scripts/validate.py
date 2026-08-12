#!/usr/bin/env python3
"""
Pre-publication gate. Runs in CI after build.py and fails the deploy on anything
that would embarrass us in front of Google or a reader.

Checks:
  * every internal link and image resolves
  * exactly one <h1> per page
  * <title> <= 62 chars, meta description 110-165 chars
  * every JSON-LD block parses
  * every <img> has an alt attribute
  * required legal/policy pages exist
  * every post has takeaways, sources, and an FAQ
  * no placeholder text escaped into production
"""
from __future__ import annotations

import glob
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DIST = os.environ.get("FOK_DIST") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist")

REQUIRED_PAGES = ["about", "contact", "privacy-policy", "cookie-policy",
                  "terms", "disclaimer", "editorial-policy", "corrections"]
REQUIRED_FILES = ["index.html", "404.html", "sitemap.xml", "robots.txt",
                  "rss.xml", "llms.txt", "style.css", "favicon.svg"]
FORBIDDEN = ["lorem ipsum", "TODO:", "FIXME", "XXXX", "{{", "[INSERT",
             "As an AI language model", "I cannot", "placeholder text"]

errors: list[str] = []
warnings: list[str] = []


def err(msg):
    errors.append(msg)


def warn(msg):
    warnings.append(msg)


def main():
    if not os.path.isdir(DIST):
        print(f"FATAL: no build output at {DIST}")
        return 1

    for f in REQUIRED_FILES:
        if not os.path.exists(os.path.join(DIST, f)):
            err(f"missing required file: {f}")
    for p in REQUIRED_PAGES:
        if not os.path.exists(os.path.join(DIST, p, "index.html")):
            err(f"missing required policy page: /{p}/")

    pages = sorted(glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True))
    if len(pages) < 10:
        err(f"only {len(pages)} pages built — expected at least 10")

    for f in pages:
        rel = f.replace(DIST, "") or "/"
        h = open(f, encoding="utf-8").read()
        low = h.lower()

        # links + assets resolve
        for ref in re.findall(r'(?:href|src)="(/[^"#?]*)"', h):
            target = os.path.join(DIST, ref.lstrip("/"))
            if ref.endswith("/"):
                target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                err(f"{rel}: broken internal reference -> {ref}")

        # headings
        n = len(re.findall(r"<h1[ >]", h))
        if n != 1:
            err(f"{rel}: {n} <h1> elements (must be exactly 1)")

        # title + description
        m = re.search(r"<title>(.*?)</title>", h, re.S)
        if not m:
            err(f"{rel}: no <title>")
        elif len(html.unescape(m.group(1))) > 62:
            err(f"{rel}: <title> is {len(html.unescape(m.group(1)))} chars (max 62)")

        m = re.search(r'name="description" content="(.*?)"', h, re.S)
        if not m:
            err(f"{rel}: no meta description")
        else:
            d = len(html.unescape(m.group(1)))
            if not (110 <= d <= 165):
                err(f"{rel}: meta description is {d} chars (want 110-165)")

        if 'rel="canonical"' not in h:
            err(f"{rel}: no canonical link")

        # structured data
        for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(block)
            except Exception as e:
                err(f"{rel}: invalid JSON-LD ({e})")

        # images
        for img in re.findall(r"<img [^>]*>", h):
            if "alt=" not in img:
                err(f"{rel}: <img> without alt attribute")
            if "width=" not in img or "height=" not in img:
                warn(f"{rel}: <img> without explicit dimensions (CLS risk)")

        for bad in FORBIDDEN:
            if bad.lower() in low:
                err(f"{rel}: forbidden placeholder text found: {bad!r}")

    # article-quality gate
    cfg = json.load(open(os.path.join(os.path.dirname(DIST.rstrip(os.sep)) if False else
                                      os.path.join(os.path.dirname(os.path.dirname(
                                          os.path.abspath(__file__))), "site.config.json")),
                         encoding="utf-8"))
    cat_slugs = {c["slug"] for c in cfg["categories"]}
    articles = []
    for f in pages:
        parts = os.path.relpath(f, DIST).split(os.sep)
        if len(parts) == 3 and parts[0] in cat_slugs and parts[2] == "index.html":
            articles.append(f)
    if not articles:
        err("no articles found in build output")
    for f in articles:
        rel = f.replace(DIST, "")
        h = open(f, encoding="utf-8").read()
        words = len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", h)))
        if words < 900:
            err(f"{rel}: only ~{words} words — too thin to publish")
        for needle, label in [("takeaways", "key takeaways block"),
                              ("faq-item", "FAQ section"),
                              ('class="sources"', "sources list"),
                              ("disclosure", "AI/production disclosure")]:
            if needle not in h:
                err(f"{rel}: missing {label}")

    # ── AdSense site-quality gate ────────────────────────────────────────────
    # These are the things reviewers and the automated policy scan actually look
    # for. Each one has rejected real sites: duplicate metadata reads as scaled
    # content, orphan pages read as thin, and missing policy links in the footer
    # is a straight fail regardless of how good the writing is.
    titles: dict[str, str] = {}
    descs: dict[str, str] = {}
    for f in pages:
        rel = f.replace(DIST, "") or "/"
        h = open(f, encoding="utf-8").read()

        m = re.search(r"<title>(.*?)</title>", h, re.S)
        if m:
            t = html.unescape(m.group(1)).strip()
            if t in titles:
                err(f"{rel}: duplicate <title> — also used by {titles[t]} "
                    "(duplicate metadata reads as scaled content abuse)")
            titles[t] = rel
        m = re.search(r'name="description" content="(.*?)"', h, re.S)
        if m:
            d = html.unescape(m.group(1)).strip()
            if d in descs:
                err(f"{rel}: duplicate meta description — also used by {descs[d]}")
            descs[d] = rel

        # every page must reach the policy pages from its own footer
        for policy in ("privacy-policy", "terms", "disclaimer", "contact"):
            if f'/{policy}/' not in h:
                err(f"{rel}: no link to /{policy}/ (AdSense requires it site-wide)")

    for f in articles:
        rel = f.replace(DIST, "")
        h = open(f, encoding="utf-8").read()
        body = h.split('<div class="prose"', 1)[-1]
        internal = len(set(re.findall(r'href="(/(?!img/|style|favicon|rss|sitemap)[^"]*)"', body)))
        if internal < 2:
            err(f"{rel}: {internal} internal link(s) in the body — need at least 2 "
                "so the page is not an orphan")
        if not re.search(r'(datetime=|class="byline")', h):
            err(f"{rel}: no visible byline or publication date")

    cfg_ads = json.load(open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "site.config.json"), encoding="utf-8")).get("adsense", {})
    if cfg_ads.get("enabled"):
        if not os.path.exists(os.path.join(DIST, "ads.txt")):
            err("adsense.enabled is true but no ads.txt was emitted")
        pub = str(cfg_ads.get("publisher_id", ""))
        if not pub.startswith("ca-pub-") or pub.endswith("0000000000000000"):
            err(f"adsense.enabled is true but publisher_id is still a placeholder ({pub})")

    # sourcing gate — every published figure traceable to a live primary source
    try:
        import factcheck
        fc_errors, fc_legacy = factcheck.run(offline=bool(os.environ.get("FOK_OFFLINE")))
        for f in fc_errors:
            err(f"fact-check — {f}")
        for f in fc_legacy:
            warn(f"fact-check (pre-cutoff) — {f}")
    except Exception as e:                      # noqa: BLE001
        err(f"fact-check could not run: {type(e).__name__}: {e}")

    print(f"checked {len(pages)} pages ({len(articles)} articles)")
    if warnings:
        print(f"  {len(warnings)} warning(s) — first 5:")
    for w in warnings[:5]:
        print(f"  warn: {w}")
    if errors:
        print(f"\n✗ {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("✓ all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
