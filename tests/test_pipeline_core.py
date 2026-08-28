"""Core pipeline behaviour: chunking, embedding, storage, retrieval, grounding.

These run entirely in memory with no network and no optional dependency, which
is the whole point of the zero-dependency design: the pipeline that CI exercises
is the same pipeline that runs in production, not a mock of it.
"""

from __future__ import annotations

import unittest

from oodarag.chunking import ChunkConfig, chunk_document
from oodarag.embedding.hashing import HashingEmbedder, cosine
from oodarag.generate.answer import AnswerConfig, AnswerGenerator
from oodarag.generate.contract import build_citations, verify
from oodarag.models import Citation, Document, RawDocument
from oodarag.pipeline import IndexPipeline, normalize
from oodarag.retrieve.fusion import RankedList, reciprocal_rank_fusion
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.retrieve.mmr import jaccard, mmr_select
from oodarag.retrieve.rerank import _longest_common_run
from oodarag.store.sqlite_store import SqliteStore
from oodarag.store.vectors import VectorIndex, pack, unpack
from oodarag.util.stemming import stem
from oodarag.util.text import estimate_tokens, redact_secrets, tokenize

CORPUS = {
    "rag.md": ("# Retrieval augmented generation\n\n"
               "RAG grounds a language model in documents retrieved at query time, "
               "so the model can cite where an answer came from instead of relying "
               "on what it memorised during training.\n\n"
               "## Why it helps\n\n"
               "The model gets facts that are current, and the reader gets a source "
               "to verify against."),
    "chunking.md": ("# Chunking\n\n"
                    "Documents are split into passages before they are embedded. "
                    "Splitting on a fixed character count cuts sentences in half and "
                    "strips passages of the context that made them meaningful.\n\n"
                    "## Overlap\n\n"
                    "Consecutive chunks share a sentence or two so a fact spanning a "
                    "boundary is retrievable from either side."),
    "bm25.md": ("# Lexical ranking\n\n"
                "BM25 scores a passage by term frequency and inverse document "
                "frequency, saturating so a repeated word stops adding value. It "
                "finds exact identifiers that an embedding blurs away."),
    "budgets.md": ("# Crawl budgets\n\n"
                   "Every network loop is bounded by requests, bytes, depth and "
                   "wall clock time. Bounding only the accepted results lets work "
                   "run away invisibly."),
}


def make_store() -> SqliteStore:
    return SqliteStore(":memory:")


def build_index(store: SqliteStore) -> IndexPipeline:
    pipeline = IndexPipeline(store, HashingEmbedder(dim=512))
    documents = []
    for name, text in CORPUS.items():
        raw = RawDocument("filesystem", name, f"file:///corpus/{name}", name, text)
        documents.append(normalize(raw))
    store.upsert_documents(documents)
    pipeline.embedder.fit([d.text for d in documents])
    for document in documents:
        store.replace_chunks(document.doc_id, chunk_document(document))
    pipeline.embed_missing()
    return pipeline


class StemmingTest(unittest.TestCase):
    def test_inflections_share_a_stem(self):
        for a, b in [("abstain", "abstained"), ("run", "running"), ("index", "indexing"),
                     ("retrieve", "retrieved"), ("bound", "bounded")]:
            with self.subTest(pair=(a, b)):
                self.assertEqual(stem(a), stem(b))

    def test_distinct_words_keep_distinct_stems(self):
        self.assertNotEqual(stem("crawler"), stem("chunk"))
        self.assertNotEqual(stem("lexical"), stem("vector"))

    def test_stemming_is_idempotent(self):
        for word in ["running", "abstained", "generation", "citations", "policies"]:
            with self.subTest(word=word):
                self.assertEqual(stem(stem(word)), stem(word))

    def test_tokenize_stems_only_when_asked(self):
        self.assertIn("abstained", tokenize("it abstained"))
        self.assertIn("abstain", tokenize("it abstained", stem_words=True))


