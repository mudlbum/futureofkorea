# Future of Korea

English-language analysis of South Korea's economy, technology industry, capital markets,
demographics and society. A static site with zero runtime dependencies, procedurally generated
artwork, and a daily publishing pipeline driven by Claude.

**Live:** https://futureofkorea.com

---

## Quick start

```bash
pip install -r requirements.txt
python3 build.py --serve        # builds into dist/ and serves http://localhost:8000
```

That's the whole toolchain. No Node, no bundler, no CMS, no database, no image API.

## Commands

| Command | What it does |
| --- | --- |
| `python3 build.py` | Build the site into `dist/` |
| `python3 build.py --serve` | Build, then serve on `:8000` |
| `python3 scripts/validate.py` | Pre-publish gate — CI fails the deploy if this fails |
| `python3 scripts/new_post.py "Headline" -c markets` | Scaffold a post with correct front matter |
| `python3 scripts/imagegen.py my-slug markets` | Preview the generated artwork for a slug |

## How it fits together

```
content/posts/*.md   ──┐
content/pages/*.md   ──┼──▶ build.py ──▶ dist/ ──▶ GitHub Actions ──▶ GitHub Pages
site.config.json     ──┤                   ▲
static/*             ──┘                   │
                              scripts/imagegen.py
                              (hero + social card, drawn from the slug)
```

Every post automatically gets:

- a **1600×900 hero image** and a **1200×630 social card** with the headline typeset on it,
  generated procedurally from a hash of the slug — deterministic, offline, no licensing risk,
  and different for every article
- a full **JSON-LD graph**: `BlogPosting`, `FAQPage`, `BreadcrumbList`, `Organization`,
  `WebSite` with `SearchAction`, plus `speakable`
- **canonical URL, Open Graph and Twitter cards**, explicit published/modified timestamps
- a **table of contents**, **key-takeaways block**, **FAQ**, **useful links**, **sources**,
  a **production/AI disclosure**, and **related posts**
- entries in **sitemap.xml**, **rss.xml** and **llms.txt**

## Deployment

Push to `main`. `.github/workflows/deploy.yml` installs dependencies, builds, runs
`scripts/validate.py`, and publishes `dist/` to GitHub Pages. A failing validation blocks the
deploy — broken links, missing alt text, over-long titles, thin articles and invalid structured
data never reach production.

**One-time setup:**

1. Push this repository to GitHub.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. **Settings → Pages → Custom domain:** `futureofkorea.com`, and enable *Enforce HTTPS*.
4. At your DNS provider, point the apex domain at GitHub Pages:
   `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   (and a `CNAME` for `www` → `<user>.github.io`).
5. `dist/CNAME` is written automatically from `site.config.json` on every build.

## Turning on AdSense

Ads are **off** until you have been approved. Apply only once the site is live on the custom
domain with a body of published articles — that is what the reviewer looks at.

When approved, edit `site.config.json`:

```json
"adsense": {
  "enabled": true,
  "publisher_id": "ca-pub-XXXXXXXXXXXXXXXX",
  "auto_ads": true,
  "slots": { "in_article": "1234567890", "sidebar": "…", "footer": "…" }
}
```

Rebuild. This switches on the AdSense script, the `google-adsense-account` meta tag, the
in-article and footer units, and writes `dist/ads.txt` with the correct publisher line. Until
then the layout reserves labelled placeholder space so nothing shifts when ads appear.

Also fill in `analytics.ga4_id` and `analytics.search_console_verification` when you have them.

## Editorial standards

See [`CLAUDE.md`](CLAUDE.md) for the writing conventions and [`automation/daily-post.md`](automation/daily-post.md)
for the daily publishing procedure. The short version: primary sources only, every figure dated,
human review before publish, and no post at all on days without a real story.

## Licence

Site code: use it however you like. Article content: © Future of Korea, all rights reserved.
Bundled fonts in `assets/fonts/` are used under the SIL Open Font Licence; licence texts ship
alongside them.
