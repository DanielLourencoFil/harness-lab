# Phase 3 candidates — kept, not under test

Material that is deliberately **not** a setup in Suite Zero or the MVP. Kept because
it is useful later and because deleting a considered option loses the reasoning that
rejected it.

## `code-review-and-quality.md`

From `addyosmani/agent-skills`, 20.5 KB. Copied in on 2026-07-20 as a long-skill
candidate and rejected for that role: it instructs an agent to **review someone
else's change before merge** (five axes, approval standards, review turnaround), while
our trials have the agent **authoring** a fix alone and headless, with no PR and no
reviewer. As the long-skill it would have confounded role mismatch with envelope
length.

**Why it is still interesting (Phase 3):** it is a good, well-written skill pointed at
the wrong role — which makes it the natural probe for a question the current design
cannot ask. *What does a high-quality envelope aimed at the wrong task shape do to
success and cost?* If wide-net skills work by generic activation rather than by
matching the task, an off-role skill should perform like an on-role one. If it does
not, "fit" is doing the work, not "quality".

Not pinned to a commit yet — it is not a live variable. Pin it before it becomes one.
