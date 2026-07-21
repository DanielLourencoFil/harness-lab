"""The task suite must stay a valid experiment.

A task is only a measurement if its locked tests actually fail on its fixture. If
someone "helpfully" fixes a fixture — or a formatter rewrites one — every setup passes
trivially, the table fills with 100% success, and nothing in the pipeline notices.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from harness_lab import workspace

TASKS = Path(__file__).resolve().parent.parent / "tasks"
ALL_TASKS = sorted(p for p in TASKS.iterdir() if p.is_dir())


def test_there_is_at_least_one_task() -> None:
    assert ALL_TASKS


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda p: p.name)
def test_task_has_the_required_layout(task: Path) -> None:
    assert (task / "task.md").is_file()
    assert (task / "fixture").is_dir()
    assert (task / "tests").is_dir()
    assert any((task / "fixture").iterdir())
    assert any((task / "tests").iterdir())


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda p: p.name)
def test_locked_tests_fail_on_the_untouched_fixture(task: Path, tmp_path: Path) -> None:
    """The task is only a task while its tests are red before the agent starts.

    This is the guard against the quietest possible corruption of the suite: a fixture
    that no longer contains the bug still runs, still grades, and reports success for
    every setup.
    """
    ws = workspace.prepare(task, tmp_path / task.name)
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(ws), "-p", "test_*.py"],
        capture_output=True,
        text=True,
        cwd=ws,
    )
    assert completed.returncode != 0, (
        f"{task.name}: the locked tests PASS on the untouched fixture, so the task "
        f"asks the agent for nothing and every setup will score a free success."
    )


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda p: p.name)
def test_task_carries_no_harness_files(task: Path, tmp_path: Path) -> None:
    """SPEC D8 from the other end: a leak planted in the task reaches every setup."""
    ws = workspace.prepare(task, tmp_path / task.name)
    workspace.assert_no_harness_files(ws)
