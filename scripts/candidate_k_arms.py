"""Did halving `candidate_k` starve the dense arm and MMR?

ADR 0004's refreshed ablation raised two reversals and offered one hypothesis
for both. `candidate_k` went 40 -> 20 earlier in this project, measured on the
*hybrid* configuration only: same pass rates, better nDCG, 15-26% faster. What
that measurement could not see is what the change did to the parts.

Since then, dense-only has fallen 44/54 -> 42/54 and MMR has gone from earning a
case to costing 0.0116 of precision for 0.0013 of nDCG. The hypothesis is that
both follow from a smaller candidate set: the weaker arm has fewer chances to
land a hit, and there is less redundancy left for MMR to remove.

It is falsifiable. If it holds, dense-only and MMR's contribution should both
improve as `candidate_k` rises, while hybrid stays flat - which is exactly why
the original sweep saw nothing. If dense-only is flat too, the arm got worse for
some other reason and the ADR's hypothesis is wrong.

    PYTHONPATH=src python3 scripts/candidate_k_arms.py
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

KS = (10, 20, 40, 80)
ARMS = {
    "hybrid": {},
    "dense only": {"lexical_weight": 0.0},
    "lexical only": {"dense_weight": 0.0},
    "no mmr": {"use_mmr": False},
}


def main() -> None:
    work = tempfile.mkdtemp(prefix="ck-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector("corpus/external/pypi",
                                          patterns=["**/*.md"], key="fs:x")])
        cases = load_goldens("evals/goldens-external.jsonl")
        print("\n| configuration | " + " | ".join(f"k={k}" for k in KS) + " |")
        print("|---" * (len(KS) + 1) + "|")
        for label, overrides in ARMS.items():
            cells = []
            for k in KS:
                config = RetrievalConfig(candidate_k=k, **overrides)
                # The knob has to reach the retriever, not just the dataclass:
                # a sweep of a value the retriever re-derives would print a flat
                # row and read as a finding (L70's shape).
                retriever = HybridRetriever(store, pipeline.embedder, config)
                assert retriever.config.candidate_k == k
                report = EvalHarness(
                    AnswerGenerator(retriever, AnswerConfig(generator="extractive")),
                    k=8).run(cases)
                agg = report.aggregate()
                cells.append(f"{report.passed}/{len(report.cases)} "
                             f"r{agg['recall@8']['mean']:.3f} "
                             f"p{agg['precision@8']['mean']:.3f}")
            print(f"| {label} | " + " | ".join(cells) + " |", flush=True)
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
