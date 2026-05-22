# vexy-dex toolchain research

A pipeline that turns arbitrary HTML pages into per-slide PDFs needs six honest things: fetch, classify, normalize, paginate, render, slice. Everything else is decoration. This report maps each step to libraries that were still alive in 2026, with install commands and small code samples you can paste into a Fire CLI.

A short opinion up front: the cheapest path to a working v0 is **Playwright + BeautifulSoup + Paged.js**, with **WeasyPrint** as the no-browser fallback and **pikepdf/pypdf** for the slicer. Everything else in this report is a variant on those four legs. You already have `vexy-pdfsvgpy` to handle PDF→SVG, so the loop closes neatly.

## Step 1 — Readers (fetch HTML and assets)

You want raw HTML for static pages and a rendered DOM snapshot for JS-heavy ones. Two readers cover the field.

- httpx — modern requests replacement, sync + async, HTTP/2.
  - install: `uv add httpx[http2]`
  - link: [https://github.com/encode/httpx](https://github.com/encode/httpx)
  - sample:
    ```python
    import httpx
    html = httpx.get(url, follow_redirects=True, timeout=30).text
    ```
- Playwright (Python) — headless Chromium/Firefox/WebKit. Required for any page that hydrates client-side (Webflow Interactions, Bubble, Framer). The 2026 PDF4.dev benchmark puts warm Playwright at 3 ms simple / 13 ms complex per page — faster than Puppeteer at every data point ([PDF4.dev](https://pdf4.dev/blog/html-to-pdf-benchmark-2026)).
  - install: `uv add playwright && playwright install chromium`
  - link: [https://playwright.dev/python/](https://playwright.dev/python/)
  - sample:
    ```python
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        # capture all loaded assets via response handler if needed
        b.close()
    ```
- pywebcopy or monolith — single-file archival of a URL with all its assets inlined. monolith is a Rust CLI and is the more reliable one in 2026.
  - install: `cargo install monolith` (or `brew install monolith`)
  - link: [https://github.com/Y2Z/monolith](https://github.com/Y2Z/monolith)
  - usage: `monolith https://example.com -o snapshot.html` — bakes images, CSS, fonts into one file. Perfect input for downstream renderers.
- yt-dlp / pyrate-limiter — when assets include video, throttle politely.

## Step 2 — Pre-importers (classify + plan pagination)

This is the brain. You need three things: detect the page "kind", measure how the browser paginates the live DOM at your target viewport, and mark semantic break points.

### Classifier signals (cheap, no LLM)

Look for generator fingerprints before reaching for a model. They cover ~80% of cases.

- `meta[name=generator]` — MkDocs writes `mkdocs-material 9.x`; Hugo writes `Hugo 0.x`; Jekyll, Eleventy, Astro all follow suit.
- DOM class fingerprints:
  - Webflow → `html.w-mod-js`, `[data-wf-page]`, `[data-w-id]`
  - MkDocs Material → `body.md-body`, `nav.md-nav`, `article.md-content__inner`
  - Docusaurus → `#__docusaurus`, `.theme-doc-markdown`
  - Bubble → `#main-page` + `[data-bb-id]`
  - Webflow CMS items → `div.w-dyn-item`
- CSS file naming — `mkdocs-material-*.css`, `webflow.css`, `framer.app/styles`.

A tiny classifier:

```python
def classify(html: str) -> str:
    s = html.lower()
    if "data-wf-page" in s or "w-mod-js" in s: return "webflow"
    if "mkdocs-material" in s or "md-content" in s: return "mkdocs-material"
    if "__docusaurus" in s: return "docusaurus"
    if "framer.app" in s or "data-framer-name" in s: return "framer"
    if "data-bb-id" in s: return "bubble"
    return "generic"
```

### Visible-block measurement via Playwright

To learn how the browser already paginates a page at 1920×1080 (or any 16:9), use IntersectionObserver inside an `evaluate`. Walk the document, record the top/bottom of every `H1/H2/H3/section/article`, and bucket them by viewport-height units.

```python
js = """
() => {
  const vh = window.innerHeight;
  const nodes = document.querySelectorAll('h1,h2,h3,section,article,main > *');
  return Array.from(nodes).map(el => {
    const r = el.getBoundingClientRect();
    return {tag: el.tagName, top: r.top + window.scrollY,
            bottom: r.bottom + window.scrollY, vh,
            text: (el.innerText || '').slice(0, 80)};
  });
}
"""
blocks = page.evaluate(js)
# A "natural break" is any H1/H2 (or <section>) whose top sits within
# k * vh of the previous break, where k >= 1.
```

### Readability / content extraction

When the page is article-shaped (blog, MkDocs page), strip chrome with one of these:

- trafilatura — best precision/recall on news + docs, falls back to readability-lxml automatically ([Trafilatura docs](https://trafilatura.readthedocs.io/en/latest/evaluation.html)); commonly recommended over alternatives on HN ([HN discussion](https://news.ycombinator.com/item?id=44067933)).
  - install: `uv add trafilatura`
  - link: [https://github.com/adbar/trafilatura](https://github.com/adbar/trafilatura)
  - sample:
    ```python
    import trafilatura
    main_html = trafilatura.extract(html, output_format="html",
                                    include_images=True, include_links=True)
    ```
- readability-lxml — leaner, older, still maintained.
  - install: `uv add readability-lxml`
  - link: [https://github.com/buriy/python-readability](https://github.com/buriy/python-readability)
- resiliparse (Web Archive project) — fastest C-backed extractor when you process many URLs.
  - install: `uv add resiliparse`
  - link: [https://github.com/chatnoir-eu/chatnoir-resiliparse](https://github.com/chatnoir-eu/chatnoir-resiliparse)

### Optional LLM step

For pages that don't match any fingerprint, you can ship the cleaned text + an outline of headings to a small local model and ask for a slide plan. Keep it cheap and structured:

- llm CLI by Simon Willison — uniform API across providers, easy to wire into Fire.
  - install: `uv tool install llm`
  - link: [https://github.com/simonw/llm](https://github.com/simonw/llm)
- instructor — Pydantic-validated outputs so you get a list of slide breakpoints, not prose.
  - install: `uv add instructor`
  - link: [https://github.com/jxnl/instructor](https://github.com/jxnl/instructor)

## Step 3 — Importers (parse + apply kind-specific normalizers)

You need a fast DOM that survives ugly HTML and lets you move nodes around without losing attributes.

- BeautifulSoup 4 + lxml — the safe default, what `webflow2reveal` uses.
  - install: `uv add beautifulsoup4 lxml`
  - link: [https://www.crummy.com/software/BeautifulSoup/](https://www.crummy.com/software/BeautifulSoup/)
- selectolax — Lexbor-backed parser, ~25× faster than BS4 on large pages, CSS selectors, in active 2026 development ([selectolax](https://github.com/rushter/selectolax)).
  - install: `uv add selectolax`
  - sample:
    ```python
    from selectolax.lexbor import LexborHTMLParser
    tree = LexborHTMLParser(html)
    for h2 in tree.css("article h2"):
        h2.tag = "section"  # promote H2 to a slide boundary
    ```
- parsel — Scrapy's selector layer, useful when you want XPath + CSS in one API.
  - install: `uv add parsel`
- html5lib — only when you need bit-perfect WHATWG parsing of malformed HTML; slower.
  - install: `uv add html5lib`

A reveal.js wrap helper (the canonical normalization in your IDEA):

```python
from bs4 import BeautifulSoup
def wrap_reveal(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    body = soup.body
    sections = body.find_all("section", recursive=False) or _split_by_h2(body)
    reveal = soup.new_tag("div", **{"class": "reveal"})
    slides = soup.new_tag("div", **{"class": "slides"})
    for s in sections: slides.append(s.extract())
    reveal.append(slides)
    body.append(reveal)
    return str(soup)
```

Per-kind normalizers worth writing first:

- webflow: drop `nav, footer, [class*=banner], [class*=menu]`; promote each top-level `<section>` to a slide; copy `body` CSS variables onto the reveal wrapper so colours survive.
- mkdocs-material: keep `article.md-content__inner`, then split by `<h2>` (and `<h3>` if the H2 section is too tall); strip `.md-source-file`, `.md-content__button`.
- docusaurus: keep `.theme-doc-markdown`, then split by H2.
- generic: trafilatura-extract first, then split by H2.

## Step 4 — Pre-exporters (paged-media CSS injection)

Before handing off to an HTML→PDF engine, inject the CSS that turns "long page" into "16:9 stack". Two engines understand this CSS dialect: WeasyPrint (Python, no browser) and Chromium-via-Paged.js (browser-based polyfill).

A reusable stylesheet:

```css
@page {
  size: 1920px 1080px;   /* or 1280 720; or A4 landscape */
  margin: 0;
}
html, body { margin: 0; padding: 0; }
section, .slide {
  page-break-after: always;
  break-after: page;
  width: 1920px;
  height: 1080px;
  overflow: hidden;
  box-sizing: border-box;
}
section h2 { page-break-before: always; }
```

Paged.js gives you `@page` margin boxes, named pages, and running headers that Chromium alone does not support; DocRaptor's overview of Paged Media specs explains the gap ([DocRaptor](https://docraptor.com/css-paged-media)).

- Paged.js — polyfill used at build time, loads inside your headless browser.
  - install: `npm i pagedjs` (or use `pagedjs-cli`: `npm i -g pagedjs-cli`)
  - link: [https://pagedjs.org/](https://pagedjs.org/)
  - CLI sample: `pagedjs-cli input.html -o out.pdf --browserArgs=--allow-file-access-from-files`
- print-css.rocks — directory of paginated-media tools and personal ratings ([print-css.rocks/tools](https://print-css.rocks/tools)).

## Step 5 — Exporters (HTML → PDF engines)

Pick more than one. The IDEA explicitly wants multiple strategies per URL, and the engines disagree in instructive ways.

- Playwright `page.pdf()` — the workhorse. Chromium-quality, JS-executing, fastest in warm mode.
  - install: `uv add playwright && playwright install chromium`
  - sample:
    ```python
    page.set_content(html, wait_until="networkidle")
    page.add_style_tag(content=PAGED_CSS)
    page.pdf(path="deck.pdf", width="1920px", height="1080px",
             print_background=True, prefer_css_page_size=True)
    ```
- pagedjs-cli — runs Paged.js inside a bundled Chromium and emits a PDF with proper paged-media semantics. Best when your CSS uses `@page` margin boxes.
  - link: [https://gitlab.coko.foundation/pagedjs/pagedjs-cli](https://gitlab.coko.foundation/pagedjs/pagedjs-cli)
- WeasyPrint — pure-Python renderer, no browser. Smaller PDFs (8 KB simple vs 16 KB for Playwright) but 75× slower than warm Playwright and no JavaScript ([PDF4.dev benchmark](https://pdf4.dev/blog/html-to-pdf-benchmark-2026)). Excellent CSS Paged Media support.
  - install: `uv add weasyprint` (needs Pango on Linux; on macOS `brew install pango`)
  - link: [https://weasyprint.org/](https://weasyprint.org/)
  - sample:
    ```python
    from weasyprint import HTML, CSS
    HTML(string=html, base_url=url).write_pdf(
        "deck.pdf", stylesheets=[CSS(string=PAGED_CSS)])
    ```
- Vivliostyle CLI — Node-based EPUB/Web-to-PDF with strong Paged Media coverage and PDF bookmarks ([Vivliostyle](https://vivliostyle.org/en/)).
  - install: `npm i -g @vivliostyle/cli`
  - usage: `vivliostyle build input.html -o out.pdf --size 1920x1080`
- PrinceXML — commercial but free for non-commercial use; the reference implementation for CSS Paged Media. Worth including as an opt-in "premium" strategy when the user has a licence.
  - link: [https://www.princexml.com/](https://www.princexml.com/)
  - usage: `prince input.html -o out.pdf --page-size="1920px 1080px"`
- decktape — purpose-built PDF exporter for HTML slide frameworks (Reveal, Impress, Bespoke, etc.). Uses Puppeteer under the hood ([decktape](https://github.com/astefanutti/decktape)).
  - install: `npm i -g decktape`
  - usage: `decktape reveal http://localhost:8000 deck.pdf --size 1920x1080`
- Typst (via `pandoc -t typst`) — outlier strategy, useful for doc-heavy MkDocs pages where you want typographic control rather than fidelity. Pandoc-Typst-pipeline produces clean print PDFs ([HN](https://news.ycombinator.com/item?id=45404760)). Typst's own HTML export is improving in 2026 ([Typst HTML docs](https://typst.app/docs/reference/html/)).
  - install: `brew install typst pandoc`

Cross-language exporters worth knowing about:

- chromedp (Go) — drives Chromium from Go, has `page.PrintToPDF` and is the standard pick for Go services ([chromedp](https://github.com/chromedp/chromedp)).
- headless_chrome / chromiumoxide (Rust) — Rust DevTools-Protocol clients; `chromiumoxide` is the more actively maintained option in 2026 ([chromiumoxide](https://github.com/mattsse/chromiumoxide)).
- wkhtmltopdf — deprecated in 2023, do not adopt.

## Step 6 — Writers (slice the PDF, emit SVGs, build a Reveal preview)

You already control PDF↔SVG via `vexy-pdfsvgpy`. For the slicing layer, two libraries do the job without binaries.

- pypdf — pure-Python, zero deps, the recommended successor to PyPDF2 ([Stack Overflow](https://stackoverflow.com/questions/490195/split-a-multi-page-pdf-file-into-multiple-pdf-files-with-python)).
  - install: `uv add pypdf`
  - sample:
    ```python
    from pypdf import PdfReader, PdfWriter
    reader = PdfReader("deck.pdf")
    for i, page in enumerate(reader.pages, 1):
        w = PdfWriter(); w.add_page(page)
        w.write(f"slide_{i:02d}.pdf")
    ```
- pikepdf — qpdf-backed, lossless, preserves form XObjects and OCGs. Use when you need to keep Reveal-style backgrounds intact.
  - install: `uv add pikepdf`
  - link: [https://github.com/pikepdf/pikepdf](https://github.com/pikepdf/pikepdf)
- PyMuPDF (fitz) — already a dep of vexy-pdfsvgpy; can also slice. Keep one PDF library if you can.
- pdfcpu — Go CLI/library, handy for shell pipelines and batch ops ([pdfcpu](https://github.com/pdfcpu/pdfcpu)).
  - install: `brew install pdfcpu`
  - usage: `pdfcpu split deck.pdf out/`

A "reveal preview" writer (each input slide becomes a `<section>` containing the page's SVG):

```python
def build_reveal_preview(svg_paths: list[str], out: str) -> None:
    sections = "\n".join(
        f'<section><img src="{p}" style="width:100%;height:100%;object-fit:contain"></section>'
        for p in svg_paths)
    html = f"""<!doctype html><html><head>
<link rel=stylesheet href=https://cdn.jsdelivr.net/npm/reveal.js/dist/reveal.css>
<style>.reveal section{{padding:0}}</style></head><body>
<div class=reveal><div class=slides>{sections}</div></div>
<script src=https://cdn.jsdelivr.net/npm/reveal.js/dist/reveal.js></script>
<script>Reveal.initialize({{width:1920,height:1080,margin:0}})</script>
</body></html>"""
    open(out, "w").write(html)
```

## Slide framework strategies you can ship

PkgPulse's 2026 roundup is a fair summary: Slidev for code-first talks, Marp for portable Markdown decks, Reveal.js for custom HTML decks ([PkgPulse](https://www.pkgpulse.com/guides/slidev-vs-marp-vs-revealjs-code-first-presentations-2026)).

- Reveal.js — the natural target for `webflow2reveal`-style normalization. Built-in PDF export via `?print-pdf` + browser print ([reveal.js PDF export](https://revealjs.com/pdf-export/)).
  - install: `npm i reveal.js`
- Marp CLI — Markdown → PDF/PPTX in one shot. Useful as the "text-heavy" strategy: dump trafilatura-extracted Markdown into Marp and let it auto-paginate.
  - install: `npm i -g @marp-team/marp-cli`
  - usage: `marp deck.md --pdf --allow-local-files`
- Slidev — Vue + Vite based; nice for technical pages but overkill as an automatic target.
  - install: `npm i -g @slidev/cli`

## Project skeleton

A `pyproject.toml` that wires the recommended stack:

```toml
[project]
name = "vexy-dex"
requires-python = ">=3.12"
dependencies = [
  "httpx[http2]>=0.27",
  "playwright>=1.48",
  "beautifulsoup4>=4.12",
  "lxml>=5.2",
  "selectolax>=0.3.21",
  "trafilatura>=1.12",
  "weasyprint>=63",
  "pypdf>=5.0",
  "pikepdf>=9.4",
  "vexy-pdfsvgpy",
  "fire>=0.6",
  "loguru>=0.7",
  "rich>=13.7",
]

[project.scripts]
vexy-dex = "vexy_dex.__main__:main"
```

CLI shape (Fire):

```python
import fire
class VexyDex:
    def all(self, url: str, out: str = "out", viewport: str = "1920x1080",
            strategies: str = "playwright,weasyprint,paged,marp"):
        for s in strategies.split(","):
            self.run(url, out=f"{out}/{s}", strategy=s, viewport=viewport)
    def run(self, url, out, strategy, viewport): ...
def main(): fire.Fire(VexyDex)
```

## Recommended minimum viable pipeline

1. **Read** with `httpx` (static) or `playwright` (dynamic), fall back to `monolith` for archival.
2. **Classify** by generator/fingerprint; mark "article-shape" pages for trafilatura.
3. **Measure** natural breakpoints via Playwright `evaluate` returning `getBoundingClientRect` for headings/sections.
4. **Normalize** with BeautifulSoup (or selectolax when speed matters): wrap into `.reveal > .slides > section`, drop chrome.
5. **Inject** the paged-media CSS, fixed to your target ratio.
6. **Render** in parallel with three strategies — Playwright `page.pdf()`, Paged.js CLI, WeasyPrint — and a fourth Marp pipeline that consumes a trafilatura-extracted Markdown stub.
7. **Slice** each PDF into per-page files with pypdf, then convert to SVG with `vexy-pdfsvgpy`.
8. **Write** a Reveal preview that lets the user pick slides across strategies.

## What to leave on the floor

- wkhtmltopdf — abandoned, breaks on modern CSS.
- pyppeteer — deprecated; the active community moved to Playwright Python.
- PhantomJS-based decktape forks — only when the modern Puppeteer build fails.
- cairosvg / svglib — your `vexy-pdfsvgpy` rejects-list already covers this; keep it consistent.

That is the whole machine. Six steps, four engines, one slicer. Resist adding a fifth engine until two of the four have failed you twice.
