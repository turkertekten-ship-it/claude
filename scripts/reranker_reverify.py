"""Do the reranker's documented optima survive today's chunking changes?

`coverage_power` and `position_weight` carry sweep tables measured before this
session split oversized units on line boundaries and merged leading runts
forward (1,810 chunks -> 1,802, and five chunks over the ceiling -> zero). The
rule those tables are held to is my own: a measurement justifying a default has
a shelf life, and three defaults in this project have already been found
measuring worse than their recorded table said.

The chunking change is small in count and structural in kind - it split the
largest chunks in the corpus, which is where coverage and position both behave
differently - so "few chunks moved" is not a reason to assume the optima did
not.

Both corpora, because the two have wanted opposite things four times now
(L58 base_weight, L75 MMR, the abstention floor, L80 expansion). A default is
shipped for both, so one corpus cannot move it alone.

Reports the shipped value against its documented neighbours. A moved optimum
means the docstrings are now wrong; an unmoved one is a robustness result and
worth recording as re-verified rather than assumed.

    PYTHONPATH=src python3 scripts/reranker_reverify.py [external|primary]
"""
import shutil, sys, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

SWEEPS = {
    "coverage_power": (2.0, (1.0, 1.5, 2.0, 2.5, 3.0)),
    "position_weight": (0.15, (0.0, 0.05, 0.15, 0.3, 0.5)),
}
CORPORA = (
    ("external", "corpus/external/pypi", ["**/*.md"],
     "evals/goldens-external.jsonl"),
    ("primary", ".", ["**/*.md", "src/**/*.py"], "evals/goldens.jsonl"),
)
HELDOUT = "evals/goldens-heldout.jsonl"


def main() -> None:
    only = sys.argv[1:]
    selected = [c for c in CORPORA if not only or c[0] in only]
    assert selected, f"no corpus matches {only}; known: {[c[0] for c in CORPORA]}"
    for name, root, patterns, goldens in selected:
        work = tempfile.mkdtemp(prefix="reverify-")
        try:
            store = SqliteStore(f"{work}/index.db")
            pipeline = IndexPipeline(store)
            pipeline.run([FilesystemConnector(root, patterns=patterns,
                                              key=f"fs:{name}")])
            cases = load_goldens(goldens)
            # The held-out set is written against the external corpus; running
            # it over the primary index would measure the wrong thing.
            held = load_goldens(HELDOUT) if name == "external" else None
            stats = store.stats()
            print(f"\n# {name}: {stats['documents']} documents, "
                  f"{stats['chunks']} chunks, {len(cases)} cases\n")

            for knob, (shipped, values) in SWEEPS.items():
                print(f"## {name} / {knob}\n")
                header = "| value | pass | recall@8 | MRR | nDCG@8 |"
                rule = "|---|---|---|---|---|"
                if held is not None:
                    header, rule = header + " held |", rule + "---|"
                print(header)
                print(rule)
                for value in values:
                    retriever = HybridRetriever(store, pipeline.embedder,
                                                RetrievalConfig())
                    setattr(retriever.reranker, knob, value)
                    # The knob must reach the reranker, not just a local name.
                    assert getattr(retriever.reranker, knob) == value
                    generator = AnswerGenerator(
                        retriever, AnswerConfig(generator="extractive"))
                    report = EvalHarness(generator, k=8).run(cases)
                    agg = report.aggregate()
                    star = " *" if value == shipped else ""
                    row = (f"| {value}{star} | {report.passed}/{len(report.cases)} "
                           f"| {agg['recall@8']['mean']:.4f} "
                           f"| {agg['mrr']['mean']:.4f} "
                           f"| {agg['ndcg@8']['mean']:.4f} |")
                    if held is not None:
                        h = EvalHarness(generator, k=8).run(held)
                        row += f" {h.passed}/{len(h.cases)} |"
                    print(row, flush=True)
                print()
            store.close()
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
