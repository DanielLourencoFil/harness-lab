# long-skill — provenance and declared limits

The stamp lives here and never inside `SKILL.md`: the skill is under test verbatim,
and editing it — even to add a provenance header — would make the measured artifact
something nobody else can reproduce.

## Provenance

| field | value |
| --- | --- |
| Source | `addyosmani/agent-skills`, `skills/code-simplification/SKILL.md` |
| Commit pinned | `fea75b16472ba87e8c11f13a9e000c3ffdb2d1f5` (authored 2026-03-31) |
| Retrieved | 2026-07-20, via `gh api` at that ref |
| Size | 13,545 bytes, 332 lines |
| sha256 | `f0c5ed754057eb0c1e027e2587f59de816651feb5e837242296c43ea21cf621d` |
| Upstream note | the skill itself credits Anthropic's `code-simplifier` plugin as its origin |

The directory upstream contains exactly one file, so nothing is missing.

## Why this skill (the selection rule, pre-registered)

Recorded before any trial ran, because browsing 24 candidate skills and picking one
is a choice with degrees of freedom:

1. SPEC.md D2 already named the long setup "Osmani-style simplification" — the family
   was fixed by the spec, not by a browse.
2. Of the repo's 24 skills, this is the one aimed at an agent **authoring** a change.
   The obvious alternative, `code-review-and-quality` (20.5 KB), instructs an agent to
   **review someone else's change before merge** — a role our trials do not contain
   (no PR, no reviewer, agent works alone and headless). Using it would confound role
   mismatch with envelope length. It is parked in `../_phase3-candidates/`.
3. Its content is directionally identical to `mini-skill`, which is what makes the
   comparison a test of length rather than of content (see `../README.md`).

## Declared limits — found by reading it, not by summarizing it

These belong in FINDINGS v1 verbatim. They were missed by an automated summary of the
file and only surfaced on a full read; the distinction matters because the summary
was directionally correct and operationally incomplete.

**1. It instructs the agent to use infrastructure a trial workspace may not have.**

| line | instruction | present in a bare fixture dir? |
| --- | --- | --- |
| 49 | "Read CLAUDE.md / project conventions" | no |
| 118 | "Check git blame: what was the original context" | no |
| 165 | "If tests pass -> commit" | no |
| 324 | "Build succeeds with no new warnings" | no |
| 325 | "Linter/formatter passes" | no |

Unmitigated, the long setup spends turns and output tokens hunting for things that do
not exist, and that spend lands in the ADR 7 cost metric as if the envelope had caused
it. This is the F4 class of error in a new place: an artifact of the instrument read
as a property of the thing measured.

**Mitigation decided (ADR 11):** every trial workspace is `git init`-ed with one
initial commit, identically for all four setups, which removes the `git blame` and
`commit` cases. The other three are absent for every setup equally, so the residual
cost is uniform rather than differential. This is mitigation, not elimination — the
long setup may still spend more turns discovering the absence, and that is reported,
not hidden.

**2. Line 49 is also a leak vector.** Telling the agent to read `CLAUDE.md` composes
badly with F3 (`claude -p` already reads `~/.claude/`): the long setup carries an
explicit instruction to go fetch the machine layer we are trying to neutralize. The
D8 selftest must assert this specific case, not just "no harness files copied in".

**3. Its worked examples are mostly not in our language.** Lines 191-295 are
TypeScript/JS/React; Python gets ~30 lines. Our tasks are Python. So roughly 80% of
the skill's concrete content is off-language for this suite. A null result must be
read against that, never as "long skills do not help".

**4. It tells the agent when NOT to apply itself** (lines 23-28: "Code is already
clean — don't simplify for the sake of it"). On a pure bug-fix task an obedient agent
should largely ignore this skill. That is why the task mix matters: without
`simplify-under-locked-tests` tasks in the suite (SPEC.md D1), the long setup is close
to inert and a null result would be uninterpretable.
