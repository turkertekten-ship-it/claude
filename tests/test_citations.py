"""Tests for the `citations` checker.

Every fixture is a real tree on disk, read through a real `RepoIndex`. The
subset reader for the source store is the part most worth pinning down: its
failure mode is not missing a broken citation, it is failing to parse a file
and then reporting the whole repository's provenance as fabricated. The
`UnreadableStore` cases exist to keep that distinction honest.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.citations import SOURCE_STORES, CitationsChecker
from tools.claims import RepoIndex
from tools.evidence import EvidenceKind, Severity, Verdict
from tools.registry import CheckConfig, registered

STORE = "provenance/sources.yaml"
UNKNOWNS = "provenance/unknowns.md"

TWO_SOURCES = (
    "sources:\n"
    "  - id: S-1\n"
    "    kind: repository\n"
    "    ref: example/repo\n"
    "  - id: S-2\n"
    "    kind: measurement\n"
    "    command: make test\n"
)


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


class CitationsCase(unittest.TestCase):
    def findings(self, files: dict[str, str], config: CheckConfig | None = None):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        write_tree(root, files)
        repo = RepoIndex(root)
        return root, list(CitationsChecker().check(repo, config or CheckConfig()))

    def codes(self, files: dict[str, str]) -> list[str]:
        _, found = self.findings(files)
        return [f.code for f in found]


class TruePositives(CitationsCase):
    def test_tag_with_no_matching_entry_is_contradicted(self):
        root, found = self.findings(
            {
                STORE: TWO_SOURCES,
                "README.md": "The suite passes `[src:S-9]` today.\n",
                "docs/note.md": "Backed by `[src:S-1]` and `[src:S-2]`.\n",
            }
        )
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.checker, "citations")
        self.assertEqual(finding.code, "SRC_UNRESOLVED")
        self.assertEqual(finding.verdict, Verdict.CONTRADICTED)
        self.assertEqual(finding.severity, Severity.ERROR)
        self.assertEqual(finding.claim.path, "README.md")
        self.assertEqual(finding.claim.line, 1)
        self.assertIn("S-9", finding.detail)

    def test_claim_is_quoted_verbatim_from_the_line(self):
        root, found = self.findings(
            {STORE: TWO_SOURCES, "docs/n.md": "one\ntwo\nA figure `[src:S-4]` here.\n"}
        )
        claim = found[0].claim
        line = (root / claim.path).read_text().split("\n")[claim.line - 1]
        self.assertIn(claim.text, line)
        self.assertEqual(claim.line, 3)

    def test_evidence_names_the_citation_site_and_the_store(self):
        _, found = self.findings({STORE: TWO_SOURCES, "README.md": "See `[src:S-9]`.\n"})
        kinds = [e.kind for e in found[0].evidence]
        self.assertIn(EvidenceKind.FILE, kinds)
        self.assertIn(EvidenceKind.ABSENCE, kinds)
        cited = next(e for e in found[0].evidence if e.kind is EvidenceKind.FILE)
        self.assertEqual((cited.path, cited.line), ("README.md", 1))
        absence = next(e for e in found[0].evidence if e.kind is EvidenceKind.ABSENCE)
        self.assertEqual(absence.searched, (STORE,))
        self.assertIn("S-1", absence.summary)

    def test_a_missing_store_is_reported_once_and_names_what_was_looked_for(self):
        _, found = self.findings(
            {"README.md": "One `[src:S-1]`.\n", "docs/n.md": "Two `[src:S-2]`.\n"}
        )
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.code, "SRC_STORE_MISSING")
        self.assertEqual(finding.verdict, Verdict.CONTRADICTED)
        self.assertEqual(finding.severity, Severity.ERROR)
        self.assertEqual(finding.claim.path, "README.md")
        absence = next(e for e in finding.evidence if e.kind is EvidenceKind.ABSENCE)
        self.assertEqual(absence.searched, SOURCE_STORES)
        measured = next(e for e in finding.evidence if e.kind is EvidenceKind.VALUE)
        self.assertEqual(measured.value, 2)

    def test_unknown_id_absent_from_the_unknowns_file_is_a_warning(self):
        _, found = self.findings(
            {
                UNKNOWNS: "### U-1 - what is this for?\n\nNot yet answered.\n",
                "README.md": "The target is open; see U-9 in the unknowns file.\n",
            }
        )
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.code, "UNKNOWN_UNRESOLVED")
        self.assertEqual(finding.verdict, Verdict.UNSUPPORTED)
        self.assertEqual(finding.severity, Severity.WARN)
        self.assertEqual(finding.claim.path, "README.md")
        absence = next(e for e in finding.evidence if e.kind is EvidenceKind.ABSENCE)
        self.assertEqual(absence.searched, (UNKNOWNS,))

    def test_an_entry_nothing_cites_is_info(self):
        root, found = self.findings({STORE: TWO_SOURCES, "README.md": "Backed `[src:S-1]`.\n"})
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.code, "SRC_UNCITED")
        self.assertEqual(finding.verdict, Verdict.UNSUPPORTED)
        self.assertEqual(finding.severity, Severity.INFO)
        self.assertEqual(finding.claim.path, STORE)
        self.assertEqual(finding.claim.line, 5)
        line = (root / STORE).read_text().split("\n")[finding.claim.line - 1]
        self.assertIn(finding.claim.text, line)
        self.assertIn("S-2", finding.detail)

    def test_a_citation_in_a_python_docstring_is_scanned(self):
        _, found = self.findings(
            {
                STORE: TWO_SOURCES,
                "src/m.py": (
                    '"""Sixteen files were counted `[src:S-8]`.\n\n'
                    'Baseline `[src:S-1]`, measured `[src:S-2]`.\n"""\n'
                ),
            }
        )
        self.assertEqual([f.code for f in found], ["SRC_UNRESOLVED"])
        self.assertEqual(found[0].claim.path, "src/m.py")


