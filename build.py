#!/usr/bin/env python3
"""
Future of Korea — static site generator.

    python3 build.py            # build into dist/
    python3 build.py --serve    # build, then serve dist/ on :8000

Design goals, in order:
  1. Google-approval-worthy: real policy pages, transparent authorship + AI
     disclosure, cited primary sources, no thin pages.
  2. SEO: semantic HTML, one H1, canonical URLs, full JSON-LD graph,
     sitemap, RSS, breadcrumbs, internal linking, image alt text.
  3. GEO (answer-engine optimisation): key-takeaway blocks, FAQ blocks,
     explicit dates and figures, source lists, llms.txt.
  4. Core Web Vitals: zero JS frameworks, zero web-font requests, inlined
     critical CSS, explicit image dimensions, lazy loading below the fold.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import sys
import unicodedata
from email.utils import format_datetime

import markdown
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
import imagegen  # noqa: E402
import livedata  # noqa: E402
import commentary  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.environ.get("FOK_DIST") or os.path.join(ROOT, "dist")
CFG = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))

SITE = CFG["domain"].rstrip("/")
CATS = {c["slug"]: c for c in CFG["categories"]}


def live_categories(posts):
    """Categories with at least one published post.

    A category page with no articles is a thin page, and thin pages are exactly
    what AdSense review and Google's helpful-content system penalise. New beats
    therefore stay invisible — no nav entry, no index page, no sitemap entry —
    until their first article exists.
    """
    used = {p["category"] for p in posts}
    return [c for c in CFG["categories"] if c["slug"] in used]


# ────────────────────────────────────────────────────────────── helpers ──
def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def esc(s) -> str:
    return html.escape(str(s or ""), quote=True)


def write(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def parse_front_matter(raw: str):
    if not raw.startswith("---"):
        return {}, raw
    _, fm, body = raw.split("---", 2)
    return yaml.safe_load(fm) or {}, body.lstrip("\n")


MD = markdown.Markdown(
    extensions=["extra", "sane_lists", "tables", "attr_list", "footnotes", "toc", "smarty"],
    extension_configs={"toc": {"permalink": False, "toc_depth": "2-3"}},
)


def md_frag(text: str) -> str:
    """Render a short markdown fragment to HTML (block-level)."""
    MD.reset()
    return MD.convert(text or "")


def md_inline(text: str) -> str:
    """Render a fragment and strip the wrapping <p> so it can sit inside <li>."""
    out = md_frag(text).strip()
    if out.startswith("<p>") and out.endswith("</p>") and out.count("<p>") == 1:
        out = out[3:-4]
    return out


def plain(text: str) -> str:
    """Markdown -> plain text, for JSON-LD values."""
    return html.unescape(re.sub(r"<[^>]+>", "", md_frag(text))).strip()


def render_md(text: str):
    MD.reset()
    return MD.convert(text), getattr(MD, "toc_tokens", [])


def clamp(text: str, limit: int) -> str:
    """Trim to a word boundary under `limit` characters, without a dangling ellipsis mid-word."""
    text = re.sub(r"\s+", " ", (text or "").strip())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    if " " in cut:
        cut = cut[:cut.rfind(" ")]
    return cut.rstrip(" ,;:—-") + "…"


def seo_title(obj, *, suffix=" | Future of Korea", limit=62) -> str:
    """<title> under ~62 chars so Google shows it whole. `seo_title` in front matter wins."""
    base = (obj.get("seo_title") or obj.get("title") or "").strip()
    if len(base) + len(suffix) <= limit:
        return base + suffix
    return clamp(base, limit)


def meta_desc(obj, limit=158) -> str:
    """Meta description capped at ~158 chars. `meta` in front matter wins over the on-page dek."""
    return clamp(obj.get("meta") or obj.get("description") or "", limit)


def reading_time(text: str) -> int:
    return max(1, round(len(re.findall(r"\w+", text)) / 225))


def iso(d) -> str:
    if isinstance(d, str):
        d = dt.date.fromisoformat(d)
    if isinstance(d, dt.datetime):
        return d.replace(tzinfo=dt.timezone(dt.timedelta(hours=9))).isoformat()
    return dt.datetime(d.year, d.month, d.day, 9, 0,
                       tzinfo=dt.timezone(dt.timedelta(hours=9))).isoformat()


def pretty_date(d) -> str:
    if isinstance(d, str):
        d = dt.date.fromisoformat(d)
    return d.strftime("%d %B %Y").lstrip("0")



# ─────────────────────────────────────────── callouts, videos, tip boxes ──
CALLOUT_ICONS = {
    "TIP":      ("Practical tip", "&#9733;"),
    "KEY":      ("Key number", "&#9679;"),
    "WARNING":  ("Watch out", "&#9888;"),
    "NOTE":     ("Context", "&#9432;"),
    "ACTION":   ("What to do", "&#10143;"),
}


def transform_callouts(md_text: str) -> str:
    """GitHub-style admonitions: `> [!TIP]` … become styled, quotable tip boxes."""
    out, i, lines = [], 0, md_text.split("\n")
    while i < len(lines):
        m = re.match(r"^>\s*\[!(TIP|KEY|WARNING|NOTE|ACTION)\]\s*(.*)$", lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        kind, title = m.group(1), (m.group(2) or "").strip()
        i += 1
        buf = []
        while i < len(lines) and lines[i].startswith(">"):
            buf.append(re.sub(r"^>\s?", "", lines[i])); i += 1
        label, icon = CALLOUT_ICONS[kind]
        inner = md_frag("\n".join(buf))
        out.append(f'<aside class="callout callout-{kind.lower()}">'
                   f'<p class="callout-h"><span class="callout-icon" aria-hidden="true">{icon}</span>'
                   f'{esc(title or label)}</p>{inner}</aside>')
    return "\n".join(out)


def video_embed(video, *, lazy=True) -> str:
    """Privacy-enhanced YouTube facade: no cookies, no third-party JS until clicked."""
    if not video:
        return ""
    vid = video.get("id", "")
    title = video.get("title", "Related video")
    src = f"https://www.youtube-nocookie.com/embed/{esc(vid)}?rel=0"
    cap = f'<figcaption class="muted small">{esc(title)}{" — " + esc(video["channel"]) if video.get("channel") else ""}</figcaption>'
    return f"""<figure class="video">
  <div class="video-frame">
    <iframe src="{src}" title="{esc(title)}" loading="{'lazy' if lazy else 'eager'}"
      allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
      referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
  </div>{cap}
