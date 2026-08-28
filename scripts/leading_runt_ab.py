"""Should a document's first chunk be merged forward when it is a runt?

`_merge_runt_pieces` folds an undersized piece into the piece *before* it, so
the first piece of a document has no neighbour to fold into. Measured on the
external corpus: 22 of 153 documents begin with a chunk under `min_tokens`, and
**every** runt in the corpus is one of those - the backward merge handles all
the rest.

They are two different things wearing the same size:

    black.md   4t  '[image: Black Logo]'
    mccabe.md 27t  'Ned's script to check McCabe complexity. This module
                    provides a plugin for flake8, the Python code checker.'

The first is badge noise that would pollute whatever it merged into. The second
is the most descriptive sentence on the page, stranded in a chunk with almost no
term statistics. Which effect dominates is not decidable by reading, so this
measures it: shipped (leading runt left alone) against a forward merge.
"""
import shutil, sqlite3, tempfile

from oodarag import chunking
from oodarag.chunking import ChunkConfig
from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.text import estimate_tokens

SHIPPED = chunking._merge_runt_pieces


def with_forward_merge(pieces, config):
    merged = SHIPPED(pieces, config)
    if (len(merged) > 1
            and estimate_tokens(merged[0][0]) < config.min_tokens
            and estimate_tokens(merged[0][0]) + estimate_tokens(merged[1][0])
            <= config.hard_max_tokens):
        text, start, meta = merged[0]
        follow_text, _follow_start, follow_meta = merged[1]
        merged[1] = (f"{text}\n\n{follow_text}", start,
                     chunking._merge_meta(meta, follow_meta))
        del merged[0]
    return merged


def measure(label: str) -> None:
    work = tempfile.mkdtemp(prefix="runt-")
    try:
        path = f"{work}/index.db"
        store = SqliteStore(path)
        pipeline = IndexPipeline(store, chunk_config=ChunkConfig())
        pipeline.run([FilesystemConnector("corpus/external/pypi",
                                          patterns=["**/*.md"], key="fs:x")])
        con = sqlite3.connect(path)
        sizes = [estimate_tokens(r[0]) for r in con.execute("select text from chunks")]
        con.close()
        runts = sum(1 for s in sizes if s < ChunkConfig().min_tokens)
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
        generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        cells = []
        for goldens in ("evals/goldens-external.jsonl", "evals/goldens-heldout.jsonl"):
            report = EvalHarness(generator, k=8).run(load_goldens(goldens))
            agg = report.aggregate()
            cells.append(f"{report.passed}/{len(report.cases)} | "
                         f"{agg['recall@8']['mean']:.4f} | {agg['mrr']['mean']:.4f} | "
                         f"{agg['ndcg@8']['mean']:.4f}")
        print(f"| {label} | {len(sizes)} | {runts} | {cells[0]} | {cells[1]} |", flush=True)
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    print("\n| variant | chunks | runts | gate | recall@8 | MRR | nDCG@8 "
          "| held | recall@8 | MRR | nDCG@8 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    measure("shipped (backward only)")
    chunking._merge_runt_pieces = with_forward_merge
    measure("+ forward merge")
