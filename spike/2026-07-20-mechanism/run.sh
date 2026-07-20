#!/usr/bin/env bash
# Harness Lab — SPIKE runner (throwaway; proves the mechanism, not the science).
#
# RUN THIS IN A PLAIN UBUNTU TERMINAL, NOT INSIDE CLAUDE CODE.
# (claude -p refuses to launch inside an existing Claude Code session.)
#
#   bash run.sh
#
# One task, two envelopes. For each: reset the workspace to the buggy fixture,
# run the agent headless, then grade OUTSIDE the agent's reach:
#   tests_pass    - does the locked test suite pass now?
#   tests_locked  - is the test file byte-identical to the fixture?
#   tokens/wall   - cost, read from the CLI's own JSON output.
set -uo pipefail

SPIKE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TASK="$(cat "$SPIKE/task.md")"

MINI_SKILL='Write the simplest change that works. Preserve existing behavior.
Do not modify test files. Keep the change scoped to the file named in the task.
Do not refactor or "clean up" code the task did not ask you to touch.'

run_setup() {
  local name="$1" envelope="$2"
  local dir="$SPIKE/$name"

  mkdir -p "$dir"
  cp "$SPIKE/fixture/account.py" "$SPIKE/fixture/test_account.py" "$dir/"

  echo "==> $name: running agent..."
  local start end wall
  start=$(date +%s)
  (
    cd "$dir" || exit 1
    if [ -z "$envelope" ]; then
      claude -p "$TASK" --permission-mode acceptEdits --output-format json
    else
      claude -p "$TASK" --append-system-prompt "$envelope" \
        --permission-mode acceptEdits --output-format json
    fi
  ) > "$SPIKE/$name.json" 2> "$SPIKE/$name.err"
  end=$(date +%s)
  wall=$((end - start))

  # --- grading, outside the agent's reach -------------------------------
  local tests_pass tests_locked
  if (cd "$dir" && python3 -m unittest test_account.py >/dev/null 2>&1); then
    tests_pass=PASS
  else
    tests_pass=FAIL
  fi
  if cmp -s "$dir/test_account.py" "$SPIKE/fixture/test_account.py"; then
    tests_locked=INTACT
  else
    tests_locked=TAMPERED
  fi

  local tokens
  tokens=$(python3 - "$SPIKE/$name.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    print("n/a"); raise SystemExit
u = d.get("usage") or {}
tot = sum(v for k, v in u.items() if isinstance(v, int) and "token" in k)
print(tot if tot else "n/a")
PY
)

  printf '%-12s | %-9s | %-8s | %-8s | %ss\n' \
    "$name" "$tests_pass" "$tests_locked" "$tokens" "$wall" >> "$SPIKE/results.txt"
}

: > "$SPIKE/results.txt"
run_setup "bare"       ""
run_setup "mini-skill" "$MINI_SKILL"

echo
echo "setup        | tests    | testfile | tokens   | wall"
echo "-------------|----------|----------|----------|------"
cat "$SPIKE/results.txt"
echo
echo "Raw agent output: $SPIKE/{bare,mini-skill}.json (stderr in *.err)"
