"""
Deterministic, offline artwork generator for Future of Korea.

No external API, no network, no licensing risk: every hero image and social card
is drawn procedurally with Pillow from a seed derived from the post slug, so the
same post always produces the same artwork and every post looks different.

Outputs per post:
  dist/img/<slug>-hero.webp   1600x900  (article hero)
  dist/img/<slug>-og.png      1200x630  (Open Graph / Twitter card, with title)
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import re
import textwrap

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")

PALETTES = {
    "markets":    [("#0a0e1a", "#131c33"), "#c8102e", "#ff5a6e", "#f4c04e"],
    "technology": [("#050b16", "#0d2140"), "#0b6efd", "#57b8ff", "#7ef3d0"],
    "living":     [("#06140f", "#0d2c22"), "#0f9d76", "#5fe3b4", "#ffd166"],
    "society":    [("#0d0718", "#1e1236"), "#7c3aed", "#b98cff", "#ff9ecb"],
    "policy":     [("#160d02", "#2e1a06"), "#e07a00", "#ffb340", "#ffe5a3"],
    "_default":   [("#0a0e1a", "#141c2e"), "#c8102e", "#7aa2ff", "#f4c04e"],
}


def _hex(c: str):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _seed(slug: str) -> random.Random:
    return random.Random(int(hashlib.sha256(slug.encode()).hexdigest()[:16], 16))


def _font(name: str, size: int):
    path = os.path.join(FONT_DIR, name)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _gradient(size, top, bottom, rnd):
    w, h = size
    base = Image.new("RGB", (1, h))
    px = base.load()
    t, b = _hex(top), _hex(bottom)
    ang = rnd.random()
    for y in range(h):
        f = (y / max(h - 1, 1)) ** (0.8 + ang * 0.6)
        px[0, y] = tuple(int(t[i] + (b[i] - t[i]) * f) for i in range(3))
    return base.resize((w, h), Image.BILINEAR)


def _glow(img, cx, cy, radius, colour, strength=0.55):
    layer = Image.new("RGB", img.size, (0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=_hex(colour))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.55))
    return Image.blend(img, Image.blend(img, layer, 1.0), 0).point(lambda v: v) if False else \
        Image.fromarray(_screen(img, layer, strength))


def _screen(a, b, strength):
    import numpy as np
    A = np.asarray(a).astype("float32") / 255.0
    B = (np.asarray(b).astype("float32") / 255.0) * strength
    out = 1.0 - (1.0 - A) * (1.0 - B)
    return (out.clip(0, 1) * 255).astype("uint8")


def _topography(draw, w, h, rnd, colour, lines=26, alpha=70):
    """Contour-style ridgelines — reads as data/terrain, on-brief for an analysis site."""
    col = _hex(colour)
    for i in range(lines):
        base_y = h * (i + 0.5) / lines
        amp = rnd.uniform(h * 0.015, h * 0.075)
        freq = rnd.uniform(1.1, 3.4)
        phase = rnd.uniform(0, math.tau)
        pts = []
        for x in range(0, w + 8, 8):
            t = x / w
            y = base_y + math.sin(t * math.tau * freq + phase) * amp \
                       + math.sin(t * math.tau * freq * 2.3 + phase * 1.7) * amp * 0.35
            pts.append((x, y))
        draw.line(pts, fill=col + (alpha,), width=rnd.choice([1, 1, 2]), joint="curve")


def _bars(draw, w, h, rnd, colour, accent):
    """A faint chart motif anchored bottom-left."""
    n = rnd.randint(9, 16)
    bw = w * 0.030
    gap = bw * 0.55
    total = n * (bw + gap)
    x0 = w * 0.06
    v = rnd.uniform(0.25, 0.5)
    for i in range(n):
        v = max(0.08, min(1.0, v + rnd.uniform(-0.18, 0.26)))
        bh = h * 0.34 * v
        x = x0 + i * (bw + gap)
        c = _hex(accent if i == n - 1 else colour)
        draw.rounded_rectangle([x, h * 0.86 - bh, x + bw, h * 0.86], radius=int(bw * 0.28),
                               fill=c + (150 if i == n - 1 else 70,))


def _nodes(draw, w, h, rnd, colour, accent, count=16):
    pts = [(rnd.uniform(w * 0.45, w * 0.98), rnd.uniform(h * 0.08, h * 0.92)) for _ in range(count)]
    col = _hex(colour)
    for i, p in enumerate(pts):
        for q in pts[i + 1:]:
            d = math.dist(p, q)
            if d < w * 0.17:
                a = int(90 * (1 - d / (w * 0.17)))
                draw.line([p, q], fill=col + (a,), width=1)
    for i, p in enumerate(pts):
        r = rnd.uniform(2.5, 7.0)
        c = _hex(accent) if i % 5 == 0 else col
        draw.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=c + (190,))


def _grid(draw, w, h, colour, step=64, alpha=26):
    col = _hex(colour) + (alpha,)
    for x in range(0, w, step):
        draw.line([(x, 0), (x, h)], fill=col, width=1)
    for y in range(0, h, step):
        draw.line([(0, y), (w, y)], fill=col, width=1)


def _grain(img, rnd, amount=7):
    import numpy as np
    a = np.asarray(img).astype("int16")
    noise = np.random.default_rng(rnd.randint(0, 2**32 - 1)).normal(0, amount, a.shape[:2])
    a = (a + noise[..., None]).clip(0, 255).astype("uint8")
    return Image.fromarray(a)


def _canvas(slug: str, category: str, size):
    pal = PALETTES.get(category, PALETTES["_default"])
    (top, bottom), primary, secondary, highlight = pal
    rnd = _seed(slug)
    w, h = size

    img = _gradient(size, top, bottom, rnd).convert("RGB")
    img = _glow(img, w * rnd.uniform(0.55, 0.9), h * rnd.uniform(0.1, 0.5),
                w * rnd.uniform(0.28, 0.45), primary, 0.5)
    img = _glow(img, w * rnd.uniform(0.02, 0.3), h * rnd.uniform(0.55, 0.95),
                w * rnd.uniform(0.22, 0.36), secondary, 0.35)

    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    _grid(d, w, h, "#ffffff", step=int(w / 22))

    motif = rnd.choice(["topo", "nodes", "bars", "topo", "nodes"])
    if motif == "topo":
        _topography(d, w, h, rnd, "#ffffff", lines=rnd.randint(20, 32), alpha=rnd.randint(45, 85))
        _bars(d, w, h, rnd, secondary, highlight)
    elif motif == "nodes":
        _nodes(d, w, h, rnd, secondary, highlight, count=rnd.randint(14, 22))
        _topography(d, w, h, rnd, "#ffffff", lines=10, alpha=30)
    else:
        _bars(d, w, h, rnd, secondary, highlight)
        _nodes(d, w, h, rnd, secondary, highlight, count=10)

    # Signature arc — a nod to the taegeuk without reproducing the flag.
    r = w * rnd.uniform(0.16, 0.26)
    cx, cy = w * rnd.uniform(0.62, 0.86), h * rnd.uniform(0.22, 0.6)
    d.arc([cx - r, cy - r, cx + r, cy + r], rnd.randint(0, 360), rnd.randint(120, 300),
          fill=_hex(highlight) + (170,), width=max(2, int(w * 0.0035)))

    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    return _grain(img, rnd), pal


FIGURE_RE = re.compile(r"\*\*([^*]*\d[^*]*)\*\*")


def lead_figure(post: dict) -> str:
    """The first bolded number the article itself leads with, e.g. '92%' or '₩104.8tn'."""
    for item in post.get("key_takeaways") or []:
        text = item.get("text", "") if isinstance(item, dict) else str(item)
        m = FIGURE_RE.search(text)
        if m:
            fig = m.group(1).strip().rstrip(".,;:")
            if len(fig) <= 26:
                return fig
    return ""


def editorial_cover(post: dict, out_path: str, size=(1600, 900)):
    """
    Typographic cover built from the article's own headline and lead figure.

    Used when a post declares no `chart:` block. Unlike decorative art, this is
    never unrelated to the piece — every word on it comes from the piece.
    """
    slug, category = post["slug"], post.get("category", "_default")
    img, pal = _canvas(slug, category, size)
    (_, _), primary, secondary, highlight = pal
    w, h = size

    scrim = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim, "RGBA")
    for i in range(h):
        sd.line([(0, i), (w, i)], fill=(4, 7, 14, int(150 + 85 * (i / h) ** 0.7)))
    img = Image.alpha_composite(img.convert("RGBA"), scrim).convert("RGB")

    d = ImageDraw.Draw(img, "RGBA")
    pad = int(w * 0.055)

    kicker = str(post.get("category_name") or category).upper()
    kf = _font("GeistMono-Regular.ttf", int(w * 0.0165))
    d.rectangle([pad, pad + 4, pad + 5, pad + int(w * 0.019)], fill=_hex(highlight))
    d.text((pad + 18, pad), kicker, font=kf, fill=_hex(highlight) + (240,))

    fig = lead_figure(post)
    y_cursor = h - pad
    if fig:
        ff = _font("InstrumentSans-Bold.ttf", int(w * 0.105))
        fw = d.textlength(fig, font=ff)
        if fw > w - pad * 2:
            ff = _font("InstrumentSans-Bold.ttf", int(w * 0.105 * (w - pad * 2) / fw))
        fh = int(w * 0.105 * 1.05)
        y_cursor = h - pad - fh
        d.text((pad + 3, y_cursor + 3), fig, font=ff, fill=(0, 0, 0, 120))
        d.text((pad, y_cursor), fig, font=ff, fill=_hex(highlight) + (255,))
        d.line([(pad, y_cursor - int(h * 0.035)), (pad + int(w * 0.07), y_cursor - int(h * 0.035))],
               fill=_hex(highlight) + (200,), width=4)
        y_cursor -= int(h * 0.075)

    title = str(post.get("title", ""))
    box_h = max(int(h * 0.20), y_cursor - pad - int(w * 0.05))
    f, lines, fs = _fit(d, title, "InstrumentSans-Bold.ttf", w - pad * 2, box_h,
                        int(w * 0.048), min_size=int(w * 0.022))
    y = y_cursor - len(lines) * fs * 1.14
    for line in lines:
        d.text((pad + 2, y + 2), line, font=f, fill=(0, 0, 0, 130))
        d.text((pad, y), line, font=f, fill=(255, 255, 255, 250))
        y += fs * 1.14

    mono = _font("GeistMono-Regular.ttf", int(w * 0.0135))
    d.text((w - pad - d.textlength("futureofkorea.com", font=mono), pad),
           "futureofkorea.com", font=mono, fill=(255, 255, 255, 150))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "WEBP", quality=86, method=6)
    return out_path


def hero(post, category=None, out_path=None, size=(1600, 900)):
    """
    Article hero. Renders the post's data as a chart when it declares one,
    otherwise a typographic cover derived from its headline and lead figure.

    Accepts the modern form hero(post_dict, out_path) and the legacy positional
    form hero(slug, category, out_path) so older callers keep working.
    """
    if isinstance(post, str):                       # legacy: (slug, category, path)
        post = {"slug": post, "category": category}
    else:
        out_path = category if out_path is None and isinstance(category, str) else out_path

    spec = post.get("chart")
    if spec:
        import chartgen
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        png = out_path.rsplit(".", 1)[0] + "-chart.png"
        chartgen.render(spec, post.get("category", "_default"), png, size=size,
                        headline=post.get("title"))
        Image.open(png).convert("RGB").save(out_path, "WEBP", quality=88, method=6)
        os.remove(png)
        return out_path

    return editorial_cover(post, out_path, size)


def _fit(draw, text, font_path, max_w, max_h, start, min_size=34, line_gap=1.16):
    size = start
    while size >= min_size:
        f = _font(font_path, size)
        approx = max(12, int(max_w / (size * 0.50)))
        lines = textwrap.wrap(text, width=approx)
        if not lines:
            lines = [text]
        widest = max(draw.textlength(l, font=f) for l in lines)
        height = len(lines) * size * line_gap
        if widest <= max_w and height <= max_h and len(lines) <= 4:
            return f, lines, size
        size -= 3
    f = _font(font_path, min_size)
    return f, textwrap.wrap(text, width=int(max_w / (min_size * 0.50)))[:4] or [text], min_size


def social_card(slug: str, category: str, title: str, kicker: str, out_path: str,
                site_name="FUTURE OF KOREA", size=(1200, 630)):
    img, pal = _canvas(slug, category, size)
    (_, _), primary, secondary, highlight = pal
    w, h = size

    scrim = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(scrim, "RGBA")
    for i in range(h):
        sd.line([(0, i), (w, i)], fill=(4, 7, 14, int(215 * (i / h) ** 0.55)))
    sd.rectangle([0, 0, w, h], outline=(255, 255, 255, 26), width=2)
    img = Image.alpha_composite(img.convert("RGBA"), scrim).convert("RGB")

    d = ImageDraw.Draw(img, "RGBA")
    pad = 64

    # Masthead
    mast = _font("InstrumentSans-Bold.ttf", 26)
    d.rectangle([pad, pad + 6, pad + 6, pad + 32], fill=_hex(highlight))
    d.text((pad + 20, pad + 2), site_name, font=mast, fill=(255, 255, 255, 235))

    # Kicker chip
    if kicker:
        kf = _font("GeistMono-Regular.ttf", 21)
        kw = d.textlength(kicker.upper(), font=kf)
        d.rounded_rectangle([pad, h - pad - 46, pad + kw + 40, h - pad], radius=23,
                            fill=_hex(highlight) + (36,), outline=_hex(highlight) + (150,), width=1)
        d.text((pad + 20, h - pad - 36), kicker.upper(), font=kf, fill=_hex(highlight) + (255,))

    # Title block
    box_w, box_h = w - pad * 2, h - pad * 2 - 190
    f, lines, fs = _fit(d, title, "InstrumentSans-Bold.ttf", box_w, box_h, 74)
    y = h - pad - 100 - len(lines) * fs * 1.16
    for line in lines:
        d.text((pad + 2, y + 2), line, font=f, fill=(0, 0, 0, 130))
        d.text((pad, y), line, font=f, fill=(255, 255, 255, 252))
        y += fs * 1.16

    d.text((w - pad - d.textlength("futureofkorea.com", font=_font("GeistMono-Regular.ttf", 21)),
            h - pad - 34), "futureofkorea.com",
           font=_font("GeistMono-Regular.ttf", 21), fill=(255, 255, 255, 155))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path


def logo(out_path: str, size=(512, 512)):
    w, h = size
    img = Image.new("RGB", size, _hex("#0a0e1a"))
    d = ImageDraw.Draw(img, "RGBA")
    for i in range(h):
        d.line([(0, i), (w, i)], fill=_hex("#0a0e1a") if i < h * .3 else _hex("#141c2e"))
    cx, cy, r = w * .5, h * .5, w * .30
    d.arc([cx - r, cy - r, cx + r, cy + r], 200, 20, fill=_hex("#c8102e"), width=int(w * .055))
    d.arc([cx - r * .62, cy - r * .62, cx + r * .62, cy + r * .62], 20, 200,
          fill=_hex("#7aa2ff"), width=int(w * .055))
    f = _font("InstrumentSans-Bold.ttf", int(w * .30))
    tw = d.textlength("FK", font=f)
    d.text((cx - tw / 2, cy - w * .19), "FK", font=f, fill=(255, 255, 255, 245))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    import sys
    slug = sys.argv[1] if len(sys.argv) > 1 else "demo-post"
    cat = sys.argv[2] if len(sys.argv) > 2 else "markets"
    hero(slug, cat, f"/tmp/{slug}-hero.webp")
    social_card(slug, cat, "Demo headline for the social card generator", cat, f"/tmp/{slug}-og.png")
    print("wrote /tmp")
