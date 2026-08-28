"""Tests for `ooda ingest`, the command that actually runs a connector.

The interesting behaviour is not the happy path, it is the *second* run. A
connector is incremental: it returns only what is new or changed. So the naive
thing - rewrite the output file each run - deletes every document that happened
not to change, and does it during the quietest possible run, the one that
reports "unchanged 1, written 0". That bug was live until a real crawl of a real
site was run twice in a row, which is why it is pinned here.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from oodarag.cli import EXIT_ERROR, EXIT_OK, _write_documents, main
from oodarag.models import RawDocument


def doc(external_id: str, text: str = "body") -> RawDocument:
    return RawDocument(
        source_system="web",
        external_id=external_id,
        uri=f"https://example.test/{external_id}",
        title=external_id,
        text=text,
    )


class WriteDocumentsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "raw" / "web.jsonl"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def lines(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text("utf-8").splitlines() if line]

    def test_fresh_writes_a_snapshot(self) -> None:
        self.assertEqual(_write_documents(self.path, [doc("a"), doc("b")], truncate=True), 2)
        self.assertEqual([d["external_id"] for d in self.lines()], ["a", "b"])

    def test_fresh_replaces_what_was_there(self) -> None:
        _write_documents(self.path, [doc("a"), doc("b")], truncate=True)
        _write_documents(self.path, [doc("c")], truncate=True)
        self.assertEqual([d["external_id"] for d in self.lines()], ["c"])

    def test_incremental_appends_rather_than_replacing(self) -> None:
        _write_documents(self.path, [doc("a")], truncate=True)
        _write_documents(self.path, [doc("b")], truncate=False)
        self.assertEqual([d["external_id"] for d in self.lines()], ["a", "b"])

    def test_an_empty_incremental_run_leaves_the_file_alone(self) -> None:
        """The regression: 'unchanged 1, written 0' used to truncate the file."""
        _write_documents(self.path, [doc("a")], truncate=True)
        before = self.path.read_bytes()
        self.assertEqual(_write_documents(self.path, [], truncate=False), 0)
        self.assertEqual(self.path.read_bytes(), before)

    def test_an_empty_fresh_run_does_replace(self) -> None:
        """--fresh is a deliberate full re-read, so an empty source means empty."""
        _write_documents(self.path, [doc("a")], truncate=True)
        _write_documents(self.path, [], truncate=True)
        self.assertEqual(self.lines(), [])

    def test_a_failed_snapshot_leaves_the_previous_one_intact(self) -> None:
        _write_documents(self.path, [doc("a")], truncate=True)

        class Exploding(list):
            def __iter__(self):
                raise OSError("disk went away")

        with self.assertRaises(OSError):
            _write_documents(self.path, Exploding(), truncate=True)
        self.assertEqual([d["external_id"] for d in self.lines()], ["a"])
        self.assertFalse(list(self.path.parent.glob("*.tmp")), "temp file must be cleaned up")

    def test_documents_round_trip_with_their_provenance(self) -> None:
        _write_documents(self.path, [doc("a", "naïve café")], truncate=True)
        record = self.lines()[0]
        self.assertEqual(record["text"], "naïve café")
        self.assertEqual(record["uri"], "https://example.test/a")
        self.assertEqual(record["content_hash"], doc("a", "naïve café").content_hash)


class IngestCommandTestCase(unittest.TestCase):
    """Argument handling only - nothing here touches the network."""

    def run_cli(self, argv: list[str]) -> tuple[int, str]:
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = main(argv)
        return code, err.getvalue()

    def test_github_requires_owner_slash_repo(self) -> None:
        code, err = self.run_cli(["ingest", "github", "not-a-repo"])
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("OWNER/REPO", err)

    def test_web_requires_a_seed(self) -> None:
        with self.assertRaises(SystemExit):  # argparse rejects it before we run
            self.run_cli(["ingest", "web"])

    def test_help_lists_both_sources(self) -> None:
        from oodarag.cli import build_parser

        args = build_parser().parse_args(["ingest", "web", "https://x.test"])
        self.assertTrue(callable(args.func))
        self.assertEqual(args.seeds, ["https://x.test"])
        args = build_parser().parse_args(["ingest", "github", "o/r", "--ref", "main"])
        self.assertEqual((args.repo, args.ref), ("o/r", "main"))

    def test_defaults_are_incremental_not_fresh(self) -> None:
        from oodarag.cli import build_parser

        args = build_parser().parse_args(["ingest", "web", "https://x.test"])
        self.assertFalse(args.fresh, "the default must never replace existing output")
        self.assertEqual(EXIT_OK, 0)


if __name__ == "__main__":
    unittest.main()
