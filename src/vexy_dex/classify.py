# this_file: src/vexy_dex/classify.py
"""Framework classification via a small fingerprint rules engine (spec/08).

Deliberately NOT Wappalyzer (dead). Fingerprints are short and stable. Returns a
(framework, confidence) pair and a recommended strategy order.
"""

from __future__ import annotations

from dataclasses import dataclass

# (framework, list of substrings, weight). First strong match wins; ties → generic.
_RULES: list[tuple[str, list[str]]] = [
    ("webflow", ["data-wf-page", "w-mod-js", "data-w-id", "webflow.js"]),
    ("mkdocs-material", ["mkdocs-material", "md-content", "data-md-component", "md-typeset"]),
    ("docusaurus", ["__docusaurus", "theme-doc-markdown"]),
    ("framer", ["data-framer-name", "framer.app"]),
    ("bubble", ["data-bb-id", "bubble-element"]),
]

# Strategy order recommendation per framework (spec/05, 08).
_STRATEGY_ORDER: dict[str, tuple[str, ...]] = {
    "webflow": ("playwright", "reveal", "weasyprint"),
    "mkdocs-material": ("weasyprint", "vivliostyle", "playwright"),
    "docusaurus": ("weasyprint", "vivliostyle", "playwright"),
    "framer": ("playwright", "reveal"),
    "bubble": ("playwright", "weasyprint"),
    "generic": ("weasyprint", "playwright", "vivliostyle"),
}


@dataclass(frozen=True)
class Classification:
    framework: str
    confidence: float
    strategy_order: tuple[str, ...]


def classify(html: str, meta: dict | None = None) -> Classification:
    """Identify the page builder from stable DOM/meta fingerprints."""
    s = html.lower()
    gen = ((meta or {}).get("generator") or "").lower()
    best = ("generic", 0.0)
    for framework, needles in _RULES:
        hits = sum(1 for n in needles if n in s or n in gen)
        if hits:
            conf = min(1.0, 0.5 + 0.25 * (hits - 1))
            if conf > best[1]:
                best = (framework, conf)
    framework, conf = best
    return Classification(
        framework=framework,
        confidence=conf,
        strategy_order=_STRATEGY_ORDER.get(framework, _STRATEGY_ORDER["generic"]),
    )
