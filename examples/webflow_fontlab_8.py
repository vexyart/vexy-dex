#!/usr/bin/env -S uv run -s
# this_file: examples/webflow_fontlab_8.py
"""Build slide decks from the FontLab 8 product page (a Webflow page).

Input : https://fontlab-com.webflow.io/font-editor/fontlab/index-fontlab
Output: examples/output/fontlab-8/<strategy>/NN-slide.pdf

A long-form Webflow product page — many feature sections paginated into
slides. See expected/ for captured results.
"""

from __future__ import annotations

from _runner import run

if __name__ == "__main__":
    run("https://fontlab-com.webflow.io/font-editor/fontlab/index-fontlab", "fontlab-8")
