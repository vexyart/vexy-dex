# this_file: tests/test_classify.py
from __future__ import annotations

from vexy_dex.classify import classify


def test_classify_when_webflow_markers_then_webflow():
    html = '<html data-wf-page="x" class="w-mod-js"><body data-w-id="1"></body></html>'
    assert classify(html).framework == "webflow", "wf markers should classify webflow"


def test_classify_when_mkdocs_generator_then_mkdocs():
    html = '<meta name="generator" content="mkdocs-material 9.5"><div class="md-content">'
    c = classify(html, {"generator": "mkdocs-material 9.5"})
    assert c.framework == "mkdocs-material"
    assert c.strategy_order[0] == "weasyprint", "docs should prefer weasyprint first"


def test_classify_when_nothing_matches_then_generic():
    c = classify("<html><body><p>plain</p></body></html>")
    assert c.framework == "generic"
    assert c.confidence == 0.0


def test_classify_confidence_grows_with_hits():
    one = classify('<div class="md-content">')
    many = classify('<div class="md-content md-typeset" data-md-component="x">')
    assert many.confidence > one.confidence
