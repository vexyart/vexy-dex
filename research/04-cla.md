# vexy-dex: Toolchain Research Report

**TL;DR**
- For a Python-orchestrated pipeline that turns arbitrary HTML into 16:9 single-page PDFs and SVGs, the strongest stack is **Playwright (Python) for fetching and PDF export**, **selectolax + trafilatura for parsing and content extraction**, **PyMuPDF for split/extract**, **pdftocairo for PDF→SVG**, and **decktape** as the second-path renderer when the input is already a slide framework.
- For LLM-assisted page analysis, run **MiniCPM-V 4.6 GGUF via llama.cpp** locally (≈2 GB RAM, Apache 2.0); use Ollama for one-line serving and llama-cpp-python for in-process embedding.
- For CMS fingerprinting, skip the stale python-Wappalyzer and write a small rules engine inspired by **twardoch/webflow2reveal**'s class-map approach (`w-*`, `data-w-id`, `md-*`, `md-typeset`) — that repo already encodes the Webflow→reveal.js normalization patterns vexy-dex needs in step 3.

## Key Findings

- **Two-engine PDF strategy.** Headless Chromium (Playwright) handles JS-rendered marketing sites and slide frameworks; a Paged-Media engine (WeasyPrint or vivliostyle-cli) handles documentation-style HTML where CSS Paged Media controls pagination semantics. Run both in parallel; let the user pick.
- **The reveal.js path is essentially solved.** `webflow2reveal` already demonstrates the transform: wrap `<section>` elements, classify backgrounds, inject `Reveal.js 5.1` at a 1440×900 stage. Decktape then converts the deck to per-slide PDF. Adopt this pattern rather than reinvent it.
- **Maintenance casualties to avoid.** `pagedjs-cli` (npm) is flagged Inactive — last npm version >12 months old, though the repo had a Jan 2026 commit. `pyppeteer` is abandoned. `wkhtmltopdf` is upstream-deprecated. `python-Wappalyzer` last shipped 0.3.1; the active fork is the `wappalyzer-next` Python port.
- **MiniCPM-V 4.6** (released 11 May 2026, Apache 2.0) hits the sweet spot for local vision-language analysis: 1.3 B parameters, ~2 GB GGUF, 262 k context, llama.cpp support since b9049, OCR strong enough for layout reasoning on rendered screenshots.
- **PDF→SVG.** Use `pdftocairo -svg` from poppler-utils for vector-faithful, one-page-at-a-time output; fall back to `mutool convert` from MuPDF when poppler chokes on LaTeX-style PDFs. Inkscape CLI is editable but slow and breaks ligatures.

## Details

### 1. READERS — fetching HTML and assets

Pick one async HTTP client and one headless browser. Don't mix three.

**Primary recommendation**
- **Playwright (Python)** — https://playwright.dev/python
  - License: Apache 2.0. Maintained by Microsoft, weekly releases.
  - `pip install playwright && playwright install chromium`
  - Hits every requirement: viewport sizing, `page.pdf()`, `page.emulate_media('print')`, screenshot at exact stage size, JS evaluation for visibility checks. Note: `page.pdf()` only works in Chromium headless; Firefox/WebKit raise an error.
  - Minimal sample:
    ```python
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        page.goto(url)
        page.emulate_media(media="screen")
        page.pdf(path="slide.pdf", width="1920px", height="1080px",
                 print_background=True, prefer_css_page_size=True)
    ```
- **httpx** — https://github.com/encode/httpx
  - License: BSD-3. For non-JS fetches and asset downloads.
  - `pip install httpx[http2]`
  - HTTP/2 support, sync and async in one client. Per Decodo's 2026 HTTPX vs Requests vs AIOHTTP comparison, "aiohttp frequently wins by 1.5–5× throughput and lower tail latency in community benchmarks" at very high concurrency, but it is async-only and lacks HTTP/2; vexy-dex's load profile doesn't justify the trade.

