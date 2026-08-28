"""The data model, the connector contract, and text processing.

Three layers are covered here because they are one story: `util.text` decides
what a document's text *is*, `models` fingerprints it, and `ingest.base` uses
that fingerprint to decide what changed since the last run. A defect in any one
of them shows up as an index that is silently wrong rather than as a crash, so
most of what follows drives a second and third run and asserts on what the
cursor carried between them.

Nothing here touches the network. The web connector is driven through a
`FakeHttp` that serves a two-page site out of a dict: a connector test that
reaches a real site is testing the site, and the cases that matter (a crawl cut
short, a secret in a page title) are not ones a real site produces on demand.

The package's stated principle is "degrade, don't die", so the failure paths -
an unreadable document, a source that dies half way, a corrupt state file, an
exhausted budget - get at least as much room as the happy path.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from oodarag.ingest.base import Connector, JsonStateStore, MemoryStateStore
from oodarag.ingest.web import WebConnector
from oodarag.models import (
    Answer,
    Chunk,
    Citation,
    Document,
    IngestDelta,
    RawDocument,
    ScoredChunk,
)
from oodarag.util import text as T
from oodarag.util.http import HttpClient, HttpError, Response

# --------------------------------------------------------------------- fixtures


def raw(external_id: str, text: str, *, title: str = "", source: str = "test",
        fetched_at: float = 1_700_000_000.0, **metadata) -> RawDocument:
    return RawDocument(
        source_system=source,
        external_id=external_id,
        uri=f"test://{external_id}",
        title=title or f"Title of {external_id}",
        text=text,
        metadata=metadata,
        fetched_at=fetched_at,
    )


class ScriptedConnector(Connector):
    """A connector that replays one scripted batch per `run()`.

    An `Exception` placed in a batch is raised at that point in the walk, which
    is how a real source dies: not before the first document, but somewhere in
    the middle of a tree it was already streaming.
    """

    key = "scripted:source"

    def __init__(self, *batches: list) -> None:
        self.batches = list(batches)
        self.runs = 0

    def fetch(self, cursor):
        batch = self.batches[min(self.runs, len(self.batches) - 1)]
        self.runs += 1
        for item in batch:
            if isinstance(item, Exception):
                raise item
            yield item


class FakeHttp(HttpClient):
    """An `HttpClient` that serves a small site out of a dict.

    A URL that is not in the dict is a 404, which is also how a host with no
    robots.txt behaves - so `robots.txt` needs no entry of its own.
    """

    def __init__(self, pages: dict[str, str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.pages = pages
        self.requested: list[str] = []

    def request(self, method, url, *, headers=None, body=None, conditional=False,
                allow_status=()):
        self.requested.append(url)
        entry = self.pages.get(url)
        if entry is None:
            if 404 in allow_status:
                return Response(url, 404, {"content-type": "text/plain"}, b"")
            raise HttpError(404, url)
        return Response(url, 200, {"content-type": "text/html; charset=utf-8"},
                        entry.encode("utf-8"))


def page(body: str, *, title: str = "Widget docs", description: str = "The widget manual",
         link: str = "") -> str:
    anchor = f'<a href="{link}">next</a>' if link else ""
    return (f'<html><head><title>{title}</title>'
            f'<meta name="description" content="{description}">'
            f"</head><body><article><h1>Install</h1><p>{body}</p>{anchor}"
            f"</article></body></html>")


def filler(tag: str, n: int = 60) -> str:
    """`n` distinct words: enough to clear `min_words`, and distinct per tag so
    two pages never collide in the crawler's content-hash dedupe."""
    return " ".join(f"{tag}{i}" for i in range(n))


# ----------------------------------------------------------------------- models


class ContentHashing(unittest.TestCase):
    def test_the_same_bytes_hash_the_same_way_in_a_new_process(self):
        # The whole incremental path rests on this: `hash()` is salted per
        # process, so a hash that moved between runs would report every
        # document as changed on every run, forever.
        first = raw("a", "hello world").content_hash
        second = raw("a", "hello world", fetched_at=99.0, extra="ignored").content_hash
        self.assertEqual(first, second)
        self.assertEqual(first, "7971d3d52eb5609c")  # pinned: a moving hash is a full re-ingest

    def test_a_change_to_either_text_or_title_changes_the_hash(self):
        base = raw("a", "hello", title="Guide").content_hash
        self.assertNotEqual(base, raw("a", "hello!", title="Guide").content_hash)
        self.assertNotEqual(base, raw("a", "hello", title="Guide v2").content_hash)

    def test_the_title_text_boundary_is_not_ambiguous(self):
        # Without a separator between the parts, ("ab", "c") and ("a", "bc")
        # hash alike: retitling a document while editing its first character
        # would then read as no change at all.
        self.assertNotEqual(
            raw("a", "b", title="a").content_hash,
            raw("a", "", title="ab").content_hash,
        )


