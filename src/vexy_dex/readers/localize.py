# this_file: src/vexy_dex/readers/localize.py
"""Asset localization & offline bundling (spec/07).

Tier 1 baseline: a ThreadPoolExecutor walks the parsed DOM, downloads each
tag-referenced asset into asset_dir, and rewrites the reference to a local
relative path. Failures warn and continue — a missing analytics script must not
stop a render.
"""

from __future__ import annotations

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from loguru import logger

_ASSET_TAGS = {"link": "href", "script": "src", "img": "src", "source": "src"}
_SKIP_PREFIXES = ("data:", "mailto:", "javascript:", "tel:", "#")
_CSS_URL = re.compile(r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""")
_CSS_IMPORT = re.compile(r"""@import\s+['"]([^'"]+)['"]""")


def _safe_name(url: str) -> str:
    """Filesystem-safe local name; hash long/odd paths to avoid collisions."""
    path = urlparse(url).path
    name = Path(path).name or "asset"
    if len(name) > 80 or "/" in name:
        digest = hashlib.sha1(url.encode()).hexdigest()[:12]
        suffix = Path(name).suffix[:8]
        name = f"{digest}{suffix}"
    return name


def localize_assets(
    html: str, base_url: str, asset_dir: Path, *, max_workers: int = 8
) -> str:
    """Download tag-referenced assets and rewrite refs to local relative paths."""
    soup = BeautifulSoup(html, "lxml")
    asset_dir.mkdir(parents=True, exist_ok=True)
    jobs: list[tuple] = []
    for tag in soup.find_all(list(_ASSET_TAGS)):
        attr = _ASSET_TAGS[tag.name]
        val = tag.get(attr)
        if isinstance(val, list):
            val = val[0] if val else None
        if not isinstance(val, str) or val.startswith(_SKIP_PREFIXES):
            continue
        absolute = urljoin(base_url, val)
        if not absolute.startswith(("http://", "https://")):
            continue
        jobs.append((tag, attr, absolute))

    if not jobs:
        return str(soup)

    client = httpx.Client(follow_redirects=True, timeout=15)
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            list(
                pool.map(
                    lambda j: _fetch_one(client, j[0], j[1], j[2], asset_dir), jobs
                )
            )
    finally:
        client.close()
    return str(soup)


def _fetch_one(client, tag, attr, url, asset_dir: Path) -> None:
    try:
        resp = client.get(url)
        if resp.status_code != 200:
            logger.warning("asset {} -> HTTP {}", url, resp.status_code)
            return
        name = _safe_name(url)
        is_css = tag.name == "link" or "css" in resp.headers.get("content-type", "")
        if is_css:
            css = _localize_css(client, resp.text, url, asset_dir, depth=2)
            (asset_dir / name).write_text(css, encoding="utf-8")
        else:
            (asset_dir / name).write_bytes(resp.content)
        tag[attr] = f"assets/{name}"
        # The resource is now a local file. Subresource Integrity (and the CORS
        # check `crossorigin` forces) makes the browser BLOCK it under file://
        # — an opaque origin can't satisfy SRI — so a localized Webflow CSS link
        # silently fails to apply and the page renders unstyled. Drop both.
        for dead in ("integrity", "crossorigin"):
            if tag.has_attr(dead):
                del tag[dead]
    except Exception as e:  # network flake on one asset must not abort the page
        logger.warning("failed to localize asset {}: {}", url, e)


def _localize_css(
    client, css: str, css_url: str, asset_dir: Path, *, depth: int
) -> str:
    """Download url()/@import targets in a stylesheet and rewrite to local refs.

    Bounded recursion (depth) for @import chains. Failures leave the original
    reference in place rather than aborting (offline is best-effort, spec/07).
    """
    fetched: dict[str, str] = {}

    def grab(ref: str, *, as_css: bool) -> str | None:
        if ref.startswith(_SKIP_PREFIXES):
            return None
        absolute = urljoin(css_url, ref)
        if not absolute.startswith(("http://", "https://")):
            return None
        if absolute in fetched:
            return fetched[absolute]
        try:
            r = client.get(absolute)
            if r.status_code != 200:
                return None
            name = _safe_name(absolute)
            if as_css and depth > 0:
                text = _localize_css(
                    client, r.text, absolute, asset_dir, depth=depth - 1
                )
                (asset_dir / name).write_text(text, encoding="utf-8")
            else:
                (asset_dir / name).write_bytes(r.content)
            fetched[absolute] = name
            return name
        except Exception as e:
            logger.debug("css asset {} skipped: {}", absolute, e)
            return None

    def repl_url(m: re.Match) -> str:
        name = grab(m.group(1), as_css=False)
        return f"url({name})" if name else m.group(0)

    def repl_import(m: re.Match) -> str:
        name = grab(m.group(1), as_css=True)
        return f'@import "{name}"' if name else m.group(0)

    css = _CSS_IMPORT.sub(repl_import, css)
    css = _CSS_URL.sub(repl_url, css)
    return css


def content_hash(html_path: Path, asset_dir: Path) -> str:
    """Hash of the HTML plus a manifest of asset bytes (cache key, spec/21)."""
    h = hashlib.sha256()
    h.update(html_path.read_bytes())
    if asset_dir.is_dir():
        for f in sorted(asset_dir.rglob("*")):
            if f.is_file():
                h.update(f.name.encode())
                h.update(str(f.stat().st_size).encode())
    return h.hexdigest()[:16]
