# this_file: tests/test_live.py
"""Live fetch mode: navigate + keep assets online, no disk localization (spec/06)."""

from __future__ import annotations

import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from vexy_dexypy.model import Source
from vexy_dexypy.readers import read
from vexy_dexypy.readers.live import LiveReader, _inject_base, playwright_available
from vexy_dexypy.settings import build_settings

FIXTURES = Path(__file__).parent / "fixtures"


# --- pure helper -----------------------------------------------------------


def test_inject_base_adds_base_tag_when_missing():
    out = _inject_base(
        "<html><head><title>t</title></head><body></body></html>",
        "https://example.test/p",
    )
    assert '<base href="https://example.test/p"' in out


def test_inject_base_is_idempotent_when_base_present():
    html = '<html><head><base href="https://keep.me/"></head><body></body></html>'
    out = _inject_base(html, "https://other.test/")
    assert out.count("<base") == 1
    assert "https://keep.me/" in out
    assert "other.test" not in out


def test_inject_base_tolerates_missing_head():
    html = "<html><body><p>no head</p></body></html>"
    # lxml synthesizes a <head>, so a base is still injected; never raises.
    assert _inject_base(html, "https://x.test/") is not None


# --- dispatch --------------------------------------------------------------


def test_live_can_read_is_zero_so_it_never_hijacks_localize():
    # Live is mode-dispatched, not confidence-ranked.
    assert LiveReader().can_read(Source.parse("https://x.test/")) == 0.0


def test_live_mode_delegates_local_files_to_static(tmp_path):
    fixture = FIXTURES / "generic_article" / "index.html"
    settings = build_settings(out=str(tmp_path), fetch_mode="live")
    page = LiveReader().read(Source.parse(str(fixture)), settings)
    # File path: static reader runs and localizes (asset_dir is created).
    assert page.html_path.is_file()
    assert page.meta.get("fetch_mode") != "live"


# --- end-to-end over a real local origin -----------------------------------


@pytest.fixture
def served_fixture():
    """Serve tests/fixtures over loopback HTTP; yield (base_url, shutdown)."""
    root = str(FIXTURES)
    handler = functools.partial(SimpleHTTPRequestHandler, directory=root)
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.skipif(not playwright_available(), reason="needs playwright")
def test_live_read_keeps_assets_online(tmp_path, served_fixture):
    url = f"{served_fixture}/generic_article/index.html"
    settings = build_settings(out=str(tmp_path), fetch_mode="live")
    page = read(Source.parse(url), settings)

    html = page.html_path.read_text(encoding="utf-8")
    # The rendered DOM was captured and tagged as live...
    assert page.meta["fetch_mode"] == "live"
    assert "The Title" in html
    # ...a <base> points back at the live origin so assets resolve online...
    assert "<base" in html and "127.0.0.1" in page.meta["base_url"]
    # ...and nothing was localized to disk.
    assert not (page.html_path.parent / "assets").exists()
    assert page.content_hash
