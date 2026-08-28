#!/usr/bin/env python3
"""How well does the abstention gate separate answerable from unanswerable?

Pass/fail at a fixed floor says only which side of 0.15 each case landed on.
This reports the distributions either side of the decision, so a change can be
judged on the margin it opens rather than on two cases flipping.

    PYTHONPATH=src python3 scripts/gate_margin.py [--power 1.0 2.0 3.0]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

CORPUS = ("corpus/external/pypi", ("**/*.md",), "evals/goldens-external.jsonl")


def relevances(store, embedder, goldens, power: float):
    config = RetrievalConfig()
    retriever = HybridRetriever(store, embedder, config)
    retriever.reranker.coverage_power = power
    answerable, unanswerable = [], []
    for case in goldens:
        results, _ = retriever.retrieve(case.question)
        best = max((r.components.get("rerank_relevance", 0.0) for r in results),
                   default=0.0)
        (unanswerable if case.expect_abstain else answerable).append((best, case.question))
    return answerable, unanswerable


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--power", type=float, nargs="+", default=[1.0, 1.5, 2.0, 3.0])
    parser.add_argument("--floor", type=float, default=0.15)
    args = parser.parse_args()

    root, patterns, golden_path = CORPUS
    goldens = load_goldens(golden_path)
    workdir = tempfile.mkdtemp(prefix="gate-margin-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key="fs:margin")])

        print(f"\n{len(goldens)} cases, floor {args.floor}\n")
        header = (f"| {'power':<6} | {'answerable min':<14} | {'unanswerable max':<16} "
                  f"| {'margin':<7} | separable | at floor |")
        print(header)
        print("|--------|----------------|------------------|---------|-----------|----------|")
        detail = {}
        for power in args.power:
            yes, no = relevances(store, pipeline.embedder, goldens, power)
            lo = min(v for v, _ in yes)
            hi = max(v for v, _ in no)
            # A gate is separable when some threshold classifies every case.
            separable = lo > hi
            wrong = sum(1 for v, _ in yes if v < args.floor)
            wrong += sum(1 for v, _ in no if v >= args.floor)
            print(f"| {power:<6} | {lo:<14.4f} | {hi:<16.4f} | {lo - hi:<+7.4f} "
                  f"| {str(separable):<9} | {wrong:<8} |")
            detail[power] = (yes, no)

        for power in args.power:
            yes, no = detail[power]
            print(f"\n### power {power} - the cases nearest the decision")
            for value, question in sorted(no, reverse=True)[:3]:
                print(f"  unanswerable {value:.4f}  {question}")
            for value, question in sorted(yes)[:3]:
                print(f"  answerable   {value:.4f}  {question}")
        store.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
