#!/usr/bin/env python3
"""Tests for tools/probe_egress.py.

The point of the tool is a classification: does a host answer, or is the
connection refused? Getting that boundary wrong is the whole failure mode it
exists to correct - a 403 from an API means "bring a key", a refused CONNECT
means "this host is not on the allowlist", and treating the first as the second
is how a fleet concludes a data source is closed when it is merely locked.

These tests never touch the network. The probe's own transport is stubbed, so
the suite runs identically in a container with no egress at all.
"""

from __future__ import annotations

import socket
import ssl
import sys
import unittest.mock
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import probe_egress  # noqa: E402

CASES = []


def case(name):
    def wrap(fn):
        CASES.append((name, fn))
        return fn
    return wrap


def _probe_raising(exc):
    """Run one probe with the transport replaced by a raised exception."""
    with unittest.mock.patch.object(probe_egress.urllib.request, "urlopen", side_effect=exc):
        return probe_egress.probe("https://example.test/", timeout=1.0)


@case("an HTTP 200 is reachable")
def t_ok():
    resp = unittest.mock.MagicMock()
    resp.status = 200
    resp.__enter__.return_value = resp
    with unittest.mock.patch.object(probe_egress.urllib.request, "urlopen", return_value=resp):
        r = probe_egress.probe("https://example.test/", timeout=1.0)
    assert r["state"] == "reachable", r
    assert r["status"] == 200, r


@case("an HTTP 403 from the server is reachable, not blocked")
def t_403():
    # The case that matters: googleapis answering "bring an API key" is an open
    # path. Classifying it as blocked would retire a working data source.
    exc = urllib.error.HTTPError("https://example.test/", 403, "Forbidden", {}, None)
    r = _probe_raising(exc)
    assert r["state"] == "reachable", r
    assert r["status"] == 403, r


@case("an HTTP 404 is reachable")
def t_404():
    exc = urllib.error.HTTPError("https://example.test/", 404, "Not Found", {}, None)
    r = _probe_raising(exc)
    assert r["state"] == "reachable", r


@case("a refused tunnel is blocked")
def t_tunnel():
    # What the proxy actually returns for a host that is not on the allowlist.
    exc = urllib.error.URLError("Tunnel connection failed: 403 Forbidden")
    r = _probe_raising(exc)
    assert r["state"] == "blocked", r
    assert r["status"] is None, r
    assert "Tunnel connection failed" in r["detail"], r


@case("a timeout is blocked, and says so")
def t_timeout():
    r = _probe_raising(urllib.error.URLError(socket.timeout("timed out")))
    assert r["state"] == "blocked", r
    assert "timed out" in r["detail"], r


@case("a TLS failure is an error, not a block")
def t_tls():
    # A certificate problem is a local misconfiguration, not a policy decision.
    # Reporting it as "blocked" would send someone hunting the wrong thing.
    r = _probe_raising(urllib.error.URLError(ssl.SSLError("bad handshake")))
    assert r["state"] == "error", r
    assert "TLS" in r["detail"], r


@case("an unexpected exception is contained, not propagated")
def t_contained():
    r = _probe_raising(RuntimeError("something odd"))
    assert r["state"] == "error", r
    assert "RuntimeError" in r["detail"], r


@case("every probe records an elapsed time")
def t_elapsed():
    r = _probe_raising(urllib.error.URLError("nope"))
    assert isinstance(r["elapsed_ms"], int) and r["elapsed_ms"] >= 0, r


@case("the default target set is well formed")
def t_targets():
    assert probe_egress.DEFAULT_TARGETS, "no default targets"
    for row in probe_egress.DEFAULT_TARGETS:
        assert len(row) == 3, row
        group, url, why = row
        assert url.startswith("https://"), url
        assert why.strip(), f"{url} has no stated reason"


@case("an exhausted budget is reported, never silently dropped")
def t_budget():
    # A budget cut that prints like a clean sweep is the tool lying about
    # coverage. Zero budget means everything lands in not_probed.
    out = []
    with unittest.mock.patch.object(probe_egress, "probe") as fake, \
            unittest.mock.patch("builtins.print", lambda *a, **k: out.append(" ".join(map(str, a)))):
        rc = probe_egress.main(["--budget", "-1"])
        assert not fake.called, "probes ran despite an exhausted budget"
    assert rc == 0
    joined = "\n".join(out)
    assert "budget exhausted" in joined, joined
    assert "skipped (budget)" in joined, joined


def main() -> int:
    failed = 0
    for name, fn in CASES:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {name}\n       {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  ERROR {name}\n       {type(exc).__name__}: {exc}")
        else:
            print(f"  ok   {name}")
    print()
    print("all cases passed" if not failed else f"{failed} case(s) failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
