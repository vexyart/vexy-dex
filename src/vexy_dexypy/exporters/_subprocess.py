# this_file: src/vexy_dexypy/exporters/_subprocess.py
"""Subprocess discipline shared by Node/CLI exporters (spec/16)."""

from __future__ import annotations

import subprocess

from ..errors import ExportError


def run_engine(cmd: list[str], *, timeout: int = 120) -> None:
    """Run an engine subprocess with a timeout and captured stderr surfaced."""
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=timeout)
    except FileNotFoundError as e:
        raise ExportError(f"engine not found: {cmd[0]} ({e})") from e
    except subprocess.TimeoutExpired as e:
        raise ExportError(f"{cmd[0]} timed out after {timeout}s") from e
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or b"").decode(errors="replace")[-500:]
        raise ExportError(f"{cmd[0]} failed: {stderr}") from e
