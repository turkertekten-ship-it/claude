"""Does fusing two arms actually beat using the better one?

The question that matters about hybrid retrieval is not whether it works but
whether it *earns its second index*. Measured in aggregate on this corpus the
answer looked like no: BM25 alone scores higher than the fused ranking, which is
the documented "weakest-link effect" of unweighted RRF.

Measured per query class the answer reverses. The dense arm here is a
character-n-gram hashing embedder, so its strength is degraded input, and this
corpus's clean questions never exercise that. Once queries carry typos the dense
arm becomes the better arm and fusion beats both.

So the invariant worth guarding is conditional, and this file states both halves
rather than only the flattering one:

  * On NOISY queries, fusion must be at least as good as its best single arm.
  * On CLEAN queries it is NOT, by roughly 0.04 MRR, and that is the accepted
    price of the 1.0/1.0 default. The test pins the size of that loss so it
    cannot quietly grow.
"""

from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from oodarag.evals.harness import load_goldens
from oodarag.ingest.files import FilesConnector
from oodarag.pipeline import Pipeline, PipelineConfig
from oodarag.retrieve import HybridRetriever, RetrievalConfig

CORPUS = Path("evals/corpus")
GOLDENS = Path("evals/goldens.jsonl")

#: How far fusion is allowed to trail its best arm on clean queries. Measured at
#: 0.043; the headroom is for run-to-run variation on a set this small, not a
#: budget to spend.
CLEAN_TOLERANCE = 0.08


def _transpose(word: str, rng: random.Random) -> str:
    """Swap two adjacent inner characters.

    This is the owner's own dominant misspelling shape, taken from their goal
    strings: ultrathink -> ultrahtink, continue -> conitnue.
    """
    if len(word) < 5:
        return word
    i = rng.randrange(1, len(word) - 2)
    return word[:i] + word[i + 1] + word[i] + word[i + 2:]


def _corrupt(question: str, n: int, rng: random.Random) -> str:
    words = question.split()
    idx = [i for i, w in enumerate(words) if len(w) >= 5]
    rng.shuffle(idx)
    for i in idx[:n]:
        words[i] = _transpose(words[i], rng)
    return " ".join(words)


class FusionInvariant(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not CORPUS.is_dir() or not GOLDENS.is_file():
            raise unittest.SkipTest("seed corpus or golden set missing")
        cls._tmp = tempfile.TemporaryDirectory()
        cls.pipe = Pipeline(PipelineConfig(root=Path(cls._tmp.name)))
        cls.pipe.ingest([FilesConnector(str(CORPUS))])
        cls.pipe.refresh_indexes()
        cls.store = cls.pipe.store
        cls.docs = {d.doc_id: d for d in cls.store.documents()}
        cls.goldens = [g for g in load_goldens(GOLDENS) if not g.should_abstain]
        cls.retriever = HybridRetriever(cls.store, cls.pipe.embedder,
                                        cls.pipe.bm25, cls.pipe.dense, RetrievalConfig())
        if not cls.goldens:
            raise unittest.SkipTest("no answerable goldens")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pipe.close()
        cls._tmp.cleanup()

    def _rr(self, chunk_ids, golden) -> float:
        for rank, cid in enumerate(chunk_ids, 1):
            chunk = self.store.get_chunk(cid)
            if chunk and any(u in self.docs[chunk.doc_id].uri for u in golden.relevant_uris):
                return 1.0 / rank
        return 0.0

    def _mrr(self, arm, typos: int, seeds: int = 2) -> float:
        total = 0.0
        for seed in range(seeds):
            rng = random.Random(seed)
            questions = [_corrupt(g.question, typos, rng) for g in self.goldens]
            total += sum(self._rr(arm(q), g) for q, g in zip(questions, self.goldens))
        return total / (seeds * len(self.goldens))

    def _arms(self):
        return {
            "bm25": lambda q: [c for c, _ in self.pipe.bm25.search(q, 8)],
            "dense": lambda q: [c for c, _ in self.pipe.dense.search(
                self.pipe.embedder.embed_one(q), 8)],
            "hybrid": lambda q: [s.chunk.chunk_id for s in self.retriever.retrieve(q, 8)],
        }

    def test_on_noisy_queries_fusion_beats_its_best_arm(self) -> None:
        # The load-bearing case. If this fails, the second index is dead weight
        # and ADR 0002 no longer describes the system.
        arms = self._arms()
        scores = {name: self._mrr(fn, typos=6) for name, fn in arms.items()}
        best_single = max(scores["bm25"], scores["dense"])
        self.assertGreaterEqual(
            scores["hybrid"], best_single,
            f"fusion lost to its best arm on noisy queries: {scores}")

    def test_the_dense_arm_wins_on_noisy_queries(self) -> None:
        # The reason fusion has anything to fuse. A change that makes the dense
        # arm uniformly worse than BM25 removes the case for hybrid entirely.
        arms = self._arms()
        self.assertGreater(self._mrr(arms["dense"], typos=6),
                           self._mrr(arms["bm25"], typos=6),
                           "the dense arm no longer wins its home class")

    def test_the_clean_query_loss_stays_bounded(self) -> None:
        # The honest half: on clean queries fusion IS worse than BM25 alone.
        # That is accepted, but it is pinned so it cannot quietly grow.
        arms = self._arms()
        scores = {name: self._mrr(fn, typos=0, seeds=1) for name, fn in arms.items()}
        gap = max(scores["bm25"], scores["dense"]) - scores["hybrid"]
        self.assertLess(gap, CLEAN_TOLERANCE,
                        f"fusion's clean-query deficit grew to {gap:.3f}: {scores}")

    def test_typos_actually_degrade_the_lexical_arm(self) -> None:
        # Guards the experiment itself: if corruption stopped biting, every
        # result above would be measuring nothing.
        arms = self._arms()
        self.assertLess(self._mrr(arms["bm25"], typos=6),
                        self._mrr(arms["bm25"], typos=0, seeds=1),
                        "corruption no longer degrades BM25; the fixture is broken")


if __name__ == "__main__":
    unittest.main()
