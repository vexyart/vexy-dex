# this_file: src/vexy_dex/cli.py
"""Fire CLI surface (spec/04). `build` is the headline; others expose stages."""

from __future__ import annotations

import sys

from loguru import logger
from rich.console import Console
from rich.table import Table

from . import orchestrator
from .errors import UsageError, VexyDexError
from .model import Source
from .settings import build_settings

console = Console()


def _setup_logging(verbose: bool) -> None:
    logger.remove()
    logger.add(sys.stderr, level="DEBUG" if verbose else "INFO",
               format="<level>{level: <7}</level> {message}")


def _summary(results) -> int:
    """Print the per-strategy outcome table; return the exit code (spec/22)."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("strategy")
    table.add_column("result")
    table.add_column("slides", justify="right")
    table.add_column("output / error")
    ok = 0
    for r in results:
        if r.ok:
            ok += 1
            table.add_row(r.strategy.name, "[green]✓[/green]",
                          str(r.slide_count), str(r.out_dir))
        else:
            table.add_row(r.strategy.name, "[red]✗[/red]", "-", r.error or "failed")
    console.print(table)
    total = len(results)
    console.print(f"{ok}/{total} strategies succeeded." if total else "no strategies ran.")
    if total == 0 or ok == 0:
        return 2
    return 0


class VexyDex:
    """Turn an HTML page into slide decks through several engines at once."""

    def build(self, url: str, out: str = "out", aspect: str | None = None,
              size: str | None = None, strategies: str = "all", svg: bool = False,
              vision: bool = False, verbose: bool = False, no_cache: bool = False) -> int:
        """Fetch -> analyze -> normalize -> render -> split, every strategy."""
        _setup_logging(verbose)
        settings = build_settings(
            out=out, aspect=aspect, size=size, strategies=strategies,
            svg=svg, vision=vision, verbose=verbose, no_cache=no_cache,
        )
        results = orchestrator.build(Source.parse(url), settings)
        return _summary(results)

    def read(self, url: str, out: str = "out", verbose: bool = False) -> str:
        """Stage 1 only: fetch and localize. Emits a PageDoc sidecar."""
        _setup_logging(verbose)
        settings = build_settings(out=out, verbose=verbose)
        page = orchestrator.read_page(Source.parse(url), settings)
        console.print(f"localized {url} -> {page.html_path} ({page.framework})")
        return str(page.html_path)

    def analyze(self, url: str, out: str = "out", aspect: str | None = None,
                size: str | None = None, vision: bool = False, verbose: bool = False) -> int:
        """Stage 1+2: fetch, classify, and plan slide breaks."""
        _setup_logging(verbose)
        settings = build_settings(out=out, aspect=aspect, size=size,
                                  vision=vision, verbose=verbose)
        page = orchestrator.read_page(Source.parse(url), settings)
        plan = orchestrator.analyze_page(page, settings)
        console.print(f"{plan.slide_count} slide(s); breaks at "
                      f"{[round(b.y) for b in plan.breaks]}")
        return plan.slide_count

    def render(self, slug: str, strategy: str, out: str = "out",
               svg: bool = False, verbose: bool = False) -> int:
        """Stages 4-6 for one strategy from existing sidecars (re-run)."""
        _setup_logging(verbose)
        settings = build_settings(out=out, strategies=strategy, svg=svg, verbose=verbose)
        result = orchestrator.render_one(slug, strategy, settings)
        return _summary([result])

    def split(self, pdf: str, out: str = ".", svg: bool = False,
              prefix: str = "slide", verbose: bool = False) -> int:
        """Stage 6 only: split a PDF into named per-slide files."""
        from pathlib import Path

        from . import writers

        _setup_logging(verbose)
        slides = writers.split_pdf(Path(pdf), Path(out), prefix=prefix)
        if svg:
            writers.to_svgs(slides, Path(out))
        writers.build_preview(slides, Path(out))
        console.print(f"split into {len(slides)} slide(s) in {out}")
        return len(slides)


def _annotate_help() -> None:
    """Append the runtime-discovered strategies to `build`'s help (spec/04)."""
    try:
        from .exporters import discover_exporters

        avail = [n for n, e in discover_exporters().items() if e.available()]
        missing = [n for n, e in discover_exporters().items() if not e.available()]
        note = f"\n\n  Available strategies: {', '.join(sorted(avail)) or 'none'}."
        if missing:
            note += f" Unavailable (install deps): {', '.join(sorted(missing))}."
        note += "\n  Tip: put flag values after a `--` if Fire mistakes them for positionals."
        VexyDex.build.__doc__ = (VexyDex.build.__doc__ or "") + note
    except Exception:
        pass


def main() -> None:
    import fire

    _annotate_help()
    try:
        result = fire.Fire(VexyDex)
        if isinstance(result, int):
            sys.exit(result)
    except UsageError as e:
        console.print(f"[red]usage error:[/red] {e}")
        sys.exit(1)
    except VexyDexError as e:
        console.print(f"[red]error:[/red] {e}")
        sys.exit(2)
