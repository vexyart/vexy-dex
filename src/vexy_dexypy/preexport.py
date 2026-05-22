# this_file: src/vexy_dexypy/preexport.py
"""Stage 4 pre-exporters: paged-media CSS + reveal scaffolding (spec/15)."""

from __future__ import annotations

from importlib.resources import files

from . import dom
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
.w-webflow-badge { display: none !important; }  /* "Made in Webflow" badge */
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
    src = files("vexy_dexypy").joinpath("assets", "reveal")
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


def _bundle_impress(html: str, strat_dir, plan: SlidePlan) -> str:
    """Turn neutral HTML into a self-contained impress.js deck (spec/15)."""
    dst = strat_dir / "impress"
    dst.mkdir(parents=True, exist_ok=True)
    src = files("vexy_dexypy").joinpath("assets", "impress")
    for name in ("impress.js",):
        (dst / name).write_bytes((src / name).read_bytes())

    soup = dom.parse(html)
    head = soup.head or soup.new_tag("head")

    style_text = (
        f"{_THEME_CSS}\n"
        ".hint { display: none !important; }\n"
        f"#impress .step {{ width: {plan.stage_w}px; height: {plan.stage_h}px; box-sizing: border-box; transition: none !important; }}\n"
        "body { overflow: hidden; }\n"
    )
    style_tag = soup.new_tag("style")
    style_tag.string = style_text
    head.append(style_tag)

    body = soup.body or soup.new_tag("body")
    sections = body.find_all("section", recursive=False)

    impress_div = soup.new_tag("div", id="impress")
    impress_div["data-transition-duration"] = "0"

    for i, sec in enumerate(sections):
        sec.extract()
        classes = sec.get("class") or []
        if "step" not in classes:
            classes.append("step")
        sec["class"] = classes
        sec["data-x"] = str(i * (plan.stage_w + 400))
        sec["data-y"] = "0"
        impress_div.append(sec)

    body.append(impress_div)

    js_script = soup.new_tag("script", src="impress/impress.js")
    init_script = soup.new_tag("script")
    init_script.string = "impress().init();"
    body.append(js_script)
    body.append(init_script)

    return str(soup)


def _translate_to_marp(html: str, plan: SlidePlan) -> str:
    """Translate neutral HTML into Marp Markdown format (spec/16)."""
    md = [
        "---",
        "marp: true",
        "theme: default",
        "html: true",
        "---",
        "",
    ]

    soup = dom.parse(html)

    # Gather head links and styles
    head_styles_str = ""
    for tag in dom.head_styles(soup):
        head_styles_str += str(tag) + "\n"

    # Standard theme + section sizing CSS for Marp
    theme_style = (
        f"<style>{_THEME_CSS}\n"
        f"section {{ width: {plan.stage_w}px; height: {plan.stage_h}px; padding: 0; margin: 0; box-sizing: border-box; }}\n"
        "</style>\n"
    )

    first_slide_header = head_styles_str + theme_style

    sections = soup.body.find_all("section", recursive=False) if soup.body else []

    slide_mds = []
    for i, sec in enumerate(sections):
        cls = " ".join(sec.get("class") or [])
        bg = sec.get("data-background-color") or ""

        directives = []
        if cls:
            directives.append(f"<!-- _class: {cls} -->")
        if bg:
            directives.append(f"<!-- _backgroundColor: {bg} -->")

        inner_html = "".join(str(c) for c in sec.contents)
        slide_content = "\n".join(directives) + "\n" + inner_html
        if i == 0:
            slide_content = first_slide_header + slide_content
        slide_mds.append(slide_content)

    md.append("\n\n---\n\n".join(slide_mds))
    return "\n".join(md)


def prepare(page: PageDoc, plan: SlidePlan, strategy: Strategy) -> RenderJob:
    """Build an engine-ready RenderJob for one strategy (spec/15)."""
    work = page.html_path.parent.parent  # out/<slug>/
    strat_dir = work / strategy.name
    strat_dir.mkdir(parents=True, exist_ok=True)

    css_path = strat_dir / "_paged.css"
    css_path.write_text(paged_css(plan.stage_w, plan.stage_h), encoding="utf-8")
    theme_path = strat_dir / "_theme.css"
    theme_path.write_text(_THEME_CSS, encoding="utf-8")

    html = page.html_path.read_text(encoding="utf-8")

    chassis = strategy.chassis or "reveal"

    # We parse the neutral html to extract sections and head nodes
    soup = dom.parse(html)
    head_nodes = dom.head_styles(soup)
    sections = [
        sec
        for sec in (
            soup.body.find_all("section", recursive=False) if soup.body else []
        )
    ]

    if chassis == "reveal":
        reveal_html = dom.wrap_reveal(sections, head_nodes)
        html = _bundle_reveal(reveal_html, strat_dir, plan)
        job_file = strat_dir / "_input.html"
        job_file.write_text(html, encoding="utf-8")
    elif chassis == "impress":
        html = _bundle_impress(html, strat_dir, plan)
        job_file = strat_dir / "_input.html"
        job_file.write_text(html, encoding="utf-8")
    elif chassis == "marp":
        html = _translate_to_marp(html, plan)
        job_file = strat_dir / "_input.md"
        job_file.write_text(html, encoding="utf-8")
    else:  # "paged" chassis
        # Inline theme + paged CSS so single-file engines render it offline.
        inject = (
            f"<style>{_THEME_CSS}\n{paged_css(plan.stage_w, plan.stage_h)}</style>"
        )
        if "</head>" in html:
            html = html.replace("</head>", inject + "</head>", 1)
        else:
            html = inject + html
        job_file = strat_dir / "_input.html"
        job_file.write_text(html, encoding="utf-8")

    return RenderJob(
        page=page,
        plan=plan,
        strategy=strategy,
        html_path=job_file,
        extra_css=[css_path],
    )