class DocumentProvenance(unittest.TestCase):
    def test_from_raw_derives_the_doc_id_from_source_and_external_id_only(self):
        # The id must survive an edit: it is what links a citation to a document
        # across runs. Only the source system and the source's own id feed it.
        one = Document.from_raw(raw("path/to/a.md", "first"), "first", {})
        two = Document.from_raw(raw("path/to/a.md", "rewritten"), "rewritten", {})
        self.assertEqual(one.doc_id, two.doc_id)

        other_source = Document.from_raw(
            raw("path/to/a.md", "first", source="github"), "first", {})
        self.assertNotEqual(one.doc_id, other_source.doc_id)

    def test_from_raw_takes_its_timestamps_from_the_fetch_not_the_clock(self):
        # `created_at` defaults to time.time(); taking it from the raw document
        # is what makes a re-run reproducible and a stale document detectable.
        doc = Document.from_raw(raw("a", "text", fetched_at=1_234_567.5), "text", {})
        self.assertEqual(doc.created_at, 1_234_567.5)
        self.assertEqual(doc.updated_at, 1_234_567.5)

    def test_from_raw_hashes_the_normalized_text_not_the_bytes_it_arrived_as(self):
        # Normalization happens between RawDocument and Document, so the two
        # hashes differ by design. A connector comparing the wrong one against
        # its cursor would report a change every time whitespace was folded.
        source = raw("a", "hello  world\r\n", title="Guide")
        doc = Document.from_raw(source, T.clean(source.text), {"kind": "file"})
        self.assertEqual(doc.text, "hello world")
        self.assertNotEqual(doc.content_hash, source.content_hash)
        self.assertEqual(doc.metadata, {"kind": "file"})
        self.assertEqual(doc.uri, "test://a")


class Chunks(unittest.TestCase):
    def test_the_context_header_is_prefixed_only_when_there_is_one(self):
        bare = Chunk(chunk_id="c1", doc_id="d1", ordinal=0, text="it depends on chunk size")
        self.assertEqual(bare.indexed_text, "it depends on chunk size")

        with_header = Chunk(chunk_id="c1", doc_id="d1", ordinal=0,
                            text="it depends on chunk size",
                            context_header="Widget docs > Tuning")
        self.assertEqual(with_header.indexed_text,
                         "Widget docs > Tuning\n\nit depends on chunk size")

    def test_the_header_is_part_of_what_is_hashed_and_counted(self):
        # The header is embedded with the body, so a chunk whose header changed
        # is a different vector and must not be served from the old cache entry.
        bare = Chunk("c1", "d1", 0, "body text here")
        headed = Chunk("c1", "d1", 0, "body text here", context_header="Guide > Setup")
        self.assertNotEqual(bare.content_hash, headed.content_hash)
        self.assertGreater(headed.token_estimate, bare.token_estimate)
        self.assertEqual(bare.token_estimate, T.estimate_tokens("body text here"))

    def test_an_empty_chunk_estimates_zero_tokens(self):
        self.assertEqual(Chunk("c1", "d1", 0, "").token_estimate, 0)


class AnswerSerialization(unittest.TestCase):
    def _answer(self) -> Answer:
        chunk = Chunk("c1", "d1", 0, "the widget accepts a size argument", char_start=10,
                      char_end=44)
        doc = Document.from_raw(raw("a", "the widget accepts a size argument"),
                                "the widget accepts a size argument", {})
        return Answer(
            question="what size?",
            text="Any positive integer [1].",
            citations=[Citation(marker=1, chunk_id="c1", doc_id="d1", title="Guide",
                                uri="test://a", quote="a size argument", score=0.87)],
            confidence=0.123456789,
            metrics={"latency_ms": 12},
            retrieved=[ScoredChunk(chunk=chunk, score=0.87654,
                                   components={"lexical": 0.5123, "dense": 0.36424},
                                   document=doc)],
        )

    def test_to_dict_publishes_the_answer_without_the_retrieval_working(self):
        out = self._answer().to_dict()
        self.assertEqual(set(out), {"question", "answer", "confidence", "abstained",
                                    "generator", "citations", "metrics"})
        self.assertEqual(out["answer"], "Any positive integer [1].")
        self.assertEqual(out["confidence"], 0.1235)  # rounded, not truncated
        self.assertEqual(out["citations"][0]["quote"], "a size argument")
        self.assertNotIn("retrieved", out)

    def test_include_retrieved_adds_the_score_breakdown_for_debugging(self):
        out = self._answer().to_dict(include_retrieved=True)
        got = out["retrieved"][0]
        self.assertEqual(got["chunk_id"], "c1")
        self.assertEqual(got["score"], 0.8765)
        self.assertEqual(got["components"], {"lexical": 0.5123, "dense": 0.3642})
        self.assertEqual(got["uri"], "test://a")  # the document's URI, not the doc_id
        self.assertEqual(got["preview"], "the widget accepts a size argument")

    def test_a_scored_chunk_with_no_document_still_cites_something(self):
        # Retrieval can outlive the document store it was built from; a citation
        # falling back to the doc_id is degraded but usable, a KeyError is not.
        orphan = ScoredChunk(chunk=Chunk("c1", "d1", 0, "body"), score=0.1)
        self.assertEqual(orphan.citation_uri, "d1")
        self.assertEqual(orphan.citation_title, "d1")

    def test_to_json_is_valid_json_and_keeps_non_ascii_readable(self):
        answer = self._answer()
        answer.text = "Größe: any positive integer"
        payload = answer.to_json(include_retrieved=True)
        self.assertIn("Größe", payload)  # ensure_ascii=False, so no \u escapes
        self.assertEqual(json.loads(payload)["answer"], answer.text)

    def test_a_metric_json_cannot_encode_does_not_lose_the_whole_answer(self):
        # BUG (fixed): `metrics` is a free-form bag every stage writes counters
        # into. One stage recording a set raised TypeError out of `to_json`,
        # discarding a finished answer at the last step over a diagnostic field.
        answer = self._answer()
        answer.metrics = {"matched_terms": {"size", "widget"}}
        self.assertIn("matched_terms", json.loads(answer.to_json())["metrics"])


