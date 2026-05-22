# this_file: src/vexy_dexypy/orchestrator.py
"""Pipeline orchestration & fan-out (spec/21).

Stages 1-3 run once per page; stages 4-6 run per strategy. Strategies are
independent and isolated: one failing yields a failed DeckResult, never an
aborted run.
"""

from __future__ import annotations

import shutil
from dataclasses import replace

import anyio
from loguru import logger

from . import paginate, preexport, readers, writers
from .classify import classify
from .exporters import select_exporters
from .importers import pick_importer
from .model import DeckResult, PageDoc, SlidePlan, Source, Strategy, write_sidecar
from .settings import Settings

# Cap concurrent browser-class exporters (Chromium is heavy, spec/21).
_BROWSER_LIMIT = 3


def read_page(source: Source, settings: Settings) -> PageDoc:
    page = readers.read(source, settings)
    cls = classify(page.html_path.read_text(encoding="utf-8"), page.meta)
    page = replace(page, framework=cls.framework)
    page.meta["classification"] = {
        "framework": cls.framework,
        "confidence": cls.confidence,
        "strategy_order": list(cls.strategy_order),
    }
    logger.info(
        "classified {} as {} (conf {:.2f})", source.slug, cls.framework, cls.confidence
    )
    _meta = settings.out_dir / source.slug / "_meta"
    write_sidecar(_meta / "page.json", page.to_dict())
    return page


def analyze_page(page: PageDoc, settings: Settings) -> SlidePlan:
    plan = paginate.analyze(page, settings.stage_w, settings.stage_h)
    if settings.vision:
        try:
            from .vision import refine

            plan = refine(page, plan, settings)
        except Exception as e:  # vision is an enhancement, never a dependency
            logger.warning("vision refine failed ({}); using heuristic plan", e)
    _meta = settings.out_dir / page.source.slug / "_meta"
    write_sidecar(_meta / "slideplan.json", plan.to_dict())
    logger.info("planned {} slide(s) for {}", plan.slide_count, page.source.slug)
    return plan


def _cache_key(page: PageDoc, plan: SlidePlan, strat: Strategy) -> str:
    return f"{page.content_hash}-{strat.name}-{plan.stage_w}x{plan.stage_h}"


def run_strategy(
    page: PageDoc, plan: SlidePlan, exporter, settings: Settings
) -> DeckResult:
    chassis_map = {
        "reveal": "reveal",
        "playwright": "paged",
        "vivliostyle": "paged",
        "prince": "paged",
        "impress": "impress",
        "marp": "marp",
    }
    chassis = chassis_map.get(exporter.name, "reveal")
    strat = Strategy(name=exporter.name, exporter=exporter.name, chassis=chassis)
    try:
        job = preexport.prepare(page, plan, strat)
        combined = job.html_path.parent / "_combined.pdf"
        cache_dir = settings.out_dir / page.source.slug / "_meta" / "cache"
        cached = cache_dir / f"{_cache_key(page, plan, strat)}.pdf"
        if not settings.no_cache and cached.is_file():
            logger.debug("cache hit for {}", strat.name)
            shutil.copyfile(cached, combined)
        else:
            exporter.export(job, combined)
            cache_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(combined, cached)
        return writers.write_deck(job, combined, svg=settings.svg)
    except Exception as e:  # isolate: one strategy must not kill the others
        logger.warning("strategy {} failed: {}", strat.name, e)
        out_dir = settings.out_dir / page.source.slug / strat.name
        return DeckResult(strategy=strat, out_dir=out_dir, ok=False, error=str(e))


async def _run_all(normalized, plan, exporters, settings) -> list[DeckResult]:
    """Run strategies concurrently; cap browser-class engines (spec/21)."""
    limiter = anyio.CapacityLimiter(_BROWSER_LIMIT)
    results: list[DeckResult | None] = [None] * len(exporters)

    async def worker(i: int, ex) -> None:
        if getattr(ex, "needs_js", False):
            async with limiter:
                results[i] = await anyio.to_thread.run_sync(
                    run_strategy, normalized, plan, ex, settings
                )
        else:
            results[i] = await anyio.to_thread.run_sync(
                run_strategy, normalized, plan, ex, settings
            )

    async with anyio.create_task_group() as tg:
        for i, ex in enumerate(exporters):
            tg.start_soon(worker, i, ex)
    return [r for r in results if r is not None]


def render_one(slug: str, strategy_name: str, settings: Settings) -> DeckResult:
    """Re-run one strategy from existing sidecars (the `render` CLI verb, spec/04)."""
    import json

    meta = settings.out_dir / slug / "_meta"
    page = PageDoc.from_dict(json.loads((meta / "page.json").read_text()))
    plan = SlidePlan.from_dict(json.loads((meta / "slideplan.json").read_text()))
    normalized_html = settings.out_dir / slug / "normalized" / "normalized.html"
    if normalized_html.is_file():
        page = replace(page, html_path=normalized_html)
    exporters = select_exporters((strategy_name,), ())
    if not exporters:
        raise RuntimeError(f"strategy {strategy_name!r} unavailable")
    return run_strategy(page, plan, exporters[0], settings)


def build(source: Source, settings: Settings) -> list[DeckResult]:
    """Full pipeline for one source across all selected strategies (spec/21)."""
    page = read_page(source, settings)
    plan = analyze_page(page, settings)

    importer = pick_importer(page)
    logger.info("normalizing with importer {}", importer.name)
    normalized = importer.transform(page, plan, settings)

    order = tuple(page.meta.get("classification", {}).get("strategy_order", ()))
    exporters = select_exporters(settings.strategies, order)
    if not exporters:
        logger.warning("no exporters available for {}", settings.strategies)

    results = anyio.run(_run_all, normalized, plan, exporters, settings)
    write_sidecar(
        settings.out_dir / source.slug / "_meta" / "run-summary.json",
        {
            "source": source.raw,
            "framework": page.framework,
            "slides": plan.slide_count,
            "results": [
                {
                    "strategy": r.strategy.name,
                    "ok": r.ok,
                    "slides": r.slide_count,
                    "error": r.error,
                }
                for r in results
            ],
        },
    )
    return results
