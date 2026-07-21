"""The rendered envelope is the experimental variable — not the file on disk.

These tests exist because two runners can read identical files and still send
different strings to the model. What the trial measures is what reaches
`--append-system-prompt`, so that is what is specified and pinned here.
"""

import pytest

from harness_lab import envelopes


def test_bare_renders_to_nothing() -> None:
    """`bare` is the absence of an envelope, so the runner omits the flag entirely.

    An empty string is the signal for that. Passing `--append-system-prompt ""` would
    not be the same thing: it appends an empty section rather than none.
    """
    assert envelopes.render("bare") == ""


def test_force_cage_renders_exactly_the_mini_text() -> None:
    """ADR 13 — the cage holds the text constant and adds only the loop.

    If these ever diverge, the mini-vs-cage contrast stops isolating the mechanism
    and D7 row 2 becomes unreadable.
    """
    assert envelopes.render("force-cage") == envelopes.render("mini-skill")
    assert envelopes.render("force-cage") != ""


def test_long_skill_render_drops_the_frontmatter() -> None:
    """ADR 15 — the frontmatter is selection metadata, not instruction.

    Its `description` says "Use when refactoring code for clarity" three times over.
    Fed to a bug-fix task as instruction, it invites the model to conclude the skill
    does not apply — which would turn "does length help?" into "did the model decide
    the skill applied?" and make a null result unreadable.
    """
    rendered = envelopes.render("long-skill")

    assert "name: code-simplification" not in rendered
    assert "description:" not in rendered
    assert not rendered.startswith("---")
    assert rendered.startswith("# Code Simplification")
    # The body survived intact.
    assert "Chesterton's Fence" in rendered
    assert "The Rule of 500" in rendered


def test_no_envelope_ends_in_whitespace() -> None:
    """A trailing newline is a file convention, not experimental design.

    The mini envelope came from a shell literal with none and a file with one; left
    alone, mini and long would differ by an invisible byte whose origin is how the
    text happened to be stored.
    """
    for setup in envelopes.SETUPS:
        rendered = envelopes.render(setup)
        assert rendered == rendered.rstrip(), f"{setup} renders trailing whitespace"


def test_unknown_setup_raises_rather_than_rendering_empty() -> None:
    """A typo must not silently become a `bare` trial.

    Returning "" for an unrecognized name would produce a run that looks successful
    and is secretly the floor — a whole row of the results table, wrong, with nothing
    to show for it.
    """
    with pytest.raises(KeyError):
        envelopes.render("mini_skill")  # underscore, not hyphen
    with pytest.raises(KeyError):
        envelopes.render("")


def test_frontmatter_stripping_only_touches_a_leading_block() -> None:
    """A `---` inside the body is a horizontal rule, not a delimiter.

    Today's long skill has none, so this guards the next one rather than the current
    one: a naive "cut to the last ---" would silently swallow most of a skill body and
    the trial would still run.
    """
    text = "---\nname: x\n---\n# Title\n\nBody one.\n\n---\n\nBody two.\n"
    assert envelopes.strip_frontmatter(text) == ("# Title\n\nBody one.\n\n---\n\nBody two.\n")


def test_text_without_frontmatter_is_unchanged() -> None:
    body = "Write the simplest change that works.\n"
    assert envelopes.strip_frontmatter(body) == body


def test_rendered_envelopes_match_their_pinned_hashes() -> None:
    """Drift detection on the rendered string, closing the gap test_setups.py leaves.

    test_setups.py pins the files; this pins what the model actually receives. Both
    are needed: a change to the render rule moves these hashes while the files stay
    identical.
    """
    assert envelopes.rendered_sha256("mini-skill") == envelopes.PINNED_SHA256["mini-skill"]
    assert envelopes.rendered_sha256("long-skill") == envelopes.PINNED_SHA256["long-skill"]
