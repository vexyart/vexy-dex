<!-- this_file: CHANGELOG.md -->

# Changelog

## Unreleased

### Added

- **Continuous integration.** `.github/workflows/ci.yml` runs the offline test
  suite on Ubuntu, macOS and Windows across Python 3.12 and 3.13, plus a lint job
  (`ruff check`, `ruff format --check`, `mypy`). All jobs use `uv`.
- **Release automation.** `.github/workflows/release.yml` builds the sdist/wheel
  on every `v*` tag, publishes to PyPI via trusted publishing, and cuts a GitHub
  release with the matching changelog section attached.
- **Documentation site.** `docs/` now carries a Jekyll + Just the Docs page
  (`docs/index.md`, `docs/_config.yml`) for GitHub Pages, with a hand-drawn
  project icon at `docs/assets/icon.png`.

### Changed

- **`mypy` is now clean.** Added a pragmatic `[tool.mypy]` config and resolved the
  BeautifulSoup `Tag`/`PageElement` typing friction in `dom.py`, `preexport.py`
  and the importers with `isinstance` guards (no runtime change).
- **`ruff format` applied** across `src/` and `tests/` so the tree is
  format-clean and CI can enforce it.
- **README status** updated from "specification complete, implementation
  starting" to reflect the working core pipeline and offline test suite.

### Fixed

