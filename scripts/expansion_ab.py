"""Re-run the query-expansion A/B on the corpus and golden set as they are now.

`retrieve/expansion.py` is off by default on the strength of a measurement whose
table reads "external 20/20". The external set has held 54 cases for some time
and the corpus is now 153 documents, so that conclusion was drawn against a
corpus roughly a third the size and a golden set a third the length. L49's rule
is to re-run the command rather than read the table.

It also matters more now than it did then: L51 concluded that the remaining
failures need meaning rather than term statistics, and pseudo-relevance feedback
is the one source of corpus-derived meaning already in the tree.
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

ARMS = [
    ("off", dict(use_expansion=False)),
    ("on, 8 terms, w=0.5", dict(use_expansion=True, expansion_terms=8, expansion_weight=0.5)),
    ("on, 4 terms, w=0.5", dict(use_expansion=True, expansion_terms=4, expansion_weight=0.5)),
    ("on, 8 terms, w=0.25", dict(use_expansion=True, expansion_terms=8, expansion_weight=0.25)),
    ("on, 12 terms, w=0.5", dict(use_expansion=True, expansion_terms=12, expansion_weight=0.5)),
]

from _corpora import CORPORA as _CORPORA  # noqa: E402

CORPORA = [
    ("external", *_CORPORA["external"]),
    ("primary", *_CORPORA["primary"]),
]

for name, root, patterns, goldens_path in CORPORA:
    work = tempfile.mkdtemp(prefix=f"exp-{name}-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=list(patterns), key=f"fs:{name}")])
        cases = load_goldens(goldens_path)
        print(f"\n## {name}: {store.stats()['documents']} documents, {len(cases)} cases\n")
        print("| expansion | pass | recall@8 | MRR | nDCG@8 |")
        print("|---|---|---|---|---|")
        for label, overrides in ARMS:
            r = HybridRetriever(store, pipeline.embedder, RetrievalConfig(**overrides))
            rep = EvalHarness(AnswerGenerator(r, AnswerConfig(generator="extractive")),
                              k=8).run(cases)
            a = rep.aggregate()
            print(f"| {label:<19} | {rep.passed}/{len(rep.cases)} | {a['recall@8']['mean']:.4f} "
                  f"| {a['mrr']['mean']:.4f} | {a['ndcg@8']['mean']:.4f} |", flush=True)
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)
