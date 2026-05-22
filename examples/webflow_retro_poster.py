#!/usr/bin/env -S uv run -s
# this_file: examples/webflow_retro_poster.py
"""Build slide decks from a live Webflow case-study page.

Input : https://www.vexy.art/lines/case-retro-poster/  (a Webflow page)
Output: examples/output/retro-poster/<strategy>/NN-slide.pdf  (+ index.html)

This is the canonical Webflow example. vexy-dex fetches the live page, localizes
its assets for offline rendering, classifies it as Webflow, plans slide breaks
by probing the rendered layout at 1920x1080, normalizes each `<section>` into a
slide, then renders through two engines in parallel:

- playwright  -> Chromium fidelity (best for Webflow's styled hero sections)
- weasyprint  -> pure-CSS paged media (more, text-tighter slides)

The two engines paginate differently on purpose; you cherry-pick the best
rendering of each slide across the two folders.

Requires the `all` extra (`uv sync --extra all` + `playwright install chromium`).
On macOS, WeasyPrint needs Homebrew Pango on the dyld path:

    DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run examples/webflow_retro_poster.py
"""

from __future__ import annotations

import json
from pathlib import Path

from vexy_dex.model import Source
from vexy_dex.orchestrator import build
from vexy_dex.settings import build_settings

URL = "https://www.vexy.art/lines/case-retro-poster/"
OUT = Path(__file__).parent / "output" / "retro-poster"


def main() -> None:
    settings = build_settings(
        out=str(OUT), strategies="playwright,weasyprint", size="1920x1080"
    )
    results = build(Source.parse(URL), settings)

    print(f"\nInput : {URL}")
    print(f"Output: {OUT}/<strategy>/\n")
    for r in results:
        if r.ok:
            print(f"  {r.strategy.name:<11} {r.slide_count:>3} slides  ->  {r.out_dir}")
        else:
            print(f"  {r.strategy.name:<11} FAILED: {r.error}")

    summary = OUT / Source.parse(URL).slug / "_meta" / "run-summary.json"
    if summary.is_file():
        print("\nrun-summary.json:")
        print(json.dumps(json.loads(summary.read_text()), indent=2))


if __name__ == "__main__":
    main()
