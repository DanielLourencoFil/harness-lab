"""Trial zero: ask the agent what instruction files it was given, before measuring.

Structural checks look at what we know to look for. This asks the only witness that
sees everything — the agent — and it exists because the structural checks were not
enough on 2026-07-21:

- `assert_neutralized` passed (HOME held only credentials);
- `assert_no_harness_files` passed (the workspace directory was clean);
- and the trial still ran carrying two constitutions, because the CLI reads
  instruction files from ancestor directories and the workspace lived inside this
  repo.

Both guards reported clean while the floor was contaminated. This one would have
caught it, so it runs before a batch and aborts it — not a command someone remembers
to type.
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Final

from harness_lab import apparatus, environment

PROMPT: Final = (
    "List every instruction file whose contents appear in your system instructions "
    "(CLAUDE.md, AGENTS.md, or similar), giving the exact path of each. "
    "Reply with exactly NONE if there are none."
)

# The agent answers in prose, so the check is deliberately blunt: any path-shaped
# mention of an instruction file counts as contamination. A false positive costs one
# investigation; a false negative costs a whole batch of invalid numbers.
_MARKERS: Final[tuple[str, ...]] = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules")


class ContaminationError(RuntimeError):
    """The agent reports instruction files, so trials here would not measure the floor."""


def is_clean(answer: str) -> bool:
    """True when the agent reports no instruction files.

    `NONE` alone is not required — the agent may say "NONE" in a sentence — but any
    mention of an instruction file name is treated as contamination.
    """
    return not any(marker in answer for marker in _MARKERS)


def parse_answer(raw: str) -> str:
    payload: dict[str, Any] = json.loads(raw)
    if payload.get("is_error", True):
        raise ContaminationError(
            f"Contamination check could not run: {str(payload.get('result'))[:200]!r}"
        )
    return str(payload.get("result", ""))


def check(workspace: Path, home: Path) -> str:
    """Run trial zero in `workspace`. Returns the agent's answer; raises if dirty.

    Runs in the exact directory the trials will run in, because the contamination
    found on 2026-07-21 depended on the working directory and nothing else.
    """
    argv = [
        "claude",
        "-p",
        PROMPT,
        "--output-format",
        "json",
        *apparatus.flags(),
    ]
    completed = subprocess.run(
        argv,
        cwd=workspace,
        env=environment.trial_env(home),
        capture_output=True,
        text=True,
    )
    if not completed.stdout.strip():
        raise ContaminationError(
            f"Contamination check produced no output (exit {completed.returncode}): "
            f"{completed.stderr[:200]!r}"
        )

    answer = parse_answer(completed.stdout)
    if not is_clean(answer):
        raise ContaminationError(
            "The agent reports instruction files in this workspace, so a trial here "
            "would measure the harness rather than the floor.\n\n"
            f"Workspace: {workspace}\n"
            f"Agent said:\n{answer}"
        )
    return answer
