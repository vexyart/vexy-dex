# this_file: src/vexy_dex/importers/others.py
"""Light-touch importers for Docusaurus, Bubble, Framer (spec/14).

Each is a thin plugin reusing dom helpers and mostly delegating to the generic
path. Resist over-fitting — generic + trafilatura handles the long tail.
"""

from __future__ import annotations

import re

from .. import dom
from ..model import PageDoc, SlidePlan
from ._common import write_normalized
from .generic import GenericImporter

_DOCUSAURUS_CHROME = [".navbar", ".theme-doc-sidebar-container", "footer", "nav"]


class DocusaurusImporter:
    name = "docusaurus"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        hits = sum(h in html for h in ("__docusaurus", "theme-doc-markdown"))
        return min(1.0, 0.5 + 0.2 * hits) if hits else 0.0

    def transform(self, page: PageDoc, plan: SlidePlan) -> PageDoc:
        raw = page.html_path.read_text(encoding="utf-8")
        if dom.already_reveal(raw):
            return page
        soup = dom.parse(raw)
        dom.drop_chrome(soup, _DOCUSAURUS_CHROME)
        content = soup.select_one(".theme-doc-markdown") or soup.body or soup
        sections = dom.sectionize(str(content), target=plan.slide_count)
        return write_normalized(page, dom.wrap_reveal(sections, dom.head_styles(soup)))


class BubbleImporter:
    name = "bubble"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        return 0.6 if ("data-bb-id" in html or "bubble-element" in html) else 0.0

    def transform(self, page: PageDoc, plan: SlidePlan) -> PageDoc:
        raw = page.html_path.read_text(encoding="utf-8")
        if dom.already_reveal(raw):
            return page
        soup = dom.parse(raw)
        # Bubble uses absolute positioning; relax it so content flows, then
        # delegate the actual slide split to the generic path.
        for el in soup.find_all(style=re.compile(r"position\s*:\s*absolute", re.I)):
            el["style"] = re.sub(
                r"position\s*:\s*absolute",
                "position: relative",
                el["style"],
                flags=re.I,
            )
        flattened = write_normalized(page, str(soup), suffix="flattened")
        return GenericImporter().transform(flattened, plan)


class FramerImporter:
    name = "framer"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        return 0.6 if "data-framer-name" in html else 0.0

    def transform(self, page: PageDoc, plan: SlidePlan) -> PageDoc:
        # Framer is JS-heavy; after a dynamic/frozen fetch it is best handled by
        # the generic content extractor.
        return GenericImporter().transform(page, plan)