</figure>"""


def resources_block(p) -> str:
    """Useful links + tools the reader can act on — the 'helpful content' signal."""
    if not p.get("resources"):
        return ""
    rows = "".join(
        f'<li><a href="{esc(r["url"])}" rel="noopener" target="_blank">{esc(r["title"])}</a>'
        f'<span class="muted"> — {esc(r.get("note",""))}</span></li>' for r in p["resources"])
    return f"""<section class="resources" aria-labelledby="res-h">
  <h2 id="res-h">Useful links &amp; tools</h2>
  <p class="muted small">Official portals and primary data sources for this topic. Opens in a new tab.</p>
  <ul class="plain linky">{rows}</ul></section>"""


# ─────────────────────────────────────────────────────────────── content ──
def load_posts():
    posts = []
    pdir = os.path.join(ROOT, "content", "posts")
    for name in sorted(os.listdir(pdir)):
        if not name.endswith(".md"):
            continue
        meta, body = parse_front_matter(read(os.path.join(pdir, name)))
        if meta.get("draft"):
            continue
        meta["slug"] = meta.get("slug") or slugify(meta["title"])
        meta["category"] = meta.get("category", "markets")
        meta["date"] = meta.get("date") or dt.date.today()
        meta["updated"] = meta.get("updated") or meta["date"]
        meta["body_md"] = body
        meta["reading_time"] = reading_time(body)
        meta["url"] = f"/{meta['category']}/{meta['slug']}/"
        meta["abs_url"] = SITE + meta["url"]
        meta["source_file"] = name
        posts.append(meta)
    posts.sort(key=lambda p: (str(p["date"]), p["slug"]), reverse=True)
    return posts


def load_pages():
    pages = []
    pdir = os.path.join(ROOT, "content", "pages")
    for name in sorted(os.listdir(pdir)):
        if not name.endswith(".md"):
            continue
        meta, body = parse_front_matter(read(os.path.join(pdir, name)))
        meta["slug"] = meta.get("slug") or slugify(meta["title"])
        meta["body_md"] = body
        meta["url"] = f"/{meta['slug']}/"
        meta["abs_url"] = SITE + meta["url"]
        pages.append(meta)
    return pages


# ───────────────────────────────────────────────────────────── ad slots ──
def ad_unit(kind: str) -> str:
    ad = CFG["adsense"]
    if not ad.get("enabled"):
        return (f'\n<div class="ad-slot ad-{kind}" data-ad-placeholder="{kind}" aria-hidden="true">'
                f'<span>Advertisement</span></div>\n')
    slot = ad["slots"].get(kind, "")
    return f"""
<div class="ad-slot ad-{kind}">
  <span class="ad-label">Advertisement</span>
  <ins class="adsbygoogle" style="display:block" data-ad-client="{ad['publisher_id']}"
       data-ad-slot="{slot}" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>
"""


def inject_in_article_ads(html_body: str, every: int = 4) -> str:
    """Place in-article units between paragraphs — never inside content, never above the fold."""
    parts = re.split(r"(?=<h2)", html_body)
    if len(parts) < 3:
        return html_body
    out, n = [], 0
    for i, part in enumerate(parts):
        out.append(part)
        n += 1
        if 0 < i < len(parts) - 1 and n % every == 0:
            out.append(ad_unit("in_article"))
    return "".join(out)


# ─────────────────────────────────────────────────────────────── layout ──
LIVE = livedata.fetch(offline=bool(os.environ.get("FOK_OFFLINE")))
LIVE_CATS: set[str] = set()

def head(title, description, canonical, *, og_image, og_type="article",
         published=None, modified=None, jsonld=None, robots="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"):
    ad = CFG["adsense"]
    gsc = CFG["analytics"].get("search_console_verification")
    ga = CFG["analytics"].get("ga4_id")
    bits = [f"""<!doctype html>
