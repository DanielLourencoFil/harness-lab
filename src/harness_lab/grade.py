"""The success predicate, assembled in one place.

SPEC D3: `success ≡ tests_pass AND tests_locked AND scope_ok`, evaluated by the grader
outside the agent's reach, identically for every setup. Before the audit of 2026-07-21
the terms were computed in two files and printed separately; the conjunction existed
only in a reader's head, and the grading command was spelled twice, byte-identical, in
places that could drift apart without anything failing.

**Grading never happens inside the agent's workspace.** The grader reconstructs a
directory containing exactly the task's declared fixture files (in the agent's
version) plus the locked test files (in the task's pristine version), and runs there.
Anything else the agent created is excluded by construction — including a directory
named `unittest`, which in the agent's own workspace would shadow the standard library
and let a trial report a pass it did not earn.

That reconstruction is also what makes `scope_ok` cheap: a file the agent created that
the task never declared is, definitionally, out of scope.
"""

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from harness_lab import workspace


@dataclass(frozen=True)
class Grade:
    """The D3 predicate and its terms. `success` is never computed anywhere else."""

    tests_pass: bool
    tests_locked: bool
    scope_ok: bool
    out_of_scope_files: tuple[str, ...]

    @property
    def success(self) -> bool:
        return self.tests_pass and self.tests_locked and self.scope_ok


def declared_files(task_dir: Path) -> tuple[frozenset[str], frozenset[str]]:
    """(fixture file names, locked test file names) — what a task says it consists of."""
    fixtures = frozenset(p.name for p in (task_dir / "fixture").iterdir() if p.is_file())
    tests = frozenset(p.name for p in (task_dir / "tests").iterdir() if p.is_file())
    return fixtures, tests


def out_of_scope(task_dir: Path, ws: Path) -> tuple[str, ...]:
    """Files present in the workspace that the task never declared.

    `.git/` is excluded: the runner created it (ADR 11), so it is the instrument's
    doing, not the agent's.
    """
    fixtures, tests = declared_files(task_dir)
    declared = fixtures | tests
    found: list[str] = []
    for path in sorted(ws.rglob("*")):
        relative = path.relative_to(ws)
        if relative.parts and relative.parts[0] == ".git":
            continue
        if path.is_file() and str(relative) not in declared:
            found.append(str(relative))
    return tuple(found)


def run_locked_tests(task_dir: Path, ws: Path, into: Path) -> bool:
    """Grade in `into`, a reconstructed directory the agent never touched.

    Only declared files are copied: the agent's fixtures, the task's pristine tests.
    An agent that wrote its own `unittest` package cannot follow the code here.
    """
    into.mkdir(parents=True, exist_ok=True)
    fixtures, tests = declared_files(task_dir)

    for name in sorted(fixtures):
        source = ws / name
        if source.is_file():
            shutil.copyfile(source, into / name)
    for name in sorted(tests):
        # Pristine, from the task — never the workspace copy, which the agent may have
        # edited. tests_locked reports that separately; grading uses the real test.
        shutil.copyfile(task_dir / "tests" / name, into / name)

    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(into), "-p", "test_*.py"],
        capture_output=True,
        cwd=into,
    )
    return completed.returncode == 0


def grade(task_dir: Path, ws: Path, into: Path) -> Grade:
    """Evaluate D3 for one finished trial."""
    offenders = out_of_scope(task_dir, ws)
    return Grade(
        tests_pass=run_locked_tests(task_dir, ws, into),
        tests_locked=workspace.tests_locked(ws, workspace.locked_hashes(task_dir)),
        scope_ok=not offenders,
        out_of_scope_files=offenders,
    )
