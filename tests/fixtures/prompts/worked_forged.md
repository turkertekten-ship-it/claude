**Role.** You are working in this Python 3.11 repository.
**Context.** `tests/test_ingest.py::test_dedupe` fails with `KeyError: 'uri'`
after commit `1d7ce8f`. The module under test is `src/oodarag/ingest/base.py`.
**Task.** Make that test pass.
**Constraints.** Touch only `base.py`. Do not change the test. No new
dependencies.
**Output.** A unified diff, then two sentences on the root cause.
**Acceptance.** `python3 -m unittest tests.test_ingest -v` passes, and
`bash tests/run_all.sh` stays green.
**If you cannot.** If the failure does not reproduce, stop and report what you
actually saw rather than changing code to fit the description.
