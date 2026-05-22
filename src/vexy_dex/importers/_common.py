# this_file: src/vexy_dex/importers/_common.py
"""Shared helper for writing a normalized PageDoc (spec/11)."""

from __future__ import annotations

from dataclasses import replace

from ..model import PageDoc


def write_normalized(page: PageDoc, html: str, suffix: str = "normalized") -> PageDoc:
    """Write transformed HTML beside the raw page and return an updated PageDoc."""
    work = page.html_path.parent.parent  # out/<slug>/
    norm_dir = work / "normalized"
    norm_dir.mkdir(parents=True, exist_ok=True)
    # Keep assets reachable: normalized HTML references ../raw/assets/...
    out = norm_dir / f"{suffix}.html"
    html = html.replace('"assets/', '"../raw/assets/').replace("'assets/", "'../raw/assets/")
    out.write_text(html, encoding="utf-8")
    return replace(page, html_path=out)
