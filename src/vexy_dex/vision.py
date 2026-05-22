# this_file: src/vexy_dex/vision.py
"""Optional vision/LLM pagination refinement (spec/10).

Strictly opt-in (--vision), cached, never on the critical path. The heuristic
SlidePlan is the floor; vision only adjusts it. If the model server is down we
log and return the input plan unchanged.
"""

from __future__ import annotations

import hashlib
import json

from loguru import logger

from .model import Break, PageDoc, SlidePlan
from .settings import Settings


def _screenshot(page: PageDoc, settings: Settings):
    from playwright.sync_api import sync_playwright

    from ._browser import serving

    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_context(
            viewport={"width": settings.stage_w, "height": settings.stage_h}
        ).new_page()
        with serving(pg, page.html_path):
            png = pg.screenshot(full_page=True)
        browser.close()
    return png


def _ask_model(png: bytes, settings: Settings) -> list[dict]:
    """Query an OpenAI-compatible endpoint (Ollama/llama.cpp) for break offsets.

    NOTE: callers must serve MiniCPM-V with the thinking template OFF
    (`--reasoning off`) or Instruct output breaks (spec/10).
    """
    import base64

    import httpx

    b64 = base64.b64encode(png).decode()
    prompt = (
        "List the y-coordinates (px) where a new slide should start. "
        'Output JSON only: {"breaks": [{"y": <int>, "reason": "<text>"}]}'
    )
    resp = httpx.post(
        f"{settings.vision_endpoint}/api/chat",
        json={
            "model": settings.vision_model,
            "stream": False,
            "messages": [{"role": "user", "content": prompt, "images": [b64]}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    content = resp.json().get("message", {}).get("content", "{}")
    data = json.loads(content)
    return data.get("breaks", [])


def refine(page: PageDoc, plan: SlidePlan, settings: Settings) -> SlidePlan:
    """Merge validated vision breaks onto the heuristic plan (heuristic is floor)."""
    cache_dir = settings.out_dir / page.source.slug / "_meta" / "vision"
    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        png = _screenshot(page, settings)
    except Exception as e:
        logger.warning("vision screenshot failed ({}); skipping", e)
        return plan
    key = hashlib.sha1(png).hexdigest()[:16] + "-" + settings.vision_model
    cache = cache_dir / f"{key}.json"
    if cache.is_file():
        raw = json.loads(cache.read_text())
    else:
        try:
            raw = _ask_model(png, settings)
            cache.write_text(json.dumps(raw))
        except Exception as e:
            logger.warning("vision model unavailable ({}); using heuristic plan", e)
            return plan

    extra = []
    for item in raw:  # validate, never trust prose
        try:
            extra.append(Break(float(item["y"]), "vision", 0.7))
        except (KeyError, TypeError, ValueError):
            continue
    merged = SlidePlan(plan.stage_w, plan.stage_h, [*plan.breaks, *extra], plan.notes)
    return merged.normalized(tol=settings.stage_h * 0.1)
