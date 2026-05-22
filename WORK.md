<!-- this_file: WORK.md -->

# WORK — progress log

## 2026-05-22 — MVP walking skeleton + CMS-aware pipeline

Implemented the full pipeline end-to-end. `vexy-dex build <local.html>
--strategies weasyprint` produces classified, normalized, paginated, split decks
with a preview index and JSON sidecars — verified on the mkdocs and generic
fixtures.

### Done

- **Project setup**: `pyproject.toml` (hatch-vcs, entry points for readers/
  importers/exporters), `uv` env, `DEPENDENCIES.md`, `.gitignore` for `out/`.
- **IR** (`model.py`): Source, PageDoc, Break, SlidePlan (sorted/deduped),
  Strategy, RenderJob, DeckResult + JSON sidecars.
- **Settings** (`settings.py`): flag > TOML > defaults; aspect/size profiles,
  default 1920×1080.
- **CLI** (`cli.py`): `build`, `read`, `analyze`, `split`; rich summary table;
  exit codes 0/1/2.
- **Readers**: ABC + entry-point discovery; static (httpx + retry), dynamic
  (Playwright), file handling, thin-body escalation, tier-1 asset localization,
  content_hash.
- **Classification**: fingerprint engine + strategy-order recommendation.
- **Pagination**: Playwright bounding-box probe + `plan_breaks` (semantic-snap,
  overflow, giant-split) with a static fallback when no browser.
- **Vision**: optional MiniCPM-V refine via Ollama HTTP, cached, heuristic-floor.
- **Importers**: dom helpers (wrap_reveal, split_by_heading, drop_chrome,
  luminance); webflow (adapted from compiler.py), mkdocs-material, generic
  (trafilatura); idempotent on canonical input.
- **Pre-export**: paged-media CSS + neutral theme injection → RenderJob.
- **Exporters**: ABC + capability-aware selection; weasyprint, playwright,
  vivliostyle, decktape, prince (all with `available()` gating + subprocess
  discipline).
- **Writers**: pypdf split, optional SVG via vexy-pdfsvgpy, preview index.
- **Orchestrator**: fan-out, per-strategy isolation, run-summary sidecar.
- **Tests**: 29 passing (classify, dom, paginate, settings, importers, writers,
  full integration through WeasyPrint). `test.sh` + `examples/build_local.py`.

### Notes / gotchas

- macOS WeasyPrint needs `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`
  (documented in DEPENDENCIES.md and test.sh).
- Pagination falls back to a static heuristic when Playwright isn't installed —
  the `browser` extra enables the real viewport probe.

### Next

- `render` CLI verb (single-stage re-run); `anyio` concurrency + Chromium pool
  limiter; content-addressed cache + `--no-cache`.
- Asset CSS `url()`/`@import` localization (tier 2/3: pywebcopy, monolith).
- Bubble/Docusaurus/Framer importers; reveal.js asset bundling for DeckTape.
- Golden SlidePlan snapshots; more edge/error tests.
