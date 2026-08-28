# Constraint grades across this repository's own forged prompts — 2026-08-27

Each prompt checked against a dummy answer, to inventory what its constraints
are rather than whether an answer met them.

## tests/fixtures/prompts/worked_forged.md
```
0/0 countable constraint(s) held, 2 runnable but not run here, 5 for a reader to judge


  runnable — this tool does not execute commands; run these yourself:
    $ python3 -m unittest tests.test_ingest -v
      to satisfy: `python3 -m unittest tests.test_ingest -v` passes, and
    $ bash tests/run_all.sh
      to satisfy: `bash tests/run_all.sh` stays green.

  for a reader to judge — no command named, nothing countable:
    · Touch only `base.py`.
    · Do not change the test.
    · No new
    · dependencies.
    · A unified diff, then two sentences on the root cause.
```

## tests/fixtures/prompts/clean_task.md
```
1/2 countable constraint(s) held, 0 runnable but not run here, 8 for a reader to judge

  ok   MAX_COUNT        at most 40 lines             1 lines
  FAIL ONE_CODE_BLOCK   one code block               0 fenced block(s)

  for a reader to judge — no command named, nothing countable:
    · no third-party actions beyond `actions/checkout`;
    · do not add
    · dependencies;
    · `python3 -c "import yaml,sys;
    · yaml.safe_load(open('.github/workflows/ci.yml'))"`
    · parses it, and the job name is exactly `checks`.
    · If the repository already has a workflow at that path, say so and stop rather
    · than overwriting it.
```

## The finding

The skill's exemplar prompt — the one documented at 100/100 — has **zero**
countable constraints. Two of its seven are runnable: they name a command
(`python3 -m unittest ...`, `bash tests/run_all.sh`). The rest are prose.

That is not a bad prompt. It is the strongest kind of acceptance test there
is, and the first version of check_output.py filed it identically to "make it
clean" — which would have steered authors away from naming commands.
