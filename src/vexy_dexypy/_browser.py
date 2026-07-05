# this_file: src/vexy_dexypy/_browser.py
"""Shared Playwright navigation for local pages (spec/17, spec/09, spec/19).

We serve the localized page over a throwaway loopback HTTP server and navigate
to it, rather than opening it as `file://`. A real `http://` origin avoids the
file:// opaque-origin quirks that silently break rendering: CORS-gated webfonts,
`fetch()`/XHR, ES modules, and Subresource Integrity. The server is rooted at
the deck directory so `../raw/assets/` references resolve, serves only the
localized files (still offline, spec/07), and is torn down on exit.

Navigation waits for the `load` event (not `networkidle`): an offline page whose
JS retries the 4xx/5xx assets we couldn't localize never goes idle, so
`networkidle` would hang to its timeout (seen on Webflow pages with dead CDN
assets). A short settle after `load` lets fonts/layout/JS catch up; callers
needing a stronger signal add their own `wait_for_function`.
"""

from __future__ import annotations

import contextlib
import functools
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Generator, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from playwright.sync_api import Browser as PlaywrightBrowser, Page
    from .settings import Settings

SETTLE_MS = 400  # brief pause after `load` for fonts/layout/JS to settle


@contextlib.contextmanager
def serving(
    pg: Page, html_path: Path, *, settle_ms: int = SETTLE_MS, timeout: int = 30_000
):
    """Serve `html_path` over loopback HTTP, navigate to it, keep it up in-scope.

    The server stays alive for the whole `with` body so lazily-loaded assets,
    screenshots and slide stepping all resolve over http://.
    """
    html_path = html_path.resolve()
    # Root two levels up so sibling `../raw/assets/` references resolve.
    root = html_path.parents[1] if len(html_path.parents) >= 2 else html_path.parent
    rel = html_path.relative_to(root).as_posix()

    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/{rel}"
        pg.goto(url, wait_until="load", timeout=timeout)
        pg.wait_for_timeout(settle_ms)
        yield url
    finally:
        server.shutdown()
        server.server_close()


@contextlib.contextmanager
def launched_browser(settings: Settings) -> Generator[PlaywrightBrowser, None, None]:
    """Launch the chosen browser engine as a context manager."""
    engine = (settings.browser_engine or "playwright").lower()
    logger.debug("launching browser engine: {}", engine)

    if engine == "playwrightauthor":
        p_path = Path("private/playwrightauthor/src").resolve()
        if str(p_path) not in sys.path:
            sys.path.insert(0, str(p_path))
        from playwrightauthor import Browser as AuthorBrowser

        with AuthorBrowser() as browser:
            yield browser

    elif engine == "cloakbrowser":
        import cloakbrowser

        browser = cloakbrowser.launch(headless=True)
        try:
            yield browser
        finally:
            browser.close()

    else:  # default standard playwright
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch()
            yield browser


def get_browser_page(browser: PlaywrightBrowser, settings: Settings) -> Page:
    """Retrieve a page from the browser context, matching the viewport setting."""
    if hasattr(browser, "get_page"):
        pg = browser.get_page()
        pg.set_viewport_size({"width": settings.stage_w, "height": settings.stage_h})
    else:
        pg = browser.new_context(
            viewport={"width": settings.stage_w, "height": settings.stage_h}
        ).new_page()
    return pg


def run_js_preprocessor(html_path: Path, settings: Settings, config: dict) -> str:
    """Launch browser, serve HTML, inject vexy-dexyjs.js preprocessor, and run transform."""
    js_path = Path(__file__).parent / "assets" / "vexy-dexyjs.js"
    if not js_path.is_file():
        raise RuntimeError(f"vexy-dexyjs bundle not found at {js_path}")
    js_code = js_path.read_text(encoding="utf-8")

    with launched_browser(settings) as browser:
        pg = get_browser_page(browser, settings)
        with serving(pg, html_path):
            pg.emulate_media(media="screen")
            pg.evaluate(js_code)
            result = pg.evaluate("config => window.VexyDexy.preprocess(config)", config)
            return result["html"]
