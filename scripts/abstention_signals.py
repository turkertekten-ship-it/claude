"""Is there a better abstention signal than the one the gate uses?

L77 established that the incumbent - `max rerank_relevance` - cannot separate
the three remaining failures at any threshold: the medians of the answerable and
abstainable classes separate, the tails overlap completely. That is a statement
about one signal, and the useful follow-up is whether any *other* quantity the
pipeline already computes does better.

Ranked by AUC, which is threshold-free: the probability that a randomly chosen
answerable question scores above a randomly chosen abstainable one. 0.5 is a
coin flip. This is the right tool for killing a candidate before building it
(L22), and the wrong tool for choosing between two survivors - AUC asks whether
pairs are ordered, the system is judged on whether a case crosses a floor.

Two candidates are already-paid-for dead ends and are here as controls, so a
suspiciously good number from a new signal can be read against a known-bad one:
term co-occurrence (L51, TPR-FPR 0.159, re-confirmed at 153 documents) and
`rerank_recency`, which L43 found saturated.

    PYTHONPATH=src python3 scripts/abstention_signals.py
"""
import shutil, statistics, tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

SETS = ("evals/goldens-external.jsonl", "evals/goldens-heldout.jsonl")


def component(results, key, reducer=max):
    values = [r.components.get(key, 0.0) for r in results]
    return reducer(values) if values else 0.0


def signals(results) -> dict[str, float]:
    """Every candidate, computed from one retrieval."""
    scores = [r.score for r in results]
    rel = [r.components.get("rerank_relevance", 0.0) for r in results]
    top = scores[0] if scores else 0.0
    second = scores[1] if len(scores) > 1 else 0.0
    return {
        "rerank_relevance (incumbent)": max(rel) if rel else 0.0,
        "top fused score": top,
        "absolute margin top-2": top - second,
        "relative margin (top-2)/top": (top - second) / top if top else 0.0,
        "mean relevance over 8": statistics.mean(rel) if rel else 0.0,
        "relevance of the top chunk": rel[0] if rel else 0.0,
        "answerability": component(results, "rerank_answerability"),
        "max coverage": component(results, "rerank_coverage"),
        "max phrase": component(results, "rerank_phrase"),
        "recency (known saturated)": component(results, "rerank_recency"),
    }


def auc(positive: list[float], negative: list[float]) -> float:
    wins = ties = 0
    for p in positive:
        for n in negative:
            if p > n:
                wins += 1
            elif p == n:
                ties += 1
    total = len(positive) * len(negative)
    return (wins + 0.5 * ties) / total if total else 0.5


def main() -> None:
    work = tempfile.mkdtemp(prefix="sig-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector("corpus/external/pypi",
                                          patterns=["**/*.md"], key="fs:x")])
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())

        answerable: dict[str, list[float]] = {}
        abstainable: dict[str, list[float]] = {}
        for path in SETS:
            for case in load_goldens(path):
                results, _ = retriever.retrieve(case.question)
                bucket = abstainable if case.expect_abstain else answerable
                for name, value in signals(results).items():
                    bucket.setdefault(name, []).append(value)

        n_pos = len(next(iter(answerable.values())))
        n_neg = len(next(iter(abstainable.values())))
        print(f"\n{n_pos} answerable, {n_neg} abstainable\n")
        print("| signal | AUC | answerable median | abstainable median |")
        print("|---|---|---|---|")
        rows = [(auc(answerable[k], abstainable[k]), k) for k in answerable]
        for score, name in sorted(rows, reverse=True):
            print(f"| {name} | {score:.3f} "
                  f"| {statistics.median(answerable[name]):.4f} "
                  f"| {statistics.median(abstainable[name]):.4f} |")
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
