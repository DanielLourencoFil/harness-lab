# Phase 3 candidates — kept, not under test

Material that is deliberately **not** a setup in Suite Zero or the MVP. Kept because
it is useful later and because deleting a considered option loses the reasoning that
rejected it.

## `code-review-and-quality.md`

| field | value |
| --- | --- |
| Source | `addyosmani/agent-skills`, `skills/code-review-and-quality/SKILL.md` |
| Commit pinned | `e270415226899ad9c6947e5474a16f28bb0a2f55` (authored 2026-06-27) |
| Retrieved | 2026-07-21, via `gh api` at that ref |
| Size | 20,543 bytes |
| sha256 | `bec431b759ff389e47b8d2c9d74e1981ff93cf5f3c36b4a3b6a71a75c250be2c` |

Provenance is recorded now even though the file is not yet a live variable: deferring
the *hash* is defensible, but the commit a file was copied at cannot be recovered once
upstream moves, and recording it costs nothing today. (The first copy taken by hand on
2026-07-20 was one byte short — a missing trailing newline — and was replaced by the
`gh api` fetch above, the same defect found in the long-skill copy.)

Rejected as the long-skill: it instructs an agent to **review someone else's change
before merge** (five axes, approval standards, review turnaround), while
our trials have the agent **authoring** a fix alone and headless, with no PR and no
reviewer. As the long-skill it would have confounded role mismatch with envelope
length.

**Why it is still interesting (Phase 3):** it is a good, well-written skill pointed at
the wrong role — which makes it the natural probe for a question the current design
cannot ask. *What does a high-quality envelope aimed at the wrong task shape do to
success and cost?* If wide-net skills work by generic activation rather than by
matching the task, an off-role skill should perform like an on-role one. If it does
not, "fit" is doing the work, not "quality".

Its hash is recorded above but **not enforced** by `tests/test_setups.py`: enforcement
arrives when it becomes a live variable, and the pin is only meaningful once something
reads the file. Promoting it to a setup means adding it to the pinned set there.
