**Turning messy HTML pages into flexible slide decks isn't rocket science — it's a six-stage pipeline with the right open-source tools doing the heavy lifting in 2026.**

vexy-dex ingests any URL or file, spots patterns (Webflow hero sections, MkDocs article flows, plain static sites), normalizes the DOM for slide-friendly structure, then spits out multiple strategy folders. Each folder holds single-page 16:9 PDFs (or SVGs) so you cherry-pick the best slides later. Everything stays offline, Python-first, Fire CLI friendly.

Here are the actively maintained libraries that actually deliver in 2026 — no abandoned wkhtmltopdf ghosts, no hype. Favor these for each step.

### Readers & Pre-Importers: Fetch, Render, Decide Breaks
These grab raw HTML + assets and figure out smart pagination before any exporter runs.

**Playwright (Python primary, also JS/TS/Java/.NET)**  
- **Fits**: Readers (full rendered fetch), Pre-importers (viewport simulation at exact slide size, visibility + bounding-box checks for natural page breaks before `<h2>`, `<section>`, or `<article>`).  
- **Why it wins**: Real browser engine sees exactly what users see. Set 1920×1080 (or custom 16:9), query element positions, count "screens" to next semantic break. Handles Webflow JS, MkDocs dynamic bits, or React monsters without guesswork.  
- **Active 2026**: Core Microsoft project, frequent releases, rock-solid.  
- **Install**:
  ```bash
  pip install playwright
  playwright install chromium   # ~150-300 MB one-time; use firefox if you prefer
  ```
- **Code sample** (pre-importer: probe pagination at slide viewport):
  ```python
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
      browser = p.chromium.launch()
      page = browser.new_page()
      page.set_viewport_size({"width": 1920, "height": 1080})
      page.goto("https://www.vexy.art/lines/")  # or local file
      # Find semantic breaks + their screen positions
      breaks = page.evaluate("""() => {
        const candidates = document.querySelectorAll('h1, h2, section, article, .hero, [class*="section"]');
        return Array.from(candidates).map(el => {
          const r = el.getBoundingClientRect();
          return {tag: el.tagName, text: el.innerText.slice(0,60), top: Math.round(r.top), visible: r.top >= 0 && r.top < 1080};
        }).filter(b => b.visible || b.top > 0);
      }""")
      print(breaks)  # decide page breaks here
      page.pdf(path="raw.pdf", width="1920px", height="1080px", landscape=True)
  ```
  Link: https://playwright.dev/python/

**Trafilatura (Python)**  
- **Fits**: Pre-importers (strip nav/footers, extract clean main content + metadata + structure for text-heavy strategies).  
- **Why**: Better than readability-lxml for modern sites; keeps headings, lists, code blocks intact. Perfect "is this a blog post or a marketing page?" classifier.  
- **Active 2026**: Yes, actively developed for production scraping.  
- **Install**: `pip install trafilatura`  
- **Code sample**:
  ```python
  import trafilatura
  html = open("page.html").read()
  text = trafilatura.extract(html, include_comments=False, include_tables=True)
  metadata = trafilatura.metadata.extract(html)
  print(metadata.title, metadata.author)
  ```
  Link: https://trafilatura.readthedocs.io/

**BeautifulSoup4 + lxml (Python)**  
- **Fits**: Readers (parse) + Importers (normalize).  
- **Why**: Dead-simple DOM surgery — wrap `<section>`s, move hero to first slide, add `data-slide` attrs.  
- **Install**: `pip install beautifulsoup4 lxml`  
- **Code sample** (basic normalization for reveal.js wrapper):
  ```python
  from bs4 import BeautifulSoup
  soup = BeautifulSoup(open("page.html"), "lxml")
  # Example: wrap top-level sections
  for sec in soup.select("main > section, article > section"):
      wrapper = soup.new_tag("div", **{"class": "slide"})
      sec.wrap(wrapper)
  # Add reveal skeleton if needed
  reveal = soup.new_tag("div", **{"class": "reveal"})
  slides = soup.new_tag("div", **{"class": "slides"})
  # ... append logic ...
  open("normalized.html", "w").write(str(soup))
  ```
  Link: https://www.crummy.com/software/BeautifulSoup/

### Importers & Normalizers: Kind-Specific Tweaks
No universal magic — detect Webflow (`w-` classes, CMS items), MkDocs (`.md-content`, code fences), or generic.

