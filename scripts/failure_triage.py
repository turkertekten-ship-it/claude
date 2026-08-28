"""What is actually still failing, and at which stage.

Five external cases and three held-out ones fail, and the last several sessions
tuned parameters without a current picture of *why* they fail. Every sweep in
`scripts/` optimises a number that these eight cases dominate; none of them says
whether the gold chunk was missing from the candidate pool, present but ranked
below k, present and ranked but refused by the abstention gate, or retrieved
correctly and let down by the answer contract.

Those four call for four different fixes, and three of them are not reachable
by any parameter this project has swept.

For each failure, reports the stage that lost it:

  * `unreachable` - no expected source even with the candidate pool widened to
                    100 and MMR off. Nothing downstream can fix this.
  * `candidate`   - reachable when widened, but not in the shipped pool of 20.
                    A `candidate_k` problem, not a reranker one.
  * `ranking`     - in the shipped pool, ranked below k. The reranker's.
  * `abstention`  - retrieved and ranked, and the gate refused to answer.
  * `answer`      - retrieved, ranked, answered, and the contract rejected it.
  * `false-answer`- an abstain case that got answered.

Also prints, for a ranking loss, the best rank any expected source reached, so
"one place short" and "buried at 40" are distinguishable.

    PYTHONPATH=src python3 scripts/failure_triage.py
"""
import shutil, tempfile

from oodarag.eval.harness import EvalHarness, load_goldens
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

CORPUS = ("corpus/external/pypi", ["**/*.md"])
SETS = ("evals/goldens-external.jsonl", "evals/goldens-heldout.jsonl")
K = 8
#: How deep the widened probe looks. Bounded, and the bound is reported when it
#: bites - an unbounded search reads as "not in the corpus" for a chunk at 500.
DEEP = 100


def matches(uri: str, title: str, wanted: list[str]) -> bool:
    hay = f"{uri} {title}".lower()
    return any(w.lower() in hay for w in wanted)


def main() -> None:
    work = tempfile.mkdtemp(prefix="triage-")
    try:
        store = SqliteStore(f"{work}/index.db")
        pipeline = IndexPipeline(store)
        pipeline.run([FilesystemConnector(CORPUS[0], patterns=CORPUS[1], key="fs:x")])
        retriever = HybridRetriever(store, pipeline.embedder, RetrievalConfig())
        generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        # The shipped pool is `candidate_k`, so asking the shipped retriever for
        # more only re-slices twenty. A second retriever with the pool widened
        # and MMR off answers a different question: is it reachable at all?
        wide = HybridRetriever(store, pipeline.embedder,
                               RetrievalConfig(candidate_k=DEEP, top_k=DEEP,
                                               use_mmr=False))
        stats = store.stats()
        print(f"\n{stats['documents']} documents, {stats['chunks']} chunks, k={K}\n")

        tally: dict[str, int] = {}
        for path in SETS:
            cases = load_goldens(path)
            report = EvalHarness(generator, k=K).run(cases)
            by_question = {c.question: c for c in report.cases}
            print(f"## {path}  {report.passed}/{len(report.cases)}\n")
            for case in cases:
                result = by_question.get(case.question)
                if result is None or result.passed:
                    continue

                if case.expect_abstain:
                    stage = "false-answer"
                    detail = "answered a question the corpus cannot support"
                else:
                    def best_rank(r) -> int | None:
                        hits, _ = r.retrieve(case.question, top_k=DEEP)
                        for i, hit in enumerate(hits, 1):
                            if matches(hit.citation_uri, hit.citation_title,
                                       case.expect_sources):
                                return i
                        return None

                    shipped = best_rank(retriever)
                    best = shipped if shipped is not None else best_rank(wide)
                    if best is None:
                        stage = "unreachable"
                        detail = f"absent from a pool of {DEEP} with MMR off"
                    elif shipped is None:
                        stage = "candidate"
                        detail = f"reachable at rank {best} only with the pool widened"
                    elif best > K:
                        stage = "ranking"
                        detail = f"in the shipped pool at rank {best}, below k={K}"
                    elif result.abstained:
                        stage = "abstention"
                        detail = f"gate refused; expected source was at rank {best}"
                    else:
                        stage = "answer"
                        detail = f"rank {best}, failures={result.failures}"

                tally[stage] = tally.get(stage, 0) + 1
                print(f"  [{stage:12}] {case.question[:72]}")
                print(f"  {'':14} {detail}")
            print()

        print("## where the failures are lost\n")
        for stage, count in sorted(tally.items(), key=lambda kv: -kv[1]):
            print(f"  {stage:12} {count}")
        print()
        store.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
