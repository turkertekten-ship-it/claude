"""Tests for the connector contract and its incremental accounting.

The accounting is the thing worth pinning. Every connector inherits it, so an
off-by-one in "new vs changed vs unchanged" is not one wrong number in one
report - it is a wrong hash map written into the cursor, which makes the *next*
run wrong too, and the one after that. The cases below are therefore mostly
about the runs that do not finish: a `limit` that cuts the stream, a source that
raises halfway, a document that will not hash, a state file that will not be
written. Each of those leaves a partial view of the source behind, and the only
safe thing to do with a partial view is add to what is already known.

Nothing here touches the network or the developer's home directory: the
connectors are lists of documents, and every state file lives in a
TemporaryDirectory.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from oodarag.ingest import base
from oodarag.ingest.base import (
    MAX_ERRORS,
    MAX_REMOVED_REPORTED,
    Connector,
    ConnectorResult,
    JsonStateStore,
    MemoryStateStore,
)
from oodarag.models import RawDocument


def doc(external_id: str, text: str = "body", title: str = "title") -> RawDocument:
    return RawDocument(
        source_system="fake",
        external_id=external_id,
        uri=f"https://example.test/{external_id}",
        title=title,
        text=text,
    )


class Unhashable(RawDocument):
    """A document whose bytes defeat hashing - a real connector hits this when
    a file it listed disappears between the listing and the read."""

    @property
    def content_hash(self) -> str:
        raise ValueError("could not read the document")


class ListConnector(Connector):
    """A connector with a scripted stream.

    `raise_at` makes the source itself fail after N documents, which is the
    interesting shape: the documents before it are real and must survive.
    """

    key = "fake:source"

    def __init__(self, docs: list[Any], *, raise_at: int | None = None,
                 enumerates: bool = False, key: str = "fake:source") -> None:
        self.docs = docs
        self.raise_at = raise_at
        self.enumerates_source = enumerates
        self.key = key
        self.seen_cursors: list[dict[str, Any]] = []
        self.closed = False

    def fetch(self, cursor: dict[str, Any]):
        self.seen_cursors.append(dict(cursor))
        try:
            for index, item in enumerate(self.docs):
                if self.raise_at is not None and index == self.raise_at:
                    raise RuntimeError("the source went away")
                yield item
        finally:
            # Set on exhaustion *and* on close, so a test can tell whether `run`
            # released the stream it stopped pulling from.
            self.closed = True


class AccountingTestCase(unittest.TestCase):
    """new / changed / unchanged, walked against hand-worked examples."""

    def test_first_run_is_all_new(self) -> None:
        state = MemoryStateStore()
        result = ListConnector([doc("a"), doc("b")]).run(state=state)
        delta = result.delta
        self.assertEqual((delta.new, delta.changed, delta.unchanged), (2, 0, 0))
        self.assertEqual([d.external_id for d in result.documents], ["a", "b"])
        self.assertEqual(len(result), 2)
        self.assertEqual(result.delta.source_key, "fake:source")

    def test_second_identical_run_is_all_unchanged_and_emits_nothing(self) -> None:
        state = MemoryStateStore()
        ListConnector([doc("a"), doc("b")]).run(state=state)
        result = ListConnector([doc("a"), doc("b")]).run(state=state)
        delta = result.delta
        self.assertEqual((delta.new, delta.changed, delta.unchanged), (0, 0, 2))
        self.assertEqual(result.documents, [])
        self.assertEqual(delta.touched, 0)

    def test_new_changed_and_unchanged_in_one_run(self) -> None:
        """a unchanged, b edited, c added: 1 new, 1 changed, 1 unchanged."""
        state = MemoryStateStore()
        ListConnector([doc("a"), doc("b")]).run(state=state)
        result = ListConnector([doc("a"), doc("b", "edited"), doc("c")]).run(state=state)
        delta = result.delta
        self.assertEqual((delta.new, delta.changed, delta.unchanged), (1, 1, 1))
        self.assertEqual([d.external_id for d in result.documents], ["b", "c"])
        self.assertEqual(result.delta.touched, 2)

    def test_the_title_is_part_of_the_hash(self) -> None:
        """Retitling a page with identical body is a change, not a no-op."""
        state = MemoryStateStore()
        ListConnector([doc("a", "body", "old")]).run(state=state)
        result = ListConnector([doc("a", "body", "new")]).run(state=state)
        self.assertEqual(result.delta.changed, 1)

    def test_a_run_without_a_store_still_reports_a_delta(self) -> None:
        result = ListConnector([doc("a")]).run()
        self.assertEqual(result.delta.new, 1)
        self.assertEqual(result.cursor["hashes"], {"a": doc("a").content_hash})

    def test_an_empty_source_is_a_clean_zero(self) -> None:
        result = ListConnector([]).run(state=MemoryStateStore())
        self.assertEqual(result.documents, [])
        self.assertEqual(result.delta.as_dict()["failed"], 0)

    def test_the_connector_is_handed_the_cursor_it_stored(self) -> None:
        state = MemoryStateStore()
        first = ListConnector([doc("a")])
        first.run(state=state)
        second = ListConnector([doc("a")])
        second.run(state=state)
        self.assertEqual(second.seen_cursors[0]["hashes"], {"a": doc("a").content_hash})
        self.assertTrue(second.seen_cursors[0]["complete_run"])


class VanishedDocumentTestCase(unittest.TestCase):
    """What "removed" may and may not be inferred from."""

    def test_an_enumerating_connector_reports_what_vanished(self) -> None:
        state = MemoryStateStore()
        ListConnector([doc("a"), doc("b")], enumerates=True).run(state=state)
        result = ListConnector([doc("a")], enumerates=True).run(state=state)
        self.assertEqual(result.cursor["removed_last_run"], ["b"])
        self.assertEqual(result.cursor["removed_count"], 1)
        self.assertNotIn("b", result.cursor["hashes"])

    def test_a_sampling_connector_never_claims_a_deletion(self) -> None:
        """The default. A crawl that did not see a page has not seen it deleted."""
        state = MemoryStateStore()
        ListConnector([doc("a"), doc("b")]).run(state=state)
        result = ListConnector([doc("a")]).run(state=state)
        self.assertEqual(result.cursor["removed_last_run"], [])
        self.assertEqual(result.cursor["removed_count"], 0)
        self.assertIn("b", result.cursor["hashes"], "the hash map may only grow")

    def test_a_subset_run_does_not_re_ingest_the_documents_it_skipped(self) -> None:
        """The corruption this accounting exists to prevent: a connector that
        yields only what changed must not have the rest forgotten under it."""
        state = MemoryStateStore()
        ListConnector([doc("a"), doc("b"), doc("c")]).run(state=state)
        ListConnector([doc("b", "edited")]).run(state=state)  # only the changed one
        third = ListConnector([doc("a"), doc("b", "edited"), doc("c")]).run(state=state)
        self.assertEqual((third.delta.new, third.delta.changed, third.delta.unchanged), (0, 0, 3))

    def test_the_removed_list_is_capped_but_the_count_is_not(self) -> None:
        state = MemoryStateStore()
        ListConnector([doc(f"d{i:03d}") for i in range(150)], enumerates=True).run(state=state)
        result = ListConnector([], enumerates=True).run(state=state)
        removed = result.cursor["removed_last_run"]
        self.assertEqual(len(removed), MAX_REMOVED_REPORTED)
        self.assertEqual(result.cursor["removed_count"], 150)
        self.assertEqual(removed, sorted(removed), "a capped list must be stable across runs")
        self.assertEqual(removed[0], "d000")

    def test_an_empty_enumerating_run_empties_the_map(self) -> None:
        """It promised to list everything and listed nothing: everything is gone."""
        state = MemoryStateStore()
        ListConnector([doc("a")], enumerates=True).run(state=state)
        result = ListConnector([], enumerates=True).run(state=state)
        self.assertEqual(result.cursor["hashes"], {})

    def test_an_empty_sampling_run_keeps_the_map(self) -> None:
        """Zero documents is the success case for a cursor-driven source: it is
        "nothing changed", not "the source is empty", and wiping the map here
        would both declare every document deleted and re-ingest the lot."""
        state = MemoryStateStore()
        first = ListConnector([doc("a"), doc("b")]).run(state=state)
        result = ListConnector([]).run(state=state)
        self.assertEqual(result.cursor["hashes"], first.cursor["hashes"])
        self.assertEqual(result.cursor["removed_last_run"], [])

    def test_the_hash_map_is_bounded(self) -> None:
        state = MemoryStateStore()
        with mock.patch.object(base, "MAX_TRACKED_HASHES", 3):
            ListConnector([doc(f"d{i}") for i in range(5)]).run(state=state)
        self.assertEqual(list(state.get("fake:source")["hashes"]), ["d2", "d3", "d4"])


class LimitTestCase(unittest.TestCase):
    """`limit` truncates the stream, and a truncated run knows it."""

    def test_limit_stops_after_n_documents(self) -> None:
        result = ListConnector([doc("a"), doc("b"), doc("c")]).run(limit=2)
        self.assertEqual([d.external_id for d in result.documents], ["a", "b"])
        self.assertFalse(result.cursor["complete_run"])

    def test_limit_zero_means_zero(self) -> None:
        result = ListConnector([doc("a")]).run(limit=0)
        self.assertEqual(result.documents, [])
        self.assertFalse(result.cursor["complete_run"])

    def test_a_limit_equal_to_the_stream_is_not_a_truncation(self) -> None:
        """The exact-cap boundary: the break only fires if a document was left."""
        result = ListConnector([doc("a"), doc("b")]).run(limit=2)
        self.assertTrue(result.cursor["complete_run"])

    def test_a_truncated_run_writes_a_partial_map_that_only_adds(self) -> None:
        """The regression: the break happens before the hash is recorded, so the
        documents past the limit are unread. Replacing the map with that partial
        view made every one of them look deleted and then new again."""
        state = MemoryStateStore()
        full = ListConnector([doc("a"), doc("b"), doc("c")], enumerates=True).run(state=state)
        cut = ListConnector([doc("a"), doc("b"), doc("c")], enumerates=True).run(
            state=state, limit=1
        )
        self.assertEqual(cut.cursor["hashes"], full.cursor["hashes"])
        self.assertEqual(cut.cursor["removed_last_run"], [])

    def test_the_run_after_a_truncated_one_sees_no_change(self) -> None:
        state = MemoryStateStore()
        ListConnector([doc("a"), doc("b")]).run(state=state)
        ListConnector([doc("a"), doc("b")]).run(state=state, limit=1)
        result = ListConnector([doc("a"), doc("b")]).run(state=state)
        self.assertEqual((result.delta.new, result.delta.unchanged), (0, 2))

    def test_limit_counts_emitted_documents_not_scanned_ones(self) -> None:
        state = MemoryStateStore()
        ListConnector([doc("a"), doc("b"), doc("c")]).run(state=state)
        result = ListConnector([doc("a"), doc("b", "edited"), doc("c", "edited")]).run(
            state=state, limit=1
        )
        self.assertEqual([d.external_id for d in result.documents], ["b"])
        self.assertEqual(result.delta.unchanged, 1)

    def test_a_stopped_stream_is_closed(self) -> None:
        connector = ListConnector([doc("a"), doc("b"), doc("c")])
        connector.run(limit=1)
        self.assertTrue(connector.closed, "run must release a generator it stopped pulling from")


class FailureTestCase(unittest.TestCase):
    """Every error path: partial results are kept, the cursor is held."""

    def test_a_source_that_dies_midway_keeps_what_it_already_yielded(self) -> None:
        result = ListConnector([doc("a"), doc("b"), doc("c")], raise_at=2).run()
        self.assertEqual([d.external_id for d in result.documents], ["a", "b"])
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.delta.new, 2)
        self.assertIn("RuntimeError: the source went away", result.delta.errors[0])
        self.assertFalse(result.cursor["complete_run"])

    def test_a_source_failure_does_not_forget_anything(self) -> None:
        state = MemoryStateStore()
        first = ListConnector([doc("a"), doc("b")], enumerates=True).run(state=state)
        broken = ListConnector([doc("a"), doc("b")], raise_at=1, enumerates=True).run(state=state)
        self.assertEqual(broken.cursor["hashes"], first.cursor["hashes"])
        self.assertEqual(broken.cursor["removed_last_run"], [])

    def test_a_source_that_fails_before_the_first_document(self) -> None:
        result = ListConnector([doc("a")], raise_at=0).run(state=MemoryStateStore())
        self.assertEqual(result.documents, [])
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.delta.touched, 0)

    def test_one_unreadable_document_does_not_stop_the_others(self) -> None:
        result = ListConnector([doc("a"), Unhashable("fake", "b", "u", "t", "x"), doc("c")]).run()
        self.assertEqual([d.external_id for d in result.documents], ["a", "c"])
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.delta.new, 2)
        self.assertIn("b: ValueError", result.delta.errors[0])

    def test_an_unreadable_document_keeps_its_prior_hash(self) -> None:
        """It exists, so it is not "removed"; it was never delivered, so the next
        clean read has to count as a change rather than as unchanged."""
        state = MemoryStateStore()
        ListConnector([doc("a", "v1")], enumerates=True).run(state=state)
        failed = ListConnector(
            [Unhashable("fake", "a", "u", "t", "v2")], enumerates=True
        ).run(state=state)
        self.assertEqual(failed.cursor["removed_last_run"], [])
        self.assertEqual(failed.cursor["hashes"]["a"], doc("a", "v1").content_hash)
        result = ListConnector([doc("a", "v2")], enumerates=True).run(state=state)
        self.assertEqual((result.delta.changed, result.delta.unchanged), (1, 0))

    def test_a_document_with_no_external_id_is_a_failure_not_a_document(self) -> None:
        result = ListConnector([doc(""), doc("a")]).run()
        self.assertEqual([d.external_id for d in result.documents], ["a"])
        self.assertEqual(result.delta.failed, 1)
        self.assertIn("no external_id", result.delta.errors[0])

    def test_a_document_that_is_not_a_document_at_all(self) -> None:
        result = ListConnector(["not a document", doc("a")]).run()
        self.assertEqual([d.external_id for d in result.documents], ["a"])
        self.assertEqual(result.delta.failed, 1)

    def test_the_same_id_twice_in_one_run_is_reported_once(self) -> None:
        """Downstream ids derive from external_id, so admitting both would index
        one document twice and count it as two new ones."""
        result = ListConnector([doc("a", "first"), doc("a", "second")]).run()
        self.assertEqual(len(result.documents), 1)
        self.assertEqual(result.delta.new, 1)
        self.assertEqual(result.delta.failed, 1)
        self.assertIn("duplicate external_id", result.delta.errors[0])

    def test_error_strings_are_bounded(self) -> None:
        result = ListConnector([doc("") for _ in range(MAX_ERRORS + 10)]).run()
        self.assertEqual(result.delta.failed, MAX_ERRORS + 10)
        self.assertEqual(len(result.delta.errors), MAX_ERRORS + 1)
        self.assertIn("suppressed", result.delta.errors[-1])

    def test_a_credential_in_an_exception_never_reaches_the_delta(self) -> None:
        token = "ghp_" + "A" * 36

        class Leaky(Connector):
            key = "leaky"

            def fetch(self, cursor):
                raise RuntimeError(f"401 from https://api.test with {token}")
                yield  # pragma: no cover - unreachable, makes this a generator

        result = Leaky().run()
        self.assertNotIn(token, result.delta.errors[0])
        self.assertIn("<redacted:github-token>", result.delta.errors[0])
        self.assertLessEqual(len(result.delta.errors[0]), base.MAX_ERROR_CHARS)

    def test_a_long_exception_message_is_clipped(self) -> None:
        class Verbose(Connector):
            key = "verbose"

            def fetch(self, cursor):
                raise RuntimeError("x" * 5000)
                yield  # pragma: no cover - unreachable, makes this a generator

        result = Verbose().run()
        self.assertEqual(len(result.delta.errors[0]), base.MAX_ERROR_CHARS)


class CursorAndStateTestCase(unittest.TestCase):
    """The store is an optimization; a broken one costs time, not documents."""

    def test_a_store_that_cannot_be_read_runs_as_if_fresh(self) -> None:
        class Unreadable:
            written: dict[str, Any] = {}

            def get(self, key: str) -> dict[str, Any]:
                raise ValueError("state file is a directory")

            def set(self, key: str, value: dict[str, Any]) -> None:
                self.written = value

        store = Unreadable()
        result = ListConnector([doc("a")]).run(state=store)
        self.assertEqual(result.delta.new, 1)
        self.assertEqual(result.delta.failed, 0)
        self.assertIn("hashes", store.written)

    def test_a_store_that_cannot_be_written_still_returns_the_documents(self) -> None:
        class ReadOnly:
            def get(self, key: str) -> dict[str, Any]:
                return {}

            def set(self, key: str, value: dict[str, Any]) -> None:
                raise OSError("read-only file system")

        result = ListConnector([doc("a")]).run(state=ReadOnly())
        self.assertEqual([d.external_id for d in result.documents], ["a"])
        self.assertEqual(result.delta.failed, 1)
        self.assertIn("cursor not persisted", result.delta.errors[0])

    def test_a_cursor_holding_junk_degrades_to_a_full_re_ingest(self) -> None:
        for junk in ([], "hashes", None, {"a": ["not", "a", "hash"]}, 7):
            with self.subTest(junk=junk):
                state = MemoryStateStore()
                state.set("fake:source", {"hashes": junk})
                result = ListConnector([doc("a")]).run(state=state)
                self.assertEqual(result.delta.new, 1)
                self.assertEqual(result.delta.failed, 0)

    def test_a_store_returning_something_that_is_not_a_cursor(self) -> None:
        class Odd:
            def get(self, key: str) -> Any:
                return ["not", "a", "cursor"]

            def set(self, key: str, value: dict[str, Any]) -> None:
                pass

        result = ListConnector([doc("a")]).run(state=Odd())
        self.assertEqual(result.delta.new, 1)

    def test_a_connector_whose_next_cursor_raises_holds_the_previous_one(self) -> None:
        class BadCursor(ListConnector):
            def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
                raise KeyError("mine")

        state = MemoryStateStore()
        state.set("fake:source", {"hashes": {}, "custom": "kept"})
        result = BadCursor([doc("a")]).run(state=state)
        self.assertEqual([d.external_id for d in result.documents], ["a"])
        self.assertEqual(result.cursor["custom"], "kept")
        self.assertIn("next_cursor", result.delta.errors[0])

    def test_a_connector_whose_next_cursor_returns_junk(self) -> None:
        class JunkCursor(ListConnector):
            def next_cursor(self, cursor: dict[str, Any]) -> Any:
                return "not a cursor"

        result = JunkCursor([doc("a")]).run(state=MemoryStateStore())
        self.assertEqual(result.cursor["hashes"], {"a": doc("a").content_hash})

    def test_next_cursor_additions_survive(self) -> None:
        class Advancing(ListConnector):
            def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
                cursor["head"] = "abc123"
                return cursor

        result = Advancing([doc("a")]).run(state=MemoryStateStore())
        self.assertEqual(result.cursor["head"], "abc123")
        self.assertIn("hashes", result.cursor)

    def test_the_delta_is_timed(self) -> None:
        result = ListConnector([doc("a")]).run()
        self.assertGreaterEqual(result.delta.duration_s, 0.0)
        self.assertIsInstance(result.cursor["last_run"], float)


class JsonStateStoreTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.path = self.root / "state" / "ingest.json"

    def test_it_creates_its_directory_and_round_trips(self) -> None:
        store = JsonStateStore(self.path)
        store.set("web:x", {"hashes": {"a": "deadbeef"}, "note": "naïve café"})
        reopened = JsonStateStore(self.path)
        self.assertEqual(reopened.get("web:x")["hashes"], {"a": "deadbeef"})
        self.assertEqual(reopened.get("web:x")["note"], "naïve café")

    def test_an_unknown_key_is_an_empty_cursor(self) -> None:
        self.assertEqual(JsonStateStore(self.path).get("nobody"), {})

    def test_the_returned_cursor_is_a_copy(self) -> None:
        store = JsonStateStore(self.path)
        store.set("k", {"hashes": {}})
        store.get("k")["hashes"]["a"] = "1"
        self.assertEqual(store.get("k")["hashes"], {})

    def test_a_stored_cursor_is_copied_in(self) -> None:
        store = JsonStateStore(self.path)
        cursor = {"hashes": {"a": "1"}}
        store.set("k", cursor)
        cursor["hashes"] = {"b": "2"}
        self.assertEqual(JsonStateStore(self.path).get("k")["hashes"], {"a": "1"})

    def test_the_write_leaves_no_temp_files(self) -> None:
        store = JsonStateStore(self.path)
        store.set("k", {"n": 1})
        store.set("k", {"n": 2})
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])
        self.assertEqual(json.loads(self.path.read_text("utf-8")), {"k": {"n": 2}})

    def test_a_corrupt_state_file_degrades_to_a_full_re_ingest(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text("{not json at all", encoding="utf-8")
        store = JsonStateStore(self.path)  # must not raise
        self.assertEqual(store.get("k"), {})
        store.set("k", {"n": 1})
        self.assertEqual(JsonStateStore(self.path).get("k"), {"n": 1})

    def test_a_state_file_that_is_not_utf8(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_bytes(b'{"k": {"n": "\xff\xfe caf"}}')
        self.assertEqual(JsonStateStore(self.path).get("k"), {})

    def test_a_state_file_that_is_not_an_object(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text('["a", "b"]', encoding="utf-8")
        self.assertEqual(JsonStateStore(self.path).get("k"), {})

    def test_a_cursor_that_is_not_an_object(self) -> None:
        self.path.parent.mkdir(parents=True)
        self.path.write_text('{"k": 7, "other": {"n": 1}}', encoding="utf-8")
        store = JsonStateStore(self.path)
        self.assertEqual(store.get("k"), {})
        self.assertEqual(store.get("other"), {"n": 1})

    def test_a_state_path_that_is_a_directory(self) -> None:
        self.path.mkdir(parents=True)
        self.assertEqual(JsonStateStore(self.path).get("k"), {})

    def test_a_directory_that_cannot_be_created_fails_at_write_time(self) -> None:
        """Construction is total; the write is where the caller finds out, with
        the run's documents already in hand."""
        blocker = self.root / "blocker"
        blocker.write_text("i am a file", encoding="utf-8")
        store = JsonStateStore(blocker / "nested" / "state.json")  # must not raise
        self.assertEqual(store.get("k"), {})
        with self.assertRaises(OSError):
            store.set("k", {"n": 1})

    def test_an_unwritable_state_store_is_reported_through_the_delta(self) -> None:
        blocker = self.root / "blocker"
        blocker.write_text("i am a file", encoding="utf-8")
        store = JsonStateStore(blocker / "nested" / "state.json")
        result = ListConnector([doc("a")]).run(state=store)
        self.assertEqual(len(result.documents), 1)
        self.assertIn("cursor not persisted", result.delta.errors[0])

    def test_an_unserializable_cursor_leaves_the_previous_file_intact(self) -> None:
        store = JsonStateStore(self.path)
        store.set("k", {"n": 1})
        with self.assertRaises(TypeError):
            store.set("k", {object(): "unserializable key"})
        self.assertEqual(json.loads(self.path.read_text("utf-8")), {"k": {"n": 1}})
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])

    def test_the_last_writer_of_two_open_stores_wins(self) -> None:
        """Pinned rather than fixed: each store holds its own view of the whole
        file, so two long-lived stores on one path are a lost update. One store
        per path per process is the contract."""
        first = JsonStateStore(self.path)
        second = JsonStateStore(self.path)
        first.set("a", {"n": 1})
        second.set("b", {"n": 2})
        self.assertEqual(json.loads(self.path.read_text("utf-8")), {"b": {"n": 2}})

    def test_a_store_opened_after_a_write_sees_it(self) -> None:
        JsonStateStore(self.path).set("a", {"n": 1})
        store = JsonStateStore(self.path)
        store.set("b", {"n": 2})
        self.assertEqual(set(json.loads(self.path.read_text("utf-8"))), {"a", "b"})

    def test_the_cursor_round_trips_across_processes(self) -> None:
        """The whole point of the file: run, forget everything, run again."""
        ListConnector([doc("a"), doc("b")]).run(state=JsonStateStore(self.path))
        result = ListConnector([doc("a"), doc("b", "edited")]).run(state=JsonStateStore(self.path))
        self.assertEqual((result.delta.changed, result.delta.unchanged), (1, 1))
        self.assertEqual([d.external_id for d in result.documents], ["b"])

    def test_the_state_file_is_not_world_readable(self) -> None:
        """Cursors carry ETags and shas from private repositories."""
        store = JsonStateStore(self.path)
        store.set("k", {"n": 1})
        self.assertEqual(os.stat(self.path).st_mode & 0o077, 0)


class MemoryStateStoreTestCase(unittest.TestCase):
    def test_it_copies_in_and_out(self) -> None:
        store = MemoryStateStore()
        cursor: dict[str, Any] = {"hashes": {"a": "1"}}
        store.set("k", cursor)
        cursor["hashes"] = {}
        self.assertEqual(store.get("k")["hashes"], {"a": "1"})
        store.get("k")["hashes"]["b"] = "2"
        self.assertEqual(store.get("k")["hashes"], {"a": "1"})

    def test_an_unknown_key_is_empty(self) -> None:
        self.assertEqual(MemoryStateStore().get("nope"), {})


class ConnectorResultTestCase(unittest.TestCase):
    def test_an_empty_result_is_falsey_by_length(self) -> None:
        self.assertEqual(len(ConnectorResult()), 0)
        self.assertEqual(ConnectorResult().delta.source_key, "")


if __name__ == "__main__":
    unittest.main()
