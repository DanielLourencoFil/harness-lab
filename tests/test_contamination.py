"""Trial zero — the check that would have caught the invalid batch of 2026-07-21.

The parsing and the verdict are pure and tested here; the subprocess call is not
crossed, as everywhere else.
"""

import json

import pytest

from harness_lab import contamination


def test_only_the_bare_clean_token_is_clean() -> None:
    """Strict equality after normalization (audit R2).

    An answer that explains rather than answers is not clean. The prose form
    "There are none — NONE." is now rejected: it is indistinguishable, to a substring
    check, from "There are none besides CLAUDE.md — NONE elsewhere", and the cost of
    telling them apart by parsing prose is a parser nobody will maintain.

    The price is a possible false positive stopping a batch for one investigation.
    ADR 18 priced that against a batch of invalid numbers.
    """
    assert contamination.is_clean("NONE")
    assert contamination.is_clean("  none  ")
    assert contamination.is_clean("None.")

    assert not contamination.is_clean("There are none — NONE.")
    assert not contamination.is_clean("NONE, except the project conventions file.")


def test_an_empty_answer_is_not_clean() -> None:
    """The fail-open path the first version had (audit R2).

    `parse_answer` returns "" when the CLI omits `result`, and "" contained none of
    the banned substrings — so a check that returned nothing certified the floor.
    """
    assert not contamination.is_clean("")
    assert not contamination.is_clean("   \n  ")


def test_an_answer_naming_a_skill_or_settings_file_is_not_clean() -> None:
    """The second fail-open (audit R2): the blacklist held four constitution
    filenames, while SPEC F9 defines the harness as constitution, hooks, skills AND
    memory. A skill or a settings file passed straight through.
    """
    assert not contamination.is_clean("I can see /home/u/.claude/skills/x/SKILL.md")
    assert not contamination.is_clean("settings.json is in my instructions")


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
