"""How a broken reference is resolved to the path a proposal will create.

Split out from the detector's own tests because this is the half that can do
damage. `docs.broken_ref` produces `safe`-tier proposals, which means they are
applied unattended - so if the resolution picks the wrong candidate, the loop
quietly creates a file at a path nobody referenced and nobody will ever look
for, every night, until someone notices the litter.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from oodarag.reflect.detect.base import DetectContext, build_detectors
from oodarag.reflect.detect.docs import _resolutions
from oodarag.reflect.models import KIND_FILE, Signal


class TestReferenceResolutionOrder(unittest.TestCase):
    """The head of the list is what gets created, so its order is load-bearing."""

    def test_markdown_links_stay_document_relative(self) -> None:
        """A relative link is doc-relative by definition; that is what it means."""
        self.assertEqual(
            _resolutions("docs/adr/0002.md", "0001-zero.md", "link")[0],
            "docs/adr/0001-zero.md",
        )

    def test_code_span_with_a_directory_is_repository_relative(self) -> None:
        """`internal/PLAN.md` quoted inside docs/adr/ means the one at the root."""
        candidates = _resolutions("docs/adr/0002.md", "internal/PLAN.md", "code")
        self.assertEqual(candidates[0], "internal/PLAN.md")
        self.assertIn("docs/adr/internal/PLAN.md", candidates,
                      "the other reading is still checked before calling it missing")

    def test_bare_filename_in_a_code_span_stays_document_relative(self) -> None:
        """A sibling file cited by name is beside the document, not at the root."""
        self.assertEqual(
            _resolutions("docs/adr/0002.md", "0001-zero.md", "code")[0],
            "docs/adr/0001-zero.md",
        )

    def test_a_document_at_the_root_has_one_reading(self) -> None:
        self.assertEqual(_resolutions("README.md", "internal/PLAN.md", "link"),
                         ["internal/PLAN.md"])

    def test_references_escaping_the_workspace_are_refused(self) -> None:
        """Never ours to check, and never ours to create."""
        self.assertEqual(_resolutions("docs/a.md", "../../etc/passwd", "link"), [])
        self.assertEqual(_resolutions("docs/a.md", "/etc/passwd", "link"), [])


class TestProposedPathIsTheReferencedOne(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def doc(self, rel: str, body: str) -> Signal:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return Signal(kind=KIND_FILE, source="workspace:files", text=body, uri=rel,
                      session="workspace", metadata={"is_doc": True, "ext": ".md"})

    def proposals_for(self, signals: list[Signal]) -> list[tuple[str, str]]:
        ctx = DetectContext(signals=signals, root=self.root, now=time.time())
        out: list[tuple[str, str]] = []
        for detector in build_detectors(enabled=["docs.broken_ref"]):
            for finding in detector.run(ctx):
                for proposal in detector.run_propose(finding, ctx):
                    out.extend((proposal.risk, edit.path) for edit in proposal.edits)
        return out

    def test_nested_doc_quoting_a_root_path_creates_it_at_the_root(self) -> None:
        signal = self.doc("docs/adr/0002.md", "See `internal/PLAN.md` for the plan.\n")
        self.assertEqual(self.proposals_for([signal]), [("safe", "internal/PLAN.md")])

    def test_an_existing_target_produces_nothing(self) -> None:
        (self.root / "internal").mkdir()
        (self.root / "internal" / "PLAN.md").write_text("here", encoding="utf-8")
        signal = self.doc("docs/adr/0002.md", "See `internal/PLAN.md` for the plan.\n")
        self.assertEqual(self.proposals_for([signal]), [])

    def test_two_documents_naming_one_missing_file_agree_on_the_path(self) -> None:
        """They collide, and the Decide stage settles it - but only if they agree."""
        signals = [
            self.doc("README.md", "See [the plan](internal/PLAN.md).\n"),
            self.doc("docs/adr/0002.md", "the README links to `internal/PLAN.md`\n"),
        ]
        paths = {path for _risk, path in self.proposals_for(signals)}
        self.assertEqual(paths, {"internal/PLAN.md"})


if __name__ == "__main__":
    unittest.main()
