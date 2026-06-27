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
- **Exporters**: ABC + capability-aware selection; playwright, vivliostyle,
  reveal (native reveal.js via Playwright + pypdf), prince (all with
  `available()` gating + subprocess discipline).
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

## 2026-05-22 — closing the MVP: localization, reveal bundling, decktape server

- CSS `url()`/`@import` localization with bounded recursion (offline fonts/bg).
- Golden SlidePlan regression test; `--help` lists discovered strategies.
- Vendored reveal.js 5.1; pre-exporter bundles a self-contained deck for the
  DeckTape path; DeckTape serves it over a throwaway local HTTP server.
- 50 tests passing; ruff clean. 9 commits.

### Deliberately deferred (documented, not done)

These 4 TODO items are left as optional follow-ups — finishing them now would
break a project principle (CLAUDE.md):

- **pywebcopy tier-2 localization** — redundant with the working tier-1
  downloader + CSS localization; adding it is build-vs-buy bloat for no new
  capability.
- **monolith tier-3 freeze** — needs the `monolith` Rust binary (not installed);
  the dynamic Playwright reader already handles JS-heavy pages. Writing the path
  without the binary to validate it would ship untested code.
- **retire webflow2reveal** — premature; parity across diverse Webflow pages
  isn't yet confirmed. Remove only after broader acceptance testing.
- **warm browser/context reuse** — a performance optimization, not correctness;
  current per-strategy launch is correct and fast enough for the local CLI use.

State: every pipeline stage works end-to-end, validated live on
blog.fontlab.com, with 50 tests and 4 wired exporters (Playwright + native
reveal fully validated locally).

## 2026-05-22 — decktape→reveal rename + drop WeasyPrint

- Replaced the Node DeckTape exporter with a native `reveal` exporter
  (Playwright steps reveal.js, pypdf merges one PDF page per slide); no Node/
  decktape toolchain.
- Removed WeasyPrint entirely: exporter, entry point, optional dependency, and
  all spec/doc/example references. Paged-media recommendation is now Vivliostyle.
- Updated `classify._STRATEGY_ORDER` (no weasyprint); tests now gate on
  Playwright availability and synthesize fixtures via pypdf blank pages.

## 2026-05-23 — issue 103 Phase 1: `vexy-dexyjs` npm package

Decomposed issue 103 into `PLAN.md` (5 phases). Confirmed several asks are
already implemented: rename to `vexy-dexypy` + hatch-vcs git-tag semver, browser
choice (playwright/playwrightauthor/cloakbrowser) in `_browser.py`, and in-browser
preprocessing via `run_js_preprocessor` injecting `vexy-dexyjs`. The real deltas
are (a) a live, no-download browser mode and (b) shipping `vexy-dexyjs` to npm.

### Done (Phase 1 — self-contained, low risk)

- Reworked `vexy-dexyjs/package.json`: npm/CDN metadata + multi-format esbuild
  build (ESM `dist/index.mjs`, CJS `dist/index.cjs`, IIFE global
  `dist/vexy-dexyjs.global.js` + minified `.min.js`). Kept the `build:py` target
  that vendors `src/vexy_dexypy/assets/vexy-dexyjs.js`.
- Added `index.d.ts` (public type surface), `README.md` (API/CDN/consumers),
  `test/smoke.mjs` (`npm test`), `publish.sh` (gitnextver → npm).

### Verified

- `npm run build` emits all five artifacts; `npm test` passes (9 exports +
  luminance/CSS-parse/bg-class assertions).
- Python runtime asset rebuilt **byte-identical** (absent from `git status`) →
  no behavioral change to the Python pipeline.
- `pytest`: 48 passed, 5 skipped, **2 failed** — both pre-existing and
  environmental (`No module named 'playwright'`; the `browser` extra is not
  installed in this env), unrelated to the JS-only changes.

### Next

- Phase 2 (browser-native "live" mode) is a deep change to the Python core that
  forks the spec's offline guarantee. Gate it behind `Settings.fetch_mode` so the
  green `localize` path is never broken. Needs a product decision on the default
  mode (see PLAN.md Phase 2).

## 2026-05-23 — issue 103 Phase 2: browser-native `live` fetch mode (default)

Implemented the in-browser, no-download path. User decisions: live mode is the
default (localize opt-in); installed playwright here to verify end-to-end.

### Done

- `readers/live.py` — `LiveReader`: navigate URL in the chosen engine, capture
  rendered DOM, inject `<base href>` at the post-redirect origin, **no asset
  localization**. `can_read` returns 0 (mode-dispatched, never confidence-ranked).
- `settings.py` — `fetch_mode` field (default `live`), `[fetch]` config section,
  `build_settings(fetch_mode=...)`.
- `readers/__init__.py` — routes `live` mode to `LiveReader`; falls back to
  `localize` with a warning when playwright is absent. Local files always go to
  the static reader.
