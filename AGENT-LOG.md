# Agent log

Public record of where the agent helped and where it failed on this project. Failures
are recorded with the same weight as successes — a log that only lists wins is
marketing, and this repo's entire subject is measuring what harnesses actually do.

## 2026-07-20 — Mechanism spike

**Helped.** After three days of specification, the whole mechanism was proved end to
end in about two minutes of execution: agent run headless, tokens read from the CLI's
own JSON, grader (unittest) running outside the agent's reach, isolated workspaces,
two-row table produced. The task was `account.py` with two planted bugs and a locked
test file. Both setups came out PASS/INTACT — no quality signal, which is the correct
outcome for a trivial task, and exactly what a walking skeleton is supposed to show.

**Failed — and this is the entry that matters.** The spike runner's token accounting
was wrong: it summed every JSON field whose name contained "token". That total was 91%
`cache_read`, and `--append-system-prompt` invalidates the prompt cache, inflating
`cache_creation` 2.5x for the setup under test. Of the 32k "extra" tokens attributed
to the mini-skill, 99% was cache mechanics and 168 tokens (0.5%) was real output.

**The headline "the mini-skill costs 20% more" would have been false**, and it would
have been published as a finding of a lab whose purpose is to replace taste with
measurement. It was caught on review, not by a test. The fix is recorded as ADR 7 and
SPEC.md F4; the broken runner is preserved under `spike/` rather than corrected, so
the error stays on the record.

**What it says about the instrument.** The first real output of this lab was a false
measurement, produced by the lab itself, in the cheapest possible run. That is the
argument for Suite Zero (D10) stated better than the spec stated it: the dominant
risk is not "no findings", it is *confident wrong findings*.

## 2026-07-21 — Audit of PR #1 (the `setups/` unit)

**9 findings, 9 real, 0 confabulated.** Every finding was re-verified against the
files before being accepted; the auditor's report is testimony too. The ratio is not
a compliment to the auditor — it is a measure of how much unverified assertion the
authoring session had shipped.

Two were reified as red tests and turned green by the fix: the mini envelope was not
byte-identical to the spike text it claimed to reproduce (one trailing newline), and
a "verbatim" quote in `setups/long-skill/README.md` had silently dropped two words.

**The three that mattered were claims, not code.** All three were mine, all three were
stated with confidence, and all three would have travelled into FINDINGS:

1. I described `long-skill` as "the same instruction as `mini-skill`, elaborated 63x".
   It is not. It shares three restraint clauses and then carries three
   scan-for-and-change catalogues plus an explicit rebuttal of "it's working, don't
   touch it" — directives `mini-skill` has no analogue for and whose third line
   forbids. D7 row 1 was armed to convert a long-vs-mini gap into a **measured** claim
   about *length*; the gap could as easily be content direction.
2. I settled an open question from the spec (`force-cage` = "mini (or no) skill") in a
   README table cell, with no ADR, and then wrote "one variable, four values". The
   design is two factors, and `bare` vs `force-cage` — the comparison that framing
   licenses — differs on both, crediting the loop with the mini text's contribution.
3. I labeled `bare` "floor / pure model", the exact label F3 had retracted three
   sections earlier in the same repo, on the same day, in a document I wrote.

**What the audit says about the writing session.** Every one of these passed a green
`verify`, a green CI run, and my own review, because none of them is the kind of thing
a test was watching. The unit's one mechanical gate — the hash pin — was working
perfectly and guarded a property nobody was going to get wrong. The claims doing the
real load-bearing work were unguarded prose.

**And the audit did not catch everything.** While reifying finding N2 I wrote a test
that could not fail: the quote it checked is wrapped across two lines in the markdown,
so the substring check was always false and the assertion never ran. Written ten
minutes after I told the owner that a test never seen red is a hypothesis. Fixed by
normalizing whitespace; recorded here because the failure mode — a green test that
asserts nothing — is exactly what this project exists to measure.

**Consequence.** ADR 14 and `tests/test_preconditions.py`: the four validity debts
that were prose in four different files are now `xfail(strict=True)` tests in one
place, proven to bite in both directions (open debt → silent xfail; debt paid → hard
failure demanding the marker be removed).

