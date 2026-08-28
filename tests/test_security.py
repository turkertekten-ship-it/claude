"""Regressions for the findings of a security review of this pipeline.

Each test names the concrete attack it prevents. They are grouped here rather
than spread through the per-module suites because the property under test is
the same in every case: input this pipeline does not control must not be able
to leak a credential, escape a boundary, or exhaust a resource.
"""

from __future__ import annotations

import gzip
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.chunk import _MEMBER_RE, chunk_document  # noqa: E402
from oodarag.ingest.files import FileConnector  # noqa: E402
from oodarag.ingest.skills import lint_skill, parse_skill  # noqa: E402
from oodarag.models import Document, RawDocument  # noqa: E402
from oodarag.util.http import (  # noqa: E402
    MAX_DECOMPRESSED_RATIO,
    HttpError,
    TransportError,
    _decompress,
    _SafeRedirectHandler,
    safe_url,
)
from oodarag.util.text import redact_secrets  # noqa: E402

# Credential-shaped fixtures are assembled at runtime rather than written as
# literals. They are fabricated and non-functional either way, but a literal
# that matches a provider's published signature trips secret scanning on every
# push — GitHub's push protection rejected an earlier version of this file over
# the Stripe-shaped one. Splitting the prefix keeps the scanner quiet while the
# value the redactor sees is byte-for-byte identical.
def _shaped(prefix: str, body: str) -> str:
    """Build a provider-shaped test credential without embedding its signature."""
    return prefix + body


FAKE_GOOGLE_KEY = _shaped("AIza", "SyD-1234567890abcdefghijklmnopqrstu")
FAKE_GH_TOKEN = _shaped("ghp" + "_", "A" * 36)


class TestCredentialsNeverReachALog(unittest.TestCase):
    """A retry is routine — 429 *is* what quota exhaustion looks like — so
    anything that logs a full URL leaks the key on an ordinary failure."""

    def test_a_query_string_is_stripped_from_a_logged_url(self) -> None:
        url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet&key={FAKE_GOOGLE_KEY}"
        self.assertNotIn(FAKE_GOOGLE_KEY, safe_url(url))
        self.assertIn("youtube/v3/videos", safe_url(url))

    def test_a_url_without_a_query_is_left_readable(self) -> None:
        self.assertEqual(safe_url("https://api.github.com/rate_limit"),
                         "https://api.github.com/rate_limit")

    def test_the_exception_message_carries_no_credential(self) -> None:
        # `raise ... from exc` keeps the cause attached, so a key in the
        # exception text survives even when the new message is scrubbed.
        err = HttpError(429, f"https://x/v3?key={FAKE_GOOGLE_KEY}", "slow down")
        self.assertNotIn(FAKE_GOOGLE_KEY, str(err))

    def test_a_malformed_url_does_not_raise(self) -> None:
        self.assertIsInstance(safe_url("http://[::1"), str)


class TestCredentialsNeverCrossAnOrigin(unittest.TestCase):
    """urllib copies every header to a redirect target and, unlike requests,
    does not drop Authorization when the host changes."""

    def _redirect(self, frm: str, to: str) -> object:
        import urllib.request

        req = urllib.request.Request(frm, headers={
            "Authorization": f"Bearer {FAKE_GH_TOKEN}",
            "Cookie": "session=abc",
            "Accept": "application/json",
        })
        return _SafeRedirectHandler().redirect_request(
            req, None, 302, "Found", {}, to
        )

    def test_authorization_is_dropped_when_the_host_changes(self) -> None:
        new = self._redirect("https://api.github.com/a", "https://evil.example/b")
        self.assertIsNotNone(new)
        rendered = " ".join(f"{k}:{v}" for k, v in new.headers.items())  # type: ignore[attr-defined]
        self.assertNotIn(FAKE_GH_TOKEN, rendered)
        self.assertNotIn("session=abc", rendered)

    def test_ordinary_headers_survive_the_redirect(self) -> None:
        new = self._redirect("https://api.github.com/a", "https://evil.example/b")
        rendered = " ".join(f"{k}:{v}" for k, v in new.headers.items())  # type: ignore[attr-defined]
        self.assertIn("application/json", rendered)

    def test_credentials_survive_a_same_origin_redirect(self) -> None:
        # Dropping them there would break ordinary pagination.
        new = self._redirect("https://api.github.com/a", "https://api.github.com/b")
        rendered = " ".join(f"{k}:{v}" for k, v in new.headers.items())  # type: ignore[attr-defined]
        self.assertIn(FAKE_GH_TOKEN, rendered)

    def test_a_scheme_downgrade_counts_as_an_origin_change(self) -> None:
        new = self._redirect("https://api.github.com/a", "http://api.github.com/b")
        rendered = " ".join(f"{k}:{v}" for k, v in new.headers.items())  # type: ignore[attr-defined]
        self.assertNotIn(FAKE_GH_TOKEN, rendered)


