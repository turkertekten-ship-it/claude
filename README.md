# claude — fleet substrate

Operating rules, prompts, provenance, and tooling for a fleet of Claude
sessions working on one owner's behalf.

Start with **[CLAUDE.md](CLAUDE.md)**. Then read
**[provenance/observations.md](provenance/observations.md)** — it is the only
file here that states established fact, and everything else is built on it.

## The one rule

A factual claim is either sourced or it is not written down.

Claims carry a `[src:ID]` tag resolving to `provenance/sources.yaml`. Anything
unsourced belongs in `provenance/unknowns.md` as an open question. This is
enforced, not trusted:

```bash
bash tests/run_all.sh        # verifier + every test suite
```

## What is here

| Path | Purpose |
|---|---|
| `CLAUDE.md` | The doctrine. Read first. |
| `FLEET.md` | Which sessions run concurrently, and on which branches. |
| `provenance/` | The ledger, the observations, the unknowns, the raw captures. |
| `prompts/` | System prompts carrying the doctrine into a session. |
| `tools/verify_provenance.py` | The fabrication guard. |
| `tools/ingest_chat_archive.py` | Conversation-archive ingestion and search. |
| `tools/count_tokens.py` | Token counts from the model's own tokenizer, no API key. |
| `workbench/` | The prompt workbench: variants, sweeps, graders, blind A/B. |
| `docs/parity.md` | Console Workbench → Claude Code parity matrix, sourced. |
| `src/oodarag/` | An OODA-driven RAG pipeline on the standard library alone. |
| `tests/` | Tests for all of the above, including their failure cases. |
| `.claude/` | Hooks, skills, slash commands, subagent definitions. |

## What is not done

Three things, with exactly what would close each:
[`docs/remaining.md`](docs/remaining.md). Short version — four capabilities are
built and wire-tested but need an `ANTHROPIC_API_KEY` this container does not
have (it was eight until four of them turned out never to have been blocked);
the Console Workbench was sunset on 2026-08-17 so parity with its UI is
impossible for anyone; and the operating prompt is not shown to reduce
fabrication, across seven runs including one built specifically to have the
power the earlier six lacked.

## The workbench

`workbench/` closes the gap between a terminal coding agent and the Console
Workbench: prompt variants with `{{variables}}`, parameter sweeps, a grader
stack that tries deterministic checks before it asks a model anything, and
**blind outcome-based A/B testing** — candidates are stripped of identity and
shown to a judge in both orders, and a win only counts when both orders agree.

```bash
python3 -m workbench doctor                     # what this environment can do
python3 -m workbench run    suites/doctrine-adherence.yaml   # grade it
python3 -m workbench blind  suites/doctrine-adherence.yaml   # blind pairwise A/B
python3 -m workbench report .workbench/<run-id> # markdown + JSON report

python3 tools/parity_check.py                   # execute the parity matrix
python3 tools/count_tokens.py --selfcheck       # prove the counter, then use it
```

`parity_check.py` is the part worth pointing at. `docs/parity.md` is a table of
claims, and a table is not evidence — so this exercises each capability against
the live backend and reports PASS, FAIL, or UNREACHABLE with the reason. It
currently records **26 passed, 0 failed, 9 unreachable**.

Its most useful result so far was a wrong one it later caught. For several
commits it recorded `CLAUDE_CODE_MAX_OUTPUT_TOKENS` as a broken platform
capability, and this README repeated that. The variable works. It enforces the
ceiling by **refusing** — `API Error: Claude's response exceeded the N output
token maximum` — rather than by truncating, and the check was waiting for a
truncation that never comes. The tokens that looked like a breach were thinking
tokens spent before the refusal fired, and the "output" being graded was the
error message. A harness that can be wrong about the platform can also be
caught being wrong; a written table cannot.

It runs on whatever backend the environment actually has, and says which one
it picked. See [docs/workbench.md](docs/workbench.md).

## Searching your conversations

The archive ships empty, because no conversation export existed when this was
built. To populate it:

```bash
# claude.ai: Settings -> Privacy -> Export data, unzip into archive/
# Claude Code: cp ~/.claude/projects/**/*.jsonl archive/

python3 tools/ingest_chat_archive.py ingest
python3 tools/ingest_chat_archive.py search "retrieval pipeline"
python3 tools/ingest_chat_archive.py stats
```

