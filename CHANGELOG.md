<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

### Changed

- `examples/_runner.py` now defaults to `strategies="all"`, so examples exercise
  every engine whose deps are installed (playwright/decktape/prince here) and
  cleanly skip the rest via `available()`, instead of force-running a hardcoded
  `playwright,weasyprint` pair (which surfaced a loud GLib error for weasyprint).

### Spec — decouple the slide IR from reveal.js (planning)

The normalized IR was reveal-shaped (`.reveal > .slides`) emitted by importers,
so the five strategies diverged only by PDF engine, not by framework. Revised
the spec to make the **chassis** (reveal / paged / impress / marp) a per-strategy
stage-4 choice over a framework-neutral `<section class="slide">` IR, so genuine
alternatives to reveal are possible. Updated spec/03, spec/11, spec/15, spec/16,
spec/19 and added the refactor + `impress`/`marp` tasks to TODO.md. Code refactor
is tracked, not yet implemented.

### Fixed

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
