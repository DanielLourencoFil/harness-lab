# Setups — the four envelopes under test

One variable, four values. Everything else in a trial is held identical: same model,
same task text, same grader, same workspace, same caps (SPEC.md D2/D3).

| setup | envelope | file | role |
| --- | --- | --- | --- |
| `bare` | none | — (no file by definition) | floor / pure model |
| `mini-skill` | ~3 lines of steer | `mini-skill/SKILL.md` | cheap steer |
| `long-skill` | 13.5 KB curated skill | `long-skill/SKILL.md` | expensive steer / "wide net" |
| `force-cage` | mini + mechanical outer loop | — (lives in the runner) | the harness thesis |

`bare` and `force-cage` have no file here on purpose: `bare` is the absence of an
envelope, and `force-cage` is control flow (verify → red → re-invoke until cap), not
text. Both are implemented in the runner.

## Why mini and long say the same thing

`long-skill` is not a *different* instruction from `mini-skill` — it is the same
instruction elaborated ~63x (13,545 bytes vs 216). That is deliberate. The
pre-registered decision in SPEC.md D7 ("long-skill does not beat mini-skill on
success, at >=2x dynamic tokens -> skill body cap and 'mini over long' become
measured rows in CLAIMS.md") only means something if the two differ in *length and
elaboration*, not in content. If they said different things, any gap would be
content, and the length question would stay unanswered.

Compare for yourself: `mini-skill/SKILL.md` says "preserve existing behavior", "do
not modify test files", "keep the change scoped". `long-skill/SKILL.md` says the same
three things at lines 34, 311/323 and 103 respectively, with ~300 lines of
elaboration, tables and worked examples around them.

## Open decision for the runner: frontmatter

`long-skill/SKILL.md` carries YAML frontmatter (`name`, `description`); the mini
skill has none. Passing the file verbatim to `--append-system-prompt` therefore feeds
the long setup a few lines the mini setup never sees. Decide once, apply to all
setups, and record it: either strip frontmatter from every envelope, or pass every
envelope whole. Not yet decided — do not let the runner settle it by accident.

## The pin is mechanical

`tests/test_setups.py` asserts the sha256 of `long-skill/SKILL.md` on every `verify`.
An experimental variable that drifts silently invalidates every comparison made
before the drift, so the gate is a test, not a note. Changing the skill version is
legitimate — it just has to be a deliberate commit that updates the expected hash.

## `_phase3-candidates/`

Material kept but **not** under test in Suite Zero or the MVP. See its own README.
