"""Tests for the redaction boundary, and the text helpers around it.

`redact_secrets` is the single point where a credential is supposed to stop.
Everything that reads material the user did not write for publication passes
through it: chat transcripts, shell history, workspace files, GitHub error
bodies. What it misses reaches a nightly report, a journal and an index.

A shape-matching redactor goes stale in one direction only - a format that
shipped after the table was written passes straight through - so the tests below
are a checklist of prefixes rather than a proof of completeness. That limit is
why the GitHub connector also redacts its own token by value: the one credential
a component can identify with certainty is the one it was handed.
"""

from __future__ import annotations

import unittest

from oodarag.util.text import (
    clean,
    estimate_tokens,
    heading_path,
    normalize_whitespace,
    redact_secrets,
    split_markdown_sections,
    summarize,
    tokenize,
    truncate_tokens,
)

# Assembled at runtime rather than written as literals. A literal here is
# indistinguishable from a real key to a secret scanner, and GitHub's push
# protection rejected the first version of this file over the Stripe fixture -
# correctly. The test needs a string that matches the pattern; the repository
# must not contain one.
_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789"
_UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

CREDENTIALS = {
    "github classic": "ghp" + "_" + _ALNUM,
    "github fine-grained": "github" + "_pat_" + "11" + _UPPER + "_" + _ALNUM + _ALNUM,
    "anthropic": "sk" + "-ant-" + "api03-" + _ALNUM,
    "openai project": "sk" + "-proj-" + _ALNUM + _UPPER,
    "google api": "AIza" + _ALNUM + _ALNUM[:2],
    "stripe live": "sk" + "_live_" + _ALNUM[:24],
    "npm": "npm" + "_" + _ALNUM,
    "pypi": "pypi" + "-" + "AgEIcHlwaS5vcmc" + _ALNUM,
    "slack bot": "xoxb" + "-" + "1234567890-" + _ALNUM[:12],
    "slack app": "xapp" + "-" + "1-A01234567-1234567890123-" + _ALNUM[:6],
    "aws key id": "AKIA" + _UPPER[:16],
    "jwt": "eyJ" + "hbGciOiJIUzI1NiJ9" + "." + "eyJ" + "zdWIiOiIxIn0" + "." + _ALNUM[:16],
}


class RedactionTestCase(unittest.TestCase):
    def test_every_known_format_is_removed(self) -> None:
        for label, secret in CREDENTIALS.items():
            with self.subTest(format=label):
                out = redact_secrets(secret)
                self.assertIn("redacted", out, f"{label} passed through")
                self.assertNotIn(secret, out)

    def test_a_secret_embedded_in_a_line_is_removed(self) -> None:
        """It is never alone: it is in an export, a URL, a config line."""
        for secret in CREDENTIALS.values():
            with self.subTest(secret=secret[:12]):
                line = f'export TOKEN="{secret}"  # do not commit'
                out = redact_secrets(line)
                self.assertNotIn(secret, out)
                self.assertIn("do not commit", out, "the surrounding text must survive")

    def test_the_openai_project_form_is_not_truncated_at_the_hyphen(self) -> None:
        """A bare-alphanumeric class stops at the first hyphen and leaves the
        secret half of `sk-proj-...` in the clear."""
        out = redact_secrets(CREDENTIALS["openai project"])
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", out)

    def test_ordinary_prose_is_untouched(self) -> None:
        for text in (
            "the ghp_ prefix is used by github",
            "npm install foo",
            "sk-short",
            "AIzabc",
            "run make test before you commit",
        ):
            with self.subTest(text=text):
                self.assertEqual(redact_secrets(text), text)

    def test_assignment_shapes_are_caught_without_a_known_prefix(self) -> None:
        """The backstop for formats this table has never heard of."""
        out = redact_secrets("api_key = 9f8e7d6c5b4a39281706abcdef")
        self.assertNotIn("9f8e7d6c5b4a39281706abcdef", out)

    def test_a_private_key_block_goes_entirely(self) -> None:
        block = (
            "-----BEGIN RSA PRIVATE KEY-----\n"
            "MIIEowIBAAKCAQEAoo\nsecretsecretsecret\n"
            "-----END RSA PRIVATE KEY-----"
        )
        out = redact_secrets(f"before\n{block}\nafter")
        self.assertNotIn("secretsecretsecret", out)
        self.assertIn("before", out)
        self.assertIn("after", out)

    def test_redaction_is_idempotent(self) -> None:
        """It runs at more than one boundary; a marker must not be re-redacted."""
        once = redact_secrets(CREDENTIALS["github classic"])
        self.assertEqual(redact_secrets(once), once)

    def test_empty_and_huge_inputs_do_not_raise(self) -> None:
        self.assertEqual(redact_secrets(""), "")
        self.assertIsInstance(redact_secrets("x" * 200_000), str)


class TextHelpersTestCase(unittest.TestCase):
    def test_clean_normalizes_unicode_and_whitespace(self) -> None:
        self.assertEqual(clean("  a  b\r\n\r\n\r\nc  "), "a b\n\nc")

    def test_normalize_whitespace_keeps_paragraphs(self) -> None:
        self.assertEqual(normalize_whitespace("a\n\n\n\n\nb"), "a\n\nb")

    def test_tokenize_drops_stopwords_and_single_characters(self) -> None:
        tokens = tokenize("The quick brown fox a b snake_case dotted.path")
        self.assertNotIn("the", tokens)
        self.assertNotIn("a", tokens)
        self.assertIn("snake_case", tokens)
        self.assertIn("dotted.path", tokens)

    def test_estimate_tokens_is_monotonic_and_zero_for_empty(self) -> None:
        self.assertEqual(estimate_tokens(""), 0)
        self.assertGreater(estimate_tokens("a b c d e"), estimate_tokens("a b"))

    def test_truncate_tokens_leaves_short_text_alone(self) -> None:
        self.assertEqual(truncate_tokens("short text", 100), "short text")
        self.assertTrue(truncate_tokens("word " * 500, 10).endswith("..."))

    def test_summarize_bounds_length(self) -> None:
        self.assertLessEqual(len(summarize("word " * 500, max_chars=80)), 84)
        self.assertEqual(summarize("short"), "short")

    def test_heading_path_tracks_nesting(self) -> None:
        doc = "# A\n\ntext\n\n## B\n\nmore\n\n### C\n\ndeep\n\n## D\n\nend\n"
        self.assertEqual(heading_path(doc, doc.index("deep")), ["A", "B", "C"])
        self.assertEqual(heading_path(doc, doc.index("end")), ["A", "D"])

    def test_fenced_code_is_not_split_on_a_heading_inside_it(self) -> None:
        doc = "# Real\n\n```\n# not a heading\n```\n\n## Also real\n\nbody\n"
        sections = split_markdown_sections(doc)
        self.assertEqual([path[-1] for path, _body, _off in sections], ["Real", "Also real"])


if __name__ == "__main__":
    unittest.main()
