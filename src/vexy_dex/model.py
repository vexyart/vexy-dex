# this_file: src/vexy_dex/model.py
"""The typed intermediate representation that flows between stages (spec/03).

Parse, don't validate: raw input becomes a typed object at the boundary, and its
existence proves validity. These are plain dataclasses; JSON sidecars are emitted
by `to_dict`/`from_dict` so per-stage CLI verbs can run independently.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path


class SourceKind(str, Enum):
    URL = "url"
    FILE = "file"


def slugify(raw: str) -> str:
    """Filesystem-safe identifier derived from a URL or path."""
    s = re.sub(r"^https?://", "", raw.strip().lower())
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:80] or "page"


@dataclass(frozen=True)
class Source:
    """What the user asked us to convert."""

    raw: str
    kind: SourceKind
    slug: str

    @classmethod
    def parse(cls, raw: str) -> Source:
        raw = raw.strip()
        if raw.startswith(("http://", "https://")):
            kind = SourceKind.URL
        else:
            kind = SourceKind.FILE
        return cls(raw=raw, kind=kind, slug=slugify(raw))


@dataclass
class PageDoc:
    """A localized, parseable page. The spine of the pipeline."""

    source: Source
    html_path: Path
    asset_dir: Path
    framework: str = "generic"
    meta: dict = field(default_factory=dict)
    content_hash: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["source"]["kind"] = self.source.kind.value
        d["html_path"] = str(self.html_path)
        d["asset_dir"] = str(self.asset_dir)
        return d


@dataclass(frozen=True)
class Break:
    """One pagination boundary on the rendered stage."""

    y: float
    reason: str  # "section" | "h2" | "overflow" | "vision"
    confidence: float = 1.0


@dataclass
class SlidePlan:
    """Where slides should start, decided by the pre-importer (spec/09, 10)."""

    stage_w: int
    stage_h: int
    breaks: list[Break] = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    def normalized(self, tol: float = 1.0) -> SlidePlan:
        """Return a copy with breaks sorted ascending and deduplicated."""
        seen: list[Break] = []
        for b in sorted(self.breaks, key=lambda x: x.y):
            if not seen or abs(b.y - seen[-1].y) > tol:
                seen.append(b)
        return SlidePlan(self.stage_w, self.stage_h, seen, dict(self.notes))

    @property
    def slide_count(self) -> int:
        return len(self.normalized().breaks) + 1

    def to_dict(self) -> dict:
        return {
            "stage_w": self.stage_w,
            "stage_h": self.stage_h,
            "breaks": [asdict(b) for b in self.breaks],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> SlidePlan:
        return cls(
            stage_w=d["stage_w"],
            stage_h=d["stage_h"],
            breaks=[Break(**b) for b in d.get("breaks", [])],
            notes=d.get("notes", {}),
        )


@dataclass(frozen=True)
class Strategy:
    """A named rendering route (output sub-folder name == exporter name)."""

    name: str
    exporter: str


@dataclass
class RenderJob:
    """Engine-ready input for one strategy (built by the pre-exporter, spec/15)."""

    page: PageDoc
    plan: SlidePlan
    strategy: Strategy
    html_path: Path
    extra_css: list[Path] = field(default_factory=list)


@dataclass
class DeckResult:
    """What a writer produces for one strategy (spec/20)."""

    strategy: Strategy
    out_dir: Path
    slide_pdfs: list[Path] = field(default_factory=list)
    slide_svgs: list[Path] = field(default_factory=list)
    index_html: Path | None = None
    ok: bool = True
    error: str | None = None

    @property
    def slide_count(self) -> int:
        return len(self.slide_pdfs)


def write_sidecar(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