class TrueNegatives(CitationsCase):
    def test_a_tag_that_resolves_says_nothing(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: TWO_SOURCES,
                    "README.md": "One `[src:S-1]` and two `[src:S-2]`.\n",
                }
            ),
            [],
        )

    def test_list_items_at_the_parents_indentation_still_parse(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: "sources:\n- id: S-1\n  kind: file\n- id: S-2\n  kind: file\n",
                    "README.md": "One `[src:S-1]`, two `[src:S-2]`.\n",
                }
            ),
            [],
        )

    def test_quoted_ids_and_trailing_comments_parse(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: '# header\n\nsources:\n  - id: "S-1"  # the baseline\n    kind: file\n',
                    "README.md": "Backed `[src:S-1]`.\n",
                }
            ),
            [],
        )

    def test_a_flat_mapping_of_id_to_mapping_parses(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: "S-1:\n  kind: file\n  ref: a\nS-2:\n  kind: file\n  ref: b\n",
                    "README.md": "One `[src:S-1]`, two `[src:S-2]`.\n",
                }
            ),
            [],
        )

    def test_a_recorded_unknown_id_says_nothing(self):
        self.assertEqual(
            self.codes(
                {
                    UNKNOWNS: "### U-3 - is there a quality target?\n\nUndetermined.\n",
                    "README.md": "No target has been set; see U-3 in the unknowns file.\n",
                }
            ),
            [],
        )

    def test_an_entry_cited_from_a_python_comment_is_not_uncited(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: TWO_SOURCES,
                    "README.md": "One `[src:S-1]`.\n",
                    "src/m.py": "# measured at S-1, re-measured `[src:S-2]`\n",
                }
            ),
            [],
        )


class UnreadableStore(CitationsCase):
    def test_a_store_this_reader_cannot_parse_is_unverifiable_not_unresolved(self):
        _, found = self.findings(
            {
                STORE: "sources: [{id: S-1, kind: file}, {id: S-2, kind: file}]\n",
                "README.md": "One `[src:S-1]` and two `[src:S-9]`.\n",
            }
        )
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.code, "SRC_STORE_UNREADABLE")
        self.assertEqual(finding.verdict, Verdict.UNVERIFIABLE)
        self.assertFalse(finding.is_problem)
        self.assertTrue(finding.detail)
        self.assertIn("no entries", finding.detail)
        self.assertEqual(finding.claim.path, STORE)

    def test_a_store_of_entries_under_another_key_invents_nothing(self):
        _, found = self.findings(
            {
                STORE: "version: 2\nrecords:\n  - id: S-1\n    kind: file\n",
                "README.md": "Backed `[src:S-1]`.\n",
            }
        )
        self.assertEqual([f.code for f in found], ["SRC_STORE_UNREADABLE"])
        self.assertEqual(found[0].verdict, Verdict.UNVERIFIABLE)

    def test_a_store_holding_only_comments_leaves_citations_unchecked(self):
        _, found = self.findings(
            {STORE: "# nothing recorded yet\n", "README.md": "Backed `[src:S-1]`.\n"}
        )
        self.assertEqual([f.code for f in found], ["SRC_STORE_UNREADABLE"])
        self.assertIn("no entries at all", found[0].detail)

    def test_an_empty_store_nobody_cites_is_left_alone(self):
        self.assertEqual(self.codes({STORE: "# nothing recorded yet\n"}), [])


