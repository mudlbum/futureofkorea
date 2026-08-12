---
title: "The HBM4 handover: who actually supplies the AI memory in 2026"
slug: hbm4-2026-sk-hynix-samsung-micron
seo_title: "HBM4 in 2026: Who Supplies the AI Memory"
meta: "SK hynix still leads high-bandwidth memory, Micron has passed Samsung on some measures, and HBM4 resets the board. What the share numbers really mean."
category: technology
date: 2026-08-10
updated: 2026-08-12
description: "SK hynix still leads high-bandwidth memory, Micron has overtaken Samsung on some measures, and the HBM4 qualification race for NVIDIA's Rubin platform resets the board. What the share numbers mean and what they don't."
image_alt: "Abstract network artwork representing high-bandwidth memory supply chains"
tags: [HBM, HBM4, SK hynix, Samsung Electronics, Micron, DRAM, NVIDIA Rubin, semiconductors]
about: ["High Bandwidth Memory", "SK hynix", "Samsung Electronics", "Micron Technology", "DRAM"]
key_takeaways:
  - "SK hynix remains the HBM leader but its share has been **falling from a very high base** — roughly 69% a year ago, about 58% in Q1 2026 on Counterpoint's numbering, with other trackers putting the current figure in the 50–55% range."
  - "**Micron overtook Samsung** on several 2026 share estimates, which is the genuinely new fact — Samsung is no longer automatically the number two in HBM."
  - "The **HBM market roughly grows from $38bn in 2025 to $58bn in 2026**. HBM3E remains about two-thirds of shipments; HBM4 ramps through the second half."
  - "UBS projects **SK hynix at roughly 70% of HBM4 for NVIDIA's Rubin platform** in 2026 — but Samsung was reportedly first to supply HBM4 to NVIDIA, so the qualification race is not settled."
  - "Capacity is the constraint everyone is racing: **Samsung targeting ~50% capacity expansion in 2026**, SK hynix raising infrastructure investment by more than four times its previous plan."
video:
  id: MgAH_jA_tNA
  title: "What's driving South Korea's epic stock market rally? — the AI memory cycle in context"
  channel: "BBC World Service — Asia Specific"
faq:
  - q: "Why do published HBM market-share figures disagree so much?"
    a: "Because they measure different things. Some trackers count revenue, some count bit shipments, some count wafer starts. Some report a single quarter, some a trailing year. HBM3E and HBM4 carry very different prices per bit, so a revenue-share number and a volume-share number can diverge by twenty points and both be correct. When you see an HBM share figure, always establish three things: revenue or volume, which quarter, and which generations are included."
  - q: "What actually is HBM, in one paragraph?"
    a: "High-Bandwidth Memory is DRAM stacked vertically into a cube, connected by through-silicon vias, and placed on the same package as the processor. Instead of data crossing a long, narrow path to distant memory modules, it crosses a very short, very wide one. For AI training and inference — which are memory-bandwidth-bound far more than they are compute-bound — this is the difference between an accelerator running at capacity and one waiting for data."
  - q: "Is HBM4 a bigger jump than previous generations?"
    a: "Structurally, yes. HBM4 widens the interface substantially and, critically, changes the base die — the logic layer at the bottom of the stack — into something closer to a custom logic component, which pulls foundry capability into what was previously a pure memory problem. That is why the competitive order in HBM4 is not guaranteed to match HBM3E: it rewards a different mix of skills."
  - q: "Does this mean Samsung is losing?"
    a: "It means Samsung lost the HBM3E generation's early lead and is trying to recover position in HBM4. It is the world's largest memory manufacturer by overall capacity and it is expanding aggressively. A company can simultaneously be third in one high-value product line and structurally central to the industry. Both things are true here."
  - q: "How does this connect to the KOSPI?"
    a: "Directly and almost mechanically. Samsung Electronics and SK hynix dominate the Korean index, and HBM economics drove their 2026 earnings expectations. The index's near-doubling and subsequent crash were, in substance, a repricing of this one product cycle — see our [2026 crash explainer](/markets/kospi-crash-2026-explained/)."
  - q: "What would change the picture fastest?"
    a: "A qualification decision. HBM supply is sole-sourced or dual-sourced per accelerator platform, and being designed into a flagship product locks in volume for years. Watch for qualification announcements around NVIDIA's Rubin generation and for custom-accelerator programmes at the large cloud providers, which increasingly specify their own memory partners."