**Alternatives worth knowing**
- **monolith** (Rust, public-domain CC0) — https://github.com/Y2Z/monolith — `cargo install monolith` or `brew install monolith`. Inlines every asset as data URI. Useful as a "freeze the page" pre-importer; pipe Chromium-rendered DOM through it: `chromium --headless --dump-dom URL | monolith - -I -b URL -o frozen.html`. Last release v2.10.x, actively maintained on master.
- **Scrapy** — overkill for a single-page tool; only worth it if vexy-dex grows a crawler.
- **trafilatura's `fetch_url`** — convenient if you also want politeness/sitemaps; otherwise httpx is plenty.

### 2. PRE-IMPORTERS — classification, semantic analysis, LLM

This is the brain. Two sub-tracks: deterministic (fingerprints + DOM heuristics) and probabilistic (vision LM on a screenshot).

**HTML parsing — speed-tier choice**
- **selectolax** — https://github.com/rushter/selectolax — `pip install selectolax`. MIT. Cython binding to the lexbor C parser. The rushter/selectolax README benchmark table (examples/benchmark.py) puts selectolax (Modest) at ~2 s vs lxml 14.48 s vs Beautiful Soup (html.parser) 59.64 s on the author's 754-domain corpus. Use `LexborHTMLParser` — the lexbor backend is the maintained one as of 2024; Modest is legacy.
  ```python
  from selectolax.lexbor import LexborHTMLParser
  tree = LexborHTMLParser(html)
  sections = tree.css("section, article, main")
  ```
- **lxml** as fallback for XPath needs.
- **BeautifulSoup** only if a human will edit the parsing code.

**Content extraction**
- **trafilatura** — https://github.com/adbar/trafilatura — `pip install trafilatura`. Apache 2.0. Active, v2.x as of late 2024. Best mean F1 (0.883) across eight evaluation datasets per Bevendorff, J., Gupta, S., Kiesel, J., & Stein, B. (2023). "An Empirical Comparison of Web Content Extraction Algorithms." Proceedings of the 46th International ACM SIGIR Conference, Taipei, Taiwan, ACM, pp. 2594–2603 (Table 3: "Trafilatura · 0.913 · 0.895 · 0.883"). It is also the only mainstream tool that emits Markdown, XML-TEI, and structured JSON in one call. Use `extract(html, output_format="xml", include_links=True, include_images=True)` to keep the structure vexy-dex needs.

**CMS / builder fingerprinting**
- Wappalyzer's official extension was discontinued (the open data still lives at `tomnomnom/wappalyzer` and `enthec/webappanalyzer`); `python-Wappalyzer` (chorsley) hasn't seen a real release since 0.3.1 in 2020. Don't rely on it as a runtime detector.
- Instead, write a 200-line rules engine. The fingerprints are short and stable:
  - **Webflow**: `class*="w-"`, `data-w-id` attribute, `<html data-wf-domain>`, `webflow.js` script src, `.w-container`, `.w-layout-grid`, `.w-nav`. Webflow's component classes are documented across help.webflow.com and the Webflow Designer Flowkit docs.
  - **MkDocs Material**: `<body class="md-grid">`, `md-content`, `md-typeset`, `md-nav`, `data-md-component` attribute, `<meta name="generator" content="mkdocs-1.x, mkdocs-material-9.x">`.
  - **Hugo / Jekyll / Astro / Next.js**: meta generator tag is reliable; Next.js leaks `__NEXT_DATA__`, Astro leaks `astro-` attributes, Gatsby leaks `gatsby-` ids.
  - **Bubble**: `bubble-r-line`, `bubble-element` classes.
  - **Shuffle / Wix / Squarespace / WordPress**: generator tag + characteristic script paths.

