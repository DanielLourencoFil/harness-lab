"""CLI entry point for a single trial. Invoked by scripts/run-trial.sh.

Orchestration only — every decision it makes lives in a tested module. What this file
owns is the order of operations and the lifetime of the temporary HOME.
"""

import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from harness_lab import apparatus, contamination, environment, trial, workspace

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

    stamp = f"{task_name}__{setup}__{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
    run_dir = RUNS / stamp
    run_dir.mkdir(parents=True)
    home_parent = Path(tempfile.mkdtemp(prefix="harness-lab-home-"))
    # The workspace lives OUTSIDE this repository. On 2026-07-21 workspaces sat in
    # runs/ and every trial inherited harness-lab's own CLAUDE.md, because the CLI
    # reads instruction files from ancestor directories. Results stay in runs/ — they
    # are output, not the agent's working directory.
    ws_parent = Path(tempfile.mkdtemp(prefix="harness-lab-trial-"))

    try:
        home = environment.create_neutralized_home(home_parent)
        environment.assert_neutralized(home)

        ws = workspace.prepare(task_dir, ws_parent / "workspace")
        workspace.assert_no_harness_files(ws)
        locked = workspace.locked_hashes(task_dir)

        task_text = (task_dir / "task.md").read_text(encoding="utf-8").strip()
        argv_cmd = trial.build_argv(task_text=task_text, setup=setup)

        print(f"task     : {task_name}")
        print(f"setup    : {setup}")
        print(f"model    : {apparatus.MODEL}  effort: {apparatus.EFFORT}")
        print(f"workspace: {ws}")
        print(f"HOME     : {home}  (neutralized)")

        # Trial zero. The structural guards above both passed on 2026-07-21 while the
        # floor was contaminated; this asks the agent itself, in the exact directory
        # the trial will run in.
        print("checking for contamination...", flush=True)
        answer = contamination.check(ws, home)
        (run_dir / "contamination.txt").write_text(answer, encoding="utf-8")
        print(f"  agent reports: {answer.strip()[:80]}")

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
        contamination.ContaminationError,
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
        # The workspace is kept: its diff is the trial's artifact. Its path is printed
        # above so a failed trial can be inspected.


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
