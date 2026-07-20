---
name: audit
description: Fresh-context audit of a completed unit with reify-to-test triage. Use after a feature or module is complete, or on demand for a named scope.
source: agentic-harness@3226f96
---

<!-- Copied verbatim from templates/ts-base; no command adaptation needed. -->

# /audit <scope: directory, module, or diff>

1. Launch the `auditor` agent (fresh context, read-only) on the named scope.
   Pass the scope verbatim. Do not add "find bugs" framing: the auditor's
   prompt is neutral by design, and "none found" is a valid outcome.
2. Triage every finding by reifying it into a test:
   - Write a test that reproduces the finding.
   - Test fails on current code = real bug: report it and propose the fix
     (apply only if the human asks).
   - Test passes on current code = the finding was confabulated: discard it
     and delete the test.
   - Low-confidence findings without a reproduction are leads, not facts:
     list them separately, do not act on them.
3. Log the outcome in `AGENT-LOG.md`: N findings, N real, N confabulated.
   This ratio calibrates how much to trust future audits.

## Rationalizations this rite refuses

Replies are statements, never open questions: a session answers an open
question to itself silently and moves on.

| Alibi | Reply |
| --- | --- |
| "This finding is obviously real; skip the test" | Obvious findings are the cheapest to reify. A finding that will not become a red test is not a bug. |
| "I wrote this code; I can audit it in this session" | The writing session defends its own choices. The auditor runs in a fresh context (step 1), always. |
| "Zero findings looks lazy; report something" | "None found" is a valid, welcome result. An invented finding costs a confabulation entry in the log. |

## Verifiable output

- The auditor's report: per-finding severity, confidence, and concrete reproduction.
- One test per triaged finding, shown red (real) or discarded as confabulated.
- The `AGENT-LOG.md` line with the found-real / confabulated counts.
