# this_file: src/vexy_dex/importers/generic.py
"""Generic importer: trafilatura extract (optional) + h2 split (spec/14)."""

from __future__ import annotations

from loguru import logger

from .. import dom
from ..model import PageDoc, SlidePlan
from ._common import write_normalized


class GenericImporter:
    name = "generic"

    def detect(self, page: PageDoc) -> float:
        return 0.1  # always a low-confidence fallback so specific importers win

    def transform(self, page: PageDoc, plan: SlidePlan) -> PageDoc:
        raw = page.html_path.read_text(encoding="utf-8")
        if dom.already_reveal(raw):  # idempotent on canonical input
            return page
        body_html = self._extract(raw)
        sections = dom.sectionize(body_html, target=plan.slide_count)
        head = dom.head_styles(dom.parse(raw))
        return write_normalized(page, dom.wrap_reveal(sections, head))

    def _extract(self, html: str) -> str:
        try:
            import trafilatura

            out = trafilatura.extract(
                html, output_format="html", include_images=True, include_links=True
            )
            if out:
                return out
        except Exception as e:
            logger.debug("trafilatura unavailable/failed ({}); using raw body", e)
        # Fallback: strip obvious chrome and keep the body.
        soup = dom.parse(html)
        dom.drop_chrome(soup, ["nav", "header", "footer", "aside", "script", "style"])
        return str(soup.body or soup)
