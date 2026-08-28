"""Do the two chunk-size parameters change what retrieval sees?

Six retrieval parameters were tuned in this project before anything upstream of
them was examined. Chunking decides what retrieval is choosing *between*, so a
retrieval parameter tuned over one chunking is fitted to it.

Measured first, before sweeping anything (L: look at the input): the shipped
`target_tokens` is 320, and the median chunk is **109** estimated tokens on the
external corpus, 136 on the primary one. p90 is 314. Only 9% of chunks reach
the target at all.

The cause is in `_split_prose`: a section at or under `hard_max_tokens` is
emitted **whole**, and only a section above it is packed to `target_tokens`.
On the external corpus that is 31 sections out of 2,486 - **target_tokens has
any say over 1.2% of them**. So the prediction this script exists to falsify is
that sweeping target measures flat, and that `hard_max` is the parameter
actually shaping the corpus.

Run:
    PYTHONPATH=src python3 scripts/chunk_size_sweep.py
"""
import shutil, sqlite3, tempfile

from oodarag.chunking import ChunkConfig
from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.text import estimate_tokens

CORPUS = ("corpus/external/pypi", ["**/*.md"])
GOLDENS = "evals/goldens-external.jsonl"
HELDOUT = "evals/goldens-heldout.jsonl"


def measure(config: ChunkConfig) -> dict:
    work = tempfile.mkdtemp(prefix="chunk-")
    try:
        path = f"{work}/index.db"
        store = SqliteStore(path)
        pipeline = IndexPipeline(store, chunk_config=config)
        pipeline.run([FilesystemConnector(CORPUS[0], patterns=CORPUS[1], key="fs:x")])
        con = sqlite3.connect(path)
        sizes = sorted(estimate_tokens(r[0]) for r in con.execute("select text from chunks"))
        con.close()
        out = {"chunks": len(sizes), "median": sizes[len(sizes) // 2]}
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
        generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        for label, goldens in (("gate", GOLDENS), ("held", HELDOUT)):
            cases = load_goldens(goldens)
            report = EvalHarness(generator, k=8).run(cases)
            agg = report.aggregate()
            out[label] = (report.passed, len(report.cases),
                          agg["recall@8"]["mean"], agg["mrr"]["mean"], agg["ndcg@8"]["mean"])
        store.close()
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)


def table(title: str, rows: list[tuple[str, dict]]) -> None:
    print(f"\n## {title}\n")
    print("| value | chunks | median | gate pass | recall@8 | MRR | nDCG@8 | held pass |")
    print("|---|---|---|---|---|---|---|---|")
    for label, m in rows:
        gp, gn, rec, mrr, ndcg = m["gate"]
        hp, hn, *_ = m["held"]
        print(f"| {label} | {m['chunks']} | {m['median']} | {gp}/{gn} | {rec:.4f} "
              f"| {mrr:.4f} | {ndcg:.4f} | {hp}/{hn} |", flush=True)


SWEEPS = {
    "target": ("target_tokens (hard_max fixed at 640)", 320,
               (96, 160, 224, 320, 448, 640),
               lambda v: ChunkConfig(target_tokens=v)),
    "hard-max": ("hard_max_tokens (target fixed at 320)", 640,
                 (160, 224, 320, 448, 640, 960),
                 lambda v: ChunkConfig(hard_max_tokens=v)),
    "overlap": ("overlap_tokens (target 320, hard_max 640)", 64,
                (0, 16, 32, 64, 96, 128),
                lambda v: ChunkConfig(overlap_tokens=v)),
}

if __name__ == "__main__":
    import sys

    wanted = sys.argv[1:] or list(SWEEPS)
    for key in wanted:
        title, shipped, values, build = SWEEPS[key]
        table(title, [(f"{v}{' *' if v == shipped else ''}", measure(build(v)))
                      for v in values])
