# this_file: tests/test_chassis.py
from __future__ import annotations

from vexy_dexypy import preexport
from vexy_dexypy.model import PageDoc, SlidePlan, Source, Strategy


def _page(tmp_path) -> PageDoc:
    work = tmp_path / "slug"
    norm = work / "normalized"
    norm.mkdir(parents=True)
    html = norm / "normalized.html"
    # Neutral IR: simple flat list of section slides
    html.write_text(
        "<html><head></head><body>"
        '<section class="slide">Slide A</section>'
        '<section class="slide">Slide B</section>'
        "</body></html>",
        encoding="utf-8",
    )
    return PageDoc(
        source=Source.parse("https://x.test/p"),
        html_path=html,
        asset_dir=work / "raw" / "assets",
    )


def test_chassis_divergence_guarantee(tmp_path):
    # Tests that the exact same neutral IR rendered through different strategy chassis
    # produces distinctly formatted documents (reveal, paged, impress, marp).
    
    page = _page(tmp_path)
    plan = SlidePlan(1920, 1080)
    
    # 1. Reveal Chassis
    reveal_strategy = Strategy("reveal", "reveal", chassis="reveal")
    reveal_job = preexport.prepare(page, plan, reveal_strategy)
    reveal_text = reveal_job.html_path.read_text(encoding="utf-8")
    assert "reveal/reveal.css" in reveal_text
    assert 'class="reveal"' in reveal_text
    assert 'class="slides"' in reveal_text
    assert "Reveal.initialize" in reveal_text
    assert reveal_job.html_path.name == "_input.html"

    # 2. Paged Chassis
    paged_strategy = Strategy("playwright", "playwright", chassis="paged")
    paged_job = preexport.prepare(page, plan, paged_strategy)
    paged_text = paged_job.html_path.read_text(encoding="utf-8")
    assert "@page" in paged_text
    assert "reveal/reveal.css" not in paged_text
    assert 'id="impress"' not in paged_text
    assert paged_job.html_path.name == "_input.html"

    # 3. Impress Chassis
    impress_strategy = Strategy("impress", "impress", chassis="impress")
    impress_job = preexport.prepare(page, plan, impress_strategy)
    impress_text = impress_job.html_path.read_text(encoding="utf-8")
    assert 'id="impress"' in impress_text
    assert 'class="slide step"' in impress_text
    assert "impress/impress.js" in impress_text
    assert "impress().init()" in impress_text
    assert impress_job.html_path.name == "_input.html"

    # 4. Marp Chassis
    marp_strategy = Strategy("marp", "marp", chassis="marp")
    marp_job = preexport.prepare(page, plan, marp_strategy)
    marp_text = marp_job.html_path.read_text(encoding="utf-8")
    assert "marp: true" in marp_text
    assert "theme: default" in marp_text
    assert "Slide A" in marp_text
    assert "Slide B" in marp_text
    assert marp_job.html_path.name == "_input.md"

    # Divergence verification: All output file contents are distinct
    assert reveal_text != paged_text
    assert reveal_text != impress_text
    assert paged_text != impress_text
    assert marp_text != reveal_text
