"""The measurement conditions, pinned and then verified.

SPEC D3 requires the model to be identical across setups. Probe B (2026-07-21) showed
that requirement is not self-enforcing: neutralizing HOME dropped the model from
`claude-opus-4-6` to the CLI default `claude-sonnet-4-6` with no warning, because the
model was coming from `~/.claude/settings.json` all along.

So the apparatus is pinned by flag *and* checked against what actually ran. A flag is
an intention; the `modelUsage` key in the result is evidence.
"""

from typing import Any, Final

# Full name, never the `opus` alias: an alias resolves to whatever is newest, so a
# batch run across a model release would silently mix two models. SPEC section 9
# already concedes the numbers expire when the model changes — which is only an honest
# limit if the record says which model produced them.
MODEL: Final = "claude-opus-4-8"

# DECLARED LIMIT (2026-07-21, first real trial): the owner's machine runs
# `effortLevel: max`, but `--effort max` is rejected by the CLI for Claude.ai
# subscribers ("Please use low, medium, or high"), so the lab cannot reproduce that
# condition through the flag. `high` is the closest available.
#
# This satisfies D3, which requires the effort to be CONSTANT across setups, not
# maximal. It does mean the lab measures at a slightly lower effort than the owner's
# interactive sessions — a limit that belongs in FINDINGS, not a detail to bury.
EFFORT: Final = "high"


class ApparatusMismatchError(RuntimeError):
    """The run did not happen under the pinned conditions, so it is not a trial."""


# The tool grant is a measurement condition, not an invocation detail — D3 requires it
# constant across setups AND non-interacting with the envelope, and it was neither
# until the audit of 2026-07-21 (finding C1).
#
# `--permission-mode acceptEdits` alone auto-accepts edits but still DENIES Bash, and
# headless nothing ever approves it. The first real trial recorded the agent saying
# "The tests need approval to run." The cost of that is differential: `bare` and
# `mini-skill` hit one Bash-requiring instruction (the task text), while `long-skill`
# carries about nine of its own (run tests after each change, git blame, commit,
# build, linter). Every denial burns a turn, and num_turns is half the ADR 7 cost
# signature — so the long setup would have measured as more expensive because of a
# permission flag, not because of its length. That is the F4 failure mode in a third
# place.
#
# Deciding it explicitly, narrowly, and identically for every setup:
#   Bash(python3:*)  the task text asks for `python3 -m unittest test_account.py`
#   Bash(git:*)      what ADR 11 git-initializes the workspace to make possible
# Nothing else — no network, no installs, no writes outside the workspace.
# `--dangerously-skip-permissions` is rejected: it would close the confound by opening
# everything, and its own help text limits it to sandboxes with no internet.
ALLOWED_TOOLS: Final[tuple[str, ...]] = ("Bash(python3:*)", "Bash(git:*)")

# SPEC D6 asks for caps on turns, tokens and wall clock; SPEC section 5 requires them
# "generous and equal across setups", with cap_hit reported per setup.
#
# DECLARED LIMIT: this CLI has no --max-turns and no token cap, so **only wall clock is
# enforceable inside one invocation**. D2's equal-budget guard — "bare and force-cage
# capped at the same turns/tokens, so the cage never wins merely by being allowed more
# attempts" — therefore has to be built from what is enforceable: the same wall-clock
# cap per invocation, and an equal cap on the force-cage's re-invocations, which the
# runner does control. That is a weaker guarantee than D2 assumed and belongs in
# FINDINGS: within a single invocation, an agent may take as many turns as it likes.
#
# Generous by design (the clean bare trial took 13s): the cap exists to stop an
# unattended batch hanging, not to shape behaviour.
WALL_CLOCK_CAP_S: Final = 600


def flags() -> list[str]:
    """CLI flags pinning the apparatus, identical for every setup.

    `--fallback-model` is deliberately absent: a fallback is a silent apparatus change
    in the middle of an unattended batch, which is precisely the failure probe B found.
    An overloaded model must fail loudly instead.
    """
    return [
        "--model",
        MODEL,
        "--effort",
        EFFORT,
        "--permission-mode",
        "acceptEdits",
        "--allowedTools",
        " ".join(ALLOWED_TOOLS),
    ]


def verify_no_denials(result: dict[str, Any]) -> None:
    """Raise if the agent was denied a tool it was instructed to use.

    A denial is not a neutral event: it costs a turn, and the number of denials
    depends on how many times an envelope tells the agent to run something. Measuring
    that as envelope cost is measuring the permission configuration.
    """
    denials = result.get("permission_denials") or []
    if denials:
        names = sorted({str(d.get("tool_name")) for d in denials})
        raise ApparatusMismatchError(
            f"The agent was denied {len(denials)} tool call(s) ({', '.join(names)}). "
            f"Denials cost turns, and their count varies by envelope, so this trial's "
            f"cost is partly a property of the permission grant. Allowed tools: "
            f"{list(ALLOWED_TOOLS)}."
        )


# The CLI runs a cheap model for its own internal chores — observed 2026-07-21, once
# tools were granted: a trial reported both `claude-opus-4-8` (673 output tokens, the
# actual work) and `claude-haiku-4-5-20251001` (32 output tokens), the latter almost
# certainly generating the one-line descriptions the CLI attaches to Bash calls.
#
# This is apparatus, not the agent under test, and refusing it would make every
# tool-using trial unrunnable. But it is allowed by NAME PREFIX and nothing else: the
# whole point of this check is that probe B found the model silently becoming Sonnet,
# and "allow any extra model" would hand that failure straight back.
#
# The top-level `usage.output_tokens` reports the MAIN model only — verified against
# the same result: 673, not 673+32 — so the ADR 7 cost signature is unaffected.
# Auxiliary usage is recorded separately and never folded in, because the number of
# internal calls tracks the number of tool calls, which varies by envelope: the same
# shape as C1, small, and worth keeping visible rather than absorbed.
AUXILIARY_MODEL_PREFIXES: Final[tuple[str, ...]] = ("claude-haiku",)


def auxiliary_usage(result: dict[str, Any]) -> dict[str, int]:
    """Output tokens per auxiliary model, for the record. Never part of the cost pair."""
    usage = result.get("modelUsage") or {}
    return {name: int(data.get("outputTokens", 0)) for name, data in usage.items() if name != MODEL}


def verify_model(result: dict[str, Any]) -> None:
    """Raise unless the pinned model did the work, and only known helpers assisted.

    Absence is not agreement: a result with no `modelUsage` (probe A's failed run
    returned `{}`) is unverifiable and therefore discarded, never assumed to have run
    under the pin.
    """
    usage = result.get("modelUsage")
    if not isinstance(usage, dict) or not usage:
        raise ApparatusMismatchError(
            "Result records no modelUsage, so the model that ran it cannot be "
            "verified. An unverifiable trial is discarded."
        )

    if MODEL not in usage:
        raise ApparatusMismatchError(
            f"Trial ran on {sorted(usage)}, and the pinned model {MODEL} is not among "
            f"them. Comparisons across setups assume one model (SPEC D3)."
        )

    unexpected = [
        name for name in usage if name != MODEL and not name.startswith(AUXILIARY_MODEL_PREFIXES)
    ]
    if unexpected:
        raise ApparatusMismatchError(
            f"Trial also ran on {sorted(unexpected)}, which is neither the pinned "
            f"model nor a known CLI helper. A second substantive model makes the "
            f"trial uninterpretable (SPEC D3)."
        )
