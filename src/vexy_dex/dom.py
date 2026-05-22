# this_file: src/vexy_dex/dom.py
"""Shared DOM helpers used by every importer (spec/11).

Importers compose these; they don't each reinvent reveal wrapping. Built on
BeautifulSoup + lxml for readable DOM surgery.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup, Tag

HEADINGS = ("h1", "h2", "h3", "h4", "h5", "h6")


def parse(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def drop_chrome(soup: BeautifulSoup, selectors: list[str]) -> None:
    """Remove navigation/footer/etc. nodes matching tag names or CSS selectors."""
    for sel in selectors:
        for node in soup.select(sel):
            node.decompose()


def luminance(color: str) -> float:
    """Perceptual luminance 0..1 of a CSS color (#rgb/#rrggbb/rgb()). White=1."""
    color = (color or "").strip().lower()
    rgb: tuple[int, int, int] | None = None
    if color.startswith("#"):
        h = color[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) >= 6:
            try:
                rgb = (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
            except ValueError:
                rgb = None
    else:
        m = re.match(r"rgba?\(([^)]+)\)", color)
        if m:
            parts = [p.strip() for p in m.group(1).split(",")[:3]]
            try:
                rgb = tuple(int(float(p)) for p in parts)  # type: ignore[assignment]
            except ValueError:
                rgb = None
    if rgb is None:
        return 1.0  # assume light when unknown
    r, g, b = (c / 255 for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def bg_class(color: str) -> str:
    """Tag a slide light/dark by luminance for correct text contrast."""
    return "slide-light-bg" if luminance(color) >= 0.5 else "slide-dark-bg"


def split_by_heading(
    container: Tag,
    levels: tuple[str, ...] = ("h1", "h2"),
    max_h: int | None = None,
    fallback: str | None = None,
) -> list[Tag]:
    """Split a content container into <section> slides at heading boundaries.

    A heading in `levels` starts a new slide; everything until the next such
    heading is its body. (max_h/fallback are advisory hooks for future
    overflow-aware splitting; the current pass groups by heading only.)
    """
    soup = BeautifulSoup("", "lxml")
    sections: list[Tag] = []
    current = soup.new_tag("section")

    children = [c for c in container.children if getattr(c, "name", None) or str(c).strip()]
    for child in children:
        name = getattr(child, "name", None)
        if name in levels and current.contents:
            sections.append(current)
            current = soup.new_tag("section")
        if name is not None:
            current.append(child.extract() if hasattr(child, "extract") else child)
    if current.contents:
        sections.append(current)
    if not sections:  # nothing matched; keep the whole container as one slide
        only = soup.new_tag("section")
        only.append(container)
        sections = [only]
    return sections


def wrap_reveal(sections: list[Tag]) -> str:
    """Wrap a list of <section> slides in the canonical reveal chassis (spec/11)."""
    soup = BeautifulSoup(
        '<!doctype html><html><head><meta charset="utf-8"></head>'
        '<body><div class="reveal"><div class="slides"></div></div></body></html>',
        "lxml",
    )
    slides = soup.select_one("div.slides")
    assert slides is not None
    for sec in sections:
        if "slide" not in (sec.get("class") or []):
            sec["class"] = [*(sec.get("class") or []), "slide"]
        slides.append(sec)
    return str(soup)


def already_reveal(html: str) -> bool:
    soup = parse(html)
    return bool(soup.select_one("div.reveal div.slides"))
