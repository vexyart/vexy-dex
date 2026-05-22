#!/usr/bin/env -S uv run -s
# this_file: examples/mkdocs_blog_post.py
"""Build slide decks from a FontLab blog post (MkDocs Material).

Input : https://blog.fontlab.com/2026/05/07/from-bland-to-bold-with-vexy-lines/
Output: examples/output/blog-post/<strategy>/NN-slide.pdf

A real article: classified mkdocs-material, content column extracted, split by
heading (code blocks/tables preserved). WeasyPrint is the natural fit for clean
documentation HTML. See expected/mkdocs_blog_post.md.
"""

from __future__ import annotations

from _runner import run

URL = "https://blog.fontlab.com/2026/05/07/from-bland-to-bold-with-vexy-lines/"

if __name__ == "__main__":
    run(URL, "blog-post")
