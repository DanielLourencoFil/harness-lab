"""The neutralized environment, and every way it can silently fail to be neutral.

Probe A (2026-07-21) established that an empty HOME breaks authentication, so the
trial HOME is not empty — it carries exactly one file. That makes "is it neutral?" a
real question rather than a tautology, and these are the ways the answer can be wrong.
"""

from pathlib import Path

import pytest

from harness_lab import environment


def test_a_freshly_created_home_is_neutralized(tmp_path: Path, fake_credentials: Path) -> None:
    home = environment.create_neutralized_home(tmp_path, fake_credentials)
    environment.assert_neutralized(home)
    assert (home / ".claude" / ".credentials.json").is_file()


def test_the_real_home_is_never_neutralized() -> None:
    """The failure this whole module exists to prevent.

    A trial run against the owner's real HOME carries the constitution, the hooks and
    the skills, and measures the harness while claiming to measure its absence.
    """
    with pytest.raises(environment.ContaminatedEnvironmentError):
        environment.assert_neutralized(Path.home())


def test_a_home_carrying_a_constitution_is_not_neutralized(
    tmp_path: Path, fake_credentials: Path
) -> None:
    home = environment.create_neutralized_home(tmp_path, fake_credentials)
    (home / "CLAUDE.md").write_text("# anything at all\n")
    with pytest.raises(environment.ContaminatedEnvironmentError):
        environment.assert_neutralized(home)


def test_a_home_carrying_settings_or_skills_is_not_neutralized(
    tmp_path: Path, fake_credentials: Path
) -> None:
    """Settings carry the apparatus (model, effort) and skills carry the harness.

    Checked as a whitelist rather than a blacklist: we must not have to enumerate
    what lives in ~/.claude to know a HOME is clean, because the day something new
    appears there is the day a blacklist starts lying.
    """
    home = environment.create_neutralized_home(tmp_path, fake_credentials)
    (home / ".claude" / "settings.json").write_text("{}\n")
    with pytest.raises(environment.ContaminatedEnvironmentError):
        environment.assert_neutralized(home)

    home2 = environment.create_neutralized_home(tmp_path / "second", fake_credentials)
    (home2 / ".claude" / "skills").mkdir()
    with pytest.raises(environment.ContaminatedEnvironmentError):
        environment.assert_neutralized(home2)


def test_a_home_without_credentials_is_rejected(tmp_path: Path) -> None:
    """Probe A: without credentials the run fails with "Not logged in".

    Caught before the invocation rather than after, so the failure costs no tokens
    and reads as a setup error rather than as a trial result.
    """
    home = tmp_path / "empty"
    (home / ".claude").mkdir(parents=True)
    with pytest.raises(environment.ContaminatedEnvironmentError):
        environment.assert_neutralized(home)


def test_trial_env_points_home_at_the_neutralized_directory(
    tmp_path: Path, fake_credentials: Path
) -> None:
    home = environment.create_neutralized_home(tmp_path, fake_credentials)
    env = environment.trial_env(home)
    assert env["HOME"] == str(home)


def test_trial_env_clears_the_nested_session_marker(tmp_path: Path, fake_credentials: Path) -> None:
    """F1 — `claude -p` refuses to run inside a Claude Code session.

    The runner is launched from a normal terminal, but the marker must not survive
    into the child by accident: a leaked CLAUDECODE turns every trial into a crash
    whose message points at nesting rather than at the runner.
    """
    home = environment.create_neutralized_home(tmp_path, fake_credentials)
    env = environment.trial_env(home)
    assert "CLAUDECODE" not in env


def test_each_neutralized_home_is_distinct_and_removed_after_use(
    fake_credentials: Path,
) -> None:
    """Single-use, because the CLI writes to HOME as it runs (observed 2026-07-21).

    One invocation left `.claude.json`, `.claude/settings.json`, `.claude/debug/` and
    `.claude/projects/<workspace>/…jsonl` — session transcript. Sharing a HOME across
    trials would let trial N read trial N-1's history.
    """
    with environment.neutralized_home(fake_credentials) as first:
        first_path = first
        assert first.is_dir()
        with environment.neutralized_home(fake_credentials) as second:
            assert second != first
    assert not first_path.exists()


def test_a_home_dirtied_by_a_previous_run_is_no_longer_neutral(
    tmp_path: Path, fake_credentials: Path
) -> None:
    """The abort that exposed the reuse bug, as a test.

    These are the exact paths the CLI created in a supposedly neutral HOME.
    """
    home = environment.create_neutralized_home(tmp_path, fake_credentials)
    for leftover in (
        ".claude.json",
        ".claude/settings.json",
        ".claude/projects/-tmp-workspace/session.jsonl",
    ):
        path = home / leftover
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n")
        with pytest.raises(environment.ContaminatedEnvironmentError):
            environment.assert_neutralized(home)
        path.unlink()


def test_running_inside_a_claude_code_session_is_refused() -> None:
    """Refused with a clear message rather than left to fail as a nested-session crash."""
    with pytest.raises(environment.NestedSessionError):
        environment.assert_not_nested({"CLAUDECODE": "1"})

    environment.assert_not_nested({})  # a normal terminal: no raise
