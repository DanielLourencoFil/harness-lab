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
