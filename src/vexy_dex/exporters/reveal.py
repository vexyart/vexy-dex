# this_file: src/vexy_dex/exporters/reveal.py
"""Reveal exporter — drive reveal.js via Playwright, one PDF page per slide (spec/19).

DeckTape's reveal capture is ~30 lines of Reveal API calls; we already ship
Playwright and pypdf, so we reimplement it natively and need no Node/decktape
toolchain. Playwright steps the deck (`Reveal.next`), renders each slide with
`page.pdf`, and pypdf merges the single-page buffers into the strategy PDF.
"""

from __future__ import annotations

import io
from pathlib import Path

from ..errors import ExportError
from ..model import RenderJob

# The deck reports readiness once Reveal has laid out the slides.
_READY = "() => window.Reveal && Reveal.getTotalSlides && Reveal.getTotalSlides() > 0"


class RevealExporter:
    name = "reveal"
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
            raise ExportError(f"reveal deps missing: {e}") from e
        from .._browser import serving

        w, h = job.plan.stage_w, job.plan.stage_h
        try:
            writer = PdfWriter()
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": w, "height": h})
                with serving(page, job.html_path):
                    page.wait_for_function(_READY, timeout=30_000)
                    page.emulate_media(media="screen")

                    count = int(page.evaluate("Reveal.getTotalSlides()"))
                    page.evaluate("Reveal.slide(0, 0)")
                    for i in range(count):
                        buf = page.pdf(
                            width=f"{w}px",
                            height=f"{h}px",
                            print_background=True,
                            page_ranges="1",
                        )
                        writer.append(PdfReader(io.BytesIO(buf)))
                        if i < count - 1:
                            page.evaluate("Reveal.next()")
                            page.wait_for_timeout(80)  # let the slide settle
                browser.close()

            with out.open("wb") as f:
                writer.write(f)
        except Exception as e:
            raise ExportError(f"reveal export failed: {e}") from e
        return out