<html lang="{CFG['lang']}" prefix="og: https://ogp.me/ns#">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:site_name" content="{esc(CFG['site_name'])}">
<meta property="og:locale" content="{CFG['locale']}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(title)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_image)}">
<meta name="theme-color" content="#0a0e1a" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/img/logo.png">
<link rel="alternate" type="application/rss+xml" title="{esc(CFG['site_name'])}" href="/rss.xml">
<link rel="sitemap" type="application/xml" href="/sitemap.xml">
<link rel="stylesheet" href="/style.css">"""]
    if published:
        bits.append(f'<meta property="article:published_time" content="{published}">')
    if modified:
        bits.append(f'<meta property="article:modified_time" content="{modified}">')
    if gsc:
        bits.append(f'<meta name="google-site-verification" content="{esc(gsc)}">')
    if jsonld:
        bits.append('<script type="application/ld+json">'
                    + json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))
                    + "</script>")
    # Consent Mode v2 must be established before gtag.js or the AdSense tag load,
    # so this script is synchronous and deliberately first. Everything Google
    # loads afterwards inherits the denied-by-default state until the reader
    # accepts. Order here is a compliance requirement, not a style choice.
    if ga or ad.get("enabled"):
        bits.append('<script src="/consent.js"></script>')
        bits.append('<link rel="preconnect" href="https://www.googletagmanager.com" crossorigin>')
    if ad.get("enabled"):
        bits.append('<link rel="preconnect" href="https://pagead2.googlesyndication.com" crossorigin>')
        bits.append(f'<meta name="google-adsense-account" content="{ad["publisher_id"]}">')
        if ad.get("auto_ads"):
            bits.append('<script async crossorigin="anonymous" '
                        f'src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ad["publisher_id"]}"></script>')
    if ga:
        bits.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={ga}"></script>'
                    "<script>window.dataLayer=window.dataLayer||[];"
                    "function gtag(){dataLayer.push(arguments)}"
                    f"gtag('js',new Date());"
                    f"gtag('config','{ga}',{{anonymize_ip:true}});</script>")
    bits.append("</head>")
    return "\n".join(bits)


def header_html(active=""):
    def _link(n):
        cur = ' aria-current="page"' if n["url"].strip("/") == active else ""
        return '<a href="%s"%s>%s</a>' % (n["url"], cur, esc(n["label"]))
    nav_items = [n for n in CFG["nav"]
                 if not (n["url"].strip("/") in CATS and n["url"].strip("/") not in LIVE_CATS)]
    links = "".join(_link(n) for n in nav_items)
    return f"""<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="/" aria-label="{esc(CFG['site_name'])} home">
      <svg class="brand-mark" viewBox="0 0 40 40" aria-hidden="true" width="34" height="34">
        <circle cx="20" cy="20" r="18" fill="none" stroke="var(--accent)" stroke-width="3"
                stroke-dasharray="70 43" transform="rotate(-40 20 20)"/>
        <circle cx="20" cy="20" r="11" fill="none" stroke="var(--accent-2)" stroke-width="3"
                stroke-dasharray="42 27" transform="rotate(140 20 20)"/>
      </svg>
      <span class="brand-text"><strong>Future</strong> of Korea</span>
    </a>
    <input type="checkbox" id="navtoggle" class="navtoggle" aria-label="Open menu">
    <label for="navtoggle" class="burger" aria-hidden="true"><span></span><span></span><span></span></label>
    <nav class="site-nav" aria-label="Primary">{links}</nav>
  </div>
</header>
<main id="main">"""


def footer_html():
    cats = "".join(f'<li><a href="/{c["slug"]}/">{esc(c["name"])}</a></li>'
                   for c in CFG["categories"] if c["slug"] in LIVE_CATS)
    year = dt.date.today().year
    return f"""</main>
<footer class="site-footer">
  <div class="wrap footer-grid">
    <div>
      <p class="footer-brand"><strong>Future of Korea</strong></p>
      <p class="muted">{esc(CFG['tagline'])}</p>
      <p class="muted small">Independent English-language analysis of the Korean economy,
      technology industry, capital markets and society. Published from Seoul time (KST).</p>
    </div>
    <div>
      <h2 class="footer-h">Sections</h2>
      <ul class="plain">{cats}</ul>
    </div>
    <div>
      <h2 class="footer-h">The site</h2>
      <ul class="plain">
        <li><a href="/about/">About</a></li>
        <li><a href="/editorial-policy/">Editorial &amp; AI policy</a></li>
        <li><a href="/contact/">Contact</a></li>
        <li><a href="/rss.xml">RSS feed</a></li>
      </ul>
    </div>
    <div>
      <h2 class="footer-h">Legal</h2>
      <ul class="plain">
        <li><a href="/privacy-policy/">Privacy policy</a></li>
        <li><a href="/cookie-policy/">Cookie policy</a></li>
        <li><a href="/terms/">Terms of use</a></li>
        <li><a href="/disclaimer/">Disclaimer</a></li>
      </ul>
    </div>
  </div>
  <div class="wrap footer-bottom">
    <p class="muted small">&copy; {year} Future of Korea. All rights reserved.
    Nothing on this site is investment, legal, immigration or tax advice —
    see our <a href="/disclaimer/">disclaimer</a>.</p>
  </div>
