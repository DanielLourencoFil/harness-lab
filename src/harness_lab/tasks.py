"""Task metadata and the freeze that keeps the suite an experiment.

Two things the audit of 2026-07-21 found missing (R5).

**The task is an experimental variable and was unpinned.** ADR 12 hashes the
envelopes because "drift in an experimental variable produces runs that still succeed
while silently measuring something else". The task text, the fixture and the locked
tests are exactly as load-bearing, and nothing hashed them: deleting "Do not edit
test_account.py" from `task.md` left `verify` green. SPEC section 5 requires the suite
"frozen before any setup runs (authorship bias guard)" — the freeze was prose.

**Tasks carried no type.** SPEC section 4 requires results "always sliced by task type
— never only the aggregate", because the aggregate can invert the story. Classifying
tasks after Suite Zero results are visible would itself be an edit-after-results, so
the classification is written now, while it is still blind.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

TASKS_DIR: Final = Path(__file__).resolve().parent.parent.parent / "tasks"

# Written blind, before any setup has run against these tasks.
TASK_TYPES: Final[frozenset[str]] = frozenset(
    {"bug-fix", "pure-function", "simplify-under-locked-tests", "boundary-validation"}
)
DIFFICULTIES: Final[frozenset[str]] = frozenset({"trivial", "hard"})


@dataclass(frozen=True)
class TaskMeta:
    id: str
    type: str
    difficulty: str
    temptation: bool


def load_meta(task_dir: Path) -> TaskMeta:
    raw = json.loads((task_dir / "task.json").read_text(encoding="utf-8"))
    if raw["type"] not in TASK_TYPES:
        raise ValueError(f"{task_dir.name}: unknown task type {raw['type']!r}")
    if raw["difficulty"] not in DIFFICULTIES:
        raise ValueError(f"{task_dir.name}: unknown difficulty {raw['difficulty']!r}")
    return TaskMeta(
        id=raw["id"],
        type=raw["type"],
        difficulty=raw["difficulty"],
        temptation=bool(raw["temptation"]),
    )


def content_hash(task_dir: Path) -> str:
    """One hash over everything that defines the task.

    Covers `task.md`, every fixture file and every locked test, name and bytes, in
    sorted order — so a renamed file changes the hash as surely as an edited one.
    `task.json` is excluded: it labels the task, it is not the task the agent sees.
    """
    digest = hashlib.sha256()
    parts: list[Path] = [task_dir / "task.md"]
    for sub in ("fixture", "tests"):
        parts += sorted(p for p in (task_dir / sub).iterdir() if p.is_file())

    for path in parts:
        digest.update(path.relative_to(task_dir).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


# The freeze. A task changing is legitimate; doing it silently is not, and doing it
# after seeing results is unrecoverable — no amount of care un-sees them.
FROZEN: Final[dict[str, str]] = {
    "01-account-bugs": "864a869a7058ced0f4b0d826de073b0edd4d9cee5ec6c3414f811654d6c6a832",
}
