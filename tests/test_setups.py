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


def test_mini_skill_is_the_text_the_spike_actually_ran() -> None:
    """Guards the mini envelope against silent editing.

    The text is byte-identical to the MINI_SKILL variable in the spike runner
    (spike/2026-07-20-mechanism/run.sh), so results from the spike and from the real
    runner describe the same envelope.
    """
    mini = (SETUPS / "mini-skill" / "SKILL.md").read_text()
    assert mini == (
        "Write the simplest change that works. Preserve existing behavior.\n"
        "Do not modify test files. Keep the change scoped to the file named in the task.\n"
        'Do not refactor or "clean up" code the task did not ask you to touch.\n'
    )


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
