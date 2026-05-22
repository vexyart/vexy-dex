<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

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
