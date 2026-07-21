"""The envelopes under test are pinned by hash, enforced on every verify.

An experimental variable that drifts silently invalidates every comparison made
before the drift — and nobody notices, because the runs still succeed. So the pin is
a test, not a line in a README. Changing an envelope is legitimate; it just has to be
a deliberate commit that updates the expected hash here, which is exactly the friction
that makes the change visible in review.
"""

import hashlib
from pathlib import Path

SETUPS = Path(__file__).resolve().parent.parent / "setups"

# setups/long-skill/SKILL.md — addyosmani/agent-skills@fea75b16, verbatim.
# Provenance and the selection rule: setups/long-skill/README.md
LONG_SKILL_SHA256 = "f0c5ed754057eb0c1e027e2587f59de816651feb5e837242296c43ea21cf621d"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_long_skill_matches_its_pinned_hash() -> None:
    skill = SETUPS / "long-skill" / "SKILL.md"
    assert _sha256(skill) == LONG_SKILL_SHA256, (
        "long-skill/SKILL.md no longer matches the pinned upstream file. "
        "If this change is intentional, update LONG_SKILL_SHA256 and the provenance "
        "table in setups/long-skill/README.md in the same commit."
    )


def test_mini_skill_is_the_text_the_spike_ran_modulo_the_trailing_newline() -> None:
    """The mini envelope is the spike's text, read from the spike rather than retyped.

    Not byte-identical, and the difference is pre-registered rather than papered over:
    the shell literal in run.sh closes immediately after "touch." and carries no
    trailing newline, while a text file properly ends with one. So the file is the
    literal + "\\n".

    The render rule that follows is binding on the runner: **trailing whitespace is
    stripped from every envelope before it reaches --append-system-prompt**, applied
    identically to all setups. Without it the mini and long envelopes would differ by
    an invisible byte whose origin is file convention, not experimental design.
    Enforcing it on the rendered string is a precondition (see test_preconditions.py).
    """
    run_sh = (SETUPS.parent / "spike" / "2026-07-20-mechanism" / "run.sh").read_text()
    literal = run_sh.split("MINI_SKILL='", 1)[1].split("'", 1)[0]
    mini = (SETUPS / "mini-skill" / "SKILL.md").read_text()

    assert mini == literal + "\n"
    assert mini.rstrip("\n") == literal
    assert not literal.endswith("\n")


def test_readme_quotes_of_the_long_skill_are_verbatim() -> None:
    """Reification of audit finding N2.

    setups/long-skill/README.md presents these inside quotation marks and states the
    limits "belong in FINDINGS v1 verbatim". A misquote there propagates into a
    published document.

    Whitespace is normalized on both sides: markdown wraps quotes across lines, and a
    naive substring check silently skips every wrapped quote — a test that cannot fail.
    """

    def flat(text: str) -> str:
        return " ".join(text.split())

    skill = flat((SETUPS / "long-skill" / "SKILL.md").read_text())
    readme = flat((SETUPS / "long-skill" / "README.md").read_text())
    quoted = [
        "Read CLAUDE.md / project conventions",
        "Check git blame: what was the original context",
        "Build succeeds with no new warnings",
        "Linter/formatter passes",
        "Code is already clean and readable — don't simplify for the sake of it",
    ]
    checked = [p for p in quoted if flat(p) in readme]
    assert len(checked) == len(quoted), "a listed quote is no longer in the README"
    for phrase in checked:
        assert flat(phrase) in skill, f"README quotes {phrase!r}, absent from SKILL.md"


def test_envelopes_without_files_have_none() -> None:
    """`bare` and `force-cage` are not text and must not acquire a file by accident.

    `bare` is the absence of an envelope; `force-cage` is control flow in the runner.
    A stray SKILL.md in either would silently change what the floor and the cage mean.
    """
    for setup in ("bare", "force-cage"):
        assert not (SETUPS / setup).exists(), (
            f"setups/{setup}/ exists. That envelope is defined by the runner, not by "
            f"a file — see setups/README.md."
        )


def test_setups_directory_holds_exactly_the_known_entries() -> None:
    """A runner that globs setups/*/ must not discover a fifth setup by accident.

    `_phase3-candidates/` is parked material, not an envelope, and the two file-backed
    setups have different shapes (long-skill/ carries a README beside its SKILL.md).
    Pinning the set means a new directory has to be declared here before anything can
    enumerate it as a setup.
    """
    dirs = {p.name for p in SETUPS.iterdir() if p.is_dir()}
    assert dirs == {"mini-skill", "long-skill", "_phase3-candidates"}

    files = {p.name for p in SETUPS.iterdir() if p.is_file()}
    assert files == {"README.md"}

    # Only SKILL.md is an envelope; everything else in a setup dir is documentation.
    assert {p.name for p in (SETUPS / "mini-skill").iterdir()} == {"SKILL.md"}
    assert {p.name for p in (SETUPS / "long-skill").iterdir()} == {
        "SKILL.md",
        "README.md",
    }
