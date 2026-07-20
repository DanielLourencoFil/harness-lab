---
name: feature
description: Feature implementation rite - spec interview, plan approval, negative tests first, evidence gate. Use when starting any new feature; the rite runs on invocation instead of from memory.
source: agentic-harness@3226f96
---

<!-- Copied from templates/ts-base. Deliberate divergences (ADR 9):
     `pnpm verify` -> `./scripts/verify.sh`; the scenario checklist is recorded in
     docs/SCENARIOS.md, not docs/SPEC.md, because SPEC.md here is a locked research
     plan (amended only by dated sections), not a growing feature spec. -->

# /feature <short feature description>

Run the playbook's feature loop. Do not skip or reorder steps.

## 1. Spec interview (the human owns the answers)

Ask the human, one question at a time, and record the answers:

- What is ALWAYS true once this feature works? (becomes the positive tests)
- What must NEVER be possible? (becomes the negative tests: the cases AI forgets)
- Which state transition is forbidden? (becomes the impossible-case test)
- How would a malicious or careless user abuse this?

Write the resulting scenario checklist into `docs/SCENARIOS.md`.

## 2. Plan before code

Propose a short plan: files affected, existing components to reuse (run the
reuse-scan first), and any scenarios you would add to the human's checklist.
Do NOT write production code until the human approves the plan.

## 3. Negative tests first

Write the negative tests from the checklist and show them failing. If you
cannot write a negative test, you do not understand the feature yet: stop
and ask.

## 4. Implement

Minimal diff until `./scripts/verify.sh` is green. Tests ship in the same commit
as the logic. Commit and push per the repo conventions.

## 5. Evidence and closeout

"Done" requires shown command output: verify green, plus the feature actually
exercised. No evidence = report status as "IMPLEMENTED - NOT VERIFIED" with
the exact command the human should run. If the project keeps a plan or
execution doc, update its matching entry now (the doc is a view over the
tests, never a parallel source of truth). Remind the human that a completed
unit gets `/audit` in a fresh context.

## Rationalizations this rite refuses

Replies are statements, never open questions: a session answers an open
question to itself silently and moves on.

| Alibi | Reply |
| --- | --- |
| "Too small for the full rite" | A rite skipped when small stops firing when large. The steps shrink with the task; they are not optional. |
| "I'll add the tests right after the code" | After-the-fact tests describe the implementation, not the behavior. Negative tests come first (step 3). |
| "Verify is green, so it works" | Verify gates regressions; "works" requires the feature exercised with output shown (step 5). |
| "The plan is obvious; the human would approve" | Approval is an event, not an inference. No production code before it happens (step 2). |

## Verifiable output

- `docs/SCENARIOS.md` updated with the scenario checklist (human's answers recorded).
- Negative tests shown failing before implementation, then green.
- `verify` output pasted; the feature exercised with its output shown.
- Commits pushed per the repo conventions (SHAs in the closeout).