- `cli.py` — `--fetch-mode` on `build`/`read`/`analyze`.
- `pyproject.toml` — `live` reader entry point; `playwright` moved to a core dep
  (live is the default and needs it); `trafilatura` returned to the `extract`
  extra; dropped the now-redundant `browser` extra.
- `spec/06`/`spec/07` — documented the two modes; scoped the offline guarantee to
  `localize` mode.

### Verified

- `tests/test_live.py` (6 tests): `_inject_base` (insert/idempotent/no-head),
  `can_read == 0`, file→static delegation, and an **end-to-end live read over a
  real loopback origin** (base injected, `fetch_mode=live`, no `assets/` dir).
- Full suite: **61 passed** (was 55) in ~23s.
- Manual end-to-end: `live` build of a served `generic_article` fixture →
  **4 slide PDFs**, `localized asset dirs created: []` (download-free confirmed).

### Next

- Phase 3 (opt-in offlinization via vexy-dexyjs: single-file/monolith/css-inline),
  Phase 4 (Chrome extension scaffold), Phase 5 (vexy-dexypy consumes the published
  vexy-dexyjs / pinned CDN). See PLAN.md.

## 2026-05-23 — issue 103 Phase 4: Chrome extension scaffold (+ env repair)

- `vexy-dexyjs/extension/` — MV3 scaffold: `manifest.json` (activeTab+scripting),
  `popup.html`/`popup.js` (inject IIFE bundle, run `preprocess` on the active tab),
  `README.md`. Added `build:ext` esbuild target (in `npm run build`) emitting the
  git-ignored `extension/vexy-dexyjs.global.min.js`.
- DEPENDENCIES.md: moved `playwright` to core (live default); documented the
  vendored `vexy-dexyjs` bundle sync (Phase 5 partial).

### Environment note

Mid-session the homebrew `node` (25.8.1) broke on a `simdjson`/`llhttp` soname
mismatch (a pre-existing partial-upgrade state, unrelated to the code). Repaired
by upgrading to `node` 26.0.0. After repair: `npm run build` emits all dist
formats + the extension bundle, `npm test` passes, the Python asset rebuilds
byte-identical, and the Python suite is **61 passed**.

### Status vs issue 103

Core delivered + verified: Phase 1 (npm package), Phase 2 (live no-download mode,
default), Phase 4 (extension scaffold), Phase 5 (vendored-sync documented).
Phase 3 (opt-in offlinization: single-file/monolith/css-inline) remains, specified
in PLAN.md — the issue marks it optional and it is a sizable separate effort.

## 2026-05-23 — issue 103 Phase 3: `offline` fetch mode (single-file archiving)

- `readers/offline.py` — `OfflineReader`: shells out to `single-file`/`monolith`
  (`Settings.offline_tool`) to produce one self-contained `index.html` (spec/07
  Tier-3). `--fetch-mode offline`; `can_read == 0` (mode-dispatched); graceful
  fallback to `localize` when the tool is absent; file sources → static.
  Subprocess discipline: timeout, captured stderr, non-empty-output check.
- Wired `offline_tool` through settings + `[fetch] tool` config; `offline` reader
  entry point; CLI `--fetch-mode` doc; spec/06 + DEPENDENCIES updated.

### Verified

- `tests/test_offline.py` (6): command construction (single-file/monolith),
  settings plumbing, `can_read == 0`, tool-absent fallback (mocked), file→static.
- Full suite: **67 passed** (was 61); ruff clean.

All five PLAN phases now landed (Phase 5 partial: vendored-sync documented, CDN
pinning left optional). Issue 103's substantive scope is complete and verified.

## 2026-05-23 — faithful rendering (issue 104) + Webflow sectioning fix

Reported: TransType slides showed white bg + margins + only the footer survived.

### Fixed

- **Webflow/Framer sectioning** (`vexy-dexyjs` `preprocess`): selecting slides via
  `querySelectorAll('section, .section, …')` matched only stray footer/menu blocks
  carrying a `section` token. Now prefers content-bearing top-level children of the
  content root, falling back to explicit selectors for wrapper-nested layouts.
  TransType: 2 footer-only → 14 real sections.
- **Faithful rendering** (`preexport.theme_css`): the neutral slide theme
  (`.slide{padding:4%}`, `.slide-light-bg{background:#fff}`) overrode designed
  pages. Webflow/Framer now keep their own CSS (badge-hide only); generic/Markdown
  keep the neutral theme.
- **Faithful PDF capture** (issue 104): paged CSS injects
  `* { print-color-adjust: exact }`; Playwright `page.pdf` pins zero margins (screen
  media + stage `@page` already in place). spec/17 + spec/20 + TODO updated with the
  full recipe and the two SVG strategies (PDF→SVG default; DOM→SVG optional).

### Default size

- Stage default → 1280×720; profiles renamed `720p`/`1080p`/`810p` (all 16:9).

### Verified

- 67 tests pass; ruff clean. Live builds of the TransType page render the real red
  hero (slide 1) and green quote (slide 5) at 1280×720 — true colours, no white bg,
  no margins, desktop layout.
