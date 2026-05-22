<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

### Changed

- **Replaced the Node/DeckTape `decktape` strategy with a native `reveal`
  exporter** (`exporters/reveal.py`): Playwright drives reveal.js
  (`getTotalSlides`/`slide`/`next`) and captures one `page.pdf` per slide,
  `pypdf` merges them. Drops the Node + `decktape` toolchain entirely — the
  reveal deck is initialized with `fragments:false` and all chrome off so the
  capture loop is deterministic. Strategy/output folder renamed `decktape` →
  `reveal`; classifier order updated.
- **Removed WeasyPrint support entirely** — exporter, entry point, extras,
  classifier orders, tests, examples and spec/doc references. The paged-media
  recommendation is now Vivliostyle (with Prince opt-in). `test_writers` builds
  its sample PDF with `pypdf` instead of WeasyPrint (also fixing the prior
  GLib-related failures). Shipped engines: playwright, vivliostyle, reveal, prince.
- `examples/_runner.py` now defaults to `strategies="all"`, so examples exercise
  every engine whose deps are installed and cleanly skip the rest via
  `available()`, instead of a hardcoded pair.

### Spec — decouple the slide IR from reveal.js (planning)

The normalized IR was reveal-shaped (`.reveal > .slides`) emitted by importers,
so the five strategies diverged only by PDF engine, not by framework. Revised
the spec to make the **chassis** (reveal / paged / impress / marp) a per-strategy
stage-4 choice over a framework-neutral `<section class="slide">` IR, so genuine
alternatives to reveal are possible. Updated spec/03, spec/11, spec/15, spec/16,
spec/19 and added the refactor + `impress`/`marp` tasks to TODO.md. Code refactor
is tracked, not yet implemented.

### Fixed

- **Localized pages rendered unstyled.** Three causes, all fixed:
  - Localized `<link>`/`<script>` kept `integrity`/`crossorigin`; under `file://`
    (and even http) Subresource Integrity blocks the now-local stylesheet. The
    localizer strips both attributes (`readers/localize.py`).
  - The Webflow importer dropped the page's stylesheets when wrapping slides —
    now carries them via `dom.head_styles` (matching the other importers).
  - An already-reveal-shaped live page (e.g. a vexy.art deck) short-circuited
    normalization and kept `assets/` refs relative to `raw/`, which broke once
    the HTML moved to the strategy dir. The `already_reveal` branch now relocates
    + rewrites paths via `write_normalized` for raw input (idempotent no-op for
    our own normalized output).
- **Browser navigation hardened.** All local-page rendering (playwright/reveal/
  vision/pagination probe) now serves the deck over a throwaway loopback HTTP
  server and waits for `load` instead of opening `file://` and waiting for
  `networkidle` — a real http:// origin avoids file:// CORS/SRI/font quirks, and
  `load` doesn't hang when offline JS retries dead CDN assets (`_browser.py`;
  fixes the fontlab-8 `Page.goto` timeout).
- **Webflow "Made in Webflow" badge** (`.w-webflow-badge`) is DOM-removed in the
  importer and force-hidden via the pre-exporter theme CSS.
- Reveal chassis now disables all reveal.js UI chrome (controls, progress,
  slide-number, help/pause overlays) via `Reveal.initialize` flags plus a CSS
  guard — slides are destined for PDF/SVG and must not show navigation buttons
  (`preexport._bundle_reveal`, spec/15).

- Content-extracting importers (mkdocs-material, docusaurus, generic) now carry
  the source page's stylesheet `<link>`s and `<style>` blocks into the reveal
  chassis via the new `dom.head_styles` helper. Previously `wrap_reveal` emitted
  an empty `<head>`, so the localized framework/highlight CSS (spec/07, spec/13)
  never loaded and decks rendered as unstyled prose.
- `examples/webflow_fontlab_8.py`: corrected a malformed `httpshttps://` URL and
  the copy-pasted header/docstring (was duplicating the homepage example).

### Added — initial implementation

The full six-stage pipeline, implemented and tested end-to-end.

- **Core**: typed IR (`model.py`), `Settings` with aspect/size profiles
  (default 1920×1080), typed error taxonomy, `loguru` logging.
- **CLI** (Fire): `build`, `read`, `analyze`, `split` with a rich per-strategy
  summary and 0/1/2 exit codes.
- **Stage 1 — readers**: static (httpx) + dynamic (Playwright) with plugin
  discovery, file handling, thin-body escalation, retry-with-backoff, tier-1
  asset localization, content hashing.
- **Stage 2 — pre-importers**: fingerprint classifier (webflow, mkdocs-material,
  docusaurus, framer, bubble, generic) with strategy-order recommendation;
  viewport bounding-box pagination with a no-browser fallback; optional
  MiniCPM-V vision refinement (cached, heuristic-floor).
- **Stage 3 — importers**: shared DOM helpers + webflow (adapted from
  webflow2reveal `compiler.py`), mkdocs-material, and generic (trafilatura)
  importers; idempotent on canonical input.
- **Stage 4 — pre-exporters**: paged-media CSS + neutral theme injection →
  `RenderJob`.
- **Stage 5 — exporters**: capability-aware selection; weasyprint, playwright,
  vivliostyle, decktape, prince with availability gating and subprocess
  discipline.
- **Stage 6 — writers**: pypdf split, optional SVG via vexy-pdfsvgpy, preview
  index; per-strategy failure isolation.
- **Tests**: 29 passing including a full pipeline integration through WeasyPrint;
  offline fixtures, `test.sh`, and a runnable example.
- **Docs**: `DEPENDENCIES.md` with the licence-hazard table.

### Notes

- Webflow logic copied & adapted from the author's legacy `webflow2reveal`
  (now first-class vexy-dex code; the package is slated for removal).
