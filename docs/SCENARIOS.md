# Scenario checklists

What must always be true, and what must never be possible, per feature. The owner
answers; the agent writes the test code. A scenario that matters becomes a named test —
this file is a view over those tests, never a parallel source of truth.

---

## Runner step 1 — one trial, neutralized (2026-07-21)

Closes preconditions F3 (machine layer) and ADR 11 (git workspace). Scope: run one
task under one setup (`bare`) end to end and measure it.

### What two probes changed, before any code was written (2026-07-21)

**Probe A — an empty `HOME` breaks authentication.** `claude -p` returned
`Not logged in · Please run /login`. Credentials live in `~/.claude/.credentials.json`.
So the neutralized `HOME` carries that one file and nothing else.

**Probe A also exposed a trap in the result format:** the failed run reported
`"subtype":"success"` with `"is_error":true` and `"output_tokens":0`. A runner
filtering on `subtype` would have recorded a failed trial as a successful one with
zero cost. **The success signal is `is_error == false`, never `subtype`.**

**Probe B — neutralizing `HOME` silently changed the model.** The spike ran
`claude-opus-4-6` (from `settings.json: model: opus`); the neutralized probe ran
`claude-sonnet-4-6`, the CLI default. This forces a distinction the design did not
have:

| machine-layer content | what it is | neutralize? |
| --- | --- | --- |
| `CLAUDE.md`, hooks, skills, `projects/` | **the harness** — the object of the experiment | **yes** — its absence is what `bare` measures |
| `model`, `effortLevel`, `switchModelsOnFlag` | **the apparatus** — the conditions of measurement | **no** — pinned explicitly, identical for every setup |

Neutralizing `HOME` removes both. Only the first should go; the second returns as
explicit flags, or "same model" (D3) is faith rather than fact.

**Also learned:** `cache_read: 0` in probe B is *not* proof the constitution is gone —
the spike's 141,122 came from 7 turns re-reading what turn 1 cached, and this probe ran
1 turn with nothing to re-read. The structural check is the gate; the token comparison
is only evidence when it is like-for-like (same task, same turn count).

### Always true

- A trial runs with `HOME` pointing at a **temporary directory containing only
  `.claude/.credentials.json`**, unique to that trial and deleted afterwards. The
  harness is treated as a black box: neutralizing it must not depend on our being able
  to enumerate what lives in `~/.claude/`.
- The apparatus is pinned explicitly on every invocation: `--model claude-opus-4-8`
  (full name, never the `opus` alias, which moves), `--effort high` (`max` is rejected
  for Claude.ai subscribers — a declared limit, see `apparatus.py`), and an explicit
  tool grant, identical for every setup.
- The trial **verifies** the apparatus rather than trusting it: the `modelUsage` key in
  the result JSON must match the pinned model. `--fallback-model` is never set, so an
  overloaded model fails loudly instead of silently switching mid-batch.
- A trial is successful only when `is_error == false`.
- A trial workspace is a **git repository with one initial commit** before the agent
  is invoked (ADR 11), identically for every setup.
- The trial records `cache_read_input_tokens` **as reported evidence** alongside the
  structural check. The spike measured 141,122; the number after neutralization is
  what shows a reader of FINDINGS that the contamination actually went away.
- The envelope sent to the agent is `harness_lab.envelopes.render(setup)` — never a
  file read at the call site.

### Never possible

- **A trial must never run against the real `HOME`.** If the environment is not
  neutralized, the runner **aborts before spending a single token**. A contaminated
  trial is not recoverable after the fact, and a warning in stdout is a warning nobody
  reads in an unattended 40-trial batch.
- A trial workspace must never contain harness files (`CLAUDE.md`, `AGENTS.md`,
  `.claude/`), whether copied in by the runner or pulled in by the envelope — the long
  skill instructs the agent to "Read CLAUDE.md / project conventions" (line 49), so
  the leak has two directions.
- The grader must never run inside the agent's reach, and must never be able to be
  edited by the agent.
- An unknown setup name must never render an empty envelope and silently become an
  unlabeled `bare` trial (already guarded in `test_envelopes.py`).
- **A trial must never be recorded as successful on `subtype` alone** — probe A
  produced `"subtype":"success"` for a run that failed to authenticate.
- **A trial must never be recorded when the model that ran it differs from the model
  pinned.** Silent model substitution invalidates the D3 constant, and a fallback is
  exactly how it would happen unnoticed in an unattended batch.
- A trial reporting `output_tokens == 0` must never be recorded as a normal result: it
  is the signature of an aborted or refused run, not of a cheap one.

### Forbidden state transition

- A trial that aborted (contaminated environment, missing task, failed workspace
  preparation) must never produce a result row. There is no "partial" trial: it either
  ran clean and is recorded, or it did not run and nothing is written. A half-written
  result is worse than no result, because it enters the dataset looking complete.

### Abuse / carelessness

- Running the runner from inside a Claude Code session (F1: `claude -p` refuses, and
  `unset CLAUDECODE` would bypass the refusal). The runner should detect and refuse
  rather than produce a confusing nested-session error.
- Re-running a trial into a workspace that already exists, silently mixing a previous
  run's artifacts into the new one.
- Pointing the runner at the quarantined `spike/` fixture instead of a live task, so
  results describe a file that is documented as historical evidence.
