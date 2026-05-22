# this_file: src/vexy_dex/readers/dynamic.py
"""Dynamic reader: Playwright renders client-side pages before capture (spec/06).

Optional — requires the `browser` extra. If Playwright isn't installed,
`can_read` returns 0 so the static reader wins.
"""

from __future__ import annotations

from loguru import logger

from ..errors import ReadError
from ..model import PageDoc, Source, SourceKind
from ..settings import Settings
from .localize import content_hash, localize_assets
from .static import _extract_meta


def _playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401

        return True
    except Exception:
        return False


class DynamicReader:
    name = "dynamic"

    def can_read(self, source: Source) -> float:
        if source.kind != SourceKind.URL or not _playwright_available():
            return 0.0
        return 0.3  # below static by default; static escalates here when needed

    def read(self, source: Source, settings: Settings) -> PageDoc:
        if not _playwright_available():
            raise ReadError("dynamic reader needs the `browser` extra (playwright)")
        from playwright.sync_api import sync_playwright

        work = settings.out_dir / source.slug
        raw_dir = work / "raw"
        asset_dir = raw_dir / "assets"
        raw_dir.mkdir(parents=True, exist_ok=True)

        logger.info("rendering {} in headless chromium", source.raw)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_context(
                viewport={"width": settings.stage_w, "height": settings.stage_h}
            ).new_page()
            page.goto(source.raw, wait_until="networkidle")
            html = page.content()
            browser.close()

        local_html = localize_assets(html, source.raw, asset_dir)
        html_path = raw_dir / "index.html"
        html_path.write_text(local_html, encoding="utf-8")

        doc = PageDoc(source=source, html_path=html_path, asset_dir=asset_dir)
        doc.content_hash = content_hash(html_path, asset_dir)
        doc.meta = _extract_meta(local_html)
        return doc
