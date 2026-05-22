# this_file: src/vexy_dex/_browser.py
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
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SETTLE_MS = 400  # brief pause after `load` for fonts/layout/JS to settle


@contextlib.contextmanager
def serving(pg, html_path: Path, *, settle_ms: int = SETTLE_MS, timeout: int = 30_000):
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
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/{rel}"
        pg.goto(url, wait_until="load", timeout=timeout)
        pg.wait_for_timeout(settle_ms)
        yield url
    finally:
        server.shutdown()
        server.server_close()
