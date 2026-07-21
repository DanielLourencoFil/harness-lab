"""CLI entry point for a single trial. Invoked by scripts/run-trial.sh.

Orchestration only — every decision it makes lives in a tested module. What this file
owns is the order of operations, the lifetime of the temporary HOMEs, and writing the
record.
"""

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from harness_lab import apparatus, contamination, environment, grade, tasks, trial, workspace

ROOT = Path(__file__).resolve().parent.parent.parent
RUNS = ROOT / "runs"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m harness_lab.run_trial <task-name> <setup>", file=sys.stderr)
        return 2
    task_name, setup = argv

    task_dir = ROOT / "tasks" / task_name
    if not task_dir.is_dir():
        print(f"No such task: {task_dir}", file=sys.stderr)
        return 2

    try:
        environment.assert_not_nested()
    except environment.NestedSessionError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3

    started = datetime.now(UTC)
    run_dir = RUNS / f"{task_name}__{setup}__{started:%Y%m%dT%H%M%SZ}"
    run_dir.mkdir(parents=True)
    # The workspace lives OUTSIDE this repository: the CLI reads instruction files from
    # ancestor directories, so a workspace under runs/ inherits harness-lab's own
    # CLAUDE.md (ADR 16). runs/ holds the record, which is output, not a working tree.
    ws_parent = Path(tempfile.mkdtemp(prefix="harness-lab-trial-"))

    record: dict[str, Any] = {
        "task": task_name,
        "setup": setup,
        "started_at": started.isoformat(),
        "model": apparatus.MODEL,
        "effort": apparatus.EFFORT,
        "allowed_tools": list(apparatus.ALLOWED_TOOLS),
        "task_hash": tasks.content_hash(task_dir),
    }

    try:
        meta = tasks.load_meta(task_dir)
        record |= {"task_type": meta.type, "difficulty": meta.difficulty}

        ws = workspace.prepare(task_dir, ws_parent / "workspace")
        workspace.assert_no_harness_files(ws)

        task_text = (task_dir / "task.md").read_text(encoding="utf-8").strip()
        argv_cmd = trial.build_argv(task_text=task_text, setup=setup)

        print(f"task     : {task_name}  ({meta.type}, {meta.difficulty})")
        print(f"setup    : {setup}")
        print(f"model    : {apparatus.MODEL}  effort: {apparatus.EFFORT}")
        print(f"tools    : {' '.join(apparatus.ALLOWED_TOOLS)}")
        print(f"workspace: {ws}")

        # Trial zero. The structural guards both passed on 2026-07-21 while the floor
        # was contaminated; this asks the agent itself, in the exact directory the
        # trial will use. Its own HOME, because an invocation dirties one.
        print("checking for contamination...", flush=True)
        with environment.neutralized_home() as probe_home:
            answer = contamination.check(ws, probe_home)
        (run_dir / "contamination.txt").write_text(answer, encoding="utf-8")
        print(f"  agent reports: {answer.strip()[:80]}")

        print("running...", flush=True)
        with environment.neutralized_home() as home:
            raw = trial.invoke(argv_cmd, workspace=ws, home=home)
        (run_dir / "result.json").write_text(raw, encoding="utf-8")

        result = trial.parse_result(raw)
        graded = grade.grade(task_dir, ws, ws_parent / "grading")

        record |= {
            "outcome": "completed",
            "success": graded.success,
            "tests_pass": graded.tests_pass,
            "tests_locked": graded.tests_locked,
            "scope_ok": graded.scope_ok,
            "out_of_scope_files": list(graded.out_of_scope_files),
            "output_tokens": result.output_tokens,
            "num_turns": result.num_turns,
            "cache_read": result.cache_read,
            "cache_creation": result.cache_creation,
            "wall_ms": result.duration_ms,
            "cap_hit": False,
            "auxiliary_model_tokens": apparatus.auxiliary_usage(json.loads(raw)),
            "workspace": str(ws),
        }
        _write(run_dir, record)
        _report(record, run_dir)
        return 0

    except trial.CapExceededError as exc:
        # A cap hit is data, not an abort: SPEC section 5 requires cap_hit per setup,
        # and a cage that fails to converge is a result about the cage.
        record |= {"outcome": "cap_hit", "success": False, "cap_hit": True, "error": str(exc)}
        _write(run_dir, record)
        print(f"\nCAP HIT — recorded.\n  {exc}", file=sys.stderr)
        return 1

    except (
        contamination.ContaminationError,
        environment.ContaminatedEnvironmentError,
        environment.NestedSessionError,
        workspace.HarnessLeakError,
        apparatus.ApparatusMismatchError,
        trial.TrialFailedError,
        ValueError,
    ) as exc:
        # No measurement row on an aborted trial: a half-written result enters the
        # dataset looking complete, which is worse than no result. The abort itself is
        # recorded, so a batch leaves a trace of what it refused to measure.
        (run_dir / "aborted.json").write_text(
            json.dumps(record | {"outcome": "aborted", "error": f"{type(exc).__name__}: {exc}"}),
            encoding="utf-8",
        )
        print(
            f"\nABORTED — no measurement recorded.\n  {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1


def _write(run_dir: Path, record: dict[str, Any]) -> None:
    """The grade belongs on disk, not in terminal scrollback (audit R7)."""
    (run_dir / "trial.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def _report(record: dict[str, Any], run_dir: Path) -> None:
    print()
    print(f"D3 success      : {'SUCCESS' if record['success'] else 'FAILURE'}")
    print(f"  tests_pass    : {'PASS' if record['tests_pass'] else 'FAIL'}")
    print(f"  tests_locked  : {'INTACT' if record['tests_locked'] else 'TAMPERED'}")
    print(f"  scope_ok      : {'OK' if record['scope_ok'] else record['out_of_scope_files']}")
    print(f"output_tokens   : {record['output_tokens']}")
    print(f"num_turns       : {record['num_turns']}")
    print(f"cache_read      : {record['cache_read']}")
    print(f"cache_creation  : {record['cache_creation']}")
    print(f"wall_ms         : {record['wall_ms']}")
    print()
    print("cache fields are reported separately and never summed (SPEC F4).")
    print(f"record: {run_dir / 'trial.json'}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
