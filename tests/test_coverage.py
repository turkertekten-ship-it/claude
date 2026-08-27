"""Capability claims must have code behind them - and prose must be left alone.

This checker is the one most able to do damage by being noisy: it reads every
sentence in the repository. So most of these tests are about silence. The rule
it enforces is not "this word is uncommon" but "this word is code-shaped", which
is what stops a stopword list from having to contain the English language.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.checkers.coverage import CoverageChecker, _is_distinctive, _tokens
from tools.claims import RepoIndex
from tools.registry import CheckConfig

SOURCE = '''"""Retrieval."""


def rrf_fuse(dense, lexical):
    """Reciprocal rank fusion."""
    return dense + lexical


BM25_K1 = 1.2
'''


def repo(tmp: str, readme: str, *, source: str = SOURCE) -> Path:
    root = Path(tmp)
    (root / "src" / "pkg").mkdir(parents=True)
    (root / "src" / "pkg" / "__init__.py").write_text("")
    (root / "src" / "pkg" / "retrieve.py").write_text(source)
    (root / "README.md").write_text(readme)
    return root


def codes(root: Path) -> list[str]:
    return [f.code for f in CoverageChecker().check(RepoIndex(root), CheckConfig())]


class TestDistinctiveness(unittest.TestCase):
    """Ordinary English must never qualify, however uncommon it is."""

    def test_acronyms_qualify(self):
        for token in ("BM25", "RRF", "nDCG", "HNSW"):
            self.assertTrue(_is_distinctive(token, frozenset()), token)

    def test_ordinary_english_never_qualifies(self):
        # Every one of these was reported against this repository by an earlier
        # length-plus-stopword rule. None is in any plausible stopword list, and
        # none is a capability claim.
        for token in ("synonyms", "briefly", "inconvenient", "indicates", "invoked",
                      "uncertain", "orientation", "unfamiliar", "advertised", "refuted"):
            self.assertFalse(_is_distinctive(token, frozenset()), token)

    def test_backticks_make_an_ordinary_word_a_claim(self):
        # The author asserting `chunker` is a symbol is what makes it checkable.
        self.assertFalse(_is_distinctive("chunker", frozenset()))
        self.assertTrue(_is_distinctive("chunker", frozenset({"chunker"})))

    def test_metric_shapes_qualify(self):
        self.assertTrue(_tokens("fused with recall@k scoring"))

    def test_hyphenated_english_does_not_qualify(self):
        self.assertFalse(_is_distinctive("project-agnostic", frozenset()))
        self.assertFalse(_is_distinctive("read-only", frozenset()))


class TestVerdicts(unittest.TestCase):
    def test_a_capability_with_code_behind_it_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = "# P\n\nHybrid retrieval fuses the arms with RRF and BM25 scoring.\n"
            self.assertEqual(codes(repo(tmp, readme)), [])

    def test_a_capability_with_no_code_behind_it_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = "# P\n\nResults are reranked with a HNSW graph index for speed.\n"
            self.assertIn("CAPABILITY_UNSUPPORTED", codes(repo(tmp, readme)))

    def test_the_finding_names_the_tokens_it_searched_for(self):
        # Without the token list the reader cannot reproduce the grep, which
        # makes the finding an assertion rather than evidence.
        with tempfile.TemporaryDirectory() as tmp:
            readme = "# P\n\nResults are reranked with a HNSW graph index for speed.\n"
            found = [f for f in CoverageChecker().check(RepoIndex(repo(tmp, readme)),
                                                        CheckConfig())
                     if f.code == "CAPABILITY_UNSUPPORTED"]
            blob = " ".join(e.summary + e.detail if hasattr(e, "detail") else e.summary
                            for f in found for e in f.evidence) + " ".join(f.detail for f in found)
            self.assertIn("HNSW", blob)

    def test_ordinary_prose_is_silent(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = (
                "# P\n\n"
                "Use these four words and no synonyms. The reader needs to know the search\n"
                "space to interpret the silence, so state it briefly. That is inconvenient\n"
                "but it indicates what was actually invoked.\n"
            )
            self.assertEqual(codes(repo(tmp, readme)), [])

    def test_a_roadmap_section_is_not_a_false_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = ("# P\n\n## Not yet built — roadmap\n\n"
                      "Reranking with a HNSW graph index.\n")
            self.assertEqual(codes(repo(tmp, readme)), [])

    def test_prose_that_states_the_absence_is_not_a_false_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            readme = ("# P\n\nThe README described HNSW reranking. "
                      "No such code exists in the tree.\n")
            self.assertEqual(codes(repo(tmp, readme)), [])

    def test_findings_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# P\n\nReranked with a HNSW graph index.\n")
            self.assertEqual(codes(root), codes(root))


if __name__ == "__main__":
    unittest.main()


class TestPolyglotRepositories(unittest.TestCase):
    """A capability is not false because it is implemented in another language."""

    def test_a_capability_backed_by_a_dockerfile_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# P\n\nImages are built by the Dockerfile with BuildKit.\n")
            (Path(tmp) / "Dockerfile").write_text("FROM python:3.11\n# syntax uses BuildKit\n")
            self.assertEqual(codes(root), [])

    def test_a_capability_backed_by_a_shell_script_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# P\n\nReleases are cut by the RELEASE-1 pipeline script.\n")
            (Path(tmp) / "release.sh").write_text("#!/bin/sh\n# RELEASE-1 pipeline\n")
            self.assertEqual(codes(root), [])

    def test_prose_repeating_prose_is_not_evidence(self):
        # Markdown is excluded from the haystack on purpose: a second document
        # restating the claim would otherwise satisfy it.
        with tempfile.TemporaryDirectory() as tmp:
            root = repo(tmp, "# P\n\nResults are reranked with a HNSW graph index.\n")
            (Path(tmp) / "DESIGN.md").write_text("# Design\n\nWe will use HNSW.\n")
            self.assertIn("CAPABILITY_UNSUPPORTED", codes(root))
