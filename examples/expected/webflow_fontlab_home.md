<!-- this_file: examples/expected/webflow_fontlab_home.md -->

# Expected output — `webflow_fontlab_home.py`

Captured 2026-05-22. Slide counts vary with the live page and engine metrics.

- Input: <https://www.fontlab.com/>
- Classified: **webflow** (confidence 0.50)
- Stage: 1920×1080

```json
{
  "source": "https://www.fontlab.com/",
  "framework": "webflow",
  "slides": 3,
  "results": [
    { "strategy": "playwright", "ok": true, "slides": 2 },
    { "strategy": "weasyprint", "ok": true, "slides": 4 }
  ]
}
```

A short, hero-heavy homepage with a couple of real `<section>` tags — few
slides, mostly visual. Playwright keeps it tight (2); WeasyPrint splits the
footer-ish content into 4. Output under
`examples/output/fontlab-home/<strategy>/` (gitignored PDFs + `index.html`).
