<!-- this_file: DEPENDENCIES.md -->

# Dependencies

Every dependency, why it was chosen, and its licence. Licence hazards are called
out because vexy-dexypy ships under MIT and must not link AGPL/GPL code (spec/24).

## Core (always installed)

- **httpx[http2]** (BSD-3) — static fetch + asset downloads; HTTP/2, sync API.
- **beautifulsoup4** (MIT) + **lxml** (BSD) — readable DOM surgery in importers.
- **selectolax** (MIT) — fast Lexbor-backed parsing for hot paths.
- **pypdf** (BSD) — pure-Python PDF split; vendorable, no native dep.
- **fire** (Apache-2.0) — zero-boilerplate CLI.
- **loguru** (MIT) — structured logging.
- **rich** (MIT) — the per-strategy summary table.
- **anyio** (MIT) — structured concurrency primitives.
- **playwright** (Apache-2.0) — core since `live` is the default fetch mode
  (issue 103): navigation, pagination probe, in-browser preprocessing, Chromium
  PDF export. Needs `playwright install chromium`. When absent, `live` degrades to
  `localize` (httpx) so the package still functions.

## Optional extras

- **trafilatura** (`extract`, Apache-2.0) — content extraction for the generic
  importer. Falls back to a chrome-stripping pass if absent.
- **pikepdf** (`pdf`, MPL-2.0) — qpdf-backed split for damaged/structured PDFs.
- **instructor** (`vision`, MIT) — structured/validated LLM output.

## External tools (not pip; degrade gracefully when missing)

- **Node** → `@vivliostyle/cli` (AGPL-3.0). **Vivliostyle is shelled out only —
  never linked** (AGPL boundary).
- **single-file / monolith** (CC0) — single-file page archivers for `offline`
  fetch mode (`offline_tool`); inline a page into one self-contained HTML (spec/07
  Tier-3). `single-file` via npm (`single-file-cli`), `monolith` via cargo/brew.
  Absent ⇒ degrade to `localize`.
- **poppler** (`pdftocairo`) — pulled in by `vexy-pdfsvgpy` for SVG output.
- **Prince** (proprietary) — opt-in premium exporter; set `VEXY_DEX_PRINCE_PATH`.
- **Ollama / llama.cpp** — optional MiniCPM-V vision server. Serve with the
  thinking template OFF (`--reasoning off`) or Instruct output breaks.

## Licence hazards (do not violate)

- **Vivliostyle CLI** — AGPL-3.0: subprocess only.
- **PyMuPDF** — AGPL/commercial: **not used**; pypdf/pikepdf instead.
- **Surya** — GPL-3.0: research-only, not a dependency.
- **Prince** — proprietary: opt-in, user-supplied binary.

## Vendored assets

- **reveal.js 5.1** (MIT) — `src/vexy_dexypy/assets/reveal/` (reveal.css, reveal.js,
  theme white.css). Bundled so the reveal exporter input and reveal preview are
  self-contained offline decks.
- **vexy-dexyjs** (MIT) — `src/vexy_dexypy/assets/vexy-dexyjs.js`, the in-browser
  DOM preprocessor injected by `_browser.run_js_preprocessor`. Vendored, not a pip
  dependency: it lives in the sibling `vexy-dexyjs` repo (npm package) and is
  regenerated into this asset path by that repo's `npm run build:py`. Keep the two
  in sync when the JS changes; a future option is to pin a published CDN version.

## Not a dependency

- **webflow2reveal** — its `compiler.py` was copied and adapted into
  `vexy_dexypy.importers.webflow` (author's own code, no constraint). The legacy
  package is scheduled for removal once the importer reaches full parity.
