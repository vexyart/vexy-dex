# this_file: tests/test_localize.py
"""CSS url()/@import localization (spec/07) with a fake HTTP client."""

from __future__ import annotations

from vexy_dex.readers.localize import _localize_css, _safe_name


class _Resp:
    def __init__(self, body: bytes | str, ctype: str = "text/css"):
        self._body = body
        self.status_code = 200
        self.headers = {"content-type": ctype}

    @property
    def content(self) -> bytes:
        return self._body if isinstance(self._body, bytes) else self._body.encode()

    @property
    def text(self) -> str:
        return self._body if isinstance(self._body, str) else self._body.decode()


class _FakeClient:
    def __init__(self, routes: dict[str, _Resp]):
        self.routes = routes
        self.seen: list[str] = []

    def get(self, url: str) -> _Resp:
        self.seen.append(url)
        if url in self.routes:
            return self.routes[url]
        return _Resp(b"x", "font/woff2")


def test_localize_css_rewrites_url_and_downloads(tmp_path):
    client = _FakeClient({})
    css = "body{background:url('https://cdn.test/bg.png')}"
    out = _localize_css(client, css, "https://site.test/a.css", tmp_path, depth=1)
    assert "https://cdn.test" not in out, "remote url should be rewritten"
    assert "https://cdn.test/bg.png" in client.seen
    assert any(tmp_path.iterdir()), "asset should be saved locally"


def test_localize_css_follows_import_bounded(tmp_path):
    inner = "div{background:url('https://cdn.test/x.png')}"
    client = _FakeClient({"https://site.test/inner.css": _Resp(inner)})
    css = '@import "https://site.test/inner.css";'
    out = _localize_css(client, css, "https://site.test/main.css", tmp_path, depth=2)
    assert "@import" in out
    assert "https://site.test/inner.css" in client.seen
    # the imported sheet's own asset should also be fetched (depth recursion)
    assert "https://cdn.test/x.png" in client.seen


def test_localize_css_skips_data_uri(tmp_path):
    client = _FakeClient({})
    css = "i{background:url(data:image/png;base64,AAAA)}"
    out = _localize_css(client, css, "https://site.test/a.css", tmp_path, depth=1)
    assert "data:image/png" in out, "data URIs left untouched"
    assert client.seen == []


def test_safe_name_hashes_long_paths():
    long = "https://x.test/" + "a" * 200 + ".css"
    assert len(_safe_name(long)) <= 30
