"""What can the abstention floor actually buy, and at what price?

Three of the five remaining external gate failures are abstention failures, not
retrieval misses: the system answers an out-of-corpus question instead of
refusing. The obvious response is to raise `min_relevance` from 0.19. This
prints the whole trade-off instead of one point, because a floor is a threshold
on a feature and what matters is whether the two distributions separate at all.

Scored over every golden in both external sets, split by whether the case
expects an answer or an abstention, using the exact quantity the gate reads
(`max rerank_relevance` over the returned chunks).

**This is not the pass-rate curve, and must not be read as one.** It isolates
the floor's own decision - which side of answer/abstain each case lands on -
holding retrieval fixed. "Answers correctly" here means "cleared the floor",
which a case can do while still failing because the wrong document was
retrieved. The end-to-end sweep in `AnswerConfig.min_relevance` measures pass
rate and is the one the shipped value is chosen on; on its own terms it favours
0.19, and nothing here overrides it. Both are legitimate and they answer
different questions - the point of this one is what the floor *can* do, not what
value to ship.

    PYTHONPATH=src python3 scripts/abstention_floor_curve.py
"""
import shutil, statistics, tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

SETS = ("evals/goldens-external.jsonl", "evals/goldens-heldout.jsonl")
FLOORS = (0.0, 0.10, 0.19, 0.25, 0.30, 0.33, 0.40, 0.50, 0.73)


def main() -> None:
    work = tempfile.mkdtemp(prefix="floor-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector("corpus/external/pypi",
                                          patterns=["**/*.md"], key="fs:x")])
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())

        answerable, abstainable = [], []
        for path in SETS:
            for case in load_goldens(path):
                results, _ = retriever.retrieve(case.question)
                best = max((r.components.get("rerank_relevance", 0.0)
                            for r in results), default=0.0)
                (abstainable if case.expect_abstain else answerable).append(
                    (best, case.question))

        for label, rows in (("should answer", answerable),
                            ("should abstain", abstainable)):
            scores = sorted(s for s, _ in rows)
            print(f"\n{label}: {len(scores)} cases  "
                  f"min {scores[0]:.4f}  p25 {scores[len(scores)//4]:.4f}  "
                  f"median {statistics.median(scores):.4f}  "
                  f"p75 {scores[3*len(scores)//4]:.4f}  max {scores[-1]:.4f}")

        print("\n| floor | abstains caught | answers past the floor | sum |")
        print("(not pass rate - see the module docstring)")
        print("|---|---|---|---|")
        for floor in FLOORS:
            caught = sum(1 for s, _ in abstainable if s < floor)
            kept = sum(1 for s, _ in answerable if s >= floor)
            star = " *" if abs(floor - 0.19) < 1e-9 else ""
            print(f"| {floor:.2f}{star} | {caught}/{len(abstainable)} "
                  f"| {kept}/{len(answerable)} | {caught + kept} |")

        print("\nAbstain cases the shipped 0.19 floor lets through:")
        for score, question in sorted(abstainable, reverse=True):
            if score >= 0.19:
                print(f"  {score:.4f}  {question}")
        print("\nAnswerable cases already below the shipped floor:")
        for score, question in sorted(answerable):
            if score < 0.19:
                print(f"  {score:.4f}  {question}")
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