- **Faithful rendering of designed pages — no more white-bg/margin override.**
  The pre-exporter injected a neutral slide theme (`.slide { padding: 4% }`,
  `.slide-light-bg { background:#fff }`) onto every deck, overriding the design of
  Webflow/Framer pages. `preexport.theme_css(framework)` now returns only the
  badge-hide rule for `webflow`/`framer` (keeping the page's own CSS) and the full
  neutral theme for generic/Markdown decks; structural paging CSS is unchanged.
  The Playwright exporter pins zero margins for a true vector "PDF screenshot"
  (screen media, exact stage size, real backgrounds), and the paged CSS injects
  `* { -webkit-print-color-adjust: exact; print-color-adjust: exact }` so colours
  survive in Chromium and Prince (issue 104). Verified: the TransType page renders
  its real red hero and green quote slides at 1280×720 instead of white-bg slides.
  spec [17](spec/17.md) documents the full faithful-capture recipe and
  [20](spec/20.md) the two SVG routes (PDF→SVG default vs browser-side DOM→SVG);
  `TODO.md` tracks the deferred WebKit-native and DOM→SVG options.
- **Webflow/Framer sectioning dropped real content, keeping only the footer.**
  The `vexy-dexyjs` preprocessor selected slides via
  `querySelectorAll('section, .section, …')`, which on many live Webflow pages
  matches only stray footer/menu blocks carrying a `section` class token while
  missing the actual content blocks (`<div class="tr-section1">`, `hero`, …). It
  now prefers the content-bearing **top-level children** of the content root,
  falling back to the explicit section selectors only for wrapper-nested layouts.
  Verified on the TransType page: 2 footer-only sections → 14 real content
  sections. (Rebuild `vexy-dexyjs` to refresh the vendored bundle.)

### Changed

- **Default stage is now 1280×720; size profiles renamed by resolution.** The
  `[stage] aspect` / `--aspect` profiles are now `720p` (1280×720, **default**),
  `1080p` (1920×1080), and `810p` (1440×810) — all 16:9; the previous
  `16:9`/`4:3`/`a4-landscape` names are removed (`--size WxH` still overrides).
  Updated `settings.py`, spec [04](spec/04.md)/[05](spec/05.md), README, and tests
  (the short generic fixture now paginates to 2 slides at 720p).

### Added

- **`offline` fetch mode — single-file archiving** (issue 103, Phase 3). New
  `OfflineReader` (`readers/offline.py`) shells out to `single-file` or `monolith`
  (per `Settings.offline_tool`) to inline a page into one self-contained
  `index.html` — the spec/07 Tier-3 path. Selected via `--fetch-mode offline`;
  degrades to `localize` when the archiver is absent, like every other external
  engine. Subprocess discipline (timeout, captured stderr, output check).
- **Chrome extension scaffold for `vexy-dexyjs`** (issue 103, Phase 4). MV3
  extension under `vexy-dexyjs/extension/` (`manifest.json`, `popup.html`,
  `popup.js`, `README.md`) that injects the IIFE bundle into the active tab and
  runs `preprocess()` in place. A `build:ext` esbuild target (wired into
  `npm run build`) emits the git-ignored `extension/vexy-dexyjs.global.min.js`.
- **Browser-native `live` fetch mode, now the default** (issue 103, Phase 2).
  New `LiveReader` (`readers/live.py`) navigates the URL in the chosen browser
  engine, captures the rendered DOM, and injects a `<base href>` at the page's
  post-redirect origin — **without localizing any assets**. Fonts/CSS/images stay
  online and load over the network during the probe, in-browser preprocessing,
  and export, so slides render exactly as the live site serves them. Added
  `Settings.fetch_mode` (`live` | `localize`), the `--fetch-mode` CLI flag, a
  `[fetch]` config section, and the `live` reader entry point. The existing
  `localize` path is preserved as an opt-in for reproducible offline archives;
  `playwright` moved to a core dependency since `live` (the default) needs it.
  Spec [06](spec/06.md)/[07](spec/07.md) updated; offline guarantee scoped to
  `localize` mode. Verified end-to-end: `live` build of a served fixture produced
  4 slide PDFs with zero localized asset dirs.
- **`vexy-dexyjs` promoted to a publishable npm package** (issue 103, Phase 1).
  Reworked `vexy-dexyjs/package.json` with `main`/`module`/`browser`/`unpkg`/
  `jsdelivr`/`exports`/`types` and a multi-format esbuild build: `dist/index.mjs`
  (ESM), `dist/index.cjs` (CJS), `dist/vexy-dexyjs.global.js` + `.min.js` (IIFE
  global `VexyDexy`, for CDN/script-tag use). A separate `build:py` target keeps
  refreshing the bundle vendored at `assets/vexy-dexyjs.js` (verified
  byte-identical, so the Python pipeline is unaffected). Added hand-maintained
  `index.d.ts`, a DOM-free smoke test (`npm test`), a generalized `README.md`,
  and `publish.sh` (git-tag semver via `gitnextver` → npm). See `PLAN.md`.

### Changed

- **Replaced the Node/DeckTape `decktape` strategy with a native `reveal`
  exporter** (`exporters/reveal.py`): Playwright drives reveal.js
  (`getTotalSlides`/`slide`/`next`) and captures one `page.pdf` per slide,
  `pypdf` merges them. Drops the Node + `decktape` toolchain entirely — the
  reveal deck is initialized with `fragments:false` and all chrome off so the
  capture loop is deterministic. Strategy/output folder renamed `decktape` →
  `reveal`; classifier order updated.
- **Removed WeasyPrint support entirely** — exporter, entry point, extras,
  classifier orders, tests, examples and spec/doc references. The paged-media
  recommendation is now Vivliostyle (with Prince opt-in). `test_writers` builds
  its sample PDF with `pypdf` instead of WeasyPrint (also fixing the prior
  GLib-related failures). Shipped engines: playwright, vivliostyle, reveal, prince.
- `examples/_runner.py` now defaults to `strategies="all"`, so examples exercise
  every engine whose deps are installed and cleanly skip the rest via
  `available()`, instead of a hardcoded pair.

### Spec — decouple the slide IR from reveal.js (planning)

The normalized IR was reveal-shaped (`.reveal > .slides`) emitted by importers,
so the five strategies diverged only by PDF engine, not by framework. Revised
the spec to make the **chassis** (reveal / paged / impress / marp) a per-strategy
stage-4 choice over a framework-neutral `<section class="slide">` IR, so genuine
alternatives to reveal are possible. Updated spec/03, spec/11, spec/15, spec/16,
spec/19 and added the refactor + `impress`/`marp` tasks to TODO.md. Code refactor
is tracked, not yet implemented.

### Fixed

- **Localized pages rendered unstyled.** Three causes, all fixed:
  - Localized `<link>`/`<script>` kept `integrity`/`crossorigin`; under `file://`
    (and even http) Subresource Integrity blocks the now-local stylesheet. The
    localizer strips both attributes (`readers/localize.py`).
  - The Webflow importer dropped the page's stylesheets when wrapping slides —
    now carries them via `dom.head_styles` (matching the other importers).
  - An already-reveal-shaped live page (e.g. a vexy.art deck) short-circuited
    normalization and kept `assets/` refs relative to `raw/`, which broke once
    the HTML moved to the strategy dir. The `already_reveal` branch now relocates
    + rewrites paths via `write_normalized` for raw input (idempotent no-op for
    our own normalized output).
- **Browser navigation hardened.** All local-page rendering (playwright/reveal/
  vision/pagination probe) now serves the deck over a throwaway loopback HTTP
  server and waits for `load` instead of opening `file://` and waiting for
  `networkidle` — a real http:// origin avoids file:// CORS/SRI/font quirks, and
  `load` doesn't hang when offline JS retries dead CDN assets (`_browser.py`;
  fixes the fontlab-8 `Page.goto` timeout).
