#!/usr/bin/env bash
# One-time (and idempotent) setup of the development environment.
#
#   ./scripts/bootstrap.sh
#
# This machine has no global pip/pip3/pipx/uv, so pip is bootstrapped INSIDE the
# venv via ensurepip — that constraint is why this script exists at all, and it is
# the main input for the future py-base template.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> creating venv (.venv)"
python3 -m venv .venv

echo "==> bootstrapping pip inside the venv (no global pip on this machine)"
.venv/bin/python -m ensurepip --upgrade
.venv/bin/python -m pip install --upgrade pip --quiet

echo "==> installing pinned dev dependencies"
.venv/bin/python -m pip install -r requirements-dev.txt --quiet

echo "==> wiring git hooks (core.hooksPath)"
git config core.hooksPath .githooks

echo
echo "Done. Verify with: ./scripts/verify.sh"
