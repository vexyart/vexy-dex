# this_file: src/vexy_dex/errors.py
"""Typed error taxonomy (spec/22). Errors carry context so messages are UX."""

from __future__ import annotations


class VexyDexError(Exception):
    """Base for all vexy-dex errors."""


class UsageError(VexyDexError):
    """Bad invocation; fail fast before doing work. CLI exit code 1."""


class ReadError(VexyDexError):
    """Fetch / localize failed (Stage 1). Often fatal to the run."""


class NormalizeError(VexyDexError):
    """A normalizer choked (Stage 3). Caller may fall back to generic."""


class ExportError(VexyDexError):
    """One engine failed (Stage 5). Isolated to its strategy."""


class WriteError(VexyDexError):
    """Splitting / SVG failed (Stage 6). Isolated to its strategy."""


class VisionError(VexyDexError):
    """Vision model unavailable or returned garbage (Stage 2). Non-fatal."""