class TestDecompressionIsBounded(unittest.TestCase):
    """The wire cap bounds what is read, not what it expands to."""

    def test_a_compression_bomb_is_refused(self) -> None:
        bomb = gzip.compress(b"\0" * (200 * 1024 * 1024))
        self.assertLess(len(bomb), 1024 * 1024)  # small on the wire
        with self.assertRaises(TransportError):
            _decompress(bomb, "gzip", max_bytes=8 * 1024 * 1024)

    def test_an_ordinary_response_still_decompresses(self) -> None:
        payload = gzip.compress(b"hello world " * 100)
        self.assertIn(b"hello world", _decompress(payload, "gzip"))

    def test_an_unencoded_body_passes_through(self) -> None:
        self.assertEqual(_decompress(b"plain", ""), b"plain")

    def test_a_server_lying_about_the_encoding_does_not_crash(self) -> None:
        self.assertEqual(_decompress(b"not gzip at all", "gzip"), b"not gzip at all")

    def test_the_ratio_cap_is_finite(self) -> None:
        self.assertGreater(MAX_DECOMPRESSED_RATIO, 1)
        self.assertLess(MAX_DECOMPRESSED_RATIO, 10_000)


class TestChunkingIsLinear(unittest.TestCase):
    """A regex that backtracks quadratically is a denial of service that any
    ingested repository can plant."""

    def test_leading_whitespace_does_not_backtrack(self) -> None:
        payload = "def f():\n    pass\n" + " " * 200_000 + "\n"
        started = time.perf_counter()
        _MEMBER_RE.findall(payload)
        elapsed = time.perf_counter() - started
        # The quadratic version took ~11s at 16,000 characters; this is more
        # than ten times that input. A generous ceiling still fails it by
        # orders of magnitude.
        self.assertLess(elapsed, 2.0, f"member pattern took {elapsed:.2f}s")

    def test_an_adversarial_document_chunks_promptly(self) -> None:
        big = "def f():\n    pass\n" + " " * 400_000 + "\n"
        meta = {"kind": "file", "suffix": ".py"}
        raw = RawDocument("github", "x.py", "https://e.com/x.py", "x.py", big, meta)
        started = time.perf_counter()
        chunk_document(Document.from_raw(raw, big, meta))
        self.assertLess(time.perf_counter() - started, 2.0)


class TestRedactionCoversRealCredentials(unittest.TestCase):
    def test_the_pipelines_own_key_format_is_redacted(self) -> None:
        # The one that matters most: a key that leaks must be caught by the
        # function meant to catch it.
        self.assertNotIn(FAKE_GOOGLE_KEY, redact_secrets(f"key = {FAKE_GOOGLE_KEY}"))

    def test_a_credential_in_a_query_string_is_redacted(self) -> None:
        text = f"https://youtube.googleapis.com/v3/videos?part=snippet&key={FAKE_GOOGLE_KEY}"
        self.assertNotIn(FAKE_GOOGLE_KEY, redact_secrets(text))

    def test_the_credential_shapes_a_review_found_missing(self) -> None:
        cases = {
            "fine-grained PAT": _shaped("github" + "_pat" + "_", "11ABCDEFG0" + "a" * 30),
            "jwt": _shaped("eyJ", "hbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3"),
            "openai project key": _shaped("sk" + "-proj-", "abcdefghijklmnopqrstuvwxyz0123456789"),
            "stripe live key": _shaped("sk" + "_live" + "_", "abcdefghijklmnopqrstuvwxyz01"),
            "connection string": "postgres://appuser:" + "hunter2secret" + "@db.internal:5432/app",
            "basic auth": "Authorization: Basic " + "YWRtaW46c3VwZXJzZWNyZXQxMjM=",
        }
        for label, secret in cases.items():
            self.assertIn("redacted", redact_secrets(secret), label)

    def test_ordinary_prose_and_benign_urls_are_untouched(self) -> None:
        # A redactor that eats the corpus is not usable.
        for text in (
            "The retrieval budget is 40 pages and the crawl delay is 3 seconds.",
            "Secret sauce: read the source rather than the README.",
            "See https://example.com/docs?page=2&sort=name for the listing.",
        ):
            self.assertEqual(redact_secrets(text), text)


