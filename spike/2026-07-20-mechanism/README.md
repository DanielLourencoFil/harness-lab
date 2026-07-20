# Mechanism spike — 2026-07-20

**This is a historical artifact, not instrument code. Do not fix it.**

It is excluded from `verify` (`pyproject.toml`: ruff `extend-exclude`, mypy
`exclude`, pytest `testpaths`) on purpose. Its token accounting is *provably wrong*,
and that error is the most useful thing this directory contains — correcting it here
would delete the evidence. The correction lives in `docs/SPEC.md` §10 F4 and ADR 7.

Originally produced in a session scratchpad under `/tmp` (ephemeral); migrated here
at kickoff as the project's first versioned artifact.

## What it proved

The riskiest assumption in the spec — that the measurement mechanism works at all —
died in about two minutes of execution, after three days of specification. One task
(`account.py` with two planted bugs, locked test file), two envelopes, agent run
headless, grading performed outside the agent's reach, workspaces isolated.

```
setup        | tests    | testfile | tokens*  | wall
-------------|----------|----------|----------|------
bare         | PASS     | INTACT   | 154785   | 26s
mini-skill   | PASS     | INTACT   | 186847   | 27s
```

*The `tokens` column is the invalid metric — see below.

Both setups passed with the test file intact. That is the correct outcome for a
trivial task and carries **no quality signal**: it shows the pipe runs, nothing more.

## The four findings

**F1 — `claude -p` refuses to run inside a Claude Code session** ("nested sessions
will crash all active sessions"). Bypass is `unset CLAUDECODE`; it was not used.
Consequence: the real runner is a standalone script launched from a plain terminal.

**F2 — `--append-system-prompt` is the envelope mechanism.** Each setup is one value
of that flag. The plumbing is roughly ten lines; the cost of this project is the task
suite and the analysis.

**F3 — `bare` is not bare.** `claude -p` reads `~/.claude/`, so the "no envelope"
setup carries the whole machine layer: the 141,122 `cache_read` tokens below are the
constitution re-read across turns. There is no true floor until `HOME` is neutralized.

**F4 — the token accounting in `run.sh` is invalid.** It sums every `usage` field
whose name contains "token" (see the `PY` heredoc in `run.sh`). Raw numbers from
`bare.json` and `mini-skill.json`:

| field | bare | mini-skill | delta |
| --- | --- | --- | --- |
| `output_tokens` | 998 | 1,166 | **+168** |
| `num_turns` | 7 | 8 | +1 |
| `cache_creation_input_tokens` | 12,658 | 31,560 | +18,902 (2.5x) |
| `cache_read_input_tokens` | 141,122 | 154,113 | +12,991 |
| naive sum | 154,785 | 186,847 | +32,062 |

`cache_read` alone is 91% of `bare`'s total. And `--append-system-prompt` changes the
system-prompt prefix, which **invalidates the cache** — hence 2.5x `cache_creation`
for the setup under test, an artifact of measuring, not of the envelope.

The naive sum reads "the mini-skill costs 20.7% more". Of those 32,062 extra tokens,
**168 (0.5%) were real output**; the rest was cache mechanics. **That headline would
have been false.**

Fix, now binding on the real runner: compare on `output_tokens` + `num_turns`, report
cache fields as separate columns, and never publish a summed token count.

## Contents

- `run.sh` — the throwaway runner, wrong accounting included.
- `task.md`, `fixture/` — the task and the buggy starting state.
- `bare/`, `mini-skill/` — the workspaces each setup produced (the artifacts graded).
- `bare.json`, `mini-skill.json` — the CLI's own output, the source of the table above.
- `results.txt` — the table as printed on the day.
- `account.py`, `test_account.py`, `bare-result.json` — loose files from building the
  fixture, kept as found.

Empty `*.err` files (stderr was empty for both runs) were dropped in the migration.