**Headless layout analysis (the "is this element on the 1920×1080 stage?" check)**
- Inject a small script via `page.evaluate`:
  ```python
  rects = page.evaluate("""
    () => Array.from(document.querySelectorAll('section, article, h1, h2, h3, img'))
      .map(el => {
        const r = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return {tag: el.tagName, top: r.top, height: r.height,
                visible: cs.display !== 'none' && r.height > 0};
      })
  """)
  ```
- For natural pagination break points, walk the DOM at viewport stride, scoring breaks at `<section>`, `<article>`, `<hr>`, and at headings whose top-edge crosses a multiple of the stage height.

**LLM-based page analyzer (vision)**

Primary: **MiniCPM-V 4.6 GGUF via llama.cpp**.
- Hugging Face: https://huggingface.co/openbmb/MiniCPM-V-4.6-gguf
- License: Apache 2.0. 1.3 B params, SigLIP2-400M + Qwen3.5-0.8B.
- llama.cpp PR #22529 merged; need build ≥ b9049.
- Inference CLI:
  ```bash
  ./llama-mtmd-cli \
    -m MiniCPM-V-4.6-Q4_K_M.gguf \
    --mmproj mmproj-MiniCPM-V-4.6-F16.gguf \
    -c 8192 --reasoning off --image slide.png \
    -p "Describe the slide layout: title, body, image positions."
  ```
- Or via Ollama: `ollama pull openbmb/minicpm-v4.6` then OpenAI-compatible HTTP. Easiest for vexy-dex to embed.
- Python: `llama-cpp-python` (`pip install llama-cpp-python[server]`) gives an in-process binding plus an OpenAI-compatible server.

Alternatives:
- **Qwen2.5-VL-7B** (Apache 2.0) — heavier, better at small text/charts; use when accuracy beats cost.
- **Florence-2** (MIT) — 230 M / 770 M, excellent for OCR + region grounding via single-token task tags (`<CAPTION>`, `<OD>`, `<OCR>`). Underrated for "find headings on this screenshot."
- **Moondream2** — tiny, good for quick captioning.
- **Surya** (`datalab-to/surya`) — purpose-built doc layout/reading-order model, GPL-3.0 (commercial self-host needs a license). Use for the "where does this page naturally break?" question when the input has been rasterized.

### 3. IMPORTERS — normalizing for known CMSes

For each detected builder, a normalizer should output a canonical structure: `<div class="reveal"><div class="slides"><section>…</section>…</div></div>` plus a `slide-*` vocabulary the exporter understands.

**The webflow2reveal pattern (lifted whole)**
- Repo: https://github.com/twardoch/webflow2reveal (public; Apache-2.0 in sidebar, MIT in README footer — clarify before reuse). Ships as `webflow2reveal` (PyPI, Python) and `webflow2revealjs` (npm). The README documents a five-step transform that vexy-dex's Webflow importer should copy verbatim:
  1. *Resolve colours* — scan inline and linked stylesheets into a `class → background-colour` map.
  2. *Select slides* — every `<section>` becomes a slide unless its classes or id mark it as nav, footer, menu, header, or banner.
  3. *Normalize the DOM* — rewrite each slide into a small layout vocabulary: `slide-split-layout`, `slide-column`, `slide-text-container`, `slide-image-cover`, `slide-badge`.
  4. *Classify backgrounds* — set `data-background-color` and tag each slide `slide-light-bg` / `slide-dark-bg` by perceptual luminance.
  5. *Inject Reveal.js 5.1* plus a bundled stylesheet that sizes everything to a 1440×900 stage and hides Webflow chrome.
- Reveal 5.1 lives at https://revealjs.com (MIT). The official stage size is configurable via `Reveal.initialize({ width, height })`.

**MkDocs Material normalizer**
- Stage: the `<article class="md-content__inner md-typeset">` is the slide source. Each `<h1>` or `<h2>` starts a new slide; everything until the next heading of the same level is its body.
- Drop `md-sidebar`, `md-header`, `md-footer`, `md-search`, `md-nav` wholesale.
- Material for MkDocs README confirms the DOM uses `md-` prefixed classes throughout and a `partials/` template tree, so the selectors are stable across themes. As of 2026 the project is in maintenance mode (the team is building "Zensical" as a successor); the DOM is unlikely to churn.

