"""max or mean relevance for the abstention floor, measured end to end.

`scripts/abstention_signals.py` ranks mean above max by AUC, 0.863 to 0.845.
AUC asks whether pairs are ordered; the system is judged on whether a case
crosses a floor, and those come apart (L22). So this sweeps each statistic's own
floor end to end and compares the best of each, on the pass rate the gates read.

The two statistics are on different scales - answerable medians 0.4542 for max
and 0.2579 for mean - so comparing them at one floor would be meaningless. Each
gets its own sweep and is judged at its own best.

    PYTHONPATH=src python3 scripts/relevance_statistic_ab.py
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

FLOORS = {
    "max": (0.10, 0.15, 0.19, 0.22, 0.25, 0.30),
    "mean": (0.03, 0.05, 0.07, 0.09, 0.11, 0.14, 0.18),
}
CORPORA = [
    ("external", "corpus/external/pypi", ["**/*.md"], "evals/goldens-external.jsonl"),
    ("primary", ".", ["**/*.md", "src/**/*.py"], "evals/goldens.jsonl"),
]
HELDOUT = "evals/goldens-heldout.jsonl"


def main() -> None:
    for name, root, patterns, goldens in CORPORA:
        work = tempfile.mkdtemp(prefix=f"stat-{name}-")
        try:
            store = SqliteStore(f"{work}/index.db")
            pipeline = IndexPipeline(store)
            pipeline.run([FilesystemConnector(root, patterns=patterns, key=f"fs:{name}")])
            retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
            cases = load_goldens(goldens)
            negatives = {g.question for g in cases if g.expect_abstain}
            held = load_goldens(HELDOUT) if name == "external" else None
            print(f"\n## {name}: {len(cases)} cases\n")
            print("| statistic | floor | pass | over-answered | over-refused |"
                  + (" held |" if held else ""))
            print("|---|---|---|---|---|" + ("---|" if held else ""))
            for statistic, floors in FLOORS.items():
                for floor in floors:
                    config = AnswerConfig(generator="extractive",
                                          relevance_statistic=statistic,
                                          min_relevance=floor)
                    generator = AnswerGenerator(retriever, config)
                    report = EvalHarness(generator, k=8).run(cases)
                    # Classify the failures rather than only counting them: a
                    # floor trades one kind for the other, and a single pass
                    # number hides which way it moved.
                    over_answered = sum(
                        1 for c in report.cases
                        if c.question in negatives and not c.passed)
                    over_refused = sum(
                        1 for c in report.cases
                        if c.question not in negatives and not c.passed
                        and c.abstained)
                    row = (f"| {statistic} | {floor:.2f} "
                           f"| {report.passed}/{len(report.cases)} "
                           f"| {over_answered} | {over_refused} |")
                    if held:
                        h = EvalHarness(generator, k=8).run(held)
                        row += f" {h.passed}/{len(h.cases)} |"
                    print(row, flush=True)
            store.close()
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
