# this_file: tests/test_paginate.py
from __future__ import annotations

from vexy_dex.paginate import plan_breaks


def _el(tag, top, height, visible=True):
    return {"tag": tag, "top": top, "height": height, "visible": visible}


def test_plan_breaks_when_semantic_heading_then_break_at_top():
    els = [
        _el("h1", 0, 200),
        _el("p", 220, 100),
        _el("h2", 500, 80),  # within the stage but past 40% => semantic break
    ]
    plan = plan_breaks(els, 1920, 1080)
    assert any(b.reason == "h2" for b in plan.breaks), "h2 should start a slide"
    assert any(round(b.y) == 500 for b in plan.breaks)


def test_plan_breaks_when_giant_block_then_screen_splits():
    els = [_el("img", 0, 3000)]  # ~3 screens at 1080
    plan = plan_breaks(els, 1920, 1080)
    assert len([b for b in plan.breaks if b.reason == "overflow"]) >= 2


def test_plan_breaks_invisible_ignored():
    els = [_el("section", 2000, 100, visible=False)]
    plan = plan_breaks(els, 1920, 1080)
    assert plan.breaks == []


def test_plan_breaks_are_sorted_and_deduped():
    els = [_el("section", 1500, 50), _el("h2", 1500, 50), _el("section", 3200, 50)]
    plan = plan_breaks(els, 1920, 1080)
    ys = [b.y for b in plan.breaks]
    assert ys == sorted(ys)
    assert len(ys) == len(set(round(y) for y in ys))


def test_empty_elements_then_single_slide():
    plan = plan_breaks([], 1920, 1080)
    assert plan.breaks == []
    assert plan.slide_count == 1


def test_plan_breaks_golden():
    """Regression snapshot: a fixed layout must yield a stable plan (spec/23)."""
    els = [
        _el("h1", 0, 150),
        _el("section", 600, 400),    # semantic start past 40% of stage
        _el("img", 1100, 3300),      # ~3 screens => two interior overflow breaks
    ]
    plan = plan_breaks(els, 1920, 1080)
    got = [(round(b.y), b.reason) for b in plan.breaks]
    expected = [(600, "section"), (2180, "overflow"), (3260, "overflow")]
    assert got == expected, f"plan drifted: {got}"
