"""Does decoupling the gate's coverage power from the ranker's buy anything?

Prediction to falsify: at ranking power 2.5 the sweep measured the best
recall@8 of the whole range (0.9419 vs 0.9186 at 1.0) and the worst-but-two
pass rate, because `relevance` - and so the abstention floor - is computed from
the same sharpened number. Holding the gate at 1.0 should keep the floor
calibrated while the ranking improves, so pass rate should be >= 48/54.

Confirmed: 49/54 at rank 2.5 / gate 1.0, and the recovery grows with the
sharpening (+1 at rank 2.0, +2 at 2.5, +3 at 3.0), which is the mechanism
rather than one lucky cell. The defaults did *not* change on the strength of
it - see the note on `HeuristicReranker.gate_coverage_power` for what sharpening
the ranker costs the primary corpus.
"""
import shutil, tempfile

from _corpora import EXTERNAL  # noqa: E402
from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

RANK = [1.0, 1.5, 2.0, 2.5, 3.0]
GATE = [None, 1.0, 1.5, 2.0]

workdir = tempfile.mkdtemp(prefix="gatepower-")
try:
    store = SqliteStore(f"{workdir}/index.db")
    pipeline = IndexPipeline(store)
    root, patterns, _ = EXTERNAL
    pipeline.run([FilesystemConnector(root, patterns=patterns, key="fs:external")])
    cases = load_goldens("evals/goldens-external.jsonl")
    print("| rank power | gate power | pass | recall@8 | MRR | nDCG@8 |")
    print("|------------|------------|------|----------|-----|--------|")
    for rp in RANK:
        for gp in GATE:
            retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
            retriever.reranker.coverage_power = rp
            retriever.reranker.gate_coverage_power = gp
            report = EvalHarness(
                AnswerGenerator(retriever, AnswerConfig(generator="extractive")),
                k=8).run(cases)
            agg = report.aggregate()
            print(f"| {rp:<10} | {str(gp):<10} | {report.passed}/{len(report.cases)} "
                  f"| {agg['recall@8']['mean']:.4f} | {agg['mrr']['mean']:.4f} "
                  f"| {agg['ndcg@8']['mean']:.4f} |", flush=True)
    store.close()
finally:
    shutil.rmtree(workdir, ignore_errors=True)
