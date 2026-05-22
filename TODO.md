<!-- this_file: TODO.md -->

# vexy-dex — TODO

We have committed the changes so far into https://github.com/vexyart/vexy-dex 

Actionable, flat task list derived from [`spec/`](spec/00-tldr.md). Each item
links the chapter that specifies it. Order roughly follows the MVP staging in
[spec/24](spec/24.md). `[x]` = done, `[~]` = partial. Mirror detail in `WORK.md`.

## Stage 0 — Project setup

- [x] Init `uv` project, Python 3.12, `src/vexy_dex/` layout ([spec/24](spec/24.md))
- [x] Add core deps: httpx, bs4, lxml, selectolax, pypdf, fire, loguru, rich, anyio; heavy engines (playwright, weasyprint, trafilatura, pikepdf) as extras ([spec/24](spec/24.md))
- [x] `playwright install chromium`; document Node/monolith/poppler externals ([spec/24](spec/24.md))
- [x] `hatch-vcs` versioning; `vexy-dex` script entry point ([spec/24](spec/24.md))
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
- [x] Exit codes 0/1/2 + per-strategy summary table ([spec/04](spec/04.md), [spec/22](spec/22.md))
- [~] `--help` (Fire-generated); document the `--` caveat; list discovered strategies ([spec/04](spec/04.md))

## Stage 1 — Readers

- [x] Reader ABC + `vexy_dex.readers` entry-point discovery ([spec/06](spec/06.md))
- [x] Static reader (`httpx[http2]`, redirects, timeout) ([spec/06](spec/06.md))
- [x] Dynamic reader (Playwright, `networkidle`, hydrated `content()`) ([spec/06](spec/06.md))
- [x] Local-file / `file://` handling ([spec/06](spec/06.md))
- [x] Static→dynamic escalation heuristic ([spec/06](spec/06.md))
- [x] `ReadError` with URL/status; one retry w/ backoff+jitter ([spec/06](spec/06.md), [spec/22](spec/22.md))

## Stage 1 — Asset localization

- [x] Tier 1: `ThreadPoolExecutor` tag-asset downloader + path rewrite ([spec/07](spec/07.md))
- [ ] Tier 2: `pywebcopy` static mirror integration ([spec/07](spec/07.md))
- [ ] Tier 3: `monolith` freeze (Chromium dump-dom | monolith) ([spec/07](spec/07.md))
- [x] CSS `url()`/`@import` localization (bounded recursion; fonts/bg images) ([spec/07](spec/07.md))
- [x] Path sanitation (hash long names, no traversal, stay under out/) ([spec/07](spec/07.md))
- [x] Compute `PageDoc.content_hash` over html + asset manifest ([spec/07](spec/07.md), [spec/21](spec/21.md))

## Stage 2 — Classification

- [x] Fingerprint rules engine: webflow, mkdocs-material, docusaurus, framer, bubble, generic ([spec/08](spec/08.md))
- [x] Confidence scoring + tie-break to generic; log matches ([spec/08](spec/08.md))
- [x] Strategy-order recommendation per framework ([spec/08](spec/08.md), [spec/05](spec/05.md))

## Stage 2 — Pagination

- [x] Playwright bounding-box probe JS at stage size ([spec/09](spec/09.md))
- [x] `plan_breaks`: semantic-snap, overflow, giant-split, tolerance ([spec/09](spec/09.md))
- [x] Dedupe/sort breaks; screen-count fallback for div-soup ([spec/09](spec/09.md))
- [ ] Golden `SlidePlan` snapshots for fixtures ([spec/23](spec/23.md))

## Stage 2 — Vision (optional)

- [x] `vision.py`: screenshot → MiniCPM-V via Ollama/llama.cpp HTTP ([spec/10](spec/10.md))
- [x] Structured break output (JSON-validated); reject prose ([spec/10](spec/10.md))
- [x] `--reasoning off` footgun documented in code + DEPENDENCIES ([spec/10](spec/10.md))
- [x] Merge vision breaks onto heuristic plan (heuristic is floor) ([spec/10](spec/10.md))
- [x] Cache by screenshot-hash + model; graceful fallback if server down ([spec/10](spec/10.md), [spec/21](spec/21.md))

## Stage 3 — Importers

- [x] Importer ABC + `vexy_dex.importers` discovery ([spec/11](spec/11.md))
- [x] `vexy_dex.dom` helpers: `wrap_reveal`, `split_by_heading`, `drop_chrome`, `luminance` ([spec/11](spec/11.md))
- [x] Canonical layout vocabulary classes ([spec/11](spec/11.md))
- [x] Webflow importer — adapted from `webflow2reveal/.../compiler.py` (section select, chrome drop, luminance bg, reveal wrap) ([spec/12](spec/12.md))
- [ ] After parity: retire the legacy `webflow2reveal` package ([spec/12](spec/12.md), [spec/24](spec/24.md))
- [x] MkDocs Material importer — `md-content__inner`, heading split, chrome drop, preserve code/tables ([spec/13](spec/13.md))
- [x] Generic importer — trafilatura extract + h2 split ([spec/14](spec/14.md))
- [x] Bubble / Docusaurus / Framer light rule sets ([spec/14](spec/14.md))
- [x] Idempotency: re-running transform is a no-op on canonical input ([spec/11](spec/11.md))

## Stage 4 — Pre-exporters

- [x] Parameterized paged-media stylesheet template ([spec/15](spec/15.md))
- [x] Reconcile SlidePlan with structure: plan-driven `sectionize`/`split_to_count` fallback when heading-splitting under-segments ([spec/11](spec/11.md), [spec/15](spec/15.md))
- [~] Theme injection done; bundle reveal.js for the DeckTape path ([spec/15](spec/15.md))
- [ ] Bundle `assets/reveal.js` ([spec/15](spec/15.md))
- [x] Emit per-strategy `RenderJob` ([spec/15](spec/15.md), [spec/03](spec/03.md))

## Stage 5 — Exporters

- [x] Exporter ABC: `available/needs_js/supports_paged_media/export` + discovery ([spec/16](spec/16.md))
- [x] Capability-aware dispatch (user `--strategies` authoritative) ([spec/16](spec/16.md))
- [x] Subprocess discipline: timeouts, captured stderr, file paths ([spec/16](spec/16.md))
- [x] Playwright exporter (`page.pdf`, `prefer_css_page_size`, screen media) ([spec/17](spec/17.md))
- [x] WeasyPrint exporter ([spec/18](spec/18.md))
- [x] Vivliostyle exporter (shell out; AGPL boundary) ([spec/18](spec/18.md))
- [x] Prince exporter (opt-in, path-gated) ([spec/18](spec/18.md))
- [x] DeckTape exporter ([spec/19](spec/19.md))
- [ ] DeckTape optional throwaway local server for asset-relative pages ([spec/19](spec/19.md))

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
