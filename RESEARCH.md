<!-- this_file: RESEARCH.md -->

# vexy-dexypy — Research Conclusions & Recommendations

This file distills the seven research reports in `research/` (qwen, grok, dsk,
cla, pplx, gemi, gpt1) into a single set of decisions. Where the reports
disagree, the disagreement is noted and a call is made. Everything here feeds
the specification in `spec/`.

## The one-sentence scope

> Fetch an HTML page, classify it, normalize its DOM, paginate it intelligently
> at a target aspect ratio, render it to PDF through several engines in
> parallel, and slice each result into named single-page PDFs and SVGs so the
> user can cherry-pick slides across strategies.

Resist everything that isn't in that sentence.

## Consensus across all reports

Six independent reports agreed on the spine of the tool. When six models
converge without coordination, treat it as a strong prior.

- **Hybrid Python core, subprocess for Node/CLI engines.** A pure-Python
  renderer can't see JavaScript layout; a pure-Node tool fights the Fire-CLI
  requirement. The Python orchestrator shells out to browser- and Node-based
  engines. (All reports.)
- **Playwright is the backbone.** It is the reader for JS-heavy pages, the
  pagination analyzer (bounding-box probing at the target viewport), and a
  first-class PDF exporter. Microsoft-maintained, weekly releases, Apache-2.0.
  Note: `page.pdf()` is Chromium-only — Firefox/WebKit raise. (All reports.)
- **Multi-engine export is the product, not a feature.** Different engines
  paginate differently; that divergence is the point. Run them in parallel,
  emit one folder per strategy, let the user choose. (IDEA + all reports.)
- **Per-slide splitting is a writer concern.** Render a multi-page PDF, then
  split into `NN-slide.pdf` files. (All reports.)
- **Fire CLI, `importlib.metadata` entry points for importer/exporter plugins.**
  (cla, dsk explicitly; others implicitly.)

## Decisions by pipeline stage

### Stage 1 — Readers (fetch + asset localization)

- **Primary fetch:** `httpx[http2]` for static pages; **Playwright** for pages
  that hydrate client-side (Webflow Interactions, Bubble, Framer).
