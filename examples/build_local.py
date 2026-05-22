#!/usr/bin/env -S uv run -s
# this_file: examples/build_local.py
"""Build slide decks from a local fixture with every available strategy.

Runs offline. Doubles as a smoke test (spec/23). Each engine whose runtime deps
are present runs; the rest are silently skipped (`available()` gate).
"""

from __future__ import annotations

from pathlib import Path

from vexy_dex.model import Source
from vexy_dex.orchestrator import build
from vexy_dex.settings import build_settings

FIXTURE = (
    Path(__file__).parent.parent
    / "tests"
    / "fixtures"
    / "generic_article"
    / "index.html"
)


def main() -> None:
    settings = build_settings(out="out", strategies="all")
    results = build(Source.parse(str(FIXTURE)), settings)
    for r in results:
        status = "ok" if r.ok else f"FAILED: {r.error}"
        print(f"{r.strategy.name}: {r.slide_count} slides -> {r.out_dir} [{status}]")


if __name__ == "__main__":
    main()
