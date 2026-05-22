<!-- this_file: IDEA.md -->

# vexy-dexypy — the idea

vexy-dexypy turns an HTML page into slide decks (primarily PDF). It does not invent
slides; it discovers the slides a page already implies, normalizes the markup,
and renders that structure through several PDF engines at once. Each engine
writes its own folder of single-page slides. The user assembles a final deck by
picking the best rendering of each slide across folders — the hero section from
one strategy, the text-heavy slides from another.

The divergence between strategies is the product, not a defect. One strategy may
produce 11 slides and another 14; that is normal and expected.

## One-sentence scope

> Fetch an HTML page, classify it, normalize its DOM, paginate it intelligently
> at a target aspect ratio (16:9 by default, customizable), render it to PDF
> through several engines in parallel, and slice each result into named
> single-page PDFs and SVGs so the user can cherry-pick slides across
> strategies.

vexy-dexypy is written in Python, works offline after the initial fetch, and runs
as a [Fire](https://github.com/google/python-fire) CLI.

## Recognizing the page

vexy-dexypy recognizes common page builders and delegates DOM preprocessing to
`vexy-dexyjs` running in the browser.

- **Webflow** — already a stack of sectioned `<section>`s; preprocessed using the
  `vexy-dexyjs` package, which is a smarter, generalized successor to the legacy
  [`webflow2reveal`](https://github.com/twardoch/webflow2reveal) (locally cloned as
  `./private/webflow2reveal/`) and its js implementation.
- **MkDocs + MkDocs Material** — clean semantic docs; the content column is extracted,
  split by heading, and formatted.
- **Other builders** (Bubble, Framer, Docusaurus, Shuffle, static-site
  generators) — light-touch rules over a generic content-extraction path.

## Normalization

After ingesting a page, the pipeline normalizes it — moving DOM nodes and adding
wrappers so a slide engine can consume it. The canonical target is a reveal.js-compatible
chassis:

```html
<div class="reveal">
  <div class="slides">
    <section>Slide 1</section>
    <section>Slide 2</section>
  </div>
</div>
```

The normalization happens inside the browser context using `vexy-dexyjs`. This ensures
dynamic layout changes, computed styles, and page assets are correctly preprocessed.

## The six-stage pipeline

1. **Readers** — technical fetching of HTML from URLs/files plus assets (images, fonts,
   CSS), localized for offline use. Supports a choice of standard `playwright`,
   `playwrightauthor` (persistent logged-in sessions via Chrome for Testing), and
   `cloakbrowser` (stealth Chromium for bypassing bot detection).
2. **Pre-importers** — decision makers. Render the page in a headless browser at the
   target slide viewport and measure how the browser naturally paginates it: collect
   bounding boxes, check visibility, and snap slide breaks to semantics, then count
   how many "screens" run until the next break. Optionally, a cheap local vision model
   refines breaks on unstructured pages.
3. **Importers** — ingest the page and run `vexy-dexyjs` in the browser context to perform
   general preprocessing and DOM normalization into slide-ready structures.
4. **Pre-exporters** — the middle of the process: inject paged-media CSS, wrap for
   reveal.js (or alternative chassis), and prepare engine-ready HTML.
5. **Exporters** — the engines that transform HTML into PDF (single- or multi-page).
   Run several in parallel (Playwright Chromium, Vivliostyle, Prince, native Reveal).
6. **Writers** — purely technical: split exporter output into appropriately named
   single-page PDFs, optional SVGs (via `vexy-pdfsvgpy`), and a preview index.

## Tools it builds on

Decided after research, synthesized in `RESEARCH.md`:

- **Fetch / freeze:** `httpx`, Playwright, `playwrightauthor`, `cloakbrowser`.
- **In-browser Preprocessor:** `vexy-dexyjs` (generalizes `webflow2revealjs` to preprocess any page).
- **Offlinization / Linearization:** Integration with tools like `single-file-cli`, `monolith`,
  `juice`, and `css-inline` via `vexy-dexyjs`.
- **Export engines:** Playwright (Chromium), [Vivliostyle](https://vivliostyle.org/en/),
  a native reveal.js exporter, and opt-in [Prince](https://www.princexml.com/).
- **Split / SVG:** `pypdf`/`pikepdf`, and `vexy-pdfsvgpy`.
- **Optional vision:** MiniCPM-V 4.6 via llama.cpp/Ollama.

## Where to go next

- The synthesized research and tool decisions: [`RESEARCH.md`](RESEARCH.md).
- The full design, 24 chapters: [`spec/00-tldr.md`](spec/00-tldr.md).
- The build plan: [`TODO.md`](TODO.md).
- Guidance for contributors and coding agents: [`CLAUDE.md`](CLAUDE.md).
