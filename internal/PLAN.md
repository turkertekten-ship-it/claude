# Build plan

What is built, what is next, and the order the pieces have to land in.

## Status

| Stage | State |
|---|---|
| **Zero-dependency core** — HTTP client, robots, crawler, HTML extraction, GitHub connector | Built |
| **Nightly `reflect` loop** — observe, orient, decide, act, learn | Built |
| Chunking, embedding, index | Not started |
| Hybrid retrieval (dense + BM25, RRF fusion) | Not started |
| Answer generation with verified citations | Not started |
| Eval harness (recall@k, MRR, nDCG, citation coverage) | Not started |
| Retrieval-freshness OODA loop | Not started |

`ooda index`, `ooda query`, `ooda eval`, `ooda demo` and `ooda loop` are declared
in the CLI and exit with a message rather than a traceback. They will start
working as the stages below land, in this order.

## The nightly loop (built)

Documented in the README and in `docs/adr/0002-autonomy-tiers.md`. In summary:

```
Observe   sources/     chat transcripts, shell history, the file tree, git log
Orient    detect/      13 rules across friction, terminal, docs, hygiene
Decide    decide/      learned priors, risk gating, budgets, conflict resolution
Act       act/         backed-up atomic edits, review queue, the nightly report
Learn     journal.py   append-only verdicts, folded into tomorrow's priors
```

Verified end to end against this repository: it observes ~230 signals, produces
18 findings and 10 proposals, applies the one `safe`-tier fix, is idempotent on
a second run, and `ooda reflect revert <cycle>` puts everything back.

The web and GitHub stack has since had a full adversarial review: 128 defects
fixed, 663 tests added, three features that had never worked at all. Written up
in `REVIEW-2026-08-28.md`.

### Known limits, deliberately

- `.gitignore` support is a documented subset; negation (`!`) lines are dropped
  rather than approximated, which errs toward observing less.
- `friction.*` needs several sessions of history before it says anything. On a
  fresh machine the first useful night is the third or fourth.
- Rule promotion is not implemented. `src/oodarag/reflect/decide/priors.py` already computes the
  per-rule confidence that would drive it; the gap is evidence from real use,
  not code. See ADR 0002.

## Next: chunking and the index

The loop gave the project its `Signal` -> `Finding` -> `Proposal` spine and a
working actuator; retrieval needs the parallel `Document` -> `Chunk` ->
`ScoredChunk` path, which `src/oodarag/models.py` already declares.

1. **chunk/** — structure-aware splitting over the sections
   `util.text.split_markdown_sections` already produces, with the contextual
   header `Chunk.context_header` exists for. Prose, markdown, code and dialogue
   each need their own boundary rule; the shared part is the header.
2. **embed/** — the hashing-trick embedder behind an interface, with a
   content-hash cache. Deterministic and cheap by construction, per ADR 0001,
   so a hosted model is an accelerator rather than a requirement.
3. **index/** — SQLite, one table per arm. The lexical arm is BM25 over a
   postings table; the dense arm is a flat scan until it is measurably too slow.
4. **retrieve/** — both arms fused with reciprocal rank fusion, keeping the
   per-arm components on `ScoredChunk.components` so a bad result can be
   attributed to an arm rather than guessed at.
5. **generate/** — extractive first. `Answer.citations` is verified against
   retrieved chunk ids before an answer is returned, never generated alongside
   the text.
6. **eval/** — a goldens file under evals/ plus recall@k, MRR, nDCG and citation
   coverage. This lands before any tuning: "is retrieval any good" has to be a
   number before anyone is allowed to have an opinion about chunk size.
7. **`ooda loop`** — the freshness cycle. `IngestDelta` is already the Observe
   half of it.

Steps 1-3 can proceed in parallel; 4 needs all three; 6 should land no later
than 4, because tuning without it is guesswork.
