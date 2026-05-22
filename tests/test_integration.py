# this_file: tests/test_integration.py
"""Full pipeline on local fixtures for one strategy (spec/23).

Runs offline. WeasyPrint needs native libs (pango); skip if it can't import.
"""

from __future__ import annotations

import pytest

from vexy_dex.model import Source
from vexy_dex.orchestrator import build
from vexy_dex.settings import build_settings


def _weasyprint_ok() -> bool:
    try:
        import weasyprint  # noqa: F401

        weasyprint.HTML(string="<p>x</p>").write_pdf()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _weasyprint_ok(), reason="weasyprint native libs unavailable"
)


def test_build_generic_fixture_produces_slides(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "generic_article" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="weasyprint")
    results = build(src, settings)
    assert len(results) == 1
    r = results[0]
    assert r.ok, r.error
    assert r.slide_count >= 3, "article should split into several slides"
    assert (r.out_dir / "index.html").exists()
    assert all(p.exists() for p in r.slide_pdfs)


def test_build_mkdocs_fixture_classified_and_rendered(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "mkdocs_sample" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="weasyprint")
    results = build(src, settings)
    assert results[0].ok, results[0].error
    assert results[0].slide_count >= 2
