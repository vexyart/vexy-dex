# this_file: src/vexy_dexypy/readers/offline.py
"""Offline reader: shell out to a single-file archiver (spec/06, 07 Tier-3).

`fetch_mode="offline"` produces a fully self-contained `index.html` by running an
external archiver — `single-file` (SingleFile CLI) or `monolith` — which inlines
HTML, CSS, JS, fonts and images into one document. This is the opposite end from
`live`: maximum portability instead of live assets. The archivers are external
tools (like Vivliostyle/Prince); when the chosen one is absent we degrade to the
`localize` path so a run never hard-fails on a missing optional binary.

Local-file sources have nothing to archive online, so they delegate to static.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from loguru import logger

from ..errors import ReadError
from ..model import PageDoc, Source, SourceKind
from ..settings import Settings
from .localize import content_hash
from .static import StaticReader, _extract_meta


def _archive_cmd(tool: str, url: str, out: Path) -> list[str]:
    """Command line for the chosen archiver writing a self-contained file."""
    if tool == "monolith":
        return ["monolith", url, "-o", str(out)]
    # SingleFile CLI: `single-file <url> <output>`.
    return ["single-file", url, str(out)]


class OfflineReader:
    name = "offline"

    def can_read(self, source: Source) -> float:
        # Dispatched explicitly by `Settings.fetch_mode`, never confidence-ranked.
        return 0.0

    def read(self, source: Source, settings: Settings) -> PageDoc:
        if source.kind == SourceKind.FILE:
            return StaticReader().read(source, settings)

        tool = settings.offline_tool or "single-file"
        if shutil.which(tool) is None:
            logger.warning(
                "offline tool {!r} not found on PATH; falling back to localize", tool
            )
            return StaticReader().read(source, settings)

        work = settings.out_dir / source.slug
        raw_dir = work / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        asset_dir = raw_dir / "assets"  # everything is inlined; no separate assets
        html_path = raw_dir / "index.html"

        cmd = _archive_cmd(tool, source.raw, html_path)
        logger.info("offline: archiving {} via {}", source.raw, tool)
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired as e:
            raise ReadError(f"{tool} timed out after 120s on {source.raw}") from e
        except subprocess.CalledProcessError as e:
            stderr = (e.stderr or b"").decode(errors="replace")[-500:]
            raise ReadError(f"{tool} failed on {source.raw}: {stderr}") from e

        if not html_path.is_file() or html_path.stat().st_size == 0:
            raise ReadError(f"{tool} produced no output for {source.raw}")

        live_html = html_path.read_text(encoding="utf-8", errors="replace")
        page = PageDoc(source=source, html_path=html_path, asset_dir=asset_dir)
        page.content_hash = content_hash(html_path, asset_dir)
        page.meta = _extract_meta(live_html)
        page.meta["fetch_mode"] = "offline"
        page.meta["offline_tool"] = tool
        return page
