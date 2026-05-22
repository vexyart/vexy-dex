# this_file: src/vexy_dexypy/__init__.py
"""vexy-dexypy: turn an HTML page into slide decks through several engines at once."""

try:
    # Written at build time by hatch-vcs from the latest git tag (gitignored).
    from .__version__ import __version__
except Exception:  # pragma: no cover - editable/dev tree before a build
    try:
        from importlib.metadata import version

        __version__ = version("vexy-dexypy")
    except Exception:
        __version__ = "0.0.0.dev0"
