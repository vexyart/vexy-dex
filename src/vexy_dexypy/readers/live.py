# this_file: src/vexy_dexypy/readers/live.py
"""Live reader: navigate the page in a browser, keep its assets online (spec/06).

The `live` fetch mode (issue 103) is the default. Unlike the static/dynamic
readers, it does **not** download or localize assets: it navigates the URL in the
chosen browser engine, captures the rendered DOM, and injects a `<base href>`
pointing at the page's own (post-redirect) origin. Every downstream stage serves
that HTML over loopback, and the `<base>` makes relative asset references resolve
against the live origin over the network — so fonts, CSS and images stay in the
browser and are never written to disk.

Local files have nothing to fetch online, so `live` mode delegates them to the
static reader (assets are already on disk).
"""

from __future__ import annotations

from loguru import logger

from ..errors import ReadError
from ..model import PageDoc, Source, SourceKind
from ..settings import Settings
from .localize import content_hash
from .static import StaticReader, _extract_meta

_SETTLE_MS = 600  # let fonts/layout/JS settle after `load` before capture


def playwright_available() -> bool:
    try:
        import playwright.sync_api  # noqa: F401

        return True
    except Exception:
        return False


def _inject_base(html: str, base_url: str) -> str:
    """Ensure the document has a `<base href>` so live asset refs resolve."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    head = soup.head
    if head is None:  # pathological, but keep going
        return html
    if head.find("base") is None:
        base = soup.new_tag("base", href=base_url)
        head.insert(0, base)
    return str(soup)


class LiveReader:
    name = "live"

    def can_read(self, source: Source) -> float:
        # Live is dispatched explicitly by `Settings.fetch_mode`, never picked by
        # confidence ranking — return 0 so it can't hijack `localize` mode.
        return 0.0

    def read(self, source: Source, settings: Settings) -> PageDoc:
        if source.kind == SourceKind.FILE:
            return StaticReader().read(source, settings)
        if not playwright_available():
            raise ReadError("live reader needs playwright")

        work = settings.out_dir / source.slug
        raw_dir = work / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        asset_dir = raw_dir / "assets"  # intentionally not created: nothing localized

        from .._browser import get_browser_page, launched_browser

        logger.info("live: navigating {} (assets stay online)", source.raw)
        with launched_browser(settings) as browser:
            pg = get_browser_page(browser, settings)
            pg.goto(source.raw, wait_until="load", timeout=30_000)
            pg.wait_for_timeout(_SETTLE_MS)
            final_url = pg.url or source.raw
            html = pg.content()

        live_html = _inject_base(html, final_url)
        html_path = raw_dir / "index.html"
        html_path.write_text(live_html, encoding="utf-8")

        page = PageDoc(source=source, html_path=html_path, asset_dir=asset_dir)
        page.content_hash = content_hash(html_path, asset_dir)
        page.meta = _extract_meta(live_html)
        page.meta["fetch_mode"] = "live"
        page.meta["base_url"] = final_url
        return page
