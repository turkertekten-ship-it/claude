"""One date parser, and the dates a source actually sends reaching retrieval.

Four connectors read a real date from their source and filed it in metadata,
where nothing scores it. Every document in a run then shared one `fetched_at`,
which made the recency factor a constant - see LEARNINGS L43/L44. This file
pins two things:

* `util.dates.to_timestamp` parses what these sources send, and returns None
  rather than guessing at anything else;
* each connector's own output carries that date through to `Document.updated_at`.

Expectations here are derived from the ISO strings with `calendar.timegm`, a
different stdlib implementation reading the same input, rather than copied from
a run of the code under test.
"""

from __future__ import annotations

import calendar
import json
import os
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from oodarag.models import Document, RawDocument
from oodarag.retrieve.rerank import _as_timestamp
from oodarag.util.dates import to_timestamp


def from_raw(raw: RawDocument) -> Document:
    """`Document.from_raw` as the pipeline calls it: the raw text and metadata."""
    return Document.from_raw(raw, raw.text, dict(raw.metadata))


def utc_epoch(text: str) -> float:
    """The expected timestamp, derived independently of `to_timestamp`.

    `time.strptime` + `calendar.timegm` is a second implementation of the same
    conversion; agreeing with it is evidence the parser is right rather than
    evidence it is unchanged.
    """
    return float(calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%S")))


class ToTimestampTest(unittest.TestCase):
    def test_the_iso_shapes_the_sources_actually_send(self):
        # GitHub sends a trailing Z; a page's <time datetime> may send an
        # offset or nothing at all. All three name the same instant.
        expected = utc_epoch("2026-01-02T03:04:05")
        for text in ("2026-01-02T03:04:05Z",
                     "2026-01-02T03:04:05+00:00",
                     "2026-01-02T03:04:05"):
            with self.subTest(text=text):
                self.assertEqual(to_timestamp(text), expected)

    def test_an_offset_is_applied_rather_than_ignored(self):
        # +02:00 is two hours *earlier* in UTC. Dropping the offset instead of
        # applying it is the quiet failure: it parses, and it is wrong by hours.
        self.assertEqual(to_timestamp("2026-01-02T05:04:05+02:00"),
                         utc_epoch("2026-01-02T03:04:05"))

    def test_a_naive_stamp_is_read_as_utc_not_as_local_time(self):
        """The sources are APIs; their naive stamps are UTC.

        `datetime.timestamp()` on a naive value reads it as *local* time, so
        this is only correct because the parser attaches UTC explicitly. Under
        a non-UTC TZ the unfixed version is off by the offset.
        """
        previous = os.environ.get("TZ")
        try:
            os.environ["TZ"] = "Asia/Kolkata"  # +05:30, so a half-hour shift shows
            time.tzset()
            self.assertEqual(to_timestamp("2026-01-02T03:04:05"),
                             utc_epoch("2026-01-02T03:04:05"))
        finally:
            if previous is None:
                os.environ.pop("TZ", None)
            else:
                os.environ["TZ"] = previous
            time.tzset()

    def test_numbers_pass_through_as_themselves(self):
        for value, expected in ((1767322445, 1767322445.0),
                                (1767322445.5, 1767322445.5),
                                ("1767322445", 1767322445.0)):
            with self.subTest(value=value):
                self.assertEqual(to_timestamp(value), expected)

    def test_what_the_source_did_not_say_is_none_and_not_a_guess(self):
        """The failure path, asserted to fire.

        None means "the source did not say", which `Document.from_raw` reads as
        "fall back to the fetch time". Returning 0.0 or now() instead would make
        an undated document either ancient or brand new, and neither is a claim
        the source made.
        """
        for absent in (None, "", "   ", "not a date", "2026-13-45",
                       "yesterday", [], {}):
            with self.subTest(value=absent):
                self.assertIsNone(to_timestamp(absent))

    def test_a_flag_is_not_a_date(self):
        # bool is an int subclass, so the numeric branch would turn True into
        # 1970-01-01T00:00:01 - an ancient document conjured from a flag.
        self.assertIsNone(to_timestamp(True))
        self.assertIsNone(to_timestamp(False))


class RerankReadsWhatConnectorsWriteTest(unittest.TestCase):
    """Two stages that parse the same field must parse it identically.

    Tokenizing that differed between indexing and reranking cost this project
    nine eval cases (L24). Date parsing has the same shape: nothing errors, one
    stage simply sees a date the other cannot.
    """

    def test_every_shape_the_parser_accepts_is_a_date_the_scorer_can_read(self):
        for text in ("2026-01-02T03:04:05Z", "2026-01-02T03:04:05+02:00",
                     "2026-01-02T03:04:05", "1767322445", 1767322445):
            with self.subTest(value=text):
                self.assertEqual(_as_timestamp(text), to_timestamp(text))

    def test_the_scorer_reports_unknown_for_what_the_parser_rejects(self):
        # The scorer's contract is 0.0 for unknown, which its caller reads as
        # "neither fresh nor stale"; the parser's is None. They must disagree
        # only in that representation, never about which values are dates.
        for absent in (None, "", "not a date", True):
            with self.subTest(value=absent):
                self.assertIsNone(to_timestamp(absent))
                self.assertEqual(_as_timestamp(absent), 0.0)


class DocumentFallbackTest(unittest.TestCase):
    def test_a_document_prefers_the_sources_date_over_the_fetch_time(self):
        raw = RawDocument(source_system="t", external_id="1", uri="u", title="t",
                          text="body", fetched_at=2_000_000.0,
                          source_updated_at=1_000_000.0)
        self.assertEqual(from_raw(raw).updated_at, 1_000_000.0)

    def test_an_undated_document_falls_back_to_the_fetch_time(self):
        raw = RawDocument(source_system="t", external_id="1", uri="u", title="t",
                          text="body", fetched_at=2_000_000.0)
        self.assertIsNone(raw.source_updated_at)
        self.assertEqual(from_raw(raw).updated_at, 2_000_000.0)


class SourceDateReachesTheDocumentTest(unittest.TestCase):
    """Each connector's own output, not a hand-built RawDocument.

    Asserting on a document assembled in the test proves what the dataclass
    does; only running the connector proves the connector reads the field. That
    distinction is what L44 was about - the earlier version of this check passed
    against a chunk nothing in the pipeline could produce.
    """

    def test_a_chat_session_is_dated_by_its_last_turn(self):
        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.chat import ChatTranscriptConnector

        first, last = "2026-03-01T10:00:00Z", "2026-03-04T18:30:00Z"
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "session-abc.jsonl"
            path.write_text("\n".join(json.dumps(entry) for entry in [
                {"type": "user", "timestamp": first, "cwd": "/w",
                 "message": {"role": "user",
                             "content": "How does the crawler bound its work?"}},
                {"type": "assistant", "timestamp": last,
                 "message": {"role": "assistant",
                             "content": "Requests, bytes and wall clock, each budgeted."}},
            ]), "utf-8")

            docs = ChatTranscriptConnector(root=tmp).run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].source_updated_at, utc_epoch("2026-03-04T18:30:00"),
                         "the session is dated by its last turn, not its first")
        self.assertEqual(from_raw(docs[0]).updated_at,
                         utc_epoch("2026-03-04T18:30:00"))
        self.assertLess(docs[0].source_updated_at, docs[0].fetched_at,
                        "a transcript written in the past read as freshly updated")

    def test_a_video_is_dated_by_its_publication(self):
        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.youtube import YouTubeConnector

        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "videos.json"
            manifest.write_text(json.dumps({"videos": [{
                "video_id": "T-D1OfcDW1M",
                "title": "What is Retrieval-Augmented Generation?",
                "channel": "IBM Technology",
                "published": "2023-08-23T00:00:00Z",
            }]}), "utf-8")
            docs = YouTubeConnector(manifest=manifest, allow_network=False) \
                .run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0].source_updated_at, utc_epoch("2023-08-23T00:00:00"))
        self.assertEqual(from_raw(docs[0]).updated_at,
                         utc_epoch("2023-08-23T00:00:00"))

    def test_an_undated_video_is_not_given_a_date(self):
        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.youtube import YouTubeConnector

        with TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "videos.json"
            manifest.write_text(json.dumps({"videos": [
                {"video_id": "T-D1OfcDW1M", "title": "Untimestamped talk"}]}), "utf-8")
            docs = YouTubeConnector(manifest=manifest, allow_network=False) \
                .run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1)
        self.assertIsNone(docs[0].source_updated_at,
                          "a missing publication date was invented")
        self.assertEqual(from_raw(docs[0]).updated_at, docs[0].fetched_at)

    def test_a_web_page_is_dated_by_its_own_time_element(self):
        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.web import WebConnector
        from tests.support.httpserver import Route, TestSite

        html = """<html><head><title>Bounding a crawl</title></head><body>
        <article><h1>Bounding a crawl</h1>
        <p>Published <time datetime="2025-11-09T08:00:00Z">last November</time>.</p>
        <p>A crawl is bounded by requests, bytes, depth and wall clock, so that
        a redirect loop costs a budget rather than an afternoon. The budget is
        spent on fetches, not on accepted pages, because a loop that rejects
        every page it fetches is still a loop and still costs an afternoon.</p>
        <p>Each bound is checked before the request is made rather than after
        the response arrives, so that a server which answers slowly cannot
        spend more of the wall clock than the budget allows it to spend.</p>
        </article></body></html>"""

        with TestSite({"/": Route(body=html),
                       "/robots.txt": Route(body="User-agent: *\nAllow: /",
                                            content_type="text/plain")}) as site:
            docs = WebConnector([site.url("/")], max_pages=1, max_depth=0) \
                .run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1, "the test page was not crawled")
        self.assertEqual(docs[0].metadata.get("published"), "2025-11-09T08:00:00Z")
        self.assertEqual(docs[0].source_updated_at, utc_epoch("2025-11-09T08:00:00"),
                         "the page stated its date and the connector discarded it")
        self.assertEqual(from_raw(docs[0]).updated_at,
                         utc_epoch("2025-11-09T08:00:00"))

    def test_an_undated_web_page_falls_back_to_when_it_was_fetched(self):
        from oodarag.ingest.base import MemoryStateStore
        from oodarag.ingest.web import WebConnector
        from tests.support.httpserver import Route, TestSite

        html = """<html><head><title>No date here</title></head><body>
        <article><h1>No date here</h1>
        <p>This page states no publication date anywhere in its markup, so the
        only honest answer about its age is when it was fetched. There is no
        time element here, no article published time, no date meta tag and no
        Dublin Core date, which is the ordinary case for a page on the web.</p>
        <p>An undated page must not be scored as though it were published on
        the day it happened to be crawled, because that would make every page
        in a crawl equally and falsely fresh.</p>
        </article></body></html>"""

        with TestSite({"/": Route(body=html),
                       "/robots.txt": Route(body="User-agent: *\nAllow: /",
                                            content_type="text/plain")}) as site:
            docs = WebConnector([site.url("/")], max_pages=1, max_depth=0) \
                .run(MemoryStateStore()).documents

        self.assertEqual(len(docs), 1)
        self.assertIsNone(docs[0].source_updated_at)
        self.assertEqual(from_raw(docs[0]).updated_at, docs[0].fetched_at)


if __name__ == "__main__":
    unittest.main()
