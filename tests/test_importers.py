# this_file: tests/test_importers.py
from __future__ import annotations

from dataclasses import replace

from vexy_dex.importers.generic import GenericImporter
from vexy_dex.importers.mkdocs import MkdocsImporter
from vexy_dex.importers.webflow import WebflowImporter
from vexy_dex.model import PageDoc, SlidePlan, Source


def _page(tmp_path, fixture_html: str) -> PageDoc:
    raw = tmp_path / "raw"
    raw.mkdir()
    html = raw / "index.html"
    html.write_text(fixture_html, encoding="utf-8")
    src = Source.parse("https://example.com/x")
    return PageDoc(source=src, html_path=html, asset_dir=raw / "assets")


PLAN = SlidePlan(1920, 1080)


def test_webflow_selects_sections_drops_chrome(tmp_path, fixtures):
    html = (fixtures / "webflow_sample" / "index.html").read_text()
    page = _page(tmp_path, html)
    out = WebflowImporter().transform(page, PLAN)
    result = out.html_path.read_text()
    assert "reveal" in result and "slides" in result
    assert "navigation chrome" not in result, "nav section should be dropped"
    assert "footer chrome" not in result, "footer section should be dropped"
    assert "Hero Headline" in result
    assert "slide-dark-bg" in result, "dark hero should be tagged dark"


def test_mkdocs_extracts_content_keeps_code(tmp_path, fixtures):
    html = (fixtures / "mkdocs_sample" / "index.html").read_text()
    page = _page(tmp_path, html)
    out = MkdocsImporter().transform(page, PLAN)
    result = out.html_path.read_text()
    assert "sidebar chrome" not in result and "header chrome" not in result
    assert 'key = "value"' in result, "code blocks must survive"


def test_generic_splits_article(tmp_path, fixtures):
    html = (fixtures / "generic_article" / "index.html").read_text()
    page = _page(tmp_path, html)
    out = GenericImporter().transform(page, PLAN)
    result = out.html_path.read_text()
    assert result.count("<section") >= 3, "h1 + h2s should yield several slides"


def test_importer_idempotent_on_canonical_input(tmp_path):
    once = _page(tmp_path, "<body><article><h1>A</h1><h2>B</h2></article></body>")
    out1 = GenericImporter().transform(once, PLAN)
    # feed the normalized output back in
    again = replace(once, html_path=out1.html_path)
    out2 = GenericImporter().transform(again, PLAN)
    assert out2.html_path == again.html_path, "already-reveal input is a no-op"
