# Evidence — F3 paid, 2026-07-21

The artifacts of the first trial that ran on a genuinely isolated floor. Committed
because `tests/test_preconditions.py` asserts against them: a precondition marked paid
on the strength of "the code exists" is a claim, while one backed by a recorded run is
evidence anyone can re-read.

`runs/` is gitignored (trial output is data). These two files are the exception.

## What was verified

| check | result |
| --- | --- |
| Trial zero — agent asked what instruction files it sees | `NONE` (`contamination.txt`) |
| `is_error` | `false` |
| Model actually used | `claude-opus-4-8` — matches the pin |
| Locked tests | `INTACT` |
| Task outcome | `PASS` |

Command: `./scripts/run-trial.sh 01-account-bugs bare`, from a plain terminal.

## It took three fixes to get here, none of them foreseen by the spec

| # | what was wrong | how it was found |
| --- | --- | --- |
| 1 | trials ran against the real `HOME` | SPEC F3, known before the runner existed |
| 2 | workspaces sat in `runs/` **inside this repo**, and the CLI reads instruction files from **ancestor** directories — so every trial inherited harness-lab's own `CLAUDE.md` | asking the agent, from inside the workspace |
| 3 | a `HOME` was checked once and reused, but the CLI **writes** to `HOME` while running — including `.claude/projects/<ws>/*.jsonl`, which is session transcript | the runner's own guard aborted the trial |

Fix 3 is the one that would have been worst if missed: a shared `HOME` would have let
trial N read trial N-1's transcript, and no structural check of a workspace would ever
have seen it.

## The numbers, and why they are not the proof

| run | out | turns | cache_read | cache_creation | read/turn |
| --- | --- | --- | --- | --- | --- |
| spike (opus-4-6, real HOME) | 998 | 7 | 141,122 | 12,658 | 20,160 |
| contaminated (HOME neutral, cwd in repo) | 930 | 6 | 119,882 | 30,579 | 19,980 |
| **clean (isolated)** | **725** | **5** | **107,781** | **2,222** | **21,556** |

**`cache_read` was never a contamination signal.** Per turn it is flat across all
three — it is the CLI's own built-in system prompt being re-read, and the owner's
`CLAUDE.md` is small beside it. The pre-registered criterion ("cache_read should
collapse") was measuring the wrong quantity, and had the structural check not existed,
a 15% drop could have been narrated as success.

`cache_creation` collapsing 30,579 → 2,222 is consistent with instruction files being
absent, and the drop in turns and output tokens is consistent with the machine layer
costing work. **Neither is offered as a finding:** n=1, the spike ran a different
model, and nothing here was repeated. These are smoke-test numbers whose only job was
to show the pipe runs.

The gate that closed F3 is the structural check plus trial zero — both green, both
mechanical, both re-runnable.
