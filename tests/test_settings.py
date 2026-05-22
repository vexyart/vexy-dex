# this_file: tests/test_settings.py
from __future__ import annotations

import pytest

from vexy_dex.errors import UsageError
from vexy_dex.settings import parse_size, resolve_stage


def test_default_stage_is_1920x1080():
    assert resolve_stage(None, None) == (1920, 1080)


def test_aspect_profiles():
    assert resolve_stage("16:9", None) == (1920, 1080)
    assert resolve_stage("4:3", None) == (1440, 1080)


def test_size_overrides_aspect():
    assert resolve_stage("4:3", "800x600") == (800, 600)


def test_parse_size_accepts_unicode_x():
    assert parse_size("1280×720") == (1280, 720)


def test_bad_size_raises_usage_error():
    with pytest.raises(UsageError):
        parse_size("oops")


def test_unknown_aspect_raises():
    with pytest.raises(UsageError):
        resolve_stage("21:9", None)
