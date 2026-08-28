#!/usr/bin/env python3
"""Map what this container can actually reach, and write it down as evidence.

Why this exists
  A sibling session reported "youtube blocked by proxy". That is a true
  statement about one hostname and a misleading one about a capability:
  `www.youtube.com` refuses to connect, while `www.googleapis.com/youtube/v3`
  answers normally and only wants an API key. A pipeline planned around the
  first sentence gives up; a pipeline planned around the second one ships.

  Egress here is an allowlist, and an allowlist is a fact about the
  environment, not about the internet. It is cheap to measure and expensive
  to guess at. This measures it.

What a result means
  reachable    an HTTP response came back. ANY status code counts, including
               401/403/404 - the bytes made the round trip, which is the only
               thing being tested. Authorisation is a separate question.
  blocked      the connection could not be established at all.
  error        something else went wrong; the reason is recorded verbatim.

Design
  Standard library only, in keeping with the pipeline's zero-dependency rule.
  Every probe is bounded by an explicit timeout, and the whole run is bounded
  by a wall-clock budget, in keeping with "everything is bounded".

Usage
  python3 tools/probe_egress.py                     # probe the default set
  python3 tools/probe_egress.py --json out.json     # capture for provenance
  python3 tools/probe_egress.py --url https://x/    # add ad-hoc targets
Exit
  0 always, unless the run itself could not start. An unreachable host is a
  finding, not a failure.
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Any

# Targets worth knowing about for this fleet's work, grouped by why we care.
DEFAULT_TARGETS: list[tuple[str, str, str]] = [
    # (group, url, why it matters here)
    ("video", "https://www.youtube.com/", "page scraping - the obvious path"),
    ("video", "https://www.googleapis.com/youtube/v3/videos?part=id&id=X",
     "YouTube Data API - metadata and caption tracks"),
    ("video", "https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId=X",
     "caption track list - reachable, but needs OAuth, not just a key"),
    ("video", "https://i.ytimg.com/", "thumbnail CDN"),
    ("code", "https://github.com/", "repository browsing"),
    ("code", "https://api.github.com/", "GitHub REST API"),
    ("code", "https://raw.githubusercontent.com/", "raw file fetch - skill install path"),
    ("packages", "https://pypi.org/simple/", "Python package index"),
    ("packages", "https://files.pythonhosted.org/", "Python package payloads"),
    ("packages", "https://registry.npmjs.org/", "npm registry"),
    ("models", "https://huggingface.co/", "model and tokenizer downloads"),
    ("models", "https://huggingface.co/ds4sd/docling-models",
     "Docling layout + TableFormer weights - blocks Docling PDF conversion"),
    ("models", "https://cdn-lfs.huggingface.co/", "HF large-file CDN"),
    ("papers", "https://arxiv.org/", "paper source"),
    ("vendor", "https://research.ibm.com/", "Docling / Granite documentation"),
    ("vendor", "https://www.ibm.com/", "vendor documentation"),
    ("api", "https://api.anthropic.com/", "Claude API"),
]

USER_AGENT = "oodarag-egress-probe/1.0 (+bounded diagnostic probe)"


def probe(url: str, timeout: float) -> dict[str, Any]:
    """Probe one URL. Any HTTP response means reachable; no connection means blocked."""
    started = time.monotonic()
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _result(url, "reachable", started, status=resp.status)
    except urllib.error.HTTPError as exc:
        # The server answered. 401/403/404 are answers - the path is open.
        return _result(url, "reachable", started, status=exc.code,
                       detail=f"HTTP {exc.code} {exc.reason}")
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, ssl.SSLError):
            return _result(url, "error", started, detail=f"TLS: {reason}")
        if isinstance(reason, socket.timeout):
            return _result(url, "blocked", started, detail=f"timed out after {timeout}s")
        return _result(url, "blocked", started, detail=str(reason))
    except socket.timeout:
        return _result(url, "blocked", started, detail=f"timed out after {timeout}s")
    except Exception as exc:  # noqa: BLE001 - a probe must never take the run down
        return _result(url, "error", started, detail=f"{type(exc).__name__}: {exc}")


def _result(url: str, state: str, started: float, *, status: int | None = None,
            detail: str = "") -> dict[str, Any]:
    return {
        "url": url,
        "state": state,
        "status": status,
        "detail": detail,
        "elapsed_ms": round((time.monotonic() - started) * 1000),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--timeout", type=float, default=15.0,
                    help="per-probe timeout in seconds (default: 15)")
    ap.add_argument("--budget", type=float, default=180.0,
                    help="wall-clock budget for the whole run in seconds (default: 180)")
    ap.add_argument("--url", action="append", default=[],
                    help="probe an extra URL (repeatable)")
    ap.add_argument("--only", default="", help="restrict to one group")
    ap.add_argument("--json", default="", help="write the full result set to this path")
    args = ap.parse_args(argv)

    targets = [t for t in DEFAULT_TARGETS if not args.only or t[0] == args.only]
    targets += [("adhoc", u, "supplied on the command line") for u in args.url]

    began = time.monotonic()
    results: list[dict[str, Any]] = []
    skipped: list[str] = []

    for group, url, why in targets:
        if time.monotonic() - began > args.budget:
            skipped.append(url)
            continue
        row = probe(url, args.timeout)
        row["group"] = group
        row["why"] = why
        results.append(row)
        mark = {"reachable": "ok  ", "blocked": "BLOCK", "error": "ERR "}[row["state"]]
        status = row["status"] if row["status"] is not None else "-"
        print(f"  {mark} {status:>4}  {url}")
        if row["detail"] and row["state"] != "reachable":
            print(f"            {row['detail']}")

    reachable = [r for r in results if r["state"] == "reachable"]
    blocked = [r for r in results if r["state"] == "blocked"]

    print()
    print(f"probe_egress: {len(reachable)} reachable, {len(blocked)} blocked, "
          f"{len(results) - len(reachable) - len(blocked)} error, "
          f"{len(skipped)} skipped (budget)")
    if skipped:
        # Never let a budget cut look like a clean sweep.
        print("  not probed, budget exhausted:")
        for url in skipped:
            print(f"    - {url}")

    if args.json:
        payload = {
            "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "timeout_s": args.timeout,
            "budget_s": args.budget,
            "results": results,
            "not_probed": skipped,
        }
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"  wrote {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
