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

## 2026-05-22 — concurrency, cache, render verb, more importers, live validation

- Added `anyio` concurrent strategy dispatch with a `CapacityLimiter` for
  browser-class exporters; per-strategy isolation preserved.
- Content-addressed render cache (content_hash+strategy+stage), `--no-cache`.
- `render` CLI verb re-runs one strategy from sidecars (`PageDoc.from_dict`).
- Docusaurus/Bubble/Framer importers (6 importers discovered).
- Installed Playwright+Chromium; validated the browser paths (probe + page.pdf)
  on the webflow fixture and live `https://blog.fontlab.com/`.
- 38 tests passing; ruff clean.

### Resolved — plan vs structure reconciliation (spec/11–12)

First live run of blog.fontlab.com produced **1** slide vs a 17-slide plan: the
blog index has no `h1/h2` inside `md-content__inner`, so heading-splitting
collapsed it. Fixed with `dom.sectionize`/`split_to_count`: when heading-split
under-segments relative to the SlidePlan, distribute the content's block
children into ~`target` slides. `_content_root` descends single wrappers so
nested headings are still seen. Re-run: **14 (playwright) / 15 (weasyprint)**
slides — close to the plan and usefully divergent, exactly as intended.

### Next

- Asset CSS `url()`/`@import` localization (tier 2/3: pywebcopy, monolith).
- reveal.js asset bundling for DeckTape; warm browser reuse.
- Golden SlidePlan snapshots; retire webflow2reveal after parity.
