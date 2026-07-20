# harness-lab

Measures **harness envelopes against each other**: same model, same task, same
grader — only the envelope changes (no harness / short skill / long skill / force
cage). Each run is graded by tests written beforehand and locked, and priced in
tokens and turns. The output is a table: which envelope passes more, at what cost —
so harness choices stop being taste and become measured trade-offs.

The lab is the evidence supplier for
[agentic-harness](https://github.com/DanielLourencoFil/agentic-harness)'s claims
ledger, which today holds zero measured claims.

- **What and why, in full:** [docs/SPEC.md](docs/SPEC.md)
- **Decisions:** [docs/DECISIONS.md](docs/DECISIONS.md)
- **Where the agent helped and failed:** [AGENT-LOG.md](AGENT-LOG.md)
- **Conventions tooling cannot enforce:** [AGENTS.md](AGENTS.md)

## Setup

```bash
./scripts/bootstrap.sh   # venv + pip (via ensurepip) + pinned deps + git hooks
./scripts/verify.sh      # format + lint + typecheck + test — the canonical gate
```

`bootstrap.sh` bootstraps pip *inside* the venv because this machine has no global
pip/pipx/uv. See [docs/DECISIONS.md](docs/DECISIONS.md).

## The separation that keeps the experiment honest

The harness gates the **instrument** (`src/`, runner, graders, analysis — where a
bug means false findings). It must never leak into a **trial workspace**, whose only
envelope is the setup under test. See D8 in the spec.

## Status

Phase 0 closed (spec locked). Phase 1 — Suite Zero — is next: 5 tasks x 4 setups x 2
runs through the complete pipe. Pre-registered kill dates: Suite Zero by 2026-08-10,
FINDINGS v1 by 2026-09-15.
