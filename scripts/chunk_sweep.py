#!/usr/bin/env python3
"""Sweep the chunker over both corpora.

Every constant this repository has swept so far is downstream of the chunk:
`candidate_k`, `mmr_lambda`, `rrf_k`, the coverage weights, the abstention
floor, the base weights (L33, L44, L61, L62). The chunker's own sizes have
never been measured. They are the most upstream numbers in the pipeline - they
decide what a retrievable unit *is*, and both arms and the reranker see only
what they produce - and L61's rule applies: an untested default is a claim.

    PYTHONPATH=src python3 scripts/chunk_sweep.py --field target_tokens \
        --values 160 240 320 480 640 --scale
    PYTHONPATH=src python3 scripts/chunk_sweep.py --field overlap_tokens \
        --values 0 32 64 128

`--scale` exists because `target_tokens` is not independent: the shipped config
is target 320, hard_max 640, overlap 64, i.e. hard_max = 2x and overlap = 0.2x.
Sweeping target alone past 640 would silently be a hard_max sweep instead, and
at 160 would leave an overlap that is 40% of a chunk. With --scale the three
move together and the knob means "chunk granularity"; without it, one field
moves and the rest stay shipped.

Cost is reported next to quality on purpose. Halving the chunk size roughly
doubles the chunk count, and that is vectors, index bytes and embed time - a
quality tie at twice the cost is a loss.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from dataclasses import replace

from oodarag.chunking import ChunkConfig
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


def chunk_config(field: str, value: int, scale: bool) -> ChunkConfig:
    if scale and field == "target_tokens":
        # Hold the shipped ratios: hard_max = 2x target, overlap = 0.2x target.
        return ChunkConfig(target_tokens=value,
                           hard_max_tokens=value * 2,
                           overlap_tokens=max(1, round(value * 0.2)))
    return replace(ChunkConfig(), **{field: value})


def run_one(root, patterns, goldens, config: ChunkConfig):
    workdir = tempfile.mkdtemp(prefix="chunksweep-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        pipeline = IndexPipeline(store, chunk_config=config)
        report = pipeline.run([FilesystemConnector(root, patterns=patterns, key="fs:sweep")])
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
        generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        result = EvalHarness(generator, k=8).run(load_goldens(goldens))
        agg = result.aggregate()
        # startswith, not `in`: "unexpected abstention" contains "expected
        # abstention", and a substring test counts every refusal as an
        # over-answer (L32).
        answered = sum(1 for c in result.cases if not c.passed
                       and any(f.startswith("expected abstention") for f in c.failures))
        refused = sum(1 for c in result.cases if not c.passed
                      and any(f.startswith("unexpected abstention") for f in c.failures))
        store.close()
        return {
            "passed": result.passed, "total": len(result.cases),
            "answered": answered, "refused": refused,
            "recall": agg["recall@8"]["mean"], "ndcg": agg["ndcg@8"]["mean"],
            "mrr": agg["mrr"]["mean"], "precision": agg["precision@8"]["mean"],
            "chunks": report.chunking.get("chunks", 0),
            "tokens_p50": report.chunking.get("tokens_p50", 0),
            "tokens_p95": report.chunking.get("tokens_p95", 0),
            "tokens_max": report.chunking.get("tokens_max", 0),
        }
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", default="target_tokens",
                        choices=[f for f in ChunkConfig.__dataclass_fields__
                                 if f.endswith("_tokens")])
    parser.add_argument("--values", nargs="+", type=int, default=[])
    parser.add_argument("--scale", action="store_true",
                        help="scale hard_max and overlap with target_tokens")
    parser.add_argument("--corpus", choices=(*CORPORA, "both"), default="both")
    parser.add_argument("--headers", action="store_true",
                        help="ablate the context header instead: --values is ignored")
    args = parser.parse_args()

    names = list(CORPORA) if args.corpus == "both" else [args.corpus]
    if args.headers:
        # Contextual retrieval is commitment 2 of this module's docstring and
        # has never been measured. It is not free: the header is 13.1% on top
        # of the external corpus's body tokens, and 29% of what gets embedded
        # for a chunk with a short body (L63).
        args.values = [1, 0]
        configs = {1: ChunkConfig(), 0: ChunkConfig(include_context_header=False)}
    else:
        configs = {v: chunk_config(args.field, v, args.scale) for v in args.values}
    results = {name: {v: run_one(*CORPORA[name], configs[v]) for v in args.values}
               for name in names}

    label = ("include_context_header" if args.headers
             else args.field + (" (scaled)" if args.scale else ""))
    print(f"\n## ChunkConfig.{label}\n")
    for name in names:
        print(f"### {name}\n")
        print("| value | pass | ans | ref | recall@8 | prec@8 | MRR    | nDCG@8 "
              "| chunks | p50 | p95 | max |")
        print("|-------|------|-----|-----|----------|--------|--------|--------"
              "|--------|-----|-----|-----|")
        for value in args.values:
            r = results[name][value]
            print(f"| {value:<5} | {r['passed']}/{r['total']} | {r['answered']:^3} "
                  f"| {r['refused']:^3} | {r['recall']:.4f}   | {r['precision']:.4f} "
                  f"| {r['mrr']:.4f} | {r['ndcg']:.4f} | {r['chunks']:>6} "
                  f"| {r['tokens_p50']:>3} | {r['tokens_p95']:>3} | {r['tokens_max']:>3} |")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
