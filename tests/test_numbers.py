"""Tests for the `numbers` checker.

Every fixture is a real tree on disk read through a real `RepoIndex`, because
the thing under test is whether a figure in a sentence survives a real search of
real source - a stubbed search would test the stub.

Most of these are negative cases, and that is the point. This checker's failure
mode is not missing an invented figure, it is reporting a year, a section
number, or a digit inside a name, and a report full of those is one nobody
reads.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.numbers import NumbersChecker
from tools.claims import RepoIndex
from tools.evidence import EvidenceKind, Severity, Verdict
from tools.registry import CheckConfig, registered


def write_tree(root: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


class NumbersCase(unittest.TestCase):
    def findings(self, files: dict[str, str]):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_tree(root, files)
        repo = RepoIndex(root)
        return root, list(NumbersChecker().check(repo, CheckConfig()))

    def assertSilent(self, files: dict[str, str]) -> None:
        _, found = self.findings(files)
        self.assertEqual([f.detail for f in found], [])


class TruePositives(NumbersCase):
    def test_an_unbacked_rate_in_prose_is_unsupported(self):
        _, found = self.findings(
            {
                "README.md": "# Crawler\n\nThe crawler sustains 5,000/hour against one host.\n",
                "src/pkg/limits.py": "BUDGET = 7\n",
            }
        )
        self.assertEqual(len(found), 1)
        finding = found[0]
        self.assertEqual(finding.checker, "numbers")
        self.assertEqual(finding.code, "NUMBER_UNSOURCED")
        self.assertEqual(finding.verdict, Verdict.UNSUPPORTED)
        self.assertEqual(finding.severity, Severity.WARN)
        self.assertEqual(finding.claim.path, "README.md")
        self.assertEqual(finding.claim.line, 3)
        self.assertIn("5,000/hour", finding.detail)

    def test_claim_is_quoted_verbatim_from_the_line(self):
        root, found = self.findings(
            {
                "README.md": "The crawler sustains 5,000/hour against one host.\n",
                "src/pkg/limits.py": "BUDGET = 7\n",
            }
        )
        claim = found[0].claim
        line = (root / claim.path).read_text().split("\n")[claim.line - 1]
        self.assertIn(claim.text, line)

    def test_evidence_names_the_site_and_the_search_space(self):
        _, found = self.findings(
            {
                "README.md": "The crawler sustains 5,000/hour against one host.\n",
                "src/pkg/limits.py": "BUDGET = 7\n",
            }
        )
        kinds = [e.kind for e in found[0].evidence]
        self.assertIn(EvidenceKind.FILE, kinds)
        self.assertIn(EvidenceKind.ABSENCE, kinds)
        cited = next(e for e in found[0].evidence if e.kind is EvidenceKind.FILE)
        self.assertEqual((cited.path, cited.line), ("README.md", 1))
        absence = next(e for e in found[0].evidence if e.kind is EvidenceKind.ABSENCE)
        self.assertEqual(absence.searched, ("src/pkg/limits.py",))
        self.assertIn("1 python files", absence.summary)

    def test_a_docstring_figure_cannot_cite_its_own_docstring(self):
        _, found = self.findings(
            {
                "src/pkg/rate.py": '"""Drains the queue at 5,000/hour."""\n',
                "src/pkg/other.py": "X = 7\n",
            }
        )
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].claim.path, "src/pkg/rate.py")
        self.assertEqual(found[0].claim.line, 1)

    def test_a_unit_bearing_figure_with_no_matching_literal(self):
        # The mirror of the supported cases below: without this the whole
        # SupportedFigures class could be passing for the wrong reason.
        _, found = self.findings(
            {
                "README.md": "The context holds 400,000 tokens at most.\n",
                "src/pkg/limits.py": "LIMIT = 7\n",
            }
        )
        self.assertEqual(len(found), 1)
        self.assertIn("400,000 tokens", found[0].detail)

    def test_a_hyphenated_figure_the_code_never_names_is_reported(self):
        _, found = self.findings(
            {
                "README.md": "We keep the top-5 candidates per query.\n",
                "src/pkg/limits.py": "BUDGET = 7\n",
            }
        )
        self.assertEqual(len(found), 1)
        self.assertIn("5", found[0].detail)

    def test_search_space_is_sorted_and_truncated_with_the_total_in_the_summary(self):
        files = {"README.md": "The crawler sustains 5,000/hour against one host.\n"}
        for index in range(12):
            files[f"src/pkg/m{index:02d}.py"] = "X = 7\n"
        _, found = self.findings(files)
        self.assertEqual(len(found), 1)
        absence = next(e for e in found[0].evidence if e.kind is EvidenceKind.ABSENCE)
        self.assertEqual(len(absence.searched), 8)
        self.assertEqual(list(absence.searched), sorted(absence.searched))
        self.assertIn("12 python files", absence.summary)


class SupportedFigures(NumbersCase):
    def test_a_bare_literal_backs_the_figure(self):
        self.assertSilent(
            {
                "README.md": "The limiter allows 10 rps per host.\n",
                "src/pkg/limits.py": "RPS = 10\n",
            }
        )

    def test_comma_grouping_matches_an_underscored_literal(self):
        self.assertSilent(
            {
                "README.md": "The context holds 400,000 tokens at most.\n",
                "src/pkg/limits.py": "LIMIT = 400_000\n",
            }
        )

    def test_a_product_of_powers_of_two_backs_the_expanded_figure(self):
        self.assertSilent(
            {
                "README.md": "The chunk is 8388608 bytes wide.\n",
                "src/pkg/limits.py": "CHUNK = 8 * 1024 * 1024\n",
            }
        )

    def test_a_unit_expands_against_a_plain_literal(self):
        self.assertSilent(
            {
                "README.md": "The cap is 2 MiB per fetch.\n",
                "src/pkg/limits.py": "CHUNK = 2097152\n",
            }
        )

    def test_a_string_literal_in_code_counts_as_support(self):
        self.assertSilent(
            {
                "README.md": "Throughput is capped at 5,000/hour per host.\n",
                "src/pkg/limits.py": 'BUDGET = "5,000/hour"\n',
            }
        )

    def test_a_percentage_matches_the_fraction_in_code(self):
        self.assertSilent(
            {
                "README.md": "Sampling covers 5% of the corpus.\n",
                "src/pkg/limits.py": "RATE = 0.05\n",
            }
        )


class MustNotFlag(NumbersCase):
    """The quiet half of the contract: numbers nobody was asserting anything about."""

    def test_a_line_that_says_version(self):
        self.assertSilent(
            {
                "README.md": "The parser requires version 2.7 of the toolchain.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_semver_shaped_pin(self):
        self.assertSilent(
            {
                "README.md": "Pinned at 1.4.2 until the rewrite lands.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_year(self):
        self.assertSilent(
            {
                "README.md": "Written in 2019 by the first team.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_number_in_a_heading(self):
        self.assertSilent(
            {
                "README.md": "## Budget of 5,000/hour\n\nProse with no figures in it.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_table_of_contents_entry(self):
        self.assertSilent(
            {
                "README.md": (
                    "# Doc\n\n## Contents\n\n- [Budget 5,000/hour](#budget)\n\n"
                    "## Budget\n\nProse with no figures in it.\n"
                ),
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_list_ordinal_in_a_docstring(self):
        self.assertSilent(
            {"src/pkg/rules.py": '"""Rules.\n\n1. Deterministic behaviour throughout.\n"""\n'}
        )

    def test_document_and_section_numbers(self):
        self.assertSilent(
            {
                "README.md": (
                    "See ADR 0001 for the rationale here.\n"
                    "Robots parsing follows RFC 9309 closely.\n"
                    "Discovery follows PEP 503 exactly.\n"
                ),
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_an_http_status_code(self):
        self.assertSilent(
            {
                "README.md": "The client retries after a 503 status code.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_python_version(self):
        self.assertSilent(
            {
                "README.md": "Runs on Python 3.11 and nothing older.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_digit_welded_into_a_name(self):
        self.assertSilent(
            {
                "README.md": "Digests are sha256 throughout the store.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_fenced_code_block(self):
        self.assertSilent(
            {
                "README.md": "# Doc\n\n```text\nsustained 5,000/hour\n```\n\nProse after it.\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_table_cell_that_is_only_a_number(self):
        self.assertSilent(
            {
                "README.md": "| metric | value |\n| --- | --- |\n| budget | 5000 |\n",
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_count_of_a_noun_the_unit_vocabulary_cannot_name(self):
        # Three real false positives this checker produced on its own repository
        # before the admission test existed. None of them names a dimension, and
        # two are illustrations rather than assertions about the system at all.
        self.assertSilent(
            {
                "README.md": (
                    "The package is 16 Python files and 2,583 lines today.\n"
                    "One unreadable file in a 4,000-file repository must not "
                    "abort the ingest of the other 3,999.\n"
                ),
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_figure_that_already_carries_a_provenance_tag(self):
        # Including the tag on the line the sentence wraps to, which is where a
        # citation usually lands.
        self.assertSilent(
            {
                "provenance/observations.md": (
                    "The crawler sustained 5,000/hour against one host\n"
                    "`[src:S-1]`, measured over a single run.\n"
                ),
                "src/pkg/limits.py": "X = 7\n",
            }
        )

    def test_a_year_a_padded_run_and_a_status_code_glued_to_a_name(self):
        # Hyphen tails, so the admission test passes them through and the rules
        # below it are what has to reject them.
        self.assertSilent(
            {
                "README.md": (
                    "Snapshots are tagged fy-2019, runs are named run-007, "
                    "and failures surface as http-503.\n"
                ),
                "src/pkg/limits.py": "X = 7\n",
            }
        )


class Ambiguity(NumbersCase):
    """Rule 6: when the shape alone cannot decide, the checker stays quiet."""

    def test_a_hyphenated_name_the_code_uses_is_not_a_figure(self):
        # `utf-8` and `top-5` are the same shape. The only honest separator is
        # whether the code writes the name, so this must stay silent while
        # `top-5` above is reported - on a tree with no literal 8 anywhere.
        self.assertSilent(
            {
                "README.md": "Payloads are decoded as utf-8 everywhere.\n",
                "src/pkg/io_util.py": "import io  # payloads are utf-8\n",
            }
        )

    def test_no_python_sources_is_unverifiable_and_said_once(self):
        _, found = self.findings(
            {"README.md": "The crawler sustains 5,000/hour against one host.\n"}
        )
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].verdict, Verdict.UNVERIFIABLE)
        self.assertEqual(found[0].evidence, [])
        self.assertIn("no Python sources", found[0].detail)


class Wiring(NumbersCase):
    def test_the_checker_is_registered_under_its_name(self):
        self.assertIn("numbers", registered())
        self.assertEqual(registered()["numbers"].name, "numbers")

    def test_two_runs_over_one_tree_agree(self):
        files = {
            "README.md": "The crawler sustains 5,000/hour against one host.\n",
            "src/pkg/limits.py": "BUDGET = 7\n",
        }
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        write_tree(root, files)
        first = [f.as_dict() for f in NumbersChecker().check(RepoIndex(root), CheckConfig())]
        second = [f.as_dict() for f in NumbersChecker().check(RepoIndex(root), CheckConfig())]
        self.assertEqual(first, second)
        self.assertEqual(len(first), 1)


if __name__ == "__main__":
    unittest.main()