- **Asset localization / offline freeze:** `monolith` (Rust CLI, CC0) is the
  most reliable single-file archiver in 2026; pipe Chromium-rendered DOM through
  it. `pywebcopy` is the pure-Python fallback for static pages. Custom
  `ThreadPoolExecutor` asset downloader (gemi's `PageReader`) is the
  no-extra-dependency baseline.
- **Avoid:** `wget --convert-links` doesn't rewrite JS-generated paths; fine
  only for quick static tests.

### Stage 2 — Pre-Importers (classify + paginate + optional vision)

- **Framework fingerprinting:** a ~200-line rules engine, NOT a library. The
  active reports (cla, dsk, pplx) agree `python-Wappalyzer` is dead (0.3.1,
  2020) and Wappalyzer went closed. Fingerprints are short and stable:
  - Webflow → `data-wf-page`, `[data-w-id]`, `html.w-mod-js`, `w-*` classes,
    `webflow.js`.
  - MkDocs Material → `md-content`, `md-typeset`, `md-nav`, `data-md-component`,
    `<meta name=generator content="mkdocs-material ...">`.
  - Docusaurus → `#__docusaurus`, `.theme-doc-markdown`.
  - Bubble → `bubble-element`, `[data-bb-id]`. Framer → `data-framer-name`.
  - Static generators (Hugo/Jekyll/Astro/Next) → trust `meta[generator]` and
    semantic HTML; route to the generic importer.
- **Viewport pagination:** no off-the-shelf library exists. Inject JS via
  `page.evaluate`, collect `getBoundingClientRect()` for
  `section, article, h1, h2, h3, img`, then snap page breaks to semantic
  boundaries; split over-tall blocks into `round(height / stage_height)`
  screens. gemi's `_calculate_breakpoints` is the reference algorithm.
- **Content extraction (for text-heavy pages):** `trafilatura` (Apache-2.0,
  best F1 in the cited 2023 SIGIR benchmark, emits HTML/Markdown/XML).
- **Parsing speed tier:** `selectolax` (Lexbor backend, ~25× faster than BS4)
  for hot paths; `BeautifulSoup4 + lxml` where humans edit the code (the
  `webflow2reveal` choice).
- **Optional vision/LLM:** `MiniCPM-V 4.6` GGUF via `llama.cpp` or Ollama
  (Apache-2.0, ~2 GB, OCR-strong). **Footgun:** pass `--reasoning off` —
  llama.cpp enables a thinking template by default that breaks Instruct output.
  Strictly optional, cached by URL+screenshot hash, behind a flag. Validate
  output with `instructor`/Pydantic, never trust prose.

### Stage 3 — Importers (normalize per framework)

- **Webflow:** copy and adapt the five-step transform from
  `private/webflow2reveal/py/src/webflow2reveal/compiler.py` (one ~31 KB module,
  the author's own legacy code) directly into vexy-dexypy — not as a dependency:
  resolve colours → select `<section>` slides (drop nav/footer/menu/banner) →
  rewrite into a small layout vocabulary (`slide-split-layout`, `slide-column`,
  `slide-image-cover`, …) → classify backgrounds by perceptual luminance →
  inject Reveal.js 5.1, generalized to vexy-dexypy's configurable stage and shared
  IR. vexy-dexypy supersedes `webflow2reveal`; the old package is then retired.
- **MkDocs Material:** keep `article.md-content__inner`; split by `<h2>` (then
  `<h3>` if a section overflows); drop `md-sidebar/header/footer/search/nav`.
- **HTML cleaning before paged engines:** `clear-html` flattens div-soup that
  chokes WeasyPrint.
- **Generic:** trafilatura-extract, then split by `<h2>`.

### Stage 4 — Pre-Exporters (CSS injection + reveal wrapping)

- Inject a reusable paged-media stylesheet: `@page { size: 1920px 1080px;
  margin: 0 }`, `section/.slide { break-after: page; width/height fixed;
  overflow: hidden }`, `h2 { break-before: page }`.
- Wrap into `.reveal > .slides > section` for the reveal path (the canonical
  IDEA normalization).

### Stage 5 — Exporters (HTML → PDF, multiple strategies)

Ship four engines; each is a plugin implementing one ABC.

- **Playwright `page.pdf()`** — Chromium fidelity, executes JS. Primary for
  marketing/Webflow. Use `prefer_css_page_size=True`. Fastest warm.
- **WeasyPrint** — pure-Python, no browser, excellent CSS Paged Media, no JS.
  Primary for MkDocs/clean HTML. BSD-3, v68+ in 2026.
- **Vivliostyle CLI** — Node, Chromium-backed, strongest CSS Paged Media
  (running headers, margin boxes). **AGPL-3.0 — shell out, never link.**
- **DeckTape** — for the reveal.js path specifically; Puppeteer-based, captures
  each slide as a clean frame. MIT, v3.16.x.
- **Prince** — opt-in "premium" strategy when the user has a licence; the CSS
  Paged Media reference implementation. Free non-commercial.
- **Avoid:** `pagedjs-cli` (release cadence too slow — reports split, lean
  Vivliostyle), `wkhtmltopdf` (deprecated), `pyppeteer` (abandoned).

### Stage 6 — Writers (split, SVG, preview)

- **PDF split:** `pypdf` (BSD, pure-Python, vendorable) is the default for a
  permissively-licensed tool. `pikepdf` (MPL-2.0, qpdf) for damaged/structured
  PDFs. **`PyMuPDF` is fast but AGPL** — only if the project itself is AGPL or
  licensed commercially.
- **PDF → SVG:** delegate to **`vexy-pdfsvgpy`** (the sibling project), which
  wraps `pdftocairo` (poppler) with a `mutool convert` fallback. Avoid Inkscape
  (breaks ligatures) and cairosvg/svglib (wrong direction; already on
  vexy-pdfsvgpy's reject list).
- **Reveal preview writer:** emit `index.html` with one `<section><img
  src="slide.svg"></section>` per page inside the reveal chassis,
  `Reveal.initialize({width:1920,height:1080})`.

## Cross-cutting decisions

- **CLI:** Fire (Apache-2.0). Caveat: flags after positionals need `--`.
- **Plugins:** `importlib.metadata` entry-point groups `vexy_dexypy.readers`,
  `.importers`, `.exporters`, `.writers`. Each implements a tiny ABC with a
  `detect(html) -> float` confidence score.
- **Concurrency:** `anyio` over raw asyncio; cap the Chromium pool with a
  `CapacityLimiter` (browsers are heavy).
- **Logging:** `loguru`, always-on `--verbose`.
- **Python:** 3.12+, `uv`, type hints everywhere, dataclasses/Pydantic at I/O
  edges.

## License hazards to track (DEPENDENCIES.md must record these)

- Vivliostyle CLI — AGPL-3.0 (shell out only).
- PyMuPDF — AGPL or commercial (prefer pypdf/pikepdf).
- Surya — GPL-3.0, commercial licence for self-host (research only).
- Prince — proprietary (opt-in).
- `webflow2reveal` — **not a dependency.** Its `compiler.py` is copied/adapted
  into vexy-dexypy (author's own code, no constraint); the legacy package is
  retired once the Webflow importer reaches parity.

## MVP staging (synthesized from cla + dsk roadmaps)

1. **Week 1 — walking skeleton:** httpx/Playwright reader → generic importer →
   Playwright exporter → pypdf writer → Fire `build URL`. One strategy, one
   deck/sec on static pages.
2. **Weeks 2–3 — CMS-aware:** Webflow + MkDocs importers; Vivliostyle +
   native reveal exporters; fingerprint engine; viewport pagination.
   Benchmark against fontlab.com and blog.fontlab.com.
3. **Week 4+ — optional intelligence:** MiniCPM-V pre-importer behind a flag;
   SVG output via vexy-pdfsvgpy; reveal preview writer.
