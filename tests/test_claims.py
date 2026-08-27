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


class TestSkipDirsAreRepoRelative(unittest.TestCase):
    """Regression: SKIP_DIRS was matched against the absolute path.

    A repository checked out under `~/dev/build/repo`, a CI workspace at
    `/var/lib/ci/build/job`, or anything vendored inside `node_modules/` had
    every one of its own files filtered out. The tool then read zero bytes and
    reported zero findings with exit 0 - a clean bill of health for a tree it
    never opened, which is the worst failure available to it.
    """

    def _index(self, base: Path) -> RepoIndex:
        base.mkdir(parents=True, exist_ok=True)
        (base / "README.md").write_text("# Demo\n\nA claim.\n")
        (base / "Makefile").write_text("help:\n\techo hi\n")
        return RepoIndex(base)

    def test_a_repo_under_a_skip_named_directory_is_still_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            plain = self._index(Path(tmp) / "demo")
            buried = self._index(Path(tmp) / "build" / "demo")
            self.assertEqual(sorted(f.rel for f in plain.files),
                             sorted(f.rel for f in buried.files))
            self.assertTrue(buried.files, "a repo under build/ must not read as empty")
            self.assertEqual(len(buried.all_paths), len(plain.all_paths))

    def test_every_skip_dir_name_is_survivable_as_a_parent(self):
        from tools.claims import SKIP_DIRS

        with tempfile.TemporaryDirectory() as tmp:
            for name in sorted(SKIP_DIRS):
                with self.subTest(parent=name):
                    idx = self._index(Path(tmp) / name / "repo")
                    self.assertTrue(idx.files, f"a repo under {name}/ read as empty")

    def test_skip_dirs_inside_the_repo_are_still_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "demo"
            idx = self._index(root)
            (root / "build").mkdir()
            (root / "build" / "generated.py").write_text("x = 1\n")
            self.assertNotIn("build/generated.py", {f.rel for f in RepoIndex(root).files})


class TestTildeFences(unittest.TestCase):
    """Regression: `~~~` is a valid CommonMark fence and was read as prose."""

    def test_a_tilde_fence_is_a_fence(self):
        f = source("# T\n\n~~~sh\nmake test\n~~~\n")
        fences = f.fences()
        self.assertEqual(len(fences), 1)
        self.assertEqual(fences[0].lang, "sh")
        self.assertEqual(fences[0].commands, [(4, "make test")])

    def test_tilde_fenced_content_is_not_prose(self):
        f = source("# T\n\n~~~sh\npython3 -m demo.cli --config config/settings.toml\n~~~\n")
        texts = [c.text for c in f.prose_claims()]
        self.assertNotIn("python3 -m demo.cli --config config/settings.toml", texts)

    def test_a_backtick_run_inside_a_tilde_fence_is_content(self):
        # This is what tilde fences are for.
        f = source("# T\n\n~~~\n```\nnot a fence\n```\n~~~\n\nafter\n")
        self.assertEqual(len(f.fences()), 1)
        self.assertIn("after", [c.text for c in f.prose_claims()])

    def test_a_longer_backtick_fence_still_works(self):
        f = source("# T\n\n````bash\nmake test\n````\n")
        self.assertEqual(f.fences()[0].commands, [(4, "make test")])


class TestDocstringLineAttribution(unittest.TestCase):
    """Regression: module docstrings were attributed to line 1 unconditionally."""

    def test_a_shebang_does_not_shift_docstring_claims(self):
        src = '#!/usr/bin/env python3\n# a licence header\n\n"""The cache holds tokens.\n\nSecond line.\n"""\n'
        f = SourceFile(Path("m.py"), "m.py", src)
        by_text = {c.text: c.line for c in f.comment_claims()}
        self.assertEqual(by_text["The cache holds tokens."], 4)
        self.assertEqual(by_text["Second line."], 6)

    def test_the_quoted_text_really_is_on_the_reported_line(self):
        src = '#!/usr/bin/env python3\n\n"""Alpha.\n\nBeta.\n"""\n'
        f = SourceFile(Path("m.py"), "m.py", src)
        for claim in f.comment_claims():
            self.assertIn(claim.text, f.line_text(claim.line),
                          f"{claim.text!r} is not on line {claim.line}")
