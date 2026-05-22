# this_file: src/vexy_dex/paginate.py
"""Stage 2 viewport pagination analysis (spec/09).

Renders the localized page in Chromium at the stage size, collects bounding
boxes, and snaps slide breaks to semantic boundaries. Falls back to a static
heuristic when Playwright is unavailable.
"""

from __future__ import annotations

from loguru import logger

from .model import Break, PageDoc, SlidePlan

_PROBE_JS = """
() => {
  const sel = 'section, article, h1, h2, h3, img, .card, [class*="hero"]';
  return Array.from(document.querySelectorAll(sel)).map(el => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {tag: el.tagName.toLowerCase(),
            top: r.top + window.scrollY, height: r.height,
            visible: cs.display !== 'none' && r.height > 0};
  });
}
"""

_SEMANTIC = ("h1", "h2", "section", "article")


def plan_breaks(elements: list[dict], stage_w: int, stage_h: int, tol: float = 50.0) -> SlidePlan:
    """Decide slide-start offsets from measured element geometry (spec/09)."""
    els = sorted((e for e in elements if e.get("visible")), key=lambda e: e["top"])
    breaks: list[Break] = []
    cursor = 0.0
    for e in els:
        top, h, tag = e["top"], e["height"], e["tag"]
        if h > stage_h:  # over-tall block → split into screen-height pieces
            for k in range(1, round(h / stage_h)):
                breaks.append(Break(top + k * stage_h, "overflow", 0.6))
            cursor = top + h
        elif top > cursor + stage_h - tol:  # would overflow the stage
            breaks.append(Break(top, "overflow", 0.8))
            cursor = top
        elif tag in _SEMANTIC and (top - cursor) > stage_h * 0.4:  # semantic start
            breaks.append(Break(top, tag, 1.0))
            cursor = top
    return SlidePlan(stage_w, stage_h, breaks).normalized()


def _probe_playwright(page: PageDoc, stage_w: int, stage_h: int) -> list[dict] | None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            pg = browser.new_context(
                viewport={"width": stage_w, "height": stage_h}
            ).new_page()
            pg.goto(page.html_path.resolve().as_uri(), wait_until="networkidle")
            pg.emulate_media(media="screen")
            elements = pg.evaluate(_PROBE_JS)
            browser.close()
        return elements
    except Exception as e:  # rendering failed; caller falls back
        logger.warning("pagination probe failed: {}", e)
        return None


def _heuristic_static(page: PageDoc, stage_w: int, stage_h: int) -> SlidePlan:
    """No-browser fallback: one break per top-level <section>/<h2> (spec/09)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(page.html_path.read_text(encoding="utf-8"), "lxml")
    nodes = soup.select("section, h2")
    # Without geometry we can't compute y; emit evenly-spaced advisory breaks.
    breaks = [Break(float(i + 1) * stage_h, "section", 0.5) for i in range(len(nodes))]
    plan = SlidePlan(stage_w, stage_h, breaks, {"mode": "static-fallback"})
    return plan.normalized()


def analyze(page: PageDoc, stage_w: int, stage_h: int) -> SlidePlan:
    """Produce a SlidePlan, preferring the browser probe (spec/09)."""
    elements = _probe_playwright(page, stage_w, stage_h)
    if elements is not None:
        return plan_breaks(elements, stage_w, stage_h)
    logger.info("playwright unavailable; using static pagination heuristic")
    return _heuristic_static(page, stage_w, stage_h)
