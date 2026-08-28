"""Does dropping the phrase term from the abstention gate pay end to end?

`scripts/gate_split_sweep.py` finds the gate's coverage/phrase split is monotone
in coverage and flat from 0.8 up: `gate_phrase_weight` 0.0 scores AUC 0.851
against the shipped 0.4's 0.845, so the phrase term buys the gate nothing by
that measure.

L78 is the reason this script exists rather than a patch. There, a signal that
won on AUC by 0.018 lost end to end by three cases - in this same gate, where
L22 had earlier found a 0.010 AUC gain worth three cases. AUC has now pointed
the wrong way once and the right way once, so it decides nothing on its own.

Prediction, stated first: given both distributions shift upward when the phrase
term goes (abstainable median 0.0901 -> 0.1400), each weight needs its own floor
and I expect the two to come out close. A clear win would be a surprise.

    PYTHONPATH=src python3 scripts/gate_phrase_ab.py
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

WEIGHTS = (0.4, 0.0)
FLOORS = (0.15, 0.19, 0.22, 0.25, 0.28, 0.32)
CORPORA = [
    ("external", "corpus/external/pypi", ["**/*.md"], "evals/goldens-external.jsonl"),
    ("primary", ".", ["**/*.md", "src/**/*.py"], "evals/goldens.jsonl"),
]
HELDOUT = "evals/goldens-heldout.jsonl"


def main() -> None:
    for name, root, patterns, goldens in CORPORA:
        work = tempfile.mkdtemp(prefix=f"gp-{name}-")
        try:
            store = SqliteStore(f"{work}/index.db")
            pipeline = IndexPipeline(store)
            pipeline.run([FilesystemConnector(root, patterns=patterns, key=f"fs:{name}")])
            cases = load_goldens(goldens)
            negatives = {g.question for g in cases if g.expect_abstain}
            held = load_goldens(HELDOUT) if name == "external" else None
            print(f"\n## {name}: {len(cases)} cases\n")
            print("| gate_phrase_weight | floor | pass | over-answered | over-refused |"
                  + (" held |" if held else ""))
            print("|---|---|---|---|---|" + ("---|" if held else ""))
            for weight in WEIGHTS:
                retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
                retriever.reranker.gate_phrase_weight = weight
                # The knob must reach the reranker, not just the local name.
                assert retriever.reranker.gate_phrase_weight == weight
                for floor in FLOORS:
                    generator = AnswerGenerator(
                        retriever, AnswerConfig(generator="extractive",
                                                min_relevance=floor))
                    report = EvalHarness(generator, k=8).run(cases)
                    over_answered = sum(1 for c in report.cases
                                        if c.question in negatives and not c.passed)
                    over_refused = sum(1 for c in report.cases
                                       if c.question not in negatives
                                       and not c.passed and c.abstained)
                    star = " *" if weight == 0.4 and floor == 0.19 else ""
                    row = (f"| {weight:.1f} | {floor:.2f}{star} "
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
