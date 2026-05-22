# this_file: tests/test_edge.py
"""Edge and error cases (spec/23)."""

from __future__ import annotations

import pytest

from vexy_dexypy import dom
from vexy_dexypy.errors import ReadError
from vexy_dexypy.importers.generic import GenericImporter
from vexy_dexypy.importers.others import BubbleImporter, DocusaurusImporter
from vexy_dexypy.model import PageDoc, SlidePlan, Source
from vexy_dexypy.readers.static import StaticReader
from vexy_dexypy.settings import build_settings

PLAN = SlidePlan(1920, 1080)


def _page(tmp_path, html: str) -> PageDoc:
    raw = tmp_path / "raw"
    raw.mkdir()
    f = raw / "index.html"
    f.write_text(html, encoding="utf-8")
    return PageDoc(
        source=Source.parse("https://x.test/p"), html_path=f, asset_dir=raw / "assets"
    )


def test_empty_page_yields_one_slide(tmp_path):
    out = GenericImporter().transform(
        _page(tmp_path, "<html><body></body></html>"), PLAN
    )
    assert dom.already_neutral(out.html_path.read_text())


def test_malformed_html_does_not_crash(tmp_path):
    bad = "<html><body><h1>unclosed<section><p>x</body>"
    out = GenericImporter().transform(_page(tmp_path, bad), PLAN)
    assert dom.already_neutral(out.html_path.read_text())


def test_no_headings_single_slide(tmp_path):
    html = "<body><div>just some text, no headings at all</div></body>"
    out = GenericImporter().transform(_page(tmp_path, html), PLAN)
    assert out.html_path.read_text().count("<section") >= 1


def test_missing_file_raises_read_error(tmp_path):
    src = Source.parse(str(tmp_path / "nope.html"))
    with pytest.raises(ReadError):
        StaticReader().read(src, build_settings(out=str(tmp_path)))


def test_docusaurus_detect_and_split(tmp_path):
    html = (
        '<div id="__docusaurus"><div class="theme-doc-markdown">'
        "<h1>A</h1><p>1</p><h2>B</h2><p>2</p></div></div>"
    )
    page = _page(tmp_path, html)
    imp = DocusaurusImporter()
    assert imp.detect(page) > 0
    out = imp.transform(page, PLAN)
    assert out.html_path.read_text().count("<section") >= 2


def test_bubble_relaxes_absolute_positioning(tmp_path):
    html = (
        '<body data-bb-id="1"><div style="position:absolute;top:0">'
        "<h1>Hi</h1></div></body>"
    )
    out = BubbleImporter().transform(_page(tmp_path, html), PLAN)
    assert "position: relative" in out.html_path.read_text().lower()
