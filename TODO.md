<!-- this_file: TODO.md -->

# vexy-dexypy — TODO

We have committed the changes so far into https://github.com/vexyart/vexy-dexypy

Actionable, flat task list derived from [`spec/`](spec/00-tldr.md). Each item
links the chapter that specifies it. Order roughly follows the MVP staging in
[spec/24](spec/24.md). `[x]` = done, `[/]` = in progress, `[ ]` = todo.

## Stage 0 — Project setup

- [x] Init `uv` project, Python 3.12, `src/vexy_dexypy/` layout ([spec/24](spec/24.md))
- [x] Add core deps: httpx, bs4, lxml, selectolax, pypdf, fire, loguru, rich, anyio; heavy engines (playwright, weasyprint, trafilatura, pikepdf) as extras ([spec/24](spec/24.md))
- [x] `playwright install chromium`; document Node/monolith/poppler externals ([spec/24](spec/24.md))
- [x] Support local clone of `playwrightauthor` under `./private/playwrightauthor/` and integrate `cloakbrowser` dependency ([spec/06](spec/06.md))
- [x] `hatch-vcs` versioning; `vexy-dexypy` script entry point ([spec/24](spec/24.md))
- [x] Create `DEPENDENCIES.md` with the licence-hazard table ([spec/24](spec/24.md))

## Data model & config

- [x] Implement IR dataclasses: `Source`, `PageDoc`, `Break`, `SlidePlan`, `Strategy`, `RenderJob`, `DeckResult` ([spec/03](spec/03.md))
- [x] JSON sidecar (de)serialization for IR types into `_meta/` ([spec/03](spec/03.md), [spec/21](spec/21.md))
- [x] `Settings` parser: flag > TOML > defaults precedence ([spec/05](spec/05.md))
- [x] Aspect/size profiles (16:9, 4:3, A4-landscape, `WxH` override) → `(stage_w, stage_h)` ([spec/05](spec/05.md))
- [x] Enforce IR invariants (sorted/deduped breaks, local-resolving html_path) ([spec/03](spec/03.md))

## CLI (Fire)

- [x] `VexyDex` class with `build`, `read`, `analyze`, `render`, `split` ([spec/04](spec/04.md))
- [x] Flags: `--out --aspect --size --strategies --svg --vision --verbose --no-cache` ([spec/04](spec/04.md))
- [x] Add flags for browser engine selection: `--browser-engine` (playwright | playwrightauthor | cloakbrowser) ([spec/04](spec/04.md))
- [x] Exit codes 0/1/2 + per-strategy summary table ([spec/04](spec/04.md), [spec/22](spec/22.md))
- [x] `--help` lists runtime-discovered (un)available strategies + documents the `--` caveat ([spec/04](spec/04.md))

## Stage 1 — Readers & Browsers

- [x] Reader ABC + `vexy_dexypy.readers` entry-point discovery ([spec/06](spec/06.md))
- [x] Static reader (`httpx[http2]`, redirects, timeout) ([spec/06](spec/06.md))
- [x] Dynamic reader choices:
  - [x] Standard `playwright` driver ([spec/06](spec/06.md))
  - [x] `playwrightauthor` driver (persistent, logged-in sessions via Chrome for Testing) ([spec/06](spec/06.md))
  - [x] `cloakbrowser` driver (stealth-patched Chromium to bypass anti-bot challenges) ([spec/06](spec/06.md))
- [x] Local-file / `file://` handling ([spec/06](spec/06.md))
- [x] Static→dynamic escalation heuristic ([spec/06](spec/06.md))
- [x] `ReadError` with URL/status; one retry w/ backoff+jitter ([spec/06](spec/06.md), [spec/22](spec/22.md))

## Stage 1 — Asset Localization & Offlinization

- [x] Tier 1: `ThreadPoolExecutor` tag-asset downloader + path rewrite ([spec/07](spec/07.md))
- [ ] Tier 2: `pywebcopy` static mirror integration ([spec/07](spec/07.md))
- [ ] Tier 3: JS-based offlinization inside `vexy-dexyjs` (delegated from Python):
  - [ ] Support `single-file-cli` integration ([spec/07](spec/07.md))
  - [ ] Support `monolith` (Rust / npm wrapper) inlining ([spec/07](spec/07.md))
  - [ ] Support CSS inliners (`juice`, `css-inline`, `inline-css`) for linearizing and inlining styles ([spec/07](spec/07.md))
