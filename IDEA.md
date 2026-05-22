<!-- this_file: IDEA.md -->

# vexy-dex — the idea

vexy-dex turns an HTML page into slide decks (primarily PDF). It does not invent
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

vexy-dex is written in Python, works offline after the initial fetch, and runs
as a [Fire](https://github.com/google/python-fire) CLI.

## Recognizing the page

vexy-dex recognizes common page builders and applies a tailored normalization to
each:

- **Webflow** — already a stack of sectioned `<section>`s; copy and adapt the
  transform from
  [`webflow2reveal`](https://github.com/twardoch/webflow2reveal) (see
  `./private/webflow2reveal/`) into vexy-dex as first-class code. vexy-dex
  supersedes that legacy one-trick pony, which is then retired. Examples:
  <https://www.vexy.art/lines/>,
  <https://www.vexy.art/lines/case-retro-poster/>, <https://www.fontlab.com/>.
- **MkDocs + MkDocs Material** — clean semantic docs; extract the content
  column, split by heading, keep code and tables. Example:
  <https://blog.fontlab.com/> (`fontlab/blog.fontlab.com`).
- **Other builders** (Bubble, Framer, Docusaurus, Shuffle, static-site
  generators) — light-touch rules over a generic, content-extraction path.

## Normalization

After ingesting a page, vexy-dex normalizes it — moving DOM nodes and adding
wrappers so a slide engine can consume it. The canonical target is the reveal.js
chassis:

```html
<div class="reveal">
  <div class="slides">
    <section>Slide 1</section>
    <section>Slide 2</section>
  </div>
</div>
```

There is one shared normalization into a canonical layout vocabulary, plus
output-specific preparation per engine.

## The six-stage pipeline

1. **Readers** — purely technical fetching of HTML from URLs and files, plus
   assets (images, fonts, CSS, video), localized for offline use.
2. **Pre-importers** — decision makers. Render the page in a headless browser at
   the target slide viewport and measure how the browser naturally paginates it:
   collect bounding boxes, check visibility, and snap slide breaks to semantics
   (before a new `<section>`, or in its absence before a high-level heading like
   `<h2>`), then count how many "screens" run until the next break. Optionally,
   a cheap local vision model (e.g.
   [MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6-gguf)) refines
   breaks on unstructured pages. The pagination must not be stupid.
3. **Importers** — ingest the readers' output and apply framework-specific
   preprocessors and normalizers.
4. **Pre-exporters** — the middle of the process: inject paged-media CSS, wrap
   for reveal.js, and prepare engine-ready HTML.
5. **Exporters** — the engines that transform HTML into PDF (single- or
   multi-page). Run several in parallel; let the user choose.
6. **Writers** — purely technical: split exporter output into appropriately
   named single-page PDFs, optional SVGs (via
   [`vexy-pdfsvgpy`](https://github.com/vexyart/vexy-pdfsvgpy)), and a preview —
   for example a reveal.js page where each slide is a full-page SVG.

## Tools it builds on

Decided after the research in [`research/`](research/), synthesized in
[`RESEARCH.md`](RESEARCH.md):

- **Fetch / freeze:** `httpx`, Playwright, `monolith`.
- **Parse / extract:** `selectolax`, `BeautifulSoup`+`lxml`, `trafilatura`.
- **Normalize Webflow:** code copied & adapted from
  [`webflow2reveal`](https://github.com/twardoch/webflow2reveal)'s `compiler.py`
  (`./private/webflow2reveal/`), now first-class vexy-dex code; the legacy
  package is retired.
- **Export engines:** Playwright (Chromium),
  [Vivliostyle](https://vivliostyle.org/en/), a native reveal.js exporter, and
  opt-in [Prince](https://www.princexml.com/).
- **Split / SVG:** `pypdf`/`pikepdf`, and `vexy-pdfsvgpy`.
- **Optional vision:** MiniCPM-V 4.6 via llama.cpp/Ollama.

It installs and uses these where possible, degrading gracefully when an optional
engine is absent.

## Where to go next

- The synthesized research and tool decisions: [`RESEARCH.md`](RESEARCH.md).
- The full design, 24 chapters: [`spec/00-tldr.md`](spec/00-tldr.md).
- The build plan: [`TODO.md`](TODO.md).
- Guidance for contributors and coding agents: [`CLAUDE.md`](CLAUDE.md).
