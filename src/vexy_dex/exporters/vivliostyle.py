# this_file: src/vexy_dex/exporters/vivliostyle.py
"""Vivliostyle CLI exporter — shell out only (AGPL boundary, spec/18)."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..model import RenderJob
from ._subprocess import run_engine


class VivliostyleExporter:
    name = "vivliostyle"
    needs_js = True
    supports_paged_media = True

    def available(self) -> bool:
        return shutil.which("vivliostyle") is not None

    def export(self, job: RenderJob, out: Path) -> Path:
        run_engine(
            [
                "vivliostyle",
                "build",
                str(job.html_path),
                "-s",
                f"{job.plan.stage_w}px,{job.plan.stage_h}px",
                "-o",
                str(out),
            ],
            timeout=180,
        )
        return out
