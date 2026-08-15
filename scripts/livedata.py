#!/usr/bin/env python3
"""
Build-time live data for the "Korea now" strip on the homepage.

Fetched during the build rather than in the reader's browser. That choice is
deliberate:

  * no third-party script runs on the page, so nothing can inject layout shift
    or slow first paint — both are scored by Core Web Vitals and AdSense
  * the numbers are baked into the HTML, so they render instantly and work with
    JavaScript disabled
  * the site rebuilds every day when the article task runs, so the values are
    never more than a day old, and each one is stamped with when it was read

Every value is cached to content/_data/live.json. If an API is unreachable at
build time the cached value is reused and its original timestamp kept, so a
transient outage degrades to "slightly stale" rather than "blank" or, worse,
"wrong but confident".

APIs used (both free, no key, no attribution requirement beyond naming them):
  * exchangerate-api.com open endpoint — USD base rates
  * open-meteo.com — Seoul current conditions
"""
from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "content", "_data", "live.json")
TIMEOUT = 12
UA = "futureofkorea-build/1.0 (+https://futureofkorea.com/)"

FX_URL = "https://open.er-api.com/v6/latest/USD"
WX_URL = ("https://api.open-meteo.com/v1/forecast?latitude=37.5665&longitude=126.9780"
          "&current=temperature_2m,relative_humidity_2m,weather_code"
          "&daily=temperature_2m_max,temperature_2m_min"
          "&timezone=Asia%2FSeoul&forecast_days=1")

# WMO weather codes → (label, glyph). Kept deliberately small and text-first.
WMO = {
    0: ("Clear", "☀"), 1: ("Mainly clear", "🌤"), 2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁"), 45: ("Fog", "🌫"), 48: ("Freezing fog", "🌫"),
    51: ("Light drizzle", "🌦"), 53: ("Drizzle", "🌦"), 55: ("Heavy drizzle", "🌦"),
    61: ("Light rain", "🌧"), 63: ("Rain", "🌧"), 65: ("Heavy rain", "🌧"),
    66: ("Freezing rain", "🌧"), 67: ("Freezing rain", "🌧"),
    71: ("Light snow", "🌨"), 73: ("Snow", "🌨"), 75: ("Heavy snow", "🌨"),
    77: ("Snow grains", "🌨"), 80: ("Showers", "🌦"), 81: ("Showers", "🌦"),
    82: ("Violent showers", "⛈"), 85: ("Snow showers", "🌨"), 86: ("Snow showers", "🌨"),
    95: ("Thunderstorm", "⛈"), 96: ("Thunderstorm, hail", "⛈"), 99: ("Thunderstorm, hail", "⛈"),
}


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _load_cache() -> dict:
    try:
        return json.load(open(CACHE, encoding="utf-8"))
    except Exception:                                    # noqa: BLE001
        return {}


def _save_cache(data: dict) -> None:
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    json.dump(data, open(CACHE, "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def fetch(offline: bool = False) -> dict:
    cache = _load_cache()
    out = dict(cache)
    now = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")

    if not offline:
        try:
            d = _get(FX_URL)
            krw = float(d["rates"]["KRW"])
            out["fx"] = {
                "usd_krw": round(krw, 2),
                "krw_usd": round(1.0 / krw, 6),
                "source": "exchangerate-api.com",
                "as_of": d.get("time_last_update_utc") or now,
                "fetched": now,
                "stale": False,
            }
        except Exception as e:                           # noqa: BLE001
            print(f"  livedata: FX fetch failed ({type(e).__name__}) — using cache")
            if out.get("fx"):
                out["fx"]["stale"] = True

        try:
            d = _get(WX_URL)
            cur = d["current"]
            day = d.get("daily", {})
            code = int(cur.get("weather_code", 0))
            label, glyph = WMO.get(code, ("—", "•"))
            out["weather"] = {
                "temp_c": round(float(cur["temperature_2m"])),
                "humidity": int(cur.get("relative_humidity_2m", 0)),
                "label": label,
                "glyph": glyph,
                "high_c": round(float(day.get("temperature_2m_max", [None])[0]))
                          if day.get("temperature_2m_max") else None,
                "low_c": round(float(day.get("temperature_2m_min", [None])[0]))
                         if day.get("temperature_2m_min") else None,
                "source": "open-meteo.com",
                "fetched": now,
                "stale": False,
            }
        except Exception as e:                           # noqa: BLE001
            print(f"  livedata: weather fetch failed ({type(e).__name__}) — using cache")
            if out.get("weather"):
                out["weather"]["stale"] = True

    if out != cache:
        _save_cache(out)
    return out


def render(data: dict) -> str:
    """The homepage strip. Returns '' when there is nothing trustworthy to show."""
    fx, wx = data.get("fx"), data.get("weather")
    if not fx and not wx:
        return ""

    cells = []
    if fx:
        stale = ' data-stale="1"' if fx.get("stale") else ""
        krw_usd = fx["krw_usd"]
        # One cell, both directions. A second "₩1,000,000 buys" cell was dropped
        # as redundant — it restated the same rate in different units.
        cells.append(
            f'<div class="now-cell now-fx"{stale}>'
            f'<span class="now-icon" aria-hidden="true">₩</span>'
            f'<span class="now-k">Won / Dollar</span>'
            f'<span class="now-v" translate="no">₩{fx["usd_krw"]:,.2f}<span class="now-unit"> per $1</span></span>'
            f'<span class="now-s" translate="no">$1 = ₩{fx["usd_krw"]:,.0f} · ₩1,000 = ${1000 * krw_usd:,.2f}</span>'
            f'</div>')
    if wx:
        stale = ' data-stale="1"' if wx.get("stale") else ""
        rng = ""
        if wx.get("high_c") is not None and wx.get("low_c") is not None:
            rng = f'{wx["low_c"]}° / {wx["high_c"]}° today'
        cells.append(
            f'<div class="now-cell now-wx"{stale}>'
            f'<span class="now-icon" aria-hidden="true">{wx["glyph"]}</span>'
            f'<span class="now-k">Seoul right now</span>'
            f'<span class="now-v" translate="no">{wx["temp_c"]}<span class="now-unit">°C</span></span>'
            f'<span class="now-s">{wx["label"]}{" · " + rng if rng else ""}</span>'
            f'</div>')

    srcs = " · ".join(filter(None, [
        (fx or {}).get("source"), (wx or {}).get("source")]))
    when = (fx or wx or {}).get("fetched", "")[:10]

    return f"""<section class="korea-now" aria-label="Korea at a glance">
  <div class="wrap">
    <div class="now-grid">{''.join(cells)}</div>
    <p class="now-foot muted small">Refreshed each build · {when} · {srcs} ·
    indicative mid-market rates, not dealing prices.</p>
  </div>
</section>"""


if __name__ == "__main__":
    import sys
    d = fetch(offline="--offline" in sys.argv)
    print(json.dumps(d, indent=2, ensure_ascii=False))
    print("\n--- html ---\n")
    print(render(d))
