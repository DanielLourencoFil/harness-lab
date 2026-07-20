#!/usr/bin/env bash
# The canonical gate: format + lint + typecheck + test. One string, used everywhere
# (pre-commit hook, CI, the /feature and /audit rites). If it is not green, nothing
# ships.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Prefer the project venv; fall back to whatever python is on PATH (CI installs
# the same pins into the runner's interpreter).
if [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

echo "==> ruff format --check"
"$PY" -m ruff format --check .

echo "==> ruff check"
"$PY" -m ruff check .

echo "==> mypy"
"$PY" -m mypy src tests

echo "==> pytest"
"$PY" -m pytest

echo
echo "verify: OK"