class Deltas(unittest.TestCase):
    def test_touched_counts_the_work_downstream_has_to_redo(self):
        delta = IngestDelta("web:x", new=3, changed=2, unchanged=41, failed=1)
        self.assertEqual(delta.touched, 5)  # unchanged and failed are not work
        self.assertEqual(IngestDelta("web:x").touched, 0)
        self.assertEqual(delta.as_dict()["unchanged"], 41)


# ------------------------------------------------------- the connector contract


class Classification(unittest.TestCase):
    def test_a_first_run_reports_every_document_as_new(self):
        connector = ScriptedConnector([raw("a", "one"), raw("b", "two")])
        result = connector.run(MemoryStateStore())
        self.assertEqual((result.delta.new, result.delta.changed, result.delta.unchanged),
                         (2, 0, 0))
        self.assertEqual([d.external_id for d in result.documents], ["a", "b"])
        self.assertEqual(len(result), 2)

    def test_an_unchanged_document_is_counted_but_never_re_emitted(self):
        # The point of the whole cursor: re-chunking and re-embedding a document
        # whose bytes did not move is the most expensive no-op in the pipeline.
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one"), raw("b", "two")],
            [raw("a", "one"), raw("b", "TWO, rewritten")],
        )
        connector.run(state)
        second = connector.run(state)
        self.assertEqual((second.delta.new, second.delta.changed, second.delta.unchanged),
                         (0, 1, 1))
        self.assertEqual([d.external_id for d in second.documents], ["b"])

    def test_classification_ignores_timestamps_and_metadata_entirely(self):
        # Stated design decision: timestamps lie (mirrors, rebases, re-uploads,
        # clock skew). A re-fetch with a fresh clock is not a change.
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one", fetched_at=1.0, etag="v1")],
            [raw("a", "one", fetched_at=9_999.0, etag="v2")],
        )
        connector.run(state)
        second = connector.run(state)
        self.assertEqual(second.delta.unchanged, 1)
        self.assertEqual(second.documents, [])

    def test_a_retitled_document_counts_as_changed(self):
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one", title="Guide")],
            [raw("a", "one", title="Guide (2024)")],
        )
        connector.run(state)
        self.assertEqual(connector.run(state).delta.changed, 1)


class Failures(unittest.TestCase):
    def test_one_unreadable_document_does_not_abort_the_rest_of_the_walk(self):
        # The docstring's promise, at 1/80th scale: one unreadable file in a
        # 4,000-file repository must not cost the other 3,999. `text=None` is
        # what a connector hands back when a JSON field it trusted was null.
        batch = [raw(f"file{i}.md", f"contents {i}") for i in range(50)]
        batch[17] = raw("broken.md", None)  # type: ignore[arg-type]
        result = ScriptedConnector(batch).run(MemoryStateStore())

        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.delta.new, 49)
        self.assertEqual(len(result.documents), 49)
        self.assertNotIn("broken.md", [d.external_id for d in result.documents])
        self.assertEqual(len(result.delta.errors), 1)
        # The error names the document and the exception, or it is not
        # actionable: "1 failed" out of 4,000 is not a bug report.
        self.assertIn("broken.md", result.delta.errors[0])
        self.assertIn("AttributeError", result.delta.errors[0])

    def test_a_connector_whose_fetch_raises_is_recorded_not_propagated(self):
        connector = ScriptedConnector([RuntimeError("the API went away")])
        result = connector.run(MemoryStateStore())  # must not raise
        self.assertEqual(result.delta.failed, 1)
        self.assertEqual(result.documents, [])
        self.assertIn("RuntimeError: the API went away", result.delta.errors[0])
        self.assertEqual(result.delta.source_key, "scripted:source")

    def test_a_run_with_no_state_store_still_works(self):
        # Ad-hoc runs (a one-off script, a test harness) pass no store at all.
        result = ScriptedConnector([raw("a", "one")]).run()
        self.assertEqual(result.delta.new, 1)
        self.assertEqual(result.cursor["hashes"], {"a": raw("a", "one").content_hash})


