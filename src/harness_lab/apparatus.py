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


def verify_model(result: dict[str, Any]) -> None:
    """Raise unless the result reports exactly the pinned model.

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

    models = set(usage.keys())
    if models != {MODEL}:
        raise ApparatusMismatchError(
            f"Trial ran on {sorted(models)}, pinned model is {MODEL}. "
            f"Comparisons across setups assume one model (SPEC D3)."
        )
