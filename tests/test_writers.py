# this_file: tests/test_writers.py
from __future__ import annotations

import pytest

from vexy_dex import writers


def _make_pdf(path, pages: int):
    weasyprint = pytest.importorskip("weasyprint")
    html = "".join(
        f'<div style="page-break-after:always">slide {i}</div>' for i in range(pages)
    )
    weasyprint.HTML(string=html).write_pdf(str(path))


def test_split_pdf_names_zero_padded(tmp_path):
    pytest.importorskip("weasyprint")
    pdf = tmp_path / "deck.pdf"
    _make_pdf(pdf, 3)
    out = tmp_path / "out"
    slides = writers.split_pdf(pdf, out, prefix="slide")
    assert [p.name for p in slides] == ["01-slide.pdf", "02-slide.pdf", "03-slide.pdf"]
    assert all(p.exists() for p in slides)


def test_build_preview_emits_index(tmp_path):
    pytest.importorskip("weasyprint")
    pdf = tmp_path / "deck.pdf"
    _make_pdf(pdf, 2)
    out = tmp_path / "out"
    slides = writers.split_pdf(pdf, out)
    index = writers.build_preview(slides, out)
    assert index.exists()
    assert "embed" in index.read_text()
