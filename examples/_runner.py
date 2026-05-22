# this_file: examples/_runner.py
"""Shared helper for the example scripts: build a URL and print a summary.

Keeps each example script to a few lines. On macOS, WeasyPrint needs Homebrew
Pango on the dyld path:

    DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib uv run examples/<script>.py
"""

from __future__ import annotations

import json
from pathlib import Path

from vexy_dex.model import Source
from vexy_dex.orchestrator import build
from vexy_dex.settings import build_settings

OUTPUT_ROOT = Path(__file__).parent / "output"


def run(url: str, name: str, strategies: str = "playwright,weasyprint",
        size: str = "1920x1080") -> None:
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
