# this_file: tests/test_decktape_server.py
"""DeckTape's throwaway local server serves localized files (spec/19)."""

from __future__ import annotations

import urllib.request

from vexy_dex.exporters.decktape import _serve


def test_serve_returns_file_over_http(tmp_path):
    (tmp_path / "index.html").write_text("<h1>hello deck</h1>", encoding="utf-8")
    with _serve(tmp_path) as port:
        body = urllib.request.urlopen(
            f"http://127.0.0.1:{port}/index.html", timeout=5
        ).read().decode()
    assert "hello deck" in body


def test_serve_tears_down(tmp_path):
    with _serve(tmp_path) as port:
        pass
    # after teardown the port should no longer accept connections
    import socket

    s = socket.socket()
    s.settimeout(0.5)
    try:
        connected = s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()
    assert not connected, "server should be closed after the context exits"
