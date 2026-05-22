# this_file: src/vexy_dex/readers/static.py
"""Static reader: httpx fetch (or local file) + asset localization (spec/06)."""

from __future__ import annotations

import random
import time
from pathlib import Path

import httpx
from loguru import logger

from ..errors import ReadError
from ..model import PageDoc, Source, SourceKind
from ..settings import Settings
from .localize import content_hash, localize_assets

# Heuristic: a body this short on a URL fetch likely means client-rendered.
_THIN_BODY = 500


class StaticReader:
    name = "static"

    def can_read(self, source: Source) -> float:
        return 0.5  # the always-available baseline; dynamic outranks for SPAs

    def read(self, source: Source, settings: Settings) -> PageDoc:
        work = settings.out_dir / source.slug
        raw_dir = work / "raw"
        asset_dir = raw_dir / "assets"
        raw_dir.mkdir(parents=True, exist_ok=True)

        if source.kind == SourceKind.FILE:
            html = self._read_file(source.raw)
            base_url = Path(source.raw).resolve().as_uri()
        else:
            html = self._fetch(source.raw)
            base_url = source.raw
            if self._looks_client_rendered(html):
                logger.info(
                    "thin static body for {}; escalating to dynamic", source.raw
                )
                try:
                    from .dynamic import DynamicReader

                    return DynamicReader().read(source, settings)
                except Exception as e:  # dynamic optional; keep the static result
                    logger.warning("dynamic escalation failed ({}); using static", e)

        local_html = localize_assets(html, base_url, asset_dir)
        html_path = raw_dir / "index.html"
        html_path.write_text(local_html, encoding="utf-8")

        page = PageDoc(source=source, html_path=html_path, asset_dir=asset_dir)
        page.content_hash = content_hash(html_path, asset_dir)
        page.meta = _extract_meta(local_html)
        return page

    def _read_file(self, path: str) -> str:
        p = Path(path)
        if not p.is_file():
            raise ReadError(f"no such file: {path}")
        return p.read_text(encoding="utf-8", errors="replace")

    def _fetch(self, url: str, retries: int = 1) -> str:
        last: Exception | None = None
        for attempt in range(retries + 1):
            try:
                resp = httpx.get(url, follow_redirects=True, timeout=30)
                if resp.status_code >= 400:
                    raise ReadError(f"{url} -> HTTP {resp.status_code}")
                return resp.text
            except (httpx.HTTPError, ReadError) as e:
                last = e
                if attempt < retries:
                    time.sleep(0.5 * (2**attempt) + random.random() * 0.2)
        raise ReadError(f"failed to fetch {url}: {last}")

    def _looks_client_rendered(self, html: str) -> bool:
        from bs4 import BeautifulSoup

        body = BeautifulSoup(html, "lxml").body
        return body is not None and len(body.get_text(strip=True)) < _THIN_BODY


def _extract_meta(html: str) -> dict:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    meta: dict = {}
    if soup.title and soup.title.string:
        meta["title"] = soup.title.string.strip()
    gen = soup.find("meta", attrs={"name": "generator"})
    if gen and gen.get("content"):
        meta["generator"] = gen["content"]
    return meta