## 2026-07-21 — Building the runner: five findings, none from the spec

**Helped.** The pipe runs end to end on a genuinely isolated floor. All five Suite
Zero preconditions are paid and the gate is empty of markers, each one removed because
CI turned red and demanded it rather than because anyone remembered.

**The pattern worth recording is the order of discovery.** Every finding came from
running something, and each was only visible after the previous one was fixed:

| # | found | how |
| --- | --- | --- |
| 1 | an empty `HOME` breaks auth; credentials are one file | probe, before any code |
| 2 | the result JSON says `subtype: "success"` on failed runs | the same probe's output |
| 3 | neutralizing `HOME` silently changes the model | second probe |
| 4 | the CLI reads instruction files from **ancestor** directories | asking the agent from inside a workspace |
| 5 | the CLI **writes** to `HOME`, including session transcript | the runner's own guard aborting a trial |

Nothing in three days of specification reached any of them. Findings 4 and 5 were not
merely unforeseen — they were invisible to the checks written specifically to catch
their category.

**Failed — the important one.** I pre-registered the wrong success criterion for F3:
"cache_read should collapse". It cannot. Per turn it is flat at ~20-21.5k across a
contaminated run, a partly contaminated run and a clean one, because it is the CLI's
own system prompt being re-read; the owner's `CLAUDE.md` is small beside it. The
observed 15% drop was narratable as success, and only the structural check stopped
that story being told. **This is the second time in two days that a token field was
mistaken for evidence** — the first produced a false headline about the mini-skill
(F4). The lesson is now explicit in the spec: token fields are a poor instrument for
structural questions, and a plausible number moving in the expected direction is not
evidence of its cause.

**Failed — the one that made a measurement invalid.** I put trial workspaces in
`runs/` inside this repo, for tidiness. Because the CLI walks up the directory tree,
every trial inherited harness-lab's own `CLAUDE.md`: the `bare` floor ran carrying two
constitutions, and the first "real measurement" was void. Both structural guards
reported clean the whole time, including the one named for exactly this
(`assert_no_harness_files`) — it checked the workspace directory and the contamination
was in its parent.

**What that changed.** Trial zero (ADR 18): before each measurement the runner asks
the agent, in the exact directory the trial will use, which instruction files it can
see, and aborts unless the answer is `NONE`. A structural check looks for what its
author knew to look for; the agent is the only witness that sees everything actually
injected. It is wired into the runner, because the alternative was a command someone
remembers to type — the failure mode this whole file exists to document.

**Also caught, unprompted by any tool:** `assert_no_harness_files` was written and
never called. A guard that exists and is not wired is decoration.

## 2026-07-21 — Audit of PR #4 (runner step 1)

**15 findings, 14 confirmed real, 1 hypothesis that turned out real on testing, 0
confabulated.** Every one verified against the code before being accepted.

**The Critical was in the evidence file I had just committed as proof of rigour.**
`--permission-mode acceptEdits` denies Bash, and the artifact the Suite Zero gate
asserts against contains the agent saying *"The tests need approval to run."* The
grader still produced a correct `tests_pass`, because it runs outside the agent's
reach — that part held. The cost did not: every denial burns a turn, `num_turns` is
half the ADR 7 cost signature, and the number of Bash-requiring instructions differs
by envelope — one for `bare` and `mini-skill`, about ten for `long-skill`. The long
setup would have measured as more expensive because of a permission flag. **Third
instance in two days of an instrument artifact being readable as an envelope
property.**

**The finding under the finding: my own gate retired a debt that was never paid.**
ADR 11 git-initializes workspaces so `git blame` and `commit` do not fail. They still
failed — Bash was denied. But `test_trial_workspace_is_git_initialized` asserted that
`.git` exists, so it passed, `xfail(strict=True)` fired, and I removed the marker
believing the mechanism worked. **The gate is only worth what the assertion inside it
says.** A test that asserts the mechanism instead of the property will retire an
unpaid debt loudly enough to look rigorous. The debt is reopened.

