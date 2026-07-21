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

# The owner's real working setting. The D3 requirement is that it be constant, not
# that it be low.
EFFORT: Final = "max"


class ApparatusMismatchError(RuntimeError):
    """The run did not happen under the pinned conditions, so it is not a trial."""


def flags() -> list[str]:
    """CLI flags pinning the apparatus, identical for every setup.

    `--fallback-model` is deliberately absent: a fallback is a silent apparatus change
    in the middle of an unattended batch, which is precisely the failure probe B found.
    An overloaded model must fail loudly instead.
    """
    return ["--model", MODEL, "--effort", EFFORT]


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