</footer>
<script src="/script.js" defer></script>
</body></html>"""


# ────────────────────────────────────────────────────────────── JSON-LD ──
def org_node():
    return {
        "@type": "Organization",
        "@id": SITE + "/#organization",
        "name": CFG["publisher"]["name"],
        "url": SITE + "/",
        "logo": {"@type": "ImageObject", "url": SITE + "/img/logo.png", "width": 512, "height": 512},
        "email": CFG["publisher"]["email"],
        "foundingDate": CFG["publisher"]["founded"],
        "description": CFG["tagline"],
        "knowsAbout": ["South Korean economy", "KOSPI", "Korean semiconductors",
                       "Korean demographics", "Korea visas", "Korea trade policy"],
    }


def website_node():
    return {
        "@type": "WebSite",
        "@id": SITE + "/#website",
        "url": SITE + "/",
        "name": CFG["site_name"],
        "description": CFG["tagline"],
        "publisher": {"@id": SITE + "/#organization"},
        "inLanguage": "en-US",
        "potentialAction": {
            "@type": "SearchAction",
            "target": {"@type": "EntryPoint", "urlTemplate": SITE + "/search/?q={search_term_string}"},
            "query-input": "required name=search_term_string",
        },
    }


def author_node():
    a = CFG["author"]
    return {
        "@type": "Organization",
        "@id": SITE + "/about/#desk",
        "name": a["name"],
        "url": SITE + "/about/",
        "description": a["bio"],
        "parentOrganization": {"@id": SITE + "/#organization"},
    }


def breadcrumbs(items):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u}
            for i, (n, u) in enumerate(items)
        ],
    }


# ──────────────────────────────────────────────────────────────── cards ──
def post_card(p, *, eager=False, size="md"):
    c = CATS.get(p["category"], {})
    return f"""<article class="card card-{size}">
  <a class="card-media" href="{p['url']}" tabindex="-1" aria-hidden="true">
    <img src="/img/{p['slug']}-hero.webp" alt="" width="1600" height="900"
         loading="{'eager' if eager else 'lazy'}" {'fetchpriority="high"' if eager else 'decoding="async"'}>
  </a>
  <div class="card-body">
    <a class="chip chip-{p['category']}" href="/{p['category']}/">{esc(c.get('name', p['category']))}</a>
    <h2 class="card-title"><a href="{p['url']}">{esc(p['title'])}</a></h2>
    <p class="card-dek">{esc(p.get('description', ''))}</p>
    <p class="card-meta"><time datetime="{iso(p['date'])}">{pretty_date(p['date'])}</time>
      <span aria-hidden="true">·</span> {p['reading_time']} min read</p>
  </div>
</article>"""


# ───────────────────────────────────────────────────────────── renderers ──
def render_post(p, all_posts):
    cat = CATS.get(p["category"], {})
    body_html, toc = render_md(transform_callouts(p["body_md"]))

    # Key takeaways — the block answer engines lift verbatim.
    kt = ""
    if p.get("key_takeaways"):
        def takeaway(k):
            """Render a takeaway with a superscript citation into the sources list."""
            if not isinstance(k, dict):
                return f"<li>{md_inline(k)}</li>"          # legacy plain string
            refs = k.get("source")
            refs = [] if refs is None else (refs if isinstance(refs, list) else [refs])
            cites = "".join(
                f'<sup class="cite"><a href="#source-{r}" '
                f'aria-label="Source {r}">{r}</a></sup>' for r in refs)
            return f'<li>{md_inline(k.get("text", ""))}{cites}</li>'

        items = "".join(takeaway(k) for k in p["key_takeaways"])
        kt = f"""<aside class="takeaways" aria-labelledby="key-takeaways">
  <h2 id="key-takeaways">Key takeaways</h2>
  <ul>{items}</ul>
