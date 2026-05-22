# vexy-dex: A Toolchain Audit

*Open-source libraries that eat HTML and spit out slide decks — organized by pipeline stage, with clear winners and honest caveats.*

---

## Step 1: Readers — Fetch HTML and Assets

You need two things here: grab the raw HTML, and download every image, font, CSS, and JS file so offline rendering works. The tool that does both well:

### pywebcopy

- **Repo**: [github.com/rajatomar788/pywebcopy](https://github.com/rajatomar788/pywebcopy)
- **Install**: `pip install pywebcopy`
- **License**: MIT · **Stars**: ~640 · **Language**: Python

It mirrors a full page (or entire site) to disk, rewriting all asset paths to local relative links. CSS, JS, images, fonts — everything lands in a folder you can point a browser or PDF engine at.

```python
from pywebcopy import save_webpage

save_webpage(
    url="https://www.vexy.art/lines/",
    project_folder="fetched/vexy-lines",
    bypass_robots=True
)
```

**Why it fits**: It produces a self-contained local copy. Every downstream tool in this report expects local files, not live URLs.

### Alternatives

- **wget** (system tool): `wget --mirror --page-requisites --convert-links` works but doesn't rewrite JavaScript-generated asset paths. Fine for static pages; useless for Webflow or SPAs.
- **Playwright/Puppeteer** directly: You can intercept network requests and save responses. More control, more code. Worth it when pages are entirely JS-rendered.
- **pagesource** ([github.com/timf34/pagesource](https://github.com/timf34/pagesource)): Captures resources like the browser DevTools Sources tab. Good for dynamic imports (webpack chunks, Vite code-splitting).

### Recommendation

- Use **pywebcopy** for static and mostly-static pages (Webflow, MkDocs, Bubble exported pages).
- Use a custom **Playwright** script for SPAs that assemble their DOM entirely in JavaScript.
- Fall back to `wget` when you want zero Python dependencies for a quick test.

---

## Step 2: Pre-Importers — Analyze and Classify

This is where vexy-dex gets clever. Before converting, you need to know *what kind of page* you're dealing with, and where the natural "slide breaks" should fall.

### Page Classification

**@threvo/website-understanding-sdk** — the most pragmatic classifier available.

- **Repo**: [npmjs.com/package/@threvo/website-understanding-sdk](https://www.npmjs.com/package/@threvo/website-understanding-sdk)
- **Install**: `npm install @threvo/website-understanding-sdk`
- **Language**: TypeScript (Node)

It detects page type (product, article, search, list, login, home), identifies semantic sections (nav, hero, footer, sidebar, card grids, forms, content areas), and extracts CSS selectors for all interactive elements.

```javascript
import { analyzePage } from '@threvo/website-understanding-sdk';

const result = await analyzePage('https://www.fontlab.com/font-editor/fontlab/', {
  dynamic: true  // renders JS before analysis
});

console.log(result.page_type);  // e.g. "product"
console.log(result.sections);
// [{type: "nav", selector: "nav"}, {type: "hero", selector: "[class*='hero']"}, ...]
```

For vexy-dex, the section detection is the prize: knowing where the hero ends and the feature grid begins tells you where to insert page breaks.

**Fathom** (by Mozilla) is the more sophisticated alternative.

- **Repo**: [github.com/mozilla/fathom](https://github.com/mozilla/fathom)
- **Install**: `npm install fathom-web`
- **Language**: JavaScript

Fathom uses trained rulesets to recognize page parts — it's a supervised-learning framework that scores DOM nodes against conditions you define. It ships with rulesets for pop-ups, address forms, slideshows, and previous/next buttons. If you invest time writing custom rulesets, Fathom can classify Webflow sections, MkDocs nav, and Bubble repeating groups with high accuracy. The cost is upfront: you need to label training pages.

### DOM Structure Analysis

**betterhtmlchunking** — heading-aware segmentation.

- **Repo**: [github.com/carlosplanchon/betterhtmlchunking](https://github.com/carlosplanchon/betterhtmlchunking)
- **Install**: `pip install betterhtmlchunking`
- **License**: Open source · **Language**: Python

It builds a DOM tree, identifies content-rich regions, and splits HTML into chunks based on headings and text density. This is essentially what you'd build by hand for the "split before H2" logic described in the vexy-dex idea.

```python
from betterhtmlchunking import DomRepresentation

dom = DomRepresentation(
    MAX_NODE_REPR_LENGTH=500,
    website_code=html_content,
)
dom.start()

for idx in dom.tree_regions_system.sorted_roi_by_pos_xpath:
    html_chunk = dom.render_system.get_roi_html_render_with_pos_xpath(idx)
    print(f"--- Slide {idx} ---")
    print(html_chunk)
```

### Viewport-Aware Pagination Detection

This is the most vexy-dex-specific step and there is no off-the-shelf library for it. You need to render the page at 16:9 viewport dimensions and detect where the natural visual breaks are. The approach:

1. Launch Playwright with a viewport matching the target slide deck (e.g., 1920×1080).
2. Inject a JavaScript snippet that walks the DOM and records the `getBoundingClientRect()` of every block-level element.
3. Group elements by vertical position into "screenfuls."
4. Cross-reference with semantic breaks (section tags, H2 headings, `<article>` boundaries).
5. When a semantic break falls within a screenful, snap the page break to the semantic boundary.

Tools that help:
- **Playwright Python** (`pip install playwright; playwright install chromium`): The browser automation layer.
- **Pagespec** ([npmjs.com/package/pagespec](https://www.npmjs.com/package/pagespec)): A CLI that extracts component bounds, computed styles, and occlusion data. It injects a client-side object walker and outputs a JSON tree. Useful as a reference implementation for your own DOM walker.
- **shot-scraper** (`pip install shot-scraper`): Simon Willison's CLI for Playwright-based screenshots and JavaScript execution. Good for prototyping the viewport analysis without writing browser automation from scratch.

---

## Step 3: Importers — Normalize and Restructure

Once you've classified the page and decided where slides should break, you need to restructure the DOM: wrap slide groups in the target framework's markup, strip cruft, normalize tags.

### HTML Cleaning

**clear-html** — removes div soup, normalizes structure.

- **Repo**: [github.com/zytedata/clear-html](https://github.com/zytedata/clear-html)
- **Install**: `pip install clear-html`
- **License**: Open source · **Language**: Python

It strips style attributes, removes empty wrapper divs, converts `<div>` containers to semantic elements like `<article>` and `<p>`, and preserves embedded content (Twitter, Instagram).

```python
from lxml.html import fromstring
from clear_html import clean_node, cleaned_node_to_html

node = fromstring(raw_html)
cleaned = clean_node(node)
normalized_html = cleaned_node_to_html(cleaned)
```

This is useful as a pre-pass before feeding HTML to a PDF engine — especially WeasyPrint, which chokes on deeply nested divs.

### DOM Restructuring

For reveal.js output, you need to wrap slides in `<div class="reveal"><div class="slides">`. The most reliable approach is **BeautifulSoup 4** with **lxml** parser:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html, 'lxml')

# Wrap sections in reveal.js structure
reveal_div = soup.new_tag('div', **{'class': 'reveal'})
slides_div = soup.new_tag('div', **{'class': 'slides'})

for section in soup.find_all('section'):
    slides_div.append(section.extract())

reveal_div.append(slides_div)
soup.body.append(reveal_div)
```

For more complex transformations (Webflow to reveal.js specifically), the npm package `@loomchild/webflow-revealjs` provides a starting point, though it's dated and may need updating.

### MkDocs Material Detection

If the source is MkDocs Material, you already have clean semantic HTML. The pre-importer should detect `<article>` tags and the `.md-content` class. You can then extract sections based on heading hierarchy directly.

---

## Step 4: Pre-Exporters — Prepare for Rendering

This stage bridges the gap between normalized DOM and the specific requirements of each PDF engine. Different engines need different things:

- **Reveal.js + Decktape/Playwright**: Needs a complete HTML page with reveal.js CSS/JS loaded, print stylesheet applied, and `?print-pdf` URL parameter.
- **WeasyPrint**: Needs flat, semantically clean HTML with `@page` CSS rules for slide dimensions.
- **Vivliostyle**: Needs HTML with CSS Paged Media directives.
- **Prince**: Similar to Vivliostyle but with proprietary extensions.
- **Fullbleed**: Needs a Python script that composes pages programmatically.
- **Paged.js**: Needs the `paged.polyfill.js` script injected into the page, then rendered through Puppeteer.

### Key Pre-Exporters

- **Paged.js CLI** ([gitlab.pagedmedia.org/tools/pagedjs-cli](https://gitlab.pagedmedia.org/tools/pagedjs-cli)): Takes an HTML file, injects the Paged.js polyfill, runs it through Puppeteer, outputs a paginated PDF. Install: `npm install -g pagedjs-cli`. Usage: `pagedjs-cli ./input.html -o output.pdf`. This is the most direct path from "HTML with CSS print rules" to "paginated PDF."

- **Vivliostyle CLI** ([vivliostyle.org](https://vivliostyle.org/)): Similar idea, stronger typesetting. Install: `npm install -g @vivliostyle/cli`. It reads a configuration file that specifies entry HTML and CSS, then produces PDF via Chromium.

- **Reveal.js PDF export**: If you choose the reveal.js strategy, the pre-exporter generates a self-contained HTML file with reveal.js bundled, then passes it to Playwright for PDF export (see Step 5).

---

## Step 5: Exporters — HTML to PDF

This is the engine room. The right choice depends on what you value: fidelity, speed, offline capability, or typographic quality.

### Chromium-Based (Maximum Fidelity)

**Playwright** (recommended) and **Puppeteer** produce pixel-perfect output because they use a real browser engine. Every CSS feature works. JavaScript executes. The cost: a ~200MB Chromium binary and 1–3 seconds per page.

```python
# Playwright Python example
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    page.goto("file:///path/to/normalized.html")
    page.pdf(
        path="output.pdf",
        width="16in",
        height="9in",
        print_background=True
    )
    browser.close()
```

For single-slide-per-page output, use CSS `page-break-after: always` on slide containers, or use Playwright to screenshot individual elements and stitch into a PDF.

**Gotenberg** ([github.com/gotenberg/gotenberg](https://github.com/gotenberg/gotenberg)) wraps Chromium in a Dockerized Go API. If you want a microservice architecture, it's the cleanest option — submit HTML, get PDF back over HTTP. 11.8K GitHub stars, MIT license.

```bash
docker run -p 3000:3000 gotenberg/gotenberg:8
```

### CSS Print Engines (Offline, Fast, Typographically Superior)

**WeasyPrint** is the Python workhorse.

- **Repo**: [github.com/Kozea/WeasyPrint](https://github.com/Kozea/WeasyPrint)
- **Install**: `pip install weasyprint`
- **License**: BSD · **Stars**: ~8.9K

```python
from weasyprint import HTML

HTML('input.html').write_pdf('output.pdf')
```

Strengths: Pure Python, no browser dependency, excellent CSS Paged Media support, fast. Weaknesses: No JavaScript execution, limited flexbox/grid support. Ideal for MkDocs and other static HTML sources.

**Fullbleed** is the Rust newcomer worth watching.

- **Repo**: [github.com/fullbleed-engine/fullbleed](https://github.com/fullbleed-engine/fullbleed)
- **Install**: `pip install fullbleed`
- **License**: AGPLv3 · **Language**: Rust with Python bindings

It parses HTML+CSS directly and renders to PDF without a browser. Deterministic and reproducible (SHA256 hashing, `--repro-record` / `--repro-check` flags). Python calls release the GIL during rendering, so batch operations are genuinely parallel via Rayon. Not yet at full CSS feature parity, but actively developed.

**PlutoPrint** is a solid middle ground.

- **Repo**: [github.com/plutoprint/plutoprint](https://github.com/plutoprint/plutoprint)
- **Install**: `pip install plutoprint`
- **License**: MIT · **Stars**: ~1,100
- **Language**: Python bindings over a C++ rendering engine (PlutoBook)

Generates PDFs and PNGs with page-level control — extract specific pages, render individual pages to canvas, export ranges. Good when you need programmatic page-by-page control.

```python
import plutoprint

book = plutoprint.Book(plutoprint.PAGE_SIZE_A4)
book.load_url("input.html")
book.write_to_pdf("output.pdf", start_page=2, end_page=15)
```

**Prince** ([princexml.com](https://www.princexml.com/)) is the gold standard for CSS Paged Media but is proprietary. It's worth mentioning because it's the benchmark: if your open-source pipeline matches Prince's output quality, you've won. DocRaptor is its SaaS API wrapper.

### Multi-Strategy Matrix

| Strategy | Engine | Best For | JS Support |
|---|---|---|---|
| reveal.js → Playwright PDF | Chromium | Webflow, highly styled pages | Full |
| Paged.js → Puppeteer | Chromium + polyfill | Pages with CSS print rules | Full |
| Vivliostyle CLI | Chromium + typesetting | Books, long-form documentation | Full |
| WeasyPrint | Python CSS engine | MkDocs, clean semantic HTML | None |
| Fullbleed | Rust engine | Batch, deterministic output | None |
| PlutoPrint | C++ engine | Programmatic page control | None |
| Gotenberg | Chromium (API) | Microservice architecture | Full |

---

## Step 6: Writers — Split, Name, and Package

The exporter produces a multi-page PDF. The writer splits it into single-page PDFs, names them sequentially, and optionally converts pages to SVGs.

### PDF Splitting

**pypdf** — the standard pure-Python PDF manipulation library.

- **Repo**: [github.com/py-pdf/pypdf](https://github.com/py-pdf/pypdf)
- **Install**: `pip install pypdf`
- **License**: BSD · **Stars**: ~10K

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("output.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(f"slides/slide_{i+1:03d}.pdf")
```

**pikepdf** — for when you need surgical precision.

- **Repo**: [github.com/pikepdf/pikepdf](https://github.com/pikepdf/pikepdf)
- **Install**: `pip install pikepdf`
- **License**: MPL 2.0

Built on QPDF (C++), pikepdf manipulates PDF internals — objects, streams, dictionaries — without re-rendering. Faster than pypdf for large files, and handles corrupted PDFs that pypdf chokes on.

```python
import pikepdf

pdf = pikepdf.open("output.pdf")
for i, page in enumerate(pdf.pages):
    single = pikepdf.Pdf.new()
    single.pages.append(page)
    single.save(f"slides/slide_{i+1:03d}.pdf")
```

### SVG Conversion

The vexy-dex idea references [vexy-pdfsvgpy](https://github.com/vexyart/vexy-pdfsvgpy) for PDF-to-SVG conversion. If you need an open-source alternative:

- **pdf2svg** (system tool, Unix): `pdf2svg input.pdf output.svg 1` — extracts page 1 as SVG. Simple, fast, wrapped easily in Python's `subprocess`.
- **Inkscape** command line: `inkscape --export-type=svg --pdf-page=1 input.pdf`
- **CairoSVG**: Only goes SVG → PDF, not the reverse.
- **pdf.js**: Mozilla's PDF renderer can output to canvas, which you can then export as SVG with additional tooling.

---

## Cross-Cutting: CLI Framework

The vexy-dex idea specifies a **Python Fire** CLI.

**Python Fire** ([github.com/google/python-fire](https://github.com/google/python-fire)) turns any Python object into a CLI with zero configuration. Install: `pip install fire`.

```python
import fire

class VexyDex:
    def process(self, url, output_dir="./output", strategies="all"):
        """Process a URL into slide decks."""
        pass

if __name__ == "__main__":
    fire.Fire(VexyDex)
```

Usage:
```bash
python vexy_dex.py process https://www.vexy.art/lines/ --output_dir=./decks --strategies=revealjs,weasyprint
```

Fire auto-generates help text and handles argument parsing. For a tool that exposes multiple commands (fetch, analyze, normalize, export, split), it keeps boilerplate minimal.

---

## Recommended Default Stack

For a first working version of vexy-dex, this stack covers the full pipeline with minimal dependency pain:

1. **pywebcopy** → fetch page + assets
2. **@threvo/website-understanding-sdk** → classify page type and detect sections
3. **betterhtmlchunking** → identify slide boundaries from heading hierarchy
4. **Playwright + custom JS** → viewport-aware pagination detection
5. **BeautifulSoup + lxml** → DOM normalization and reveal.js wrapping
6. **WeasyPrint** (primary) or **Playwright PDF** (fallback for JS-heavy pages) → PDF generation
7. **pypdf** → split multi-page PDF into single slides
8. **Python Fire** → CLI

---

## What to Watch

- **Fullbleed** is the most interesting project in this space. If its CSS support matures over the next 12 months, it could replace WeasyPrint + Chromium for many workflows. Rust performance with Python bindings is exactly the right architecture for a batch document pipeline.
- **Paged.js** is under active development and its CLI (`pagedjs-cli`) is the simplest path from HTML to print-quality PDF. The Paged.js team is pushing CSS Paged Media standards through the W3C — betting on Paged.js means betting on web standards.
- **LLM-based pre-importers**: The vexy-dex idea mentions LLM-based analysis. Libraries like **domdistill** (heading-aware semantic chunking) and **betterhtmlchunking** were designed for LLM pipelines. You could add an optional step where an LLM (via an API like Claude or GPT-4) reviews the detected slide boundaries and suggests adjustments — but that's an enhancement, not a foundation.

---

*Report compiled May 2026. All tools verified active as of this date. Stars and version numbers are approximate snapshots; check repositories for current status.*