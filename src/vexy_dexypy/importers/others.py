from __future__ import annotations

import re

from loguru import logger
from .. import dom
from ..model import PageDoc, SlidePlan
from ..settings import Settings
from ._common import write_normalized
from .generic import GenericImporter
from .._browser import run_js_preprocessor

_DOCUSAURUS_CHROME = [".navbar", ".theme-doc-sidebar-container", "footer", "nav"]


class DocusaurusImporter:
    name = "docusaurus"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        hits = sum(h in html for h in ("__docusaurus", "theme-doc-markdown"))
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
            dom.drop_chrome(soup, _DOCUSAURUS_CHROME)
            content = soup.select_one(".theme-doc-markdown") or soup.body or soup
            sections = dom.sectionize(str(content), target=plan.slide_count)
            return write_normalized(
                page, dom.wrap_neutral(sections, dom.head_styles(soup))
            )


class BubbleImporter:
    name = "bubble"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        return 0.6 if ("data-bb-id" in html or "bubble-element" in html) else 0.0

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
            # Bubble uses absolute positioning; relax it so content flows, then
            # delegate the actual slide split to the generic path.
            for el in soup.find_all(style=re.compile(r"position\s*:\s*absolute", re.I)):
                style = el["style"]
                if not isinstance(style, str):
                    continue
                el["style"] = re.sub(
                    r"position\s*:\s*absolute",
                    "position: relative",
                    style,
                    flags=re.I,
                )
            flattened = write_normalized(page, str(soup), suffix="flattened")
            return GenericImporter().transform(flattened, plan, settings)


class FramerImporter:
    name = "framer"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        return 0.6 if "data-framer-name" in html else 0.0

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
                "browser preprocessor failed: {}; falling back to generic transform", e
            )
            return GenericImporter().transform(page, plan, settings)