- [x] CSS `url()`/`@import` localization (bounded recursion; fonts/bg images) ([spec/07](spec/07.md))
- [x] Path sanitation (hash long names, no traversal, stay under out/) ([spec/07](spec/07.md))
- [x] Compute `PageDoc.content_hash` over html + asset manifest ([spec/07](spec/07.md), [spec/21](spec/21.md))

## Stage 2 — Classification & Pagination

- [x] Fingerprint rules engine: webflow, mkdocs-material, docusaurus, framer, bubble, generic ([spec/08](spec/08.md))
- [x] Confidence scoring + tie-break to generic; log matches ([spec/08](spec/08.md))
- [x] Strategy-order recommendation per framework ([spec/08](spec/08.md), [spec/05](spec/05.md))
- [x] Playwright bounding-box probe JS at stage size ([spec/09](spec/09.md))
- [x] `plan_breaks`: semantic-snap, overflow, giant-split, tolerance ([spec/09](spec/09.md))
- [x] Dedupe/sort breaks; screen-count fallback for div-soup ([spec/09](spec/09.md))
- [x] Golden `SlidePlan` snapshot regression test ([spec/23](spec/23.md))
- [x] `vision.py`: screenshot → MiniCPM-V via Ollama/llama.cpp HTTP ([spec/10](spec/10.md))
- [x] Structured break output (JSON-validated); reject prose ([spec/10](spec/10.md))
- [x] Merge vision breaks onto heuristic plan (heuristic is floor) ([spec/10](spec/10.md))
- [x] Cache by screenshot-hash + model; graceful fallback if server down ([spec/10](spec/10.md), [spec/21](spec/21.md))

## Stage 3 — vexy-dexyjs (In-Browser Importers & Preprocessors)

- [x] Initialize companion package `./vexy-dexyjs/` as an NPM package ([spec/11](spec/11.md))
- [x] Port and generalize Webflow compiler logic from `private/webflow2reveal/js/` into `vexy-dexyjs` ([spec/12](spec/12.md))
- [x] Write generalized page preprocessing/normalizer in `vexy-dexyjs` (smarter version of `webflow2revealjs` that works on ANY page) ([spec/11](spec/11.md))
- [x] Implement browser injection bridge in `vexy_dexypy` to load and run `vexy-dexyjs` inside Playwright/playwrightauthor/cloakbrowser context ([spec/11](spec/11.md))
- [x] Integrate offlinization options (e.g. `single-file-cli`, `monolith`, `juice`) inside `vexy-dexyjs` ([spec/07](spec/07.md))
- [x] Implement MkDocs Material preprocessing rules in `vexy-dexyjs` ([spec/13](spec/13.md))
- [x] Implement generic, Docusaurus, Framer, and Bubble DOM preprocessing rules in `vexy-dexyjs` ([spec/14](spec/14.md))
- [x] Make `vexy-dexyjs` packageable as a Chrome extension ([spec/11](spec/11.md))
- [x] Retain idempotency: re-running transform is a no-op on canonical input ([spec/11](spec/11.md))

## Stage 4 — Pre-exporters

- [x] Parameterized paged-media stylesheet template ([spec/15](spec/15.md))
- [x] Reconcile SlidePlan with structure: plan-driven `sectionize`/`split_to_count` fallback when heading-splitting under-segments ([spec/11](spec/11.md), [spec/15](spec/15.md))
- [x] Bundle reveal.js 5.1 (`assets/reveal/`) and inject it for the DeckTape path with a stage-sized `Reveal.initialize` ([spec/15](spec/15.md))
- [x] Disable all reveal UI chrome (controls/progress/slide-number/help/pause) in the reveal chassis — slides are for print, not navigation ([spec/15](spec/15.md))
- [x] Emit per-strategy `RenderJob` ([spec/15](spec/15.md), [spec/03](spec/03.md))

## Framework chassis — real alternatives to reveal (refactor)