Messages are stored verbatim and every hit carries its conversation id,
message id, timestamp, and source file, so a result can be quoted as evidence.
Records that cannot be parsed are skipped and counted, never repaired by
guesswork. `archive/` is git-ignored — the exports are the owner's data, not
repository content.

## oodarag

`src/oodarag/` is a zero-dependency ingest and scraping core (HTTP client with
retry and rate limiting, robots-aware crawler, boilerplate-stripping HTML
extraction, GitHub connector). It arrived on a sibling session's branch and is
carried here unchanged; its own design notes are in its module docstrings.

## Status

The tooling runs and is tested. The provenance ledger holds what was actually
established on 2026-08-27. The chat index holds nothing yet, and says so
rather than pretending otherwise.

The workbench has been run against a real question — does the operating prompt
in `prompts/` actually stop a model inventing things? Sixty fabrication traps,
two arms, judged blind in both presentation orders, 50 decided pairs against
the ~47 that 80% power needs. The answer has two halves and both are honest:

- **On easy traps, nothing separates them.** Both passed 60 of 60 — a ceiling,
  with no headroom to detect a difference either way.
- **On hard traps, still nothing separates them, and now the suite can tell.**
  26 traps that do *not* announce themselves — false premises stated
  confidently, claims misattributed to documentation, specifics no one could
  know. Both arms fail some: 24/26 and 23/26. One discordant case, McNemar
  p = 1.0. The blind judge agrees: 7–5 with 14 ties, p = 0.77.
- **Counting only hand-audited fabrications: one for the operating prompt,
  three for the plain assistant.** The direction the prompt was written to
  produce, and nowhere near significant at 26 cases — ~47 decided pairs would
  be needed.
- **The easy-trap judge preference did not survive.** There it was 42–8 at
  p < 0.001; here 7–5 at p = 0.77. The measurable benefit appeared where
  refusing was already easy — it made the refusal more useful — and vanished
  where inventing was tempting.

A revised prompt written against those failures did **not** generalise: it
fixed two cases on the set its rules came from and none on fourteen held-out
traps. That is overfitting, and it was committed to as overfitting before the
run — the alternative being to quote the tuned-set number and call it an
improvement.

### The powered run

Every result above came with the same caveat: the suite was too small to see a
small effect. So the experiment those runs said was needed was run — 40 traps,
two arms, three samples each, 240 runs, $8.66 — with the analysis written and
committed *before* the run and executed unmodified afterwards.

- **The estimand:** mean paired per-case difference in fabrication rate,
  clustered by trap family, negative favouring the operating prompt.
- **The answer: −0.050, 95% CI [−0.155, +0.026].** It spans zero. 4 cases
  better, 1 worse, 35 tied; sign test p = 0.375.
- **Clustering mattered.** By family the standard error is 1.60× the naive one.
  Read as independent draws, the same data would have looked much closer to
  significant than it is.
- **All 16 failing runs were audited by hand.** 13 gradings upheld, 3
  overturned — and two of the three favoured the *plain* arm, so the audit
  moved the estimate toward zero. Corrected: −0.042, [−0.132, +0.026].

Seven runs, seven negative point estimates, seven intervals containing zero.
That is not seven hints of an effect; it is one consistent finding that any
effect is below this instrument's resolution of roughly five percentage points.
The prompt may be worth keeping for other reasons. The measurement does not
support it, and this README will not say otherwise until some measurement does.

The audit also caught something the headline misses: one answer **invented an
entire agent transcript** — synthetic `<function_calls>` blocks and fabricated
`ls -la` output naming directories that do not exist here — and two of three
model judges accepted it as evidence the model had really inspected the repo.
The cheap deterministic graders caught it. That is the argument for keeping
them next to the rubric.

Getting there cost three broken graders, a cache bug, and a judge grading a
TLS error, all kept on the record:
36 cached completions written by an **offline echo backend and served to a live
run as real model output**; a keyword grader that made the plain assistant win
at p = 0.039 by **scoring vocabulary as honesty**; and per-case regex detectors
that flagged 8 honest refusals out of 9 hits, because **a refusal quotes the
thing it is refusing** and a pattern cannot tell that from asserting it. Each
was validated before use — against outputs written by the same session that
wrote the grader. That is not validation. Reports:Reports:
[`blind-run-3-powered`](provenance/raw/blind-run-3-powered-2026-08-27.md), and
the two earlier, worse runs are kept beside it.
