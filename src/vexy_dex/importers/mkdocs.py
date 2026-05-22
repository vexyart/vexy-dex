# this_file: src/vexy_dex/importers/mkdocs.py
"""MkDocs Material importer: content extraction + heading split (spec/13)."""

from __future__ import annotations

from .. import dom
from ..model import PageDoc, SlidePlan
from ._common import write_normalized

_CHROME = [
    ".md-sidebar", ".md-header", ".md-footer", ".md-search", ".md-nav",
    ".md-source-file", ".md-content__button", "header", "nav", "footer",
]


class MkdocsImporter:
    name = "mkdocs-material"

    def detect(self, page: PageDoc) -> float:
        html = page.html_path.read_text(encoding="utf-8").lower()
        hits = sum(h in html for h in ("md-content", "md-typeset", "data-md-component"))
        return min(1.0, 0.5 + 0.2 * hits) if hits else 0.0

    def transform(self, page: PageDoc, plan: SlidePlan) -> PageDoc:
        raw = page.html_path.read_text(encoding="utf-8")
        if dom.already_reveal(raw):
            return page
        soup = dom.parse(raw)
        dom.drop_chrome(soup, _CHROME)
        content = soup.select_one("article.md-content__inner") or soup.body or soup
        # Code blocks and tables ride along inside content — never stripped.
        sections = dom.sectionize(str(content), target=plan.slide_count)
        for sec in sections:
            sec["class"] = [*(sec.get("class") or []), "slide-light-bg"]
        return write_normalized(page, dom.wrap_reveal(sections))
