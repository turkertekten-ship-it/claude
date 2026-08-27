"""Claim extraction: line numbers and verbatim text.

Every finding the tool emits points at `path:line`. If extraction is off by one,
every locator in every report is wrong and the whole thing is unusable - so the
line numbers are what these tests actually guard.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.claims import RepoIndex, SourceFile


def source(text: str, name: str = "README.md") -> SourceFile:
    return SourceFile(Path(name), name, text)


class TestLineAccuracy(unittest.TestCase):
    def test_prose_claim_line_numbers_are_exact(self):
        f = source("# Title\n\nSome intro.\n\n- a bullet claim\n\nTrailing sentence.\n")
        by_line = {c.line: c.text for c in f.prose_claims()}
        self.assertEqual(by_line[1], "Title")
        self.assertEqual(by_line[5], "a bullet claim")
        self.assertEqual(by_line[7], "Trailing sentence.")

    def test_claim_text_is_a_verbatim_substring(self):
        text = "# Title\n\nThe crawler bounds pages, bytes and depth.\n"
        f = source(text)
        for claim in f.prose_claims():
            self.assertIn(claim.text, text, f"{claim.text!r} was paraphrased, not quoted")

    def test_table_cells_become_separate_claims(self):
        f = source("| Feature | Status |\n|---|---|\n| BM25 retrieval | done |\n")
        cells = [c.text for c in f.prose_claims() if c.kind == "table_cell"]
        self.assertIn("BM25 retrieval", cells)
        self.assertIn("done", cells)
        self.assertNotIn("---", cells)

    def test_line_at_maps_offsets_to_lines(self):
        f = source("one\ntwo\nthree\n")
        self.assertEqual(f.line_at(0), 1)
        self.assertEqual(f.line_at(4), 2)
        self.assertEqual(f.line_at(8), 3)


class TestFences(unittest.TestCase):
    def test_fence_start_line_points_at_first_content_line(self):
        f = source("intro\n\n```bash\nmake test\nmake lint\n```\n")
        fence = f.fences()[0]
        self.assertEqual(fence.lang, "bash")
        self.assertEqual(fence.start_line, 4)
        self.assertEqual(fence.commands, [(4, "make test"), (5, "make lint")])

    def test_fenced_content_is_not_also_prose(self):
        f = source("# T\n\n```bash\nrm -rf /\n```\n\nreal prose\n")
        texts = [c.text for c in f.prose_claims()]
        self.assertNotIn("rm -rf /", texts)
        self.assertIn("real prose", texts)

    def test_continuations_are_joined(self):
        f = source("```bash\npython3 -m tools.ultrareview . \\\n  --json out.json\n```\n")
        self.assertEqual(
            f.fences()[0].commands,
            [(2, "python3 -m tools.ultrareview . --json out.json")],
        )

    def test_prompts_and_comments_are_stripped(self):
        f = source("```sh\n# a comment\n$ make test\n\n```\n")
        self.assertEqual(f.fences()[0].commands, [(3, "make test")])

    def test_non_shell_fences_yield_no_commands(self):
        f = source("```python\nimport os\n```\n")
        self.assertEqual(f.fences()[0].commands, [])

    def test_unterminated_fence_still_returns_what_was_read(self):
        f = source("```bash\nmake test\n")
        self.assertEqual(len(f.fences()), 1)


class TestPythonClaims(unittest.TestCase):
    SRC = (
        '"""Module does a thing.\n\nAnd another thing.\n"""\n'
        "\n"
        "# a standalone comment\n"
        "def f():\n"
        '    """Inner docstring."""\n'
        "    return 1\n"
    )

    def test_docstrings_and_comments_are_claims(self):
        f = SourceFile(Path("m.py"), "m.py", self.SRC)
        claims = f.comment_claims()
        texts = [c.text for c in claims]
        self.assertIn("Module does a thing.", texts)
        self.assertIn("And another thing.", texts)
        self.assertIn("a standalone comment", texts)
        self.assertIn("Inner docstring.", texts)

    def test_comment_line_numbers_are_exact(self):
        f = SourceFile(Path("m.py"), "m.py", self.SRC)
        by_text = {c.text: c.line for c in f.comment_claims()}
        self.assertEqual(by_text["a standalone comment"], 6)
        self.assertEqual(by_text["Module does a thing."], 1)

    def test_syntax_error_degrades_to_comments_only(self):
        f = SourceFile(Path("m.py"), "m.py", "# still a comment\ndef (:\n")
        self.assertEqual([c.text for c in f.comment_claims()], ["still a comment"])


class TestRepoIndex(unittest.TestCase):
    def test_index_reads_text_files_and_skips_noise(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Hi\n\nA claim.\n")
            (root / "Makefile").write_text("test:\n\techo hi\n")
            (root / "mod.py").write_text("x = 1\n")
            (root / "__pycache__").mkdir()
            (root / "__pycache__" / "junk.py").write_text("nope\n")
            (root / "logo.png").write_bytes(b"\x89PNG\r\n")

            repo = RepoIndex(root)
            names = sorted(f.rel for f in repo.files)
            self.assertEqual(names, ["Makefile", "README.md", "mod.py"])
            self.assertEqual([f.rel for f in repo.markdown], ["README.md"])
            self.assertEqual([f.rel for f in repo.python], ["mod.py"])

    def test_exists_refuses_to_escape_the_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = RepoIndex(Path(tmp))
            (Path(tmp) / "here.md").write_text("x")
            self.assertTrue(repo.exists("here.md"))
            self.assertFalse(repo.exists("../../../etc/passwd"))
            self.assertFalse(repo.exists("nope.md"))

    def test_get_returns_the_cached_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "README.md").write_text("# T\n")
            repo = RepoIndex(Path(tmp))
            self.assertIsNotNone(repo.get("README.md"))
            self.assertIsNone(repo.get("absent.md"))


if __name__ == "__main__":
    unittest.main()


class TestEmptyFenceDoesNotSwallowClaims(unittest.TestCase):
    """Regression: an empty fence covered one line past its closing marker."""

    def test_claim_immediately_after_empty_fence_survives(self):
        f = source("# T\n\n```\n```\nthis claim must survive\n")
        self.assertIn("this claim must survive", [c.text for c in f.prose_claims()])

    def test_claim_immediately_after_normal_fence_survives(self):
        f = source("# T\n\n```bash\nmake test\n```\nthis one too\n")
        texts = [c.text for c in f.prose_claims()]
        self.assertIn("this one too", texts)
        self.assertNotIn("make test", texts)
