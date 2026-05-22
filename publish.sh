#!/usr/bin/env bash
# this_file: publish.sh
# Clean, bump the git-tag version, build, and publish to PyPI.
# Version is derived from git tags by hatch-vcs (see pyproject.toml); gitnextver
# creates the next semver tag, so build/publish must run after it.
set -euo pipefail
cd "$(dirname "$0")"

echo "== hatch clean =="
uvx hatch clean

echo "== gitnextver (create next semver git tag) =="
uvx gitnextver

echo "== uv build =="
uv build

echo "== uv publish =="
uv publish