**The hypothesis that was real.** The auditor could not execute, so it labelled the
stdlib-shadow attack a hypothesis: an agent writing a `unittest/` package into its
workspace would have its own code run as the grader. Reproduced in one command — the
old grader returned `tests_pass=True` on a workspace where both bugs were still
present. The grader now reconstructs a directory from declared files only, and the
attack is unreachable rather than defended against.

**Two fail-open checks, both written by me the same day, both contradicting a comment
I had written four lines above the other one.** `contamination.is_clean("")` returned
True; `trial_env` copied all 51 inherited variables and removed one. `environment.py`
argues explicitly for allowlists over blacklists — and its own sibling functions were
blacklists.

**And two of three guards in `invoke` were held by no test.** Deleting
`assert_not_nested()` and `assert_neutralized()` left the whole suite green, in a unit
whose own docstring says a guard that is never called is decoration.

**Calibration.** Two audits, 24 findings, 23 real, 1 confabulated-by-omission (none).
Both audits found things that had passed a green `verify`, a green CI run and my own
review. The pattern across both: what fails is never the mechanism I built
deliberately — it is the assertion I wrote *about* the mechanism.

## 2026-07-21 — Owner evaluation session: the theses were never in the repo

**What happened.** The owner opened a fresh session saying the lab felt off the rails
and asked what the code actually does. The code matched the spec at every point
checked. The session still found the real problem, and no file in this repo could have
surfaced it: **the owner's actual theses exist nowhere in writing.**

**The theses, in the owner's formulation (recorded here so an unpause starts from
them, not from re-derivation):** the lab tests how instruction should be written and
delivered to an agent. One capability under test — deliver green without cheating and
without touching what was not asked. Three vehicles that must express **exactly the
same idea**: a short skill (~30 lines), the same content stretched long (~300 lines),
and the force-cage (the mechanical loop). Only the vehicle varies; content is held
constant. The output decides practice: whether skills are written short or long,
verbose-repetitive or terminologically strict — and when a cage replaces a skill
entirely. It is also a theater detector: when someone claims a 300-line skill
delivers, measure it against the same ideas in 30 lines.

**What was found against that statement:**

1. **The built arms violate it.** `long-skill` (the vendored Osmani skill) is not the
   mini elaborated — it commands refactoring catalogues the mini's third line forbids.
   Audit finding 1 had already documented this as a caveat; against the owner's
   statement it is a design error: the arm answers "does this artifact deliver?" (a
   product test), not "does the same content delivered longer help or hurt?" (the
   owner's question).
2. **The owner's controlled experiment sits in Phase 3 of the spec** (placebo skill,
   formulation ablation) — deferred behind the artifact test it should have preceded.
3. **The spec's one-line owner goal underdetermines the design.** Each building
   session filled the gap with locally defensible choices that collectively drifted.
   Intent living only in the owner's head is re-derived by every fresh session —
   documented-but-unwritten intent is the same prayer this repo's doctrine warns
   about, one level up.

**Where the agent failed.** The first evaluation report described mechanism (modules,
guards, gates) and pronounced the code faithful to the spec. The owner's question was
purpose-fit, and the misalignment only surfaced after he restated his theses from
scratch. An evaluator checking code-against-spec cannot see spec-against-intent; only
the owner's replica caught it.

**What held.** The owner raised the equivalence question cold — "how do we know two
results are comparable, since more expensive is not by itself worse?" — and the
existing design answered it without amendment: equivalence is defined ex ante by the
D3 predicate, cost is compared only conditional on success and only within a task, and
quality beyond the predicate is a declared limit (SPEC section 9). The instrument
survives this session untouched: every guard, every gate and the cost accounting serve
any set of arms equally.

**Outcome.** Option A — realign the arms to the theses (mini and long share content,
the long produced by a pre-registered expansion rule; Osmani relabeled as an
artifact-test arm; the theses written into SPEC.md owner-signed) — was reported and
not approved. The owner announced the intent to pause the lab: "it seems it will not
have the practical effect I expect." A pause now is the kill-criteria design doing its
job early — the decision to stop cheaply was made at spec time, clear-headed,
precisely so this moment would not become a renegotiation under sunk cost.
