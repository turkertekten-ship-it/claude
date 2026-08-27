# The data-checker contract

A data checker answers one question about a repository, and answers it with
observations rather than impressions. Everything here exists to keep the review
itself from becoming another unbacked claim.

## Shape

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from tools.claims import RepoIndex
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register


@dataclass
class MyChecker:
    name: str = "my_checker"
    description: str = "One line: what question this answers."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        ...


register(MyChecker())
```

## Rules

1. **Quote, never paraphrase.** A `Claim.text` is a verbatim substring of the
   file at `Claim.path`, on `Claim.line`. A reader must be able to run
   `sed -n '<line>p' <path>` and see it.

2. **Every verdict carries its evidence.** `Finding.__post_init__` enforces
   this. Use `Evidence.at()` for a file location, `Evidence.ran()` to record a
   command that was actually executed, `Evidence.measured()` for a computed
   value, and `Evidence.absent()` when the finding *is* that something is not
   there - `absent()` requires you to name the search space, because "not found"
   without one is a guess.

3. **`UNVERIFIABLE` is a real answer.** If the check cannot decide - network is
   off, a file is unparseable, the claim is too vague to resolve - emit
   `Verdict.UNVERIFIABLE` with `detail` naming what stopped it. Never round an
   undecidable check to `SUPPORTED`. Never round it to `CONTRADICTED` either.

4. **Prefer `CONTRADICTED` over `UNSUPPORTED` only with positive evidence.**
   `UNSUPPORTED` means "I covered the search space and found nothing backing
   this". `CONTRADICTED` means "I found something that says the opposite". These
   are different findings and a reader will act on them differently.

5. **Be quiet when there is nothing to say.** Do not emit a `SUPPORTED` finding
   for every claim that passes; a report where 900 lines of noise hide 4 real
   problems has failed. Emit `SUPPORTED` only where confirming is itself
   informative (a headline claim like "zero dependencies"), and say so in the
   description.

6. **No false positives from ambiguity.** If the leading token of a "command"
   does not resolve to anything, it was prose in a code fence, not a command:
   skip it silently. A checker that cries wolf gets switched off, and then it
   catches nothing at all.

7. **Deterministic.** Same repository, same verdicts. No clocks, no randomness,
   no network unless `config.allow_network` is set. Sort anything you iterate
   from a set or dict.

8. **Read-only.** A checker never writes to the repository under review.

## Severity

| Severity | Use for |
|---|---|
| `ERROR` | A documented promise that is broken now: a command that fails, a path that does not exist, an entry point that cannot be imported. Fails the run. |
| `WARN`  | A claim that is unbacked but not provably false: an unsourced number, a capability described in prose with no code behind it. |
| `INFO`  | Confirmations worth stating, and drift that is cosmetic. |

## Tests

Each checker ships `tests/test_<name>.py` using `unittest`, stdlib only. Build
fixtures with `tempfile.TemporaryDirectory()` and write real files into it -
never monkeypatch `RepoIndex`. Cover, at minimum:

* the true positive (a fabricated claim is caught),
* the true negative (a well-supported claim is not flagged),
* one ambiguity case that must **not** produce a finding (rule 6).

Run them with `PYTHONPATH=. python3 -m unittest tests.test_<name> -v` from the
repository root before you report done.
