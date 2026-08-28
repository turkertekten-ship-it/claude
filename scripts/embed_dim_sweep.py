"""Does the dense arm's 768-dimension budget cost it anything?

`HashingEmbedder` projects a BM25-weighted sparse vector into `dim` buckets by
signed feature hashing. Its docstring says signed hashing makes collisions
"cancel in expectation instead of accumulating into a systematic bias" - true of
the expectation, and silent about the variance, which grows with load.

Measured before sweeping (L: look at the input): the external corpus has
**126,791 distinct features** - tokens plus character 4-grams - hashed into 768
buckets. That is **165 features per bucket**, with no bucket empty at any
dimension tried. Every coordinate of every document vector is a signed sum of
~165 unrelated features.

So the prediction is that raising `dim` should measurably help, and the sweep
exists to falsify it. If it does not, the finding is about the *pipeline* rather
than the embedder: the reranker's adjustment already outweighs the fused
retrieval score 34.5x (L58), so a better dense arm would have nowhere to show up.

    PYTHONPATH=src python3 scripts/embed_dim_sweep.py
"""
import shutil, tempfile, time

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.embedding.hashing import HashingEmbedder
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

DIMS = (256, 768, 1536, 3072, 6144)


def measure(dim: int) -> None:
    work = tempfile.mkdtemp(prefix=f"dim{dim}-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store, embedder=HashingEmbedder(dim=dim))
        started = time.monotonic()
        pipeline.run([FilesystemConnector("corpus/external/pypi",
                                          patterns=["**/*.md"], key="fs:x")])
        index_s = time.monotonic() - started
        # Assert the knob is actually wired through, rather than trusting that
        # passing it had an effect: a sweep of a parameter the pipeline quietly
        # replaced would produce a flat table that looks like a real finding.
        assert pipeline.embedder.dim == dim, pipeline.embedder.dim
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
        generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        cells = []
        for goldens in ("evals/goldens-external.jsonl", "evals/goldens-heldout.jsonl"):
            report = EvalHarness(generator, k=8).run(load_goldens(goldens))
            agg = report.aggregate()
            cells.append(f"{report.passed}/{len(report.cases)} | "
                         f"{agg['recall@8']['mean']:.4f} | {agg['mrr']['mean']:.4f} | "
                         f"{agg['ndcg@8']['mean']:.4f}")
        print(f"| {dim}{' *' if dim == 768 else ''} | {126791/dim:.0f} | "
              f"{index_s:.1f}s | {cells[0]} | {cells[1]} |", flush=True)
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    print("\n| dim | features/bucket | index | gate | recall@8 | MRR | nDCG@8 "
          "| held | recall@8 | MRR | nDCG@8 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for d in DIMS:
        measure(d)
