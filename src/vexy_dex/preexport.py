# this_file: src/vexy_dex/preexport.py
"""Stage 4 pre-exporters: paged-media CSS + reveal scaffolding (spec/15)."""

from __future__ import annotations

from importlib.resources import files

from .model import PageDoc, RenderJob, SlidePlan, Strategy

# Strategies that consume a full reveal.js deck rather than a paged document.
_REVEAL_STRATEGIES = {"reveal"}

_PAGED_CSS = """\
@page {{ size: {w}px {h}px; margin: 0; }}
html, body {{ margin: 0; padding: 0; }}
section, .slide {{
  break-after: page;
  page-break-after: always;
  width: {w}px; height: {h}px;
  overflow: hidden; box-sizing: border-box;
}}
section h2 {{ break-before: page; page-break-before: always; }}
"""

# Minimal neutral theme for the layout vocabulary (spec/15). Kept small on purpose.
_THEME_CSS = """\
.slide { padding: 4%; font-family: system-ui, sans-serif; }
.slide-light-bg { background: #fff; color: #111; }
.slide-dark-bg { background: #111; color: #f5f5f5; }
.slide img { max-width: 100%; height: auto; }
.slide-image-cover img { width: 100%; height: 100%; object-fit: cover; }
"""


def paged_css(stage_w: int, stage_h: int) -> str:
    return _PAGED_CSS.format(w=stage_w, h=stage_h)


def _bundle_reveal(html: str, strat_dir, plan: SlidePlan) -> str:
    """Turn normalized reveal HTML into a self-contained reveal.js deck (spec/15).

    Copies the vendored reveal.js 5.1 dist next to the input and injects the
    stylesheet/script with a stage-sized `Reveal.initialize`, so the reveal
    exporter (and the preview) get a real, offline deck.
    """
    dst = strat_dir / "reveal"
    dst.mkdir(parents=True, exist_ok=True)
    src = files("vexy_dex").joinpath("assets", "reveal")
    for name in ("reveal.css", "reveal.js", "theme.css"):
        (dst / name).write_bytes((src / name).read_bytes())

    head = (
        '<link rel="stylesheet" href="reveal/reveal.css">'
        '<link rel="stylesheet" href="reveal/theme.css">'
        f"<style>{_THEME_CSS}</style>"
        # Belt-and-braces: hide any reveal UI chrome even if a plugin re-adds it.
        "<style>.reveal .controls,.reveal .progress,.reveal .slide-number,"
        ".reveal .pause-overlay,.reveal .speaker-notes{display:none!important}</style>"
    )
    tail = (
        '<script src="reveal/reveal.js"></script>'
        f"<script>Reveal.initialize({{width:{plan.stage_w},height:{plan.stage_h},"
        "margin:0,controls:false,progress:false,slideNumber:false,fragments:false,"
        "controlsTutorial:false,hash:false,help:false,transition:'none'});</script>"
    )
    if "</head>" in html:
        html = html.replace("</head>", head + "</head>", 1)
    else:
        html = head + html
    if "</body>" in html:
        html = html.replace("</body>", tail + "</body>", 1)
    else:
        html = html + tail
    return html


def prepare(page: PageDoc, plan: SlidePlan, strategy: Strategy) -> RenderJob:
    """Build an engine-ready RenderJob for one strategy (spec/15).

    All current engines consume the normalized reveal HTML plus a paged-media
    stylesheet; the stylesheet locks every engine to the same stage geometry.
    """
    work = page.html_path.parent.parent  # out/<slug>/
    strat_dir = work / strategy.name
    strat_dir.mkdir(parents=True, exist_ok=True)

    css_path = strat_dir / "_paged.css"
    css_path.write_text(paged_css(plan.stage_w, plan.stage_h), encoding="utf-8")
    theme_path = strat_dir / "_theme.css"
    theme_path.write_text(_THEME_CSS, encoding="utf-8")

    html = page.html_path.read_text(encoding="utf-8")
    if strategy.name in _REVEAL_STRATEGIES:
        html = _bundle_reveal(html, strat_dir, plan)
    else:
        # Inline theme + paged CSS so single-file engines render it offline.
        inject = f"<style>{_THEME_CSS}\n{paged_css(plan.stage_w, plan.stage_h)}</style>"
        if "</head>" in html:
            html = html.replace("</head>", inject + "</head>", 1)
        else:
            html = inject + html
    job_html = strat_dir / "_input.html"
    job_html.write_text(html, encoding="utf-8")

    return RenderJob(
        page=page,
        plan=plan,
        strategy=strategy,
        html_path=job_html,
        extra_css=[css_path],
    )
