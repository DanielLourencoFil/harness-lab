"""The task suite must stay a valid experiment.

A task is only a measurement if its locked tests actually fail on its fixture. If
someone "helpfully" fixes a fixture — or a formatter rewrites one — every setup passes
trivially, the table fills with 100% success, and nothing in the pipeline notices.
"""

from pathlib import Path

import pytest

from harness_lab import grade, tasks, workspace

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

    Grades through `grade.grade` rather than re-spelling the command: the audit found
    it written byte-identically here and in the runner, two copies of one predicate
    that could drift apart with nothing failing (R6).
    """
    ws = workspace.prepare(task, tmp_path / task.name)
    result = grade.grade(task, ws, tmp_path / f"{task.name}-grading")
    assert not result.tests_pass, (
        f"{task.name}: the locked tests PASS on the untouched fixture, so the task "
        f"asks the agent for nothing and every setup will score a free success."
    )


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda p: p.name)
def test_task_content_matches_its_frozen_hash(task: Path) -> None:
    """SPEC section 5 — the suite is frozen before any setup runs (R5).

    The freeze was prose: deleting "Do not edit test_account.py" from task.md left
    verify green. Changing a task is legitimate; changing it silently is not, and
    changing it after seeing results is unrecoverable.
    """
    assert task.name in tasks.FROZEN, f"{task.name} is not frozen; add its hash"
    assert tasks.content_hash(task) == tasks.FROZEN[task.name], (
        f"{task.name} has drifted from its frozen content. If this change is "
        f"intentional AND no results depend on the old version, update FROZEN in the "
        f"same commit and say why in the message."
    )


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda p: p.name)
def test_task_declares_its_type_blind(task: Path) -> None:
    """SPEC section 4 — results are always sliced by task type.

    Written now, before any setup has run: classifying tasks once results are visible
    is itself an edit-after-results.
    """
    meta = tasks.load_meta(task)
    assert meta.id == task.name


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda p: p.name)
def test_task_carries_no_harness_files(task: Path, tmp_path: Path) -> None:
    """SPEC D8 from the other end: a leak planted in the task reaches every setup."""
    ws = workspace.prepare(task, tmp_path / task.name)
    workspace.assert_no_harness_files(ws)
