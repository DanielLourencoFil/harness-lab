"""CLI entry point for a single trial. Invoked by scripts/run-trial.sh.

Orchestration only — every decision it makes lives in a tested module. What this file
owns is the order of operations and the lifetime of the temporary HOME.
"""

import shutil
import sys
import tempfile
from pathlib import Path

from harness_lab import apparatus, environment, trial, workspace

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

    stamp = f"{task_name}__{setup}"
    run_dir = RUNS / stamp
    home_parent = Path(tempfile.mkdtemp(prefix="harness-lab-home-"))

    try:
        home = environment.create_neutralized_home(home_parent)
        environment.assert_neutralized(home)

        ws = workspace.prepare(task_dir, run_dir / "workspace")
        workspace.assert_no_harness_files(ws)
        locked = workspace.locked_hashes(task_dir)

        task_text = (task_dir / "task.md").read_text(encoding="utf-8").strip()
        argv_cmd = trial.build_argv(task_text=task_text, setup=setup)

        print(f"task     : {task_name}")
        print(f"setup    : {setup}")
        print(f"model    : {apparatus.MODEL}  effort: {apparatus.EFFORT}")
        print(f"workspace: {ws}")
        print(f"HOME     : {home}  (neutralized)")
        print("running...", flush=True)

        raw = trial.invoke(argv_cmd, workspace=ws, home=home)
        (run_dir / "result.json").write_text(raw, encoding="utf-8")

        result = trial.parse_result(raw)
        tests_pass = _tests_pass(ws)
        locked_ok = workspace.tests_locked(ws, locked)

        print()
        print(f"tests_pass      : {'PASS' if tests_pass else 'FAIL'}")
        print(f"tests_locked    : {'INTACT' if locked_ok else 'TAMPERED'}")
        print(f"output_tokens   : {result.output_tokens}")
        print(f"num_turns       : {result.num_turns}")
        print(f"cache_read      : {result.cache_read}")
        print(f"cache_creation  : {result.cache_creation}")
        print(f"wall_ms         : {result.duration_ms}")
        print()
        print("cache fields are reported separately and never summed (SPEC F4).")
        print(f"raw result: {run_dir / 'result.json'}")
        return 0

    except (
        environment.ContaminatedEnvironmentError,
        environment.NestedSessionError,
        workspace.HarnessLeakError,
        apparatus.ApparatusMismatchError,
        trial.TrialFailedError,
    ) as exc:
        # No result row on an aborted trial: a half-written result enters the dataset
        # looking complete, which is worse than no result at all.
        print(f"\nABORTED — nothing recorded.\n  {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    finally:
        # Credentials must not outlive the run.
        shutil.rmtree(home_parent, ignore_errors=True)


def _tests_pass(ws: Path) -> bool:
    import subprocess

    return (
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(ws), "-p", "test_*.py"],
            capture_output=True,
            cwd=ws,
        ).returncode
        == 0
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
