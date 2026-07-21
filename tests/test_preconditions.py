"""Suite Zero entry gate: debts that must be paid before any number is comparable.

Each test below asserts a property the lab needs for its results to mean what the
FINDINGS will say they mean. Each is currently unpaid and marked
`xfail(strict=True)`, which means:

- while the debt stands, the test is expected to fail and `verify` stays green;
- **the moment a debt is paid, the test passes, `strict=True` turns that into a
  failure, and someone must come here and remove the marker.**

That is the point. A debt tracked in prose is discharged by remembering; a debt
tracked this way announces itself in CI from both directions. The list is the one
place the preconditions live — SPEC.md and the setups READMEs point here, and none of
them is authoritative on whether a debt is still open.

Doctrine this implements: "if a rule can be a tool/test/hook, wire it; only what
cannot be reified goes into convention docs" — documented-but-unwired governance is a
prayer, not a gate.
"""

import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Set by the runner once it can prove the property; unset in normal development.
# Until the runner exists, nothing sets these, and every precondition stays red.
RUNNER_PROVES = os.environ.get("HARNESS_LAB_RUNNER_PROVES", "").split(",")


@pytest.mark.xfail(strict=True, reason="F3 debt: machine layer not yet neutralized")
def test_bare_setup_is_a_true_floor() -> None:
    """SPEC.md F3 — `claude -p` reads ~/.claude/, so `bare` is not a pure-model floor.

    The spike measured 141k cache-read tokens of constitution inside the "no envelope"
    setup. Until the runner launches trials with a neutralized HOME (or an empty
    --settings), every cross-setup comparison sits on a floor that already contains
    the harness, and `bare` may only be labeled "machine-layer only".
    """
    assert "neutralized_home" in RUNNER_PROVES


@pytest.mark.xfail(strict=True, reason="frontmatter render rule not yet decided")
def test_envelope_render_is_decided_and_hashed() -> None:
    """R4(b,c) — the pin covers the file on disk, not the string sent to the model.

    long-skill/SKILL.md carries YAML frontmatter that mini-skill has none of, and the
    trailing-newline convention differs between a file and a shell literal. Two
    runners can pass test_setups.py and still send different envelopes. Closing this
    needs a render function whose output is hashed, applying one rule (strip
    frontmatter or keep it; strip trailing whitespace) identically to all setups.
    """
    assert (ROOT / "src" / "harness_lab" / "envelopes.py").exists()


@pytest.mark.xfail(strict=True, reason="D8 selftest not written; no trial workspaces yet")
def test_trial_workspace_contains_no_harness_files() -> None:
    """SPEC.md D8 — the cage wraps the instrument and must never leak into a trial.

    Two specific cases, not just "no harness files copied in":
    1. no CLAUDE.md / AGENTS.md / .claude/ inside a trial workspace, and
    2. long-skill line 49 instructs the agent to "Read CLAUDE.md / project
       conventions" — so the leak can be pulled in by the envelope itself, not only
       pushed in by the runner.
    """
    assert "workspace_isolation" in RUNNER_PROVES


@pytest.mark.xfail(strict=True, reason="ADR 11: workspaces are not git-initialized yet")
def test_trial_workspace_is_git_initialized() -> None:
    """ADR 11 — long-skill instructs `git blame` (line 118) and `commit` (line 165).

    In a plain fixture directory both fail, and the turns spent land in the ADR 7 cost
    metric as if the envelope had caused them. Every workspace gets `git init` plus one
    initial commit, identically for all four setups.
    """
    assert "git_workspaces" in RUNNER_PROVES


def test_every_vendored_third_party_file_records_its_upstream_commit() -> None:
    """N3, paid — provenance is not deferrable even when enforcement is.

    A vendored file whose upstream commit was never recorded cannot be pinned
    retroactively once upstream moves. Deferring the *hash check* while material is
    not a live variable is fine; losing the commit it came from is not.

    Not an xfail: this debt was paid in the same commit that added this gate.
    """
    vendored = {
        "setups/long-skill/README.md": "fea75b16472ba87e8c11f13a9e000c3ffdb2d1f5",
        "setups/_phase3-candidates/README.md": ("e270415226899ad9c6947e5474a16f28bb0a2f55"),
    }
    for readme, commit in vendored.items():
        text = (ROOT / readme).read_text()
        assert commit in text, f"{readme} does not record upstream commit {commit}"
        assert "sha256" in text, f"{readme} records no sha256"
