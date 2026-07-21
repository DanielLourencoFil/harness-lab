# Harness Lab — decided spec (2026-07-18)

> **Provenance.** Moved here at kickoff (2026-07-20) from
> `agentic-harness/docs/HARNESS-LAB-SPEC-2026-07-18.md`, byte-identical — the plan
> lives in the project's own repo. Sections 1-9 are the document as approved and
> **were not rewritten**. Section 10 is new: the spike of 2026-07-20 amended two
> decisions, and an amendment must be visible and dated, never a silent edit.

**Status:** Phase 0 closed (owner-signed 2026-07-20) — kickoff pending the
interview-funnel week. Supersedes the exploratory
`docs/HARNESS-LAB-BRIEF-2026-07-17.md` (kept as the idea's origin) with the
decisions from the 2026-07-17/18 evaluation session. Every decision below
carries its why and what was rejected, so the owner can audit the reasoning.

**Owner's goal (verbatim intent):** measure the effectiveness of harness
setups against each other — e.g. a simple skill vs a complex one — to justify
choices with data and to tune agentic-harness itself.

---

## 1. The experiment in one paragraph

Same model, same task prompt, same grader — only the **envelope** changes
(no harness / short skill / long skill / force cage). Each run is graded by
tests written beforehand and locked, and priced in tokens and wall time. The
output is a table: which envelope passes more, at what cost — so harness
choices stop being taste and become measured trade-offs.

## 2. The weighing — does each element earn its place?

The owner's goal is two things only: **(a)** justify harness choices with
data, **(b)** tune agentic-harness. Every element below was weighed against
those two; anything serving neither was cut.

| Element | Serves (a)/(b) how | Verdict |
| --- | --- | --- |
| Microtasks + locked tests (D1) | The objective judge — without it there is no (a), only opinion | **Essential** |
| 4 setups incl. force-cage (D2) | The comparison IS the product; without force-cage, (b)'s core thesis stays untested | **Essential** |
| Identical success predicate (D3) | Without it the comparisons are invalid — silently kills (a) | **Essential** |
| Envelope vs dynamic tokens (D4) | Without it H-steer is confirmed by arithmetic — fake (a) | **Essential** |
| Pre-registered decision table (D7) | The bridge to (b): each result changes a named thing in the harness | **Essential** — this is what makes the lab load-bearing instead of curious |
| Real-CLI runner (D6) | Measures the harness people actually use; also 10× cheaper to build | **Essential** |
| Suite Zero first (D10) | Attacks the dominant risk (never finishing) | **Essential** |
| Temptation tasks (D5) | Measures layer A's actual claim (destruction avoided) — unique signal | **Supporting, high value** — in MVP, not Suite Zero |
| Placebo skill | Separates length from content — sharpens (a) | **Supporting** — Phase 3 only |
| Formulation ablation (canonical terms vs paraphrase, same content) | Tests the retrieval-cue hypothesis: canonical terminology activates the model's learned clusters, paraphrase is noise — turns skill-writing style from taste into data. Design rule: manipulate INSTRUCTION CONTENT terms only, never identity labels — the identity axis is already empirically dead (persona prompts don't improve objective performance: Zheng, Pei et al., Findings of EMNLP 2024, checked 2026-07-19) | **Supporting** — Phase 3 only |
| Blind human sample | Secondary sanity check on "maintainability" | Optional — only if FINDINGS v1 ships |
| Explore/edit time proxies (brief §6.4) | Curiosity; serves neither (a) nor (b) directly | **Cut from MVP** |
| cost_usd column | Pricing drift; tokens already carry the signal | **Cut** |
| Second model, multi-agent, toolization, dashboards | Scope traps named by the brief itself | **Cut from scope** (Phase 3+ at most) |
| Single showcase app (todo + auth + DB) | Not measurable objectively (see D1) | **Cut as data**; optional demo later |

## 3. Decisions made (with justification)

### D1 — Many small tasks, not one big app

**Decided:** ~20 microtasks (pure functions from failing tests, bug fixes,
simplify-under-locked-tests, boundary validation), each with a pre-written,
locked test suite as the objective judge.
**Why:** one big app (todo + auth + DB) gives one noisy data point per run
and no objective judge — "quality of a whole app" is opinion. Twenty small
tasks × 4 setups give 80+ gradable points and a paired analysis (which setup
succeeded where another failed).
**Rejected:** the single showcase app as the measurement unit (kept at most
as a later out-of-scope demo, never as data).

