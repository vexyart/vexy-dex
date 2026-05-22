# this_file: src/vexy_dex/exporters/weasyprint.py
"""WeasyPrint exporter — pure-Python CSS paged media, no JS (spec/18)."""

from __future__ import annotations

from pathlib import Path

from ..errors import ExportError
from ..model import RenderJob


class WeasyPrintExporter:
    name = "weasyprint"
    needs_js = False
    supports_paged_media = True

    def available(self) -> bool:
        try:
            import weasyprint  # noqa: F401

            return True
        except Exception:
            return False

    def export(self, job: RenderJob, out: Path) -> Path:
        try:
            from weasyprint import CSS, HTML
        except Exception as e:  # pragma: no cover
            raise ExportError(f"weasyprint not installed: {e}") from e
        try:
            HTML(filename=str(job.html_path)).write_pdf(
                str(out),
                stylesheets=[CSS(filename=str(c)) for c in job.extra_css],
            )
        except Exception as e:
            raise ExportError(f"weasyprint failed: {e}") from e
        return out
