"""Can a conjunction-aware signal separate answerable from abstainable?

L91 established that the shipped gate signal cannot: 55 of 61 answerable cases
score at or below the highest abstainable one, and the best floor anywhere on
the range makes the same eight errors the shipped floor makes. So the feature
has to change, and the mechanism L91 named is the place to change it - coverage
is a weighted *average* over query terms, which a multi-clause question
satisfies on its common clause alone. "Renders Jinja templates to PDF" scores
0.59 against a corpus holding Jinja and no PDF renderer.

Not the same idea as `cooccurrence_probe.py`, which asked whether the query's
rare terms appear together in one *document* anywhere in the corpus and was
rejected (L51). This asks whether the *chunk the gate is about to answer from*
contains the query's most discriminating terms. Corpus-level co-occurrence says
"someone somewhere wrote both words"; this says "the passage I am citing has
both".

Candidates, all computed from the top-ranked chunk unless noted:

  relevance         the shipped signal, as the baseline to beat
  gate_coverage     its coverage half, unmultiplied by answerability
  answerability     corpus-level: share of query idf mass the corpus holds
  topN_present      share of the N most informative query terms in the chunk,
                    for N in 1..3
  weakest_term      the *minimum* idf-weighted presence over query terms
                    rather than the mean - a conjunction, softened
  relevance_x_top2  the shipped signal gated by the top-2 conjunction

Determinism matters here and has bitten before: `max(query_set, key=idf)` picks
an arbitrary element when idf ties, and Python randomises string hashing per
process, so the same question abstained or answered depending on the run (see
`_answerability`'s docstring). Every ordering below breaks ties on the term
string.

AUC kills candidates; it does not choose between survivors (L78). Anything that
survives here needs the end-to-end sweep before it means anything.

    PYTHONPATH=src python3 scripts/gate_conjunction.py
"""
import shutil, tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.text import tokenize

SETS = ("evals/goldens-external.jsonl", "evals/goldens-heldout.jsonl")


def auc(positive: list[float], negative: list[float]) -> float:
    wins = ties = 0
    for p in positive:
        for n in negative:
            if p > n:
                wins += 1
            elif p == n:
                ties += 1
    return (wins + 0.5 * ties) / (len(positive) * len(negative))


def best_floor(positive: list[float], negative: list[float]) -> tuple[float, int]:
    """The floor minimising total errors, and how many it makes.

    Answerable below the floor is a lost answer; abstainable at or above it is
    a false answer. Ties in error count go to the lower floor, which is the
    conservative choice for recall.
    """
    best = (0.0, len(positive) + len(negative))
    for cut in sorted({*positive, *negative}):
        wrong = sum(1 for v in positive if v < cut) + sum(1 for v in negative if v >= cut)
        if wrong < best[1]:
            best = (cut, wrong)
    return best


def main() -> None:
    work = tempfile.mkdtemp(prefix="conj-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector("corpus/external/pypi",
                                          patterns=["**/*.md"], key="fs:x")])
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
        retriever._refresh_analysis()
        idf = retriever.reranker.idf
        assert idf is not None, "no corpus statistics; every signal would be a constant"

        signals: dict[str, tuple[list[float], list[float]]] = {}

        def record(name: str, value: float, abstainable: bool) -> None:
            pos, neg = signals.setdefault(name, ([], []))
            (neg if abstainable else pos).append(value)

        for path in SETS:
            for case in load_goldens(path):
                hits, _ = retriever.retrieve(case.question)
                if not hits:
                    continue
                top = hits[0]
                chunk_terms = set(tokenize(top.chunk.indexed_text, stem_words=True))
                # Deterministic: sort by descending idf, then by the term itself.
                query_terms = list(dict.fromkeys(tokenize(case.question, stem_words=True)))
                ranked = sorted(query_terms, key=lambda t: (-idf(t), t))
                a = case.expect_abstain

                for name, key in (("relevance", "rerank_relevance"),
                                  ("gate_coverage", "rerank_gate_coverage"),
                                  ("answerability", "rerank_answerability")):
                    record(name, top.components.get(key, 0.0), a)

                for n in (1, 2, 3):
                    head = ranked[:n]
                    value = (sum(1.0 for t in head if t in chunk_terms) / len(head)
                             if head else 1.0)
                    record(f"top{n}_present", value, a)
                    if n == 2:
                        top2 = value

                # The conjunction, softened: the least-covered query term rather
                # than the average over them. Weighted so a common term missing
                # costs less than a rare one.
                if ranked:
                    total = sum(idf(t) for t in ranked)
                    weakest = min(
                        (idf(t) if t in chunk_terms else 0.0) / (idf(t) or 1.0)
                        for t in ranked) if total else 1.0
                else:
                    weakest = 1.0
                record("weakest_term", weakest, a)
                record("relevance_x_top2",
                       top.components.get("rerank_relevance", 0.0) * top2, a)

        pos_n = len(next(iter(signals.values()))[0])
        neg_n = len(next(iter(signals.values()))[1])
        print(f"\n{pos_n} answerable, {neg_n} abstainable\n")
        print("| signal | AUC | best floor | errors at it | shipped-signal errors |")
        print("|---|---|---|---|---|")
        baseline = best_floor(*signals["relevance"])[1]
        for name, (pos, neg) in signals.items():
            cut, wrong = best_floor(pos, neg)
            print(f"| {name} | {auc(pos, neg):.4f} | {cut:.4f} | {wrong} | {baseline} |")
        print()
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
