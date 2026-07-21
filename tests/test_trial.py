"""Trial command construction and result parsing.

No test here invokes the agent. The subprocess call is the one thin line the tests do
not cross; everything that decides anything is pure and checked without mocks.
"""

import json
from pathlib import Path

import pytest

from harness_lab import apparatus, trial

TASK = Path(__file__).resolve().parent.parent / "tasks" / "01-account-bugs"


def _result(**overrides: object) -> str:
    """A result JSON shaped like the ones the probes actually returned."""
    payload: dict[str, object] = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "num_turns": 7,
        "duration_ms": 22627,
        "usage": {
            "input_tokens": 7,
            "output_tokens": 998,
            "cache_creation_input_tokens": 12658,
            "cache_read_input_tokens": 141122,
        },
        "modelUsage": {apparatus.MODEL: {"outputTokens": 998}},
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_bare_omits_the_envelope_flag_entirely() -> None:
    """An empty `--append-system-prompt ""` appends an empty section; `bare` must
    append nothing at all.
    """
    argv = trial.build_argv(task_text="fix it", setup="bare")
    assert "--append-system-prompt" not in argv


def test_a_setup_with_an_envelope_passes_the_rendered_string() -> None:
    argv = trial.build_argv(task_text="fix it", setup="mini-skill")
    index = argv.index("--append-system-prompt")
    assert argv[index + 1].startswith("Write the simplest change that works.")
    assert not argv[index + 1].endswith("\n")


def test_every_argv_pins_the_apparatus() -> None:
    for setup in ("bare", "mini-skill", "long-skill", "force-cage"):
        argv = trial.build_argv(task_text="fix it", setup=setup)
        assert "--model" in argv and apparatus.MODEL in argv
        assert "--effort" in argv and apparatus.EFFORT in argv
        assert "--output-format" in argv and "json" in argv


def test_a_successful_result_parses() -> None:
    parsed = trial.parse_result(_result())
    assert parsed.output_tokens == 998
    assert parsed.num_turns == 7
    assert parsed.cache_read == 141122
    assert parsed.cache_creation == 12658


def test_a_result_flagged_is_error_is_rejected_despite_subtype_success() -> None:
    """Probe A returned exactly this: subtype "success", is_error true, 0 tokens.

    Filtering on subtype would have recorded a failed authentication as a successful,
    free trial.
    """
    with pytest.raises(trial.TrialFailedError):
        trial.parse_result(_result(is_error=True, subtype="success"))


def test_a_result_with_zero_output_tokens_is_rejected() -> None:
    """The signature of an aborted or refused run, not of a cheap one."""
    with pytest.raises(trial.TrialFailedError):
        trial.parse_result(_result(usage={"output_tokens": 0, "input_tokens": 0}, num_turns=1))


def test_a_result_from_the_wrong_model_is_rejected() -> None:
    with pytest.raises(apparatus.ApparatusMismatchError):
        trial.parse_result(_result(modelUsage={"claude-sonnet-4-6": {}}))


def test_unparseable_output_is_rejected_rather_than_guessed() -> None:
    """The CLI can emit a stack trace or a partial stream. None of it is a trial."""
    with pytest.raises(trial.TrialFailedError):
        trial.parse_result("Traceback (most recent call last):\n  ...\n")
    with pytest.raises(trial.TrialFailedError):
        trial.parse_result("")


def test_invoke_refuses_a_workspace_the_harness_leaked_into(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The D8 guard has to be wired, not merely written.

    A guard that exists and is never called is decoration; this asserts `invoke`
    actually refuses, and it refuses before spending a token.
    """
    from harness_lab import environment, workspace

    monkeypatch.delenv("CLAUDECODE", raising=False)
    home = environment.create_neutralized_home(tmp_path / "home")
    ws = workspace.prepare(TASK, tmp_path / "ws")
    (ws / "CLAUDE.md").write_text("leaked\n")

    with pytest.raises(workspace.HarnessLeakError):
        trial.invoke(["claude", "--version"], workspace=ws, home=home)


def test_cache_fields_are_kept_separate_and_never_summed() -> None:
    """ADR 7 / SPEC F4 — a summed token total is 91% cache mechanics and inverts under
    --append-system-prompt cache invalidation. The type must not offer a total.
    """
    parsed = trial.parse_result(_result())
    assert not hasattr(parsed, "total_tokens")
    assert parsed.cost_signature() == (998, 7)  # output_tokens, num_turns