class ChunkingTest(unittest.TestCase):
    def test_markdown_sections_carry_their_heading_path(self):
        text = CORPUS["rag.md"]
        doc = Document.from_raw(RawDocument("fs", "a", "file:///a", "rag.md", text), text, {})
        chunks = chunk_document(doc)
        headers = " ".join(c.context_header for c in chunks)
        self.assertIn("Why it helps", headers)
        for chunk in chunks:
            self.assertIn("rag.md", chunk.context_header)

    def test_code_is_split_on_definitions(self):
        code = ("import os\n\n\n"
                "def alpha(x):\n    return x + 1\n\n\n"
                "def beta(y):\n    return y * 2\n\n\n"
                "class Gamma:\n    pass\n")
        doc = Document.from_raw(
            RawDocument("gh", "m.py", "file:///m.py", "m.py", code), code,
            {"language": "python"})
        chunks = chunk_document(doc)
        # These definitions are tiny, so they merge into one chunk - and the
        # merged chunk must declare every symbol it contains, not just the first.
        declared = []
        for chunk in chunks:
            declared.extend(chunk.metadata.get("symbols")
                            or [chunk.metadata.get("symbol")])
        self.assertEqual(declared, ["alpha", "beta", "Gamma"])
        for symbol in ("alpha", "beta", "Gamma"):
            self.assertIn(symbol, " ".join(c.context_header for c in chunks))
        # The preamble travels with the first definition rather than being lost.
        self.assertIn("import os", chunks[0].text)

    def test_large_definitions_get_their_own_chunk(self):
        body = "\n".join(f"    value_{i} = compute(i) + offset" for i in range(60))
        code = f"def alpha(x):\n{body}\n\n\ndef beta(y):\n{body}\n"
        doc = Document.from_raw(
            RawDocument("gh", "big.py", "file:///big.py", "big.py", code), code,
            {"language": "python"})
        symbols = [c.metadata.get("symbol") for c in chunk_document(doc)]
        self.assertIn("alpha", symbols)
        self.assertIn("beta", symbols)

    def test_indexed_text_includes_the_context_header(self):
        text = CORPUS["chunking.md"]
        doc = Document.from_raw(RawDocument("fs", "c", "file:///c", "chunking.md", text),
                                text, {})
        chunk = chunk_document(doc)[0]
        self.assertTrue(chunk.indexed_text.startswith(chunk.context_header))
        self.assertIn(chunk.text, chunk.indexed_text)

    def test_runt_chunks_are_merged_into_their_neighbour(self):
        text = "# A\n\n" + ("word " * 400) + "\n\n# B\n\ntiny.\n"
        doc = Document.from_raw(RawDocument("fs", "d", "file:///d", "d.md", text), text, {})
        chunks = chunk_document(doc, ChunkConfig(min_tokens=40))
        self.assertTrue(all(c.token_estimate >= 20 for c in chunks),
                        [c.token_estimate for c in chunks])

    def test_a_unit_the_splitter_cannot_divide_still_respects_the_ceiling(self):
        """The shape that broke it: a changelog list with no full stop in it.

        `split_sentences` returns one unit for text with no terminal
        punctuation, and packing used to emit an over-ceiling unit whole - 8 of
        1,810 external chunks, the largest 2.1x the ceiling (L63).
        """
        config = ChunkConfig(target_tokens=60, hard_max_tokens=120, overlap_tokens=12)
        entries = "\n".join(f"- Fix issue {i} in module_{i} by contributor_{i}"
                             for i in range(120))
        text = f"# Changelog\n\n{entries}\n"
        doc = Document.from_raw(RawDocument("fs", "c", "file:///c", "c.md", text), text, {})
        chunks = chunk_document(doc, config)

        self.assertGreater(len(chunks), 3, "the oversized unit was emitted whole")
        for chunk in chunks:
            self.assertLessEqual(estimate_tokens(chunk.text), config.hard_max_tokens,
                                 f"{estimate_tokens(chunk.text)} tokens in {chunk.text[:60]!r}")
        # Nothing invented, nothing dropped, nothing cut mid-word: the words of
        # the pieces are the words of the source, in order.
        self.assertEqual(" ".join(c.text for c in chunks).split(), text.split())
        # And each piece still says truthfully where it came from, which is what
        # a citation resolves against.
        for chunk in chunks:
            self.assertEqual(text[chunk.char_start:chunk.char_start + len(chunk.text)],
                             chunk.text)

    def test_one_line_too_big_to_split_is_windowed_on_word_boundaries(self):
        """A minified line has no newline to split on either. Words are the floor."""
        config = ChunkConfig(target_tokens=40, hard_max_tokens=80, overlap_tokens=8)
        line = " ".join(f"token{i}" for i in range(400))
        doc = Document.from_raw(RawDocument("fs", "m", "file:///m", "m.md", line), line, {})
        chunks = chunk_document(doc, config)

        self.assertGreater(len(chunks), 3)
        for chunk in chunks:
            self.assertLessEqual(estimate_tokens(chunk.text), config.hard_max_tokens)
        self.assertEqual(" ".join(c.text for c in chunks).split(), line.split())

    def test_the_ceiling_bounds_the_body_and_the_header_is_added_on_top(self):
        """Two different numbers that both get called "the chunk size".

        `hard_max_tokens` is spent on the body; `Chunk.token_estimate` measures
        the body *plus* the context header, which is a median 19 tokens and 13%
        of the external corpus's embedded text (L63). Reading a size without
        its units is how a 640 ceiling reports 667.
        """
        config = ChunkConfig(target_tokens=60, hard_max_tokens=120, overlap_tokens=12)
        entries = "\n".join(f"- Fix issue {i} in module_{i}" for i in range(120))
        text = f"# Changelog\n\n{entries}\n"
        doc = Document.from_raw(RawDocument("fs", "h", "file:///h", "h.md", text), text, {})
        chunks = chunk_document(doc, config)

        widest = max(chunks, key=lambda c: c.token_estimate)
        self.assertLessEqual(estimate_tokens(widest.text), config.hard_max_tokens)
        self.assertEqual(widest.token_estimate,
                         estimate_tokens(widest.indexed_text))
        self.assertGreater(estimate_tokens(widest.context_header), 0)

    def test_ordinals_are_contiguous_after_merging(self):
        text = CORPUS["rag.md"] + "\n\n# Tail\n\nx.\n"
        doc = Document.from_raw(RawDocument("fs", "e", "file:///e", "e.md", text), text, {})
        chunks = chunk_document(doc)
        self.assertEqual([c.ordinal for c in chunks], list(range(len(chunks))))


