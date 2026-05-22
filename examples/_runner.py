# this_file: examples/_runner.py
"""Shared helper for the example scripts: build a URL and print a summary.

Keeps each example script to a few lines. The default `strategies="all"` runs
every engine whose runtime deps are present and silently skips the rest
(`available()` gate), so the example output reflects what's actually installed:

  - playwright  → needs `playwright install chromium` (usually present)
  - vivliostyle → needs Node + `npm i -g @vivliostyle/cli` (else skipped)
  - reveal      → native reveal.js capture via Playwright (else skipped)
  - prince      → opt-in proprietary binary via [engines].prince_path (else skipped)

Pass an explicit comma list to force specific strategies (and to surface a loud
error if a forced engine's deps are missing).
"""

from __future__ import annotations

import json
from pathlib import Path

from vexy_dexypy.model import Source
from vexy_dexypy.orchestrator import build
from vexy_dexypy.settings import build_settings

OUTPUT_ROOT = Path(__file__).parent / "output"


def run(url: str, name: str, strategies: str = "all", size: str = "1920x1080") -> None:
    out = OUTPUT_ROOT / name
    settings = build_settings(out=str(out), strategies=strategies, size=size)
    results = build(Source.parse(url), settings)

    print(f"\nInput : {url}")
    print(f"Output: {out}/<strategy>/\n")
    for r in results:
        if r.ok:
            print(f"  {r.strategy.name:<11} {r.slide_count:>3} slides  ->  {r.out_dir}")
        else:
            print(f"  {r.strategy.name:<11} FAILED: {r.error}")

    summary = out / Source.parse(url).slug / "_meta" / "run-summary.json"
    if summary.is_file():
        print("\nrun-summary.json:")
        print(json.dumps(json.loads(summary.read_text()), indent=2))
