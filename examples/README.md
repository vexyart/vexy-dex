<!-- this_file: examples/README.md -->

# Examples

Runnable scripts that double as smoke tests (spec/23). Each writes its decks to
`examples/output/` (gitignored — PDFs are binary). A captured manifest of the
real output for the live examples lives in `examples/expected/`.

## Setup

```bash
uv sync --extra all          # weasyprint + playwright + trafilatura + pikepdf
uv run playwright install chromium
```

On macOS, WeasyPrint needs Homebrew Pango on the dyld path — prefix commands
with `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` (or run via `../test.sh`).

## Scripts

| Script | Input | Kind | Result (plan → pw/weasy) | Expected |
|---|---|---|---|---|
| `build_local.py` | `tests/fixtures/generic_article/index.html` | offline fixture | — | quickest smoke test, no network |
| `webflow_retro_poster.py` | `vexy.art/lines/case-retro-poster/` | Webflow case study | 33 → 18 / 26 | [md](expected/webflow_retro_poster.md) |
| `webflow_fontlab_home.py` | `fontlab.com/` | Webflow homepage | 3 → 2 / 4 | [md](expected/webflow_fontlab_home.md) |
| `webflow_transtype.py` | `fontlab.com/font-converter/transtype/` | Webflow (div-sections) | 18 → 14 / 17 | [md](expected/webflow_transtype.md) |
| `mkdocs_blog_post.py` | `blog.fontlab.com/2026/05/07/…` | MkDocs article | 7 → 6 / 12 | [md](expected/mkdocs_blog_post.md) |

`pw` = playwright, `weasy` = weasyprint. Counts are representative (they depend
on the live page + engine metrics). All live examples share `_runner.py`.

## Run

```bash
# offline, instant
uv run examples/build_local.py

# live Webflow page (needs network + Chromium)
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run examples/webflow_retro_poster.py
```

Then open a strategy's `index.html` to browse its slides, and cherry-pick the
best rendering of each slide across the `playwright/` and `weasyprint/` folders.

## Equivalent CLI

Every example maps to a `vexy-dex` command:

```bash
vexy-dex build https://www.vexy.art/lines/case-retro-poster/ \
    --out examples/output/retro-poster --strategies playwright,weasyprint
```
