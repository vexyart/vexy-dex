# this_file: src/vexy_dex/exporters/decktape.py
"""DeckTape exporter — per-slide capture of the reveal.js deck (spec/19)."""

from __future__ import annotations

import contextlib
import functools
import shutil
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from ..model import RenderJob
from ._subprocess import run_engine


@contextlib.contextmanager
def _serve(root: Path):
    """Serve `root` over HTTP on an ephemeral port; tear down on exit.

    reveal.js decks with asset-relative paths can misbehave under file://; an
    HTTP origin avoids that (spec/19). The server only serves the localized
    files — still offline.
    """
    handler = functools.partial(SimpleHTTPRequestHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address[1]
    finally:
        server.shutdown()
        server.server_close()


class DeckTapeExporter:
    name = "decktape"
    needs_js = True
    supports_paged_media = False

    def available(self) -> bool:
        return shutil.which("decktape") is not None or shutil.which("npx") is not None

    def export(self, job: RenderJob, out: Path) -> Path:
        runner = ["decktape"] if shutil.which("decktape") else ["npx", "decktape"]
        with _serve(job.html_path.parent) as port:
            url = f"http://127.0.0.1:{port}/{job.html_path.name}"
            run_engine(
                [
                    *runner, "reveal",
                    "--size", f"{job.plan.stage_w}x{job.plan.stage_h}",
                    url, str(out),
                ],
                timeout=180,
            )
        return out
