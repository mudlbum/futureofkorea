#!/usr/bin/env python3
"""Scaffold a correctly-shaped post file.

    python3 scripts/new_post.py "Why the won stays weak" --category policy
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "site.config.json"), encoding="utf-8"))
CATS = [c["slug"] for c in CFG["categories"]]


def slugify(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[-\s]+", "-", re.sub(r"[^\w\s-]", "", t).strip().lower())


TEMPLATE = '''---
title: "{title}"
slug: {slug}
seo_title: "TODO under 44 chars"
meta: "TODO 110-158 characters, primary keyword near the front, gives a reason to click."
category: {category}
date: {date}
updated: {date}
description: "TODO one or two sentence standfirst shown on the page and in cards."
image_alt: "TODO describes the generated artwork for screen readers"
tags: [todo, five, to, eight, tags]
about: ["TODO entity names for schema.org"]
# Every takeaway must state a **bolded figure** and cite the source it came from
# by its 1-based index in `sources:` below. validate.py fails the build otherwise.
key_takeaways:
  - text: "TODO lead with the number. **Bold the figure.** Name the source period."
    source: 1
  - text: "TODO **figure**"
    source: 2
  - text: "TODO **figure**"
    source: 1
  - text: "TODO **figure**"
    source: 3
# Optional. Present a `chart:` block and the hero image becomes a real chart of
# these numbers instead of a typographic cover. Omit it entirely if the piece
# has no series worth plotting — a wrong chart is worse than no chart.
# chart:
#   type: line              # line | bar | grouped_bar
#   title: "TODO what the chart shows, with its period"
#   y_label: "TODO unit"
#   y_suffix: ""            # e.g. "%"
#   source: "TODO who published these numbers"
#   annotate_last: true
#   series:
#     - label: "TODO"
#       points: [["Jan", 0], ["Feb", 0]]
# video:            # optional — only with a real, verified YouTube ID
#   id: XXXXXXXXXXX
#   title: "Video title as published"
#   channel: "Channel name"
faq:
  - q: "TODO a question a reader would actually type"
    a: "TODO a complete answer in two to five sentences."
  - q: "TODO"
    a: "TODO"
  - q: "TODO"
    a: "TODO"
  - q: "TODO"
    a: "TODO"
  - q: "TODO"
    a: "TODO"
resources:
  - title: "TODO official portal"
    url: "https://"
    note: "TODO what it is and why you would open it"
# At least 3 sources, at least 1 marked `primary: true` — the statistics office,
# central bank, exchange, regulator or filing you read the figure off. News
# coverage corroborates a primary source; it does not replace one.
# `accessed` is the date you actually opened it and saw the number.
sources:
  - title: "TODO the page or release title as published"
    url: "https://"
    publisher: "TODO Bank of Korea / Statistics Korea / KRX / DART / ministry"
    accessed: {date}
    primary: true
  - title: "TODO"
    url: "https://"
    publisher: "TODO outlet, month year"
    accessed: {date}
  - title: "TODO"
    url: "https://"
    publisher: "TODO outlet, month year"
    accessed: {date}
---

TODO opening: the news or the question, in two or three sentences. No throat-clearing.

## TODO an H2 that makes a claim or asks a question

TODO.

> [!KEY] TODO the number that matters
> TODO.

## TODO

TODO — use a table for anything comparative.

> [!TIP] TODO something the reader can act on
> TODO.

## TODO

> [!ACTION] TODO what to watch
> - TODO
> - TODO

*Figures current as of {pretty}, sourced to the outlets and data portals listed below.*
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--category", "-c", required=True, choices=CATS)
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--slug")
    a = ap.parse_args()

    slug = a.slug or slugify(a.title)
    path = os.path.join(ROOT, "content", "posts", f"{a.date}-{slug}.md")
    if os.path.exists(path):
        print(f"refusing to overwrite {path}")
        return 1
    d = dt.date.fromisoformat(a.date)
    with open(path, "w", encoding="utf-8") as f:
        f.write(TEMPLATE.format(title=a.title.replace('"', "'"), slug=slug,
                                category=a.category, date=a.date,
                                pretty=d.strftime("%d %B %Y").lstrip("0")))
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
