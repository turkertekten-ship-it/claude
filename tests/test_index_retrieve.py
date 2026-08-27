"""Tests for persistence and hybrid retrieval.

Bias throughout: prove the failure modes. Anyone can watch BM25 return the
document containing the query word. What is worth a test is what happens when
the transaction dies halfway, the embedder has no API key, the index outlives
the rows it points at, the query is Turkish, or numpy is installed on one
machine and not the other.

No network, no numpy required. The accelerated vector path is exercised through
a minimal stand-in module so the "identical ordering" contract is actually
tested in an environment where numpy is absent.
"""

from __future__ import annotations

import json
import math
import random
import sqlite3
import tempfile
import threading
import unittest
from array import array
from pathlib import Path
from unittest import mock

from oodarag.index.bm25 import BM25Index, tokenize_index_text, tr_lower, turkish_stem
from oodarag.index.store import Store, StoreError, decode_vector, encode_vector
from oodarag.index.vector import VectorIndex
from oodarag.models import Chunk, Document, ScoredChunk
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalFilters
from oodarag.retrieve.rerank import RerankWeights, explain, rerank, rerank_report
from oodarag.util.hashing import content_hash
from oodarag.util.text import tokenize_all

# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

DAY = 86400.0
NOW = 1_750_000_000.0


def make_doc(
    doc_id: str,
    text: str = "body",
    *,
    source: str = "web",
    title: str = "T",
    uri: str = "",
    updated: float = NOW,
    metadata: dict | None = None,
) -> Document:
    return Document(
        doc_id=doc_id,
        source_system=source,
        external_id=doc_id,
        uri=uri or f"https://example.test/{doc_id}",
        title=title,
        text=text,
        content_hash=content_hash(text, title),
        metadata=metadata or {},
        created_at=updated,
        updated_at=updated,
    )


def make_chunk(chunk_id: str, doc_id: str, text: str, ordinal: int = 0, **meta: object) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        ordinal=ordinal,
        text=text,
        context_header="",
        metadata=dict(meta),
    )


VOCAB = ("fon", "portföy", "risk", "vergi", "gayrimenkul", "denetim", "rapor", "yatırım")


def toy_embed(text: str) -> list[float]:
    """A deterministic bag-of-vocabulary embedder. No network, no model."""
    tokens = tokenize_index_text(text)
    present = set(tokens) | {turkish_stem(t) for t in tokens}
    return [1.0 if word in present else 0.0 for word in VOCAB]


class _FakeArray:
    def __init__(self, values: list[float]) -> None:
        self.values = list(values)

    def reshape(self, n: int, d: int) -> _FakeMatrix:
        return _FakeMatrix([self.values[i * d : (i + 1) * d] for i in range(n)])

    def astype(self, _dtype: object) -> _FakeArray:
        return self

    def tolist(self) -> list[float]:
        return list(self.values)


class _FakeMatrix:
    def __init__(self, rows: list[list[float]]) -> None:
        self.rows = rows

    def astype(self, _dtype: object) -> _FakeMatrix:
        return self

    def dot(self, other: _FakeArray) -> _FakeArray:
        q = other.values
        # Accumulate in the opposite order to the stdlib path on purpose: the
        # contract under test is that rounding, not luck, keeps the orderings
        # identical when the two disagree in the last bits.
        return _FakeArray(
            [
                sum(a * b for a, b in zip(row[::-1], q[::-1], strict=True))
                for row in self.rows
            ]
        )


class _FakeNumpy:
    """The five names oodarag.index.vector actually uses from numpy."""

    float32 = "f4"
    float64 = "f8"

    @staticmethod
    def frombuffer(buf: bytes, dtype: object = None) -> _FakeArray:
        arr = array("f")
        arr.frombytes(buf)
        return _FakeArray(list(arr))

    @staticmethod
    def array(values: list[float], dtype: object = None) -> _FakeArray:
        return _FakeArray(list(values))


# --------------------------------------------------------------------------


