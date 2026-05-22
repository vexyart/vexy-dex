# this_file: src/vexy_dexypy/exporters/__init__.py
"""Stage 5 exporters: RenderJob -> multi-page PDF (spec/16-19)."""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path
from typing import Protocol, runtime_checkable

from loguru import logger

from ..model import RenderJob


@runtime_checkable
class Exporter(Protocol):
    name: str
    needs_js: bool
    supports_paged_media: bool

    def available(self) -> bool: ...

    def export(self, job: RenderJob, out: Path) -> Path: ...


def discover_exporters() -> dict[str, Exporter]:
    out: dict[str, Exporter] = {}
    try:
        eps = entry_points(group="vexy_dexypy.exporters")
    except TypeError:  # pragma: no cover
        eps = entry_points().get("vexy_dexypy.exporters", [])  # type: ignore[attr-defined]
    for ep in eps:
        try:
            inst = ep.load()()
            out[inst.name] = inst
        except Exception as e:
            logger.debug("exporter plugin {} unavailable: {}", ep.name, e)
    return out


def select_exporters(
    requested: tuple[str, ...], order: tuple[str, ...]
) -> list[Exporter]:
    """Resolve the requested strategy names into available exporters (spec/16).

    `requested` is authoritative. 'all' = every discovered exporter whose deps
    resolve, ordered by the classifier's recommendation first.
    """
    found = discover_exporters()
    if requested == ("all",):
        names = [n for n in order if n in found] + [n for n in found if n not in order]
        return [found[n] for n in names if found[n].available()]
    selected: list[Exporter] = []
    for name in requested:
        if name not in found:
            from ..errors import UsageError

            raise UsageError(f"unknown strategy {name!r}; known: {sorted(found)}")
        selected.append(found[name])
    return selected
