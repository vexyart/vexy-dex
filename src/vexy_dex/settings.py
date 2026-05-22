# this_file: src/vexy_dex/settings.py
"""Configuration, profiles and strategy selection (spec/05).

Precedence: CLI flags > ./vexy-dex.toml > ~/.config/vexy-dex/config.toml > defaults.
Resolved once at startup into a frozen Settings passed down the pipeline.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from .errors import UsageError

# Named aspect/size profiles → concrete (stage_w, stage_h). Default is 16:9.
PROFILES: dict[str, tuple[int, int]] = {
    "16:9": (1920, 1080),
    "4:3": (1440, 1080),
    "a4-landscape": (1123, 794),
}

DEFAULT_SIZE = (1920, 1080)


def parse_size(size: str) -> tuple[int, int]:
    """Parse a 'WxH' string into (w, h)."""
    m = size.lower().replace("×", "x").split("x")
    if len(m) != 2:
        raise UsageError(
            f"bad --size {size!r}; expected WxH like 1920x1080 "
            f"or an --aspect from {sorted(PROFILES)}"
        )
    try:
        w, h = int(m[0]), int(m[1])
    except ValueError as e:
        raise UsageError(f"bad --size {size!r}: {e}") from e
    if w <= 0 or h <= 0:
        raise UsageError(f"--size must be positive, got {size!r}")
    return w, h


def resolve_stage(aspect: str | None, size: str | None) -> tuple[int, int]:
    """--size wins over --aspect; otherwise the named profile; otherwise default."""
    if size:
        return parse_size(size)
    if aspect:
        key = aspect.lower()
        if key not in PROFILES:
            raise UsageError(
                f"unknown --aspect {aspect!r}; choose from {sorted(PROFILES)} "
                f"or pass --size WxH"
            )
        return PROFILES[key]
    return DEFAULT_SIZE


@dataclass(frozen=True)
class Settings:
    out_dir: Path = Path("out")
    stage_w: int = DEFAULT_SIZE[0]
    stage_h: int = DEFAULT_SIZE[1]
    strategies: tuple[str, ...] = ("all",)
    svg: bool = False
    vision: bool = False
    verbose: bool = False
    no_cache: bool = False
    # engine config
    prince_path: str = ""
    node_bin: str = "node"
    vision_model: str = "minicpm-v-4.6"
    vision_endpoint: str = "http://localhost:11434"

    def with_stage(self, w: int, h: int) -> Settings:
        return replace(self, stage_w=w, stage_h=h)


def _load_toml(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise UsageError(f"invalid config {path}: {e}") from e


def load_config() -> dict:
    """Merge project then user TOML (project wins)."""
    user = _load_toml(Path.home() / ".config" / "vexy-dex" / "config.toml")
    proj = _load_toml(Path("vexy-dex.toml"))
    merged = {**user}
    for section, vals in proj.items():
        merged[section] = {**merged.get(section, {}), **vals}
    return merged


def build_settings(
    *,
    out: str | None = None,
    aspect: str | None = None,
    size: str | None = None,
    strategies: str | None = None,
    svg: bool | None = None,
    vision: bool | None = None,
    verbose: bool = False,
    no_cache: bool = False,
) -> Settings:
    """Resolve flags over config over defaults into a frozen Settings (spec/05)."""
    cfg = load_config()
    out_cfg = cfg.get("output", {})
    stage_cfg = cfg.get("stage", {})
    strat_cfg = cfg.get("strategies", {})
    vision_cfg = cfg.get("vision", {})
    eng_cfg = cfg.get("engines", {})

    w, h = resolve_stage(
        aspect or stage_cfg.get("aspect"),
        size or stage_cfg.get("size"),
    )

    strat_raw = strategies if strategies is not None else strat_cfg.get("enabled", "all")
    if isinstance(strat_raw, str):
        strat = tuple(s.strip() for s in strat_raw.split(",") if s.strip())
    else:
        strat = tuple(strat_raw)
    if not strat:
        strat = ("all",)

    return Settings(
        out_dir=Path(out or out_cfg.get("dir", "out")),
        stage_w=w,
        stage_h=h,
        strategies=strat,
        svg=svg if svg is not None else bool(out_cfg.get("svg", False)),
        vision=vision if vision is not None else bool(vision_cfg.get("enabled", False)),
        verbose=verbose,
        no_cache=no_cache,
        prince_path=eng_cfg.get("prince_path", ""),
        node_bin=eng_cfg.get("node_bin", "node"),
        vision_model=vision_cfg.get("model", "minicpm-v-4.6"),
        vision_endpoint=vision_cfg.get("endpoint", "http://localhost:11434"),
    )