class StoreSchemaTest(unittest.TestCase):
    def test_opens_in_memory_and_reports_empty_stats(self) -> None:
        with Store(":memory:") as store:
            stats = store.stats()
        self.assertEqual(stats["schema_version"], 1)
        self.assertEqual(stats["documents"], 0)
        self.assertEqual(stats["chunks"], 0)
        self.assertEqual(stats["chunks_without_vectors"], 0)

    def test_file_store_enables_wal_and_survives_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "index.db"  # parent must be created for us
            store = Store(path)
            mode = store._conn.execute("PRAGMA journal_mode").fetchone()[0]
            self.assertEqual(mode.lower(), "wal")
            store.upsert_documents([make_doc("d1")])
            store.close()

            again = Store(path)
            self.addCleanup(again.close)
            self.assertIsNotNone(again.get_document("d1"))
            self.assertEqual(again.stats()["schema_version"], 1)

    def test_refuses_a_database_from_a_newer_schema(self) -> None:
        """A loud failure beats writing v1 rows into a v2 file."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.db"
            Store(path).close()
            conn = sqlite3.connect(path)
            conn.execute("UPDATE meta SET value='99' WHERE key='schema_version'")
            conn.commit()
            conn.close()
            with self.assertRaises(StoreError):
                Store(path)

    def test_using_a_closed_store_raises_rather_than_corrupting(self) -> None:
        store = Store(":memory:")
        store.close()
        store.close()  # idempotent
        with self.assertRaises(StoreError):
            store.get_document("d1")


class StoreWriteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)

    def test_unchanged_documents_are_skipped(self) -> None:
        docs = [make_doc("d1", "hello"), make_doc("d2", "world")]
        first = self.store.upsert_documents(docs)
        second = self.store.upsert_documents(docs)
        self.assertEqual((first.written, first.skipped), (2, 0))
        self.assertEqual((second.written, second.skipped), (0, 2))

    def test_a_moved_uri_counts_as_a_change_even_with_identical_text(self) -> None:
        self.store.upsert_documents([make_doc("d1", "same", uri="https://a.test/x")])
        report = self.store.upsert_documents([make_doc("d1", "same", uri="https://b.test/x")])
        self.assertEqual(report.written, 1)
        doc = self.store.get_document("d1")
        assert doc is not None
        self.assertEqual(doc.uri, "https://b.test/x")

    def test_chunk_set_is_idempotent_and_content_hash_guarded(self) -> None:
        self.store.upsert_documents([make_doc("d1")])
        chunks = [make_chunk(f"c{i}", "d1", f"chunk {i}", i) for i in range(3)]
        first = self.store.upsert_chunks(chunks)
        second = self.store.upsert_chunks(chunks)
        self.assertEqual(first.written, 3)
        self.assertEqual((second.written, second.skipped), (0, 3))
        self.assertEqual(len(list(self.store.iter_chunks("d1"))), 3)

    def test_changing_the_embedding_model_invalidates_the_guard(self) -> None:
        self.store.upsert_documents([make_doc("d1")])
        chunks = [make_chunk("c0", "d1", "text")]
        vecs = {"c0": [0.1, 0.2]}
        self.store.upsert_chunks(chunks, vecs, model="v1")
        again = self.store.upsert_chunks(chunks, vecs, model="v1")
        self.assertEqual(again.skipped, 1)
        switched = self.store.upsert_chunks(chunks, vecs, model="v2")
        self.assertEqual(switched.written, 1)
        self.assertEqual(switched.vectors, 1)

    def test_rechunking_replaces_the_whole_set_not_just_the_overlap(self) -> None:
        self.store.upsert_documents([make_doc("d1")])
        self.store.upsert_chunks([make_chunk(f"c{i}", "d1", f"old {i}", i) for i in range(4)])
        self.store.upsert_chunks([make_chunk("n0", "d1", "new 0", 0)])
        ids = [c.chunk_id for c in self.store.iter_chunks("d1")]
        self.assertEqual(ids, ["n0"])

    def test_a_crash_mid_index_leaves_the_previous_chunk_set_intact(self) -> None:
        """The whole reason this store is transactional."""
        self.store.upsert_documents([make_doc("d1")])
        original = [make_chunk(f"c{i}", "d1", f"old {i}", i) for i in range(3)]
        self.store.upsert_chunks(original, model="v1")

        replacement = [make_chunk(f"n{i}", "d1", f"new {i}", i) for i in range(3)]
        vectors = {c.chunk_id: [0.5, 0.5] for c in replacement}
        calls = {"n": 0}

        def explode(vec: object) -> bytes:
            calls["n"] += 1
            if calls["n"] >= 2:
                raise OSError("disk went away")
            return encode_vector(vec)  # type: ignore[arg-type]

        with mock.patch("oodarag.index.store.encode_vector", side_effect=explode):
            with self.assertRaises(OSError):
                self.store.upsert_chunks(replacement, vectors, model="v2")

        surviving = [c.chunk_id for c in self.store.iter_chunks("d1")]
        self.assertEqual(surviving, ["c0", "c1", "c2"])
        self.assertEqual(self.store.stats()["vectors"], 0)
        # and the store is still usable: the transaction depth was reset
        self.store.upsert_chunks(replacement, vectors, model="v2")
        self.assertEqual([c.chunk_id for c in self.store.iter_chunks("d1")], ["n0", "n1", "n2"])

    def test_orphan_chunks_are_dropped_not_raised(self) -> None:
        report = self.store.upsert_chunks([make_chunk("c0", "ghost", "text")])
        self.assertEqual(report.orphaned, 1)
        self.assertEqual(report.written, 0)
        self.assertIsNone(self.store.get_chunk("c0"))

    def test_put_vector_on_a_missing_chunk_returns_false(self) -> None:
        self.assertFalse(self.store.put_vector("nope", [1.0, 2.0]))

    def test_delete_document_cascades_and_is_replay_safe(self) -> None:
        self.store.upsert_documents([make_doc("d1"), make_doc("d2")])
        self.store.upsert_chunks(
            [make_chunk("c0", "d1", "a", 0), make_chunk("c1", "d1", "b", 1),
             make_chunk("c2", "d2", "c", 0)],
            {"c0": [1.0, 0.0], "c1": [0.0, 1.0], "c2": [1.0, 1.0]},
        )
        self.assertEqual(self.store.delete_document("d1"), 2)
        self.assertIsNone(self.store.get_document("d1"))
        self.assertEqual([c.chunk_id for c in self.store.iter_chunks()], ["c2"])
        self.assertEqual(self.store.stats()["vectors"], 1)
        self.assertEqual(self.store.delete_document("d1"), 0)  # replay is a no-op

    def test_vectors_round_trip_at_float32_precision(self) -> None:
        self.store.upsert_documents([make_doc("d1")])
        vec = [0.1, -2.5, 3.14159265, 0.0]
        self.store.upsert_chunks([make_chunk("c0", "d1", "x")], {"c0": vec})
        got = self.store.get_vector("c0")
        assert got is not None
        for a, b in zip(vec, list(got), strict=True):
            self.assertAlmostEqual(a, b, places=6)

    def test_nonfinite_vector_components_are_zeroed_not_stored(self) -> None:
        blob = encode_vector([1.0, float("nan"), float("inf"), -0.5])
        self.assertEqual(list(decode_vector(blob)), [1.0, 0.0, 0.0, -0.5])

    def test_truncated_vector_blob_decodes_to_whole_dimensions(self) -> None:
        blob = encode_vector([1.0, 2.0, 3.0])[:-1]
        self.assertEqual(list(decode_vector(blob)), [1.0, 2.0])

    def test_byteswapped_vectors_are_recovered(self) -> None:
        blob = encode_vector([1.0, 2.0])
        swapped = array("f", [1.0, 2.0])
        swapped.byteswap()
        self.assertEqual(list(decode_vector(swapped.tobytes(), swap=True)), [1.0, 2.0])
        self.assertEqual(list(decode_vector(blob, swap=False)), [1.0, 2.0])

    def test_iter_vectors_skips_vectors_whose_chunk_is_gone(self) -> None:
        self.store.upsert_documents([make_doc("d1")])
        self.store.upsert_chunks([make_chunk("c0", "d1", "x")], {"c0": [1.0, 0.0]})
        self.store.upsert_chunks([make_chunk("c1", "d1", "y")], model="later")
        self.assertEqual([cid for cid, _ in self.store.iter_vectors()], [])

    def test_a_paused_iterator_does_not_block_a_writer(self) -> None:
        """Holding the connection lock across a yield would deadlock the indexer."""
        self.store.upsert_documents([make_doc("d1")])
        self.store.upsert_chunks([make_chunk(f"c{i}", "d1", f"t{i}", i) for i in range(5)])
        walk = self.store.iter_chunks(batch_size=1)
        self.addCleanup(walk.close)
        next(walk)  # suspended mid-walk with a live cursor

        finished = threading.Event()

        def writer() -> None:
            self.store.upsert_documents([make_doc("d2")])
            finished.set()

        thread = threading.Thread(target=writer, daemon=True)
        thread.start()
        thread.join(timeout=5.0)
        self.assertTrue(finished.is_set(), "a writer blocked behind a paused iterator")

    def test_blobs_round_trip_and_missing_names_return_none(self) -> None:
        self.assertIsNone(self.store.get_blob("absent"))
        self.store.put_blob("bm25", b"\x00\x01payload", {"docs": 3})
        blob = self.store.get_blob("bm25")
        assert blob is not None
        self.assertEqual(blob.payload, b"\x00\x01payload")
        self.assertEqual(blob.meta["docs"], 3)
        self.assertTrue(self.store.delete_blob("bm25"))
        self.assertFalse(self.store.delete_blob("bm25"))

    def test_exotic_metadata_degrades_to_a_string_instead_of_failing(self) -> None:
        self.store.upsert_documents([make_doc("d1", metadata={"weird": object()})])
        got = self.store.get_document("d1")
        assert got is not None
        self.assertIn("object object at", got.metadata["weird"])

    def test_circular_metadata_does_not_take_down_the_write(self) -> None:
        loop: dict = {}
        loop["self"] = loop  # json.dumps refuses this outright
        self.store.upsert_documents([make_doc("d2", metadata=loop)])
        got = self.store.get_document("d2")
        assert got is not None
        self.assertIn("_unserializable", got.metadata)


class StoreFilterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)
        self.store.upsert_documents(
            [
                make_doc("spk1", source="spk", updated=NOW,
                         metadata={"lang": "tr", "kind": "bulletin"}),
                make_doc("web1", source="web", updated=NOW - 400 * DAY, metadata={"lang": "en"}),
                make_doc("spk2", source="spk", updated=NOW - 10 * DAY, metadata={"lang": "tr"}),
            ]
        )
        self.store.upsert_chunks(
            [
                make_chunk("a", "spk1", "alpha"),
                make_chunk("b", "web1", "beta"),
                make_chunk("c", "spk2", "gamma"),
            ]
        )

    def test_filter_by_source_system(self) -> None:
        self.assertEqual(self.store.find_chunk_ids(source_system="spk"), {"a", "c"})
        self.assertEqual(self.store.find_chunk_ids(source_system=["web", "spk"]), {"a", "b", "c"})

    def test_filter_by_document_metadata_key(self) -> None:
        self.assertEqual(self.store.find_chunk_ids(metadata={"lang": "tr"}), {"a", "c"})
        self.assertEqual(self.store.find_chunk_ids(metadata={"kind": "bulletin"}), {"a"})
        self.assertEqual(
            self.store.find_chunk_ids(metadata={"lang": ["tr", "en"]}), {"a", "b", "c"}
        )
        self.assertEqual(self.store.find_chunk_ids(metadata={"lang": "de"}), set())

    def test_filter_by_recency_window(self) -> None:
        self.assertEqual(self.store.find_chunk_ids(updated_after=NOW - 30 * DAY), {"a", "c"})
        self.assertEqual(self.store.find_chunk_ids(updated_before=NOW - 30 * DAY), {"b"})

    def test_filters_compose(self) -> None:
        self.assertEqual(
            self.store.find_chunk_ids(source_system="spk", updated_after=NOW - DAY), {"a"}
        )


# --------------------------------------------------------------------------


class TurkishTokenisationTest(unittest.TestCase):
    def test_ascii_path_is_byte_identical_to_tokenize_all(self) -> None:
        text = "Chunking the snake_case docs at dotted.path/v2 -- 42 times."
        self.assertEqual(tokenize_index_text(text), tokenize_all(text))

    def test_turkish_characters_survive_tokenisation(self) -> None:
        """util.text.tokenize_all splits `değerleme` into `de` + `erleme`."""
        self.assertEqual(tokenize_index_text("değerleme esasları"), ["değerleme", "esasları"])
        self.assertNotEqual(tokenize_index_text("değerleme"), tokenize_all("değerleme"))
        self.assertEqual(tokenize_index_text("İstanbul"), ["istanbul"])
        self.assertEqual(tokenize_index_text("portföy yönetimi"), ["portföy", "yönetimi"])

    def test_dotted_i_lowercases_to_a_single_code_point(self) -> None:
        self.assertEqual(tr_lower("İSTANBUL"), "ıstanbul".replace("ı", "i", 1))
        self.assertEqual(len(tr_lower("İ")), 1)

    def test_turkish_casing_is_not_applied_to_evidently_english_tokens(self) -> None:
        self.assertEqual(tr_lower("IBM"), "ibm")
        self.assertEqual(tr_lower("ILAÇ"), "ılaç")

    def test_stemmer_reduces_the_inflections_that_matter(self) -> None:
        for surface in ("fon", "fonun", "fonlar", "fonları", "fonların", "fonlarının",
                        "fonda", "fondan", "fona", "fonu"):
            self.assertEqual(turkish_stem(surface), "fon", surface)

    def test_stemmer_does_not_cut_across_a_morpheme_boundary(self) -> None:
        """The precision argument against character n-grams, as a test."""
        self.assertEqual(turkish_stem("fonksiyon"), "fonksiyon")
        self.assertNotEqual(turkish_stem("fonksiyon"), "fon")

    def test_stemmer_leaves_identifiers_and_short_tokens_alone(self) -> None:
        self.assertEqual(turkish_stem("iii-52.1"), "iii-52.1")
        self.assertEqual(turkish_stem("api"), "api")
        self.assertEqual(turkish_stem("v2"), "v2")


class BM25Test(unittest.TestCase):
    def setUp(self) -> None:
        self.chunks = [
            make_chunk("c1", "d1", "Fonun portföy değeri artmıştır."),
            make_chunk("c2", "d1", "Fonlar için değerleme esasları belirlendi.", 1),
            make_chunk("c3", "d2", "Bu bir fonksiyon tanımıdır, konuyla ilgisi yoktur."),
            make_chunk("c4", "d2", "Vergi istisnası hakkında genel bilgi.", 1),
        ]
        self.index = BM25Index().build(self.chunks)

    def test_a_query_for_fon_hits_the_inflected_forms(self) -> None:
        hits = dict(self.index.search("fon", k=10))
        self.assertIn("c1", hits)  # fonun
        self.assertIn("c2", hits)  # fonlar

    def test_fonksiyon_is_not_retrieved_for_fon(self) -> None:
        hits = dict(self.index.search("fon", k=10))
        self.assertNotIn("c3", hits)

    def test_exact_surface_match_outranks_a_morphological_one(self) -> None:
        index = BM25Index().build(
            [
                make_chunk("exact", "d", "fon fon fon"),
                make_chunk("inflected", "d", "fonun fonun fonun"),
            ]
        )
        ranked = [cid for cid, _ in index.search("fon", k=5)]
        self.assertEqual(ranked[0], "exact")
        self.assertIn("inflected", ranked)

    def test_empty_and_unknown_queries_return_nothing(self) -> None:
        self.assertEqual(self.index.search(""), [])
        self.assertEqual(self.index.search("   "), [])
        self.assertEqual(self.index.search("kriptopara"), [])
        self.assertEqual(self.index.search("fon", k=0), [])
        self.assertEqual(BM25Index().search("fon"), [])

    def test_idf_never_goes_negative_for_a_ubiquitous_term(self) -> None:
        index = BM25Index().build(
            [make_chunk(f"c{i}", "d", "the same words here") for i in range(5)]
        )
        for _, score in index.search("the same words here", k=5):
            self.assertGreaterEqual(score, 0.0)

    def test_allowed_set_restricts_results_inside_the_scoring_loop(self) -> None:
        hits = self.index.search("fon", k=10, allowed={"c2"})
        self.assertEqual([cid for cid, _ in hits], ["c2"])
        self.assertEqual(self.index.search("fon", k=10, allowed=set()), [])

    def test_delete_tombstones_and_compact_reclaims(self) -> None:
        self.assertTrue(self.index.delete("c1"))
        self.assertFalse(self.index.delete("c1"))
        self.assertNotIn("c1", [cid for cid, _ in self.index.search("fon", k=10)])
        self.assertEqual(len(self.index), 3)
        stats = self.index.stats()
        self.assertEqual(stats["tombstones"], 1)
        self.index.compact()
        self.assertEqual(self.index.stats()["tombstones"], 0)
        self.assertEqual(len(self.index), 3)

    def test_readding_a_chunk_id_does_not_double_count_it(self) -> None:
        index = BM25Index().build([make_chunk("c", "d", "fon")])
        index.add(make_chunk("c", "d", "vergi"))
        self.assertEqual(len(index), 1)
        self.assertEqual(index.search("fon"), [])
        self.assertEqual([cid for cid, _ in index.search("vergi")], ["c"])

    def test_blank_chunks_are_not_indexed(self) -> None:
        index = BM25Index().build([make_chunk("blank", "d", "   ")])
        self.assertEqual(len(index), 0)

    def test_results_are_deterministic_across_rebuilds(self) -> None:
        other = BM25Index().build(self.chunks)
        self.assertEqual(self.index.search("fon değerleme", k=10),
                         other.search("fon değerleme", k=10))


class BM25PersistenceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)
        self.store.upsert_documents([make_doc("d1", source="spk")])
        self.chunks = [
            make_chunk("c1", "d1", "Fonun portföy değeri artmıştır.", 0),
            make_chunk("c2", "d1", "Vergi istisnası uygulanır.", 1),
        ]
        self.store.upsert_chunks(self.chunks)

    def test_round_trip_through_the_store_preserves_every_score(self) -> None:
        built = BM25Index().build_from_store(self.store)
        built.save(self.store)
        loaded = BM25Index.load(self.store)
        assert loaded is not None
        self.assertEqual(len(loaded), len(built))
        for query in ("fon", "vergi", "portföy değeri"):
            self.assertEqual(built.search(query, k=10), loaded.search(query, k=10), query)

    def test_a_corrupt_blob_returns_none_rather_than_raising(self) -> None:
        self.store.put_blob("bm25", b"not a zlib stream at all")
        self.assertIsNone(BM25Index.load(self.store))

    def test_a_blob_from_an_unknown_format_is_refused(self) -> None:
        import zlib

        payload = zlib.compress(json.dumps({"format": 999}).encode())
        self.store.put_blob("bm25", payload)
        self.assertIsNone(BM25Index.load(self.store))

    def test_a_structurally_broken_blob_is_refused(self) -> None:
        import zlib

        payload = zlib.compress(
            json.dumps({"format": 1, "ids": ["a", "b"], "lengths": [1.0], "live": [1, 1],
                        "postings": {}}).encode()
        )
        self.store.put_blob("bm25", payload)
        self.assertIsNone(BM25Index.load(self.store))

    def test_ensure_builds_when_absent_and_rebuilds_when_stale(self) -> None:
        index = BM25Index.ensure(self.store)
        self.assertEqual(len(index), 2)
        self.assertIsNotNone(self.store.get_blob("bm25"))

        self.store.upsert_documents([make_doc("d2")])
        self.store.upsert_chunks([make_chunk("c3", "d2", "gayrimenkul yatırım fonu")])
        refreshed = BM25Index.ensure(self.store)
        self.assertEqual(len(refreshed), 3)
        self.assertIn("c3", refreshed)

    def test_ensure_survives_a_store_that_will_not_accept_the_blob(self) -> None:
        broken = sqlite3.OperationalError("attempt to write a readonly database")
        with mock.patch.object(Store, "put_blob", side_effect=broken):
            index = BM25Index.ensure(self.store)
        self.assertEqual(len(index), 2)


# --------------------------------------------------------------------------


class VectorIndexTest(unittest.TestCase):
    def test_empty_index_returns_nothing(self) -> None:
        self.assertEqual(VectorIndex().search([1.0, 0.0]), [])

    def test_dimension_mismatch_never_raises(self) -> None:
        index = VectorIndex()
        index.add("a", [1.0, 0.0, 0.0])
        self.assertFalse(index.add("b", [1.0, 0.0]))
        self.assertEqual(index.search([1.0, 0.0]), [])
        self.assertEqual(index.search([1.0, 0.0, 0.0, 0.0]), [])
        self.assertEqual(index.stats()["rejected_dim"], 1)
        self.assertEqual(len(index), 1)

    def test_degenerate_queries_return_nothing(self) -> None:
        index = VectorIndex()
        index.add("a", [1.0, 0.0])
        self.assertEqual(index.search([]), [])
        self.assertEqual(index.search([0.0, 0.0]), [])
        self.assertEqual(index.search([1.0, 0.0], k=0), [])

    def test_zero_vectors_are_stored_but_never_win(self) -> None:
        index = VectorIndex()
        self.assertTrue(index.add("zero", [0.0, 0.0]))
        index.add("real", [1.0, 0.0])
        self.assertEqual(index.search([1.0, 0.0], k=2)[0][0], "real")
        self.assertEqual(index.stats()["rejected_zero"], 1)

    def test_cosine_is_clamped_and_ordered(self) -> None:
        index = VectorIndex()
        index.add("same", [1.0, 0.0])
        index.add("orth", [0.0, 1.0])
        index.add("opposite", [-1.0, 0.0])
        hits = index.search([2.0, 0.0], k=3)
        self.assertEqual([cid for cid, _ in hits], ["same", "orth", "opposite"])
        self.assertLessEqual(hits[0][1], 1.0)
        self.assertAlmostEqual(hits[0][1], 1.0, places=6)
        self.assertGreaterEqual(hits[-1][1], -1.0)

    def test_remove_and_replace(self) -> None:
        index = VectorIndex()
        index.add("a", [1.0, 0.0])
        index.add("b", [0.0, 1.0])
        index.add("a", [0.0, 1.0])  # replace, not append
        self.assertEqual(len(index), 2)
        self.assertTrue(index.remove("a"))
        self.assertFalse(index.remove("a"))
        self.assertEqual([cid for cid, _ in index.search([0.0, 1.0], k=5)], ["b"])

    def test_allowed_restricts_results(self) -> None:
        index = VectorIndex()
        index.add("a", [1.0, 0.0])
        index.add("b", [0.9, 0.1])
        self.assertEqual([cid for cid, _ in index.search([1.0, 0.0], allowed={"b"})], ["b"])

    def test_numpy_path_gives_identical_output_to_the_stdlib_path(self) -> None:
        """The whole point of the optional accelerator: same answers, faster."""
        rng = random.Random(20260827)
        vectors = [
            (f"c{i}", [rng.uniform(-1.0, 1.0) for _ in range(16)]) for i in range(40)
        ]
        # A pair of near-duplicates makes near-ties, which is where the two
        # summation orders would otherwise disagree.
        vectors.append(("dup1", list(vectors[0][1])))
        vectors.append(("dup2", [v + 1e-12 for v in vectors[0][1]]))

        plain = VectorIndex(use_numpy=False)
        accel = VectorIndex(use_numpy=True, numpy_module=_FakeNumpy(), numpy_threshold=1)
        plain.add_many(vectors)
        accel.add_many(vectors)
        self.assertFalse(plain.stats()["numpy"])
        self.assertTrue(accel.stats()["numpy"])

        for _ in range(20):
            query = [rng.uniform(-1.0, 1.0) for _ in range(16)]
            self.assertEqual(plain.search(query, k=10), accel.search(query, k=10))

    def test_a_broken_numpy_falls_back_instead_of_raising(self) -> None:
        class Exploding:
            float32 = "f4"
            float64 = "f8"

            @staticmethod
            def frombuffer(*_a: object, **_kw: object) -> None:
                raise ValueError("buffer is the wrong shape")

        index = VectorIndex(use_numpy=True, numpy_module=Exploding(), numpy_threshold=1)
        index.add("a", [1.0, 0.0])
        index.add("b", [0.0, 1.0])
        self.assertEqual([cid for cid, _ in index.search([1.0, 0.0], k=2)], ["a", "b"])

    def test_requesting_numpy_when_absent_degrades_silently(self) -> None:
        index = VectorIndex(use_numpy=True, numpy_module=None, numpy_threshold=1)
        index.add("a", [1.0, 0.0])
        self.assertEqual([cid for cid, _ in index.search([1.0, 0.0])], ["a"])

    def test_build_from_store_loads_every_live_vector(self) -> None:
        store = Store(":memory:")
        self.addCleanup(store.close)
        store.upsert_documents([make_doc("d1")])
        store.upsert_chunks(
            [make_chunk("c1", "d1", "a", 0), make_chunk("c2", "d1", "b", 1)],
            {"c1": [1.0, 0.0], "c2": [0.0, 1.0]},
        )
        index = VectorIndex.from_store(store)
        self.assertEqual(len(index), 2)
        self.assertEqual(index.dim, 2)
        self.assertEqual([cid for cid, _ in index.search([1.0, 0.0], k=1)], ["c1"])


# --------------------------------------------------------------------------


class HybridRetrieverTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = Store(":memory:")
        self.addCleanup(self.store.close)
        self.store.upsert_documents(
            [
                make_doc("spk1", source="spk", title="Bülten", updated=NOW,
                         metadata={"lang": "tr"}),
                make_doc("blog1", source="web", title="Blog", updated=NOW - 500 * DAY,
                         metadata={"lang": "tr"}),
                make_doc("gh1", source="github", title="README", updated=NOW - 5 * DAY,
                         metadata={"lang": "en"}),
            ]
        )
        chunks = [
            make_chunk("s1", "spk1", "Fonun portföy sınırlamaları güncellendi.", 0),
            make_chunk("s2", "spk1", "Vergi istisnası ve denetim raporu.", 1),
            make_chunk("b1", "blog1", "Fonlar hakkında genel bir yatırım yazısı.", 0),
            make_chunk("g1", "gh1", "risk model calibration in python", 0),
        ]
        self.chunks = chunks
        self.store.upsert_chunks(chunks, {c.chunk_id: toy_embed(c.indexed_text) for c in chunks})
        self.retriever = HybridRetriever.from_store(self.store, embedder=toy_embed)

    def test_components_carry_both_arms_and_both_ranks(self) -> None:
        results = self.retriever.retrieve("fon portföy", k=4)
        self.assertTrue(results)
        for result in results:
            for key in ("bm25", "dense", "rrf", "rank_bm25", "rank_dense"):
                self.assertIn(key, result.components, key)
            self.assertIsNotNone(result.document)
            self.assertAlmostEqual(result.score, result.components["rrf"], places=9)

    def test_a_chunk_only_one_arm_found_records_rank_zero_for_the_other(self) -> None:
        results = self.retriever.retrieve("fon portföy", k=4)
        by_id = {r.chunk.chunk_id: r for r in results}
        self.assertIn("s1", by_id)
        for result in results:
            if result.components["rank_bm25"] == 0.0:
                self.assertEqual(result.components["bm25"], 0.0)
            if result.components["rank_dense"] == 0.0:
                self.assertEqual(result.components["dense"], 0.0)

    def test_rrf_arithmetic_is_what_it_claims(self) -> None:
        fused = self.retriever._fuse([("x", 9.0)], [("x", 0.9)])
        self.assertEqual(fused[0][0], "x")
        self.assertAlmostEqual(fused[0][1]["rrf"], 2.0 / 61.0, places=12)
        self.assertEqual(fused[0][1]["rank_bm25"], 1.0)
        self.assertEqual(fused[0][1]["rank_dense"], 1.0)

    def test_no_embedder_leaves_the_lexical_arm_answering_alone(self) -> None:
        lexical_only = HybridRetriever.from_store(self.store, embedder=None)
        results = lexical_only.retrieve("fon", k=3)
        self.assertTrue(results)
        self.assertTrue(all(r.components["rank_dense"] == 0.0 for r in results))

    def test_an_embedder_that_throws_degrades_to_the_lexical_arm(self) -> None:
        def broken(_text: str) -> list[float]:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        retriever = HybridRetriever.from_store(self.store, embedder=broken)
        results = retriever.retrieve("fon", k=3)
        self.assertTrue(results)
        self.assertTrue(all(r.components["dense"] == 0.0 for r in results))

    def test_an_embedder_returning_nothing_is_not_fatal(self) -> None:
        retriever = HybridRetriever.from_store(self.store, embedder=lambda _t: [])
        self.assertTrue(retriever.retrieve("fon", k=3))

    def test_a_batch_style_embedder_is_accepted(self) -> None:
        class Batch:
            def embed(self, texts: list[str]) -> list[list[float]]:
                return [toy_embed(t) for t in texts]

        retriever = HybridRetriever.from_store(self.store, embedder=Batch())
        results = retriever.retrieve("fon portföy", k=4)
        self.assertTrue(any(r.components["rank_dense"] > 0 for r in results))

    def test_an_unusable_embedder_is_refused_at_construction(self) -> None:
        retriever = HybridRetriever.from_store(self.store, embedder=object())
        self.assertTrue(retriever.retrieve("fon", k=2))  # lexical arm still works

    def test_empty_query_returns_nothing(self) -> None:
        self.assertEqual(self.retriever.retrieve("   "), [])
        self.assertEqual(self.retriever.retrieve(""), [])

    def test_filter_by_source_system(self) -> None:
        results = self.retriever.retrieve("fon", k=5, filters={"source_system": "spk"})
        self.assertTrue(results)
        self.assertTrue(all(r.document and r.document.source_system == "spk" for r in results))

    def test_filter_by_document_metadata(self) -> None:
        results = self.retriever.retrieve("risk fon", k=5, filters={"metadata": {"lang": "en"}})
        self.assertEqual([r.chunk.chunk_id for r in results], ["g1"])

    def test_filter_by_recency_window(self) -> None:
        results = self.retriever.retrieve(
            "fon", k=5, filters={"within_days": 30}, now=NOW
        )
        self.assertTrue(results)
        self.assertNotIn("b1", [r.chunk.chunk_id for r in results])

    def test_a_filter_that_matches_nothing_returns_nothing(self) -> None:
        self.assertEqual(self.retriever.retrieve("fon", filters={"source_system": "kap"}), [])

    def test_unknown_filter_keys_are_dropped_not_fatal(self) -> None:
        results = self.retriever.retrieve("fon", k=3, filters={"nonsense": "x"})
        self.assertTrue(results)

    def test_a_filter_backend_failure_fails_closed(self) -> None:
        """Widening to the whole corpus would leak documents the caller excluded."""
        with mock.patch.object(Store, "find_chunk_ids", side_effect=sqlite3.OperationalError("x")):
            self.assertEqual(self.retriever.retrieve("fon", filters={"source_system": "spk"}), [])

    def test_filters_coerce_accepts_aliases_and_rejects_junk(self) -> None:
        parsed = RetrievalFilters.coerce({"source": "spk", "days": 7, "doc_id": "d1"})
        assert parsed is not None
        self.assertEqual(parsed.source_system, ("spk",))
        self.assertEqual(parsed.within_days, 7.0)
        self.assertEqual(parsed.doc_ids, ("d1",))
        self.assertIsNone(RetrievalFilters.coerce(None))
        self.assertIsNone(RetrievalFilters.coerce(["not", "a", "mapping"]))
        self.assertTrue(RetrievalFilters().is_empty)

    def test_a_stale_index_pointing_at_deleted_chunks_backfills(self) -> None:
        """The index outlives the rows. k results must still be k results."""
        stale = HybridRetriever.from_store(self.store, embedder=toy_embed)
        self.store.delete_document("spk1")  # index still holds s1 and s2
        results = stale.retrieve("fon yatırım risk vergi", k=2)
        ids = [r.chunk.chunk_id for r in results]
        self.assertEqual(len(ids), 2)
        self.assertNotIn("s1", ids)
        self.assertNotIn("s2", ids)

    def test_both_arms_empty_returns_nothing(self) -> None:
        empty = Store(":memory:")
        self.addCleanup(empty.close)
        retriever = HybridRetriever.from_store(empty, embedder=toy_embed)
        self.assertEqual(retriever.retrieve("fon"), [])

    def test_stats_reports_both_arms(self) -> None:
        stats = self.retriever.stats()
        self.assertEqual(stats["bm25"]["documents"], 4)
        self.assertEqual(stats["vector"]["vectors"], 4)
        self.assertTrue(stats["embedder"])
        self.assertEqual(stats["rrf_k"], 60.0)


# --------------------------------------------------------------------------


class RerankTest(unittest.TestCase):
    def _scored(self, chunk: Chunk, score: float, doc: Document | None) -> ScoredChunk:
        return ScoredChunk(chunk=chunk, score=score, components={"rrf": score}, document=doc)

    def test_empty_input_is_empty_output(self) -> None:
        self.assertEqual(rerank("fon", []), [])

    def test_every_feature_is_written_into_components(self) -> None:
        doc = make_doc("d1", source="spk", updated=NOW - 10 * DAY)
        chunk = make_chunk("c1", "d1", "nitelikli yatırımcı tanımı")
        out = rerank("nitelikli yatırımcı", [self._scored(chunk, 0.03, doc)],
                     authority={"spk": 0.98}, now=NOW)
        components = out[0].components
        for key in ("pre_rerank", "rerank_base", "phrase", "coverage", "authority",
                    "recency", "age_days", "relevance", "duplicate_penalty",
                    "rerank_score", "rerank_rank"):
            self.assertIn(key, components, key)
        self.assertEqual(components["rrf"], 0.03)  # arm components survive
        self.assertAlmostEqual(components["pre_rerank"], 0.03)
        self.assertAlmostEqual(components["phrase"], 1.0)
        self.assertAlmostEqual(components["coverage"], 1.0)
        self.assertAlmostEqual(components["authority"], 0.98)
        self.assertAlmostEqual(components["age_days"], 10.0, places=3)

    def test_the_exact_phrase_beats_the_same_words_scattered(self) -> None:
        doc = make_doc("d1")
        phrase = make_chunk("phrase", "d1", "burada nitelikli yatırımcı tanımı yer alır")
        scattered = make_chunk(
            "scattered", "d1",
            "nitelikli bir sonuç elde edildi ve ayrıca yatırımcı sayısı arttı",
        )
        out = rerank(
            "nitelikli yatırımcı",
            [self._scored(scattered, 0.05, doc), self._scored(phrase, 0.05, doc)],
            now=NOW,
        )
        self.assertEqual(out[0].chunk.chunk_id, "phrase")
        self.assertGreater(out[0].components["phrase"], out[1].components["phrase"])

    def test_coverage_separates_on_topic_from_merely_nearby(self) -> None:
        doc = make_doc("d1")
        on_topic = make_chunk("on", "d1", "vergi istisnası ve portföy sınırlamaları")
        nearby = make_chunk("near", "d1", "genel ekonomik görünüm hakkında bir not")
        out = rerank("vergi istisnası portföy", [self._scored(nearby, 0.05, doc),
                                                 self._scored(on_topic, 0.05, doc)], now=NOW)
        self.assertEqual(out[0].chunk.chunk_id, "on")
        self.assertEqual(out[1].components["coverage"], 0.0)

    def test_authority_breaks_a_tie_and_unknown_sources_get_the_default(self) -> None:
        official = make_doc("o", source="resmigazete")
        blog = make_doc("b", source="randomblog")
        text = "portföy sınırlamaları değişti"
        out = rerank(
            "portföy sınırlamaları",
            [self._scored(make_chunk("blog", "b", text), 0.05, blog),
             self._scored(make_chunk("official", "o", text), 0.05, official)],
            authority={"resmigazete": 1.0},
            now=NOW,
            diversity=0.0,
        )
        self.assertEqual(out[0].chunk.chunk_id, "official")
        self.assertEqual(out[0].components["authority"], 1.0)
        self.assertEqual(out[1].components["authority"], 0.5)  # unmapped default

    def test_authority_outside_zero_to_one_is_clamped(self) -> None:
        doc = make_doc("d1", source="loud")
        out = rerank("fon", [self._scored(make_chunk("c", "d1", "fon"), 0.1, doc)],
                     authority={"loud": 99.0}, now=NOW)
        self.assertEqual(out[0].components["authority"], 1.0)

    def test_recency_decays_by_half_over_one_half_life(self) -> None:
        fresh = make_doc("f", updated=NOW)
        old = make_doc("o", updated=NOW - 180 * DAY)
        text = "vergi istisnası"
        out = rerank(
            "vergi istisnası",
            [self._scored(make_chunk("old", "o", text), 0.05, old),
             self._scored(make_chunk("fresh", "f", text), 0.05, fresh)],
            now=NOW, half_life_days=180.0, diversity=0.0,
        )
        self.assertEqual(out[0].chunk.chunk_id, "fresh")
        self.assertAlmostEqual(out[0].components["recency"], 1.0, places=4)
        self.assertAlmostEqual(out[1].components["recency"], 0.5, places=4)

    def test_recency_can_be_switched_off_for_a_corpus_of_statutes(self) -> None:
        old = make_doc("o", updated=NOW - 3650 * DAY)
        out = rerank("fon", [self._scored(make_chunk("c", "o", "fon"), 0.05, old)],
                     now=NOW, half_life_days=0.0)
        self.assertEqual(out[0].components["recency"], 1.0)

    def test_a_document_with_no_timestamp_is_neutral_not_stale(self) -> None:
        chunk = make_chunk("c", "orphan", "fon")
        out = rerank("fon", [self._scored(chunk, 0.05, None)], now=NOW)
        self.assertEqual(out[0].components["recency"], 0.5)
        self.assertEqual(out[0].components["age_days"], -1.0)

    def test_a_future_timestamp_does_not_produce_a_recency_above_one(self) -> None:
        doc = make_doc("d", updated=NOW + 90 * DAY)  # clock skew on a mirror
        out = rerank("fon", [self._scored(make_chunk("c", "d", "fon"), 0.05, doc)], now=NOW)
        self.assertEqual(out[0].components["recency"], 1.0)
        self.assertEqual(out[0].components["age_days"], 0.0)

    def test_near_duplicates_are_demoted_and_the_penalty_is_visible(self) -> None:
        """Eight mirrors of one paragraph is the most common bad result set."""
        text = "fonun portföy sınırlamaları hakkında ayrıntılı açıklama burada"
        distinct = "vergi istisnası konusunda ayrı bir portföy açıklaması"
        doc_a, doc_b, doc_c = make_doc("a"), make_doc("b"), make_doc("c")
        candidates = [
            self._scored(make_chunk("orig", "a", text), 0.050, doc_a),
            self._scored(make_chunk("mirror", "b", text), 0.049, doc_b),
            self._scored(make_chunk("other", "c", distinct), 0.048, doc_c),
        ]
        greedy = [s.chunk.chunk_id for s in rerank("portföy", candidates, now=NOW, diversity=0.0)]
        diverse = rerank("portföy", candidates, now=NOW, diversity=0.9)
        self.assertEqual(greedy, ["orig", "mirror", "other"])
        self.assertEqual([s.chunk.chunk_id for s in diverse], ["orig", "other", "mirror"])
        self.assertEqual(diverse[-1].components["duplicate_penalty"], 1.0)
        self.assertEqual(diverse[0].components["duplicate_penalty"], 0.0)

    def test_the_input_list_is_not_mutated(self) -> None:
        doc = make_doc("d1")
        original = self._scored(make_chunk("c", "d1", "fon"), 0.05, doc)
        rerank("fon", [original], now=NOW)
        self.assertEqual(original.score, 0.05)
        self.assertEqual(set(original.components), {"rrf"})

    def test_relevance_stays_inside_the_unit_interval(self) -> None:
        doc = make_doc("d1", source="spk", updated=NOW)
        out = rerank(
            "fon portföy vergi",
            [self._scored(make_chunk("c", "d1", "fon portföy vergi"), 0.05, doc)],
            authority={"spk": 1.0}, now=NOW,
        )
        self.assertLessEqual(out[0].components["relevance"], 1.0)
        self.assertGreaterEqual(out[0].components["relevance"], 0.0)

    def test_a_constant_fused_score_does_not_get_min_maxed_into_noise(self) -> None:
        doc = make_doc("d1")
        candidates = [
            self._scored(make_chunk(f"c{i}", "d1", f"fon {i}"), 0.05, doc) for i in range(3)
        ]
        out = rerank("fon", candidates, now=NOW)
        self.assertTrue(all(s.components["rerank_base"] == 1.0 for s in out))

    def test_an_empty_query_still_returns_the_candidates(self) -> None:
        doc = make_doc("d1")
        out = rerank("", [self._scored(make_chunk("c", "d1", "fon"), 0.05, doc)], now=NOW)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].components["phrase"], 0.0)

    def test_k_truncates_after_diverse_selection(self) -> None:
        doc = make_doc("d1")
        candidates = [
            self._scored(make_chunk(f"c{i}", "d1", f"fon konu {i}"), 0.05 - i * 0.001, doc)
            for i in range(5)
        ]
        self.assertEqual(len(rerank("fon", candidates, now=NOW, k=2)), 2)

    def test_custom_weights_change_the_outcome(self) -> None:
        official = make_doc("o", source="resmigazete")
        blog = make_doc("b", source="blog")
        out = rerank(
            "fon",
            [self._scored(make_chunk("blog", "b", "fon"), 0.09, blog),
             self._scored(make_chunk("official", "o", "fon"), 0.05, official)],
            authority={"resmigazete": 1.0, "blog": 0.1},
            now=NOW,
            weights=RerankWeights(base=0.0, phrase=0.0, coverage=0.0, authority=1.0, recency=0.0),
            diversity=0.0,
        )
        self.assertEqual(out[0].chunk.chunk_id, "official")

    def test_ranks_are_dense_and_one_based(self) -> None:
        doc = make_doc("d1")
        out = rerank(
            "fon",
            [self._scored(make_chunk(f"c{i}", "d1", f"fon {i}"), 0.05 - i * 0.01, doc)
             for i in range(3)],
            now=NOW,
        )
        self.assertEqual([s.components["rerank_rank"] for s in out], [1.0, 2.0, 3.0])

    def test_explain_and_report_do_not_blow_up_on_edges(self) -> None:
        self.assertEqual(explain([]), "no results")
        self.assertEqual(rerank_report([])["results"], 0)
        doc = make_doc("d1", source="spk")
        out = rerank("fon", [self._scored(make_chunk("c", "d1", "fon"), 0.05, doc)], now=NOW)
        self.assertIn("dup-pen", explain(out))
        report = rerank_report(out)
        self.assertEqual(report["results"], 1)
        self.assertEqual(report["sources"], ["spk"])


class EndToEndTest(unittest.TestCase):
    """Ingest -> index -> persist -> reopen -> retrieve -> rerank, on disk."""

    def test_a_corpus_survives_a_restart_and_still_answers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.db"
            docs = [
                make_doc("spk1", source="spk", title="Bülten", updated=NOW),
                make_doc("blog1", source="web", title="Blog", updated=NOW - 900 * DAY),
            ]
            chunks = [
                make_chunk("s1", "spk1", "Fonun portföy sınırlamaları güncellendi.", 0),
                make_chunk("s2", "spk1", "Vergi istisnası ve denetim raporu yayımlandı.", 1),
                make_chunk("b1", "blog1", "Fonlar hakkında eski bir yatırım yazısı.", 0),
            ]
            with Store(path) as store:
                store.upsert_documents(docs)
                store.upsert_chunks(
                    chunks, {c.chunk_id: toy_embed(c.indexed_text) for c in chunks},
                    model="toy-v1",
                )
                BM25Index.ensure(store)

            # A new process: nothing rebuilt, everything reloaded.
            with Store(path) as store:
                self.assertIsNotNone(store.get_blob("bm25"))
                retriever = HybridRetriever.from_store(store, embedder=toy_embed)
                results = retriever.retrieve("fon portföy", k=3)
                self.assertTrue(results)
                ranked = rerank(
                    "fon portföy", results,
                    authority={"spk": 0.98, "web": 0.4}, now=NOW, half_life_days=180.0,
                )
                self.assertEqual(ranked[0].chunk.chunk_id, "s1")
                by_id = {r.chunk.chunk_id: r for r in ranked}
                self.assertIn("b1", by_id)
                self.assertLess(
                    by_id["b1"].components["recency"], by_id["s1"].components["recency"]
                )
                self.assertGreater(by_id["s1"].components["authority"],
                                   by_id["b1"].components["authority"])
                self.assertTrue(math.isfinite(ranked[0].score))
                self.assertIn("rrf", ranked[0].components)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
