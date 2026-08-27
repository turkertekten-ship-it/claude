---
provenance: enforced
---

# `rag-audit` re-run against `src/oodarag/` — 2026-08-27

The first audit was run by another session against the tree before the
retrieval spine existed, and closed with: *"Re-run this audit when the retrieval
spine lands."* It has, so this is the re-run, against the same six categories.

> Framing, not a claim: the original audit and the skill it applied were
> written by `claude/personal-skills-repos-research-dxmflq`, and its findings
> are quoted from that branch rather than from a summary of it. The
> measurements below are this session's own.

## Observed — the five original findings

- All five findings of the original audit are closed. Four — the missing `cli.py`, the README presenting planned work as delivered, the four Makefile targets that could not succeed, and the chunking contract with no implementation — were closed by work done here before the audit was read. [src:AUDIT-CLOSED-2026-08-27]
- The fifth was conditional: record the `estimate_tokens` bias in the ADR once the eval harness landed. It is recorded there now. [src:AUDIT-CLOSED-2026-08-27]

## Observed — the four categories that could not be assessed before

- The original audit reported that embedding configuration, vector store setup, retrieval pipeline and generation configuration could not be assessed, because none of those stages existed. [src:SIBLING-AUDIT-2026-08-27]
- All four exist now and are assessed below. [src:AUDIT-RERUN-2026-08-27]

### Chunking strategy

- Chunking branches across four strategies — markdown, code, atomic and transcript — selected by document kind and refined by file suffix. [src:AUDIT-RERUN-2026-08-27]
- Overlap measured 18.0% of a 319-token average chunk, inside the 10-20% band the checklist gives. [src:AUDIT-RERUN-2026-08-27]
- Metadata survives chunking: `source_system`, `uri`, `title` and the heading path travel on every chunk. [src:AUDIT-RERUN-2026-08-27]

**Three defects fixed during this audit**, all found by measuring rather than reading:

- Overlap was a fixed single sentence, measuring **6.9%** of a 320-token chunk — below the band. It is derived from the target size now. [src:AUDIT-RERUN-2026-08-27]
- Both file connectors label every file `kind="file"`, markdown included, so **prose was being routed through the code strategy** — no overlap, split on definitions it does not have. Routing consults the suffix now. [src:AUDIT-RERUN-2026-08-27]
- `ChunkConfig.resolved()` overrode caller-supplied sizing with the policy's, so a requested `target_tokens=800` silently became 320. A field the caller changed now wins; only fields left at their default are filled by the policy. [src:AUDIT-RERUN-2026-08-27]

### Embedding configuration

- Dimension is 512, a power of two, sized against the Johnson-Lindenstrauss bound for this corpus; the choice and its cost are in the ADR. [src:AUDIT-RERUN-2026-08-27]
- Batch embedding exists, and duplicate text within a batch costs one computation. [src:AUDIT-RERUN-2026-08-27]
- **Fixed during this audit:** `hashing.py` documented an embedding cache keyed by content hash, and none existed. One exists now: 49.5% hit rate on a half-duplicate batch, 1.9x faster than the same batch uncached. [src:AUDIT-RERUN-2026-08-27]

> The honest caveat, which is not a defect: the embedder is a hashing trick,
> not a learned model. It captures term overlap and morphology, not meaning.
> The ADR states why, and `Embedder` is the seam for anyone who has a real one.

### Vector store setup

- Storage is one SQLite file — documents, chunks, float32 vectors, and an FTS5 external-content index kept in step by triggers. [src:AUDIT-RERUN-2026-08-27]
- The distance metric matches the representation: vectors are L2-normalised at construction and scored by dot product, which is cosine on normalised input. [src:AUDIT-RERUN-2026-08-27]
- **Not done:** there is no ANN index; dense scoring is an exact linear scan. At this corpus size that is the right trade — no recall loss, no parameters to get wrong — and the wrong one at a much larger size. [src:AUDIT-RERUN-2026-08-27]

### Retrieval pipeline

- Hybrid: an FTS5/BM25 arm and a dense arm, fused by Reciprocal Rank Fusion at k=60 with 1-based ranks. [src:AUDIT-RERUN-2026-08-27]
- Top-k is configurable, and the candidate pool is deliberately much larger than it so fusion has something to reorder. [src:AUDIT-RERUN-2026-08-27]
- A rerank stage applies source authority, exact-phrase presence, cross-arm agreement and heading-term overlap, bounded as a relative adjustment. [src:AUDIT-RERUN-2026-08-27]
- **Fixed during this audit:** retrieval had no metadata filtering. It has now, applied after fusion so the arms still see the whole corpus, and the report states how many candidates the filter removed. [src:AUDIT-RERUN-2026-08-27]

**Deliberately not done — score thresholding.** `min_score` exists and defaults
to off. A fused RRF score is not a similarity: at k=60 a hit ranked first in
both arms scores about 0.033, and that number means nothing outside the query
that produced it. A fixed threshold would be a magic constant dropping results
on one corpus and nothing on another. Abstention is judged in the generator,
against the retrieved text, where it can be judged.

**Not done — query expansion.** It needs a model, and the default path has none.

### Generation configuration

- Generation is extractive: an answer is assembled from sentences present in retrieved chunks, so it cannot contain a sentence the corpus does not. [src:AUDIT-RERUN-2026-08-27]
- Citations are verified against the chunks actually retrieved for that question, and `verify_citations` re-checks them afterwards — including for a generator this repository did not write. [src:AUDIT-RERUN-2026-08-27]
- Abstention is the hallucination guardrail: below a confidence floor the generator declines and says what it searched, and one eval case exists solely to check that it does. [src:AUDIT-RERUN-2026-08-27]
- Temperature does not apply, because there is no sampling. That follows from the extractive choice rather than being a setting.

### Production readiness

- Errors are classified rather than swallowed: the barrier taxonomy separates a blocked network from a missing credential from a spent quota, and states which are worth retrying. [src:AUDIT-RERUN-2026-08-27]
- One connector failing does not stop the others; the failure is carried in the report. [src:AUDIT-RERUN-2026-08-27]
- Rate limiting is a token bucket per client, and HTTP honours `Retry-After` and conditional requests. [src:AUDIT-RERUN-2026-08-27]
- Logging is structured, with a level and an optional JSON mode. [src:AUDIT-RERUN-2026-08-27]

## Result

- 236 tests pass, the provenance verifier is clean, and the eval scores recall@8 0.9286, MRR 0.9286 and nDCG@8 0.892 over 8 golden cases, with zero citation problems and zero contaminated cases. [src:AUDIT-RERUN-2026-08-27]

## What a third run should look at

Three things are known-absent rather than overlooked, and each has a trigger:

1. **An ANN index**, when the corpus outgrows an exact scan. The seam is `Retriever._dense_search`.
2. **A real tokenizer**, when chunk sizes must match a model's context budget rather than each other. The bias is documented in the ADR.
3. **Clause-aware chunking**, if the corpus becomes contract text. A second-hand report describes the owner's own documents as an M&A transaction set [src:SIBLING-AUDIT-2026-08-27], and a clause is a different retrievable unit from a section. Nothing has been built for that, and nothing has been ingested.