**Other builders** — Bubble emits container divs (`bubble-r-container`) you can flatten by depth; Shuffle/Wix/Squarespace need ad-hoc rules; for static-site generators (Hugo, Jekyll, Astro, Next.js, Gatsby), trust the semantic HTML and use the generic importer.

### 4 + 5. PRE-EXPORTERS + EXPORTERS — HTML → PDF

Run two engines in parallel and offer both. They produce different but defensible results.

**Engine A: Headless Chromium via Playwright (PRIMARY for marketing/JS sites)**
- Already in the dependency tree from step 1; no extra cost.
- Set `width="1920px" height="1080px" prefer_css_page_size=True` to lock the 16:9 stage.
- Inject `@page { size: 1920px 1080px; margin: 0; }` and `html, body { width: 1920px; height: 1080px; }` via `page.add_style_tag` to defeat scaling.
- Output: one PDF per page, no pagination tricks needed.
- Strength: JS, fonts, exact pixel parity with browser. Weakness: no proper CSS Paged Media (no `@page :left`, no running headers, no orphan/widow control).

**Engine B: vivliostyle-cli (PRIMARY for documentation/article HTML)**
- https://github.com/vivliostyle/vivliostyle-cli — AGPL-3.0, TypeScript, actively maintained (commits within the last week as of May 2026).
- `npm install -g @vivliostyle/cli` (Node ≥16).
- `vivliostyle build slide.html -s 1920mm,1080mm -o slide.pdf` — accepts custom sizes, supports full CSS Paged Media via the Vivliostyle JS engine.
- Best for content that already uses `@page`, `break-before`, `string-set`, page counters.

**Engine C: WeasyPrint (Python-native fallback)**
- https://weasyprint.org — BSD-3, Python, very active (v68.1 Jan 2026, regular security and feature releases).
- `pip install weasyprint`
- Pure-Python engine, no Chromium dependency. No JS execution — that's the cost and the point. For pre-rendered, declarative HTML it's hard to beat.
- ```python
  from weasyprint import HTML, CSS
  HTML(string=html).write_pdf("slide.pdf",
      stylesheets=[CSS(string="@page { size: 1920px 1080px; margin: 0 }")])
  ```

**Engine D: PrinceXML** (paid for commercial; free non-commercial)
- https://www.princexml.com — version 16.2 as of mid-2025, with continuous improvements through 2026 per the public roadmap.
- The reference implementation for CSS Paged Media; supports JavaScript, SVG foreignObject, CSS cascade layers, advanced OpenType. If output fidelity matters above all and budget allows, Prince is the gold standard. Otherwise skip.

**Engine E: PagedJS** — note but **don't ship**
- pagedjs-cli is flagged Inactive by Snyk (no npm release in >12 months as of mid-2024; v0.5.0-beta.1 is the most recent on the `next` tag). The pagedjs org had commits as recently as Jan 2026 on pagedjs-cli, so it isn't dead, but the cadence is too slow to depend on. Print-css.rocks dropped it from their test suite in 2023 citing inactivity. Use Vivliostyle instead.

**Decktape — for the reveal.js path specifically**
- https://github.com/astefanutti/decktape — MIT, v3.16.1 released May 2026 (latest on npm as of the report date, "last published: 16 days ago"), ~2.4 k GitHub stars.
- Built on Puppeteer; bundles a headless Chrome. Knows reveal.js, Slidev, impress.js, Bespoke, deck.js, DZSlides, Flowtime, Inspire, NueDeck, remark, RISE, Shower, Slidy, WebSlides, plus a `generic` fallback driven by key emulation.
- CLI: `npx decktape reveal --size 1920x1080 --slides 1-50 input.html output.pdf`. Use `--fragments` to emit one PDF page per Reveal fragment.
- Why include it: once the importer has produced a Reveal.js HTML, decktape captures each slide as a separate canvas frame — that's the cleanest path to per-slide PDFs without scaling artefacts.