- **Webflow "Made in Webflow" badge** (`.w-webflow-badge`) is DOM-removed in the
  importer and force-hidden via the pre-exporter theme CSS.
- Reveal chassis now disables all reveal.js UI chrome (controls, progress,
  slide-number, help/pause overlays) via `Reveal.initialize` flags plus a CSS
  guard — slides are destined for PDF/SVG and must not show navigation buttons
  (`preexport._bundle_reveal`, spec/15).

- Content-extracting importers (mkdocs-material, docusaurus, generic) now carry
  the source page's stylesheet `<link>`s and `<style>` blocks into the reveal
  chassis via the new `dom.head_styles` helper. Previously `wrap_reveal` emitted
  an empty `<head>`, so the localized framework/highlight CSS (spec/07, spec/13)
  never loaded and decks rendered as unstyled prose.
- `examples/webflow_fontlab_8.py`: corrected a malformed `httpshttps://` URL and
  the copy-pasted header/docstring (was duplicating the homepage example).

### Added — initial implementation

The full six-stage pipeline, implemented and tested end-to-end.

- **Core**: typed IR (`model.py`), `Settings` with aspect/size profiles
  (default 1920×1080), typed error taxonomy, `loguru` logging.
- **CLI** (Fire): `build`, `read`, `analyze`, `split` with a rich per-strategy
  summary and 0/1/2 exit codes.
- **Stage 1 — readers**: static (httpx) + dynamic (Playwright) with plugin
  discovery, file handling, thin-body escalation, retry-with-backoff, tier-1
  asset localization, content hashing.
- **Stage 2 — pre-importers**: fingerprint classifier (webflow, mkdocs-material,
  docusaurus, framer, bubble, generic) with strategy-order recommendation;
  viewport bounding-box pagination with a no-browser fallback; optional
  MiniCPM-V vision refinement (cached, heuristic-floor).
- **Stage 3 — importers**: shared DOM helpers + webflow (adapted from
  webflow2reveal `compiler.py`), mkdocs-material, and generic (trafilatura)
  importers; idempotent on canonical input.
- **Stage 4 — pre-exporters**: paged-media CSS + neutral theme injection →
  `RenderJob`.
- **Stage 5 — exporters**: capability-aware selection; weasyprint, playwright,
  vivliostyle, decktape, prince with availability gating and subprocess
  discipline.
- **Stage 6 — writers**: pypdf split, optional SVG via vexy-pdfsvgpy, preview
  index; per-strategy failure isolation.
- **Tests**: 29 passing including a full pipeline integration through WeasyPrint;
  offline fixtures, `test.sh`, and a runnable example.
- **Docs**: `DEPENDENCIES.md` with the licence-hazard table.

### Notes

- Webflow logic copied & adapted from the author's legacy `webflow2reveal`
  (now first-class vexy-dexypy code; the package is slated for removal).
