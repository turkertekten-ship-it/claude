"""Durability tests for `oodarag.index.store`.

The store is the only module in the pipeline allowed durable state, so the
failures worth catching here are the silent ones: a metadata dict that comes
back subtly different, a vector that survives the float32 round trip as
plausible-looking nonsense, a re-ingest that empties a document through a
cascade nobody asked for, and a half-finished re-chunk that leaves a document
answering questions from text it no longer contains.

Every test below asserts on a value that a constant-returning implementation
would get wrong. "It did not raise" is never the assertion.
"""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from oodarag.index import store as store_mod
from oodarag.index.store import (
    SCHEMA_VERSION,
    SchemaVersionError,
    Store,
    pack_vector,
    unpack_vector,
)
from oodarag.models import Chunk, Document

_LOG_LEVEL = store_mod.log.level


def setUpModule() -> None:
    # The store logs warnings on purpose (rejected rows, damaged vectors) and
    # several tests below provoke exactly those. Silencing keeps the expected
    # noise out of the unittest report without weakening the assertions.
    store_mod.log.level = 100


def tearDownModule() -> None:
    store_mod.log.level = _LOG_LEVEL


RICH_METADATA = {
    "authority": 0.85,
    "canonical": "https://example.test/a?b=1&c=2",
    "tags": ["docs", "rag", "ünïcøde"],
    "nested": {"depth": {"level": 3}, "flag": True, "missing": None},
    "count": 41,
    "ratio": 0.1 + 0.2,  # 0.30000000000000004 - survives JSON repr exactly
    "title_ja": "検索",
}


def make_doc(doc_id: str = "doc-1", **over: object) -> Document:
    fields: dict = {
        "doc_id": doc_id,
        "source_system": "files",
        "external_id": f"ext-{doc_id}",
        "uri": f"file:///{doc_id}.md",
        "title": "Retrieval notes — ünïcøde ✓",
        "text": "# Heading\n\nBody line one.\n\nBody line two.\t(tabbed)\n",
        "content_hash": "0123456789abcdef",
        "metadata": dict(RICH_METADATA),
        "created_at": 1_700_000_000.5,
        "updated_at": 1_700_000_123.25,
    }
    fields.update(over)
    return Document(**fields)  # type: ignore[arg-type]


def make_chunk(chunk_id: str, doc_id: str = "doc-1", ordinal: int = 0, **over: object) -> Chunk:
    fields: dict = {
        "chunk_id": chunk_id,
        "doc_id": doc_id,
        "ordinal": ordinal,
        "text": f"chunk {chunk_id} body\nwith a newline and a tab\there",
        "context_header": f"Retrieval notes > Heading ({ordinal + 1})",
        "metadata": dict(RICH_METADATA),
        "char_start": 10 * (ordinal + 1),
        "char_end": 10 * (ordinal + 1) + 42,
    }
    fields.update(over)
    return Chunk(**fields)  # type: ignore[arg-type]


