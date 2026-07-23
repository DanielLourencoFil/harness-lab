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

# A POSITIVE clean signal, not the absence of known-bad substrings. The first version
# of this check was a blacklist of four filenames, and it failed open twice (audit R2):
# an empty answer read clean, and so did an answer naming a skill or a settings file,
# because those were not on the list. SPEC F9 defines the harness as constitution,
# hooks, skills and memory — a list of constitutions was never going to cover it.
#
# environment.py says why this shape is required, four lines above its own allowlist:
# deciding neutrality by enumerating what must be absent means the day something new
# appears is the day the check starts lying. This module now obeys the same rule.
_CLEAN_TOKEN: Final = "NONE"


class ContaminationError(RuntimeError):
    """The agent reports instruction files, so trials here would not measure the floor."""


def is_clean(answer: str) -> bool:
    """True only when the agent's whole answer is the agreed clean token.

    Strict equality after normalization, deliberately. An answer that explains, hedges
    or lists anything is not clean — and an empty answer is not clean either, which is
    the fail-open path the first version had: `parse_answer` returns "" when the CLI
    omits `result`, and "" contained none of the banned substrings.

    The cost of strictness is a false positive: the agent says "NONE — I see no
    instruction files" and the batch stops for one investigation. The cost of leniency
    is a batch of invalid numbers. ADR 18 already priced that trade.
    """
    return answer.strip().rstrip(".").upper() == _CLEAN_TOKEN


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
