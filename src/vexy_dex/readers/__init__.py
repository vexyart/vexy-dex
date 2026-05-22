# this_file: src/vexy_dex/readers/__init__.py
"""Stage 1 readers: Source -> PageDoc (spec/06, 07)."""

from __future__ import annotations

from ..model import PageDoc, Source, SourceKind
from ..settings import Settings
from .base import discover_readers
from .static import StaticReader


def read(source: Source, settings: Settings) -> PageDoc:
    """Pick the best-fit reader by confidence and run it.

    Local files always use the static reader (it copies + localizes). For URLs
    we try the highest-confidence reader; the static reader can escalate to
    dynamic internally when the fetched body looks client-rendered.
    """
    readers = discover_readers()
    if source.kind == SourceKind.FILE:
        return StaticReader().read(source, settings)
    ranked = sorted(readers, key=lambda r: r.can_read(source), reverse=True)
    reader = ranked[0] if ranked else StaticReader()
    return reader.read(source, settings)
