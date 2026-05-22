# this_file: tests/test_writers.py
from __future__ import annotations

from vexy_dex import writers


def _make_pdf(path, pages: int):
    from pypdf import PdfWriter

    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=1920, height=1080)
    with path.open("wb") as f:
        w.write(f)


def test_split_pdf_names_zero_padded(tmp_path):
    pdf = tmp_path / "deck.pdf"
    _make_pdf(pdf, 3)
    out = tmp_path / "out"
    slides = writers.split_pdf(pdf, out, prefix="slide")
    assert [p.name for p in slides] == ["01-slide.pdf", "02-slide.pdf", "03-slide.pdf"]
    assert all(p.exists() for p in slides)


def test_build_preview_emits_index(tmp_path):
    pdf = tmp_path / "deck.pdf"
    _make_pdf(pdf, 2)
    out = tmp_path / "out"
    slides = writers.split_pdf(pdf, out)
    index = writers.build_preview(slides, out)
    assert index.exists()
    assert "embed" in index.read_text()