class EmbeddingTest(unittest.TestCase):
    def test_identical_text_embeds_identically_across_instances(self):
        a, b = HashingEmbedder(dim=256), HashingEmbedder(dim=256)
        self.assertEqual(a.embed_query("stable text"), b.embed_query("stable text"))

    def test_vectors_are_unit_length(self):
        vector = HashingEmbedder(dim=256).embed_query("some words here")
        self.assertAlmostEqual(sum(v * v for v in vector) ** 0.5, 1.0, places=5)

    def test_related_text_scores_above_unrelated(self):
        embedder = HashingEmbedder(dim=768)
        embedder.fit(list(CORPUS.values()))
        query = embedder.embed_query("how are documents split into passages?")
        related = embedder.embed_documents([CORPUS["chunking.md"]])[0]
        unrelated = embedder.embed_documents([CORPUS["bm25.md"]])[0]
        self.assertGreater(cosine(query, related), cosine(query, unrelated))

    def test_fingerprint_changes_when_the_space_changes(self):
        embedder = HashingEmbedder(dim=256)
        before = embedder.fingerprint
        embedder.fit(list(CORPUS.values()))
        self.assertNotEqual(before, embedder.fingerprint)
        self.assertNotEqual(HashingEmbedder(dim=512).fingerprint, before)

    def test_state_round_trips(self):
        original = HashingEmbedder(dim=256)
        original.fit(list(CORPUS.values()))
        restored = HashingEmbedder(dim=256)
        restored.load_state(original.state())
        self.assertEqual(original.fingerprint, restored.fingerprint)
        # Not bit-identical: the persisted state drops singleton terms (they all
        # carry the default maximum idf anyway) and dict iteration order changes
        # the float summation order. Directional equivalence is the property
        # that matters for retrieval.
        self.assertGreater(
            cosine(original.embed_query("chunking"), restored.embed_query("chunking")),
            0.9999,
        )

    def test_empty_text_does_not_crash(self):
        self.assertEqual(len(HashingEmbedder(dim=64).embed_query("")), 64)