class Removal(unittest.TestCase):
    def test_a_vanished_document_is_reported_and_never_deleted_here(self):
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one"), raw("b", "two")],
            [raw("a", "one")],
        )
        connector.run(state)
        second = connector.run(state)
        self.assertEqual(second.cursor["removed_last_run"], ["b"])
        # Reported only: nothing in the delta claims a deletion happened, and
        # the document is not in `documents` either.
        self.assertEqual(second.documents, [])
        self.assertNotIn("b", second.cursor["hashes"])

    def test_the_removed_list_is_capped_so_the_cursor_cannot_grow_without_bound(self):
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw(f"doc{i}", f"body {i}") for i in range(150)],
            [raw("doc0", "body 0")],
        )
        connector.run(state)
        second = connector.run(state)
        self.assertEqual(len(second.cursor["removed_last_run"]), 100)

    def test_a_source_that_dies_midway_does_not_report_the_unreached_as_removed(self):
        # BUG (fixed): `removed` was computed against whatever the walk managed
        # to see, so a source that failed on its second document reported every
        # document after it as vanished. Deletion downstream is driven off that
        # list, so a five-second API outage proposed wiping the corpus.
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one"), raw("b", "two"), raw("c", "three")],
            [raw("a", "one"), RuntimeError("connection reset"), raw("c", "three")],
        )
        connector.run(state)
        second = connector.run(state)
        self.assertEqual(second.delta.failed, 1)
        self.assertEqual(second.cursor["removed_last_run"], [])

    def test_a_source_that_dies_midway_keeps_the_hashes_it_never_reached(self):
        # BUG (fixed), the other half: the cursor was overwritten with the
        # partial hash map, so the next run saw b and c as new and re-chunked,
        # re-embedded and re-indexed documents that had never changed.
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one"), raw("b", "two"), raw("c", "three")],
            [raw("a", "one"), RuntimeError("connection reset"), raw("c", "three")],
            [raw("a", "one"), raw("b", "two"), raw("c", "three")],
        )
        connector.run(state)
        connector.run(state)
        third = connector.run(state)
        self.assertEqual((third.delta.new, third.delta.changed, third.delta.unchanged),
                         (0, 0, 3))

    def test_a_source_that_legitimately_empties_forgets_its_hashes(self):
        # BUG (fixed): the cursor said `hashes = new_hashes or seen_hashes`, so
        # a run that correctly found nothing kept the previous run's hashes.
        # The documents were reported removed and deleted downstream, and when
        # they came back byte-identical the stale hashes classified them
        # "unchanged" - so they were never re-emitted and stayed missing from
        # the index for good.
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one"), raw("b", "two")],
            [],
            [raw("a", "one"), raw("b", "two")],
        )
        connector.run(state)
        emptied = connector.run(state)
        self.assertEqual(emptied.cursor["hashes"], {})
        self.assertEqual(sorted(emptied.cursor["removed_last_run"]), ["a", "b"])

        restored = connector.run(state)
        self.assertEqual(restored.delta.new, 2)
        self.assertEqual([d.external_id for d in restored.documents], ["a", "b"])

    def test_a_document_that_failed_to_read_is_not_reported_as_removed(self):
        # BUG (fixed): a document whose hash could not be computed left no entry
        # in the new hash map, so it looked identical to one that had vanished -
        # and a file that merely failed to parse this run was queued for
        # deletion from the index.
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw("a", "one"), raw("b", "two")],
            [raw("a", "one"), raw("b", None)],  # type: ignore[arg-type]
            [raw("a", "one"), raw("b", "two")],
        )
        connector.run(state)
        second = connector.run(state)
        self.assertEqual(second.delta.failed, 1)
        self.assertEqual(second.cursor["removed_last_run"], [])
        # And the run after it sees no change, rather than re-ingesting b.
        self.assertEqual(connector.run(state).delta.unchanged, 2)


