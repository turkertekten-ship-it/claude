#!/usr/bin/env python3
"""Sweep the offline embedder's dimension - the other never-measured default.

L63 swept the chunker because it was the most upstream number nobody had
measured. `dim` is the next one: 768 buckets have carried every embedding this
project has ever produced, and the load factor says what that means -

    external corpus   129,072 distinct features -> 168 per bucket
    primary corpus     85,112 distinct features -> 111 per bucket

Signed hashing makes collisions cancel *in expectation*; it does not make them
free. Whether 768 is enough is an empirical question about this corpus, and the
dense arm is the weakest of the three in the ablation, which is what a noisy
vector space would look like.

    PYTHONPATH=src python3 scripts/embedder_sweep.py --values 256 768 3072
    PYTHONPATH=src python3 scripts/embedder_sweep.py --values 768 --no-ngrams

Cost is reported next to quality: dimension is bytes on disk and pure-python
multiply-adds per candidate, so a quality tie at 4x the width is a loss.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile

from oodarag.embedding.hashing import HashingEmbedder
from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

CORPORA = {
    "external": ("corpus/external/pypi", ("**/*.md",), "evals/goldens-external.jsonl"),
    "primary": (".", ("src/**/*.py", "tests/**/*.py", "docs/**/*.md",
                      "internal/**/*.md", "*.md", "corpus/reference/**/*.md"),
                "evals/goldens.jsonl"),
}


def measure(store, embedder, cases, config: RetrievalConfig):
    retriever = HybridRetriever(store, embedder, config)
    generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
    report = EvalHarness(generator, k=8).run(cases)
    agg = report.aggregate()
    return {"passed": report.passed, "total": len(report.cases),
            "recall": agg["recall@8"]["mean"], "ndcg": agg["ndcg@8"]["mean"],
            "mrr": agg["mrr"]["mean"], "latency": agg["latency_ms"]["mean"]}


def run_one(root, patterns, goldens, dim: int, use_ngrams: bool):
    workdir = tempfile.mkdtemp(prefix="embsweep-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        embedder = HashingEmbedder(dim=dim, use_ngrams=use_ngrams)
        pipeline = IndexPipeline(store, embedder=embedder)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key="fs:sweep")])
        cases = load_goldens(goldens)
        hybrid = measure(store, pipeline.embedder, cases, RetrievalConfig())
        # The arm the dimension actually changes. Hybrid can hide a worse dense
        # arm behind the lexical one, so both are reported.
        dense = measure(store, pipeline.embedder, cases,
                        RetrievalConfig(lexical_weight=0.0))
        size = store.stats().get("size_bytes", 0)
        store.close()
        return hybrid, dense, size
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--values", nargs="+", type=int, default=[256, 512, 768, 1536, 3072])
    parser.add_argument("--no-ngrams", action="store_true",
                        help="ablate character n-grams, which are 88% of the features")
    parser.add_argument("--corpus", choices=(*CORPORA, "both"), default="both")
    args = parser.parse_args()

    names = list(CORPORA) if args.corpus == "both" else [args.corpus]
    print(f"\n## HashingEmbedder.dim"
          f"{' (no n-grams)' if args.no_ngrams else ''}\n")
    for name in names:
        print(f"### {name}\n")
        print("| dim | hybrid | recall@8 | nDCG@8 | dense only | recall@8 | nDCG@8 "
              "| ms/query | index MB |")
        print("|-----|--------|----------|--------|------------|----------|--------"
              "|----------|----------|")
        for dim in args.values:
            h, d, size = run_one(*CORPORA[name], dim, not args.no_ngrams)
            print(f"| {dim:<3} | {h['passed']}/{h['total']}  | {h['recall']:.4f}   "
                  f"| {h['ndcg']:.4f} | {d['passed']}/{d['total']}      "
                  f"| {d['recall']:.4f}   | {d['ndcg']:.4f} | {h['latency']:>8.1f} "
                  f"| {size/1e6:>8.1f} |")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
