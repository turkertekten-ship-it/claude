"""Does capping a query term's IDF weight recover the register-mismatch cases?

Mechanism, measured: IDF is rarity in *this corpus*. PyPI pages are written in
a different register from a question, so "let", "my", "cannot", "lose",
"reversed" are rare here and score above "hook", "password", "schema". IDF puts
a non-discriminating term first in 12 of 40 goldens, and two of those twelve are
external eval failures.

If that is the cause, clipping the weight should help: no single rare-in-corpus
word can then dominate a query, while the ordering among ordinary terms is kept.
Falsifiable - if pass rate does not move, clipping is not the fix.

**It did not move.** 48/54 flat from no cap down to 5.0, then worse: 47 at 4.0,
45 at 3.5. Clipping compresses magnitudes and leaves the *ordering* alone, and
the ordering is the defect - capping at 5.0 makes "revers" 5.0 against
"password" at 4.60, still the wrong way round. The diagnosis survives (see
scripts/idf_discrimination.py); this particular fix does not.
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

CEILINGS = [None, 6.0, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0]

work = tempfile.mkdtemp(prefix="idfcap-")
try:
    store = SqliteStore(f"{work}/index.db")
    pipeline = IndexPipeline(store)
    pipeline.run([FilesystemConnector("corpus/external/pypi",
                                      patterns=("**/*.md",), key="fs:ext")])
    cases = load_goldens("evals/goldens-external.jsonl")
    print("| idf ceiling | pass | recall@8 | MRR | nDCG@8 |")
    print("|-------------|------|----------|-----|--------|")
    for cap in CEILINGS:
        r = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
        if cap is not None:
            base = r.reranker.idf
            r.reranker.idf = (lambda t, _b=base, _c=cap: min(_b(t), _c))
        rep = EvalHarness(AnswerGenerator(r, AnswerConfig(generator="extractive")),
                          k=8).run(cases)
        a = rep.aggregate()
        print(f"| {str(cap):<11} | {rep.passed}/{len(rep.cases)} "
              f"| {a['recall@8']['mean']:.4f} | {a['mrr']['mean']:.4f} "
              f"| {a['ndcg@8']['mean']:.4f} |", flush=True)
    store.close()
finally:
    shutil.rmtree(work, ignore_errors=True)