### 6. WRITERS — split, name, convert to SVG

**Split into one-PDF-per-page**
- **PyMuPDF (fitz)** — https://pymupdf.readthedocs.io — AGPL or commercial. The fastest pure-PDF operation in Python. Per pypdf maintainer Martin Thoma (Medium, March 2024), pypdf's "text extraction speed is roughly 10x — 20x slower than the one of pypdfium2/tika/PyMuPDF"; the same ratio holds for copy/merge operations on the Artifex methodology benchmark.
  ```python
  import pymupdf
  src = pymupdf.open("deck.pdf")
  for i, page in enumerate(src):
      out = pymupdf.open()
      out.insert_pdf(src, from_page=i, to_page=i)
      out.save(f"{slug}-{i+1:03d}.pdf")
  ```
- **pikepdf** (qpdf-backed, MPL-2.0) — better when you need to preserve structure or repair damage; slower but rock-solid. License is the friendly choice if you publish under permissive terms.
- **pypdf** (BSD) — pure Python, no native dep; slow but easy to vendor.

**PDF → SVG**
- **pdftocairo** (from `poppler-utils`, GPL-2.0). Mature, available everywhere.
  - `pdftocairo -svg -f 1 -l 1 slide.pdf slide-001.svg`
  - Per the pdf2svg author's own note, "the maintainers of Poppler have written a utility that works on the same principle: pdftocairo. I recommend that you use their utility since it is better maintained." Best vector fidelity for browser-generated PDFs.
- **mutool convert** (MuPDF, AGPL). Use as a fallback when poppler outputs a blank page (a known issue with LaTeX-sourced PDFs).
- **vexy-pdfsvgpy** — https://github.com/vexyart/vexy-pdfsvgpy — wrap whichever native tool is installed; expose a single `pdf_to_svg(path, page)` API and let the user pin the engine.
- **Inkscape CLI** — `inkscape --export-type=svg input.pdf` produces editable text nodes but breaks ligatures; use only when human editing is the goal.

**Emit reveal.js HTML with embedded SVGs**
- Trivial template: one `<section><img src="data:image/svg+xml;base64,…"></section>` per slide, inside the standard `<div class="reveal"><div class="slides">…</div></div>` chassis. Reveal handles the rest. Use `Reveal.initialize({ width: 1920, height: 1080, embedded: false, controls: true })` to match the stage.

### Cross-cutting concerns

**CLI framework**
- The task specifies **Fire** — https://github.com/google/python-fire — Apache 2.0, `pip install fire`. Last release v0.7.1 on 16 Aug 2025, ~28 k stars, still maintained.
- Idiom: turn any class into a CLI by `fire.Fire(MyClass)`; methods become subcommands, type hints become flags.
  ```python
  import fire
  class VexyDex:
      def build(self, url: str, output: str = "out/", size: str = "1920x1080"):
          ...
      def split(self, pdf: str, out_dir: str = "."):
          ...
  if __name__ == "__main__":
      fire.Fire(VexyDex)
  ```
- Caveats: flags after positional args need an isolated `--` separator (a Fire convention that catches every newcomer); no static completion (Click and Typer win there). For a hacker tool with a stable user (you), Fire's zero-friction class-to-CLI mapping is the right call.

**Plugin architecture for IMPORTERS/EXPORTERS**
- Use Python's `importlib.metadata` entry points. Declare in `pyproject.toml`:
  ```toml
  [project.entry-points."vexy_dex.importers"]
  webflow = "vexy_dex.importers.webflow:WebflowImporter"
  mkdocs  = "vexy_dex.importers.mkdocs:MkdocsImporter"

  [project.entry-points."vexy_dex.exporters"]
  playwright  = "vexy_dex.exporters.playwright:PlaywrightExporter"
  vivliostyle = "vexy_dex.exporters.vivliostyle:VivliostyleExporter"
  weasyprint  = "vexy_dex.exporters.weasyprint:WeasyPrintExporter"
  ```
