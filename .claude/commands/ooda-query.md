---
description: Ask the indexed corpus a question and show the verified citations
argument-hint: "<question>"
---

```bash
cd /home/user/claude && PYTHONPATH=src python3 -m oodarag.cli query "$ARGUMENTS"
```

Read-only, ~100ms. Add `-k N` for depth, `-v --json` to see the retrieved
chunks, `--filters '{"source_system":"filesystem"}'` to scope it.

Report the answer with its sources. Then check the footer:

- `confidence` and `coverage` - `coverage` is the share of claim sentences
  carrying a citation. Below 1.0 means part of the answer is ungrounded.
- `generator=extractive` is normal: no `ANTHROPIC_API_KEY`, so it falls back to
  extraction. Answers stay grounded and cited, just less fluent.
- **Exit code 1 means the system abstained**, not that the command failed.
  Observed: `generator=none confidence=0.0`, "The index contains nothing
  relevant to this question. Best query-term relevance was 0.00, below the 0.15
  floor." An abstention on a question the corpus *should* cover means retrieval
  missed - re-run with `-v` and read what came back before blaming the corpus.

`ooda query` applies **no contamination quarantine** - only `ooda eval` does.
So a golden question asked directly here can be answered from the doc that
quotes it (verified: "What is the capital of France?" answers from
`docs/EVALUATION.md` and exits 0, while the same case abstains correctly under
`ooda eval`). Never use a direct query to judge abstention behaviour; use the
eval.

Citations are verified against retrieved chunks, never generated. Do not
paraphrase past what the sources actually say.
