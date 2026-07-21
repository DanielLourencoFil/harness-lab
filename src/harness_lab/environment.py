"""The neutralized environment a trial runs in.

SPEC F3: `claude -p` reads `~/.claude/` in every setup, so the "no envelope" floor
silently carries the machine layer. This module removes it.

Two probes on 2026-07-21 shaped what "removed" means:

- An entirely empty HOME fails with "Not logged in": credentials live in
  `~/.claude/.credentials.json`. So a trial HOME carries that one file and nothing
  else — which makes neutrality a property worth checking rather than a tautology.
- Neutralizing HOME also dropped the model from opus to the CLI default. The machine
  layer holds two different things: the *harness* (constitution, hooks, skills,
  memory), whose absence is what `bare` measures, and the *apparatus* (model, effort),
  which must be held constant. Only the first is removed here; the second is pinned
  explicitly in `apparatus.py`.
"""

import os
import shutil
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Final

_CLAUDE_DIR: Final = ".claude"
_CREDENTIALS: Final = ".credentials.json"

# A whitelist, deliberately. Deciding neutrality by listing what must be *absent*
# means the day a new file appears in ~/.claude is the day the check starts lying.
_ALLOWED: Final[frozenset[str]] = frozenset({f"{_CLAUDE_DIR}/{_CREDENTIALS}"})


class ContaminatedEnvironmentError(RuntimeError):
    """The environment is not neutral, so a trial run in it would measure the harness."""


class NestedSessionError(RuntimeError):
    """The runner was launched from inside a Claude Code session (SPEC F1)."""


def real_credentials_path() -> Path:
    return Path.home() / _CLAUDE_DIR / _CREDENTIALS


def create_neutralized_home(parent: Path) -> Path:
    """Build a HOME carrying credentials and nothing else.

    `parent` is created if missing; the caller owns its lifetime and is responsible
    for deleting it after the trial (credentials should not outlive the run).
    """
    home = parent
    home.mkdir(parents=True, exist_ok=True)
    claude = home / _CLAUDE_DIR
    claude.mkdir(exist_ok=True)
    # copy, never read: the credential's contents must not pass through this process.
    shutil.copyfile(real_credentials_path(), claude / _CREDENTIALS)
    return home


def _relative_entries(home: Path) -> set[str]:
    return {
        str(path.relative_to(home).as_posix())
        for path in home.rglob("*")
        if path.is_file() or path.is_dir()
    }


def assert_neutralized(home: Path) -> None:
    """Raise unless `home` contains exactly the credential file and its directory.

    Called before every invocation. A contaminated trial cannot be repaired after the
    fact — the tokens are spent and the run measured the wrong thing — so this fails
    closed, before the agent is launched.
    """
    if home.resolve() == Path.home().resolve():
        raise ContaminatedEnvironmentError(
            f"HOME is the real home directory ({home}). A trial run here carries the "
            f"constitution, hooks and skills, and would measure the harness while "
            f"reporting the absence of one."
        )

    credential = home / _CLAUDE_DIR / _CREDENTIALS
    if not credential.is_file():
        raise ContaminatedEnvironmentError(
            f"No credentials at {credential}. Without them the CLI returns "
            f'"Not logged in" and the failure would be recorded as a trial result.'
        )

    unexpected = {
        entry for entry in _relative_entries(home) if entry not in _ALLOWED and entry != _CLAUDE_DIR
    }
    if unexpected:
        raise ContaminatedEnvironmentError(
            f"Unexpected entries in the trial HOME: {sorted(unexpected)}. "
            f"Only {sorted(_ALLOWED)} may be present."
        )


def assert_not_nested(env: dict[str, str] | None = None) -> None:
    """SPEC F1 — `claude -p` refuses to run inside a Claude Code session.

    Refused here with an explanation, rather than left to surface as a nested-session
    crash whose message points at the wrong problem.
    """
    source = os.environ if env is None else env
    if source.get("CLAUDECODE"):
        raise NestedSessionError(
            "CLAUDECODE is set: this is a Claude Code session, and `claude -p` will "
            "refuse to launch. Run the runner from a plain terminal."
        )


@contextmanager
def neutralized_home() -> Iterator[Path]:
    """A single-use neutralized HOME, deleted on exit.

    Single-use is the point. The CLI *writes* to HOME as it runs — observed
    2026-07-21: one invocation left `.claude.json`, `.claude/settings.json`,
    `.claude/debug/`, `.claude/todos/`, `.npm/_logs/` and, most importantly,
    `.claude/projects/<workspace>/…jsonl`, which is session transcript.

    Two consequences, and the second is the dangerous one:

    1. A HOME is no longer neutral after any invocation, so re-checking the same one
       fails — correctly.
    2. Reusing a HOME across trials would let trial N read trial N-1's session
       history. Every invocation therefore gets its own, and credentials never
       outlive it.
    """
    parent = Path(tempfile.mkdtemp(prefix="harness-lab-home-"))
    try:
        home = create_neutralized_home(parent)
        assert_neutralized(home)
        yield home
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def trial_env(home: Path) -> dict[str, str]:
    """The environment handed to the subprocess."""
    env = dict(os.environ)
    env["HOME"] = str(home)
    # Must not leak into the child: it would make every trial fail as a nested session.
    env.pop("CLAUDECODE", None)
    return env