- Discover at startup with `importlib.metadata.entry_points(group="vexy_dex.exporters")`. Each strategy implements a tiny ABC (`detect(html) -> float`, `transform(html) -> html`, `export(html, opts) -> Path`).

**Async pipeline**
- The pipeline is naturally a fan-out: one input → N importers → N×M exporters → N×M writers. Use **anyio** over raw asyncio so the same code runs under trio if needed. Cap concurrency on the Chromium pool (browsers are heavy); use `asyncio.Semaphore` or `anyio.CapacityLimiter`.

## Recommendations

**Stage 1 — Minimum viable pipeline (week 1)**
- Stack: Playwright + selectolax + Fire + PyMuPDF + pdftocairo.
- Single command: `vexy-dex build URL --size 1920x1080`.
- One importer (`generic` — wrap entire body in a single `<section>`) and one exporter (Playwright `page.pdf`).
- Benchmark: ≥1 deck/second on a laptop for static pages.

**Stage 2 — CMS-aware (week 2-3)**
- Add the Webflow importer (port webflow2reveal's five-step transform).
- Add the MkDocs Material importer (`md-content__inner` traversal).
- Add the Vivliostyle exporter for documentation-style inputs.
- Add the decktape exporter for reveal.js inputs.
- Benchmark threshold: faithful render of https://www.fontlab.com/ and https://blog.fontlab.com/.

**Stage 3 — LLM-assisted (week 4+)**
- Add MiniCPM-V 4.6 via Ollama as an optional pre-importer. Cache results keyed by URL+screenshot hash.
- Use it to: (a) score pagination breaks the heuristic missed, (b) generate alt text for the SVG embeds, (c) verify slide titles match h1/h2 detection.
- Switch to Qwen2.5-VL-7B if MiniCPM hallucinates titles more than ~5 % of the time on your test corpus.

**When to change course**
- If Chromium PDF output shows font kerning drift compared to the live page → add the Prince exporter (paid) or switch to the Vivliostyle path with embedded webfonts.
- If trafilatura misses the article body on test sites → add the Mozilla Readability JS port (`readabilipy`) as a second extractor and vote.
- If decktape's Puppeteer bundle starts to lag Chromium versions → patch its `--chrome-path` to point at Playwright's downloaded Chromium and skip the second install.

## Caveats

- **License conflict on webflow2reveal.** The repo sidebar shows Apache-2.0; the README footer says "MIT © Adam Twardoch." Resolve with the author before vendoring code.
- **PyMuPDF is AGPL** in the open-source channel. If vexy-dex itself ships under a permissive license, prefer **pikepdf** (MPL-2.0) for the split step and accept the speed hit, or buy a commercial PyMuPDF license.
- **Surya** changed license to GPL-3.0 and now requires a commercial license for self-hosted production use per the datalab-to/surya README. Treat as research-only unless you license it.
- **PagedJS** and **python-Wappalyzer** are de-facto unmaintained; do not depend on them.
- **MiniCPM-V's "thinking" template** is enabled by default in llama.cpp builds after PR #20606 and produces broken Instruct output unless you pass `--reasoning off` explicitly. This is a footgun documented in the MiniCPM-V Cookbook.
- **Playwright's `page.pdf()`** only works in Chromium headless — calling it on Firefox or WebKit will raise. Pin the channel at launch.
- **Vivliostyle CLI is AGPL-3.0.** Shelling out to it is fine; linking against `@vivliostyle/core` is not, if you're not also AGPL.
- **vexy-pdfsvgpy** is a thin wrapper — confirm the upstream repo is current before depending on it; otherwise vendor the ~50 lines of subprocess code directly.