class Limits(unittest.TestCase):
    def test_limit_stops_the_walk(self):
        state = MemoryStateStore()
        connector = ScriptedConnector([raw(f"doc{i}", f"body {i}") for i in range(10)])
        result = connector.run(state, limit=3)
        self.assertEqual(len(result.documents), 3)
        self.assertEqual(result.delta.new, 3)

    def test_a_limited_run_does_not_pretend_the_rest_of_the_source_is_gone(self):
        # BUG (fixed): sampling a large source with `limit=` reported every
        # document past the limit as removed and dropped its hash, so the next
        # full run re-ingested the whole source. Sampling is exactly what a
        # first look at a big repository does.
        state = MemoryStateStore()
        connector = ScriptedConnector(
            [raw(f"doc{i}", f"body {i}") for i in range(10)],
            [raw(f"doc{i}", f"body {i}") for i in range(10)],
        )
        connector.run(state, limit=3)
        full = connector.run(state)
        self.assertEqual(full.cursor["removed_last_run"], [])
        self.assertEqual((full.delta.new, full.delta.unchanged), (7, 3))


class StateStores(unittest.TestCase):
    def test_a_cursor_survives_a_new_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "state.json"  # parent is created for us
            JsonStateStore(path).set("web:docs", {"hashes": {"a": "ff"}, "last_run": 1.5})
            reopened = JsonStateStore(path)
            self.assertEqual(reopened.get("web:docs"),
                             {"hashes": {"a": "ff"}, "last_run": 1.5})
            self.assertEqual(reopened.get("never:seen"), {})

    def test_a_write_leaves_no_temporary_file_behind(self):
        # The write is atomic via a temp file plus os.replace. A leaked .tmp per
        # run fills the state directory of a long-lived scheduler.
        with tempfile.TemporaryDirectory() as tmp:
            store = JsonStateStore(Path(tmp) / "state.json")
            for i in range(5):
                store.set(f"key{i}", {"n": i})
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ["state.json"])

    def test_the_returned_cursor_is_a_copy(self):
        # `run()` mutates the cursor it is handed; if that were the stored dict,
        # a failed run would corrupt the state it was supposed to leave alone.
        with tempfile.TemporaryDirectory() as tmp:
            store = JsonStateStore(Path(tmp) / "state.json")
            store.set("k", {"hashes": {"a": "ff"}})
            cursor = store.get("k")
            cursor["hashes"] = {}
            self.assertEqual(store.get("k"), {"hashes": {"a": "ff"}})

    def test_a_corrupt_state_file_starts_clean_instead_of_raising(self):
        # A crash mid-write, an editor that truncated the file: the next run has
        # to be a full re-ingest, which is expensive but recoverable. Raising
        # here would take the scheduler down and never recover on its own.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text('{"web:docs": {"hashes": {"a": ', "utf-8")
            store = JsonStateStore(path)
            self.assertEqual(store.get("web:docs"), {})
            store.set("web:docs", {"hashes": {}})
            self.assertEqual(json.loads(path.read_text("utf-8")), {"web:docs": {"hashes": {}}})

    def test_a_state_file_that_is_valid_json_but_not_an_object_starts_clean(self):
        # BUG (fixed): only JSONDecodeError was caught, so a file containing
        # `[]` - a truncated write that happened to land on a valid document, or
        # a hand-edit - loaded fine and then raised AttributeError from `get()`
        # on every run afterwards. That is the failure this class exists to
        # prevent, reached through a different door.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text("[]", "utf-8")
            self.assertEqual(JsonStateStore(path).get("web:docs"), {})

    def test_a_cursor_entry_that_is_not_an_object_degrades_to_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text('{"web:docs": ["not", "a", "cursor"]}', "utf-8")
            self.assertEqual(JsonStateStore(path).get("web:docs"), {})

    def test_a_connector_run_round_trips_through_the_file_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            connector = ScriptedConnector(
                [raw("a", "one")],
                [raw("a", "one")],
            )
            connector.run(JsonStateStore(path))
            second = connector.run(JsonStateStore(path))  # a fresh store, as a new run has
            self.assertEqual(second.delta.unchanged, 1)


# ------------------------------------------------------------- the web adapter