</aside>"""

    toc_html = ""
    tops = [t for t in toc]
    if len(tops) >= 3:
        def li(nodes):
            return "".join(
                f'<li><a href="#{n["id"]}">{esc(n["name"])}</a>'
                + (f'<ul>{li(n["children"])}</ul>' if n.get("children") else "")
                + "</li>" for n in nodes)
        toc_html = f"""<nav class="toc" aria-labelledby="toc-h">
  <h2 id="toc-h">On this page</h2><ul>{li(tops)}</ul></nav>"""

    faq_html = ""
    if p.get("faq"):
        rows = "".join(
            f'<details class="faq-item"><summary><h3>{esc(f["q"])}</h3></summary>'
            f'<div class="faq-a">{md_frag(f["a"])}</div></details>'
            for f in p["faq"])
        faq_html = f"""<section class="faq" aria-labelledby="faq-h">
  <h2 id="faq-h">Frequently asked questions</h2>{rows}</section>"""

    src_html = ""
    if p.get("sources"):
        def source_row(i, s):
            acc = s.get("accessed")
            stamp = (f'<span class="muted small"> · verified {esc(str(acc))}</span>'
                     if acc else "")
            tag = ('<span class="src-primary" title="Primary source">primary</span>'
                   if s.get("primary") else "")
            return (f'<li id="source-{i}"><span class="src-n">{i}</span>'
                    f'<a href="{esc(s["url"])}" rel="nofollow noopener" target="_blank">'
                    f'{esc(s["title"])}</a>{tag}'
                    f'<span class="muted"> — {esc(s.get("publisher", ""))}</span>{stamp}</li>')

        rows = "".join(source_row(i, s) for i, s in enumerate(p["sources"], start=1))
        src_html = f"""<section class="sources" aria-labelledby="src-h">
  <h2 id="src-h">Sources &amp; further reading</h2>
  <p class="muted small">Every figure in the key takeaways is numbered to the source it was
  read from. Sources marked <span class="src-primary">primary</span> are the statistics
  office, central bank, exchange, regulator or filing itself.</p>
  <ol class="plain sourcelist">{rows}</ol></section>"""

    related = [q for q in all_posts if q["slug"] != p["slug"] and q["category"] == p["category"]][:3]
    if len(related) < 3:
        related += [q for q in all_posts
                    if q["slug"] != p["slug"] and q not in related][:3 - len(related)]
    rel_html = ""
    if related:
        rel_html = f"""<section class="related" aria-labelledby="rel-h">
  <h2 id="rel-h">Read next</h2>
  <div class="grid grid-3">{''.join(post_card(q, size='sm') for q in related)}</div></section>"""

    for vid in (p.get("videos") or []):
        marker = f"<!--video:{vid.get('after','')}-->"
        if marker in body_html:
            body_html = body_html.replace(marker, video_embed(vid))
    body_html = inject_in_article_ads(body_html)

    graph = [org_node(), website_node(), author_node(),
             breadcrumbs([("Home", "/"), (cat.get("name", p["category"]), f"/{p['category']}/"),
                          (p["title"], p["url"])])]
    article = {
        **commentary.jsonld(p),
        "@type": "BlogPosting",
        "@id": p["abs_url"] + "#article",
        "isPartOf": {"@id": SITE + "/#website"},
        "mainEntityOfPage": {"@type": "WebPage", "@id": p["abs_url"]},
        "headline": p["title"][:110],
        "name": p["title"],
        "description": meta_desc(p),
        "url": p["abs_url"],
        "datePublished": iso(p["date"]),
        "dateModified": iso(p["updated"]),
        "author": {"@id": SITE + "/about/#desk"},
        "publisher": {"@id": SITE + "/#organization"},
        "articleSection": cat.get("name", p["category"]),
        "keywords": ", ".join(p.get("tags", [])),
        "wordCount": len(re.findall(r"\w+", p["body_md"])),
        "inLanguage": "en-US",
        "image": {"@type": "ImageObject", "url": SITE + f"/img/{p['slug']}-og.png",
                  "width": 1200, "height": 630},
        "speakable": {"@type": "SpeakableSpecification",
                      "cssSelector": [".takeaways", ".article-dek"]},
        "isAccessibleForFree": True,
        "creativeWorkStatus": "Published",
    }
    if p.get("about"):
        article["about"] = [{"@type": "Thing", "name": t} for t in p["about"]]
    graph.append(article)
    if p.get("faq"):
        graph.append({
            "@type": "FAQPage",
            "@id": p["abs_url"] + "#faq",
            "mainEntity": [{"@type": "Question", "name": f["q"],
                            "acceptedAnswer": {"@type": "Answer", "text": plain(f["a"])}}
                           for f in p["faq"]],
        })

    doc = head(seo_title(p), meta_desc(p), p["abs_url"],
               og_image=SITE + f"/img/{p['slug']}-og.png", og_type="article",
               published=iso(p["date"]), modified=iso(p["updated"]),
               jsonld={"@context": "https://schema.org", "@graph": graph})
    doc += header_html(p["category"])
    doc += f"""
<article class="article" data-article-type="{p.get('article_type','explainer')}">
  <div class="wrap wrap-narrow">
    <nav class="crumbs" aria-label="Breadcrumb">
      <ol><li><a href="/">Home</a></li><li><a href="/{p['category']}/">{esc(cat.get('name',''))}</a></li>
      <li aria-current="page">{esc(p['title'])}</li></ol>
    </nav>
    <header class="article-head">
      <a class="chip chip-{p['category']}" href="/{p['category']}/">{esc(cat.get('name',''))}</a>
      <h1>{esc(p['title'])}</h1>
      <p class="article-dek">{esc(p.get('description',''))}</p>
      <div class="byline">
        <span>By <a href="/about/">{esc(CFG['author']['name'])}</a></span>
        <span aria-hidden="true">·</span>
        <time datetime="{iso(p['date'])}">Published {pretty_date(p['date'])}</time>
        {'<span aria-hidden="true">·</span><time datetime="%s">Updated %s</time>' % (iso(p['updated']), pretty_date(p['updated'])) if str(p['updated']) != str(p['date']) else ''}
        <span aria-hidden="true">·</span><span>{p['reading_time']} min read</span>
      </div>
    </header>
  </div>
  <figure class="hero">
    <img src="/img/{p['slug']}-hero.webp" alt="{esc(p.get('image_alt') or p['title'])}"
         width="1600" height="900" fetchpriority="high" decoding="async">
    {p.get('photo_credit', '')}
  </figure>
  <div class="wrap wrap-narrow">
    {commentary.render(p, esc)}
    {kt}
    {toc_html}
    <div class="prose">{body_html}</div>
    {video_embed(p.get('video'))}
    {resources_block(p)}
    {faq_html}
    {src_html}
    <aside class="disclosure">
      <h2>How this article was produced</h2>
      <p>Researched, drafted and fact-checked by the Future of Korea editorial desk — an
      AI-assisted publishing system — against the primary sources listed above. Every
      figure in the key takeaways is tied to a numbered source, and the article could not
      publish until an automated verification gate confirmed each source was named,
      dated and reachable. Publication is automated; a human reviews after the fact and
      corrections are issued promptly. Figures are stated with the date they were current.
      See our <a href="/editorial-policy/">editorial &amp; AI policy</a>
      and <a href="/corrections/">corrections policy</a>.</p>
    </aside>
    {ad_unit('footer')}
    {rel_html}
  </div>
