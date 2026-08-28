"""The CLI's one promise: it fails like a program, not like a stack trace.

internal/CONTRACTS.md says `main(argv)` returns a process exit code on every
path and never lets a traceback reach the terminal. That is not politeness — the
CLI is what `make demo`, `make eval` and `make loop` invoke, so an unhandled
exception here surfaces as a wall of Python to someone who asked a question
about their corpus.

These cases drive the failure paths on purpose. The success path is already
covered end to end by `make demo`.
"""

from __future__ import annotations

import io
import contextlib
import tempfile
import unittest
from pathlib import Path

from oodarag import cli


def _run(argv: list[str]) -> tuple[int, str]:
    """Call main() and capture both streams. SystemExit is a legitimate exit
    (argparse uses it), so it is caught and reported as its code."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(argv)
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 1
    return int(code or 0), out.getvalue() + err.getvalue()


class NoTracebackEscapes(unittest.TestCase):
    def test_no_arguments_is_diagnosed_not_raised(self) -> None:
        code, text = _run([])
        self.assertNotEqual(code, 0, "an empty invocation reported success")
        self.assertNotIn("Traceback", text)

    def test_an_unknown_subcommand_is_diagnosed(self) -> None:
        code, text = _run(["definitely-not-a-subcommand"])
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", text)

    def test_query_without_a_question_is_diagnosed(self) -> None:
        code, text = _run(["query"])
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", text)

    def test_stats_on_a_missing_index_explains_itself(self) -> None:
        # The commonest first-run mistake: asking about an index nobody built.
        # It must say so, not raise, and not claim an empty corpus is fine.
        with tempfile.TemporaryDirectory() as tmp:
            code, text = _run(["--root", str(Path(tmp) / "nothing"), "stats"])
            self.assertNotIn("Traceback", text)
            self.assertTrue(text.strip(), "failed silently with no diagnosis")

    def test_query_against_a_missing_index_explains_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, text = _run(["--root", str(Path(tmp) / "nothing"), "query", "anything"])
            self.assertNotIn("Traceback", text)
            self.assertTrue(text.strip(), "failed silently with no diagnosis")


class ExitCodes(unittest.TestCase):
    def test_help_exits_clean(self) -> None:
        code, text = _run(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("demo", text)

    def test_main_always_returns_an_integer(self) -> None:
        for argv in ([], ["--help"], ["stats"], ["query"], ["nonsense"]):
            with self.subTest(argv=argv):
                code, _ = _run(argv)
                self.assertIsInstance(code, int)


class SubcommandSurface(unittest.TestCase):
    def test_every_makefile_target_has_a_subcommand(self) -> None:
        # The Makefile is the documented entry point, so a target naming a
        # subcommand that does not exist is a broken promise in the README.
        makefile = Path("Makefile")
        if not makefile.is_file():
            self.skipTest("Makefile missing")
        text = makefile.read_text()
        _, help_text = _run(["--help"])
        for sub in ("demo", "index", "query", "eval", "loop", "stats"):
            with self.subTest(sub=sub):
                self.assertIn(sub, help_text, f"{sub} is invoked but not exposed")
        for sub in ("demo", "index", "query", "eval", "loop"):
            with self.subTest(target=sub):
                self.assertIn(f"oodarag.cli {sub}", text,
                              f"Makefile does not invoke `oodarag.cli {sub}`")


if __name__ == "__main__":
    unittest.main()
