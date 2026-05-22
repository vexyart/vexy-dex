<!-- this_file: spec/00-tldr.md -->

# vexy-dex Specification — Table of Contents & TL;DR

vexy-dex turns an HTML page into slide decks. One URL in; several folders out,
one per rendering strategy, each holding named single-page PDFs (and optional
SVGs). The user assembles a final deck by picking the best slide from whichever
strategy rendered it best.

This spec is 24 chapters. Each chapter is self-contained and cross-links the
others. The pipeline is six stages — **readers → pre-importers → importers →
pre-exporters → exporters → writers** — wrapped by an orchestrator. Read
chapters 01–05 for the shape of the thing; 06–20 for the stages; 21–24 for the
plumbing.

Grounding: see [`../RESEARCH.md`](../RESEARCH.md) for the tool decisions and
[`../IDEA.md`](../IDEA.md) for the original intent.

## Chapters

- **[01 — Overview, Scope & Non-Goals](01.md)** — What vexy-dex is, the
  one-sentence scope, what it deliberately refuses to do, and the anti-bloat
  rules that keep it honest.
- **[02 — Architecture & the Six-Stage Pipeline](02.md)** — The hybrid
  Python-orchestrator / subprocess-engine model, stage contracts, and why
  divergent multi-strategy output is the product.
- **[03 — Data Model & Intermediate Representation](03.md)** — The typed
  artifacts that flow between stages (`Source`, `PageDoc`, `SlidePlan`,
  `RenderJob`, `DeckResult`), parsed-not-validated at every boundary.
- **[04 — Command-Line Interface (Fire)](04.md)** — Commands, flags, the `build`
  / `read` / `analyze` / `render` / `split` verbs, exit codes, and the `--`
  positional caveat.
- **[05 — Configuration, Profiles & Strategy Selection](05.md)** — TOML config,
  viewport/aspect profiles, strategy lists, and precedence (flags > config >
  defaults).
- **[06 — Stage 1: Readers](06.md)** — Fetching HTML from URLs and files; static
  (`httpx`) vs dynamic (`Playwright`) paths; the reader plugin contract.
- **[07 — Asset Localization & Offline Bundling](07.md)** — Downloading and
  rewriting CSS, fonts, images, scripts; `monolith` freeze; the offline
  guarantee.
- **[08 — Stage 2: Framework Classification](08.md)** — The fingerprint rules
  engine (Webflow, MkDocs Material, Bubble, Docusaurus, Framer, generic); why we
  don't use Wappalyzer.
- **[09 — Stage 2: Viewport Pagination Analysis](09.md)** — Bounding-box probing
  at the target stage, semantic-snap break detection, over-tall block splitting.
- **[10 — Stage 2: Optional Vision/LLM Analysis](10.md)** — MiniCPM-V via
  llama.cpp/Ollama, structured output, caching, the `--reasoning off` footgun;
  strictly opt-in.
- **[11 — Stage 3: Importer Framework & Plugin API](11.md)** — The normalizer
  ABC, detect/transform contract, entry-point discovery, layout vocabulary.
- **[12 — Stage 3: Webflow Importer](12.md)** — Porting the `webflow2reveal`
  five-step transform; section selection, colour resolution, background
  classification.
- **[13 — Stage 3: MkDocs Material Importer](13.md)** — `md-content__inner`
  extraction, heading-based splitting, chrome removal.
- **[14 — Stage 3: Generic & Other Importers](14.md)** — trafilatura-backed
  generic path; Bubble/Docusaurus/Framer rules; `clear-html` pre-pass.
- **[15 — Stage 4: Pre-Exporters](15.md)** — Paged-media CSS injection, reveal
  wrapping, per-engine HTML preparation.
- **[16 — Stage 5: Exporter Framework & Plugin API](16.md)** — The exporter ABC,
  capability flags (JS support, paged-media), parallel dispatch.
- **[17 — Stage 5: Chromium / Playwright Exporter](17.md)** — `page.pdf()` at a
  locked stage size; the Chromium-only constraint; print-background.
- **[18 — Stage 5: CSS Paged-Media Exporters](18.md)** — Vivliostyle CLI
  (primary, AGPL, shell out), Prince (opt-in premium).
- **[19 — Stage 5: Slide-Framework Exporter (Reveal.js)](19.md)** —
  Serving the reveal HTML and capturing per-slide frames natively via Playwright.
- **[20 — Stage 6: Writers](20.md)** — PDF splitting (`pypdf`/`pikepdf`), SVG via
  `vexy-pdfsvgpy`, the reveal preview index, file naming.
- **[21 — Orchestration, Concurrency & Caching](21.md)** — The fan-out graph,
  `anyio` structured concurrency, Chromium pool limits, content-addressed cache.
- **[22 — Error Handling, Logging & Observability](22.md)** — Partial-failure
  policy (a failed strategy must not kill the run), `loguru`, helpful messages.
- **[23 — Testing Strategy & Functional Examples](23.md)** — Unit/edge/error/
  integration/smoke tiers, the `examples/` runnable corpus, golden fixtures.
- **[24 — Packaging, Dependencies & Roadmap](24.md)** — `pyproject.toml`, the
  dependency table with licence hazards, MVP staging, future work.
