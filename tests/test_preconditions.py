"""Suite Zero entry gate: debts that must be paid before any number is comparable.

Each test asserts a property the lab needs for its results to mean what the FINDINGS
will say they mean. An unpaid debt is marked `xfail(strict=True)`, which means:

- while the debt stands, the test is expected to fail and `verify` stays green;
- **the moment a debt is paid, the test passes, `strict=True` turns that into a
  failure, and someone must come here and remove the marker.**

That is the point. A debt tracked in prose is discharged by remembering; a debt
tracked this way announces itself in CI from both directions. The list is the one
place the preconditions live — SPEC.md and the setups READMEs point here, and none of
them is authoritative on whether a debt is still open.

**All five original debts are now paid** (renderer 2026-07-21, then F3, D8 isolation
and ADR 11 git workspaces on the same day), and every marker came off because the
gate turned red and demanded it — not because anyone remembered. New debts are added
here as new `xfail(strict=True)` tests; an empty file would mean the gate had stopped
being used, not that nothing is owed.

Where a debt is discharged by a *run* rather than by code, the test asserts against a
committed artifact (`docs/evidence/`), because "the code exists" is a claim and a
recorded run is evidence.

Doctrine this implements: "if a rule can be a tool/test/hook, wire it; only what
cannot be reified goes into convention docs" — documented-but-unwired governance is a
prayer, not a gate.
"""

import json
from pathlib import Path

import pytest

from harness_lab import apparatus, contamination, workspace

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "docs" / "evidence" / "2026-07-21-f3-neutralization"


def test_bare_setup_is_a_true_floor() -> None:
    """SPEC.md F3, PAID 2026-07-21 — the marker came off when this started passing.

    Three fixes, none foreseen by the spec: neutralize HOME; move workspaces outside
    this repo (the CLI reads instruction files from ancestor directories); give every
    invocation its own HOME (the CLI writes to HOME, including session transcript).

    Asserted against a recorded run rather than against code existing — see
    docs/evidence/2026-07-21-f3-neutralization/.
    """
    answer = (EVIDENCE / "contamination.txt").read_text()
    assert contamination.is_clean(answer), f"The recorded floor is contaminated: {answer[:200]!r}"

    result = json.loads((EVIDENCE / "result.json").read_text())
    assert result["is_error"] is False
    apparatus.verify_model(result)


def test_envelope_render_is_decided_and_hashed() -> None:
    """R4(b,c), PAID 2026-07-21 — the marker was removed when this started passing.

    The debt: the pin covered the file on disk, not the string sent to the model, so
    two runners could pass test_setups.py and still send different envelopes.

    Closed by ADR 15 and `harness_lab.envelopes`: one render rule (drop frontmatter,
    strip trailing whitespace) applied identically to all four setups, with the
    rendered strings hashed in tests/test_envelopes.py. This test now asserts the
    property rather than expecting its absence.
    """
    from harness_lab import envelopes

    assert (ROOT / "src" / "harness_lab" / "envelopes.py").exists()
    # One rule, all setups: nothing renders trailing whitespace, and the cage holds
    # the mini text constant (ADR 13).
    for setup in envelopes.SETUPS:
        assert envelopes.render(setup) == envelopes.render(setup).rstrip()
    assert envelopes.render("force-cage") == envelopes.render("mini-skill")
    assert "description:" not in envelopes.render("long-skill")


def test_trial_workspace_contains_no_harness_files(tmp_path: Path) -> None:
    """SPEC.md D8, PAID 2026-07-21 — the leak is guarded from both directions.

    Pushed in by the runner: assert_no_harness_files walks every ancestor, because on
    2026-07-21 the workspace directory itself was clean while the repo above it was
    not. Pulled in by the envelope: long-skill line 49 tells the agent to "Read
    CLAUDE.md / project conventions", which trial zero catches by asking the agent
    what it can actually see.
    """
    ws = workspace.prepare(ROOT / "tasks" / "01-account-bugs", tmp_path / "ws")
    workspace.assert_no_harness_files(ws)

    # A workspace inside this repo must be refused -- the exact 2026-07-21 mistake.
    with pytest.raises(workspace.HarnessLeakError):
        workspace.assert_no_harness_files(ROOT)


@pytest.mark.xfail(
    strict=True,
    reason="ADR 11 debt REOPENED: git init does not stop git blame/commit failing "
    "while Bash is denied (audit C1)",
)
def test_trial_workspace_is_git_initialized() -> None:
    """ADR 11 — REOPENED 2026-07-21 after being marked paid for the wrong property.

    The debt is about *turn cost*: long-skill instructs `git blame` (line 118) and
    `commit` (165), and every failing attempt burns a turn that lands in the ADR 7
    cost metric as if the envelope had caused it.

    The previous version of this test asserted that `.git` exists — the *mechanism* —
    and passed, so the marker came off. But the commands still failed, because
    `--permission-mode acceptEdits` denies Bash: the committed evidence shows the
    agent's own words, "The tests need approval to run." Git-initializing a workspace
    the agent cannot run git in achieves nothing.

    The lesson is about this gate, not about git: `xfail(strict=True)` is only worth
    what the assertion inside it says. A test that asserts the mechanism instead of
    the property will retire a debt that was never paid, and do it loudly enough to
    look rigorous.

    Reopened until a real trial shows zero permission denials for git commands.
    """
    evidence = json.loads((EVIDENCE / "result.json").read_text())
    assert evidence.get("permission_denials") == []


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
