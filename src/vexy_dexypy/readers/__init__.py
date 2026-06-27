# this_file: src/vexy_dexypy/readers/__init__.py
"""Stage 1 readers: Source -> PageDoc (spec/06, 07)."""

from __future__ import annotations

from loguru import logger

from ..model import PageDoc, Source, SourceKind
from ..settings import Settings
from .base import discover_readers
from .static import StaticReader


def read(source: Source, settings: Settings) -> PageDoc:
    """Pick the best-fit reader by confidence and run it.

    Local files always use the static reader (it copies + localizes). For URLs
    in the default `live` mode we navigate the page and keep its assets online
    (issue 103); in `localize` mode we pick the highest-confidence reader and the
    static reader can escalate to dynamic when the fetched body is client-rendered.
    """
    if source.kind == SourceKind.FILE:
        return StaticReader().read(source, settings)

    if settings.fetch_mode == "offline":
        from .offline import OfflineReader

        return OfflineReader().read(source, settings)

    if settings.fetch_mode == "live":
        from .live import LiveReader, playwright_available

        if playwright_available():
            return LiveReader().read(source, settings)
        logger.warning("live mode needs playwright; falling back to localize")

    readers = discover_readers()
    ranked = sorted(readers, key=lambda r: r.can_read(source), reverse=True)
    reader = ranked[0] if ranked else StaticReader()
    return reader.read(source, settings)