class WebAdapter(unittest.TestCase):
    SEED = "https://docs.example.com/one"
    SECOND = "https://docs.example.com/two"

    def _connector(self, pages, **options):
        http = FakeHttp(pages)
        connector = WebConnector([self.SEED], client=http, obey_robots=False,
                                 max_depth=1, **options)
        return connector, http

    def test_a_crawled_page_arrives_with_its_provenance_stamped(self):
        connector, _ = self._connector({
            self.SEED: page(filler("one"), link="/two"),
            self.SECOND: page(filler("two")),
        })
        docs = list(connector.fetch({}))
        self.assertEqual([d.external_id for d in docs], [self.SEED, self.SECOND])
        first = docs[0]
        self.assertEqual(first.source_system, "web")
        # external_id and uri are both the URL actually fetched: a reader
        # following a citation has to land on the page the text came from.
        self.assertEqual(first.uri, first.external_id)
        self.assertEqual(first.title, "Widget docs")
        self.assertIn("one0", first.text)
        self.assertGreater(first.fetched_at, 0)
        self.assertEqual(first.metadata["depth"], 0)
        self.assertEqual(docs[1].metadata["depth"], 1)
        self.assertEqual(first.metadata["status"], 200)
        self.assertEqual(first.metadata["authority"], 0.8)  # a web page is not a source of truth
        self.assertEqual(first.metadata["crawl_seed"], self.SEED)
        self.assertEqual(first.metadata["description"], "The widget manual")

    def test_a_secret_in_the_body_never_reaches_the_document(self):
        connector, _ = self._connector({
            self.SEED: page(f"{filler('one')} export GITHUB_TOKEN=ghp_{'A' * 20}"),
        })
        text = list(connector.fetch({}))[0].text
        self.assertNotIn("ghp_", text)
        self.assertIn("<redacted:github-token>", text)

    def test_a_secret_in_the_title_or_description_never_reaches_the_document(self):
        # BUG (fixed): redaction was applied to the body only. The title is
        # hashed into `Document.content_hash` and printed in every context
        # header and citation, and the description is stored beside it - so a
        # key pasted into a page's <title> was indexed verbatim and then copied
        # wherever the index went.
        connector, _ = self._connector({
            self.SEED: page(filler("one"), title=f"Deploy with AKIA{'Z' * 16}",
                            description=f"use sk-ant-{'B' * 24} to authenticate"),
        })
        doc = list(connector.fetch({}))[0]
        self.assertNotIn("AKIA", doc.title)
        self.assertIn("<redacted:aws-key-id>", doc.title)
        self.assertNotIn("sk-ant-", doc.metadata["description"])

    def test_the_crawl_report_survives_a_run_that_was_cut_short(self):
        # BUG (fixed): the report was assigned after the crawl loop, and
        # `run(limit=)` abandons the generator - so the record of what the crawl
        # did was lost in exactly the case it is needed, and the cursor stored
        # an empty report. A crawl returning 4 pages instead of 400 has to be
        # diagnosable without re-running it under a debugger.
        connector, _ = self._connector({
            self.SEED: page(filler("one"), link="/two"),
            self.SECOND: page(filler("two")),
        })
        result = connector.run(MemoryStateStore(), limit=1)
        self.assertEqual(len(result.documents), 1)
        self.assertTrue(connector.last_report, "the crawl report was lost")
        # The crawl runs one page ahead of its consumer, so two pages were
        # fetched to deliver one; the point is that the accounting survives.
        self.assertEqual(connector.last_report["fetched"], 2)
        self.assertEqual(result.cursor["last_report"], connector.last_report)
        self.assertGreater(result.cursor["last_crawl_at"], 0)

    def test_a_crawl_that_yields_nothing_degrades_into_a_report(self):
        # Every page too thin to index: no documents, no exception, and a report
        # that says "thin" rather than leaving the caller to guess.
        connector, http = self._connector({self.SEED: page("too short")})
        result = connector.run(MemoryStateStore())
        self.assertEqual(result.documents, [])
        self.assertEqual(result.delta.failed, 0)
        self.assertEqual(connector.last_report["skipped"].get("thin"), 1)
        self.assertIn(self.SEED, http.requested)

    def test_a_dead_seed_is_a_reported_error_not_a_raised_one(self):
        connector, _ = self._connector({})  # every URL 404s
        result = connector.run(MemoryStateStore())
        self.assertEqual(result.documents, [])
        self.assertEqual(connector.last_report["skipped"].get("http_404"), 1)
        self.assertEqual(connector.last_report["error_count"], 1)

    def test_the_key_identifies_the_source_across_runs(self):
        # The key is what the cursor is filed under; if it moved between runs
        # every run would be a cold start.
        self.assertEqual(WebConnector([self.SEED]).key, f"web:{self.SEED}")
        self.assertEqual(WebConnector([]).key, "web:empty")
        self.assertEqual(WebConnector([self.SEED], key="docs").key, "docs")


# ------------------------------------------------------------ text processing


class Normalization(unittest.TestCase):
    def test_control_characters_go_but_newlines_and_tabs_stay(self):
        # Layout is structure: a chunker splits on blank lines and a code block
        # is indented. Stripping tabs and newlines with the other control
        # characters would flatten a document into one paragraph.
        got = T.normalize_unicode("head\n\nbody\tcell\x00\x07 end​.")
        self.assertEqual(got, "head\n\nbody\tcell end.")

    def test_a_carriage_return_is_a_line_break_not_a_character_to_delete(self):
        # BUG (fixed): `\r` is a control character, and this ran before the
        # whitespace pass that knows how to fold it - so the lines either side
        # were glued together. "Done.\rNext" became "Done.Next", which the
        # tokenizer reads as the single token "done.next" (it keeps dotted paths
        # deliberately), leaving neither word in the index.
        self.assertEqual(T.clean("Done.\rNext step"), "Done.\nNext step")
        self.assertIn("next", T.tokenize(T.clean("Done.\rNext step")))
        self.assertEqual(T.clean("windows\r\nlines"), "windows\nlines")

    def test_normalization_folds_compatibility_forms_and_trailing_space(self):
        self.assertEqual(T.clean("ﬁle  name   \n\n\n\nnext"), "file name\n\nnext")

    def test_summarize_cuts_on_a_word_boundary(self):
        self.assertEqual(T.summarize("hello   world\n\nagain", 100), "hello world again")
        self.assertEqual(T.summarize("alpha beta gamma", 12), "alpha beta...")


