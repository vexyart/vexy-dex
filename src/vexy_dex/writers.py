# this_file: src/vexy_dex/writers.py
"""Stage 6 writers: split, optional SVG, reveal preview (spec/20)."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from .model import DeckResult, RenderJob, Strategy

_REVEAL_PREVIEW = """\
<!doctype html><html><head><meta charset="utf-8">
<style>body{{margin:0;background:#222}}
.s{{display:block;width:100%;max-width:1280px;margin:8px auto;background:#fff}}</style>
</head><body>
{slides}
</body></html>
"""


def split_pdf(pdf: Path, out_dir: Path, prefix: str = "slide") -> list[Path]:
    """Split a multi-page PDF into zero-padded single-page files (spec/20)."""
    from pypdf import PdfReader, PdfWriter

    out_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(pdf))
    paths: list[Path] = []
    for i, page in enumerate(reader.pages, 1):
        writer = PdfWriter()
        writer.add_page(page)
        target = out_dir / f"{i:02d}-{prefix}.pdf"
        with target.open("wb") as fh:
            writer.write(fh)
        paths.append(target)
    return paths


def to_svgs(slide_pdfs: list[Path], out_dir: Path) -> list[Path]:
    """Convert each slide PDF to SVG via vexy-pdfsvgpy (spec/20)."""
    try:
        from vexy_pdfsvgpy import pdf_to_svg
    except Exception as e:
        logger.warning("svg requested but vexy-pdfsvgpy unavailable: {}", e)
        return []
    svgs: list[Path] = []
    for pdf in slide_pdfs:
        svg = out_dir / (pdf.stem + ".svg")
        try:
            pdf_to_svg(str(pdf), str(svg), page=1)
            svgs.append(svg)
        except Exception as e:
            logger.warning("svg conversion failed for {}: {}", pdf.name, e)
    return svgs


def build_preview(slide_files: list[Path], out_dir: Path) -> Path:
    """Emit a simple per-strategy preview index of the slides (spec/20)."""
    tags = []
    for f in slide_files:
        if f.suffix == ".svg":
            tags.append(f'<img class="s" src="{f.name}">')
        else:
            tags.append(f'<embed class="s" type="application/pdf" src="{f.name}">')
    index = out_dir / "index.html"
    index.write_text(_REVEAL_PREVIEW.format(slides="\n".join(tags)), encoding="utf-8")
    return index


def write_deck(job: RenderJob, pdf: Path, *, svg: bool) -> DeckResult:
    """Split + optional SVG + preview for one strategy, isolating failures."""
    strat: Strategy = job.strategy
    out_dir = pdf.parent
    try:
        slides = split_pdf(pdf, out_dir, prefix="slide")
        svgs = to_svgs(slides, out_dir) if svg else []
        preview = build_preview(svgs or slides, out_dir)
        return DeckResult(
            strategy=strat,
            out_dir=out_dir,
            slide_pdfs=slides,
            slide_svgs=svgs,
            index_html=preview,
            ok=True,
        )
    except Exception as e:
        msg = str(e)
        logger.warning("writer failed for {}: {}", strat.name, msg)
        return DeckResult(strategy=strat, out_dir=out_dir, ok=False, error=msg)
