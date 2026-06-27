# this_file: tests/test_offline.py
"""Offline fetch mode: shell out to a single-file archiver (spec/06, 07)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from vexy_dexypy.model import Source
from vexy_dexypy.readers.offline import OfflineReader, _archive_cmd
from vexy_dexypy.settings import build_settings

FIXTURES = Path(__file__).parent / "fixtures"


def test_archive_cmd_single_file():
    cmd = _archive_cmd("single-file", "https://x.test/p", Path("/o/index.html"))
    assert cmd == ["single-file", "https://x.test/p", "/o/index.html"]


def test_archive_cmd_monolith_uses_dash_o():
    cmd = _archive_cmd("monolith", "https://x.test/p", Path("/o/index.html"))
    assert cmd == ["monolith", "https://x.test/p", "-o", "/o/index.html"]


def test_offline_settings_plumbing():
    s = build_settings(fetch_mode="offline")
    assert s.fetch_mode == "offline"
    assert s.offline_tool == "single-file"  # default


def test_can_read_is_zero_so_offline_never_hijacks_localize():
    assert OfflineReader().can_read(Source.parse("https://x.test/")) == 0.0


def test_offline_falls_back_to_localize_when_tool_absent(tmp_path):
    settings = build_settings(out=str(tmp_path), fetch_mode="offline")
    url = "https://x.test/p"
    with (
        patch("shutil.which", return_value=None),
        patch("vexy_dexypy.readers.static.StaticReader.read") as mock_static,
    ):
        OfflineReader().read(Source.parse(url), settings)
    mock_static.assert_called_once()  # degraded gracefully, no hard failure


def test_offline_delegates_local_files_to_static(tmp_path):
    fixture = FIXTURES / "generic_article" / "index.html"
    settings = build_settings(out=str(tmp_path), fetch_mode="offline")
    page = OfflineReader().read(Source.parse(str(fixture)), settings)
    assert page.html_path.is_file()
    assert page.meta.get("fetch_mode") != "offline"