The reveal wrapper is currently emitted by importers, baking one framework into
the IR; this makes the five strategies differ only by PDF engine. Decouple so
the chassis is a per-strategy stage-4 choice and genuine framework divergence
becomes possible ([spec/11](spec/11.md), [spec/15](spec/15.md), [spec/16](spec/16.md)).

- [x] Make the normalized IR framework-neutral: importers emit a flat `<section class="slide">` list, **not** `.reveal > .slides` ([spec/11](spec/11.md))
- [x] Move reveal wrapping out of importers into a `reveal` chassis in the pre-exporter; `dom.wrap_reveal` becomes the chassis helper ([spec/15](spec/15.md))
- [x] Add a `paged` chassis (neutral sections + `@page`/break CSS) as the default for weasyprint/vivliostyle/prince/playwright ([spec/15](spec/15.md))
- [x] Add `chassis` field to `Strategy`; map each strategy to its chassis ([spec/03](spec/03.md), [spec/16](spec/16.md))
- [x] `impress` chassis: wrap neutral slides in `#impress > .step`, bundle impress.js (localized), drive via DeckTape `impress` key, chrome off ([spec/15](spec/15.md), [spec/19](spec/19.md))
- [x] `marp` chassis + `marp-cli` exporter: sections → Markdown deck → native PDF ([spec/16](spec/16.md), [spec/19](spec/19.md))
- [x] Tests: one neutral IR fixture rendered through ≥2 chassis yields visibly different decks (the divergence guarantee) ([spec/23](spec/23.md))

## Stage 5 — Exporters

