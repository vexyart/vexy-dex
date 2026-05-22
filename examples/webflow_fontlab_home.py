#!/usr/bin/env -S uv run -s
# this_file: examples/webflow_fontlab_home.py
"""Build slide decks from the FontLab homepage (a Webflow marketing page).

Input : https://www.fontlab.com/
Output: examples/output/fontlab-home/<strategy>/NN-slide.pdf

A short, hero-heavy Webflow homepage — few slides, mostly visual. See
expected/webflow_fontlab_home.md for captured results.
"""

from __future__ import annotations

from _runner import run

if __name__ == "__main__":
    run("https://fontlab-com.webflow.io/", "fontlab-home")
