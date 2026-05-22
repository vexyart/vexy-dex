# this_file: tests/test_orchestrator.py
"""Concurrency, caching, and the render verb (spec/21, 04). Playwright-gated."""

from __future__ import annotations

import pytest

from vexy_dexypy.model import Source
from vexy_dexypy.orchestrator import build, render_one
from vexy_dexypy.settings import build_settings


def _playwright_ok() -> bool:
    try:
        import playwright.sync_api  # noqa: F401

        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _playwright_ok(), reason="playwright unavailable")


def test_cache_hit_on_second_build(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "generic_article" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="reveal")
    first = build(src, settings)
    cache = tmp_path / src.slug / "_meta" / "cache"
    assert any(cache.glob("*.pdf")), "first build should populate the cache"
    second = build(src, settings)  # should hit cache, still succeed
    assert second[0].ok
    assert second[0].slide_count == first[0].slide_count


def test_render_verb_reuses_sidecars(tmp_path, fixtures):
    src = Source.parse(str(fixtures / "mkdocs_sample" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="reveal")
    build(src, settings)
    result = render_one(src.slug, "reveal", settings)
    assert result.ok, result.error
    assert result.slide_count >= 2


def test_failed_strategy_isolated(tmp_path, fixtures, monkeypatch):
    """A raising exporter yields a failed DeckResult, not an aborted run."""
    src = Source.parse(str(fixtures / "generic_article" / "index.html"))
    settings = build_settings(out=str(tmp_path), strategies="reveal")
    import vexy_dexypy.exporters.reveal as rv

    def boom(self, job, out):
        raise RuntimeError("kaboom")

    monkeypatch.setattr(rv.RevealExporter, "export", boom)
    results = build(src, settings)
    assert len(results) == 1
    assert results[0].ok is False
    assert "kaboom" in (results[0].error or "")
