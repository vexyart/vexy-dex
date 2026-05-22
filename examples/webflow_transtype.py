#!/usr/bin/env -S uv run -s
# this_file: examples/webflow_transtype.py
"""Build slide decks from the TransType product page (a Webflow page).

Input : https://www.fontlab.com/font-converter/transtype/
Output: examples/output/transtype/<strategy>/NN-slide.pdf

This page uses `<div class="section">` rather than `<section>` tags — the case
that drives vexy-dex's Webflow block-distribution fallback (the importer drops
chrome and distributes the page-wrapper's blocks into the planned slide count).
See expected/webflow_transtype.md.
"""

from __future__ import annotations

from _runner import run

if __name__ == "__main__":
    run("https://fontlab-com.webflow.io/font-converter/transtype/index-transtype", "transtype")
