<!-- this_file: TODO.md -->

# vexy-dex — TODO

Actionable, flat task list derived from [`spec/`](spec/00-tldr.md). Each item
links the chapter that specifies it. Order roughly follows the MVP staging in
[spec/24](spec/24.md). Tick items as they land; mirror detail in `PLAN.md`.

## Stage 0 — Project setup

- [ ] Init `uv` project, Python 3.12, `src/vexy_dex/` layout ([spec/24](spec/24.md))
- [ ] Add core deps: httpx, playwright, bs4, lxml, selectolax, trafilatura, weasyprint, pypdf, pikepdf, fire, loguru, rich, anyio ([spec/24](spec/24.md))
- [ ] `playwright install chromium`; document Node/monolith/poppler externals ([spec/24](spec/24.md))
- [ ] `hatch-vcs` versioning; `vexy-dex` script entry point ([spec/24](spec/24.md))
- [ ] Create `DEPENDENCIES.md` with the licence-hazard table ([spec/24](spec/24.md))

## Data model & config

- [ ] Implement IR dataclasses: `Source`, `PageDoc`, `Break`, `SlidePlan`, `Strategy`, `RenderJob`, `DeckResult` ([spec/03](spec/03.md))
- [ ] JSON sidecar (de)serialization for IR types into `_meta/` ([spec/03](spec/03.md), [spec/21](spec/21.md))
- [ ] `Settings` parser: flag > TOML > defaults precedence ([spec/05](spec/05.md))
- [ ] Aspect/size profiles (16:9, 4:3, A4-landscape, `WxH` override) → `(stage_w, stage_h)` ([spec/05](spec/05.md))
- [ ] Enforce IR invariants (sorted/deduped breaks, local-resolving html_path) ([spec/03](spec/03.md))

## CLI (Fire)

- [ ] `VexyDex` class with `build`, `read`, `analyze`, `render`, `split` ([spec/04](spec/04.md))
- [ ] Flags: `--out --aspect --size --strategies --svg --vision --verbose` ([spec/04](spec/04.md))
- [ ] Exit codes 0/1/2 + per-strategy summary table ([spec/04](spec/04.md), [spec/22](spec/22.md))
- [ ] `--help` lists runtime-discovered strategies; document the `--` caveat ([spec/04](spec/04.md))

## Stage 1 — Readers

- [ ] Reader ABC + `vexy_dex.readers` entry-point discovery ([spec/06](spec/06.md))
- [ ] Static reader (`httpx[http2]`, redirects, timeout) ([spec/06](spec/06.md))
- [ ] Dynamic reader (Playwright, `networkidle`, hydrated `content()`) ([spec/06](spec/06.md))
- [ ] Local-file / `file://` handling ([spec/06](spec/06.md))
- [ ] Static→dynamic escalation heuristic ([spec/06](spec/06.md))
- [ ] `ReadError` with URL/status; one retry w/ backoff+jitter ([spec/06](spec/06.md), [spec/22](spec/22.md))

## Stage 1 — Asset localization

- [ ] Tier 1: `ThreadPoolExecutor` tag-asset downloader + path rewrite ([spec/07](spec/07.md))
- [ ] Tier 2: `pywebcopy` static mirror integration ([spec/07](spec/07.md))
- [ ] Tier 3: `monolith` freeze (Chromium dump-dom | monolith) ([spec/07](spec/07.md))
- [ ] CSS `url()`/`@import`/`@font-face` localization ([spec/07](spec/07.md))
- [ ] Path sanitation (hash long names, no traversal, stay under out/) ([spec/07](spec/07.md))
- [ ] Compute `PageDoc.content_hash` over html + asset manifest ([spec/07](spec/07.md), [spec/21](spec/21.md))

## Stage 2 — Classification

- [ ] Fingerprint rules engine: webflow, mkdocs-material, docusaurus, framer, bubble, generic ([spec/08](spec/08.md))
- [ ] Confidence scoring + tie-break to generic; log matches ([spec/08](spec/08.md))
- [ ] Strategy-order recommendation per framework ([spec/08](spec/08.md), [spec/05](spec/05.md))

## Stage 2 — Pagination

- [ ] Playwright bounding-box probe JS at stage size ([spec/09](spec/09.md))
- [ ] `plan_breaks`: semantic-snap, overflow, giant-split, tolerance ([spec/09](spec/09.md))
- [ ] Dedupe/sort breaks; screen-count fallback for div-soup ([spec/09](spec/09.md))
- [ ] Golden `SlidePlan` snapshots for fixtures ([spec/23](spec/23.md))

## Stage 2 — Vision (optional)

- [ ] `vision.py`: screenshot → MiniCPM-V via Ollama/llama.cpp HTTP ([spec/10](spec/10.md))
- [ ] `instructor`/Pydantic structured break output; reject prose ([spec/10](spec/10.md))
- [ ] `--reasoning off` footgun handling ([spec/10](spec/10.md))
- [ ] Merge vision breaks onto heuristic plan (heuristic is floor) ([spec/10](spec/10.md))
- [ ] Cache by screenshot-hash + model; graceful fallback if server down ([spec/10](spec/10.md), [spec/21](spec/21.md))