</article>"""
    doc += footer_html()
    write(os.path.join(DIST, p["category"], p["slug"], "index.html"), doc)


def render_home(posts):
    feat = posts[0] if posts else None
    rest = posts[1:CFG["posts_per_page"] + 1]
    cat_cards = "".join(
        f"""<a class="cat-card cat-{c['slug']}" href="/{c['slug']}/">
        <h3>{esc(c['name'])}</h3><p>{esc(c['blurb'])}</p><span class="cat-go">Browse →</span></a>"""
        for c in live_categories(posts))
    hero = ""
    if feat:
        hero = f"""<section class="lede">
  <a class="lede-media" href="{feat['url']}" tabindex="-1" aria-hidden="true">
    <img src="/img/{feat['slug']}-hero.webp" alt="" width="1600" height="900" fetchpriority="high">
  </a>
  <div class="lede-body">
    <a class="chip chip-{feat['category']}" href="/{feat['category']}/">{esc(CATS[feat['category']]['name'])}</a>
    <h2><a href="{feat['url']}">{esc(feat['title'])}</a></h2>
    <p class="lede-dek">{esc(feat.get('description',''))}</p>
    <p class="card-meta"><time datetime="{iso(feat['date'])}">{pretty_date(feat['date'])}</time>
      <span aria-hidden="true">·</span> {feat['reading_time']} min read</p>
  </div>
</section>"""
    graph = [org_node(), website_node(),
             {"@type": "CollectionPage", "@id": SITE + "/#webpage", "url": SITE + "/",
              "name": CFG["site_name"], "description": CFG["tagline"],
              "isPartOf": {"@id": SITE + "/#website"}, "inLanguage": "en-US"}]
    doc = head("Future of Korea — Korea's economy and markets, in English",
               "Independent English-language analysis of South Korea's economy, chip and battery "
               "industries, stock market, demographics and visa rules \u2014 sourced to primary data.",
               SITE + "/", og_image=SITE + "/img/logo.png", og_type="website",
               jsonld={"@context": "https://schema.org", "@graph": graph})
    doc += header_html()
    doc += f"""
<section class="masthead">
  <div class="wrap">
    <h1>Korea, explained for the rest of the world</h1>
    <p class="masthead-dek">{esc(CFG['tagline'])} Daily analysis of the Korean economy,
    its technology industry, its capital markets, and what it costs to live and work here —
    written in English, sourced to the primary data.</p>
  </div>
</section>
{livedata.render(LIVE)}
<div class="wrap">
  {hero}
  {ad_unit('in_article')}
  <section aria-labelledby="latest-h">
    <h2 id="latest-h" class="section-h">Latest analysis</h2>
    <div class="grid grid-3">{''.join(post_card(p) for p in rest)}</div>
  </section>
  <section aria-labelledby="sections-h">
    <h2 id="sections-h" class="section-h">Sections</h2>
    <div class="cat-grid">{cat_cards}</div>
  </section>
</div>"""
    doc += footer_html()
    write(os.path.join(DIST, "index.html"), doc)


def render_category(c, posts):
    items = [p for p in posts if p["category"] == c["slug"]]
    graph = [org_node(), website_node(),
             breadcrumbs([("Home", "/"), (c["name"], f"/{c['slug']}/")]),
             {"@type": "CollectionPage", "@id": f"{SITE}/{c['slug']}/#webpage",
              "url": f"{SITE}/{c['slug']}/", "name": c["name"], "description": meta_desc(c),
              "isPartOf": {"@id": SITE + "/#website"}, "inLanguage": "en-US",
              "mainEntity": {"@type": "ItemList", "itemListElement": [
                  {"@type": "ListItem", "position": i + 1, "url": p["abs_url"], "name": p["title"]}
                  for i, p in enumerate(items[:30])]}}]
    doc = head(seo_title({"seo_title": c["name"] + " in Korea"}), meta_desc(c), f"{SITE}/{c['slug']}/",
               og_image=SITE + "/img/logo.png", og_type="website",
               jsonld={"@context": "https://schema.org", "@graph": graph})
    doc += header_html(c["slug"])
    grid = "".join(post_card(p, eager=(i == 0)) for i, p in enumerate(items)) or \
        '<p class="muted">No articles in this section yet — check back tomorrow.</p>'
    doc += f"""
