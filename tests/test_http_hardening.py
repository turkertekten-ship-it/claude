#!/usr/bin/env python3
"""Regression tests for three defects in the HTTP client.

All three were reported by a sibling branch that had already fixed them, and
all three were confirmed present here before being fixed. Each is a case where
reading the code does not reveal the problem: the credential leak only appears
in the log line, the redirect leak only when a server chooses to redirect, and
the decompression limit only when a response is hostile.

Run: python3 tests/test_http_hardening.py
"""

import gzip
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from oodarag.util.http import (  # noqa: E402
    MAX_DECOMPRESSED_RATIO, HttpError, _decompress, _same_origin, safe_url,
)

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def credential_leak_cases() -> None:
    """A key in a query string must not reach a log line or an exception."""
    print("credentials in URLs")
    leaky = "https://api.example.com/v3/search?key=sk-SECRET-123&q=hello"
    safe = safe_url(leaky)
    check("the secret is gone", "sk-SECRET-123" not in safe, safe)
    check("the query is marked as elided, not silently dropped",
          safe.endswith("?…"), safe)
    check("the path survives, so the request is still identifiable",
          "/v3/search" in safe, safe)
    check("userinfo is stripped too",
          "hunter2" not in safe_url("https://user:hunter2@example.com/x"),
          safe_url("https://user:hunter2@example.com/x"))
    check("a URL with no query is left alone",
          safe_url("https://example.com/a/b") == "https://example.com/a/b")
    check("an unparseable URL does not raise",
          isinstance(safe_url("http://[unclosed"), str))

    # The reason this matters: the exception message is what gets pasted.
    err = HttpError(401, leaky, "unauthorized")
    check("the exception message carries no secret",
          "sk-SECRET-123" not in str(err), str(err))
    check("but the object still has the real URL for the caller that needs it",
          err.url == leaky)


def redirect_credential_cases() -> None:
    """An Authorization header must stop at an origin boundary."""
    print("\\nredirects across origins")
    check("same host, scheme and port is same-origin",
          _same_origin("https://a.example/x", "https://a.example/y"))
    check("a different host is not",
          not _same_origin("https://a.example/x", "https://evil.example/y"))
    check("a different scheme is not",
          not _same_origin("https://a.example/x", "http://a.example/x"))
    check("a different port is not",
          not _same_origin("https://a.example:443/x", "https://a.example:8443/x"))
    check("an unparseable target is not treated as same-origin",
          not _same_origin("https://a.example/x", "http://[unclosed"))

    from oodarag.util.http import _SafeRedirectHandler
    check("cookies are stripped alongside authorization",
          "cookie" in _SafeRedirectHandler.CREDENTIAL_HEADERS)


def decompression_cases() -> None:
    """A compressed response may not expand without bound."""
    print("\\ndecompression limits")
    check("ordinary content still round-trips",
          _decompress(gzip.compress(b"hello world"), "gzip") == b"hello world")
    check("deflate still round-trips",
          _decompress(zlib.compress(b"hello"), "deflate") == b"hello")

    # 200 MiB of one repeated byte compresses to roughly 200 KB.
    bomb = gzip.compress(b"A" * (200 * 1024 * 1024))
    check("the bomb really is small on the wire", len(bomb) < 1_000_000, str(len(bomb)))
    try:
        _decompress(bomb, "gzip")
        check("a zip bomb is refused", False, "it decompressed unbounded")
    except HttpError as exc:
        check("a zip bomb is refused", True)
        check("and the refusal says why",
              str(MAX_DECOMPRESSED_RATIO) in str(exc), str(exc)[:120])

    check("a server lying about the encoding still yields the raw bytes",
          _decompress(b"not actually gzip", "gzip") == b"not actually gzip")
    check("an unknown encoding is passed through",
          _decompress(b"plain", "br") == b"plain")


def redaction_consistency_cases() -> None:
    """Every path that reports a URL must redact it, not just HttpError.

    A security review found three that did not: two log lines and the
    TransportError message embedded the raw URL, query string intact, while
    HttpError next to them used safe_url. No caller in this repository puts a
    credential in a query string -- the GitHub client authenticates by header
    -- so nothing leaked. "No caller does that yet" is not a policy, and this
    module states one.
    """
    print("redaction consistency")
    import re
    source = (Path(__file__).resolve().parent.parent
              / "src" / "oodarag" / "util" / "http.py").read_text(encoding="utf-8")
    patterns = [r"url=url\b", r"\(\{url\}\)", r"request failed: \{url\}"]
    raw_uses = [m for pat in patterns for m in re.findall(pat, source)]
    check("no reporting path embeds the unredacted url",
          not raw_uses, f"found {raw_uses}")


def pagination_origin_cases() -> None:
    """A Link header is a server-supplied URL this client fetches WITH a token.

    _SafeRedirectHandler strips credentials across origins on a redirect, but
    following a Link header is a fresh request, not a redirect, so it walked
    around that protection entirely.
    """
    print("pagination origin")
    from oodarag.util.http import _same_origin
    check("same-origin next page is followed",
          _same_origin("https://api.github.com/r?page=1",
                       "https://api.github.com/r?page=2"))
    check("cross-origin next page is refused",
          not _same_origin("https://api.github.com/r", "https://evil.example/r"))
    check("scheme downgrade is refused",
          not _same_origin("https://api.github.com/r", "http://api.github.com/r"))
    source = (Path(__file__).resolve().parent.parent
              / "src" / "oodarag" / "ingest" / "github.py").read_text(encoding="utf-8")
    check("paginate checks the origin before following",
          "_same_origin(url, nxt)" in source)


def agent_env_cases() -> None:
    """Agent mode bypasses permission prompts; it must not also carry tokens.

    A successful prompt injection in an agent-mode case would otherwise get
    host execution WITH the operator's credentials -- and induced misbehaviour
    is this repository's entire subject. No suite sets `mode: agent` today,
    which is the reason to close it now rather than after the first one does.
    """
    print("agent-mode environment")
    import os
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from workbench.backend import ClaudeCLIBackend, Request

    os.environ["GITHUB_TOKEN"] = "ghp_probe"
    os.environ["SOME_API_KEY"] = "sk-probe"
    os.environ["ORDINARY_VAR"] = "keep-me"
    try:
        b = ClaudeCLIBackend()
        text = b._env(Request(prompt="p", model="m", mode="text"))
        agent = b._env(Request(prompt="p", model="m", mode="agent"))
        check("text mode is unchanged", text.get("GITHUB_TOKEN") == "ghp_probe")
        check("agent mode withholds a named token", "GITHUB_TOKEN" not in agent)
        check("agent mode withholds anything that looks like one",
              "SOME_API_KEY" not in agent)
        check("agent mode keeps ordinary variables",
              agent.get("ORDINARY_VAR") == "keep-me" and "PATH" in agent)
    finally:
        for k in ("GITHUB_TOKEN", "SOME_API_KEY", "ORDINARY_VAR"):
            os.environ.pop(k, None)


def main() -> int:
    credential_leak_cases()
    redirect_credential_cases()
    decompression_cases()
    redaction_consistency_cases()
    pagination_origin_cases()
    agent_env_cases()

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
