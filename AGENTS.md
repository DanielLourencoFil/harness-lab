# Project conventions — canonical, vendor-neutral

Every coding agent reads this file (the [agents.md](https://agents.md/) standard).
`CLAUDE.md` / `GEMINI.md` are one-line adapters pointing here — edit THIS file, never
the adapters. Only conventions tooling cannot enforce belong here; lint/type/test
rules are wired (see `pyproject.toml`), not written as prose.

Adapted from `agentic-harness@3226f96` (`templates/ts-base/AGENTS.md`); the
TypeScript section is replaced by Python, and `pnpm verify` by `./scripts/verify.sh`.

## Values

correctness > trust > performance > dev speed. Never claim "done" without command
output as evidence — "it imports" ≠ "it works". Run `./scripts/verify.sh` before
declaring anything.

## Working rules

- Plan before code; minimal diff; one concern per commit (conventional messages).
- Read a file fully before editing; reuse-scan before creating any module/util.
- Three similar lines beat a premature abstraction: generalize at the third
  use case, never before.
- After a change, list now-orphaned code explicitly and ask before removing
  it — never silently delete, never silently leave.
- Names are grep-first: unique and searchable, no generic `handler` / `manager` /
  `data`. Agents (and humans) navigate by search; a generic name is noise.
- A non-obvious constraint in code gets a one-line why-comment at the site pointing
  to its ADR (`# why: <constraint> (ADR N)`). Agents read the file they are
  editing, not the docs folder; the why must live where the risk is.
- Tests ship in the same commit as the logic. A test changes only when its requirement
  changes, in a dedicated commit. Never weaken a test to pass it.
- Isolate non-determinism (time, network, subprocess, LLM, randomness) behind a
  fakeable seam; keep load-bearing logic pure and test it without mocks.
- A bug fix starts with a reproduction test shown failing, then turned green by the
  fix in the same commit — a fix without the red-first test is a hypothesis.
- Tests assert outcomes, never internal call sequences (interaction tests break on
  refactor while behavior holds). In test code, readable duplication beats clever
  shared helpers: each test reads as a spec on its own.
- Decisions → dated one-line ADRs in `docs/DECISIONS.md`, captured live. External
  sources are cited inline in the ADR they support, with a checked-on date.
- Commit atomically (verify-gated) and push the work branch without asking; merging
  to the default branch is the human's act — open a PR and stop.
- Agent-assisted commits carry a `Co-Authored-By` trailer naming the model; every PR
  fills the Provenance section of the template (tool, model + version, reviewer).

## Dependencies

- Stdlib-first: prefer the standard library and deps already in
  `requirements-dev.txt` over adding a new one. A new dependency is a decision, not
  a reflex.
- One new dependency per PR, in its own commit, with a one-line why (and the
  alternative it beat) in the commit body; load-bearing picks get an ADR.
- Upgrades read the changelog first — never bump on version number alone.
- An upgrade is verified by a green suite before AND after the bump — "it
  installed" proves nothing.
- Pins in `requirements-dev.txt` are exact (`==`) and bumped deliberately, in their
  own commit. Honest label: pinned, not hash-locked.

## Python

- Rely on inference internally; explicit annotations at public boundaries. mypy runs
  `strict`; `Any` and `# type: ignore` are defects, not escapes — if one is truly
  needed it carries a why-comment and an ADR.
- Validate at trust boundaries: anything read from a subprocess, a JSON file or the
  filesystem is `unknown` shaped until parsed and narrowed explicitly.
- Prefer pure functions and dataclasses over classes with mutable state.

## Project specifics

**The separation that keeps the experiment honest (SPEC.md D8).** This repo contains
two kinds of code and they obey different rules:

- **Instrument** (`src/`, `scripts/`, `tests/`) — runner, graders, analysis. A bug
  here means *false findings*, so it is fully gated: verify, strict types, tests.
- **Trial workspaces** — where the agent under test actually works. Their only
  envelope is the setup being measured. **The harness must never leak into a trial
  workspace**; if it does, the experiment measures the harness twice and the `bare`
  floor is fiction (see F3, which is exactly this failure, already observed).

Whenever you touch the runner, ask which side of that line the code is on. Anything
that copies files into, or configures, a trial workspace is load-bearing for the
lab's validity and gets a test.

**Measurement rules that are conventions, not lint (SPEC.md F4 / ADR 7).**

- Cost is `output_tokens` + `num_turns`. **Never sum token fields into a total** —
  a summed token count in this setting is a cache artifact, not a measurement.
- Cache fields (`cache_read`, `cache_creation`) are reported as separate columns.
- Results are always sliced by task type (trivial / hard / temptation), never
  published as a bare aggregate — the aggregate can invert the story.
- The task suite is **frozen before any setup runs**. Editing a task after seeing
  results is authorship bias, and no amount of care makes it recoverable.
- `spike/` is a quarantined historical artifact: it is excluded from verify and
  **must not be "fixed"** — its errors are the record.