<div class="wrap">
  <nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>
    <li aria-current="page">{esc(c['name'])}</li></ol></nav>
  <header class="page-head"><h1>{esc(c['name'])}</h1><p class="page-dek">{esc(c['blurb'])}</p></header>
  {ad_unit('in_article')}
  <div class="grid grid-3">{grid}</div>
</div>"""
    doc += footer_html()
    write(os.path.join(DIST, c["slug"], "index.html"), doc)


def render_page(pg):
    body, _ = render_md(pg["body_md"])
    graph = [org_node(), website_node(),
             breadcrumbs([("Home", "/"), (pg["title"], pg["url"])]),
             {"@type": "WebPage", "@id": pg["abs_url"] + "#webpage", "url": pg["abs_url"],
              "name": pg["title"], "description": pg.get("description", ""),
              "isPartOf": {"@id": SITE + "/#website"}, "inLanguage": "en-US",
              "dateModified": iso(pg.get("updated") or dt.date.today())}]
    doc = head(seo_title(pg), meta_desc(pg), pg["abs_url"],
               og_image=SITE + "/img/logo.png", og_type="website",
               robots=pg.get("robots", "index,follow"),
               jsonld={"@context": "https://schema.org", "@graph": graph})
    doc += header_html()
    doc += f"""
<div class="wrap wrap-narrow">
  <nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="/">Home</a></li>
    <li aria-current="page">{esc(pg['title'])}</li></ol></nav>
  <header class="page-head"><h1>{esc(pg['title'])}</h1>
  <p class="muted small">Last updated {pretty_date(pg.get('updated') or dt.date.today())}</p></header>
  <div class="prose">{body}</div>
</div>"""
    doc += footer_html()
    write(os.path.join(DIST, pg["slug"], "index.html"), doc)


def render_404():
    doc = head("Page not found | Future of Korea",
               "We could not find that page. Browse the latest Future of Korea analysis on Korea's "
               "economy, technology industry, stock market, demographics and visa rules instead.",
               SITE + "/404.html", og_image=SITE + "/img/logo.png", og_type="website",
               robots="noindex,follow")
    doc += header_html()
    doc += """<div class="wrap wrap-narrow"><header class="page-head">
      <h1>That page has moved on</h1>
      <p class="page-dek">The link is broken or the article was renamed.
      Try the <a href="/">front page</a> or one of the sections in the menu.</p>
      </header></div>"""
    doc += footer_html()
    write(os.path.join(DIST, "404.html"), doc)


# ─────────────────────────────────────────────────────── machine outputs ──
def render_feeds(posts, pages):
    # (url, changefreq, priority, lastmod, image_url, image_caption)
    urls = [(SITE + "/", "daily", "1.0", dt.date.today(), None, None)]
    for c in live_categories(posts):
        urls.append((f"{SITE}/{c['slug']}/", "daily", "0.8", dt.date.today(), None, None))
    for p in posts:
        # Declaring the hero in the sitemap is what gets it considered for Google
        # Images, which is a meaningful discovery channel for chart-led articles.
        urls.append((p["abs_url"], "monthly", "0.9", p["updated"],
                     f"{SITE}/img/{p['slug']}-hero.webp",
                     p.get("image_alt") or p["title"]))
    for pg in pages:
        urls.append((pg["abs_url"], "yearly", "0.4",
                     pg.get("updated") or dt.date.today(), None, None))

    def entry(u, cf, pr, d, img, cap):
        block = (f"<url><loc>{u}</loc>"
                 f"<lastmod>{d if isinstance(d, str) else d.isoformat()}</lastmod>"
                 f"<changefreq>{cf}</changefreq><priority>{pr}</priority>")
        if img:
            block += (f"<image:image><image:loc>{img}</image:loc>"
                      f"<image:title>{esc(cap)}</image:title></image:image>")
        return block + "</url>"

    body = "".join(entry(*u) for u in urls)
    write(os.path.join(DIST, "sitemap.xml"),
          '<?xml version="1.0" encoding="UTF-8"?>'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
          'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">' + body + "</urlset>")

    write(os.path.join(DIST, "robots.txt"), f"""User-agent: *
Allow: /

# Answer engines are welcome — this site is written to be cited.
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /

Sitemap: {SITE}/sitemap.xml
""")

    now = dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    items = "".join(f"""<item>