class Tokenizing(unittest.TestCase):
    def test_tokenize_drops_stopwords_and_single_characters(self):
        self.assertEqual(T.tokenize("The size of a chunk is x"), ["size", "chunk"])

    def test_identifiers_and_dotted_paths_survive_as_one_token(self):
        # Half this corpus is code: splitting `oodarag.util.text` into three
        # tokens makes an exact-symbol query match every module in the tree.
        self.assertEqual(
            T.tokenize("call oodarag.util.text or src/oodarag/models.py with chunk_size"),
            ["call", "oodarag.util.text", "src/oodarag/models.py", "chunk_size"],
        )

    def test_tokenize_all_keeps_everything_for_phrase_matching(self):
        self.assertEqual(T.tokenize_all("The size of a chunk is x"),
                         ["the", "size", "of", "a", "chunk", "is", "x"])

    def test_an_empty_string_tokenizes_to_nothing(self):
        self.assertEqual(T.tokenize(""), [])
        self.assertEqual(T.tokenize_all("   \n\t "), [])


class MarkdownStructure(unittest.TestCase):
    DOC = (
        "# Widget\n"
        "intro line\n"
        "\n"
        "## Install\n"
        "run the installer\n"
        "\n"
        "```bash\n"
        "# not a heading\n"
        "widget install\n"
        "```\n"
        "\n"
        "after the fence\n"
        "\n"
        "## Tuning\n"
        "set the size\n"
    )

    def test_a_heading_inside_a_fence_does_not_start_a_section(self):
        sections = T.split_markdown_sections(self.DOC)
        bodies = [body for _, body, _ in sections]
        self.assertEqual(len(sections), 3)
        # The fence and its comment stay with the section that contains them.
        self.assertIn("# not a heading", bodies[1])
        self.assertIn("after the fence", bodies[1])

    def test_a_heading_inside_a_fence_is_not_in_the_heading_path(self):
        # BUG (fixed): `heading_path` scanned the raw text, so `# not a heading`
        # in a shell block was read as a level-1 heading. Being level 1 it
        # cleared the real chain, and every section after the fence was labelled
        # with a heading the document does not contain. That path goes into the
        # chunk's context header, which is embedded and indexed - so retrieval
        # cited a section no reader can find.
        offset = self.DOC.index("set the size")
        self.assertEqual(T.heading_path(self.DOC, offset), ["Widget", "Tuning"])
        self.assertEqual([path for path, _, _ in T.split_markdown_sections(self.DOC)],
                         [["Widget"], ["Widget", "Install"], ["Widget", "Tuning"]])

    def test_the_heading_path_is_the_chain_in_effect_at_an_offset(self):
        doc = "# A\ntext\n## B\ntext\n### C\ntext\n## D\ntext\n# E\ntext\n"
        self.assertEqual(T.heading_path(doc, doc.index("# A")), ["A"])
        self.assertEqual(T.heading_path(doc, doc.index("### C") + 6), ["A", "B", "C"])
        # A sibling heading pops the deeper level back off the chain.
        self.assertEqual(T.heading_path(doc, doc.index("## D") + 5), ["A", "D"])
        self.assertEqual(T.heading_path(doc, doc.index("# E") + 4), ["E"])
        self.assertEqual(T.heading_path(doc, 0), ["A"])

    def test_text_before_the_first_heading_is_still_a_section(self):
        sections = T.split_markdown_sections("preamble text\n\n# One\nbody\n")
        self.assertEqual([path for path, _, _ in sections], [[], ["One"]])
        self.assertEqual(sections[0][1], "preamble text")
        self.assertEqual(sections[1][2], len("preamble text\n\n"))

    def test_an_unclosed_fence_swallows_the_rest_of_the_document(self):
        # Truncated markdown is common (a page cut off mid-render). Treating the
        # tail as code keeps a stray `#` from inventing headings; the important
        # thing is that it degrades instead of raising.
        sections = T.split_markdown_sections("# One\n\n```\n# still code\nbody\n")
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0][0], ["One"])

    def test_an_empty_document_produces_no_sections(self):
        self.assertEqual(T.split_markdown_sections(""), [])
        self.assertEqual(T.heading_path("", 0), [])


