# Decisions

Dated one-line ADRs, captured live. External sources are cited inline in the ADR
they support, with a checked-on date. The spec's own decisions (D1-D10) live in
[SPEC.md](SPEC.md) and are not duplicated here; this file records decisions about
*this repo* — its instrument, its gates, its layout.

- **ADR 1 (2026-07-20) — The plan lives in the project repo.** `docs/SPEC.md` is the
  byte-identical migration of `agentic-harness/docs/HARNESS-LAB-SPEC-2026-07-18.md`,
  amended by a dated section 10 rather than by silent edits. *Why:* the harness repo
  is the method; a consumer's plan belongs with the consumer, and an amendment that
  loses its date loses its cause.
- **ADR 2 (2026-07-20) — pip is bootstrapped inside the venv via `ensurepip`.** This
  machine has no global pip/pip3/pipx/uv, and `venv` + `ensurepip` work without sudo.
  *Why:* the alternative (asking for sudo, or a global installer) makes setup depend
  on machine state the repo cannot see. This constraint is the primary input for the
  future `py-base` template.
- **ADR 3 (2026-07-20) — Git hooks via `core.hooksPath .githooks`, not husky.** *Why:*
  husky would make a Python repo depend on a node toolchain to install its own hooks.
  Deliberate divergence from `ts-base` (ADR 9 of agentic-harness: stamped divergence).
- **ADR 4 (2026-07-20) — `verify` = `ruff format --check` + `ruff check` + `mypy
  --strict` + `pytest`, exposed as the single string `./scripts/verify.sh`.** *Why:*
  one canonical command that the pre-commit hook, CI and every rite call identically;
  a gate with two spellings drifts into two behaviors. Zero warnings: pytest runs with
  `filterwarnings = ["error"]`.
- **ADR 5 (2026-07-20) — No build backend; no editable install.** `pytest` puts `src/`
  on the path via `pythonpath`, mypy via `mypy_path`. *Why:* packaging machinery buys
  nothing here — the lab is run, not distributed — and every unused mechanism is a
  thing that can break.
- **ADR 6 (2026-07-20) — The spike is committed as a quarantined artifact**, excluded
  from ruff/mypy/pytest (`spike/`). *Why:* it is evidence of what was run on
  2026-07-20, not instrument code. Letting the formatter touch it would rewrite the
  evidence; its token accounting is *provably wrong* (F4) and must stay wrong on the
  record. See `spike/README.md`.
- **ADR 7 (2026-07-20) — Cost is measured as `output_tokens` + `num_turns`; cache
  fields are reported separately and never summed.** *Why:* the spike proved a summed
  token total is 91% cache mechanics and inverts under `--append-system-prompt` cache
  invalidation — it would have produced a false headline (SPEC.md F4).
- **ADR 8 (2026-07-20) — Public repo.** *Why:* the lab is a showcase whose value is
  published findings, and the server-side ruleset (require PR, no force-push, no
  deletion) — the only gate that binds every actor including bots — is free on public
  repos and paid on private ones. A private repo would have traded the real gate for
  nothing.
- **ADR 9 (2026-07-20) — Rites (`/feature`, `/audit`, `/debug`, `auditor`) copied from
  `agentic-harness@3226f96`** with `pnpm verify` -> `./scripts/verify.sh`, each
  carrying its provenance stamp. *Why:* stack-family rites are copied, not reinvented;
  the stamp makes the divergence auditable when the source moves.
- **ADR 10 (2026-07-21) — `long-skill` = `addyosmani/agent-skills@fea75b16`
  `code-simplification`, vendored verbatim and pinned by hash.** Selection rule
  pre-registered before any trial ran (SPEC.md D2 already fixed the family; it is the
  only skill in that repo aimed at an *authoring* agent rather than a reviewer; its
  content is directionally identical to `mini-skill`, which makes the comparison a
  test of length rather than of content). *Why vendored:* the upstream file moves, and
  a variable that changes silently invalidates every earlier comparison; "we used
  Osmani's skill" is not reproducible, a sha256 is. Rejected: `code-review-and-quality`
  as the long setup — it instructs an agent to review someone else's change before
  merge, a role the trials do not contain, so it would confound role mismatch with
  envelope length; parked in `setups/_phase3-candidates/`. Full provenance and the four
  declared limits: `setups/long-skill/README.md`.
- **ADR 11 (2026-07-21) — Every trial workspace is `git init`-ed with one initial
  commit, identically for all four setups.** *Why:* the long skill instructs the agent
  to `git blame` (line 118) and to `commit` (line 165); in a plain fixture directory
  those fail, and the turns spent land in the ADR 7 cost metric as if the envelope had
  caused them — the F4 class of error in a new place. Three sibling cases
  (`CLAUDE.md`, build, linter) are absent for every setup equally, so their cost is
  uniform rather than differential. Honest label: mitigation, not elimination — the
  long setup may still spend turns discovering an absence, and that is reported, not
  hidden.
- **ADR 12 (2026-07-21) — Envelope pins are enforced by a test, not by a note**
  (`tests/test_setups.py`, on every `verify`). *Why:* drift in an experimental variable
  produces runs that still succeed while silently measuring something else — the
  failure mode a README cannot catch. Shown red on a deliberate 3-line mutation before
  being trusted. The same test asserts `bare` and `force-cage` own no envelope file, so
  the floor and the cage cannot acquire content by accident.