class AmbiguityStaysSilent(CitationsCase):
    def test_a_placeholder_id_is_the_convention_not_a_citation(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: TWO_SOURCES,
                    "README.md": (
                        "| `citations` | Does every `[src:ID]` resolve to a source? |\n"
                        "Claims carry a `[src:ID]` tag `[src:S-1]`, `[src:S-2]`.\n"
                    ),
                }
            ),
            [],
        )

    def test_a_fenced_example_is_an_illustration(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: TWO_SOURCES,
                    "README.md": (
                        "Cited `[src:S-1]` and `[src:S-2]`.\n\n"
                        "Write a claim like this:\n\n"
                        "```markdown\n"
                        "The suite passes `[src:S-42]`.\n"
                        "```\n"
                    ),
                }
            ),
            [],
        )

    def test_a_tag_in_a_python_string_literal_is_fixture_data(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: TWO_SOURCES,
                    "README.md": "One `[src:S-1]`, two `[src:S-2]`.\n",
                    "tests/test_x.py": 'TAG = "[src:S-99]"\nassert TAG\n',
                }
            ),
            [],
        )

    def test_unknown_ids_are_not_resolved_without_an_unknowns_file(self):
        self.assertEqual(
            self.codes(
                {
                    STORE: TWO_SOURCES,
                    "README.md": "One `[src:S-1]`, two `[src:S-2]`, and U-9 elsewhere.\n",
                }
            ),
            [],
        )

    def test_a_token_that_merely_ends_in_an_unknown_id_shape(self):
        self.assertEqual(
            self.codes(
                {
                    UNKNOWNS: "### U-1 - open\n\nUnanswered.\n",
                    "README.md": "The AU-9 alloy and the MU-2 aircraft are not questions.\n",
                }
            ),
            [],
        )

    def test_a_repository_using_neither_convention_is_left_alone(self):
        self.assertEqual(
            self.codes(
                {
                    "README.md": "# A normal project\n\nIt has docs and code.\n",
                    "src/m.py": "# no provenance conventions here\nX = 1\n",
                }
            ),
            [],
        )


class Contract(CitationsCase):
    def test_registered_under_the_name_citations(self):
        self.assertIn("citations", registered())
        self.assertEqual(registered()["citations"].name, "citations")
        self.assertTrue(registered()["citations"].description)

    def test_same_tree_same_verdicts(self):
        files = {
            STORE: TWO_SOURCES,
            UNKNOWNS: "### U-1 - open\n\nUnanswered.\n",
            "README.md": "One `[src:S-9]`, and U-4 is open.\n",
            "docs/n.md": "Backed `[src:S-1]`.\n",
        }
        first_root, first = self.findings(files)
        second_root, second = self.findings(files)
        self.assertNotEqual(first_root, second_root)
        self.assertEqual(
            [(f.code, f.claim.locator, f.verdict) for f in first],
            [(f.code, f.claim.locator, f.verdict) for f in second],
        )
        self.assertEqual([f.code for f in first], ["SRC_UNRESOLVED", "SRC_UNCITED", "UNKNOWN_UNRESOLVED"])

    def test_the_checker_does_not_write_to_the_repository(self):
        root, _ = self.findings(
            {
                STORE: TWO_SOURCES,
                UNKNOWNS: "### U-1 - open\n\nUnanswered.\n",
                "README.md": "One `[src:S-9]` and U-9.\n",
            }
        )

        def snapshot() -> list[tuple[str, int, int]]:
            return sorted(
                (str(p.relative_to(root)), p.stat().st_size, p.stat().st_mtime_ns)
                for p in root.rglob("*")
            )

        before = snapshot()
        list(CitationsChecker().check(RepoIndex(root), CheckConfig()))
        self.assertEqual(before, snapshot())

    def test_an_empty_tree_produces_nothing(self):
        self.assertEqual(self.codes({}), [])


if __name__ == "__main__":
    unittest.main()
