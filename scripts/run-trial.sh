#!/usr/bin/env bash
# Run ONE trial and print its measurement.
#
#   ./scripts/run-trial.sh <task-name> <setup>
#   ./scripts/run-trial.sh 01-account-bugs bare
#
# RUN THIS FROM A PLAIN TERMINAL, NOT INSIDE CLAUDE CODE.
# `claude -p` refuses to launch inside an existing session (SPEC F1); the runner
# detects that and stops rather than letting it surface as a nested-session crash.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ $# -ne 2 ]; then
  echo "usage: $0 <task-name> <setup>" >&2
  echo "  tasks:  $(ls tasks | tr '\n' ' ')" >&2
  echo "  setups: bare mini-skill long-skill force-cage" >&2
  exit 2
fi

PY=.venv/bin/python
[ -x "$PY" ] || PY=python3

PYTHONPATH=src "$PY" -m harness_lab.run_trial "$1" "$2"
