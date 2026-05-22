# this_file: tests/test_preexport.py
"""Pre-exporter: paged CSS vs reveal bundling (spec/15)."""

from __future__ import annotations

from vexy_dex import preexport
from vexy_dex.model import PageDoc, SlidePlan, Source, Strategy


def _page(tmp_path) -> PageDoc:
    work = tmp_path / "slug"
    norm = work / "normalized"
    norm.mkdir(parents=True)
    html = norm / "normalized.html"
    html.write_text(
        '<html><head></head><body><div class="reveal"><div class="slides">'
        "<section>a</section></div></div></body></html>",
        encoding="utf-8",
    )
    return PageDoc(
        source=Source.parse("https://x.test/p"),
        html_path=html,
        asset_dir=work / "raw" / "assets",
    )


def test_paged_strategy_injects_page_css(tmp_path):
    job = preexport.prepare(
        _page(tmp_path), SlidePlan(1920, 1080), Strategy("vivliostyle", "vivliostyle")
    )
    text = job.html_path.read_text()
    assert "@page" in text and "1920px 1080px" in text
    assert job.extra_css and job.extra_css[0].exists()


def test_reveal_strategy_bundles_revealjs(tmp_path):
    job = preexport.prepare(
        _page(tmp_path), SlidePlan(1280, 720), Strategy("reveal", "reveal")
    )
    text = job.html_path.read_text()
    assert "reveal/reveal.js" in text, "reveal.js script should be injected"
    assert "Reveal.initialize" in text and "width:1280" in text
    # Slides are for print: no nav controls, progress, slide numbers or fragments.
    assert "controls:false" in text and "fragments:false" in text
    bundle = job.html_path.parent / "reveal"
    assert (bundle / "reveal.js").exists() and (bundle / "reveal.css").exists()
