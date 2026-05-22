# this_file: src/vexy_dexypy/exporters/prince.py
"""Prince exporter — opt-in premium engine, path-gated (spec/18)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..model import RenderJob
from ._subprocess import run_engine

# Path is read from VEXY_DEX_PRINCE_PATH or PATH; config wiring lands in the CLI.
_ENV_PATH = "VEXY_DEX_PRINCE_PATH"


def _prince_bin() -> str | None:
    return os.environ.get(_ENV_PATH) or shutil.which("prince")


class PrinceExporter:
    name = "prince"
    needs_js = True
    supports_paged_media = True

    def available(self) -> bool:
        return _prince_bin() is not None

    def export(self, job: RenderJob, out: Path) -> Path:
        binary = _prince_bin()
        if not binary:
            from ..errors import ExportError

            raise ExportError("prince not configured (set VEXY_DEX_PRINCE_PATH)")
        run_engine(
            [
                binary,
                str(job.html_path),
                "-o",
                str(out),
                f"--page-size={job.plan.stage_w}px {job.plan.stage_h}px",
            ],
            timeout=180,
        )
        return out
