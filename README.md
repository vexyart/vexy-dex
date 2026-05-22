<!-- this_file: README.md -->

# vexy-dex

**Turn any web page into slide decks — several at once — and keep the slides you
like.**

vexy-dex takes one URL, figures out where the slides hiding inside the page
should break, and renders it to PDF through several engines in parallel. Each
engine writes its own folder of single-page PDFs. You skim the folders and build
your final deck from the best version of each slide: the hero from one engine,
the text-heavy slides from another. No two engines paginate a page the same way,
and that's the whole point — you get a menu, not a verdict.

It runs offline after the first fetch, it's a single Python CLI, and it doesn't
try to be a slide editor.

> Status: **specification complete, implementation starting.** This repo
> currently holds the design — see [`spec/`](spec/00-tldr.md). The roadmap is in
> [spec/24](spec/24.md) and [`TODO.md`](TODO.md).

## Why it exists

Web pages are infinite vertical scrolls; slides are fixed 16:9 rectangles.
Forcing one into the other with a naive "print to PDF" cuts headings in half and
orphans images. vexy-dex paginates *intelligently* — it renders the page at the
real slide size, watches where the browser actually breaks content, and snaps
slide boundaries to sections and headings instead of arbitrary pixel rows.

Then it refuses to pick a winner. A Webflow hero looks best through Chromium; a
documentation page looks best through a pure-CSS print engine. vexy-dex runs
them all and lets you choose.

## How it works

A six-stage pipeline, orchestrated in Python, shelling out to browser and Node
engines where they do the job better:

1. **Read** — fetch the HTML and download every asset so it works offline.
2. **Analyze** — recognize the page (Webflow, MkDocs Material, …) and plan the
   slide breaks at your target aspect ratio.
3. **Normalize** — restructure the DOM into clean, slide-shaped sections.
4. **Prepare** — inject the paged-media CSS / reveal.js wrapping each engine
   wants.
5. **Render** — export to PDF through every chosen engine, in parallel.
6. **Write** — split each PDF into named single-page slides, optionally as SVG,
   with an HTML preview to browse.

The full design is 24 chapters in [`spec/`](spec/00-tldr.md); the tool decisions
and their rationale are in [`RESEARCH.md`](RESEARCH.md).

## Planned usage

```bash
# Everything, every available strategy, default 16:9
vexy-dex build https://www.vexy.art/lines/

# Pick strategies and aspect ratio, also emit SVGs
vexy-dex build https://blog.fontlab.com/ \
    --strategies weasyprint,playwright --aspect 4:3 --svg

# Re-run a single stage on an existing PDF
vexy-dex split out/lines/playwright/_combined.pdf --out out/lines/playwright --svg
```

Output lands as:

```
out/lines/
  playwright/   01-slide.pdf  02-slide.pdf  …  index.html
  weasyprint/   01-slide.pdf  …
  decktape/     01-slide.pdf  …
  _meta/        slideplan.json  run-summary.json
```

A failed engine degrades to a warning — the run still gives you the decks that
worked, and tells you how to fix the one that didn't.

## What it recognizes

- **Webflow** — absorbs and modernizes the
  [`webflow2reveal`](https://github.com/twardoch/webflow2reveal) transform (now
  first-class vexy-dex code, superseding that legacy tool): each section becomes
  a slide, chrome is dropped, backgrounds are classified light/dark.
- **MkDocs Material** — extracts the content column, splits by heading, keeps
  code blocks and tables intact.
- **Everything else** — a generic path (via `trafilatura`) extracts the article
  body and splits by `<h2>`. Bubble, Docusaurus, and Framer get light-touch
  rules on top.

New frameworks are plugins, not core changes.

## The engines

| Strategy | Engine | Best for |
|---|---|---|
| `playwright` | Headless Chromium | Webflow, JS-heavy, highly styled pages |
| `weasyprint` | Pure-Python CSS | MkDocs and other clean, static HTML |
| `vivliostyle` | Chromium typesetting | Long-form / documentation, strong paged media |
| `decktape` | Puppeteer + reveal.js | The reveal.js path, crisp per-slide capture |
| `prince` | PrinceXML (opt-in) | Reference-quality paged media, if you have a licence |

Install only what you want — a strategy whose tool is missing is skipped with a
note, never a crash.

## Optional: smarter breaks with a local vision model

For pages with no clean structure, vexy-dex can ask a small local
vision-language model ([MiniCPM-V 4.6](https://huggingface.co/openbmb/MiniCPM-V-4.6-gguf),
via Ollama or llama.cpp) to refine the slide breaks from a screenshot. It's
strictly opt-in (`--vision`), cached, and never required — the deterministic
plan always runs first.

## Requirements (planned)

- Python 3.12+, installed with `uv`.
- Playwright Chromium (`playwright install chromium`).
- Optional: Node (`@vivliostyle/cli`, `decktape`), `monolith`, poppler (for
  SVG, pulled in by [`vexy-pdfsvgpy`](https://github.com/vexyart/vexy-pdfsvgpy)),
  Prince, and Ollama/llama.cpp for vision.

## Project layout

```
spec/           # the 24-chapter specification (start at 00-tldr.md)
research/       # the source research reports
RESEARCH.md     # synthesized conclusions and tool decisions
IDEA.md         # the original concept, kept in sync
TODO.md         # actionable task list, linked to spec chapters
CLAUDE.md       # guidance for AI coding agents / contributors
```

## Contributing

Read [`spec/00-tldr.md`](spec/00-tldr.md) and [`CLAUDE.md`](CLAUDE.md) first. The
spec is the contract: implement against a chapter, and if you must deviate,
update that chapter in the same change. Tests run offline against fixtures; every
function gets one.

## Licence

See [`LICENSE`](LICENSE). Note the dependency licence hazards documented in
[spec/24](spec/24.md) (Vivliostyle and PyMuPDF are AGPL; Prince is proprietary)
— vexy-dex shells out to AGPL engines rather than linking them.
