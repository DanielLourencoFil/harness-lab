"""One trial: build the invocation, run it, read the result.

Everything that decides something is pure and tested without mocks. The subprocess
call is the one thin line the tests do not cross — non-determinism behind a fakeable
seam, per AGENTS.md.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from harness_lab import apparatus, envelopes, environment
from harness_lab import workspace as workspace_module


class TrialFailedError(RuntimeError):
    """The invocation did not produce a usable trial, so nothing is recorded."""


@dataclass(frozen=True)
class TrialResult:
    """What one invocation cost and did.

    Deliberately offers no summed token total. SPEC F4: summing every field with
    "token" in its name gave 91% cache_read and inverted under --append-system-prompt
    cache invalidation, producing a headline ("the mini-skill costs 20% more") that was
    false. Cache fields are carried, separately, and never added to anything.
    """

    output_tokens: int
    num_turns: int
    cache_read: int
    cache_creation: int
    duration_ms: int

    def cost_signature(self) -> tuple[int, int]:
        """The behavioral cost pair comparisons are made on (ADR 7)."""
        return (self.output_tokens, self.num_turns)


def build_argv(task_text: str, setup: str) -> list[str]:
    """The exact command for a trial. Pure — no filesystem, no environment."""
    argv = ["claude", "-p", task_text, "--output-format", "json"]
    argv += apparatus.flags()
    argv += ["--permission-mode", "acceptEdits"]

    envelope = envelopes.render(setup)
    if envelope:
        # `bare` appends nothing at all: an empty --append-system-prompt would still
        # append an empty section, which is not the same as having no envelope.
        argv += ["--append-system-prompt", envelope]
    return argv


def parse_result(raw: str) -> TrialResult:
    """Read the CLI's JSON, refusing everything that is not a completed trial."""
    try:
        payload: dict[str, Any] = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise TrialFailedError(f"Output is not JSON, so it is not a trial: {raw[:200]!r}") from exc

    # Probe A returned subtype "success" on a run that failed to authenticate. The
    # success signal is is_error, never subtype.
    if payload.get("is_error", True):
        raise TrialFailedError(
            f"Run reported is_error=true (subtype={payload.get('subtype')!r}, "
            f"result={str(payload.get('result'))[:120]!r})."
        )

    apparatus.verify_model(payload)

    usage: dict[str, Any] = payload.get("usage") or {}
    output_tokens = int(usage.get("output_tokens", 0))
    if output_tokens == 0:
        raise TrialFailedError(
            "Run produced 0 output tokens — the signature of an aborted or refused "
            "run, not of a cheap one."
        )

    return TrialResult(
        output_tokens=output_tokens,
        num_turns=int(payload.get("num_turns", 0)),
        cache_read=int(usage.get("cache_read_input_tokens", 0)),
        cache_creation=int(usage.get("cache_creation_input_tokens", 0)),
        duration_ms=int(payload.get("duration_ms", 0)),
    )


def invoke(argv: list[str], workspace: Path, home: Path) -> str:
    """Run the agent. The seam: the only function here that is not pure.

    All three guards fire before the process starts, because a contaminated or nested
    run cannot be repaired afterwards — the tokens are spent and the run measured the
    wrong thing.
    """
    environment.assert_not_nested()
    environment.assert_neutralized(home)
    workspace_module.assert_no_harness_files(workspace)

    completed = subprocess.run(
        argv,
        cwd=workspace,
        env=environment.trial_env(home),
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0 and not completed.stdout.strip():
        raise TrialFailedError(
            f"claude exited {completed.returncode} with no output. "
            f"stderr: {completed.stderr[:300]!r}"
        )
    return completed.stdout
