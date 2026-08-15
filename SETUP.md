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

---

## Analytics, consent and ads — switching them on

All three are wired and dormant. Each is a one-line config change.

### 1. GA4

1. Create a GA4 property at [analytics.google.com](https://analytics.google.com), add a
   **Web** data stream for `https://futureofkorea.com`
2. Copy the **Measurement ID** (looks like `G-XXXXXXXXXX`)
3. Put it in `site.config.json` → `analytics.ga4_id`
4. Rebuild and push

The moment that ID is set, three things happen automatically: `consent.js` loads
**before** gtag, Consent Mode v2 defaults are pushed as *denied*, and the cookie
banner appears. Analytics only receives data after a reader clicks "Accept all".
Order matters — the consent defaults must land before any Google tag, or the first
pageview escapes before consent is known. That is the mistake that gets sites
flagged under the EU user consent policy.

### 2. Search Console

Either verify by DNS TXT (most robust), or paste the HTML-tag token into
`analytics.search_console_verification` and rebuild.

### 3. AdSense — only after approval

Set `adsense.enabled: true` and the real `publisher_id` in `site.config.json`.
`validate.py` will fail the build if `enabled` is true while the publisher ID is
still a placeholder, so you cannot half-enable it by accident. The same consent
banner then governs ad personalisation.

Leave `auto_ads` conservative at first. Ad density is scored by Core Web Vitals,
and aggressive placement costs you more in rankings than it earns in clicks.

### 4. Languages — deliberately not built yet

`hreflang` plumbing is ready but emits nothing while the site is single-language.
Translations are deferred on purpose: machine-translated duplicates of a small post
archive are the textbook scaled-content-abuse pattern and a common AdSense rejection
reason. Revisit after approval and 30+ posts.

---

## Are we AdSense-ready yet?

```bash
python3 build.py && python3 scripts/adsense_ready.py
```

Reports the whole site against what reviewers actually assess, and tells you
plainly whether to apply. Eight automated checks plus four you have to confirm
yourself.

**Do not apply while it reports anything blocking.** A rejection is stickier than
a delay: reapplying puts you behind the same reviewers with a site they have
already declined, and "low value content" in particular tends to require a
substantially larger archive on the second attempt than it would have on the first.

### The four you must confirm

1. **`editor@futureofkorea.com` receives mail.** It is on all eight legal pages and
   in the structured data. Reviewers test contact routes. Cloudflare Email Routing
   forwards to Gmail for free.
2. **The site is indexed.** Search `site:futureofkorea.com`. If nothing appears,
   Google has not crawled you and neither has the reviewer's expectation of a real
   site. Requires Search Console verification and a submitted sitemap.
3. **The domain has been live a while** with some organic history. A domain
   registered last week with zero impressions is frequently deferred regardless of
   content quality.
4. **Financial disclaimers stay on investing pieces.** Already automated in the
   footer, but check any new format you add.

### After approval

Set `adsense.enabled: true` and the real `publisher_id`, then rebuild.
`validate.py` refuses to build if `enabled` is true while the ID is a placeholder,
so you cannot half-enable it.

Then keep density conservative. `seocheck.py` caps one unit per 400 words and
blocks any ad before 250 words of content, because "ads exceed content" is a
common post-approval suspension as well as a rejection reason.
