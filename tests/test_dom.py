# this_file: tests/test_dom.py
from __future__ import annotations

from vexy_dex import dom


def test_luminance_white_is_light_black_is_dark():
    assert dom.luminance("#ffffff") > 0.9
    assert dom.luminance("#000000") < 0.1
    assert dom.bg_class("#ffffff") == "slide-light-bg"
    assert dom.bg_class("#101820") == "slide-dark-bg"


def test_luminance_unknown_defaults_light():
    assert dom.luminance("not-a-color") == 1.0


def test_luminance_rgb_form():
    assert dom.bg_class("rgb(255,255,255)") == "slide-light-bg"


def test_split_by_heading_groups_under_h2():
    soup = dom.parse(
        "<div><h1>A</h1><p>1</p><h2>B</h2><p>2</p><h2>C</h2><p>3</p></div>"
    )
    sections = dom.split_by_heading(soup.div, levels=("h1", "h2"))
    assert len(sections) == 3, "h1 + two h2 => three slides"


def test_wrap_reveal_produces_chassis_and_marks_idempotent():
    soup = dom.parse("<section><h1>x</h1></section>")
    html = dom.wrap_reveal([soup.section])
    assert "reveal" in html and "slides" in html
    assert dom.already_reveal(html)


def test_drop_chrome_removes_selectors():
    soup = dom.parse("<body><nav>x</nav><article>keep</article></body>")
    dom.drop_chrome(soup, ["nav"])
    assert soup.find("nav") is None
    assert soup.find("article") is not None
