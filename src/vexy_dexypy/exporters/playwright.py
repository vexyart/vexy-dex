# this_file: src/vexy_dexypy/exporters/playwright.py
"""Playwright exporter — Chromium page.pdf at a locked stage size (spec/17)."""

from __future__ import annotations

from pathlib import Path

from ..errors import ExportError
from ..model import RenderJob


class PlaywrightExporter:
    name = "playwright"
    needs_js = True
    supports_paged_media = False

    def available(self) -> bool:
        try:
            import playwright.sync_api  # noqa: F401

            return True
        except Exception:
            return False

    def export(self, job: RenderJob, out: Path) -> Path:
        try:
            from playwright.sync_api import sync_playwright
        except Exception as e:  # pragma: no cover
            raise ExportError(f"playwright not installed: {e}") from e
        from .._browser import serving

        w, h = job.plan.stage_w, job.plan.stage_h
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page(viewport={"width": w, "height": h})
                with serving(page, job.html_path):
                    for css in job.extra_css:
                        page.add_style_tag(path=str(css))
                    # Faithful "PDF screenshot": screen media (not print), exact
                    # stage size, real backgrounds, zero margins. The page's own
                    # CSS supplies the look (see preexport.theme_css).
                    page.emulate_media(media="screen")
                    page.pdf(
                        path=str(out),
                        width=f"{w}px",
                        height=f"{h}px",
                        print_background=True,
                        prefer_css_page_size=True,
                        margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                    )
                browser.close()
        except Exception as e:
            raise ExportError(f"playwright export failed: {e}") from e
        return out
