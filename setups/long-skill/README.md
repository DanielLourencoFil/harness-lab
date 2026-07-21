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
3. It shares `mini-skill`'s three restraint clauses, so the two envelopes overlap on
   content rather than being unrelated instructions. **This is not the same as being
   directionally identical** — see limit 5 below and `../README.md`, which pre-register
   what a long-vs-mini gap may and may not be read as.

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

**3. Its worked examples are mostly not in our language.** Counted by block:

| block | lines | count |
| --- | --- | --- |
| TypeScript | 65-76, 78-90, 191-236 | 71 |
| React/JSX | 275-295 | 21 |
| **Python** | **240-271** | **32** |

Our tasks are Python, so **67.7%** of the three large example blocks (67 of 99 lines)
is off-language, rising to **74.2%** (92 of 124) counting the two short TypeScript
snippets earlier in the file. A null result must be read against that, never as "long
skills do not help".

**4. It tells the agent when NOT to apply itself** (lines 23-28: "Code is already
clean and readable — don't simplify for the sake of it"). On a pure bug-fix task an
obedient agent should largely ignore this skill. That is why the task mix matters:
without `simplify-under-locked-tests` tasks in the suite (SPEC.md D1), the long setup
is close to inert and a null result would be uninterpretable.

**5. It argues both sides of restraint, which limits what a long-vs-mini gap proves.**
Alongside the three restraint clauses it shares with `mini-skill`, it carries three
scan-for-and-change catalogues (lines 129-135, 139-145, 149-155: *extract*, *split*,
*rename*, *remove dead code*, *inline the wrapper*, *replace the pattern*) and rebuts
"It's working, no need to touch it" with "Simplifying now saves time on every future
change" (line 301). `mini-skill` has no analogue for any of that, and its third line
forbids that class of edit outright.

So the two envelopes differ in **length and in content direction**, not in length
alone. `../README.md` pre-registers the consequence: the length inference for D7 row 1
is drawn only where these directives are inert, and on temptation tasks a higher
`out_of_scope_files` for this setup is read as content. Separating the two properly
needs the Phase 3 placebo (same length, content-free).