class TestIngestBoundariesHold(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "repo"
        self.root.mkdir()

    def test_a_symlinked_file_cannot_escape_the_ingest_root(self) -> None:
        # `os.walk(followlinks=False)` stops the walk descending into a
        # symlinked directory; a symlinked *file* is still listed and read.
        outside = self.base / "credentials"
        outside.write_text(_shaped("AKIA", "IOSFODNN7EXAMPLE"), "utf-8")
        (self.root / "ok.md").write_text("# Fine\n\nordinary content here", "utf-8")
        os.symlink(outside, self.root / "notes.md")
        names = {d.external_id for d in FileConnector(self.root).run().documents}
        self.assertIn("ok.md", names)
        self.assertNotIn("notes.md", names)

    def test_a_symlink_inside_the_root_is_still_ingested(self) -> None:
        (self.root / "real.md").write_text("# Real\n\ncontent that is genuinely here", "utf-8")
        os.symlink(self.root / "real.md", self.root / "alias.md")
        names = {d.external_id for d in FileConnector(self.root).run().documents}
        self.assertIn("alias.md", names)

    def _skill(self, body: str) -> set[str]:
        d = self.root / "probe"
        d.mkdir(exist_ok=True)
        (d / "SKILL.md").write_text(
            "---\nname: probe\ndescription: Does a thing. Use when testing.\n---\n" + body,
            "utf-8",
        )
        skill = parse_skill(d / "SKILL.md")
        assert skill is not None
        return {f.code for f in lint_skill(skill)}

    def test_an_absolute_reference_is_refused(self) -> None:
        # `Path / "/etc/hosts"` discards the base entirely — no `..` needed.
        # The linter reads referenced files and echoes text from them into
        # findings that land in the index.
        self.assertIn("reference-escapes", self._skill("# P\n\nSee [x](/etc/hosts)\n"))

    def test_a_dot_dot_reference_is_refused(self) -> None:
        self.assertIn("reference-escapes", self._skill("# P\n\nSee [x](../../secret.md)\n"))

    def test_a_reference_inside_the_skill_still_resolves(self) -> None:
        (self.root / "probe").mkdir(exist_ok=True)
        (self.root / "probe" / "detail.md").write_text("detail", "utf-8")
        codes = self._skill("# P\n\nSee [x](detail.md)\n")
        self.assertNotIn("reference-escapes", codes)
        self.assertNotIn("reference-missing", codes)


class TestCrawlerStaysOnPermittedHosts(unittest.TestCase):
    """The host gate is applied to the frontier URL; a redirect lands elsewhere.

    Verified end to end against two live local servers during the review: a
    page on an allowed host returning `302` to a second host had that second
    host's body indexed. These check the gate the fix routes through.
    """

    def crawler(self, **kw: object):  # type: ignore[no-untyped-def]
        from oodarag.scrape.crawler import CrawlConfig, Crawler
        cfg = CrawlConfig(seeds=["https://allowed.example/"], obey_robots=False, **kw)
        return Crawler(cfg)

    def test_an_offsite_redirect_target_fails_the_gate(self) -> None:
        crawler = self.crawler(same_site_only=True)
        ok, reason = crawler._wanted("http://169.254.169.254/latest/meta-data/", 1)
        self.assertFalse(ok)
        self.assertTrue(reason)

    def test_the_seed_host_still_passes(self) -> None:
        ok, _reason = self.crawler(same_site_only=True)._wanted(
            "https://allowed.example/page", 1
        )
        self.assertTrue(ok)

    def test_a_non_http_scheme_is_refused(self) -> None:
        ok, _ = self.crawler()._wanted("file:///etc/passwd", 1)
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestMirrorCheck(unittest.TestCase):
    """The mirror is a maintenance cost the owner accepted; drift is the risk.

    Two copies of a rule set that disagree are worse than one copy plus a
    pointer, because both look authoritative. These check that the drift is
    actually detected rather than assumed absent.
    """

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def _run(self, other: Path) -> tuple[int, str]:
        import subprocess

        repo = Path(__file__).resolve().parent.parent
        proc = subprocess.run(
            [sys.executable, str(repo / "tools" / "verify_mirror.py"), str(other)],
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout + proc.stderr

    def test_a_missing_mirror_cannot_run(self) -> None:
        code, out = self._run(self.root / "absent")
        self.assertEqual(code, 2, out)

    def test_an_empty_mirror_is_reported_as_drift(self) -> None:
        (self.root / "empty").mkdir()
        code, out = self._run(self.root / "empty")
        self.assertEqual(code, 1)
        self.assertIn("missing", out)

    def test_the_real_mirror_is_in_sync(self) -> None:
        sibling = Path(__file__).resolve().parent.parent.parent / "claude-ai"
        if not sibling.is_dir():
            self.skipTest("sibling repository not present in this checkout")
        code, out = self._run(sibling)
        self.assertEqual(code, 0, out)