## Stage 3 — Importers

- [ ] Importer ABC + `vexy_dex.importers` discovery ([spec/11](spec/11.md))
- [ ] `vexy_dex.dom` helpers: `wrap_reveal`, `split_by_heading`, `drop_chrome`, `luminance` ([spec/11](spec/11.md))
- [ ] Canonical layout vocabulary classes ([spec/11](spec/11.md))
- [ ] Webflow importer — copy & adapt `webflow2reveal/py/.../compiler.py` into `vexy_dex.importers.webflow` (configurable stage, shared IR/vocabulary, drop fetch/dev-server bits) ([spec/12](spec/12.md))
- [ ] After parity: retire the legacy `webflow2reveal` package ([spec/12](spec/12.md), [spec/24](spec/24.md))
- [ ] MkDocs Material importer — `md-content__inner`, heading split, chrome drop, preserve code/tables ([spec/13](spec/13.md))
- [ ] Generic importer — trafilatura extract + `clear-html` + h2 split ([spec/14](spec/14.md))
- [ ] Bubble / Docusaurus / Framer light rule sets ([spec/14](spec/14.md))
- [ ] Idempotency: re-running transform is a no-op on canonical input ([spec/11](spec/11.md))

## Stage 4 — Pre-exporters

- [ ] Parameterized paged-media stylesheet template ([spec/15](spec/15.md))
- [ ] SlidePlan → explicit `break-before/after` injection ([spec/15](spec/15.md))
- [ ] Reveal scaffolding (bundled reveal.js + theme.css, sized init) ([spec/15](spec/15.md))
- [ ] Bundle `assets/reveal.js` + neutral `theme.css` ([spec/15](spec/15.md))
- [ ] Emit per-strategy `RenderJob` ([spec/15](spec/15.md), [spec/03](spec/03.md))

## Stage 5 — Exporters

- [ ] Exporter ABC: `available/needs_js/supports_paged_media/export` + discovery ([spec/16](spec/16.md))
- [ ] Capability-aware dispatch (user `--strategies` authoritative) ([spec/16](spec/16.md))
- [ ] Subprocess discipline: timeouts, captured stderr, file paths ([spec/16](spec/16.md))
- [ ] Playwright exporter (`page.pdf`, `prefer_css_page_size`, screen media) ([spec/17](spec/17.md))
- [ ] WeasyPrint exporter ([spec/18](spec/18.md))
- [ ] Vivliostyle exporter (shell out; AGPL boundary) ([spec/18](spec/18.md))
- [ ] Prince exporter (opt-in, path-gated) ([spec/18](spec/18.md))
- [ ] DeckTape exporter (+ optional throwaway local server) ([spec/19](spec/19.md))

## Stage 6 — Writers

- [ ] PDF split with `pypdf`; `pikepdf` for damaged/structured PDFs ([spec/20](spec/20.md))
- [ ] Zero-padded ordered naming + optional title slug ([spec/20](spec/20.md))
- [ ] SVG export via `vexy-pdfsvgpy` under `--svg` ([spec/20](spec/20.md))
- [ ] Reveal preview `index.html` per strategy ([spec/20](spec/20.md))
- [ ] Return `DeckResult`; isolate writer failures ([spec/20](spec/20.md))

## Orchestration & cross-cutting

- [ ] Orchestrator fan-out: stages 1–3 once, 4–6 per strategy ([spec/21](spec/21.md))
- [ ] `anyio` task group; `CapacityLimiter` for Chromium pool ([spec/21](spec/21.md))
- [ ] Warm browser/context reuse across probe + Playwright export ([spec/21](spec/21.md))
- [ ] Content-addressed cache (page, plan, vision, render) + `--no-cache` ([spec/21](spec/21.md))
- [ ] Typed error taxonomy + partial-failure summary ([spec/22](spec/22.md))
- [ ] `loguru` logging with structured fields; `--verbose` DEBUG ([spec/22](spec/22.md))

## Testing & docs

- [ ] Vendor offline fixtures: webflow_sample, mkdocs_sample, generic_article, divsoup ([spec/23](spec/23.md))
- [ ] Unit tests for all pure functions (classify, plan_breaks, dom helpers, config, split) ([spec/23](spec/23.md))
- [ ] Edge + error tests (empty, no-headings, giant, malformed, missing engine, timeout) ([spec/23](spec/23.md))
- [ ] Integration: fixture → full pipeline → assert slide count + layout ([spec/23](spec/23.md))
- [ ] `examples/` runnable scripts wired into CI ([spec/23](spec/23.md))
- [ ] `./test.sh` (ruff/autoflake/pyupgrade/mypy + hatch test + examples) ([spec/23](spec/23.md))
- [ ] Manual acceptance vs vexy.art/lines, fontlab.com, blog.fontlab.com ([spec/23](spec/23.md))
- [ ] Keep README/CHANGELOG/PLAN/WORK/DEPENDENCIES current ([spec/24](spec/24.md))
