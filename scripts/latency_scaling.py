#!/usr/bin/env python3
"""Where does query time go, and how does it scale with the corpus?

ADR 0002 chose exhaustive vector search and said it "stays sub-millisecond at
the tens of thousands of chunks a documentation corpus produces", with a revisit
trigger at ~10^6 chunks. Both numbers were estimates. This measures them, using
the per-stage timings the retrieval trace already carries.

    PYTHONPATH=src python3 scripts/latency_scaling.py

Measured on the pure-Python path (no numpy, which `ooda preflight` reports):
the dense scan is linear in chunk count at about 0.027 ms per chunk and every
other stage is flat, because every other stage is bounded by `candidate_k` or
`top_k` rather than by the corpus (L82).
"""

from __future__ import annotations

import pathlib
import shutil
import statistics
import sys
import tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

from _corpora import EXTERNAL  # noqa: E402

STAGES = ("dense_ms", "lexical_ms", "fusion_ms", "rerank_ms", "mmr_ms")
QUERIES = 24


def main() -> int:
    root, patterns, goldens = EXTERNAL
    pages = sorted(pathlib.Path(root).glob("*.md"))
    questions = [g.question for g in load_goldens(goldens)][:QUERIES]
    sizes = [n for n in (90, 175, 260, len(pages)) if n <= len(pages)]

    print(f"{'docs':>5} {'chunks':>7} | {'total':>7} {'dense':>7} {'lexical':>8} "
          f"{'fusion':>7} {'rerank':>7} {'mmr':>6} | {'us/chunk':>9}")
    for target in sizes:
        step = len(pages) / target
        keep = [pages[int(i * step)] for i in range(target)]
        work = tempfile.mkdtemp(prefix="latency-")
        try:
            staging = pathlib.Path(work) / "corpus"
            staging.mkdir()
            for page in keep:
                shutil.copy(page, staging / page.name)
            store = SqliteStore(f"{work}/index.db")
            pipeline = IndexPipeline(store)
            pipeline.run([FilesystemConnector(str(staging), patterns=patterns,
                                              key="fs:latency")])
            retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
            totals: list[float] = []
            stages: dict[str, list[float]] = {name: [] for name in STAGES}
            for question in questions:
                _, trace = retriever.retrieve(question, top_k=8)
                totals.append(trace.latency_ms)
                for name in STAGES:
                    stages[name].append(trace.stages.get(name, 0.0))
            stats = store.stats()
            dense = statistics.median(stages["dense_ms"])
            print(f"{stats['documents']:>5} {stats['chunks']:>7} | "
                  f"{statistics.median(totals):>7.1f} {dense:>7.1f} "
                  f"{statistics.median(stages['lexical_ms']):>8.1f} "
                  f"{statistics.median(stages['fusion_ms']):>7.2f} "
                  f"{statistics.median(stages['rerank_ms']):>7.1f} "
                  f"{statistics.median(stages['mmr_ms']):>6.1f} | "
                  f"{1000 * dense / max(1, stats['chunks']):>9.1f}")
            store.close()
        finally:
            shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
