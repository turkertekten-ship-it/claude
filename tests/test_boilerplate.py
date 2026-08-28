"""Site-template removal.

The defect this module exists for: the external evaluation corpus - the one the
project relies on precisely because it is uncontaminated - was 90.9% PyPI
download-page furniture. `coverage.md` was 252KB of which 1,962 bytes described
the project. IDF is computed over that text, so the scale deciding what counts
as a rare term was set by hex digests and upload dates.

These tests derive their expectations from the rule rather than from a run:
each builds a document set with a known heading distribution and asserts what
the threshold must do at its boundary.
"""

from __future__ import annotations

import unittest

from oodarag.scrape.boilerplate import (
    MIN_DOCUMENTS, filter_corpus, learn_template, strip_template,
)


def _doc(*sections: str) -> str:
    return "\n\n".join(sections) + "\n"


class LearnTemplateTest(unittest.TestCase):
    def _corpus(self, total: int, with_heading: int, heading: str = "## Download files"):
        """`with_heading` of `total` documents carry `heading`; the rest do not."""
        docs = []
        for i in range(total):
            body = [f"# Package {i}", f"Package {i} does something specific."]
            if i < with_heading:
                body.append(f"{heading}\n\nA table of files.")
            docs.append(_doc(*body))
        return docs

    def test_a_heading_on_most_documents_is_template(self):
        # 8 of 10 is 80%, above the 50% default by a wide margin.
        template = learn_template(self._corpus(10, 8))
        self.assertIn("download files", template)

    def test_a_heading_on_few_documents_is_content(self):
        template = learn_template(self._corpus(10, 2))
        self.assertNotIn("download files", template)

    def test_the_threshold_is_where_the_rule_says_it_is(self):
        """Derived from min_share, not copied: at exactly half the documents the
        heading qualifies, and one document fewer it does not."""
        self.assertIn("download files", learn_template(self._corpus(10, 5)))
        self.assertNotIn("download files", learn_template(self._corpus(10, 4)))

    def test_too_few_documents_learns_nothing(self):
        """With three pages, a heading two of them share looks exactly like a
        site template. Guessing there is worse than doing nothing."""
        docs = self._corpus(MIN_DOCUMENTS - 1, MIN_DOCUMENTS - 1)
        self.assertEqual(learn_template(docs), set())

    def test_a_heading_repeated_within_one_document_is_not_template(self):
        """The regression that removed the within-document repeat rule: a
        changelog repeats "Fixed" 37 times in one page, and that page is
        content. Only repetition *across* documents is evidence."""
        changelog = _doc("# tox", "Release notes.",
                         *[f"### Fixed\n\nBug {i} fixed." for i in range(40)])
        others = self._corpus(9, 0)
        template = learn_template([changelog] + others)
        self.assertNotIn("fixed", template,
                         "a heading rare across documents was called template "
                         "because it repeats inside one")


class StripTemplateTest(unittest.TestCase):
    def test_a_templated_section_takes_its_subsections_with_it(self):
        """Removing the heading but not its nested content deletes the label and
        keeps the table, which is worse than doing nothing."""
        text = _doc(
            "# Blinker",
            "Blinker provides a fast dispatching system.",
            "## Download files",
            "Download the file for your platform.",
            "### Source Distribution",
            "blinker-1.9.0.tar.gz",
            "### File hashes",
            "SHA256 b4ce2265a7abece45e7cc896e98dbebe6cead56bcf805a3d23136d145f5445bf",
            "## Example",
            "Signal receivers can subscribe to specific senders.",
        )
        out = strip_template(text, {"download files"})
        self.assertIn("fast dispatching system", out)
        self.assertIn("## Example", out)
        self.assertIn("Signal receivers", out)
        for gone in ("Download files", "Source Distribution", "blinker-1.9.0.tar.gz",
                     "File hashes", "b4ce2265"):
            self.assertNotIn(gone, out, f"{gone!r} survived the removal")

    def test_a_section_after_a_removed_one_survives_at_the_same_level(self):
        text = _doc("# P", "Intro.", "## Drop me", "Gone.", "## Keep me", "Kept.")
        out = strip_template(text, {"drop me"})
        self.assertNotIn("Gone.", out)
        self.assertIn("## Keep me", out)
        self.assertIn("Kept.", out)

    def test_a_deeper_heading_does_not_end_a_removed_section(self):
        text = _doc("## Drop me", "Gone.", "### Also gone", "Still gone.", "# Top", "Kept.")
        out = strip_template(text, {"drop me"})
        self.assertNotIn("Still gone.", out)
        self.assertIn("Kept.", out)

    def test_an_empty_template_changes_nothing(self):
        text = _doc("# P", "Body.", "## Section", "More.")
        self.assertEqual(strip_template(text, set()), text)


class FilterCorpusTest(unittest.TestCase):
    def _corpus(self, n: int) -> dict[str, str]:
        return {
            f"pkg{i}.md": _doc(f"# pkg{i}", f"Unique description for package {i}.",
                               "## File hashes", "SHA256 " + "0" * 64)
            for i in range(n)
        }

    def test_the_report_accounts_for_what_was_removed(self):
        docs = self._corpus(10)
        filtered, report = filter_corpus(docs)
        self.assertEqual(report.documents, 10)
        self.assertEqual(report.bytes_before, sum(len(t) for t in docs.values()))
        self.assertEqual(report.bytes_after, sum(len(t) for t in filtered.values()))
        self.assertIn("file hashes", report.template_headings)
        self.assertGreater(report.removed_share, 0.0)

    def test_every_document_keeps_what_makes_it_itself(self):
        filtered, _ = filter_corpus(self._corpus(10))
        for i, text in enumerate(filtered.values()):
            self.assertIn("Unique description", text)
        self.assertFalse(any("SHA256" in t for t in filtered.values()))

    def test_too_small_a_corpus_says_so_rather_than_doing_nothing_quietly(self):
        """A filter that silently no-ops is indistinguishable from a broken one."""
        docs = self._corpus(MIN_DOCUMENTS - 1)
        filtered, report = filter_corpus(docs)
        self.assertEqual(filtered, docs)
        self.assertTrue(report.skipped_reason)
        self.assertIn(str(MIN_DOCUMENTS), report.skipped_reason)
        self.assertEqual(report.removed_share, 0.0)


if __name__ == "__main__":
    unittest.main()