### D2 — Four setups in Phase 1, force-cage included

| setup | envelope | role |
| --- | --- | --- |
| `bare` | task text only | floor / pure model |
| `mini-skill` | ~10-line steer (simple code, preserve behavior, don't touch tests) | cheap steer |
| `long-skill` | long curated skill (Osmani-style simplification) | expensive steer / "wide net" |
| `force-cage` | mini (or no) skill + mechanical outer loop: verify must pass or re-invoke until cap | the harness thesis |

**Why force-cage in Phase 1:** without it the lab only compares steer with
steer, and the core thesis (force > steer) stays untested.

**Methodological guard — the cage's pass-rate is partly tautological.** The
force-cage re-invokes until verify is green (or the cap), so a higher
pass-rate than one-shot `bare` is close to true by construction; reporting it
raw would be a finding a reviewer demolishes in one sentence ("of course, it
had retries"). The honest comparisons are therefore:
- **equal budget** — `bare` and `force-cage` capped at the same turns/tokens,
  so the cage never wins merely by being allowed more attempts;
- **cost conditional on success** — among tasks where both passed, what each
  spent (the §4 metric);
- **`cap_hit` reported per setup** — how often the cage failed to converge.

And the non-obvious hypothesis this setup actually tests: the cage puts the
agent under **pressure to go green**, which is precisely the condition that
tempts corner-cutting — weakening a test, widening scope. `tests_locked` and
`scope_ok` (D3) catch exactly that. **A live possibility is that the cage
worsens restraint** — that iterating-until-green causes more cheating than
`bare`, which simply fails honestly. That result would contradict our own
thesis, which is what makes this a measurement rather than a ceremony.

**Phase 2 addition — placebo skill:** same length as `long-skill`, generic
content-free advice. Separates the cost of *length* from the effect of
*content* — if long-placebo ≈ long-skill, wide nets are length, not wisdom.

### D3 — Identical success predicate across ALL setups (fix of brief §6.1)

```
success ≡ tests_pass AND tests_locked AND scope_ok
```

evaluated by the grader outside the agent's reach, identically for every
setup. `verify_green` inside force-cage is that setup's internal mechanism,
never part of the cross-setup success definition.
**Why:** if setups have different success bars, "equivalent success"
comparisons (the whole point of Q4) are meaningless.
**Rejected:** the brief's "(optional) verify_green if the setup defines it"
— a design bug.

### D4 — Envelope tokens separated from dynamic tokens (fix of brief §8.3)

Record `tokens_envelope` (fixed input cost of the setup, known before any
run) apart from `tokens_dynamic` (everything the run generates and consumes
beyond it).
**Why:** a long skill trivially costs more total tokens because it is long —
that is arithmetic, not a finding. The real question is whether it changes
*behavior* cost (turns, exploration, output) and success.

### D5 — Temptation tasks: measure destruction avoided, not only success

3–5 tasks with deliberate traps: messy adjacent code begging for drive-by
cleanup, a test that could be weakened, an "obvious" out-of-scope file.
`out_of_scope_files`, `tests_locked` and diff size then measure exactly what
layer A claims to prevent.
**Why:** the cage's value may be tail-risk prevention rather than average
quality; without these tasks that hypothesis is unmeasurable and a null
result on pass-rate would be misread as "the cage is useless".

### D6 — Runner drives the real agent CLI headless, on the owner's fixed plan

`claude -p` per trial run under the owner's **fixed subscription plan
(Pro/Max), never metered API**. Clean workspace per trial, caps on
turns/tokens/wall-clock, prompt-caching policy equalized across setups.
Force-cage is an **outer loop of the runner**: agent finishes → grader runs
verify → red and turns remain → re-invoke with the log.
**Why:** a hand-built API loop measures a toy, not the harness anyone
actually uses, and building it is the bulk of the project's cost. The
efficiency metric the lab needs is **tokens**, and the CLI reports `usage`
tokens in its JSON regardless of billing — so the fixed plan measures exactly
what metered API would, at zero marginal cost. This is a personal-use +
showcase project; paying per-token API for it would be waste (D4's
tokens-not-dollars stance made concrete; `cost_usd` stays cut, §2).
**The honest constraint is plan rate limits, not dollars:** a ~120-trial
batch may hit usage limits and must run phased (smoke first, then batched,
off-peak if needed) — the kill-dates (§6) protect against that becoming an
open-ended stall.
**Rejected:** metered API billing (proibitive for a self-use showcase; carried
in from the external brief by inertia, corrected on owner review 2026-07-20);
custom agent loop; multi-model in MVP.

### D7 — Pre-registered decision table (what each result changes)

The lab is load-bearing only if outcomes have consequences agreed BEFORE the
first run:

| Pre-registered result | Consequence in agentic-harness |
| --- | --- |
| long-skill ⊁ mini-skill on success, at ≥2× dynamic tokens | Skill body cap + "mini over long" doctrine become **measured** rows in CLAIMS.md |
| force-cage ↑ pass-rate at acceptable cost | force > steer graduates from doctrine to measured claim |
| force-cage ⊅ mini on efficiency, but wins temptation tasks | Honest relabel: the cage buys tail-risk prevention, not average quality |
| bare/mini destroy in temptation tasks, cage does not | Layer A gets its first quantitative evidence |
| No detectable differences anywhere | Published negative + steer growth freezes (only force enters) pending better instruments |

**Why:** without this table the lab is a curiosity; with it, every cell is an
owner decision currently made by taste, converted to data.
**New ledger status:** findings enter `docs/CLAIMS.md` as **measured** rows
(source: harness-lab suite vN) — the lab becomes the evidence supplier the
ledger lacks (today: 0 measured claims).

### D8 — Own repo, created at kickoff — and yes, gated by agentic-harness

**Own sibling repo** (`~/Dev/harness-lab`), created via `/kickoff` in a fresh
session in that folder (session scoping). Not a folder inside agentic-harness.
**Why:** the harness is the method repo; the lab is a consumer with its own
lifecycle, findings and possibly its own public future. Dependency direction
stays lab → harness (consumes a slice), per the brief's §9.

**Gated by the harness? Yes — it is the first real `/kickoff` consumer, and
skipping the cage on the instrument would undermine both projects.** What
applies, honestly labeled:

- **Machine layer: already force today** — containment, secret hooks,
  deliberation nudge fire in every session regardless of repo.
- **Layer 0 by doctrine, Python instance:** the lab is Python (pytest is the
  natural deterministic grader; the analysis is pandas/notebook). There is no
  `py-base` template yet, so kickoff assembles Layer 0 from the PLAYBOOK
  (verify = ruff + mypy + pytest on pre-commit and CI, deletion guard,
  gitignore, conventions skeleton) — and **`py-base` is extracted from this
  project afterwards**, the sanctioned extract-on-first-real-use path
  (Roadmap), a harness-candidate born from real consumption.
- **Rites copied with provenance stamps** (/feature, /audit, /debug), adapted
  from pnpm to the Python verify — deliberate, stamped divergence (ADR 9).
- **Ruleset + CI** per the kickoff checklist.

**The critical separation (so gating does not contaminate the experiment):**
the cage wraps the **instrument** (runner, graders, analysis — where a bug
means false findings); the **trials** run in sandboxed per-trial workspaces
whose only envelope is the setup under test. The harness must never leak into
a trial workspace; the selftest of the lab should assert that (a `bare` trial
workspace contains no harness files).

### D9 — Statistics sized to reality

Paired per-task analysis (helped/hurt counts), medians with bootstrap CIs,
effect sizes; no p-value theater at N≈20. Pre-registered honest limit:
effects under ~10–15pp are below this instrument's resolution. "No detectable
difference" is a publishable, pre-registered outcome (D7 last row) — the
suite does not grow until an effect appears.

### D10 — Suite Zero before MVP (completion risk is the dominant risk)

Walking skeleton first: **5 tasks × 4 setups × 2 runs (~40 trials) through
the COMPLETE pipe** (runner → grader → parquet → notebook → FINDINGS draft).
Only then scale tasks to ~20 and runs to 3.
**Why:** the realistic failure mode is an 80%-built lab with no FINDINGS —
worth zero. A small lab with published FINDINGS is the whole value.

## 4. Metrics (consolidated)

- **Success:** the D3 predicate, identical everywhere.
- **Quality proxies:** files_changed, loc±, out_of_scope_files, lint/complexity
  signals on the artifact; tests_locked as hard fail.
- **Cost:** tokens_envelope, tokens_dynamic, wall_s, turns, cap_hit.
- **Efficiency:** pass_rate; median dynamic tokens conditional on success;
  mean including failures; Pareto pass-rate × cost. The brief's "4× rule"
  stands as a pre-registered inefficiency threshold on dynamic tokens.
- **Explicitly not primary:** LLM-judge "simplicity" scores (circular),
  transcript self-reports, human vibes. Small blind human sample only as a
  labeled secondary.
- **Always sliced by task type — never only the aggregate.** Report pass-rate
  and cost separately for trivial / hard / temptation tasks. The aggregate
  hides the story and can invert it: on easy tasks the cage is pure overhead,
  and if that dilutes the temptation-task result the table will read "the
  harness costs more for nothing" while the opposite is true where it matters.
  The likeliest real finding is shaped like *"on easy tasks the cage is
  overhead; on trapped tasks it is the only thing preventing destruction"* —
  and only the sliced view can say it.

## 5. Task suite rules

- Frozen before any setup runs (authorship bias guard); part adapted from
  external katas. First candidate external seed task: the planted-bug
  workspace of patchy631/ai-engineering-hub `build-code-harness` (2 real bugs,
  pytest 3F/2P, "fix only account.py, never edit a test" — bug-fix type with
  tests_locked + scope_ok built in; evaluated 2026-07-19, ledger C-086).
- Deterministic domains only (parsers, validators, scoring rules): no
  network, no clock.
- Layout per task: `task.md` + optional `src/` + locked `tests/` +
  `grade.json` (allowed paths, budgets).
- Caps generous and equal across setups; cap_hit reported per setup
  (force-cage loops must not be strangled by unequal budgets).

## 6. Phases and kill criteria

| Phase | Content | Gate to next |
| --- | --- | --- |
| 0 — Spec lock | This document + owner approval | Owner signs |
| 1 — Suite Zero | 5 tasks × 4 setups × 2 runs, full pipe, FINDINGS draft | Pipe produces a real table |
| 2 — MVP | ~20 tasks × 4 × 3, temptation tasks in, FINDINGS v1 | FINDINGS published |
| 3 — Extensions | placebo skill, formulation ablation (canonical vs paraphrase), TS mini-suite, second model, toolization | Only if reused after v1 |

**Kill criteria (owner-signed 2026-07-20):** no running Suite Zero by
**2026-08-10**, or no FINDINGS v1 by **2026-09-15** → project parks (option C)
automatically, spec preserved. A kill-date is a pre-registered circuit breaker,
not a delivery target: if the milestone has not happened by the date, the
project freezes without renegotiation — the decision to stop was made now,
clear-headed, not later under sunk-cost pressure. Lab work never displaces the
career funnel or product work — it is the 3rd priority by standing order.

## 7. Relationship to agentic-harness (summary)

| agentic-harness | harness-lab |
| --- | --- |
| Ships products; force > steer as doctrine | Measures envelopes; turns doctrine into data |
| CLAIMS.md: enforcement degrees, 0 measured | Supplies **measured** rows |
| Grows only via harness-candidate queue (ADR 18) | Findings feed the queue and the ledger, never auto-expand the catalog |
| Gates the lab's instrument code (D8) | Never gates the trial workspaces (D8) |

## 8. Phase 0 — closed 2026-07-20

1. ✅ Spec approved (this document).
2. ✅ Kill dates set (§6): Suite Zero by 2026-08-10, FINDINGS v1 by 2026-09-15.
3. ✅ No dollar budget — runner is the owner's fixed plan (D6); the only cost
   constraint is plan rate limits, mitigated by phased runs.
4. Kickoff timing: after the current interview-funnel week (Ingentis 20-24.07),
   in a fresh session opened in `~/Dev/harness-lab` (session scoping, D8).

## 9. What the lab cannot measure (declared limits)

These belong in FINDINGS v1 verbatim. The lab's credibility comes from
marking where its authority ends, not from claiming more than it measured.

1. **Cross-sectional, while the harness's strongest claim is longitudinal.**
   Every trial is one isolated task. The harness's biggest assertion — that it
   stops a codebase from rotting over months of AI-assisted work — is about
   *accumulation*, and no single-task measurement can reach it. This is the
   most serious limit: the lab can support "the cage prevents this class of
   damage per task", never "the cage keeps a codebase healthy for a year".
2. **Headless, with no human in the loop.** The harness puts human judgment at
   the root by design ("100% of the work automated, 100% of the decision
   human"). The lab runs the agent alone, unattended. So it measures **the
   mechanical half, in a setting that is not how the harness is actually
   used**. FINDINGS must say "we measured the force cage without a human",
   never "we measured the harness".
3. **Design quality is out of reach, deliberately.** Correctness (tests) and
   restraint (tests_locked, scope_ok, out_of_scope_files, diff size) are
   measurable; "well-designed, readable, appropriately abstracted" is not —
   and faking it with an LLM judge is the circularity §4 rejects. Content
   judgment stays human (RATIONALE's fourth category).
4. **Narrow domain, perishable numbers.** Deterministic tasks (parsers,
   validators, scoring rules) say nothing about UI, distributed systems or
   exploratory work; and every number expires when the model changes. What
   survives a model release is the **protocol and the instrument**, not the
   table.
5. **Resolution floor.** At ~20 tasks, effects under roughly 10-15 percentage
   points are indistinguishable from noise (D9). "No detectable difference" is
   a pre-registered, publishable outcome — not a reason to grow the suite
   until an effect appears.

## 10. Spike findings (2026-07-20) that amend this spec

Sections 1-9 were written over three days of specification. A ~2-minute spike then
ran the mechanism end to end (one task, two envelopes, agent headless, grader
outside the agent's reach) and produced four findings that specification had not
reached. Two of them **correct decisions above**; they are recorded here rather than
edited into the text, so the correction keeps its date and its cause. The spike
itself is preserved under `spike/2026-07-20-mechanism/`.

### F1 — The runner is a standalone script, not something driven in conversation

`claude -p` refuses to run inside an existing Claude Code session ("nested sessions
will crash all active sessions"; the `unset CLAUDECODE` bypass exists and was not
used). **Consequence:** the runner is a script the owner launches from a plain
terminal. This is the right design regardless — ~120 trials is unattended batch work.

### F2 — `--append-system-prompt` is the envelope mechanism (positive finding)

Each setup in D2 is a different value of that one flag. The complete runner is
roughly ten lines. The measurement design in §1 is mechanically cheap; the cost of
this project is the task suite and the analysis, not the harness plumbing.

### F3 — Amends D2: `bare` is not bare

`claude -p` reads `~/.claude/` — the machine-layer constitution and hooks — so the
"no envelope" setup actually carries the entire machine layer. In the spike, 141k
cache-read tokens were the constitution re-read seven times.

**Consequence:** there is no true floor until the machine layer is neutralized
(clean `HOME`, or an empty `--settings`). Until then `bare` measures
"machine-layer only", not "pure model", and must be labeled that way. **This is
open debt, owed before Suite Zero produces a comparable floor** — not resolved by
this document.

### F4 — Amends D4: the naive token accounting is invalid

The spike's runner summed every field whose name contained "token". That total was
91% `cache_read`, and worse: `--append-system-prompt` changes the system-prompt
prefix and therefore **invalidates the cache**, producing 2.5x `cache_creation` for
the setup under test. Of the 32k "extra" tokens attributed to the mini-skill, 99%
was cache mechanics and only 168 tokens (0.5%) was real output.

The headline "the mini-skill costs 20% more" would have been **false** — an artifact
of the instrument, not a property of the envelope.

**Consequence — the cost metric of D4 is now:**

- **compare on `output_tokens` + `num_turns`** (behavioral cost — what the envelope
  actually changed in the agent's conduct);
- **report cache fields separately**, never folded into a total;
- **never publish a summed token count.** A single summed number in this setting is
  not a measurement, it is a cache artifact wearing a measurement's clothes.

This sharpens rather than replaces D4's envelope/dynamic split: the split says
*which* tokens to separate, F4 says *which arithmetic on them is legitimate*.

## 11. Runner findings (2026-07-21) — what building it taught

Section 10 recorded what a two-minute spike taught three days of specification.
Building the runner taught more, and in the same shape: every item below was found by
running something, none by reasoning about it. They are recorded here rather than
edited into the decisions above, so each keeps its date and its cause.

### F5 — Neutralizing the machine layer takes three fixes, not one

F3 named the problem (`claude -p` reads `~/.claude/`) and implied one fix. Three were
needed, each found only after the previous one was made:

1. **`HOME` must be neutralized** — but not emptied: credentials live in
   `~/.claude/.credentials.json`, and without them the CLI returns "Not logged in".
   A trial `HOME` carries that one file and nothing else.
2. **The working directory must be outside any repository carrying instruction
   files.** The CLI reads `CLAUDE.md` / `AGENTS.md` from **ancestor** directories.
   Trial workspaces initially sat in `runs/` inside this repo, so every trial
   inherited harness-lab's own constitution — the `bare` floor ran carrying two.
   A structural check of the workspace directory reported clean throughout.
3. **Every invocation needs its own `HOME`.** The CLI *writes* to `HOME` as it runs:
   `.claude.json`, `.claude/settings.json`, `.claude/debug/`, `.claude/todos/`, and
   `.claude/projects/<workspace>/*.jsonl` — **session transcript**. A `HOME` reused
   across trials would let trial N read trial N-1's history, a cross-trial leak no
   inspection of a workspace could ever detect.

**Consequence:** neutrality is not a property of `HOME` alone. It is a property of
(`HOME`, working directory, invocation count), and it is verified per invocation.

### F6 — Structural checks cannot certify a floor; ask the agent

At the moment the floor was contaminated, both structural guards passed:
`assert_neutralized` (the `HOME` held only credentials) and `assert_no_harness_files`
(the workspace directory was clean). A structural check looks for what its author knew
to look for.

The runner therefore runs **trial zero** before each measurement: it asks the agent, in
the exact directory the trial will use, to list every instruction file it can see, and
aborts unless the answer is `NONE`. The agent is the only witness with sight of
everything actually injected. This is wired into the runner, not left as a command
someone remembers.

### F7 — `cache_read` is not evidence of contamination

The pre-registered F3 criterion was "cache_read should collapse". It does not, and it
never could: per turn it is flat at ~20-21.5k across a contaminated run, a partially
contaminated run and a clean one, because it is the CLI's own built-in system prompt
being re-read. The owner's `CLAUDE.md` is small beside it.

Had the structural check not existed, the observed 15% drop was narratable as success.
**Second instance of the F4 lesson: token fields are a poor instrument for structural
questions, and the direction of a plausible number is not evidence of its cause.**

### F8 — The result JSON reports `subtype: "success"` on failed runs

A run that failed to authenticate returned `"subtype":"success"` with
`"is_error":true` and `"output_tokens":0`. A runner filtering on `subtype` would record
a failed trial as a successful, free one. **The success signal is `is_error == false`**;
`output_tokens == 0` is treated as an aborted run, not a cheap one.

### F9 — The apparatus is not part of the harness, and neutralizing removes it too

Neutralizing `HOME` silently changed the model from `claude-opus-4-6` to the CLI
default `claude-sonnet-4-6`, because the model came from `settings.json`. The machine
layer holds two separable things: the **harness** (constitution, hooks, skills,
memory), whose absence is what `bare` measures, and the **apparatus** (model, effort),
which D3 requires to be constant. Only the first is neutralized; the second is pinned
by flag and **verified after the run** against the result's `modelUsage`, since a flag
is an intention and the result is evidence. `--fallback-model` is never set, so an
overloaded model fails loudly rather than switching mid-batch.

**Declared limit:** `--effort max` is rejected for Claude.ai subscribers, though the
owner's machine sets `effortLevel: max`. The lab pins `high`, the closest available.
D3 requires the effort to be constant, not maximal — but the lab measures slightly
below the owner's interactive conditions, and FINDINGS must say so.
