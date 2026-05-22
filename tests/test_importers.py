# this_file: tests/test_importers.py
from __future__ import annotations

from dataclasses import replace

from vexy_dexypy import dom
from vexy_dexypy.importers.generic import GenericImporter
from vexy_dexypy.importers.mkdocs import MkdocsImporter
from vexy_dexypy.importers.webflow import WebflowImporter
from vexy_dexypy.model import PageDoc, SlidePlan, Source


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
    assert dom.already_neutral(result)
    assert "navigation chrome" not in result, "nav section should be dropped"
    assert "footer chrome" not in result, "footer section should be dropped"
    assert "Hero Headline" in result
    assert "slide-dark-bg" in result, "dark hero should be tagged dark"


def test_webflow_divsection_page_uses_plan_fallback(tmp_path):
    """Live Webflow pages use <div class=section>, not <section>; fall back to
    distributing blocks into the planned slide count (regression for transtype)."""
    blocks = "".join(
        f'<div class="section s{i}"><h2>Block {i}</h2><p>x</p></div>' for i in range(8)
    )
    html = (
        '<html data-wf-page="p"><body><div class="page-wrapper">'
        f'<nav class="w-nav">chrome</nav>{blocks}'
        '<footer class="footer">chrome</footer></div></body></html>'
    )
    from vexy_dexypy.model import Break

    # A 6-slide plan exercises the block-distribution fallback target.
    plan = SlidePlan(
        1920, 1080, [Break(float(i) * 1080, "section") for i in range(1, 6)]
    )
    out = WebflowImporter().transform(_page(tmp_path, html), plan)
    result = out.html_path.read_text()
    assert result.count("<section") >= 4, "div-section page should yield many slides"
    assert "chrome" not in result, "nav/footer chrome dropped"


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
    assert out2.html_path == again.html_path, "already-neutral input is a no-op"
