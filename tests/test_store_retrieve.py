"""Storage, the FTS5 index, and hybrid retrieval over both arms."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.chunk import chunk_document  # noqa: E402
from oodarag.embed import HashingEmbedder  # noqa: E402
from oodarag.models import Document, RawDocument  # noqa: E402
from oodarag.retrieve import RetrievalConfig, Retriever, reciprocal_rank_fusion  # noqa: E402
from oodarag.store import Store  # noqa: E402

CORPUS = {
    "budgets.md": "# Budgets\n\nEvery network stage has a budget on requests, bytes and "
                  "wall-clock time. A crawl that runs forever is stopped by the page budget.",
    "fusion.md": "# Fusion\n\nReciprocal rank fusion combines ranked lists rather than raw "
                 "scores, because BM25 scores and cosine similarities are on incomparable "
                 "scales and neither is calibrated across queries.",
    "captions.md": "# Captions\n\nA caption track for a video you do not own cannot be "
                   "downloaded with an API key. The endpoint refuses key authentication "
                   "outright and requires an owner credential.",
    "gardening.md": "# Gardening\n\nRye grass germinates quickly in cool soil and makes a "
                    "useful winter cover crop for a vegetable bed.",
}


def build_store() -> Store:
    store = Store(":memory:")
    embedder = HashingEmbedder()
    for name, text in CORPUS.items():
        raw = RawDocument("file", name, f"file:///{name}", name, text)
        doc = Document.from_raw(raw, text, {})
        store.upsert_document(doc)
        chunks = chunk_document(doc)
        store.add_chunks(chunks, embedder.embed_batch([c.indexed_text for c in chunks]))
    return store


class TestStore(unittest.TestCase):
    def setUp(self) -> None:
        self.store = build_store()
        self.addCleanup(self.store.close)

    def test_stats_count_what_was_written(self) -> None:
        stats = self.store.stats()
        self.assertEqual(stats["documents"], len(CORPUS))
        self.assertGreater(stats["chunks"], 0)
        self.assertEqual(stats["chunks"], stats["embeddings"])

    def test_unchanged_document_is_reported_as_unchanged(self) -> None:
        # The saving that makes incremental ingest worth having.
        text = CORPUS["budgets.md"]
        raw = RawDocument("file", "budgets.md", "file:///budgets.md", "budgets.md", text)
        doc = Document.from_raw(raw, text, {})
        self.assertFalse(self.store.upsert_document(doc))

    def test_changed_document_drops_its_old_chunks(self) -> None:
        # Otherwise a document that shrinks leaves orphaned passages that are
        # still retrievable and no longer true.
        raw = RawDocument("file", "budgets.md", "file:///budgets.md", "budgets.md",
                          "# Budgets\n\nCompletely replaced content about tulip bulbs.")
        doc = Document.from_raw(raw, raw.text, {})
        self.assertTrue(self.store.upsert_document(doc))
        remaining = " ".join(
            c.text for c in self.store.chunks_by_rowids(
                [r[0] for r in self.store.iter_vectors()]
            ).values()
        )
        self.assertNotIn("wall-clock", remaining)

    def test_lexical_search_returns_positive_scores_best_first(self) -> None:
        hits = self.store.search_lexical("caption owner credential", 10)
        self.assertTrue(hits)
        self.assertTrue(all(h.score > 0 for h in hits))
        self.assertEqual(hits, sorted(hits, key=lambda h: h.score, reverse=True))

    def test_a_question_with_fts_syntax_does_not_raise(self) -> None:
        # A user question is not a query expression. `NOT`, quotes and hyphens
        # are ordinary English here.
        for question in ['what is "fusion" NOT about?', "budgets -- and bytes?", "a AND b OR c"]:
            self.store.search_lexical(question, 5)  # must not raise

    def test_an_empty_query_returns_nothing_rather_than_everything(self) -> None:
        self.assertEqual(self.store.search_lexical("   ", 5), [])


class TestFusion(unittest.TestCase):
    def test_agreement_between_arms_beats_a_single_arm(self) -> None:
        fused = reciprocal_rank_fusion({"lexical": ["x", "z"], "dense": ["x", "w"]})
        totals = {k: sum(v.values()) for k, v in fused.items()}
        self.assertGreater(totals["x"], totals["z"])
        self.assertGreater(totals["x"], totals["w"])

    def test_ranks_are_one_based(self) -> None:
        # Pinned because implementations differ, and a 0-based variant changes
        # every score.
        fused = reciprocal_rank_fusion({"only": ["first"]}, k=60)
        self.assertAlmostEqual(fused["first"]["only"], 1.0 / 61)

    def test_contributions_are_kept_per_arm(self) -> None:
        fused = reciprocal_rank_fusion({"lexical": ["x"], "dense": ["x"]})
        self.assertEqual(set(fused["x"]), {"lexical", "dense"})


class TestRetriever(unittest.TestCase):
    def setUp(self) -> None:
        self.store = build_store()
        self.addCleanup(self.store.close)
        self.retriever = Retriever(self.store, HashingEmbedder(),
                                   RetrievalConfig(top_k=3, candidates=20))

    def test_finds_the_right_document_for_a_paraphrased_question(self) -> None:
        hits = self.retriever.search("can I get a transcript for someone else's video?")
        self.assertTrue(hits)
        self.assertIn("captions.md", hits[0].chunk.doc_id + str(hits[0].citation_uri))

    def test_exact_rare_term_is_found_by_the_lexical_arm(self) -> None:
        results, report = self.retriever.search_with_report("wall-clock")
        self.assertTrue(results)
        self.assertIn("lexical", report.arms_used)

    def test_score_components_explain_which_arm_produced_a_hit(self) -> None:
        hits = self.retriever.search("reciprocal rank fusion")
        self.assertTrue(hits)
        self.assertTrue(set(hits[0].components) & {"lexical", "dense"})

    def test_documents_are_attached_so_a_citation_can_name_a_source(self) -> None:
        hits = self.retriever.search("budget on requests and bytes")
        self.assertTrue(hits)
        self.assertIsNotNone(hits[0].document)
        self.assertTrue(hits[0].citation_uri.startswith("file:///"))

    def test_dense_arm_alone_still_returns_something(self) -> None:
        retriever = Retriever(self.store, HashingEmbedder(),
                              RetrievalConfig(use_lexical=False, top_k=3))
        results, report = retriever.search_with_report("network budget")
        self.assertTrue(results)
        self.assertEqual(report.arms_used, ["dense"])

    def test_lexical_arm_alone_still_returns_something(self) -> None:
        retriever = Retriever(self.store, HashingEmbedder(),
                              RetrievalConfig(use_dense=False, top_k=3))
        results, report = retriever.search_with_report("germinates")
        self.assertTrue(results)
        self.assertEqual(report.arms_used, ["lexical"])

    def test_empty_query_returns_nothing(self) -> None:
        self.assertEqual(self.retriever.search("  "), [])

    def test_a_metadata_filter_restricts_the_result_set(self) -> None:
        results = self.retriever.search("budget bytes fusion caption",
                                        filters={"source_system": "file"})
        self.assertTrue(results)
        for hit in results:
            self.assertEqual(hit.chunk.metadata["source_system"], "file")

    def test_a_filter_matching_nothing_returns_nothing(self) -> None:
        self.assertEqual(
            self.retriever.search("budget", filters={"source_system": "nonexistent"}), []
        )

    def test_a_list_filter_matches_any_member(self) -> None:
        both = self.retriever.search("budget bytes",
                                     filters={"source_system": ["file", "github"]})
        self.assertTrue(both)

    def test_a_chunk_missing_the_key_does_not_pass_the_filter(self) -> None:
        # Absent metadata is not evidence of a match; treating it as one is how
        # a filtered search returns the thing it was told to exclude.
        self.assertEqual(self.retriever.search("budget", filters={"absent_key": "x"}), [])

    def test_the_report_says_how_many_were_filtered_out(self) -> None:
        _results, report = self.retriever.search_with_report(
            "budget bytes fusion", filters={"source_system": "nonexistent"}
        )
        self.assertGreater(report.filtered_out, 0)
        self.assertEqual(report.returned, 0)

    def test_top_k_is_respected(self) -> None:
        self.assertLessEqual(len(self.retriever.search("budget fusion caption", 2)), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
