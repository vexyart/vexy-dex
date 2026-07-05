---
title: vexy-dexypy
layout: default
---

<!-- this_file: docs/index.md -->

# vexy-dexypy

Turn **any** web page into slide decks — several engines at once — and keep the
slides you like.

![One URL fanning out into five stacks of printed slides](assets/icon.png)

`vexy-dexypy` takes one URL, works out where the slides hiding inside the page
should break, and renders it to PDF through several engines in parallel. Each
engine writes its own folder of single-page PDFs. You skim the folders and build
your final deck from the best version of each slide. No two engines paginate a
page the same way, and that is the point: you get a menu, not a verdict.

## Quick start

```bash
uv pip install vexy-dexypy
playwright install chromium

# Everything, every available strategy, default 720p
vexy-dexypy build https://www.vexy.art/lines/
```

Output lands under `out/`, one folder per engine, plus a `_meta/` folder with the
slide plan and a run summary:

```
out/lines/
  playwright/   01-slide.pdf  02-slide.pdf  …  index.html
  vivliostyle/  01-slide.pdf  …
  reveal/       01-slide.pdf  …
  _meta/        slideplan.json  run-summary.json
```

A failed engine degrades to a warning — the run still hands you the decks that
worked, and tells you how to fix the one that didn't.

## The six stages

1. **Read** — fetch the HTML and localize assets so it works offline.
2. **Analyze** — recognize the page (Webflow, MkDocs Material, …) and plan the
   slide breaks at your target aspect ratio.
3. **Normalize** — restructure the DOM into slide-shaped sections in the browser
   via the companion package [`vexy-dexyjs`](https://github.com/vexyart/vexy-dexyjs).
4. **Prepare** — inject the paged-media CSS or reveal.js wrapping each engine wants.
5. **Render** — export to PDF through every chosen engine, in parallel.
6. **Write** — split each PDF into named single-page slides, optionally as SVG,
   with an HTML preview to browse.

## The engines

| Strategy | Engine | Best for |
|---|---|---|
| `playwright` | Headless Chromium | Webflow, JS-heavy, highly styled pages |
| `vivliostyle` | Chromium typesetting | Long-form / documentation, strong paged media |
| `reveal` | Native reveal.js | The reveal.js path, crisp per-slide capture |
| `prince` | PrinceXML (opt-in) | Reference-quality paged media, if you have a licence |

Install only what you want — a strategy whose tool is missing is skipped with a
note, never a crash.

## Learn more

- [README](https://github.com/vexyart/vexy-dexypy#readme) — the full tour.
- [`spec/`](https://github.com/vexyart/vexy-dexypy/tree/main/spec) — the
  24-chapter design specification.
- [`vexy-dexyjs`](https://vexyart.github.io/vexy-dexyjs/) — the browser
  preprocessor that does the DOM normalization.
