"""The 0.6/0.4 inside the abstention gate's relevance, which nobody has swept.

    relevance = (0.6 * gate_coverage + 0.4 * phrase) * answerability

That split is a hardcoded constant, not even a config field, and it sits inside
the one feature L77 identified as the bottleneck: the gate is a feature problem,
and this is the feature's only free parameter.

Sweepable from a single retrieval pass, because relevance feeds *only* the gate
and never the ordering ("Ordering uses the total; the abstention gate uses
`rerank_relevance` alone"). So the retrieved set is identical for every split
and each candidate is arithmetic on components already recorded - which is why
`rerank_gate_coverage` is now among them.

Prediction, stated before the sweep: coverage alone scores 0.805 by AUC and
phrase alone 0.707, while their 0.6/0.4 mix scores 0.845. Beating both means
they carry different information, so the optimum should be interior rather than
at an endpoint. If w=1.0 wins, the phrase term is dead weight in the gate.

AUC kills candidates; it does not choose between survivors (L78, emphatically).
Anything promising here needs the end-to-end sweep before it means anything.

    PYTHONPATH=src python3 scripts/gate_split_sweep.py
"""
import shutil, statistics, tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

SETS = ("evals/goldens-external.jsonl", "evals/goldens-heldout.jsonl")
WEIGHTS = (0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0)


def auc(positive: list[float], negative: list[float]) -> float:
    wins = ties = 0
    for p in positive:
        for n in negative:
            if p > n:
                wins += 1
            elif p == n:
                ties += 1
    return (wins + 0.5 * ties) / (len(positive) * len(negative))


def main() -> None:
    work = tempfile.mkdtemp(prefix="split-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector("corpus/external/pypi",
                                          patterns=["**/*.md"], key="fs:x")])
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())

        # One pass. Each case keeps the per-chunk triples the formula needs.
        cases: list[tuple[bool, list[tuple[float, float, float]]]] = []
        for path in SETS:
            for case in load_goldens(path):
                results, _ = retriever.retrieve(case.question)
                triples = [(r.components.get("rerank_gate_coverage", 0.0),
                            r.components.get("rerank_phrase", 0.0),
                            r.components.get("rerank_answerability", 0.0))
                           for r in results]
                cases.append((case.expect_abstain, triples))

        # The reconstruction must reproduce the shipped number exactly, or the
        # whole sweep is arithmetic on the wrong quantity (L70's shape).
        shipped = [(0.6 * c + 0.4 * p) * a
                   for _, triples in cases for c, p, a in triples]
        assert shipped, "no results retrieved"

        print(f"\n{sum(1 for a, _ in cases if not a)} answerable, "
              f"{sum(1 for a, _ in cases if a)} abstainable\n")
        print("| coverage weight | phrase weight | AUC | answerable median "
              "| abstainable median |")
        print("|---|---|---|---|---|")
        for w in WEIGHTS:
            pos, neg = [], []
            for expect_abstain, triples in cases:
                values = [(w * c + (1 - w) * p) * a for c, p, a in triples]
                (neg if expect_abstain else pos).append(max(values) if values else 0.0)
            star = " *" if abs(w - 0.6) < 1e-9 else ""
            print(f"| {w:.1f}{star} | {1 - w:.1f} | {auc(pos, neg):.3f} "
                  f"| {statistics.median(pos):.4f} | {statistics.median(neg):.4f} |")
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
