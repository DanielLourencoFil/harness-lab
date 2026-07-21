"""Trial workspace preparation.

A task keeps `fixture/` (the agent may edit) and `tests/` (locked) apart so the grader
knows which is which. The agent sees them flattened into one directory, because that
is the layout its task text describes.
"""

import hashlib
import subprocess
from pathlib import Path
from typing import Final

# Files whose presence means the harness reached a trial workspace (SPEC D8). The leak
# has two directions: pushed in by the runner, or pulled in by the envelope — the long
# skill tells the agent to "Read CLAUDE.md / project conventions" (line 49).
_HARNESS_MARKERS: Final[tuple[str, ...]] = (
    "CLAUDE.md",
    "AGENTS.md",
    "GEMINI.md",
    ".claude",
    ".cursorrules",
)


class HarnessLeakError(RuntimeError):
    """The harness reached a trial workspace, so the trial's envelope is not its own."""


def _git(workspace: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(workspace), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def prepare(task_dir: Path, dest: Path) -> Path:
    """Materialize a clean workspace for one trial.

    Refuses an existing destination: re-running into a used workspace would blend a
    previous run's edits into the new one and the result would look like a single
    clean trial.
    """
    if dest.exists():
        raise FileExistsError(
            f"{dest} already exists. Each trial gets a fresh workspace so its diff is "
            f"only its own work."
        )
    dest.mkdir(parents=True)

    for source in (task_dir / "fixture", task_dir / "tests"):
        for path in sorted(source.iterdir()):
            if path.is_file():
                (dest / path.name).write_bytes(path.read_bytes())

    # ADR 11: git blame and commit are instructed by the long skill; in a plain
    # directory they fail and the turns spent failing land in the cost metric.
    _git(dest, "init", "--quiet", "--initial-branch=main")
    _git(dest, "config", "user.email", "runner@harness-lab.invalid")
    _git(dest, "config", "user.name", "harness-lab runner")
    _git(dest, "add", "-A")
    _git(dest, "commit", "--quiet", "-m", "task fixture")
    return dest


def assert_no_harness_files(workspace: Path) -> None:
    """Raise if the workspace carries harness files (SPEC D8)."""
    found = [marker for marker in _HARNESS_MARKERS if (workspace / marker).exists()]
    if found:
        raise HarnessLeakError(
            f"Harness files in trial workspace {workspace}: {found}. The trial's only "
            f"envelope must be the setup under test."
        )


def locked_hashes(task_dir: Path) -> dict[str, str]:
    """sha256 of every locked test file, taken from the task rather than the workspace.

    Reading the baseline from the task means a workspace tampered with before the hash
    was taken cannot define its own "unmodified".
    """
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((task_dir / "tests").iterdir())
        if path.is_file()
    }


def tests_locked(workspace: Path, expected: dict[str, str]) -> bool:
    """True when every locked test file is byte-identical to the task's copy.

    A hard fail in the success predicate (SPEC D3): weakening a test to go green is
    exactly the corner-cutting the force-cage's pressure to converge might induce.
    """
    for name, digest in expected.items():
        path = workspace / name
        if not path.is_file():
            return False
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            return False
    return True
