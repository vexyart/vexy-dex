# this_file: src/vexy_dex/__init__.py
"""vexy-dex: turn an HTML page into slide decks through several engines at once."""

try:
    # Written at build time by hatch-vcs from the latest git tag (gitignored).
    from .__version__ import __version__
except Exception:  # pragma: no cover - editable/dev tree before a build
    try:
        from importlib.metadata import version

        __version__ = version("vexy-dex")
    except Exception:
        __version__ = "0.0.0.dev0"
