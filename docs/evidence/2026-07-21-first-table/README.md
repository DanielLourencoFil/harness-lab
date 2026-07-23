# Evidence — the first valid two-row table, 2026-07-21

Two trials, same task, same grader, same apparatus; only the envelope differed. Both
completed, both graded by the full D3 predicate, both with zero permission denials.
This is the walking skeleton of D10 producing an actual table.

**It is not a finding, and the reason is at the bottom.**

## The table

| setup | D3 | out | turns | cache_read | cache_creation | wall_ms |
| --- | --- | --- | --- | --- | --- | --- |
| `bare` | SUCCESS | 681 | 5 | 107,775 | 2,326 | 18,808 |
| `long-skill` | SUCCESS | 717 | 5 | 149,374 | 11,255 | 16,421 |

Both: `tests_pass PASS`, `tests_locked INTACT`, `scope_ok OK`, `permission_denials 0`,
model verified as `claude-opus-4-8` (with the CLI's internal `claude-haiku-4-5` helper
recorded separately).

## ADR 7 vindicated on real numbers

| metric | bare → long-skill |
| --- | --- |
| **output_tokens** (ADR 7) | 681 → 717 — **+5.3%** |
| **num_turns** (ADR 7) | 5 → 5 — **identical** |
| naive summed total (the F4 error) | 110,782 → 161,346 — **+45.6%** |

The naive metric this project already rejected once would report the long skill as
**46% more expensive**. The behavioral metric reports +5.3% output at the same number
of turns. The 41,599 extra `cache_read` and 8,929 extra `cache_creation` are the
13,203-character envelope sitting in the prompt prefix — arithmetic, not behaviour.

F4 was found by reading a spike's code. This is the same effect measured deliberately,
with the correct instrument beside the wrong one.

## Why this is not a finding

**The noise is three times the signal.**

Two *clean* `bare` runs, same task, same everything:

| run | output_tokens | turns |
| --- | --- | --- |
| 1 | 572 | 4 |
| 2 | 681 | 5 |

`bare` varied by **109 tokens (19.1%)** against itself. The `bare` → `long-skill` gap
is **36 tokens (5.3%)**. At n=1 per cell these are indistinguishable, and any statement
of the form "the long skill costs more" would be reading run-to-run variance.

This is SPEC D9's pre-registered resolution floor — "effects under ~10-15pp are below
this instrument's resolution" — arriving on the first day with numbers attached. It is
also a concrete design input: **two runs per cell (D10's Suite Zero plan) is unlikely
to resolve an effect this size**, and that is worth knowing before 40 trials are spent
rather than after.

The task is also trivial by construction (`task.json`: `difficulty: trivial`), so a
null result here was expected and carries no information about envelopes.
