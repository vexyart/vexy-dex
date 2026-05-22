# this_file: src/vexy_dexypy/exporters/impress.py
"""Impress exporter — drive impress.js via Playwright, one PDF page per slide (spec/19)."""

from __future__ import annotations

import io
from pathlib import Path

from ..errors import ExportError
from ..model import RenderJob


class ImpressExporter:
    name = "impress"
    needs_js = True
    supports_paged_media = False

    def available(self) -> bool:
        try:
            import playwright.sync_api  # noqa: F401
            import pypdf  # noqa: F401

            return True
        except Exception:
            return False

    def export(self, job: RenderJob, out: Path) -> Path:
        try:
            from playwright.sync_api import sync_playwright
            from pypdf import PdfReader, PdfWriter
        except Exception as e:  # pragma: no cover
            raise ExportError(f"impress deps missing: {e}") from e
        from .._browser import serving

        w, h = job.plan.stage_w, job.plan.stage_h
        try:
            writer = PdfWriter()
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": w, "height": h})
                with serving(page, job.html_path):
                    page.wait_for_function(
                        "() => window.impress && document.querySelectorAll('#impress .step').length > 0",
                        timeout=30_000,
                    )
                    page.emulate_media(media="screen")

                    count = int(
                        page.evaluate(
                            "document.querySelectorAll('#impress .step').length"
                        )
                    )
                    page.evaluate("impress().goto(0)")
                    page.wait_for_timeout(200)  # let the step transition settle

                    for i in range(count):
                        buf = page.pdf(
                            width=f"{w}px",
                            height=f"{h}px",
                            print_background=True,
                            page_ranges="1",
                        )
                        writer.append(PdfReader(io.BytesIO(buf)))
                        if i < count - 1:
                            page.evaluate("impress().next()")
                            page.wait_for_timeout(100)  # let the transition settle
                browser.close()

            with out.open("wb") as f:
                writer.write(f)
        except Exception as e:
            raise ExportError(f"impress export failed: {e}") from e
        return out
