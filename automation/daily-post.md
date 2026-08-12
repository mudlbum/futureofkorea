# Daily publishing run

This is the procedure the scheduled task follows. It is written to be executed by Claude with
web search and shell access to the repository.

## 0. Setup

```bash
cd <REPO>
git pull --rebase
```

## 1. Find today's story (do not skip this)

Run **web searches** across the beats below and look for something that changed in the last
24–72 hours. You are looking for *demand* — a thing people are actively searching about —
crossed with *a gap* in English-language coverage.

**Beat checklist:**

| Beat | What to search |
| --- | --- |
| Markets | KOSPI level and direction, foreign vs retail net flows, margin balance, notable earnings, index-provider news, new ETF listings |
| Semiconductors | HBM qualification news, memory pricing, capex changes, Samsung/SK hynix announcements, monthly chip export figures |
| Macro | Bank of Korea decisions and minutes, USD/KRW, CPI, trade balance, GDP revisions |
| Immigration & living | Ministry of Justice / HiKorea announcements, visa rule changes, tax and NHIS changes, housing policy |
| Society | Statistics Korea monthly population release, ageing, regional depopulation |
| Industry | Shipbuilding orders, defence export contracts, battery plant announcements, K-content and tourism data |

**Also check what readers are asking.** Long-tail questions with clear intent — "how do I…",
"is X still required", "what happens if…" — outperform news rewrites, rank for longer, and
attract higher-value advertising. A well-made evergreen explainer is usually a better use of a
day than a news summary that will be stale next week.

**Selection rule.** Pick the topic where you can (a) verify the facts against a primary source
today, (b) say something the existing English coverage does not, and (c) leave the reader able
to act. If nothing clears all three, publish nothing and say so. That is a valid outcome.

## 2. Verify

For every number you intend to publish, open the primary source and confirm it. Record the
source URL, the publisher, and the period the figure covers. If a figure is disputed between
sources, publish the range and name both.

**Never** state a fact on the authority of your own prior knowledge. Assume anything you
"remember" about Korean rules or figures is out of date.

## 3. Find supporting material

- **A video**, if one genuinely helps: search YouTube for coverage of the topic and take the
  ID from a real result. Never guess an ID. If nothing suitable exists, omit the field.
- **4–6 official resources**: the portals a reader would need — KOSIS, ECOS, DART, KRX,
  HiKorea, NTS, Korea Customs. Prefer English interfaces where they exist.
- **2–4 internal links** to existing posts. List them first with
  `ls content/posts/` so the URLs are real.

## 4. Write

```bash
python3 scripts/new_post.py "Headline goes here" --category markets
```

This scaffolds `content/posts/YYYY-MM-DD-slug.md` with the correct front matter. Fill it in
following the conventions in `CLAUDE.md`. Target 1,400–2,600 words.

## 5. Build, validate, ship

```bash
python3 build.py
python3 scripts/validate.py     # must exit 0
git add -A
git commit -m "post: <slug>"
git push
```

GitHub Actions rebuilds and deploys to GitHub Pages. The artwork for the new post is generated
automatically by `scripts/imagegen.py` during the build — nothing to draw, upload or license.

## 6. Housekeeping (weekly, or when prompted)

- **Refresh evergreen posts.** Any article whose figures have moved: update the number, update
  `updated:`, and note the change in the text. Do not touch `updated:` if nothing changed.
- **Check for dead links** in `sources` and `resources`.
- **Check the mix** against the target in `CLAUDE.md`.
- **Re-submit the sitemap** in Google Search Console if a batch of posts landed.

## What "no post today" looks like

Say so plainly, name what you checked, and stop. Do not pad. Do not rewrite yesterday's post
with new adjectives. Google's scaled-content-abuse policy exists precisely to catch sites that
publish daily regardless of whether they have anything to say — and a site that trips it loses
its AdSense account, not just a ranking.

---

## Step 2a — record the evidence as you verify (required)

Verification is no longer just a habit; it is a build gate. As you confirm each
figure in Step 2, write it straight into front matter:

1. Add the source to `sources:` with `title`, `url`, `publisher`, `accessed:` (today)
   and `primary: true` where it is the institution itself. Minimum three sources,
   at least one primary.
2. Write each takeaway as a mapping, not a string, and point it at the source index
   the number came from:

   ```yaml
   key_takeaways:
     - text: "Chip exports rose **21.4%** year on year in July 2026."
       source: 1
   ```

3. Every takeaway needs a **bolded figure**. No number, no takeaway.

Run the checker before you commit:

```bash
python3 scripts/factcheck.py
```

It fails on unsourced figures, missing primaries, stale `accessed` dates and dead
source URLs. `scripts/validate.py` runs it too, so a failure here blocks the deploy.

## Step 3a — decide the artwork

While drafting, decide whether the piece carries a series worth plotting.

* **Yes** → add a `chart:` block (see `CLAUDE.md`). The hero becomes that chart.
  Only plot numbers you verified in Step 2, and name the publisher in `chart.source`.
* **No** → add nothing. The hero becomes a typographic cover built from the headline
  and the lead figure.

Never fabricate a series to get a chart. An invented data point in an image is a
retraction, and images are exactly where readers stop checking.
