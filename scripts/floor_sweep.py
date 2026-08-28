#!/usr/bin/env python3
"""Sweep the abstention floor over both corpora.

`AnswerConfig.min_relevance` decides whether a question is answered or refused.
It is a property of the corpus rather than of the algorithm, so it goes stale
when the corpus changes - 0.15 was set against 33 documents and sat in a dip on
91 - and it is the kind of number that gets picked by looking at one run.

This prints the whole curve so the choice can be made on its *shape*. A plateau
several samples wide is a threshold; a single high point between two lower ones
is a fit to the golden set.

    PYTHONPATH=src python3 scripts/floor_sweep.py
    PYTHONPATH=src python3 scripts/floor_sweep.py --from 0.05 --to 0.40 --step 0.05
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


def sweep(root: str, patterns: tuple[str, ...], goldens: str,
          floors: list[float]) -> dict[float, tuple[int, int, int, int]]:
    """floor -> (passed, total, wrongly answered, wrongly refused)."""
    workdir = tempfile.mkdtemp(prefix="floor-")
    try:
        store = SqliteStore(f"{workdir}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(root, patterns=patterns, key="fs:floor")])
        cases = load_goldens(goldens)
        out = {}
        for floor in floors:
            retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
            generator = AnswerGenerator(
                retriever, AnswerConfig(generator="extractive", min_relevance=floor))
            report = EvalHarness(generator, k=8).run(cases)
            # "unexpected abstention" *contains* "expected abstention", so a
            # substring test counts every wrongly-refused case as wrongly
            # answered too. The first version of this script did exactly that
            # and produced a table where raising the floor increased
            # over-answering, which is impossible.
            answered = sum(1 for c in report.cases if not c.passed
                           and any(f.startswith("expected abstention")
                                   for f in c.failures))
            refused = sum(1 for c in report.cases if not c.passed
                          and any(f.startswith("unexpected abstention")
                                  for f in c.failures))
            out[floor] = (report.passed, len(report.cases), answered, refused)
        store.close()
        return out
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="start", type=float, default=0.10)
    parser.add_argument("--to", dest="end", type=float, default=0.30)
    parser.add_argument("--step", type=float, default=0.01)
    args = parser.parse_args()

    floors, value = [], args.start
    while value <= args.end + 1e-9:
        floors.append(round(value, 4))
        value += args.step

    results = {name: sweep(*spec, floors) for name, spec in CORPORA.items()}
    print(f"\n| floor | external | wrong-ans | wrong-ref "
          f"| primary | wrong-ans | wrong-ref | combined |")
    print("|-------|----------|-----------|-----------"
          "|---------|-----------|-----------|----------|")
    for floor in floors:
        ep, et, ea, er = results["external"][floor]
        pp, pt, pa, pr = results["primary"][floor]
        print(f"| {floor:<5} | {ep}/{et}    | {ea:^9} | {er:^9} "
              f"| {pp}/{pt}   | {pa:^9} | {pr:^9} | {ep + pp}/{et + pt} |")
    print("\nChoose a plateau, not a peak. A single high sample between two lower "
          "ones is\nthe golden set's shape, not the corpus's.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
