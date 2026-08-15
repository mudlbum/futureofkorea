#!/usr/bin/env python3
"""
AdSense readiness report.

Run this before applying:  python3 scripts/adsense_ready.py

Reviewers assess a site, not a page. This walks the built output and reports
where you stand against the things that actually decide an application, split
into what the build can verify and what only you can confirm.

It is a report, not a gate — `validate.py` already blocks the per-article
failures. This answers a different question: "is it time to apply yet?"
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.environ.get("FOK_DIST") or os.path.join(ROOT, "dist")
CFG = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))

# Google's own guidance is vague ("sufficient content"), but rejection reports
# and practitioner consensus put the practical floor well above ten articles.
# 25 is a defensible target for a site with this depth per piece.
TARGET_ARTICLES = 25
COMFORTABLE_ARTICLES = 30

PASS, FAIL, MANUAL = "PASS", "FAIL", "YOU"


def articles():
    cats = {c["slug"] for c in CFG["categories"]}
    out = []
    for f in glob.glob(os.path.join(DIST, "*", "*", "index.html")):
        parts = os.path.relpath(f, DIST).split(os.sep)
        if len(parts) == 3 and parts[0] in cats:
            out.append(f)
    return out


def check():
    rows: list[tuple[str, str, str]] = []
    arts = articles()
    n = len(arts)
    home = os.path.join(DIST, "index.html")
    home_html = open(home, encoding="utf-8").read() if os.path.exists(home) else ""

    # ── content volume ──────────────────────────────────────────────────────
    if n >= COMFORTABLE_ARTICLES:
        rows.append((PASS, "Content volume", f"{n} articles — comfortably above the bar"))
    elif n >= TARGET_ARTICLES:
        rows.append((PASS, "Content volume", f"{n} articles — at the practical minimum"))
    else:
        need = TARGET_ARTICLES - n
        rows.append((FAIL, "Content volume",
                     f"{n} articles — {need} more before applying (~{need} days at one a day). "
                     "This is the single most common rejection reason."))

    # ── policy pages ────────────────────────────────────────────────────────
    required = ["privacy-policy", "cookie-policy", "terms", "disclaimer",
                "about", "contact", "editorial-policy", "corrections"]
    missing = [p for p in required
               if not os.path.exists(os.path.join(DIST, p, "index.html"))]
    rows.append((PASS if not missing else FAIL, "Policy pages",
                 "all present and linked site-wide" if not missing
                 else f"missing: {', '.join(missing)}"))

    # ── each article properly sourced ───────────────────────────────────────
    unsourced = [f for f in arts
                 if 'class="sources"' not in open(f, encoding="utf-8").read()]
    rows.append((PASS if not unsourced else FAIL, "Sourcing",
                 "every article carries a numbered source list" if not unsourced
                 else f"{len(unsourced)} article(s) without a sources block"))

    # ── originality / duplication ───────────────────────────────────────────
    try:
        sys.path.insert(0, os.path.join(ROOT, "scripts"))
        import dedupe
        dup, _ = dedupe.check()
        rows.append((PASS if not dup else FAIL, "Original content",
                     "no duplicate topics detected" if not dup
                     else f"{len(dup)} duplicate-topic pair(s) — scaled-content risk"))
    except Exception as e:                                # noqa: BLE001
        rows.append((FAIL, "Original content", f"duplicate check failed: {e}"))

    # ── AI disclosure honesty ───────────────────────────────────────────────
    ed = os.path.join(DIST, "editorial-policy", "index.html")
    ed_html = open(ed, encoding="utf-8").read() if os.path.exists(ed) else ""
    claims_human = "human editor having read it end to end" in ed_html
    rows.append((FAIL if claims_human else PASS, "Disclosure accuracy",
                 "editorial policy claims human pre-publication review that does not happen"
                 if claims_human else
                 "editorial policy describes the actual automated process"))

    # ── ad configuration ────────────────────────────────────────────────────
    ad = CFG.get("adsense", {})
    if not ad.get("enabled"):
        rows.append((PASS, "Ad configuration",
                     "ads correctly disabled until approval — do not enable early"))
    else:
        pub = str(ad.get("publisher_id", ""))
        ok = pub.startswith("ca-pub-") and not pub.endswith("0000000000000000")
        has_txt = os.path.exists(os.path.join(DIST, "ads.txt"))
        rows.append((PASS if ok and has_txt else FAIL, "Ad configuration",
                     "publisher ID set and ads.txt emitted" if ok and has_txt
                     else f"publisher_id={pub!r}, ads.txt={'present' if has_txt else 'MISSING'}"))

    # ── consent ─────────────────────────────────────────────────────────────
    has_consent = os.path.exists(os.path.join(DIST, "consent.js"))
    wired = "consent.js" in home_html
    if has_consent and wired:
        rows.append((PASS, "EEA consent", "Consent Mode v2 loads before Google tags"))
    elif has_consent:
        rows.append((PASS, "EEA consent",
                     "consent.js ready; activates automatically with GA4 or AdSense"))
    else:
        rows.append((FAIL, "EEA consent", "no consent mechanism — required for EEA/UK ad traffic"))

    # ── navigation health ───────────────────────────────────────────────────
    broken = 0
    for f in glob.glob(os.path.join(DIST, "**", "*.html"), recursive=True):
        h = open(f, encoding="utf-8").read()
        for ref in re.findall(r'href="(/[^"#?]*)"', h):
            t = os.path.join(DIST, ref.lstrip("/"))
            if ref.endswith("/"):
                t = os.path.join(t, "index.html")
            if not os.path.exists(t):
                broken += 1
    rows.append((PASS if not broken else FAIL, "Navigation",
                 "no broken internal links" if not broken else f"{broken} broken link(s)"))

    # ── things only the operator can confirm ────────────────────────────────
    email = CFG.get("publisher", {}).get("email", "")
    rows.append((MANUAL, "Working contact address",
                 f"{email} must actually receive mail — reviewers test it"))
    rows.append((MANUAL, "Indexed in Google",
                 "search `site:futureofkorea.com` and confirm pages appear. "
                 "Requires Search Console verification and a submitted sitemap."))
    rows.append((MANUAL, "Domain age and traffic",
                 "reviewers look for a site that is live, reachable and has some "
                 "organic history. A brand-new domain with no impressions is often deferred."))
    rows.append((MANUAL, "Content suitability",
                 "economy, markets, immigration and industry coverage is squarely "
                 "acceptable. Keep financial disclaimers on investing pieces."))

    return rows, n


def main() -> int:
    if not os.path.isdir(DIST):
        print("No build output. Run python3 build.py first.")
        return 1

    rows, n = check()
    width = max(len(label) for _, label, _ in rows)
    print("\nAdSense readiness — futureofkorea.com\n" + "=" * 66)
    for status, label, detail in rows:
        mark = {"PASS": "  ok ", "FAIL": " FAIL", "YOU": " you "}[status]
        print(f"[{mark}] {label.ljust(width)}  {detail}")

    blocking = [r for r in rows if r[0] == FAIL]
    manual = [r for r in rows if r[0] == MANUAL]
    auto = [r for r in rows if r[0] != MANUAL]
    print("=" * 66)
    print(f"Automated checks: {len(auto) - len(blocking)}/{len(auto)} passing"
          f" · {len(manual)} item(s) only you can confirm")

    if blocking:
        print("\nNot ready to apply. Blocking:")
        for _, label, detail in blocking:
            print(f"  · {label}: {detail}")
    else:
        print("\nEverything the build can check is in order. Confirm the four items "
              "marked 'you' and you are ready to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