class VectorStoreTest(unittest.TestCase):
    def test_pack_round_trips_within_float32_precision(self):
        vector = [0.1, -0.25, 0.5, 0.0]
        for original, restored in zip(vector, unpack(pack(vector))):
            self.assertAlmostEqual(original, restored, places=6)

    def test_search_returns_nearest_first(self):
        index = VectorIndex(3)
        index.add("a", [1.0, 0.0, 0.0])
        index.add("b", [0.0, 1.0, 0.0])
        index.add("c", [0.9, 0.1, 0.0])
        self.assertEqual([i for i, _ in index.search([1.0, 0.0, 0.0], k=2)], ["a", "c"])

    def test_filter_is_applied_before_scoring(self):
        index = VectorIndex(2)
        index.add("a", [1.0, 0.0])
        index.add("b", [0.9, 0.1])
        index.add("c", [0.0, 1.0])
        # Without pre-filtering, top-2 would be a and b and the filter would
        # leave a single result instead of the two that were asked for.
        results = index.search([1.0, 0.0], k=2, allowed={"b", "c"})
        self.assertEqual([i for i, _ in results], ["b", "c"])


class FusionAndMmrTest(unittest.TestCase):
    def test_agreement_across_lists_beats_a_single_first_place(self):
        dense = RankedList("dense", [("solo", 0.9), ("agreed", 0.5), ("x", 0.4)])
        lexical = RankedList("lexical", [("y", 9.0), ("agreed", 8.0), ("z", 7.0)])
        fused = reciprocal_rank_fusion([dense, lexical], k=60)
        self.assertEqual(fused[0][0], "agreed")

    def test_components_are_preserved_for_debugging(self):
        fused = reciprocal_rank_fusion(
            [RankedList("dense", [("a", 0.5)]), RankedList("lexical", [("a", 3.0)])])
        components = fused[0][2]
        self.assertEqual(components["dense_rank"], 1.0)
        self.assertEqual(components["lexical_score"], 3.0)

    def test_mmr_keeps_the_best_result_first(self):
        candidates = [("a", 0.9), ("a2", 0.88), ("b", 0.5)]
        tokens = {"a": ["x", "y"], "a2": ["x", "y"], "b": ["p", "q"]}
        selected = mmr_select(candidates, lambda i, j: jaccard(tokens[i], tokens[j]), k=2)
        self.assertEqual(selected[0], "a")
        self.assertEqual(selected[1], "b", "MMR kept a near-duplicate over a diverse result")


