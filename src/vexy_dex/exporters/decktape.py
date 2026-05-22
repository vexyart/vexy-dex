# this_file: src/vexy_dex/exporters/decktape.py
"""DeckTape exporter — per-slide capture of the reveal.js deck (spec/19)."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..model import RenderJob
from ._subprocess import run_engine


class DeckTapeExporter:
    name = "decktape"
    needs_js = True
    supports_paged_media = False

    def available(self) -> bool:
        return shutil.which("decktape") is not None or shutil.which("npx") is not None

    def export(self, job: RenderJob, out: Path) -> Path:
        runner = ["decktape"] if shutil.which("decktape") else ["npx", "decktape"]
        run_engine(
            [
                *runner, "reveal",
                "--size", f"{job.plan.stage_w}x{job.plan.stage_h}",
                str(job.html_path), str(out),
            ],
            timeout=180,
        )
        return out
