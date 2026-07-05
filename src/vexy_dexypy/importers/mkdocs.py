# this_file: src/vexy_dexypy/importers/mkdocs.py
"""MkDocs Material importer: content extraction + heading split (spec/13)."""

from __future__ import annotations

from loguru import logger
from .. import dom
from ..model import PageDoc, SlidePlan
from ..settings import Settings
from ._common import write_normalized
from .._browser import run_js_preprocessor

_CHROME = [
    ".md-sidebar",
    ".md-header",
    ".md-footer",
    ".md-search",
    ".md-nav",
    ".md-source-file",
    ".md-content__button",
    "header",
    "nav",
    "footer",
]


class MkdocsImporter:
    name = "mkdocs-material"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        hits = sum(h in html for h in ("md-content", "md-typeset", "data-md-component"))
        return min(1.0, 0.5 + 0.2 * hits) if hits else 0.0

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
            dom.drop_chrome(soup, _CHROME)
            content = soup.select_one("article.md-content__inner") or soup.body or soup
            # Code blocks and tables ride along inside content — never stripped.
            sections = dom.sectionize(str(content), target=plan.slide_count)
            for sec in sections:
                # bs4 stub types the setter as str|AttributeValueList; a list is valid.
                sec["class"] = [*(sec.get("class") or []), "slide-light-bg"]  # type: ignore[assignment]
            return write_normalized(
                page, dom.wrap_neutral(sections, dom.head_styles(soup))
            )
