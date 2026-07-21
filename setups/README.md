# Setups — the four envelopes under test

Everything other than the envelope is held identical across a trial: same model, same
task text, same grader, same workspace, same caps (SPEC.md D2/D3).

| setup | envelope | file | role |
| --- | --- | --- | --- |
| `bare` | none | — (no file by definition) | CLI-default floor (see below) |
| `mini-skill` | 3 lines of steer | `mini-skill/SKILL.md` | cheap steer |
| `long-skill` | 13,545-byte curated skill | `long-skill/SKILL.md` | expensive steer / "wide net" |
| `force-cage` | mini text + mechanical outer loop | — (lives in the runner) | the harness thesis |

`bare` and `force-cage` have no file here on purpose: `bare` is the absence of an
envelope, and `force-cage` is control flow (verify → red → re-invoke until cap), not
text. Both are implemented in the runner.

**`bare` is a CLI-default floor — neither a pure-model floor nor a machine-layer
one.** F3 is paid: trials run with a neutralized `HOME`, from a directory outside any
repository carrying instruction files, and trial zero confirms per run that the agent
sees none (ADR 16-18). What remains is the CLI's own built-in system prompt — roughly
20-21.5k cache-read tokens per turn, unavoidable and identical for every setup — so
`bare` is "the model plus the tool harness the CLI always injects", and FINDINGS must
say that rather than "pure model".

## This is two factors, not one variable

Reading the four setups as one variable with four values licenses the wrong
comparisons. The design is:

| contrast | what differs | the D7 row it serves |
| --- | --- | --- |
| `bare` → `mini-skill` | + steer text | does any envelope beat the floor |
| `mini-skill` → `long-skill` | + length/elaboration (text present in both) | row 1 — skill body cap, "mini over long" |
| `mini-skill` → `force-cage` | + mechanical loop (text held constant) | row 2 — force > steer |

**`bare` vs `force-cage` differs on both factors and is never a valid reading of D7
row 2.** The cage carries the mini text (ADR 13), so a gap measured against `bare`
credits the loop with the text's contribution too. The named baseline for row 2 is
`mini-skill`.

## What mini and long share — and where they diverge

The two envelopes share three restraint clauses, and that is the only equivalence the
text supports:

| mini-skill says | long-skill line |
| --- | --- |
| "Preserve existing behavior" | 34 |
| "Do not modify test files" | 311, 323 |
| "Keep the change scoped" / no drive-by cleanup | 103 |

**The remaining ~320 lines are not elaboration of those three, and part of them argue
the other way.** Lines 129-135, 139-145 and 149-155 are three scan-for-and-change
catalogues (*extract*, *split*, *rename*, *remove dead code*, *inline the wrapper*,
*replace the pattern*); line 301 rebuts "It's working, no need to touch it" with
"Simplifying now saves time on every future change". `mini-skill` has no analogue for
any of it, and its third line forbids exactly that class of edit.

**Consequence for D7 row 1, pre-registered here:** a long-vs-mini gap may be length
*or* content direction, and this instrument cannot separate them by itself. The
length inference is therefore drawn **only on task types where long-skill's
scan-and-change directives are inert** — a bug fix in a file with no adjacent mess.
On temptation tasks (SPEC.md D5), where messy adjacent code is planted deliberately,
a higher `out_of_scope_files` for `long-skill` is read as **content**, never as the
cost of length. Phase 3's placebo skill (same length, content-free) is what would
actually separate the two; until it runs, row 1 stays conditional.

## What actually reaches the model (decided — ADR 15)

The envelope is not the file: it is what `src/harness_lab/envelopes.py` renders. One
rule, all four setups — **drop YAML frontmatter, strip trailing whitespace**.

| setup | rendered length | note |
| --- | --- | --- |
| `bare` | 0 | the runner omits the flag entirely |
| `mini-skill` | 215 chars | exactly the literal the spike ran |
| `long-skill` | 13,203 chars | the 13,545-byte file less frontmatter and final newline |
| `force-cage` | 215 chars | identical to `mini-skill` by construction (ADR 13) |

The frontmatter is dropped because it is *selection* metadata, not instruction: in
real skill use the `description` decides whether a skill loads, and only the body
reaches the model. The long skill's description says "Use when refactoring code for
clarity" three times — fed to a bug-fix task as instruction, it invites the model to
rule the skill inapplicable, quietly turning "does length help?" into "did the model
think the skill applied?".

Rendered strings are hashed in `tests/test_envelopes.py`, which is a different guard
from the file hashes in `tests/test_setups.py`: a change to the render rule moves the
rendered hashes while every file stays byte-identical.

## The pins are mechanical, and there are two of them

Both run on every `verify`. An experimental variable that drifts silently invalidates
every comparison made before the drift, so each gate is a test, not a note.

| gate | pins | catches |
| --- | --- | --- |
| `tests/test_setups.py` | the sha256 of each **file** | upstream text changing under us |
| `tests/test_envelopes.py` | the sha256 of each **rendered string** | the render rule changing while files stay identical |

Two guards rather than one, because they fail on different things: editing
`long-skill/SKILL.md` moves both hashes, while changing the frontmatter rule moves
only the rendered one. Either change is legitimate — each just has to be a deliberate
commit that updates the expected hash.

## `_phase3-candidates/`

Material kept but **not** under test in Suite Zero or the MVP. See its own README.
