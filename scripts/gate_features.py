#!/usr/bin/env python3
"""Which signals can tell an answerable question from an unanswerable one?

`gate_margin.py` showed the gate's current feature does not separate the two at
any coverage exponent: the highest-scoring unanswerable case outscores the
lowest-scoring answerable one by 0.18, and no threshold classifies every case.
That is a feature problem, not a threshold problem, so this ranks candidate
features instead of tuning the one in use.

Reported as AUC - the share of (answerable, unanswerable) pairs the feature
orders correctly - because it is threshold-free, and because a pass count at a
fixed floor conflates the feature with the floor. 0.5 is a coin flip.

    PYTHONPATH=src python3 scripts/gate_features.py

The sample is small (8 unanswerable cases here). AUC says a feature is worth
investigating; it does not say it generalises. Nothing goes into the gate on
this evidence alone - see internal/LEARNINGS.md L22 on measurement decay.
"""

from __future__ import annotations

import shutil
import statistics
import sys
import tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.text import tokenize

from _corpora import EXTERNAL as CORPUS  # noqa: E402


def unstemmed_vocabulary(store) -> set[str]:
    """Every surface form the corpus contains, before stemming.

    Answerability asks whether a query term is in the corpus vocabulary, and
    that vocabulary is stemmed - so a term absent from the corpus but sharing a
    stem with one that is present reads as *present*. "What is the boiling point
    of mercury?" is answered because `mercury` and `mercurial` both stem to
    `mercuri` and one page mentions the version control system.
    """
    vocabulary: set[str] = set()
    for row in store.conn.execute("SELECT text, context_header FROM chunks"):
        vocabulary.update(tokenize(f"{row['context_header']} {row['text']}"))
    return vocabulary


def document_terms(store, chunk_ids: list[str]) -> dict[str, set[str]]:
    """Stemmed terms per *document* for the documents these chunks came from.

    Coverage is measured per chunk, so a query whose terms are spread across a
    document scores low on every one of them. The opposite also matters and is
    what this is for: a document covering the whole query while no single chunk
    does is the shape of "Which package renders Jinja templates to PDF?" - jinja,
    template and render are all present, just never beside pdf.
    """
    chunks = store.get_chunks(chunk_ids)
    doc_ids = {c.doc_id for c in chunks.values()}
    out: dict[str, set[str]] = {}
    for doc_id in doc_ids:
        terms: set[str] = set()
        for row in store.conn.execute(
                "SELECT text, context_header FROM chunks WHERE doc_id=?", (doc_id,)):
            terms.update(tokenize(f"{row['context_header']} {row['text']}", stem_words=True))
        out[doc_id] = terms
    return out


def features(results, reranker, query: str, *, store=None,
             unstemmed: set[str] | None = None) -> dict[str, float]:
    """Every candidate is computed from what retrieval already produced, so a
    winner costs no extra work at query time."""
    relevance = [r.components.get("rerank_relevance", 0.0) for r in results]
    scores = [r.score for r in results]
    best = max(relevance) if relevance else 0.0

    # How far the top result stands above the field. When the corpus holds the
    # answer one document should stand out; when it does not, several mediocre
    # documents tie.
    gap = (scores[0] - scores[1]) if len(scores) > 1 else 0.0
    spread = (scores[0] - statistics.fmean(scores)) if scores else 0.0

    # How specific the *matched* terms are. A question made entirely of ordinary
    # words ("what keeps two processes from writing the same file at once")
    # matches plenty of moderately-rare words and identifies nothing.
    query_set = reranker._query_set(tokenize(query, stem_words=True))
    top = results[0] if results else None
    matched_idf = 0.0
    if top is not None:
        chunk_terms = set(tokenize(top.chunk.indexed_text, stem_words=True))
        matched = query_set & chunk_terms
        matched_idf = max((reranker.idf(t) for t in matched), default=0.0)

    out = {
        "rerank_relevance (in use)": best,
        "top1 - top2 score": gap,
        "top1 - mean score": spread,
        "max idf of matched terms": matched_idf,
        "relevance x top-gap": best * (1.0 + gap),
        "relevance x matched idf": best * matched_idf,
    }

    if unstemmed is not None:
        # Share of the query's idf mass whose *surface form* the corpus holds.
        raw_terms = set(tokenize(query))
        total = sum(reranker.idf(t) for t in raw_terms) or 1.0
        known = sum(reranker.idf(t) for t in raw_terms if t in unstemmed)
        surface = known / total
        out["surface answerability"] = surface
        out["relevance x surface"] = best * surface

    if store is not None and results:
        by_doc = document_terms(store, [r.chunk.chunk_id for r in results])
        chunks = store.get_chunks([r.chunk.chunk_id for r in results])
        best_doc = 0.0
        for result in results:
            chunk = chunks.get(result.chunk.chunk_id)
            if chunk is None:
                continue
            terms = by_doc.get(chunk.doc_id, set())
            total = sum(reranker.idf(t) for t in query_set) or 1.0
            matched = sum(reranker.idf(t) for t in query_set & terms)
            best_doc = max(best_doc, matched / total)
        out["document coverage"] = best_doc
        # A document that covers the query while no chunk does is the tell for a
        # question the corpus discusses in pieces but does not answer.
        out["chunk minus document coverage"] = best - best_doc

    return out


def auc(positive: list[float], negative: list[float]) -> float:
    """Share of (answerable, unanswerable) pairs ordered correctly; ties count
    half, so a constant feature scores 0.5 rather than looking perfect."""
    if not positive or not negative:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in positive for n in negative)
    return wins / (len(positive) * len(negative))


def main() -> int:
    root, patterns, golden_path = CORPUS
    goldens = load_goldens(golden_path)
    workdir = tempfile.mkdtemp(prefix="gate-features-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key="fs:gf")])
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())

        unstemmed = unstemmed_vocabulary(store)
        print(f"\nunstemmed vocabulary: {len(unstemmed)} surface forms against "
              f"{len(retriever.reranker.vocabulary or ())} stems")

        collected: dict[str, tuple[list[float], list[float]]] = {}
        for case in goldens:
            results, _ = retriever.retrieve(case.question)
            for name, value in features(results, retriever.reranker, case.question,
                                        store=store, unstemmed=unstemmed).items():
                pos, neg = collected.setdefault(name, ([], []))
                (neg if case.expect_abstain else pos).append(value)

        answerable = len(next(iter(collected.values()))[0])
        unanswerable = len(next(iter(collected.values()))[1])
        print(f"\n{answerable} answerable, {unanswerable} unanswerable "
              f"({answerable * unanswerable} pairs)\n")
        print(f"| {'feature':<26} | AUC   | separable |")
        print("|----------------------------|-------|-----------|")
        for name, (pos, neg) in sorted(collected.items(),
                                       key=lambda kv: -auc(*kv[1])):
            print(f"| {name:<26} | {auc(pos, neg):.3f} "
                  f"| {str(min(pos) > max(neg)):<9} |")
        store.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
