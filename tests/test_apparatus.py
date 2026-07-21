"""The apparatus is pinned, and then verified against what actually ran.

Probe B (2026-07-21): neutralizing HOME dropped the model from `claude-opus-4-6` to
`claude-sonnet-4-6` without a word. "Same model" (SPEC D3) is a constant only if it is
checked after the fact — a pinned flag is an intention, the `modelUsage` key is
evidence.
"""

import pytest

from harness_lab import apparatus


def test_the_model_is_pinned_by_full_name_not_by_alias() -> None:
    """`opus` resolves to whatever is newest; a run pinned to an alias is not
    reproducible, and SPEC section 9 already concedes that numbers expire when the
    model changes — which is only honest if the file says which model it was.
    """
    assert apparatus.MODEL == "claude-opus-4-8"
    assert apparatus.MODEL not in ("opus", "sonnet", "haiku")


def test_effort_is_a_level_the_cli_actually_accepts() -> None:
    """Found by the first real trial, not by reading docs.

    The owner's machine sets `effortLevel: max`, but `--effort max` is rejected for
    Claude.ai subscribers. Pinning an unavailable level aborts every trial in a batch,
    each one after the workspace is built.
    """
    assert apparatus.EFFORT in ("low", "medium", "high")


def test_flags_pin_model_and_effort_and_never_enable_fallback() -> None:
    """A fallback model is a silent apparatus change mid-batch — the exact failure
    probe B found, automated.
    """
    flags = apparatus.flags()
    assert "--model" in flags
    assert apparatus.MODEL in flags
    assert "--effort" in flags
    assert apparatus.EFFORT in flags
    assert not any(f.startswith("--fallback") for f in flags)


def test_a_result_from_the_pinned_model_verifies() -> None:
    apparatus.verify_model({"modelUsage": {apparatus.MODEL: {"outputTokens": 4}}})


def test_a_result_from_a_different_model_is_rejected() -> None:
    """The probe-B failure as a test: the run succeeded, on the wrong model."""
    with pytest.raises(apparatus.ApparatusMismatchError):
        apparatus.verify_model({"modelUsage": {"claude-sonnet-4-6": {"outputTokens": 4}}})


def test_a_result_with_no_model_recorded_is_rejected() -> None:
    """Probe A returned `modelUsage: {}` on the failed run.

    Absence must not read as agreement: an unverifiable trial is discarded, not
    assumed to have used the pinned model.
    """
    with pytest.raises(apparatus.ApparatusMismatchError):
        apparatus.verify_model({"modelUsage": {}})
    with pytest.raises(apparatus.ApparatusMismatchError):
        apparatus.verify_model({})


def test_a_result_from_several_models_is_rejected() -> None:
    """A mid-run switch leaves two keys. Neither is the trial's model."""
    with pytest.raises(apparatus.ApparatusMismatchError):
        apparatus.verify_model({"modelUsage": {apparatus.MODEL: {}, "claude-sonnet-4-6": {}}})
