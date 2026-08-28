# Forged: the standing request behind this repository

> This is the owner's own request, put through `tools/prompt_forge.py`. The raw
> version scored 38/100 and named no artifact, no bound, no output shape and no
> failure case. Every slot below is filled from what was actually built and not
> corrected over twelve loops — not from a reconstruction of what was in their
> head. Where that distinction matters, the prompt says so rather than
> pretending. Paste it, correct the parts that are wrong, and it becomes theirs.

## ROLE

You work on `turkertekten-ship-it/claude`, which holds the operating doctrine
for a fleet of Claude sessions. Read `CLAUDE.md` and
`provenance/observations.md` before acting.

## CONTEXT

A prompt system already exists here: `tools/prompt_forge.py` lints and compiles
prompts against seven slots, `tools/check_output.py` checks an answer against
the constraints its prompt stated, `tools/prompt_habits.py` scores the prompts
already written, and `tools/learn_rule.py` appends what a failure taught. It
installs into `~/.claude` for every terminal;
`prompts/portable-preamble.md` is the version that travels to a chat window.
Two different frameworks are called CLEAR — Lo's and Saraev's — and the linter
reports under either.

## TASK

Extend or correct that system. Name the artifact you will produce before you
start: a rule, a tool, a document, a measurement, or a correction to one that
exists.

## CONSTRAINTS

Python 3.11, standard library first. Every tool exits 0 for no findings, 1 for findings, and 2 when it
could not run. Work on the branch named in your session record and push only
there. Do not add a rule without a test that has been watched rejecting
something. Do not widen scope beyond the artifact you named.

## OUTPUT CONTRACT

A pushed commit, and a reply of at most 400 words saying what changed, what it
measured, and what you deliberately did not do.

## ACCEPTANCE TEST

`bash tests/run_all.sh` exits 0, which now runs twelve checks including
`tools/check_consistency.py` and the installed-copy comparison. Any factual
claim added carries a `[src:ID]` resolving in `provenance/sources.yaml`.

## IF YOU CANNOT

If a claim cannot be sourced, put it in `provenance/unknowns.md` and say it is
unknown. If a source cannot be reached, say which and why rather than working
around a policy denial. If this prompt's own reading of the request is wrong —
it was reconstructed from delivered work, not from the owner's words — say so
and ask, rather than building further on a misreading.
