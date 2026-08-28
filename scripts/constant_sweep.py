#!/usr/bin/env python3
"""Sweep any retrieval constant over both corpora.

Two thresholds in this codebase turned out to be set against a 33-document
corpus and stale on the 91-document one, found within an hour of each other
(L31, L32). That is a reason to audit the rest rather than wait for the third to
bite, and an audit needs to be cheap to repeat.

Sweeps a field of `RetrievalConfig`, or of the reranker, and prints pass counts
and failure mixes for both corpora side by side.

    PYTHONPATH=src python3 scripts/constant_sweep.py --field candidate_k --values 20 40 80 160
    PYTHONPATH=src python3 scripts/constant_sweep.py --field mmr_lambda --values 0.5 0.6 0.7 0.8 0.9
    PYTHONPATH=src python3 scripts/constant_sweep.py --on reranker --field coverage_weight --values 0.35 0.45 0.55

Choose a plateau, not a peak: a single high sample between two lower ones is the
golden set's shape rather than the corpus's.
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
    "external": ("corpus/external/pypi", ("**/*.md",), "evals/goldens-external.jsonl"),
    "primary": (".", ("src/**/*.py", "tests/**/*.py", "docs/**/*.md",
                      "internal/**/*.md", "*.md", "corpus/reference/**/*.md"),
                "evals/goldens.jsonl"),
}


def sweep(root, patterns, goldens, on: str, field: str, values: list):
    workdir = tempfile.mkdtemp(prefix="sweep-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key="fs:sweep")])
        cases = load_goldens(goldens)
        out = {}
        for value in values:
            config = RetrievalConfig()
            if on == "config":
                if not hasattr(config, field):
                    raise SystemExit(f"RetrievalConfig has no field {field!r}")
                setattr(config, field, value)
            retriever = HybridRetriever(store, pipeline.embedder, config)
            if on == "reranker":
                if not hasattr(retriever.reranker, field):
                    raise SystemExit(f"the reranker has no field {field!r}")
                setattr(retriever.reranker, field, value)
            generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
            report = EvalHarness(generator, k=8).run(cases)
            agg = report.aggregate()
            # startswith, not `in`: "unexpected abstention" contains
            # "expected abstention" and a substring test counts every refusal
            # as an over-answer (L32).
            answered = sum(1 for c in report.cases if not c.passed
                           and any(f.startswith("expected abstention") for f in c.failures))
            refused = sum(1 for c in report.cases if not c.passed
                          and any(f.startswith("unexpected abstention") for f in c.failures))
            out[value] = (report.passed, len(report.cases), answered, refused,
                          agg["recall@8"]["mean"], agg["ndcg@8"]["mean"])
        store.close()
        return out
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", required=True)
    parser.add_argument("--values", nargs="+", required=True)
    parser.add_argument("--on", choices=("config", "reranker"), default="config")
    args = parser.parse_args()

    values = []
    for raw in args.values:
        values.append(float(raw) if ("." in raw or "e" in raw.lower()) else int(raw))

    results = {name: sweep(*spec, args.on, args.field, values)
               for name, spec in CORPORA.items()}
    print(f"\n## {args.on}.{args.field}\n")
    print("| value | external | ans | ref | recall | nDCG   "
          "| primary | ans | ref | recall | nDCG   | combined |")
    print("|-------|----------|-----|-----|--------|--------"
          "|---------|-----|-----|--------|--------|----------|")
    for value in values:
        ep, et, ea, er, erc, end = results["external"][value]
        pp, pt, pa, pr, prc, pnd = results["primary"][value]
        print(f"| {str(value):<5} | {ep}/{et}    | {ea:^3} | {er:^3} | {erc:.4f} | {end:.4f} "
              f"| {pp}/{pt}   | {pa:^3} | {pr:^3} | {prc:.4f} | {pnd:.4f} | {ep + pp}/{et + pt} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
