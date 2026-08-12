# Launch checklist

Work top to bottom. Items marked **(gate)** block AdSense approval.

## 1. Get it online

- [ ] `git init && git add -A && git commit -m "initial"` in this folder
- [ ] Create a GitHub repository and push to `main`
- [ ] **Settings → Pages → Source: GitHub Actions**
- [ ] Wait for the first workflow run to go green
- [ ] **Settings → Pages → Custom domain:** `futureofkorea.com` → Save
- [ ] DNS: four `A` records on the apex pointing to
      `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
- [ ] DNS: `CNAME` for `www` → `<your-github-username>.github.io`
- [ ] Back in GitHub Pages, tick **Enforce HTTPS** once the certificate issues (can take an hour)

## 2. Tell Google it exists

- [ ] Add the property in [Google Search Console](https://search.google.com/search-console)
      (domain property, verified by DNS TXT record — the most robust method)
- [ ] Submit `https://futureofkorea.com/sitemap.xml`
- [ ] Request indexing on the front page and two or three articles
- [ ] Optional: create a GA4 property and put the measurement ID in `site.config.json`
- [ ] Optional: add the Search Console HTML-tag token to
      `analytics.search_console_verification` if you prefer meta-tag verification

## 3. Before applying to AdSense **(gates)**

- [ ] **(gate)** Site live on the custom domain with valid HTTPS
- [ ] **(gate)** Privacy policy, cookie policy, terms, disclaimer, about, contact — all present
      and linked in the footer *(already built)*
- [ ] **(gate)** A real contact route. Set up `editor@futureofkorea.com` as a forwarding
      address and confirm it actually delivers — reviewers do check
- [ ] **(gate)** Enough substantial content. Six long articles is a thin application; aim for
      **20–30 published articles** across at least three categories before applying
- [ ] **(gate)** Site indexed in Google — search `site:futureofkorea.com` and see results
- [ ] Navigation works on mobile; no broken links (`scripts/validate.py` enforces this)
- [ ] No placeholder or lorem text anywhere (also enforced)

## 4. Apply

- [ ] Create the AdSense account, add `futureofkorea.com`
- [ ] Paste the verification snippet **or** simply set `adsense.publisher_id` in
      `site.config.json` and `enabled: true`, then rebuild — the build emits both the
      `google-adsense-account` meta tag and `ads.txt`
- [ ] Wait. Review commonly takes days to a few weeks
- [ ] If rejected, read the stated reason precisely. "Low value content" almost always means
      *not enough of it yet* — keep publishing and reapply rather than rewriting everything

## 5. After approval

- [ ] Set `adsense.enabled: true` and fill the slot IDs, rebuild, push
- [ ] Confirm `https://futureofkorea.com/ads.txt` returns your publisher line
- [ ] In AdSense, set up a **consent management platform** (required for EEA/UK traffic)
- [ ] Leave Auto Ads conservative at first — aggressive density hurts both Core Web Vitals and
      the reader experience Google is measuring
- [ ] Check **Core Web Vitals** in Search Console after two weeks of real traffic

## 6. Keep it alive

- [ ] The Cowork scheduled task runs the daily research-and-publish loop
- [ ] Weekly: refresh evergreen posts whose figures have moved, check for dead links
- [ ] Monthly: review Search Console queries and write the explainer people are actually
      searching for but not finding

## Realistic expectations

Search takes months, not days. A new domain typically sees very little organic traffic for the
first three to six months regardless of content quality, then compounds. The evergreen
explainers — visa rules, how-to guides, tax mechanics — are what will still be earning in two
years; the news posts are what gets the site crawled frequently in the meantime.
