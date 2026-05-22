# this_file: src/vexy_dex/readers/base.py
"""Reader plugin contract + entry-point discovery (spec/06)."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Protocol, runtime_checkable

from loguru import logger

from ..model import PageDoc, Source
from ..settings import Settings


@runtime_checkable
class Reader(Protocol):
    name: str

    def can_read(self, source: Source) -> float: ...

    def read(self, source: Source, settings: Settings) -> PageDoc: ...


def discover_readers() -> list[Reader]:
    """Load reader plugins registered under the `vexy_dex.readers` group."""
    found: list[Reader] = []
    try:
        eps = entry_points(group="vexy_dex.readers")
    except TypeError:  # pragma: no cover - very old importlib API
        eps = entry_points().get("vexy_dex.readers", [])  # type: ignore[attr-defined]
    for ep in eps:
        try:
            found.append(ep.load()())
        except Exception as e:  # a broken/optional plugin must not kill discovery
            logger.debug("reader plugin {} unavailable: {}", ep.name, e)
    return found
