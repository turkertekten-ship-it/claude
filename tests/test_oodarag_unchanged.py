"""Silence is not absence: a saving must not read as a deletion.

Every cost optimisation in this pipeline works by not transferring something —
a 304 from a conditional GET, a git blob sha that matches, a head commit that
has not moved. Each means "still there, still the same". The document is then
never yielded, and a base class that infers absence from silence reads it as a
deletion.

Measured against the real GitHub API before the fix: a second run over an
unchanged repository took the head-sha short circuit, yielded nothing, and
reported every file in `removed_last_run` while dropping every stored hash — so
the optimisation proposed wiping the index and paid for a full re-ingest on the
run after. These tests pin the contract that stops it, for the base class and
for both connectors that rely on it.
"""

from __future__ import annotations

import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector, JsonStateStore, MemoryStateStore
from oodarag.models import RawDocument
from oodarag.scrape.crawler import CrawlReport


def doc(external_id: str, text: str) -> RawDocument:
    return RawDocument(source_system="t", external_id=external_id,
                       uri=f"https://x.test/{external_id}", title=external_id, text=text)


class Fake(Connector):
    """Yields some documents and claims others are unchanged without sending them."""

    key = "fake:source"

    def __init__(self, yields: list[RawDocument], unchanged: set[str] | None = None) -> None:
        self._yields = yields
        self._unchanged = unchanged or set()

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        yield from self._yields

    def unchanged_external_ids(self) -> set[str]:
        return set(self._unchanged)


class TestBaseContract(unittest.TestCase):
    def test_the_default_is_to_claim_nothing(self):
        state = MemoryStateStore()
        Fake([doc("a", "one")]).run(state)
        # A connector that does not override the hook must behave exactly as
        # before: absence still means absence for it.
        result = Fake([]).run(state)
        self.assertEqual(state.get("fake:source")["removed_last_run"], ["a"])
        self.assertEqual(result.delta.unchanged, 0)

    def test_a_claimed_id_is_counted_unchanged_and_not_removed(self):
        state = MemoryStateStore()
        Fake([doc("a", "one"), doc("b", "two")]).run(state)
        result = Fake([], unchanged={"a", "b"}).run(state)
        self.assertEqual((result.delta.new, result.delta.changed), (0, 0))
        self.assertEqual(result.delta.unchanged, 2)
        self.assertEqual(state.get("fake:source")["removed_last_run"], [])

    def test_the_hashes_survive_so_the_next_run_does_not_re_ingest(self):
        state = MemoryStateStore()
        Fake([doc("a", "one")]).run(state)
        before = dict(state.get("fake:source")["hashes"])
        Fake([], unchanged={"a"}).run(state)
        self.assertEqual(state.get("fake:source")["hashes"], before)
        # Third run, the document comes back byte-identical: still unchanged,
        # never re-emitted. Losing the hash here is what turned a saving into a
        # full re-ingest.
        third = Fake([doc("a", "one")]).run(state)
        self.assertEqual(third.delta.unchanged, 1)
        self.assertEqual(third.documents, [])

    def test_claiming_an_id_that_was_yielded_does_not_double_count(self):
        state = MemoryStateStore()
        Fake([doc("a", "one")]).run(state)
        result = Fake([doc("a", "CHANGED")], unchanged={"a"}).run(state)
        self.assertEqual(result.delta.changed, 1)
        self.assertEqual(result.delta.unchanged, 0, "the yielded document decides")

    def test_claiming_an_unknown_id_says_nothing(self):
        # "Unchanged since what?" - with no prior hash the claim carries no
        # information, so it must not invent a document.
        state = MemoryStateStore()
        result = Fake([], unchanged={"never-seen"}).run(state)
        self.assertEqual(result.delta.unchanged, 0)
        self.assertEqual(state.get("fake:source")["hashes"], {})

    def test_it_survives_a_real_state_file_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            Fake([doc("a", "one")]).run(JsonStateStore(path))
            Fake([], unchanged={"a"}).run(JsonStateStore(path))
            stored = JsonStateStore(path).get("fake:source")
            self.assertEqual(stored["removed_last_run"], [])
            self.assertEqual(list(stored["hashes"]), ["a"])


class TestCrawlReportCarriesNotModified(unittest.TestCase):
    def test_a_report_records_the_urls_a_server_said_were_unchanged(self):
        report = CrawlReport()
        self.assertEqual(report.not_modified, [])
        report.not_modified.append("https://x.test/a")
        self.assertEqual(report.as_dict()["not_modified"], 1)

    def test_the_web_connector_exposes_them_as_unchanged_ids(self):
        from oodarag.ingest.web import WebConnector

        conn = WebConnector(seeds=["https://x.test/"])
        self.assertEqual(conn.unchanged_external_ids(), set())
        conn._not_modified = {"https://x.test/a"}
        self.assertEqual(conn.unchanged_external_ids(), {"https://x.test/a"})


class TestGitHubShortCircuitsClaimTheirFiles(unittest.TestCase):
    def test_the_head_short_circuit_claims_every_stored_file(self):
        from oodarag.ingest.github import GitHubConnector

        conn = GitHubConnector(owner="acme", repo="widget")
        conn._unchanged = {"acme/widget#file:a.md"}
        self.assertEqual(conn.unchanged_external_ids(), {"acme/widget#file:a.md"})

    def test_the_id_shape_matches_what_the_file_documents_use(self):
        # If these two ever diverge the claim silently matches nothing and the
        # bug returns without a single test going red.
        from oodarag.ingest.github import GitHubConnector

        conn = GitHubConnector(owner="acme", repo="widget")
        built = conn._file_document("a.md", "x", 1, "s" * 40, "b" * 40, "main")
        self.assertEqual(built.external_id, f"{conn.slug}#file:a.md")


if __name__ == "__main__":
    unittest.main()
