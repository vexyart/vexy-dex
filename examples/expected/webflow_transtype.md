<!-- this_file: examples/expected/webflow_transtype.md -->

# Expected output — `webflow_transtype.py`

Captured 2026-05-22. Slide counts vary with the live page and engine metrics.

- Input: <https://www.fontlab.com/font-converter/transtype/>
- Classified: **webflow** (confidence 0.50)
- Stage: 1920×1080

```json
{
  "source": "https://www.fontlab.com/font-converter/transtype/",
  "framework": "webflow",
  "slides": 18,
  "results": [
    { "strategy": "playwright", "ok": true, "slides": 14 },
    { "strategy": "weasyprint", "ok": true, "slides": 17 }
  ]
}
```

## Why this example matters

This page has only **1 `<section>` tag** but ~146 `*section*`-classed `<div>`s
(component pieces, not slide containers). Naive `<section>` selection finds
nothing, and trafilatura collapses marketing pages — so an early build produced
**1 slide** despite an 18-slide plan.

The Webflow importer now detects the thin-section case, drops chrome
(nav/footer/menu/banner), and distributes the `page-wrapper`'s block children
into the planned slide count (`dom.sectionize` descends single wrappers). Result:
**14 / 17 slides**, close to the plan — a deck instead of a single page.

Regression-tested in `tests/test_importers.py::test_webflow_divsection_page_uses_plan_fallback`.