**Custom + BeautifulSoup / Cheerio (JS)**  
- Use the private webflow2reveal patterns (or public cousin https://github.com/loomchild/webflow-revealjs) to turn Webflow hero + CMS collections into slides.  
- For MkDocs: preserve syntax-highlighted blocks, turn nav into title slide.  
- Rule: before every `<h2>` or new `<section>`, force a slide break via injected CSS `page-break-before: always` or DOM split.  
- One normalization script serves all exporters.

### Pre-Exporters & Exporters: Multiple Strategies, One Command
Produce 3–5 variants per input. User picks winners.

**WeasyPrint (Python)**  
- **Fits**: Exporter (pure HTML/CSS → PDF with excellent paged media).  
- **Why**: No browser bloat. Add `@page { size: 16in 9in landscape; }` + `page-break-before` rules. Great for clean static pages or MkDocs. Smaller PDFs than browser routes.  
- **Active 2026**: Production/stable, frequent releases (v68+).  
- **Install**:
  ```bash
  pip install weasyprint
  # Linux: sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 shared-mime-info
  # macOS/Windows: see https://doc.courtbouillon.org/weasyprint/stable/install.html
  ```
- **Code sample**:
  ```python
  from weasyprint import HTML, CSS
  HTML("normalized.html").write_pdf(
      "weasy-strategy/slide.pdf",
      stylesheets=[CSS(string="@page { size: 1920px 1080px; margin: 0; }")]
  )
  ```
  Link: https://weasyprint.org/

**DeckTape (Node.js)**  
- **Fits**: Exporter (presentation frameworks → PDF).  
- **Why**: Native reveal.js / remark / shower support. Turns normalized reveal.js HTML into crisp slide PDFs. `--screenshots` mode gives per-slide images if you want SVGs later.  
- **Active 2026**: v3.16.1 (April 2026), actively maintained.  
- **Install**:
  ```bash
  npm install -g decktape
  # or docker: docker run --rm -v $(pwd):/slides ghcr.io/astefanutti/decktape
  ```
- **Code sample**:
  ```bash
  decktape reveal normalized-reveal.html strategy-deck/slides.pdf --slides 1-20
  # or for screenshots (then convert to SVG if needed)
  decktape reveal normalized-reveal.html --screenshots --screenshots-format png
  ```
  Link: https://github.com/astefanutti/decktape

**Vivliostyle CLI (Node.js)**  
- **Fits**: Exporter (advanced CSS paged media → print-ready PDF).  
- **Why**: Browser-based but CLI-first; handles complex `@page` margin boxes, running headers, better than WeasyPrint on some CSS3 print features.  
- **Active 2026**: Yes (v10+ recent).  
- **Install**: `npm install -g @vivliostyle/cli`  
- **Usage**: `vivliostyle build normalized.html -o vivliostyle-strategy/output.pdf --press-ready`  
  Link: https://vivliostyle.org/ + https://github.com/vivliostyle/vivliostyle-cli

**Playwright (again)**  
- Use for JS-heavy Webflow pages where WeasyPrint chokes. Same viewport + `page.pdf()` call.

### Writers: One Slide, One PDF, Named Nicely
**pypdf (Python)**  
- **Fits**: Writers (split multi-page exporter output into single-page files).  
- **Active 2026**: Yes, py-pdf/pypdf fork, pure Python, no deps.  
- **Install**: `pip install pypdf`  
- **Code sample** (split + rename):
  ```python
  from pypdf import PdfReader, PdfWriter
  import os
  reader = PdfReader("multi-strategy.pdf")
  os.makedirs("strategy-a", exist_ok=True)
  for i, page in enumerate(reader.pages):
      writer = PdfWriter()
      writer.add_page(page)
      writer.write(f"strategy-a/{i:02d}-slide.pdf")
  ```
  Link: https://github.com/py-pdf/pypdf

For SVGs: Full HTML→vector SVG is still painful (old CutyCapt/WebVector unmaintained). Use Playwright `page.screenshot(type="png", scale=2)` + optional cairosvg for simple cases, or skip to high-res PNGs. Reveal.js + embedded SVG backgrounds works for one output variant.

### Quick Strategy Recipe (Python sketch)
```python
# 1. Read + normalize (BeautifulSoup + trafilatura)
# 2. For each strategy:
if strategy == "weasy":
    inject_paged_css(normalized)
    WeasyPrint(...).write_pdf(...)
elif strategy == "reveal":
    wrap_for_reveal(normalized)
    # save index.html + run decktape
elif strategy == "vivliostyle":
    vivliostyle build ...
# 3. Writer: split every multi-page PDF into per-slide files
# 4. Output: vexy-dex/output/<url-slug>/<strategy>/01-hero.pdf ...
```

### Gotchas & UX Wins
- WeasyPrint needs system libs — error messages are clear; follow the install docs.  
- Playwright binary is big but worth it; cache it in CI.  
- Always test at exact 16:9 viewport — that's where "stupid pagination" dies.  
- For offline: download assets with `httpx` + rewrite `src`/`href` before any exporter.  
- Fire CLI: use `typer` or `fire` to expose `vexy-dex convert URL --strategies all --viewport 1920x1080`.

These tools are boringly reliable in 2026. Stack Playwright for analysis + WeasyPrint/DeckTape/Vivliostyle for output and you cover 95 % of real pages without writing your own renderer. Start with the pre-importer probe above — it will immediately show you why smart breaks beat naive "one section = one slide."

Build the pipeline. The slides will follow.