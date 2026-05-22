# this_file: tests/test_integration.py
"""Full pipeline on local fixtures for one strategy (spec/23).

Runs offline. The reveal exporter needs Playwright; skip if it can't import.
"""

from __future__ import annotations

import pytest

from vexy_dex.model import Source
from vexy_dex.orchestrator import build
from vexy_dex.settings import build_settings


def _playwright_ok() -> bool:
    try:
        import playwright.sync_api  # noqa: F401

        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _playwright_ok(), reason="playwright unavailable")


def test_build_generic_fixture_produces_slides(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "generic_article" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="reveal")
    results = build(src, settings)
    assert len(results) == 1
    r = results[0]
    assert r.ok, r.error
    assert r.slide_count >= 3, "article should split into several slides"
    assert (r.out_dir / "index.html").exists()
    assert all(p.exists() for p in r.slide_pdfs)


def test_build_mkdocs_fixture_classified_and_rendered(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "mkdocs_sample" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="reveal")
    results = build(src, settings)
    assert results[0].ok, results[0].error
    assert results[0].slide_count >= 2
