"""Trial zero — the check that would have caught the invalid batch of 2026-07-21.

The parsing and the verdict are pure and tested here; the subprocess call is not
crossed, as everywhere else.
"""

import json

import pytest

from harness_lab import contamination


def test_a_none_answer_is_clean() -> None:
    assert contamination.is_clean("NONE")
    assert contamination.is_clean("There are none — NONE.")


def test_the_exact_answer_that_exposed_the_leak_is_dirty() -> None:
    """Verbatim from the probe that invalidated the first real trial."""
    answer = (
        "Two instruction files have their contents shown in my system instructions:\n"
        "- `/home/dlourenco/.claude/CLAUDE.md`\n"
        "- `/home/dlourenco/Dev/harness-lab/CLAUDE.md`\n"
    )
    assert not contamination.is_clean(answer)


def test_any_instruction_file_mention_counts_as_dirty() -> None:
    """Blunt on purpose: a false positive costs one investigation, a false negative
    costs a batch of invalid numbers.
    """
    for marker in ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".cursorrules"):
        assert not contamination.is_clean(f"I can see {marker} somewhere.")


def test_a_failed_check_raises_rather_than_reporting_clean() -> None:
    """An unanswerable check must never read as a clean one.

    Probe A returned subtype "success" on a failed run; the same trap applies here,
    and defaulting to clean would silently green-light a contaminated batch.
    """
    with pytest.raises(contamination.ContaminationError):
        contamination.parse_answer(
            json.dumps({"is_error": True, "result": "Not logged in", "subtype": "success"})
        )


def test_a_missing_is_error_field_is_treated_as_failure() -> None:
    """Absence is not agreement (same rule as apparatus.verify_model)."""
    with pytest.raises(contamination.ContaminationError):
        contamination.parse_answer(json.dumps({"result": "NONE"}))


def test_the_prompt_asks_for_paths_not_a_yes_no() -> None:
    """A yes/no invites a confident wrong answer; a path list is checkable and it is
    what made the 2026-07-21 leak visible.
    """
    assert "exact path" in contamination.PROMPT
    assert "NONE" in contamination.PROMPT
