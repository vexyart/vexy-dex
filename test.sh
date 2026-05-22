#!/usr/bin/env bash
# this_file: test.sh
# Run the full check suite. On macOS, surface Homebrew libs for WeasyPrint.
set -euo pipefail

export DYLD_FALLBACK_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH:-/opt/homebrew/lib}"

echo "== ruff =="
uvx ruff check src tests || true
echo "== pytest =="
uv run pytest "$@"
echo "== example smoke =="
uv run python examples/build_local.py
