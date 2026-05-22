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

## Optional extras

- **playwright** (`browser`, Apache-2.0) — dynamic reader, pagination probe,
  Chromium PDF exporter. Needs `playwright install chromium`.
- **trafilatura** (`extract`, Apache-2.0) — content extraction for the generic
  importer. Falls back to a chrome-stripping pass if absent.
- **pikepdf** (`pdf`, MPL-2.0) — qpdf-backed split for damaged/structured PDFs.
- **instructor** (`vision`, MIT) — structured/validated LLM output.

## External tools (not pip; degrade gracefully when missing)

- **Node** → `@vivliostyle/cli` (AGPL-3.0). **Vivliostyle is shelled out only —
  never linked** (AGPL boundary).
- **monolith** (CC0) — single-file page freeze for the hardest pages.
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

## Not a dependency

- **webflow2reveal** — its `compiler.py` was copied and adapted into
  `vexy_dexypy.importers.webflow` (author's own code, no constraint). The legacy
  package is scheduled for removal once the importer reaches full parity.