<title>{esc(p['title'])}</title>
<link>{p['abs_url']}</link>
<guid isPermaLink="true">{p['abs_url']}</guid>
<description>{esc(p.get('description',''))}</description>
<category>{esc(CATS.get(p['category'],{}).get('name',''))}</category>
<pubDate>{format_datetime(dt.datetime.fromisoformat(iso(p['date'])))}</pubDate>
</item>""" for p in posts[:40])
    write(os.path.join(DIST, "rss.xml"), f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>{esc(CFG['site_name'])}</title>
<link>{SITE}/</link>
<atom:link href="{SITE}/rss.xml" rel="self" type="application/rss+xml"/>
<description>{esc(CFG['tagline'])}</description>
<language>en-us</language>
<lastBuildDate>{format_datetime(now)}</lastBuildDate>
{items}
</channel></rss>""")

    # llms.txt — GEO: a clean, machine-readable map of the site for answer engines.
    lines = [f"# {CFG['site_name']}", "",
             f"> {CFG['tagline']} Independent English-language analysis of South Korea's economy, "
             "technology industry, capital markets, demographics and immigration rules.", "",
             "Published from Seoul (KST). Figures are cited to primary sources — Bank of Korea, "
             "Statistics Korea, KRX, FSS, ministry releases and company filings — and each article "
             "states the date its figures were current. Content is drafted with AI assistance and "
             "published automatically once every figure passes an automated source-verification "
             "gate; reviewed by a human after publication. See /editorial-policy/.", ""]
    for c in live_categories(posts):
        items_c = [p for p in posts if p["category"] == c["slug"]]
        if not items_c:
            continue
        lines.append(f"## {c['name']}")
        lines.append(f"{c['blurb']}")
        lines.append("")
        for p in items_c:
            lines.append(f"- [{p['title']}]({p['abs_url']}): {p.get('description','')} "
                         f"(updated {p['updated']})")
        lines.append("")
    lines += ["## About", ""] + [f"- [{pg['title']}]({pg['abs_url']})" for pg in pages]
    write(os.path.join(DIST, "llms.txt"), "\n".join(lines) + "\n")

    ad = CFG["adsense"]
    if ad.get("enabled") and ad["publisher_id"].startswith("ca-pub-"):
        pub = ad["publisher_id"].replace("ca-pub-", "")
        write(os.path.join(DIST, "ads.txt"), f"google.com, pub-{pub}, DIRECT, f08c47fec0942fa0\n")

    write(os.path.join(DIST, "favicon.svg"), """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
<rect width="40" height="40" rx="8" fill="#0a0e1a"/>
<circle cx="20" cy="20" r="13" fill="none" stroke="#c8102e" stroke-width="4"
 stroke-dasharray="52 30" transform="rotate(-40 20 20)"/>
<circle cx="20" cy="20" r="7" fill="none" stroke="#7aa2ff" stroke-width="4"
 stroke-dasharray="26 18" transform="rotate(140 20 20)"/></svg>""")

    write(os.path.join(DIST, "manifest.webmanifest"), json.dumps({
        "name": CFG["site_name"], "short_name": "FoK", "start_url": "/",
        "display": "standalone", "background_color": "#0a0e1a", "theme_color": "#0a0e1a",
        "icons": [{"src": "/img/logo.png", "sizes": "512x512", "type": "image/png"}]}))


# ──────────────────────────────────────────────────────────────── build ──
def build():
    if os.path.isdir(DIST):
        try:
            shutil.rmtree(DIST)
        except OSError as e:          # some mounted filesystems disallow unlink
            print(f"! could not clear {DIST} ({e}); overwriting in place")
    os.makedirs(DIST, exist_ok=True)

    posts, pages = load_posts(), load_pages()
    global LIVE_CATS
    LIVE_CATS = {c["slug"] for c in live_categories(posts)}
    print(f"→ {len(posts)} posts, {len(pages)} pages")

    imagegen.logo(os.path.join(DIST, "img", "logo.png"))
    for p in posts:
        h = os.path.join(DIST, "img", f"{p['slug']}-hero.webp")
        o = os.path.join(DIST, "img", f"{p['slug']}-og.png")
        _pmeta = {**p, "category_name": CATS.get(p["category"], {}).get("name", "")}
        imagegen.hero(_pmeta, h)
        if _pmeta.get("_photo_credit"):
            p["photo_credit"] = _pmeta["_photo_credit"]
        if _pmeta.get("_photo_alt"):
            # describe what is actually on screen, not what used to be
            p["image_alt"] = _pmeta["_photo_alt"]
        imagegen.social_card(p["slug"], p["category"], p["title"],
                             CATS.get(p["category"], {}).get("name", ""), o)
    print(f"→ generated {len(posts)*2+1} images")

    for p in posts:
        render_post(p, posts)
    for c in live_categories(posts):
        render_category(c, posts)
    for pg in pages:
        render_page(pg)
    render_home(posts)
    render_404()
    render_feeds(posts, pages)

    for f in os.listdir(os.path.join(ROOT, "static")):
        shutil.copy(os.path.join(ROOT, "static", f), os.path.join(DIST, f))
    try:
        import dedupe
        write(os.path.join(ROOT, "content", "_data", "published-topics.md"),
              dedupe.topic_index())
    except Exception as e:                      # noqa: BLE001
        print(f"  topic index skipped ({type(e).__name__})")
    write(os.path.join(DIST, "CNAME"), SITE.split("//")[1] + "\n")
    write(os.path.join(DIST, ".nojekyll"), "")
    print(f"✓ built → {DIST}")
    return posts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    a = ap.parse_args()
    build()
    if a.serve:
        import http.server, socketserver, functools
        os.chdir(DIST)
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST)
        print("serving http://localhost:8000")
        socketserver.TCPServer(("", 8000), h).serve_forever()
