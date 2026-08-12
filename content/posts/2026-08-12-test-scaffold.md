---
draft: true
title: "Draft example — safe to delete"
slug: draft-example
category: markets
description: "A draft placeholder. Files with `draft: true` are skipped by the build, so this never reaches the site."
---

This file exists only to demonstrate the `draft: true` flag: the build ignores it entirely, so
you can leave half-finished pieces in `content/posts/` without them appearing on the site.

Delete it whenever you like, or keep it as a reminder. To scaffold a real post, run:

```bash
python3 scripts/new_post.py "Your headline here" --category markets
```
