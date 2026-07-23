"""Trial workspace preparation: flat layout, git-initialized, harness-free."""

import subprocess
from pathlib import Path

import pytest

from harness_lab import workspace

TASK = Path(__file__).resolve().parent.parent / "tasks" / "01-account-bugs"


def test_prepare_flattens_fixture_and_tests_into_the_workspace(tmp_path: Path) -> None:
    """The task keeps `fixture/` and `tests/` apart so the grader knows what is locked;
    the agent sees the flat layout its task text describes
    (`python3 -m unittest test_account.py`).
    """
    ws = workspace.prepare(TASK, tmp_path / "ws")
    assert (ws / "account.py").is_file()
    assert (ws / "test_account.py").is_file()
    assert not (ws / "fixture").exists()
    assert not (ws / "tests").exists()


def test_prepare_git_initializes_with_one_commit(tmp_path: Path) -> None:
    """ADR 11 — the long skill instructs `git blame` (line 118) and `commit` (165).

    In a plain directory both fail, and the turns spent failing land in the cost
    metric as if the envelope had caused them.
    """
    ws = workspace.prepare(TASK, tmp_path / "ws")
    assert (ws / ".git").is_dir()
    log = subprocess.run(
        ["git", "-C", str(ws), "log", "--oneline"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert len(log.splitlines()) == 1


def test_prepared_workspace_is_clean_so_the_diff_is_the_agents_work(
    tmp_path: Path,
) -> None:
    """Everything is committed before the agent starts, so `git diff` afterwards is
    exactly what the trial produced — the basis for files_changed and loc+-.
    """
    ws = workspace.prepare(TASK, tmp_path / "ws")
    status = subprocess.run(
        ["git", "-C", str(ws), "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert status == ""


def test_prepare_refuses_a_destination_that_already_exists(tmp_path: Path) -> None:
    """Re-running into a used workspace would mix a previous run's artifacts into the
    new one, and the result would look like a single clean trial.
    """
    dest = tmp_path / "ws"
    workspace.prepare(TASK, dest)
    with pytest.raises(FileExistsError):
        workspace.prepare(TASK, dest)


def test_a_workspace_containing_harness_files_is_rejected(tmp_path: Path) -> None:
    """SPEC D8 — the harness must never leak into a trial.

    Two directions: pushed in by the runner, or pulled in by the envelope (long-skill
    line 49 tells the agent to "Read CLAUDE.md / project conventions"). This catches
    the state, whichever way it arrived.
    """
    ws = workspace.prepare(TASK, tmp_path / "ws")
    workspace.assert_no_harness_files(ws)  # clean: no raise

    for leak in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        path = ws / leak
        path.write_text("leaked\n")
        with pytest.raises(workspace.HarnessLeakError):
            workspace.assert_no_harness_files(ws)
        path.unlink()

    (ws / ".claude").mkdir()
    with pytest.raises(workspace.HarnessLeakError):
        workspace.assert_no_harness_files(ws)


def test_a_workspace_inside_a_repo_carrying_harness_files_is_rejected(
    tmp_path: Path,
) -> None:
    """The leak that made the first real trial invalid (2026-07-21).

    The CLI walks UP the directory tree for instruction files. Workspaces lived in
    `runs/` inside this repo, so every trial inherited harness-lab's own CLAUDE.md —
    the `bare` floor ran carrying two constitutions. Checking only the workspace
    directory looks at the wrong place entirely.
    """
    repo = tmp_path / "some-repo"
    repo.mkdir()
    (repo / "CLAUDE.md").write_text("# a parent constitution\n")

    ws = workspace.prepare(TASK, repo / "runs" / "trial" / "workspace")
    with pytest.raises(workspace.HarnessLeakError):
        workspace.assert_no_harness_files(ws)


def test_a_workspace_in_a_clean_temp_directory_passes(tmp_path: Path) -> None:
    """The condition probe A ran under — the only one observed clean."""
    ws = workspace.prepare(TASK, tmp_path / "isolated" / "workspace")
    workspace.assert_no_harness_files(ws)


def test_the_ancestor_walk_stops_at_the_filesystem_root(tmp_path: Path) -> None:
    """Guards against a check that silently does nothing.

    If the walk terminated early it would pass everything, and the test above would be
    the only thing standing between us and another invalid batch.
    """
    ws = workspace.prepare(TASK, tmp_path / "deep" / "a" / "b" / "c" / "workspace")
    (tmp_path / "deep" / "AGENTS.md").write_text("# four levels up\n")
    with pytest.raises(workspace.HarnessLeakError):
        workspace.assert_no_harness_files(ws)


def test_locked_test_file_is_recorded_so_tampering_can_be_detected(
    tmp_path: Path,
) -> None:
    """tests_locked is a hard fail in the success predicate (SPEC D3), so the
    pre-run hash has to exist before the agent touches anything.
    """
    ws = workspace.prepare(TASK, tmp_path / "ws")
    locked = workspace.locked_hashes(TASK)
    assert "test_account.py" in locked

    assert workspace.tests_locked(ws, locked)
    (ws / "test_account.py").write_text("# weakened\n")
    assert not workspace.tests_locked(ws, locked)
