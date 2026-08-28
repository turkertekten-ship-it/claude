"""How much should the fused retrieval score count against the reranker?

Measured: over 432 results from the 54 golden queries, the RRF fused score has a
spread of 0.021 and the reranker's adjustment a spread of 0.720 - **34.5x**.
They are combined as `base_weight * fused + adjustment` with base_weight 1.0, so
the two retrieval arms decide roughly 3% of the ordering and act, in practice,
as a candidate generator for the heuristic reranker.

That is visible in the failures: the lexical arm ranks `structlog` 2nd and
`responses` 5th for their own questions, and neither survives to the output.

If the imbalance is the cause, raising base_weight toward ~34 should recover
them. Falsifiable: if nothing moves, the arms genuinely disagree with the
reranker and the reranker is right.

**The two corpora want opposite things.** External is best at base_weight 1
(49/54, falling to 43 at 35); primary is worst there (16/20, rising to 18 at 35
with recall 0.7812 -> 0.8750). The reranker dominating the ordering is correct
on the gate corpus and wrong on the other, so the shipped value is a compromise
that happens to favour the corpus the gate runs on. Nothing was changed. See
LEARNINGS L58.
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

WEIGHTS = [1, 2, 5, 10, 20, 35, 50, 80]
from _corpora import CORPORA as _CORPORA  # noqa: E402

CORPORA = [(name, root, list(patterns), goldens)
           for name, (root, patterns, goldens) in _CORPORA.items()]

for name, root, patterns, gpath in CORPORA:
    work = tempfile.mkdtemp(prefix=f"bw-{name}-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key=f"fs:{name}")])
        cases = load_goldens(gpath)
        print(f"\n## {name}: {store.stats()['documents']} documents, {len(cases)} cases\n")
        print("| base_weight | pass | recall@8 | MRR | nDCG@8 |")
        print("|---|---|---|---|---|")
        for w in WEIGHTS:
            r = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
            r.reranker.base_weight = float(w)
            rep = EvalHarness(AnswerGenerator(r, AnswerConfig(generator="extractive")),
                              k=8).run(cases)
            a = rep.aggregate()
            print(f"| {w:<11} | {rep.passed}/{len(rep.cases)} | {a['recall@8']['mean']:.4f} "
                  f"| {a['mrr']['mean']:.4f} | {a['ndcg@8']['mean']:.4f} |", flush=True)
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)
