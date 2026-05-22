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

| Script | Input | Engines | Notes |
|---|---|---|---|
| `build_local.py` | `tests/fixtures/generic_article/index.html` | weasyprint | Offline, no network; the quickest smoke test. |
| `webflow_retro_poster.py` | `https://www.vexy.art/lines/case-retro-poster/` (Webflow) | playwright + weasyprint | The canonical Webflow case. Expected output: [`expected/webflow_retro_poster.md`](expected/webflow_retro_poster.md). |

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
