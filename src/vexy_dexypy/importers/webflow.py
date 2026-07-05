# this_file: src/vexy_dexypy/importers/webflow.py
"""Webflow importer — adapted from webflow2reveal/py/.../compiler.py (spec/12).

This is a deliberate copy-and-adapt: the five-step transform becomes first-class
vexy-dexypy code, generalized to the configurable stage and shared layout
vocabulary. vexy-dexypy supersedes the legacy webflow2reveal package.

The five steps (spec/12):
  1. resolve colours        2. select <section> slides (drop chrome)
  3. normalize the DOM      4. classify backgrounds by luminance
  5. wrap in the reveal chassis
"""

from __future__ import annotations

import re

from loguru import logger
from .. import dom
from ..model import PageDoc, SlidePlan
from ..settings import Settings
from ._common import write_normalized
from .._browser import run_js_preprocessor

# Chrome keywords lifted verbatim from compiler.py:is_slide_section.
_CHROME_KEYWORDS = ("menu", "nav", "footer", "mask", "header", "banner")

# Selectors for page chrome to drop before the block-split fallback.
_CHROME_SELECTORS = [
    "nav",
    "header",
    "footer",
    ".navbar",
    ".w-nav",
    "[class*='menu']",
    "[class*='footer']",
    "[class*='banner']",
    ".w-webflow-badge",
]


def _classes_str(node) -> str:
    return (
        " ".join(node.get("class") or []).lower() + " " + (node.get("id") or "").lower()
    )


def _is_slide_section(section) -> bool:
    """A <section> is a slide unless it's nav/footer/menu/header/banner chrome."""
    classes = _classes_str(section)
    if any(k in classes for k in _CHROME_KEYWORDS):
        return False
    if section.find("vexy-menu") or section.find("vexy-footer"):
        return False
    return True


def _bg_color(section) -> str:
    """Best-effort background colour from an inline style or data attribute."""
    style = (section.get("style") or "") if hasattr(section, "get") else ""
    m = re.search(r"background(?:-color)?\s*:\s*([^;]+)", style, re.I)
    if m:
        return m.group(1).strip()
    return section.get("data-background-color", "") or "#ffffff"


class WebflowImporter:
    name = "webflow"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        hits = sum(
            n in html for n in ("data-wf-page", "data-w-id", "w-mod-js", "webflow.js")
        )
        return min(1.0, 0.5 + 0.25 * (hits - 1)) if hits else 0.0

    def transform(
        self, page: PageDoc, plan: SlidePlan, settings: Settings | None = None
    ) -> PageDoc:
        raw = page.html_path.read_text(encoding="utf-8")
        if dom.already_neutral(raw):
            return page

        actual_settings = settings or Settings()
        config = {
            "framework": self.name,
            "stageWidth": plan.stage_w,
            "stageHeight": plan.stage_h,
            "breaks": [
                {"y": b.y, "reason": b.reason, "confidence": b.confidence}
                for b in plan.breaks
            ],
        }
        logger.info("running browser preprocessor for framework: {}", self.name)
        try:
            normalized_html = run_js_preprocessor(
                page.html_path, actual_settings, config
            )
            return write_normalized(page, normalized_html)
        except Exception as e:
            logger.error(
                "browser preprocessor failed: {}; falling back to python sectionizer", e
            )
            soup = dom.parse(raw)
            # The "Made in Webflow" badge is injected on free sites; drop it before
            # extraction (the section path skips drop_chrome) — belt-and-braces with
            # the CSS hide in the pre-exporter for any JS re-injection (spec/15).
            dom.drop_chrome(soup, [".w-webflow-badge"])
            body = soup.body or soup

            sections = []
            for section in body.find_all("section"):
                if not _is_slide_section(section):
                    continue
                color = _bg_color(section)
                section["data-background-color"] = color
                # bs4 stub types the setter as str|AttributeValueList; a list is valid.
                section["class"] = [  # type: ignore[assignment]
                    *(section.get("class") or []),
                    "slide",
                    dom.bg_class(color),
                ]
                sections.append(section.extract())

            if len(sections) < 2:
                # Live Webflow pages often use <div class="section"> rather than
                # <section> tags, so tag-based selection finds too few. Drop chrome
                # and distribute the real DOM blocks into the planned slide count
                # (sectionize._content_root descends the Webflow page-wrapper). This
                # beats trafilatura, which collapses marketing pages.
                soup2 = dom.parse(raw)
                dom.drop_chrome(soup2, _CHROME_SELECTORS)
                body2 = soup2.body or soup2
                sections = dom.sectionize(str(body2), target=max(plan.slide_count, 2))

            # Carry the page's stylesheets so the Webflow design survives wrapping —
            # without them the extracted sections render as unstyled HTML.
            return write_normalized(
                page, dom.wrap_neutral(sections, dom.head_styles(soup))
            )
