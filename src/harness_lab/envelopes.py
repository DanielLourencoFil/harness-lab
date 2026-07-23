"""Renders the exact string handed to `--append-system-prompt` for each setup.

This module is the seam between "the file on disk" and "the experimental variable".
The files are pinned by tests/test_setups.py; what the model actually receives is
pinned here. Both are needed — a change to the render rule moves the rendered hashes
while leaving every file byte-identical.

The render rule (ADR 15), applied identically to all four setups:

1. YAML frontmatter is removed. It is selection metadata, not instruction: in real
   skill use the `description` is what decides whether a skill loads, and only the
   body reaches the model as instruction. Passing it as instruction replicates no
   real usage, and the long skill's description ("Use when refactoring code for
   clarity", three times over) would invite the model to rule the skill inapplicable
   on a bug-fix task — turning a measurement of length into a measurement of the
   model's applicability judgment.
2. Trailing whitespace is stripped. A trailing newline is a file convention, not
   design; without this, mini and long differ by an invisible byte whose origin is
   how each text happened to be stored (a shell literal has none, a text file has one).
3. `bare` renders to the empty string, which the runner reads as "omit the flag".
4. `force-cage` renders the mini text (ADR 13): the cage holds text constant and adds
   only the mechanical loop.
"""

import hashlib
from pathlib import Path
from typing import Final

SETUPS: Final[tuple[str, ...]] = ("bare", "mini-skill", "long-skill", "force-cage")

_SETUPS_DIR: Final = Path(__file__).resolve().parent.parent.parent / "setups"

# Which file backs each setup. `bare` has none by definition; `force-cage` reuses the
# mini text rather than owning a copy, so the two cannot drift apart.
_SOURCE: Final[dict[str, str | None]] = {
    "bare": None,
    "mini-skill": "mini-skill",
    "long-skill": "long-skill",
    "force-cage": "mini-skill",
}

_DELIMITER: Final = "---"

# sha256 of the RENDERED string, not of the file. Updated deliberately, in the same
# commit as whatever changed the render rule or the envelope text.
PINNED_SHA256: Final[dict[str, str]] = {
    # 215 chars — byte-identical to the MINI_SKILL literal the spike ran, which the
    # rstrip in render() restores (the file carries a trailing newline, the shell
    # literal did not).
    "mini-skill": "126764b362ee2aee1adc7241dd4fe4d29e00ecf2f74bfc02f8960305ae089e4a",
    # 13,203 chars — the 13,545-byte file less its 4-line frontmatter and final newline.
    "long-skill": "ad49d6095691afc1060907d35b04fc08b774fd4fba60b4c066c7d041d74a1b9c",
}


def strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block, if present.

    Only a block at the very start counts. A `---` line further down is a markdown
    horizontal rule, and cutting to it would silently swallow most of a skill body
    while leaving a trial that still runs and still reports a number.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != _DELIMITER:
        return text

    for index in range(1, len(lines)):
        if lines[index].strip() == _DELIMITER:
            return "\n".join(lines[index + 1 :]).lstrip("\n")

    # Unterminated block: not frontmatter, leave the text alone rather than guess.
    return text


def render(setup: str) -> str:
    """Return the exact envelope string for `setup`.

    Raises KeyError for an unknown setup: a typo must never quietly render empty and
    turn a trial into an unlabeled `bare` run.
    """
    source = _SOURCE[setup]
    if source is None:
        return ""
    text = (_SETUPS_DIR / source / "SKILL.md").read_text(encoding="utf-8")
    return strip_frontmatter(text).rstrip()


def rendered_sha256(setup: str) -> str:
    return hashlib.sha256(render(setup).encode("utf-8")).hexdigest()
