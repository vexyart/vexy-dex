# this_file: src/vexy_dexypy/exporters/marp.py
"""Marp exporter — shell out to Marp CLI for slide rendering (spec/16)."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..model import RenderJob
from ._subprocess import run_engine


class MarpExporter:
    name = "marp"
    needs_js = False
    supports_paged_media = True

    def available(self) -> bool:
        return shutil.which("marp") is not None or shutil.which("npx") is not None

    def export(self, job: RenderJob, out: Path) -> Path:
        cmd = ["marp"] if shutil.which("marp") else ["npx", "-y", "@marp-team/marp-cli"]
        cmd += [
            "--pdf",
            str(job.html_path),
            "-o",
            str(out),
            "--allow-local-files",
            "--no-stdin",
        ]
        run_engine(cmd, timeout=120)
        return out