class StoreTest(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.pipeline = build_index(self.store)
        self.addCleanup(self.store.close)

    def test_index_is_fully_covered(self):
        stats = self.store.stats()
        self.assertEqual(stats["documents"], len(CORPUS))
        self.assertEqual(stats["coverage"], 1.0)
        self.assertGreaterEqual(stats["chunks"], len(CORPUS))

    def test_lexical_search_finds_exact_terms(self):
        hits = self.store.search_lexical("BM25 inverse document frequency", k=5)
        self.assertTrue(hits)
        chunks = self.store.get_chunks([hits[0][0]])
        self.assertIn("BM25", chunks[hits[0][0]].text)

    def test_lexical_scores_are_higher_is_better(self):
        hits = self.store.search_lexical("chunking passages overlap", k=5)
        self.assertEqual(hits, sorted(hits, key=lambda h: h[1], reverse=True))

    def test_replacing_chunks_removes_the_old_ones(self):
        document = self.store.all_documents()[0]
        before = self.store.chunk_count()
        original = len([c for c in self.store.all_chunks() if c.doc_id == document.doc_id])
        self.store.replace_chunks(document.doc_id, [])
        self.assertEqual(self.store.chunk_count(), before - original)
        # And the removed chunks are gone from the lexical index too, not just
        # the table - an orphaned FTS row keeps citing text that no longer exists.
        for chunk_id, _ in self.store.search_lexical("retrieval augmented", k=10):
            self.assertNotEqual(self.store.get_chunks([chunk_id])[chunk_id].doc_id,
                                document.doc_id)

    def test_missing_embeddings_detects_a_changed_fingerprint(self):
        self.assertEqual(self.store.missing_embeddings(self.pipeline.embedder.fingerprint), [])
        stale = self.store.missing_embeddings("some-other-model:1536")
        self.assertEqual(len(stale), self.store.chunk_count())

    def test_source_filters_include_and_exclude(self):
        included = self.store.filter_chunk_ids({"source_system": "filesystem"})
        self.assertEqual(len(included), self.store.chunk_count())
        excluded = self.store.filter_chunk_ids({"exclude_source_system": ["filesystem"]})
        self.assertEqual(excluded, set())

    def test_idf_weights_rare_terms_above_common_ones(self):
        idf = self.store.idf_lookup()
        self.assertGreater(idf(stem("ibuprofen")), idf(stem("document")))

    def test_journal_records_and_reads_back(self):
        self.store.journal(1, "observe", {"documents_ingested": 4})
        entries = self.store.read_journal(cycle=1)
        self.assertEqual(entries[0]["phase"], "observe")
        self.assertEqual(entries[0]["documents_ingested"], 4)


class RetrievalTest(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.pipeline = build_index(self.store)
        self.retriever = HybridRetriever(self.store, self.pipeline.embedder)
        self.addCleanup(self.store.close)

    def test_both_arms_contribute(self):
        _, trace = self.retriever.retrieve("how are documents split into passages")
        self.assertGreater(trace.dense_hits, 0, "dense arm returned nothing")
        self.assertGreater(trace.lexical_hits, 0, "lexical arm returned nothing")

    def test_the_right_document_ranks_first(self):
        for query, expected in [
            ("how are documents split into passages", "chunking.md"),
            ("term frequency ranking for exact identifiers", "bm25.md"),
            ("what bounds a network loop", "budgets.md"),
        ]:
            with self.subTest(query=query):
                results, _ = self.retriever.retrieve(query, top_k=3)
                self.assertEqual(results[0].document.title, expected)

    def test_filters_restrict_results(self):
        target = self.store.all_documents()[0]
        results, trace = self.retriever.retrieve("documents", filters={"doc_ids": [target.doc_id]})
        self.assertTrue(results)
        self.assertTrue(all(r.chunk.doc_id == target.doc_id for r in results))

    def test_a_filter_matching_nothing_returns_nothing_and_says_why(self):
        results, trace = self.retriever.retrieve("documents",
                                                 filters={"source_system": "nonexistent"})
        self.assertEqual(results, [])
        self.assertIn("filter matched no chunks", trace.notes)

    def test_score_components_are_recorded(self):
        results, _ = self.retriever.retrieve("chunking overlap")
        components = results[0].components
        self.assertIn("rerank_relevance", components)
        self.assertIn("pre_rerank_score", components)


class PhraseScoringTest(unittest.TestCase):
    """The phrase component of relevance must not be satisfied by stopwords."""

    def test_a_stopword_run_scores_nothing(self):
        # "what is the boiling point of mercury" -> content terms only.
        query = tokenize("What is the boiling point of mercury?", stem_words=True)
        haystack = " ".join(tokenize(
            "The journal is the point: a cron job is silent about whether it worked.",
            stem_words=True))
        self.assertEqual(_longest_common_run(query, haystack), 0.0,
                         "a stopword run scored as a phrase match")

    def test_a_real_phrase_scores_fully(self):
        query = tokenize("reciprocal rank fusion", stem_words=True)
        haystack = " ".join(tokenize(
            "Results are combined with reciprocal rank fusion because the arms differ.",
            stem_words=True))
        self.assertEqual(_longest_common_run(query, haystack), 1.0)

    def test_a_single_shared_word_is_not_a_phrase(self):
        query = tokenize("boiling point mercury", stem_words=True)
        haystack = " ".join(tokenize("Past a point this measures less.", stem_words=True))
        self.assertEqual(_longest_common_run(query, haystack), 0.0,
                         "one shared word counted as proximity evidence")

    def test_a_partial_run_scores_proportionally(self):
        query = tokenize("reciprocal rank fusion diversity", stem_words=True)
        haystack = " ".join(tokenize("We use reciprocal rank fusion here.", stem_words=True))
        self.assertAlmostEqual(_longest_common_run(query, haystack), 3 / 4)


class GroundingTest(unittest.TestCase):
    def setUp(self):
        self.store = make_store()
        self.pipeline = build_index(self.store)
        retriever = HybridRetriever(self.store, self.pipeline.embedder)
        self.generator = AnswerGenerator(retriever, AnswerConfig(generator="extractive"))
        self.addCleanup(self.store.close)

    def test_an_answerable_question_is_answered_with_citations(self):
        answer = self.generator.answer("why are documents split into passages?")
        self.assertFalse(answer.abstained, answer.text)
        self.assertTrue(answer.citations)
        self.assertGreater(answer.confidence, 0.0)
        for citation in answer.citations:
            self.assertTrue(citation.uri.startswith("file:///corpus/"))

    def test_an_out_of_corpus_question_abstains(self):
        for question in ["What is the capital of France?",
                         "What is the recommended dosage of ibuprofen?",
                         "Who won the 1998 World Cup final?",
                         # Overlaps the corpus only on stopwords plus the common
                         # word "point"; must not clear the floor on that alone.
                         "What is the boiling point of mercury?"]:
            with self.subTest(question=question):
                answer = self.generator.answer(question)
                self.assertTrue(answer.abstained,
                                f"answered out-of-corpus question: {answer.text[:120]}")
                self.assertEqual(answer.confidence, 0.0)

    def test_every_citation_marker_resolves_to_a_retrieved_chunk(self):
        answer = self.generator.answer("what does BM25 score?")
        retrieved = {r.chunk.chunk_id for r in answer.retrieved}
        for citation in answer.citations:
            self.assertIn(citation.chunk_id, retrieved)

    def test_invalid_markers_are_stripped_not_shipped(self):
        available = [Citation(1, "c1", "d1", "T", "file:///t", "q", 0.5)]
        check = verify("Grounded claim here [1]. Invented claim here [7].", available)
        self.assertEqual(check.invalid_markers, [7])
        self.assertNotIn("[7]", check.text)
        self.assertIn("[1]", check.text)

    def test_coverage_counts_only_claim_sentences(self):
        available = [Citation(1, "c1", "d1", "T", "file:///t", "q", 0.5)]
        check = verify("- a bullet\nThe system stores every vector in one file [1].", available)
        self.assertEqual(check.coverage, 1.0)

    def test_markers_are_assigned_in_rank_order(self):
        results, _ = self.generator.retriever.retrieve("chunking", top_k=3)
        citations = build_citations(results)
        self.assertEqual([c.marker for c in citations], [1, 2, 3])
        self.assertEqual(citations[0].chunk_id, results[0].chunk.chunk_id)


class RedactionTest(unittest.TestCase):
    def test_credential_shapes_are_redacted(self):
        blob = ("token ghp_" + "A" * 20 + "\nkey sk-ant-" + "b" * 30
                + "\napi_key = 'supersecretvalue123'\nAuthorization: Bearer " + "c" * 30)
        cleaned = redact_secrets(blob)
        self.assertNotIn("ghp_AAAA", cleaned)
        self.assertNotIn("sk-ant-bbb", cleaned)
        self.assertNotIn("supersecretvalue123", cleaned)
        self.assertIn("<redacted", cleaned)

    def test_ordinary_text_is_untouched(self):
        text = "The retriever fuses two ranked lists with reciprocal rank fusion."
        self.assertEqual(redact_secrets(text), text)

    def test_normalize_redacts_before_a_document_is_created(self):
        raw = RawDocument("fs", "x", "file:///x", "x", "leak ghp_" + "Z" * 20)
        self.assertNotIn("ghp_ZZZ", normalize(raw).text)


if __name__ == "__main__":
    unittest.main()