resources:
  - title: "SK hynix newsroom — market outlook and HBM announcements"
    url: "https://news.skhynix.com/"
    note: "First-party product and capacity announcements, in English."
  - title: "Samsung Semiconductor newsroom"
    url: "https://semiconductor.samsung.com/news-events/"
    note: "Product launches, process-node and packaging announcements."
  - title: "DART — Korean company filings"
    url: "https://dart.fss.or.kr/"
    note: "Quarterly results and capex disclosures for both Korean suppliers, in primary form."
  - title: "Counterpoint Research — DRAM and HBM market share tracker"
    url: "https://counterpointresearch.com/en/insights/global-dram-and-hbm-market-share"
    note: "One of the more transparent public share trackers; note its methodology before quoting it."
  - title: "Korea Customs Service — trade statistics"
    url: "https://unipass.customs.go.kr/ets/"
    note: "Semiconductor export values by month — the fastest public read on the cycle."
sources:
  - title: "2026 Market Outlook: SK hynix's HBM to fuel AI memory boom"
    url: "https://news.skhynix.com/2026-market-outlook-focus-on-the-hbm-led-memory-supercycle/"
    publisher: "SK hynix newsroom"
  - title: "SK hynix holds 62% of HBM, Micron overtakes Samsung, 2026 battle pivots to HBM4"
    url: "https://www.astutegroup.com/news/general/sk-hynix-holds-62-of-hbm-micron-overtakes-samsung-2026-battle-pivots-to-hbm4/"
    publisher: "Astute Group, 2026"
  - title: "Global DRAM and HBM market share, quarterly"
    url: "https://counterpointresearch.com/en/insights/global-dram-and-hbm-market-share"
    publisher: "Counterpoint Research"
  - title: "Samsung and SK Hynix to scale up memory production capacity in 2026"
    url: "https://www.datacenterdynamics.com/en/news/samsung-and-sk-hynix-to-scale-up-memory-production-capacity-in-2026-to-meet-ai-demand/"
    publisher: "Data Center Dynamics, 2026"
  - title: "SK hynix, Samsung: HBM4 readiness, 1c DRAM scaling and the 2026 capacity race"
    url: "https://siliconanalysts.com/analysis/sk-hynix-samsung-2026-memory-capex-hbm4-qualification-race"
    publisher: "Silicon Analysts, 2026"
---

Roughly two Korean companies decide how fast the world's AI infrastructure can be built. That is not hyperbole — it is a description of the high-bandwidth memory market, and it is the reason the Korean stock index behaved like a leveraged AI bet in 2026.

The competitive picture inside that market changed meaningfully this year. Here is what actually moved.

## First, the number that isn't one number

If you search for HBM market share you will find figures that contradict each other by twenty percentage points. All of them are being quoted in good faith. Consider a representative sample from 2026 coverage:

| Source framing | SK hynix | Samsung | Micron |
| --- | --- | --- | --- |
| Q2 2025 share | 62% | 17% | 21% |
| Q1 2026 (Counterpoint) | 58% | — | — |
| More recent range estimates | 50–55% | 35–40% | 5–10% |

These cannot all describe the same quantity, and they don't.

> [!WARNING] Read the methodology before you quote the number
> HBM share is measured variously by **revenue**, by **bit shipments**, and by **wafer allocation**. HBM3E and HBM4 sell at very different prices per bit, so a supplier with lower volume but a richer generation mix can lead on revenue and trail on bits. Add differing quarter definitions and you get the spread above. A share figure without a stated methodology and quarter is decoration, not data.

What *is* consistent across every source is the direction of travel: **SK hynix still leads, and its lead is narrowing from an extraordinarily high base.** Roughly 69% a year ago. Around 58% in Q1 2026 on Counterpoint's numbering. That is still dominance. It is also a company giving up share every quarter, which is a different story from the one told in 2024.

