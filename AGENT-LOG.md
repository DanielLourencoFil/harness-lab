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