class TempStoreCase(unittest.TestCase):
    """A store backed by a real file, so WAL, size and reopen behaviour are real."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "nested" / "index.db"
        self.store = Store(self.db)
        self.addCleanup(self.store.close)


# ---------------------------------------------------------------------------
# round trips
# ---------------------------------------------------------------------------


class DocumentRoundTrip(TempStoreCase):
    def test_document_round_trips_every_field(self) -> None:
        doc = make_doc()
        self.assertEqual(self.store.upsert_documents([doc]), 1)

        got = self.store.get_document("doc-1")
        self.assertIsNotNone(got)
        assert got is not None
        for field in (
            "doc_id",
            "source_system",
            "external_id",
            "uri",
            "title",
            "text",
            "content_hash",
        ):
            self.assertEqual(getattr(got, field), getattr(doc, field), field)
        self.assertEqual(got.created_at, doc.created_at)
        self.assertEqual(got.updated_at, doc.updated_at)

    def test_document_metadata_dict_round_trips_losslessly(self) -> None:
        self.store.upsert_documents([make_doc()])
        got = self.store.get_document("doc-1")
        assert got is not None
        self.assertEqual(got.metadata, RICH_METADATA)
        # Not merely equal by ==: the nested structure must still be navigable.
        self.assertEqual(got.metadata["nested"]["depth"]["level"], 3)
        self.assertIs(got.metadata["nested"]["flag"], True)
        self.assertIsNone(got.metadata["nested"]["missing"])
        self.assertEqual(got.metadata["tags"][2], "ünïcøde")
        self.assertIsInstance(got.metadata["count"], int)
        self.assertAlmostEqual(got.metadata["ratio"], 0.1 + 0.2, places=15)

    def test_stored_metadata_is_a_copy_not_a_live_reference(self) -> None:
        doc = make_doc()
        self.store.upsert_documents([doc])
        doc.metadata["tags"].append("mutated-after-write")
        got = self.store.get_document("doc-1")
        assert got is not None
        self.assertNotIn("mutated-after-write", got.metadata["tags"])

    def test_missing_document_is_none_not_an_error(self) -> None:
        self.assertIsNone(self.store.get_document("never-written"))

    def test_documents_are_ordered_by_created_at_then_doc_id(self) -> None:
        self.store.upsert_documents(
            [
                make_doc("zzz", created_at=1.0),
                make_doc("aaa", created_at=2.0),
                make_doc("bbb", created_at=1.0),
            ]
        )
        self.assertEqual([d.doc_id for d in self.store.documents()], ["bbb", "zzz", "aaa"])

    def test_upsert_updates_in_place_rather_than_duplicating(self) -> None:
        self.store.upsert_documents([make_doc(title="first")])
        self.store.upsert_documents([make_doc(title="second", metadata={"authority": 0.1})])
        docs = self.store.documents()
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].title, "second")
        self.assertEqual(docs[0].metadata, {"authority": 0.1})


class ChunkRoundTrip(TempStoreCase):
    def setUp(self) -> None:
        super().setUp()
        self.store.upsert_documents([make_doc()])

    def test_chunk_round_trips_every_field(self) -> None:
        chunk = make_chunk("c-1", ordinal=3)
        self.assertEqual(self.store.upsert_chunks([chunk]), 1)

        got = self.store.get_chunk("c-1")
        self.assertIsNotNone(got)
        assert got is not None
        self.assertEqual(got.chunk_id, chunk.chunk_id)
        self.assertEqual(got.doc_id, chunk.doc_id)
        self.assertEqual(got.ordinal, 3)
        self.assertEqual(got.text, chunk.text)
        self.assertEqual(got.context_header, chunk.context_header)
        self.assertEqual(got.char_start, chunk.char_start)
        self.assertEqual(got.char_end, chunk.char_end)
        # indexed_text is derived, and it is what both indexes consume.
        self.assertEqual(got.indexed_text, chunk.indexed_text)

    def test_chunk_metadata_dict_round_trips_losslessly(self) -> None:
        self.store.upsert_chunks([make_chunk("c-1")])
        got = self.store.get_chunk("c-1")
        assert got is not None
        self.assertEqual(got.metadata, RICH_METADATA)
        self.assertEqual(got.metadata["nested"]["depth"], {"level": 3})

    def test_empty_metadata_round_trips_as_an_empty_dict(self) -> None:
        self.store.upsert_chunks([make_chunk("c-1", metadata={})])
        got = self.store.get_chunk("c-1")
        assert got is not None
        self.assertEqual(got.metadata, {})

    def test_get_chunks_returns_found_ids_and_silently_omits_missing_ones(self) -> None:
        self.store.upsert_chunks([make_chunk("c-1", ordinal=0), make_chunk("c-2", ordinal=1)])
        found = self.store.get_chunks(["c-2", "gone", "c-1"])
        self.assertEqual(sorted(found), ["c-1", "c-2"])
        self.assertEqual(found["c-2"].ordinal, 1)

    def test_get_chunks_spans_more_ids_than_one_sql_batch(self) -> None:
        batch = store_mod._LOOKUP_BATCH
        chunks = [make_chunk(f"c-{i:04d}", ordinal=i) for i in range(batch + 7)]
        self.store.upsert_chunks(chunks)
        found = self.store.get_chunks([c.chunk_id for c in chunks])
        self.assertEqual(len(found), batch + 7)

    def test_iter_chunks_streams_in_document_then_ordinal_order(self) -> None:
        self.store.upsert_documents([make_doc("doc-0")])
        self.store.upsert_chunks(
            [
                make_chunk("x", doc_id="doc-1", ordinal=2),
                make_chunk("y", doc_id="doc-0", ordinal=1),
                make_chunk("z", doc_id="doc-1", ordinal=0),
                make_chunk("w", doc_id="doc-0", ordinal=0),
            ]
        )
        got = [(c.doc_id, c.ordinal) for c in self.store.iter_chunks()]
        self.assertEqual(got, [("doc-0", 0), ("doc-0", 1), ("doc-1", 0), ("doc-1", 2)])

    def test_chunk_whose_document_is_absent_is_rejected_without_losing_the_batch(self) -> None:
        written = self.store.upsert_chunks(
            [make_chunk("good", doc_id="doc-1"), make_chunk("orphan", doc_id="no-such-doc")]
        )
        self.assertEqual(written, 1)
        self.assertIsNotNone(self.store.get_chunk("good"))
        self.assertIsNone(self.store.get_chunk("orphan"))


class VectorRoundTrip(TempStoreCase):
    def setUp(self) -> None:
        super().setUp()
        self.store.upsert_documents([make_doc()])
        self.vec = [0.5, -0.25, 0.125, 0.0, -1.0, 0.333_25, 1e-7, -3.5e-3]

    def test_pack_unpack_is_the_identity_within_float32(self) -> None:
        got = unpack_vector(pack_vector(self.vec))
        self.assertEqual(len(got), len(self.vec))
        for i, (a, b) in enumerate(zip(self.vec, got)):
            self.assertAlmostEqual(a, b, places=6, msg=f"component {i}")

    def test_truncated_vector_blob_raises(self) -> None:
        with self.assertRaises(ValueError):
            unpack_vector(b"\x01\x02\x03")

    def test_vector_round_trips_per_component(self) -> None:
        self.store.upsert_chunks([make_chunk("c-1")], {"c-1": self.vec})
        got = self.store.get_vector("c-1")
        self.assertIsNotNone(got)
        assert got is not None
        self.assertEqual(len(got), len(self.vec))
        for i, (a, b) in enumerate(zip(self.vec, got)):
            self.assertAlmostEqual(a, b, places=6, msg=f"component {i}")

    def test_vector_is_absent_when_none_was_written(self) -> None:
        self.store.upsert_chunks([make_chunk("c-1")])
        self.assertIsNone(self.store.get_vector("c-1"))

    def test_iter_vectors_yields_pairs_sorted_by_chunk_id(self) -> None:
        chunks = [make_chunk(cid, ordinal=i) for i, cid in enumerate(("c-b", "c-a", "c-c"))]
        vectors = {"c-b": [1.0, 0.0], "c-a": [0.0, 1.0], "c-c": [0.5, 0.5]}
        self.store.upsert_chunks(chunks, vectors)
        got = list(self.store.iter_vectors())
        self.assertEqual([cid for cid, _ in got], ["c-a", "c-b", "c-c"])
        self.assertAlmostEqual(dict(got)["c-c"][0], 0.5, places=6)

    def test_a_vector_covering_chunks_outside_this_batch_writes_only_the_batch(self) -> None:
        # `vectors` may legitimately cover a whole run while the batch is a slice.
        self.store.upsert_chunks([make_chunk("c-1")], {"c-1": [1.0, 0.0], "not-here": [0.0, 1.0]})
        self.assertEqual(self.store.stats()["vectors"], 1)

    def test_damaged_blob_costs_one_vector_not_the_whole_rebuild(self) -> None:
        chunks = [make_chunk(cid, ordinal=i) for i, cid in enumerate(("c-a", "c-b", "c-c"))]
        self.store.upsert_chunks(chunks, {c.chunk_id: [1.0, 0.0, 0.0] for c in chunks})
        self.store.close()

        raw = sqlite3.connect(self.db)
        raw.execute("UPDATE vectors SET vec = X'ABCDEF' WHERE chunk_id = 'c-b'")
        raw.commit()
        raw.close()

        with Store(self.db) as reopened:
            got = list(reopened.iter_vectors())
            self.assertEqual([cid for cid, _ in got], ["c-a", "c-c"])
            self.assertIsNone(reopened.get_vector("c-b"))
            self.assertIsNotNone(reopened.get_vector("c-a"))


# ---------------------------------------------------------------------------
# atomicity
# ---------------------------------------------------------------------------


class ReplaceDocumentChunks(TempStoreCase):
    def setUp(self) -> None:
        super().setUp()
        self.store.upsert_documents([make_doc("doc-1"), make_doc("doc-2")])
        self.old = [make_chunk(f"old-{i}", doc_id="doc-1", ordinal=i) for i in range(3)]
        self.other = [make_chunk("other-0", doc_id="doc-2", ordinal=0)]
        self.store.upsert_chunks(
            self.old + self.other,
            {c.chunk_id: [1.0, 0.0] for c in self.old + self.other},
        )

    def _ids(self, doc_id: str) -> list[str]:
        return [c.chunk_id for c in self.store.iter_chunks() if c.doc_id == doc_id]

    def test_replacement_leaves_exactly_the_new_chunks(self) -> None:
        new = [make_chunk(f"new-{i}", doc_id="doc-1", ordinal=i) for i in range(2)]
        self.assertEqual(self.store.replace_document_chunks("doc-1", new), 2)

        self.assertEqual(self._ids("doc-1"), ["new-0", "new-1"])
        for old in self.old:
            self.assertIsNone(self.store.get_chunk(old.chunk_id), old.chunk_id)
        for fresh in new:
            self.assertIsNotNone(self.store.get_chunk(fresh.chunk_id), fresh.chunk_id)

    def test_replacement_does_not_touch_another_document(self) -> None:
        self.store.replace_document_chunks("doc-1", [make_chunk("new-0", doc_id="doc-1")])
        self.assertEqual(self._ids("doc-2"), ["other-0"])
        self.assertIsNotNone(self.store.get_vector("other-0"))

    def test_old_vectors_go_with_the_old_chunks(self) -> None:
        new = [make_chunk("new-0", doc_id="doc-1", ordinal=0)]
        self.store.replace_document_chunks("doc-1", new, {"new-0": [0.0, 1.0]})
        self.assertIsNone(self.store.get_vector("old-0"))
        got = self.store.get_vector("new-0")
        assert got is not None
        self.assertAlmostEqual(got[1], 1.0, places=6)
        # 3 old vectors gone, 1 new one plus doc-2's untouched one remain.
        self.assertEqual(self.store.stats()["vectors"], 2)

    def test_replacing_with_nothing_empties_the_document_only(self) -> None:
        self.assertEqual(self.store.replace_document_chunks("doc-1", []), 0)
        self.assertEqual(self._ids("doc-1"), [])
        self.assertEqual(self._ids("doc-2"), ["other-0"])
        self.assertIsNotNone(self.store.get_document("doc-1"))

    def test_a_chunk_carrying_another_documents_id_is_refused(self) -> None:
        # Writing it would make it invisible to the next replace of doc-1 and so
        # unreachable by any later delete.
        written = self.store.replace_document_chunks(
            "doc-1",
            [make_chunk("mine", doc_id="doc-1"), make_chunk("theirs", doc_id="doc-2")],
        )
        self.assertEqual(written, 1)
        self.assertIsNone(self.store.get_chunk("theirs"))
        self.assertEqual(self._ids("doc-2"), ["other-0"])

    def test_a_failure_mid_replace_rolls_the_delete_back(self) -> None:
        # The whole reason this is one transaction: a crash between the delete
        # and the insert must not leave the document holding no chunks, which
        # from the outside looks like a document that answers questions badly
        # rather than like damage.
        new = [make_chunk("new-0", doc_id="doc-1", ordinal=0)]
        with mock.patch.object(self.store, "_insert_chunks", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.store.replace_document_chunks("doc-1", new)

        self.assertEqual(self._ids("doc-1"), ["old-0", "old-1", "old-2"])
        self.assertIsNotNone(self.store.get_vector("old-1"))
        self.assertIsNone(self.store.get_chunk("new-0"))

    def test_replacement_survives_a_reopen(self) -> None:
        self.store.replace_document_chunks(
            "doc-1", [make_chunk("new-0", doc_id="doc-1")], {"new-0": [0.25, 0.75]}
        )
        self.store.close()
        with Store(self.db) as reopened:
            self.assertIsNone(reopened.get_chunk("old-0"))
            got = reopened.get_vector("new-0")
            assert got is not None
            self.assertAlmostEqual(got[0], 0.25, places=6)


class ReingestDoesNotCascade(TempStoreCase):
    """`INSERT OR REPLACE` would delete the document row and cascade its chunks away."""

    def test_upserting_an_unchanged_document_keeps_its_chunks_and_vectors(self) -> None:
        doc = make_doc()
        self.store.upsert_documents([doc])
        self.store.upsert_chunks([make_chunk("c-1")], {"c-1": [1.0, 0.0]})

        self.store.upsert_documents([doc])
        self.store.upsert_documents([make_doc(title="retitled")])

        self.assertIsNotNone(self.store.get_chunk("c-1"))
        self.assertIsNotNone(self.store.get_vector("c-1"))
        self.assertEqual(self.store.stats()["chunks"], 1)


class DeleteDocument(TempStoreCase):
    def setUp(self) -> None:
        super().setUp()
        self.store.upsert_documents([make_doc("doc-1"), make_doc("doc-2")])
        self.store.upsert_chunks(
            [make_chunk("c-1", doc_id="doc-1"), make_chunk("c-2", doc_id="doc-2")],
            {"c-1": [1.0, 0.0], "c-2": [0.0, 1.0]},
        )

    def test_delete_cascades_to_chunks_and_vectors(self) -> None:
        self.assertEqual(self.store.delete_document("doc-1"), 1)
        self.assertIsNone(self.store.get_document("doc-1"))
        self.assertIsNone(self.store.get_chunk("c-1"))
        self.assertIsNone(self.store.get_vector("c-1"))
        # The other document is intact.
        self.assertIsNotNone(self.store.get_chunk("c-2"))
        self.assertIsNotNone(self.store.get_vector("c-2"))

    def test_deleting_an_absent_document_reports_zero(self) -> None:
        self.assertEqual(self.store.delete_document("never-existed"), 0)
        self.assertEqual(self.store.stats()["documents"], 2)


# ---------------------------------------------------------------------------
# schema versioning
# ---------------------------------------------------------------------------


class SchemaVersioning(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "index.db"
        with Store(self.db) as store:
            store.upsert_documents([make_doc()])
            store.upsert_chunks([make_chunk("c-1")], {"c-1": [1.0, 0.0]})

    def _set_version(self, value: str) -> None:
        raw = sqlite3.connect(self.db)
        raw.execute("UPDATE meta SET value = ? WHERE key = 'schema_version'", (value,))
        raw.commit()
        raw.close()

    def _read_version(self) -> str:
        raw = sqlite3.connect(self.db)
        try:
            return raw.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
        finally:
            raw.close()

    def test_fresh_store_stamps_the_current_version(self) -> None:
        self.assertEqual(self._read_version(), str(SCHEMA_VERSION))

    def test_opening_a_newer_index_raises_a_clear_error(self) -> None:
        newer = SCHEMA_VERSION + 1
        self._set_version(str(newer))

        with self.assertRaises(SchemaVersionError) as caught:
            Store(self.db)

        message = str(caught.exception)
        # "Clear" means both numbers are named: a refusal that says only
        # "incompatible" sends the reader to the source to find out which way.
        self.assertIn(str(newer), message)
        self.assertIn(str(SCHEMA_VERSION), message)
        self.assertIn(str(self.db), message)

    def test_a_refused_open_leaves_the_file_exactly_as_it_was(self) -> None:
        newer = SCHEMA_VERSION + 1
        self._set_version(str(newer))
        with self.assertRaises(SchemaVersionError):
            Store(self.db)
        # Not half-migrated backwards by this build's CREATEs.
        self.assertEqual(self._read_version(), str(newer))

    def test_a_refused_open_does_not_leak_the_connection(self) -> None:
        self._set_version(str(SCHEMA_VERSION + 1))
        real_connect = sqlite3.connect
        opened: list[sqlite3.Connection] = []

        def recording_connect(*args, **kwargs):
            conn = real_connect(*args, **kwargs)
            opened.append(conn)
            return conn

        with mock.patch.object(sqlite3, "connect", side_effect=recording_connect):
            with self.assertRaises(SchemaVersionError):
                Store(self.db)

        self.assertEqual(len(opened), 1, "expected exactly one connection attempt")
        # A caller that catches the error must not be left holding a live handle
        # it has no reference to. Operating on a closed connection raises
        # ProgrammingError, which is how we prove it was actually closed.
        with self.assertRaises(sqlite3.ProgrammingError):
            opened[0].execute("SELECT 1")

    def test_an_older_index_is_upgraded_and_restamped(self) -> None:
        self._set_version("0")
        with Store(self.db) as store:
            self.assertEqual(store.schema_version, SCHEMA_VERSION)
            self.assertIsNotNone(store.get_chunk("c-1"))
        self.assertEqual(self._read_version(), str(SCHEMA_VERSION))

    def test_an_unreadable_version_stamp_is_treated_as_current(self) -> None:
        self._set_version("not-a-number")
        with Store(self.db) as store:
            self.assertEqual(store.schema_version, SCHEMA_VERSION)
            self.assertIsNotNone(store.get_document("doc-1"))


class CorruptMetadataDegrades(TempStoreCase):
    def test_unreadable_metadata_json_returns_an_empty_dict(self) -> None:
        self.store.upsert_documents([make_doc()])
        self.store.close()

        raw = sqlite3.connect(self.db)
        raw.execute("UPDATE documents SET metadata = '{not json' WHERE doc_id = 'doc-1'")
        raw.commit()
        raw.close()

        with Store(self.db) as reopened:
            got = reopened.get_document("doc-1")
            assert got is not None
            self.assertEqual(got.metadata, {})
            self.assertEqual(got.title, make_doc().title)

    def test_non_dict_metadata_json_returns_an_empty_dict(self) -> None:
        self.store.upsert_documents([make_doc()])
        self.store.close()

        raw = sqlite3.connect(self.db)
        raw.execute("UPDATE documents SET metadata = '[1, 2, 3]' WHERE doc_id = 'doc-1'")
        raw.commit()
        raw.close()

        with Store(self.db) as reopened:
            got = reopened.get_document("doc-1")
            assert got is not None
            self.assertEqual(got.metadata, {})

    def test_unserializable_metadata_is_stored_empty_rather_than_losing_the_row(self) -> None:
        circular: dict = {"self": None}
        circular["self"] = circular
        self.store.upsert_documents([make_doc(metadata=circular)])
        got = self.store.get_document("doc-1")
        assert got is not None
        self.assertEqual(got.metadata, {})
        self.assertEqual(got.title, make_doc().title)


# ---------------------------------------------------------------------------
# reporting and lifecycle
# ---------------------------------------------------------------------------


class Stats(TempStoreCase):
    def test_stats_counts_documents_chunks_vectors_and_sources(self) -> None:
        self.store.upsert_documents(
            [
                make_doc("d-1", source_system="files"),
                make_doc("d-2", source_system="files"),
                make_doc("d-3", source_system="github"),
            ]
        )
        chunks = [
            make_chunk("c-1", doc_id="d-1", ordinal=0),
            make_chunk("c-2", doc_id="d-1", ordinal=1),
            make_chunk("c-3", doc_id="d-3", ordinal=0),
        ]
        self.store.upsert_chunks(chunks, {"c-1": [1.0, 0.0, 0.0], "c-3": [0.0, 1.0, 0.0]})

        stats = self.store.stats()
        for key in ("documents", "chunks", "vectors", "bytes", "sources"):
            self.assertIn(key, stats)
        self.assertEqual(stats["documents"], 3)
        self.assertEqual(stats["chunks"], 3)
        self.assertEqual(stats["vectors"], 2)
        self.assertEqual(stats["sources"], {"files": 2, "github": 1})
        self.assertEqual(stats["vector_dim"], 3)
        self.assertGreater(stats["bytes"], 0)

    def test_empty_store_reports_zeros_and_no_sources(self) -> None:
        stats = self.store.stats()
        self.assertEqual(stats["documents"], 0)
        self.assertEqual(stats["chunks"], 0)
        self.assertEqual(stats["vectors"], 0)
        self.assertEqual(stats["sources"], {})
        self.assertEqual(stats["vector_dim"], 0)


class Lifecycle(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "sub" / "dir" / "index.db"

    def test_open_creates_missing_parent_directories(self) -> None:
        with Store(self.db):
            pass
        self.assertTrue(self.db.exists())

    def test_close_is_idempotent(self) -> None:
        store = Store(self.db)
        store.close()
        store.close()  # a `with` plus an explicit close in a finally is not an error

    def test_context_manager_closes_the_connection(self) -> None:
        with Store(self.db) as store:
            store.upsert_documents([make_doc()])
        with self.assertRaises(sqlite3.ProgrammingError):
            store._conn.execute("SELECT 1")

    def test_data_survives_close_and_reopen(self) -> None:
        with Store(self.db) as store:
            store.upsert_documents([make_doc()])
            store.upsert_chunks([make_chunk("c-1")], {"c-1": [0.6, -0.8]})
        with Store(self.db) as reopened:
            doc = reopened.get_document("doc-1")
            assert doc is not None
            self.assertEqual(doc.metadata, RICH_METADATA)
            vec = reopened.get_vector("c-1")
            assert vec is not None
            for a, b in zip([0.6, -0.8], vec):
                self.assertAlmostEqual(a, b, places=6)

    def test_in_memory_store_works_and_reports_zero_bytes(self) -> None:
        with Store(":memory:") as store:
            store.upsert_documents([make_doc()])
            self.assertEqual(store.stats()["documents"], 1)
            self.assertEqual(store.stats()["bytes"], 0)


class BatchedWrites(TempStoreCase):
    def test_more_rows_than_one_write_batch_all_land(self) -> None:
        batch = store_mod._WRITE_BATCH
        n = batch + 13
        self.store.upsert_documents([make_doc(f"d-{i:05d}") for i in range(3)])
        chunks = [make_chunk(f"c-{i:05d}", doc_id=f"d-{i % 3:05d}", ordinal=i) for i in range(n)]
        self.assertEqual(self.store.upsert_chunks(chunks), n)
        self.assertEqual(self.store.stats()["chunks"], n)
        self.assertEqual(len(list(self.store.iter_chunks())), n)

    def test_generators_are_consumed_without_being_materialized_twice(self) -> None:
        self.store.upsert_documents(make_doc(f"d-{i}") for i in range(5))
        self.assertEqual(self.store.stats()["documents"], 5)


if __name__ == "__main__":
    unittest.main()
