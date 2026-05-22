<!-- this_file: examples/expected/webflow_retro_poster.md -->

# Expected output — `webflow_retro_poster.py`

Captured from a real run on 2026-05-22 (`uv sync --extra all`, Chromium
installed). Slide counts depend on the live page and on each engine's metrics,
so treat these as representative, not exact.

## Input

- URL: <https://www.vexy.art/lines/case-retro-poster/>
- Classified as: **webflow** (confidence 0.50)
- Stage: 1920×1080 (default 16:9)

## Run summary (`_meta/run-summary.json`)

```json
{
  "source": "https://www.vexy.art/lines/case-retro-poster/",
  "framework": "webflow",
  "slides": 33,
  "results": [
    { "strategy": "playwright", "ok": true, "slides": 18, "error": null },
    { "strategy": "weasyprint", "ok": true, "slides": 26, "error": null }
  ]
}
```

`slides: 33` is the pagination plan from the viewport probe; each engine then
renders its own count (Playwright 18, WeasyPrint 26). The divergence is the
point — pick the best rendering of each slide across the two folders.

## Output tree (PDFs are gitignored under `examples/output/`)

```
examples/output/retro-poster/www-vexy-art-lines-case-retro-poster/
├── raw/
│   ├── index.html              # 37 KB localized page
│   └── assets/                 # 38 localized files (css/js/img/fonts)
├── _meta/
│   ├── page.json  slideplan.json  run-summary.json
│   └── cache/                  # content-addressed render cache
├── playwright/
│   ├── 01-slide.pdf … 18-slide.pdf   (~780 KB total)
│   └── index.html              # reveal preview
└── weasyprint/
    ├── 01-slide.pdf … 26-slide.pdf   (~604 KB total)
    └── index.html
```

## Notes / caveats

- Two source assets returned `404`/`403` (a hashed path and
  `cdn.prod.website-files.com` blocking non-browser fetches). Localization logs
  a warning and continues — a few slides whose only content was a blocked
  background image render nearly empty (~570-byte PDFs). This is upstream asset
  blocking, not a pipeline failure; the run still exits `0`.
- Re-running is near-instant on the second pass thanks to the render cache; pass
  `--no-cache` (or set it in the script) to force a fresh render.
