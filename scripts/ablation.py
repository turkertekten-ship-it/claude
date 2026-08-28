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

from _corpora import CORPORA  # noqa: E402

ARMS = {
    "hybrid": {},
    "lexical only": {"dense_weight": 0.0},
    "dense only": {"lexical_weight": 0.0},
    "no rerank": {"use_rerank": False},
    "no mmr": {"use_mmr": False},
}


def sweep_coverage_power(name: str, root: str, patterns: tuple[str, ...],
                         goldens: str, powers: list[float]) -> None:
    """The coverage exponent is a documented measurement in rerank.py, so it has
    to be re-measurable. Its first table was taken on a corpus that turned out to
    be 90.9% site template, and the conclusion moved when that was removed."""
    workdir = tempfile.mkdtemp(prefix=f"power-{name}-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key=f"fs:{name}")])
        cases = load_goldens(goldens)
        print(f"\n## {name}: coverage_power\n")
        print(f"| power | pass | recall@8 | prec@8 | MRR | nDCG@8 |")
        print("|-------|------|----------|--------|-----|--------|")
        for power in powers:
            retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
            retriever.reranker.coverage_power = power
            generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
            report = EvalHarness(generator, k=8).run(cases)
            agg = report.aggregate()
            print(f"| {power:<5} | {report.passed}/{len(report.cases)} "
                  f"| {agg['recall@8']['mean']:.4f} | {agg['precision@8']['mean']:.4f} "
                  f"| {agg['mrr']['mean']:.4f} | {agg['ndcg@8']['mean']:.4f} |")
        store.close()
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


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
    parser.add_argument("--sweep-coverage-power", type=float, nargs="+",
                        metavar="P",
                        help="sweep the reranker's coverage exponent instead of "
                             "ablating arms, e.g. --sweep-coverage-power 1.0 2.0 3.0")
    args = parser.parse_args(argv)
    for name in args.corpus or sorted(CORPORA):
        if args.sweep_coverage_power:
            sweep_coverage_power(name, *CORPORA[name], args.sweep_coverage_power)
        else:
            run(name, *CORPORA[name])
    return 0


if __name__ == "__main__":
    sys.exit(main())
