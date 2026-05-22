# this_file: tests/test_orchestrator.py
"""Concurrency, caching, and the render verb (spec/21, 04). WeasyPrint-gated."""

from __future__ import annotations

import pytest

from vexy_dex.model import Source
from vexy_dex.orchestrator import build, render_one
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


def test_cache_hit_on_second_build(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "generic_article" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="weasyprint")
    first = build(src, settings)
    cache = tmp_path / src.slug / "_meta" / "cache"
    assert any(cache.glob("*.pdf")), "first build should populate the cache"
    second = build(src, settings)  # should hit cache, still succeed
    assert second[0].ok
    assert second[0].slide_count == first[0].slide_count


def test_render_verb_reuses_sidecars(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "mkdocs_sample" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="weasyprint")
    build(src, settings)
    result = render_one(src.slug, "weasyprint", settings)
    assert result.ok, result.error
    assert result.slide_count >= 2


def test_failed_strategy_isolated(tmp_path, fixtures, monkeypatch):
    """A raising exporter yields a failed DeckResult, not an aborted run."""
    src = Source.parse(str(fixtures / "generic_article" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="weasyprint")
    import vexy_dex.exporters.weasyprint as wp

    def boom(self, job, out):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(wp.WeasyPrintExporter, "export", boom)
    results = build(src, settings)
    assert len(results) == 1
    assert results[0].ok is False
    assert "kaboom" in (results[0].error or "")
