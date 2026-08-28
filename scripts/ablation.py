#!/usr/bin/env python3
"""Measure what each retrieval arm contributes.

ADR 0004 argues for hybrid retrieval on the grounds that dense and lexical
retrieval fail in uncorrelated ways. That was an argument, not a measurement.
This runs the golden sets with each arm disabled in turn, so the claim is a
table rather than a belief.

    PYTHONPATH=src python3 scripts/ablation.py

Add --corpus to point at a different filesystem tree and golden set.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

CORPORA = {
    "external": (
        "corpus/external/pypi",
        ("**/*.md",),
        "evals/goldens-external.jsonl",
    ),
    "primary": (
        ".",
        ("src/**/*.py", "tests/**/*.py", "docs/**/*.md", "internal/**/*.md",
         "*.md", "corpus/reference/**/*.md"),
        "evals/goldens.jsonl",
    ),
}

ARMS = {
    "hybrid": {},
    "lexical only": {"dense_weight": 0.0},
    "dense only": {"lexical_weight": 0.0},
    "no rerank": {"use_rerank": False},
    "no mmr": {"use_mmr": False},
}


def run(name: str, root: str, patterns: tuple[str, ...], goldens: str) -> None:
    workdir = tempfile.mkdtemp(prefix=f"ablation-{name}-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key=f"fs:{name}")])
        stats = store.stats()
        print(f"\n## {name}: {stats['documents']} documents, {stats['chunks']} chunks\n")
        print(f"| {'configuration':<14} | pass | recall@8 | prec@8 | MRR | nDCG@8 |")
        print(f"|{'-' * 16}|------|----------|--------|-----|--------|")
        cases = load_goldens(goldens)
        for label, overrides in ARMS.items():
            retriever = HybridRetriever(store, pipeline.embedder,
                                        RetrievalConfig(**overrides))
            generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
            report = EvalHarness(generator, k=8).run(cases)
            agg = report.aggregate()
            print(f"| {label:<14} | {report.passed}/{len(report.cases)} "
                  f"| {agg['recall@8']['mean']:.4f} | {agg['precision@8']['mean']:.4f} "
                  f"| {agg['mrr']['mean']:.4f} | {agg['ndcg@8']['mean']:.4f} |")
        store.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", choices=sorted(CORPORA), action="append",
                        help="which corpus to ablate (repeatable; default: all)")
    args = parser.parse_args(argv)
    for name in args.corpus or sorted(CORPORA):
        run(name, *CORPORA[name])
    return 0


if __name__ == "__main__":
    sys.exit(main())
