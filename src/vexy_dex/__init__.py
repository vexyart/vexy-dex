# this_file: src/vexy_dex/__init__.py
"""vexy-dex: turn an HTML page into slide decks through several engines at once."""

try:
    from importlib.metadata import version

    __version__ = version("vexy-dex")
except Exception:  # pragma: no cover - during local dev before install
    __version__ = "0.0.0.dev0"