class Budgets(unittest.TestCase):
    def test_estimate_tokens_uses_whichever_arm_is_larger(self):
        self.assertEqual(T.estimate_tokens(""), 0)
        self.assertEqual(T.estimate_tokens("one two three"), 3)  # word-count arm
        # Dense code has few spaces and many characters: the chars/4 arm wins.
        self.assertEqual(T.estimate_tokens("a" * 40), 10)

    def test_text_within_budget_is_returned_untouched(self):
        self.assertEqual(T.truncate_tokens("short enough", 100), "short enough")

    def test_truncation_marks_where_it_cut(self):
        got = T.truncate_tokens("word " * 100, 10)
        self.assertTrue(got.endswith(" ..."), got)
        self.assertTrue(got.startswith("word word"))

    def test_a_truncated_string_actually_fits_the_budget_it_was_given(self):
        # BUG (fixed): the cut was on characters alone, but the estimate is
        # max(separators + 1, chars / 4). One word per line - a transcript, one
        # of this package's stated corpora - truncated to "10 tokens" and came
        # back estimating 22, so a caller sizing a model context by these two
        # functions overran it by more than 2x on exactly that input.
        transcript = "line\n" * 400
        for budget in (1, 2, 5, 10, 64, 300):
            for text in (transcript, "word " * 500, "x" * 2000, "a b\nc\td " * 200):
                got = T.truncate_tokens(text, budget)
                self.assertLessEqual(T.estimate_tokens(got), budget,
                                     f"budget={budget} got={got[:40]!r}")

    def test_a_budget_of_zero_leaves_nothing(self):
        # Previously returned " ...", which is a token of nothing pretending to
        # be content - and a caller that asked for zero has no room for it.
        self.assertEqual(T.truncate_tokens("some text here", 0), "")
        self.assertEqual(T.truncate_tokens("", 0), "")


class Redaction(unittest.TestCase):
    def test_every_credential_shape_in_the_list_is_caught(self):
        cases = [
            (f"ghp_{'A' * 22}", "<redacted:github-token>"),
            (f"gho_{'B' * 30}", "<redacted:github-token>"),
            (f"sk-ant-api03-{'C' * 40}", "<redacted:anthropic-key>"),
            (f"sk-{'D' * 44}", "<redacted:api-key>"),
            (f"AKIA{'Z' * 16}", "<redacted:aws-key-id>"),
            (f"xoxb-{'1' * 12}-{'2' * 12}", "<redacted:slack-token>"),
        ]
        for secret, marker in cases:
            with self.subTest(secret=secret[:8]):
                got = T.redact_secrets(f"the value is {secret} and that is all")
                self.assertNotIn(secret, got)
                self.assertIn(marker, got)

    def test_a_bearer_header_keeps_its_scheme_and_loses_its_credential(self):
        got = T.redact_secrets(f"Authorization: Bearer {'e' * 40}\nAccept: text/html")
        self.assertEqual(got, "Authorization: Bearer <redacted>\nAccept: text/html")

    def test_a_private_key_block_goes_whole(self):
        got = T.redact_secrets(
            "config:\n-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEow\nIBAAKC\n-----END RSA PRIVATE KEY-----\ndone")
        self.assertEqual(got, "config:\n<redacted:private-key>\ndone")
        self.assertNotIn("MIIEow", got)

    def test_an_assignment_is_redacted_in_every_shape_it_is_written(self):
        # BUG (fixed): the separator had to follow the key name immediately, so
        # the JSON spelling - by far the most common way a credential is leaked
        # in the config files and pasted chat logs these connectors read - went
        # straight into the index.
        for line in ('{"password": "hunter2hunter2"}',
                     "password = hunter2hunter2",
                     "api_key: abcdefghijkl0123",
                     "API-KEY=abcdefghijkl0123",
                     "{'secret': 'abcdefghijkl0123'}"):
            with self.subTest(line=line):
                got = T.redact_secrets(line)
                self.assertIn("<redacted>", got)
                self.assertNotIn("hunter2hunter2", got)
                self.assertNotIn("abcdefghijkl0123", got)

    def test_prose_about_tokens_and_secrets_is_left_alone(self):
        # The redactor runs over every document in the corpus, and this pipeline
        # is documented in prose that uses all of these words. Mangling them
        # would corrupt the very corpus it is meant to protect.
        prose = ("The token budget is a soft budget: pass a secret to the client and it "
                 "reads the password from the environment. An api_key is not a token.")
        self.assertEqual(T.redact_secrets(prose), prose)

    def test_redaction_of_clean_text_is_a_no_op(self):
        for text in ("", "just some ordinary words", "sk-short", "AKIA"):
            self.assertEqual(T.redact_secrets(text), text)


if __name__ == "__main__":
    unittest.main()
