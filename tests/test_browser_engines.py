# this_file: tests/test_browser_engines.py
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from vexy_dexypy._browser import launched_browser
from vexy_dexypy.settings import build_settings


def test_browser_engine_setting_parsing():
    settings = build_settings(browser_engine="playwrightauthor")
    assert settings.browser_engine == "playwrightauthor"

    settings = build_settings(browser_engine="cloakbrowser")
    assert settings.browser_engine == "cloakbrowser"

    settings = build_settings()
    assert settings.browser_engine == "playwright"  # default


def test_launched_browser_standard_playwright():
    settings = build_settings(browser_engine="playwright")

    with patch("playwright.sync_api.sync_playwright") as mock_sync:
        mock_playwright = MagicMock()
        mock_sync.return_value.__enter__.return_value = mock_playwright

        with launched_browser(settings):
            pass

        mock_playwright.chromium.launch.assert_called_once()


def test_launched_browser_playwrightauthor(monkeypatch, tmp_path):
    # Mock sys.path insertion and import
    settings = build_settings(browser_engine="playwrightauthor")

    # Create mock path and module
    p_dir = tmp_path / "private" / "playwrightauthor" / "src"
    p_dir.mkdir(parents=True)

    # Patch the Path resolution to point to our temp directory
    original_path = Path

    class MockPath:
        def __init__(self, *args):
            # If resolving "private/playwrightauthor/src", redirect to tmp_path
            self._path = original_path(*args)

        def resolve(self):
            if "private/playwrightauthor/src" in str(self._path).replace("\\", "/"):
                return p_dir.resolve()
            return self._path.resolve()

    monkeypatch.setattr("vexy_dexypy._browser.Path", MockPath)

    # Mock playwrightauthor import
    mock_browser_class = MagicMock()
    mock_browser_instance = MagicMock()
    mock_browser_class.return_value.__enter__.return_value = mock_browser_instance

    # Insert mock into sys.modules so the import succeeds
    sys.modules["playwrightauthor"] = MagicMock()
    sys.modules["playwrightauthor"].Browser = mock_browser_class

    try:
        with launched_browser(settings) as browser:
            assert browser == mock_browser_instance

        mock_browser_class.assert_called_once()
        assert str(p_dir.resolve()) in sys.path
    finally:
        sys.modules.pop("playwrightauthor", None)
        if str(p_dir.resolve()) in sys.path:
            sys.path.remove(str(p_dir.resolve()))


def test_launched_browser_cloakbrowser():
    settings = build_settings(browser_engine="cloakbrowser")

    mock_cloakbrowser = MagicMock()
    mock_browser = MagicMock()
    mock_cloakbrowser.launch.return_value = mock_browser

    sys.modules["cloakbrowser"] = mock_cloakbrowser

    try:
        with launched_browser(settings) as browser:
            assert browser == mock_browser

        mock_cloakbrowser.launch.assert_called_once_with(headless=True)
        mock_browser.close.assert_called_once()
    finally:
        sys.modules.pop("cloakbrowser", None)
