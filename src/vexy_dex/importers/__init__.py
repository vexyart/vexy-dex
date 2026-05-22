# this_file: src/vexy_dex/importers/__init__.py
"""Stage 3 importers: framework-aware DOM normalization (spec/11-14)."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Protocol, runtime_checkable

from loguru import logger

from ..model import PageDoc, SlidePlan


@runtime_checkable
class Importer(Protocol):
    name: str

    def detect(self, page: PageDoc) -> float: ...

    def transform(self, page: PageDoc, plan: SlidePlan) -> PageDoc: ...


def discover_importers() -> dict[str, Importer]:
    out: dict[str, Importer] = {}
    try:
        eps = entry_points(group="vexy_dex.importers")
    except TypeError:  # pragma: no cover
        eps = entry_points().get("vexy_dex.importers", [])  # type: ignore[attr-defined]
    for ep in eps:
        try:
            inst = ep.load()()
            out[inst.name] = inst
        except Exception as e:
            logger.debug("importer plugin {} unavailable: {}", ep.name, e)
    return out


def pick_importer(page: PageDoc) -> Importer:
    """Choose by framework label, falling back to generic (spec/11)."""
    importers = discover_importers()
    if page.framework in importers:
        return importers[page.framework]
    if "generic" in importers:
        return importers["generic"]
    # last resort: highest detect() score
    ranked = sorted(importers.values(), key=lambda i: i.detect(page), reverse=True)
    if not ranked:
        raise RuntimeError("no importers registered")
    return ranked[0]
