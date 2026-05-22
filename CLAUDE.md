<!-- this_file: CLAUDE.md -->

# CLAUDE.md — guidance for coding agents working on vexy-dexypy

This file orients an AI coding agent (or any new contributor) to the project.
Read it, then read [`spec/00-tldr.md`](spec/00-tldr.md) and
[`RESEARCH.md`](RESEARCH.md) before writing code.

## What this project is

vexy-dexypy is an offline-first Python CLI that converts an HTML page into slide
decks. One URL in; several folders out, one per rendering strategy, each holding
named single-page PDFs (and optional SVGs). The user assembles a final deck by
picking the best rendering of each slide across strategies. The divergence
between strategies is the product, not a bug.

One-sentence scope (do not exceed it without an argument):

> Fetch an HTML page, classify it, normalize its DOM, paginate it intelligently
> at a target aspect ratio, render it to PDF through several engines in
> parallel, and slice each result into named single-page PDFs and SVGs so the
> user can cherry-pick slides across strategies.

## The pipeline (memorize this)

Six stages, orchestrated by a Python core that shells out to browser/Node
engines:

1. **readers** — fetch HTML + localize assets → `PageDoc` ([spec/06](spec/06.md), [spec/07](spec/07.md))
2. **pre-importers** — classify + plan pagination → `SlidePlan` ([spec/08](spec/08.md)–[10](spec/10.md))
3. **importers** — framework normalization → normalized `PageDoc` ([spec/11](spec/11.md)–[14](spec/14.md))
4. **pre-exporters** — paged CSS / reveal wrapping → `RenderJob` ([spec/15](spec/15.md))
5. **exporters** — HTML → multi-page PDF, N engines in parallel ([spec/16](spec/16.md)–[19](spec/19.md))
6. **writers** — split + SVG + preview index → `DeckResult` ([spec/20](spec/20.md))

Stages communicate only through the typed IR in [spec/03](spec/03.md). Never let
one stage reach into another's internals.

## Where things live

```
src/vexy_dexypy/
  __main__.py cli.py settings.py model.py orchestrator.py dom.py
  classify.py paginate.py vision.py preexport.py writers.py
  readers/ importers/ exporters/ assets/
spec/        # the 24-chapter specification — the source of truth
tests/ examples/
RESEARCH.md TODO.md PLAN.md WORK.md CHANGELOG.md DEPENDENCIES.md
```

Full layout and `pyproject.toml` in [spec/24](spec/24.md).

## Tech decisions already made (don't relitigate)

- **CLI:** Fire. **Concurrency:** `anyio` task groups + `CapacityLimiter` for the
  Chromium pool. **Logging:** `loguru`, always-on `--verbose`.
- **Fetch:** `httpx[http2]` (static) / Playwright (dynamic). **Freeze:**
  `monolith`. **Parse:** `selectolax` (hot paths), `bs4+lxml` (human-edited
  surgery). **Extract:** `trafilatura`.
- **Classify:** a ~200-line fingerprint rules engine — **NOT Wappalyzer** (dead).
- **Exporters:** Playwright, WeasyPrint, Vivliostyle (shell out — AGPL), DeckTape,
  Prince (opt-in). **Avoid** pagedjs-cli, wkhtmltopdf, pyppeteer.
- **Split:** `pypdf` (default) / `pikepdf` (damaged). **Avoid PyMuPDF** unless the
  project goes AGPL/commercial. **SVG:** delegate to `vexy-pdfsvgpy`.
- **Webflow importer:** copy & adapt `webflow2reveal/py/src/webflow2reveal/compiler.py`
  into vexy-dexypy (author's own legacy code, no licence concern, not a dependency).
  vexy-dexypy supersedes and ultimately retires `webflow2reveal`.
- **Plugins:** `importlib.metadata` entry points for readers/importers/exporters/
  writers; each exposes a `detect`/`available` confidence.

Rationale for every choice is in [RESEARCH.md](RESEARCH.md).

## Coding conventions

- **Python 3.12+, `uv` only** (`uv add`, never bare `pip`). Type hints everywhere
  (`list`, `dict`, `|` unions). `pathlib`, f-strings, structural matching.
- **Parse, don't validate.** Convert raw input to typed IR at the boundary
  ([spec/03](spec/03.md)). Dataclasses for internal IR; Pydantic where data is
  serialized/external (config, vision output).
- **Errors as data at boundaries.** Typed errors (`ReadError`, `ExportError`, …);
  a failed strategy is a `DeckResult(ok=False)`, never a crash that aborts the
  run ([spec/22](spec/22.md)). Error messages are UX — name the cause and the fix.
- **Partial failure is normal.** Design the recovery path first. One engine
  failing must not stop the others.
- **Subprocess discipline.** Every browser/Node/Prince call has a timeout,
  captured stderr, and a localized file path (offline). Shell out to AGPL engines;
  never link.
- **Anti-bloat (hard rule).** No analytics/metrics/telemetry, no caching/retry
  framework (use the simple keyed cache in [spec/21](spec/21.md) and a tiny
  backoff helper), no class named `Manager`/`Handler`/`System`/`Framework`.
  Functions < ~20 lines, files < ~200 lines, < 3 indent levels where practical.
- **Build vs buy.** Reuse maintained packages; write custom code only for the
  glue and the genuinely vexy-dexypy-specific pagination logic ([spec/09](spec/09.md)).
- **`this_file` header** near the top of every source file (path relative to repo
  root). Markdown uses an HTML comment; Python uses a comment after any shebang.

## Workflow expectations

- **Spec is the contract.** Implement against the relevant `spec/NN.md`. If you
  must deviate, update the spec chapter in the same change and say why.
- **Tests first, then code.** Every function ≥1 test; cover edge (empty, none,
  giant, malformed) and error (network off, missing engine, timeout) cases.
  Target ≥80% on the core. Tests run offline against `tests/fixtures/` — never
  fetch the live web in CI ([spec/23](spec/23.md)).
- **Surgical changes.** Touch only what the task needs; match surrounding style;
  don't refactor unrelated code or delete pre-existing dead code without asking.
- **Post-edit checks (Python):**
  `fd -e py -x uvx autoflake -i {}; fd -e py -x uvx pyupgrade --py312-plus {}; fd -e py -x uvx ruff check --fix --unsafe-fixes {}; fd -e py -x uvx ruff format {}; uvx hatch test`
- **Keep docs current:** `WORK.md` (progress/results), `CHANGELOG.md` (changes),
  `TODO.md`/`PLAN.md` (tick off), `DEPENDENCIES.md` (any dep/licence change).

## Licence landmines (see [spec/24](spec/24.md), DEPENDENCIES.md)

Vivliostyle (AGPL — shell out), PyMuPDF (AGPL — avoid), Surya (GPL3 — research
only), Prince (proprietary — opt-in). `webflow2reveal` is **not** a dependency —
its code is copied in (author's own), no constraint. Record every real
dependency's licence in `DEPENDENCIES.md` with the reason it was chosen.

## CodeGraph

`.codegraph/` exists — prefer `codegraph_search`/`callers`/`callees`/`impact`
over grep for symbol lookups and impact analysis when exploring the codebase.