- [x] Exporter ABC: `available/needs_js/supports_paged_media/export` + discovery ([spec/16](spec/16.md))
- [x] Capability-aware dispatch (user `--strategies` authoritative) ([spec/16](spec/16.md))
- [x] Subprocess discipline: timeouts, captured stderr, file paths ([spec/16](spec/16.md))
- [x] Playwright exporter (`page.pdf`, `prefer_css_page_size`, screen media) ([spec/17](spec/17.md))
- [x] Vivliostyle exporter (shell out; AGPL boundary) ([spec/18](spec/18.md))
- [x] Prince exporter (opt-in, path-gated) ([spec/18](spec/18.md))
- [x] Native `reveal` exporter — Playwright drives reveal.js, `page.pdf` per slide, `pypdf` merges; no Node/decktape dependency ([spec/19](spec/19.md))
- [x] Harden browser navigation: serve local decks over a loopback HTTP server (real origin, avoids file:// CORS/SRI/font quirks) and wait for `load` not `networkidle` (which hangs when offline JS retries 4xx/5xx assets); shared `_browser.serving` used by playwright/reveal/vision/probe ([spec/17](spec/17.md), [spec/09](spec/09.md), [spec/19](spec/19.md))

## Stage 6 — Writers

- [x] PDF split with `pypdf` ([spec/20](spec/20.md))
- [x] Zero-padded ordered naming ([spec/20](spec/20.md))
- [x] SVG export via `vexy-pdfsvgpy` under `--svg` ([spec/20](spec/20.md))
- [x] Reveal preview `index.html` per strategy ([spec/20](spec/20.md))
- [x] Return `DeckResult`; isolate writer failures ([spec/20](spec/20.md))

## Orchestration & cross-cutting

- [x] Orchestrator fan-out: stages 1–3 once, 4–6 per strategy ([spec/21](spec/21.md))
- [x] `anyio` task group; `CapacityLimiter` for browser-class exporters ([spec/21](spec/21.md))
- [ ] Warm browser/context reuse across probe + Playwright export ([spec/21](spec/21.md))
- [x] Content-addressed render cache honouring `--no-cache` ([spec/21](spec/21.md))
- [x] Typed error taxonomy + partial-failure summary ([spec/22](spec/22.md))
- [x] `loguru` logging; `--verbose` DEBUG ([spec/22](spec/22.md))

## Testing & docs

- [x] Vendor offline fixtures: webflow_sample, mkdocs_sample, generic_article, divsoup ([spec/23](spec/23.md))
- [x] Unit tests for pure functions (classify, plan_breaks, dom helpers, config, split) ([spec/23](spec/23.md))
- [x] Edge + error tests (empty, malformed, no-headings, missing file, failed-strategy isolation) ([spec/23](spec/23.md))
- [x] Integration: fixture → full pipeline → assert slide count + layout ([spec/23](spec/23.md))
- [x] `examples/build_local.py` runnable; run by `test.sh` ([spec/23](spec/23.md))
- [x] `./test.sh` (ruff + pytest + example smoke) ([spec/23](spec/23.md))
- [x] Manual acceptance vs blog.fontlab.com (14/15 slides, 2 strategies, offline localize OK); vexy.art/fontlab.com pending ([spec/23](spec/23.md))
- [x] Keep README/CHANGELOG/PLAN/WORK/DEPENDENCIES current ([spec/24](spec/24.md))

## Issue 103 — browser-native pipeline + `vexy-dexyjs` npm package

See [`PLAN.md`](PLAN.md) for full decomposition and sequencing.

### Phase 1 — `vexy-dexyjs` npm package (done)

- [x] Rework `package.json` (main/module/browser/unpkg/jsdelivr/exports/types, files, keywords, repo)
- [x] Multi-format esbuild build (esm, cjs, iife global, minified CDN) + `build:py` python-asset target
- [x] Hand-maintained `index.d.ts`
- [x] Generalized `README.md` (API, CDN snippet, framework support, consumers)
- [x] `publish.sh` (gitnextver → npm)
- [x] DOM-free smoke test (`npm test`); verified python asset rebuilds byte-identical

### Phase 2 — browser-native "live" mode in `vexy-dexypy`

- [x] `Settings.fetch_mode`: `live` (navigate real URL, no disk localize) | `localize` (current)
- [x] `LiveReader`: navigate live URL + `<base href>`, no localize; downstream serves it & assets load online
- [x] Reader dispatch routes `live` mode (mode-dispatched, not confidence-ranked); falls back to localize without playwright
- [x] Updated `spec/06`/`spec/07` for the two modes; offline guarantee scoped to `localize`

### Phase 3 — offlinization as opt-in capability (done)

- [x] `OfflineReader`: `--fetch-mode offline` shells out to single-file/monolith; graceful fallback
- [ ] Future: in-browser `vexy-dexyjs` critical-CSS inline / asset-ref rewrite (JS-side variant)

### Phase 4 — Chrome extension scaffold (`vexy-dexyjs/extension/`, MV3)

- [x] MV3 scaffold (manifest + popup) injects IIFE bundle, runs `preprocess` on active tab; `build:ext` emits the bundle

### Phase 5 — `vexy-dexypy` consumes published `vexy-dexyjs`

- [x] Documented vendored `assets/vexy-dexyjs.js` sync (regenerated by `vexy-dexyjs`'s `build:py`) in `DEPENDENCIES.md`; CDN pinning still optional/future

## Issue 104 — maximize PDF/SVG faithfulness

Fold the faithful-capture research (issues/104.md) into the renderer. See
[spec/17](spec/17.md) (PDF recipe) and [spec/20](spec/20.md) (two SVG strategies).

### Done

- [x] Faithful "PDF screenshot" recipe in the Playwright exporter: `emulate_media('screen')`, `print_background`, zero margins, stage-sized `@page` + `prefer_css_page_size`
- [x] Inject `* { -webkit-print-color-adjust: exact; print-color-adjust: exact }` (paged CSS) so backgrounds/colours survive in Chromium & Prince
- [x] Stop neutral re-theming of designed pages (`preexport.theme_css`): Webflow/Framer keep their own CSS, no forced white bg / 4% padding
- [x] Document the two SVG routes: PDF→SVG (default, matches the PDF via `vexy-pdfsvgpy`) vs browser-side DOM→SVG (optional)

### Future (optional, deferred)

- [ ] DOM→SVG (Strategy B): `<foreignObject>`/`dom-to-svg` capture in-browser; produce PDF from the SVG (rsvg/resvg) so the pair stays consistent; base64-inline images. Enables WebKit/Firefox + transparent backgrounds
- [ ] macOS native `WKWebView.createPDFWithConfiguration:` (PyObjC) faithful engine — no print emulation, native transparency ([spec/24](spec/24.md))
- [ ] Optional "infinite"/single-page capture: size `@page`/`width,height` to `documentElement.scrollWidth/scrollHeight` for an unpaginated canvas
- [ ] Transparent-bg PDFs via post-processing (`qpdf`/`mutool`) for users who need them