## The genuinely new fact: Micron passed Samsung

The headline most people missed is not about SK hynix at all. On several 2026 estimates, **Micron overtook Samsung** in HBM.

That would have been an implausible claim two years ago. Samsung is the largest memory manufacturer on earth by capacity. But HBM is not commodity DRAM — it is a stacking, packaging, thermal and yield problem as much as a lithography one, and Samsung's difficulties qualifying HBM3E with the dominant accelerator customer cost it a generation of position while Micron executed cleanly.

The lesson generalises: **in HBM, capacity is necessary and nowhere near sufficient.** Qualification is the gate.

## What HBM4 changes

The market is growing from roughly **$38bn in 2025 to $58bn in 2026**. HBM3E still accounts for about **two-thirds of 2026 shipments**; HBM4 ramps through the second half.

HBM4 is not a routine increment. Two changes matter:

**The interface widens dramatically.** More parallel lanes at lower per-lane rates — better bandwidth per watt, harder signal integrity and packaging.

**The base die becomes a logic problem.** The layer at the bottom of an HBM4 stack moves closer to a custom logic die, which drags foundry-grade capability into what used to be a pure memory competition. That is why HBM4 positions are not simply inherited from HBM3E: the required skill mix has changed, and companies with strong logic and packaging arms have a route back in.

> [!KEY] Where HBM4 stands right now
> UBS projects **SK hynix at roughly 70% of HBM4 supply for NVIDIA's Rubin platform** in 2026. In the same period, **Samsung was reported as the first supplier of HBM4 to NVIDIA**. Both can be true — first-to-qualify and largest-allocation are separate outcomes — and together they explain why nobody should treat the HBM4 order as settled.

## The capacity race underneath

Both Korean suppliers are spending against the same bet, that AI memory demand outruns supply through 2027:

- **Samsung** is targeting roughly **50% capacity expansion in 2026**.
- **SK hynix** has raised planned infrastructure investment to **more than four times its previously announced figure**.

Numbers of that shape carry a specific risk. HBM capacity is not fungible — it is built for a generation and a customer, with committed advanced-packaging lines behind it. If accelerator demand slows while three suppliers are mid-expansion, the industry gets a classic memory glut, except in a product with much higher fixed costs. The memory industry has run this experiment before, repeatedly, and it has never ended gently.

> [!ACTION] The four indicators worth tracking
> - **Qualification announcements** for the Rubin generation and for hyperscaler custom accelerators. This is the single highest-information event class.
> - **Korea's monthly semiconductor export value**, from Korea Customs Service — the fastest public read on the cycle, published early each month.
> - **Quarterly capex guidance** in the DART filings, not the press releases. Look for capex being *pulled forward* or *pushed out*; that is management telling you what it really thinks.
> - **Conventional DRAM pricing.** HBM consumes wafer capacity that would otherwise make standard DRAM, so HBM strength tightens the commodity market too. When that relationship breaks, something has changed.

## Why this is a Korea story and not just a semiconductor story

Because of concentration. Samsung Electronics and SK hynix together make up a very large share of the KOSPI, and HBM economics drove their 2026 earnings expectations. When the index gained about 92% in the first half of the year and then fell some 40% from its June peak, that was — in substance — the market repricing this one product cycle twice in six months. We covered the mechanics in [the 2026 crash explainer](/markets/kospi-crash-2026-explained/).

For anyone holding a Korea ETF, the practical implication is blunt: **you own the HBM cycle, whether or not you meant to.** Our [guide to buying Korean stocks from abroad](/markets/how-to-buy-korean-stocks-from-abroad/) sets out how to see that concentration in your own holdings before you size a position.

> [!TIP] A quick sanity check on any HBM headline
> Ask: *revenue or bits? which quarter? which generations?* If a piece of coverage can't answer all three, it is repeating someone else's number without knowing what it measures. That single habit will make you better informed than most of the commentary on this industry.

*Figures current as of 12 August 2026, sourced to the outlets and company disclosures listed below. Where trackers disagree, we have shown the range rather than selecting one.*
