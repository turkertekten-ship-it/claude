"""What is the RRF constant worth, and has anyone checked?

Reciprocal Rank Fusion scores a document at rank r as 1/(rrf_k + r), summed over
the arms. `rrf_k` is 60 here, which is the value from the original RRF paper and
has never been measured on this project's corpora - it is inherited, not chosen.

What it controls is how sharply rank 1 is preferred over rank 10. At rrf_k = 60
the ratio 1/(60+1) : 1/(60+10) is 1.15 - nearly flat, so fusion is close to
"appear in both arms" voting. At rrf_k = 5 it is 2.5, so a top-ranked hit in one
arm can outweigh mid-ranked agreement in both.

The relevant prior is L58: the reranker's adjustment already outweighs the fused
score by 34.5x, so this may well measure flat for the same reason
`base_weight` did - fusion is largely a candidate generator here. If so, that is
worth recording as another measurement of how little the arms decide, rather
than as a null result about RRF.

    PYTHONPATH=src python3 scripts/rrf_k_sweep.py
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

VALUES = (1, 5, 20, 60, 200)
CORPORA = [
    ("external", "corpus/external/pypi", ["**/*.md"], "evals/goldens-external.jsonl"),
    ("primary", ".", ["**/*.md", "src/**/*.py"], "evals/goldens.jsonl"),
]
HELDOUT = "evals/goldens-heldout.jsonl"


def main() -> None:
    for name, root, patterns, goldens in CORPORA:
        work = tempfile.mkdtemp(prefix=f"rrf-{name}-")
        try:
            store = SqliteStore(f"{work}/index.db")
            pipeline = IndexPipeline(store)
            pipeline.run([FilesystemConnector(root, patterns=patterns, key=f"fs:{name}")])
            cases = load_goldens(goldens)
            held = load_goldens(HELDOUT) if name == "external" else None
            print(f"\n## {name}: {store.stats()['documents']} documents, "
                  f"{len(cases)} cases\n")
            print("| rrf_k | pass | recall@8 | MRR | nDCG@8 |"
                  + (" held |" if held else ""))
            print("|---|---|---|---|---|" + ("---|" if held else ""))
            for value in VALUES:
                config = RetrievalConfig(rrf_k=value)
                retriever = HybridRetriever(store, pipeline.embedder, config)
                # The knob must reach fusion, not merely the dataclass (L70).
                assert retriever.config.rrf_k == value
                generator = AnswerGenerator(retriever,
                                            AnswerConfig(generator="extractive"))
                report = EvalHarness(generator, k=8).run(cases)
                agg = report.aggregate()
                row = (f"| {value}{' *' if value == 60 else ''} "
                       f"| {report.passed}/{len(report.cases)} "
                       f"| {agg['recall@8']['mean']:.4f} | {agg['mrr']['mean']:.4f} "
                       f"| {agg['ndcg@8']['mean']:.4f} |")
                if held:
                    h = EvalHarness(generator, k=8).run(held)
                    row += f" {h.passed}/{len(h.cases)} |"
                print(row, flush=True)
            store.close()
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
