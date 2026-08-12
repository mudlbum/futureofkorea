#!/usr/bin/env python3
"""
Photographic hero sourcing for Future of Korea.

Fetches a licensed landscape photograph per article from Pexels, caches it in the
repository, and records the photographer for attribution. The build composites it
behind the headline (see imagegen.photo_cover).

Design decisions worth knowing:

* **Cached and committed.** A photo is fetched once, written to assets/photos/,
  and its credit recorded in content/_data/photos.json. Later builds reuse the
  file. That keeps builds reproducible, keeps the article's image stable over
  time (readers and social previews hate images that silently change), and means
  CI does not depend on a third-party API being up.
* **Degrades to nothing.** No API key, no network, or no acceptable match and the
  function returns None — the caller then falls back to the typographic cover.
  A missing key is never an error.
* **Attribution is mandatory, not optional.** Pexels' licence requires crediting
  the photographer. The credit is stored alongside the file and rendered under
  the hero; a photo without a recorded credit is discarded rather than used.

Set PEXELS_API_KEY in the environment. In GitHub Actions, add it as a repository
secret and expose it to the build step.
"""
from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHOTO_DIR = os.path.join(ROOT, "assets", "photos")
INDEX = os.path.join(ROOT, "content", "_data", "photos.json")
API = "https://api.pexels.com/v1/search"
TIMEOUT = 20
UA = "futureofkorea-build/1.0 (+https://futureofkorea.com/)"

# Fallback search terms per category, used when a post declares no photo_query
# and its tags yield nothing useful. Deliberately concrete and Korea-anchored:
# generic "business" stock photography is what makes a site look like a template.
CATEGORY_TERMS = {
    "markets":    "Seoul financial district skyline trading",
    "technology": "semiconductor wafer fabrication clean room",
    "living":     "Seoul street daily life neighbourhood",
    "society":    "Seoul crowd people city street",
    "policy":     "Seoul government building architecture",
    "kcontent":   "Seoul concert stage lights performance",
    "_default":   "Seoul South Korea skyline",
}

STOPWORDS = {"the", "and", "for", "with", "from", "that", "this", "what", "how",
             "why", "korea", "korean", "2026", "explained", "guide"}


def _load_index() -> dict:
    try:
        return json.load(open(INDEX, encoding="utf-8"))
    except Exception:                                     # noqa: BLE001
        return {}


def _save_index(data: dict) -> None:
    os.makedirs(os.path.dirname(INDEX), exist_ok=True)
    json.dump(data, open(INDEX, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def query_for(post: dict) -> str:
    """Build a search phrase from the post's own front matter."""
    if post.get("photo_query"):
        return str(post["photo_query"])
    tags = [str(t) for t in (post.get("tags") or [])]
    words = [t for t in tags if t.lower() not in STOPWORDS and not re.fullmatch(r"\d+", t)]
    if words:
        return " ".join(words[:3]) + " Korea"
    return CATEGORY_TERMS.get(post.get("category", "_default"), CATEGORY_TERMS["_default"])


def fetch(post: dict, *, offline: bool = False) -> dict | None:
    """
    Return {'path', 'credit', 'credit_url', 'query'} for this post's photo, or None.

    Cached results are returned without touching the network.
    """
    slug = post["slug"]
    index = _load_index()
    hit = index.get(slug)
    if hit and os.path.exists(os.path.join(ROOT, hit.get("path", ""))):
        return {**hit, "path": os.path.join(ROOT, hit["path"])}

    key = os.environ.get("PEXELS_API_KEY", "").strip()
    if offline or not key:
        return None

    q = query_for(post)
    url = f"{API}?{urllib.parse.urlencode({'query': q, 'orientation': 'landscape', 'per_page': 5, 'size': 'large'})}"
    try:
        req = urllib.request.Request(url, headers={"Authorization": key, "User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:                                # noqa: BLE001
        print(f"  photos: search failed for {slug} ({type(e).__name__}) — falling back to cover")
        return None

    for photo in data.get("photos", []):
        src = (photo.get("src") or {}).get("large2x") or (photo.get("src") or {}).get("large")
        credit = (photo.get("photographer") or "").strip()
        if not src or not credit:
            continue                                       # no credit, no use
        try:
            os.makedirs(PHOTO_DIR, exist_ok=True)
            dest = os.path.join(PHOTO_DIR, f"{slug}.jpg")
            req = urllib.request.Request(src, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r, open(dest, "wb") as f:
                f.write(r.read())
        except Exception as e:                             # noqa: BLE001
            print(f"  photos: download failed for {slug} ({type(e).__name__})")
            return None

        rec = {
            "path": os.path.relpath(dest, ROOT).replace("\\", "/"),
            "credit": credit,
            "credit_url": photo.get("photographer_url") or photo.get("url") or "",
            "source_url": photo.get("url", ""),
            "provider": "Pexels",
            "query": q,
        }
        index[slug] = rec
        _save_index(index)
        print(f"  photos: {slug} ← “{q}” by {credit}")
        return {**rec, "path": dest}

    print(f"  photos: no usable result for {slug} (“{q}”) — falling back to cover")
    return None


def credit_html(rec: dict | None) -> str:
    if not rec or not rec.get("credit"):
        return ""
    who = rec["credit"]
    href = rec.get("credit_url") or rec.get("source_url") or ""
    name = (f'<a href="{href}" rel="nofollow noopener" target="_blank">{who}</a>'
            if href else who)
    return (f'<p class="photo-credit muted small">Photograph by {name} '
            f'on {rec.get("provider", "Pexels")}.</p>')
