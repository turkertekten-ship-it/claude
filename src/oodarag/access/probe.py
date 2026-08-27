"""Capability probing - establish what this environment can actually reach.

A data pipeline that assumes its sources are reachable fails in the worst
possible way: silently and partially. It builds an index over the three sources
that happened to work, answers confidently from a fraction of the corpus, and
nothing in the output says a word about the four sources that were blocked.

So reachability is treated as *data*, not as an assumption. `probe_all` runs a
bounded battery of live checks and returns a report that the rest of the system
consumes:

  * the OODA loop's Observe phase runs it each cycle and journals the result;
  * Decide reads it to pick a degraded strategy rather than retrying a blocked
    host forever;
  * every answer can cite which sources were live when its index was built.

The probes are deliberately cheap and bounded - one attempt, short timeout, run
concurrently - because this runs at the start of every cycle.
"""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from oodarag.util.http import HttpClient, HttpError, RetryPolicy, TransportError
from oodarag.util.logging import get_logger

log = get_logger("access")

OK = "ok"
BLOCKED = "blocked"          # reachable network, refused by policy (proxy/robots/auth)
UNAUTHORIZED = "unauthorized"  # reachable, but we lack credentials
UNREACHABLE = "unreachable"  # DNS/TLS/connection failure
DEGRADED = "degraded"        # works, but not fully


@dataclass(slots=True)
class ProbeResult:
    name: str
    kind: str
    target: str
    status: str
    latency_ms: float = 0.0
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)

    @property
    def usable(self) -> bool:
        return self.status in (OK, DEGRADED)


@dataclass(slots=True)
class Probe:
    name: str
    kind: str
    target: str
    run: Callable[[HttpClient], ProbeResult]


@dataclass
class AccessReport:
    results: list[ProbeResult] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)
    duration_s: float = 0.0
    environment: dict[str, Any] = field(default_factory=dict)

    def by_name(self, name: str) -> ProbeResult | None:
        return next((r for r in self.results if r.name == name), None)

    def usable(self, name: str) -> bool:
        result = self.by_name(name)
        return bool(result and result.usable)

    @property
    def by_kind(self) -> dict[str, list[ProbeResult]]:
        grouped: dict[str, list[ProbeResult]] = {}
        for result in self.results:
            grouped.setdefault(result.kind, []).append(result)
        return grouped

    @property
    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1
        return counts

    def degradations(self) -> list[str]:
        """What the pipeline must do differently, given what is unreachable.

        This is the part that makes the report actionable rather than
        decorative: each blocked capability maps to a named fallback.
        """
        notes: list[str] = []
        if not self.usable("github_api"):
            notes.append(
                "GitHub API unavailable: fall back to LocalGitConnector over an existing "
                "checkout; repository metadata, issues and PRs will be missing."
            )
        if self.usable("github_api") and not self.usable("github_raw"):
            notes.append(
                "raw.githubusercontent blocked: file bodies must come from the REST blob "
                "endpoint, which costs API quota - lower max_files accordingly."
            )
        web = self.by_kind.get("web", [])
        if web and not any(r.usable for r in web):
            notes.append(
                "No web host reachable: the web connector cannot contribute. Use only "
                "offline corpora and mark web-sourced answers as unavailable rather than stale."
            )
        elif any(not r.usable for r in web):
            blocked = [r.target for r in web if not r.usable]
            notes.append(
                f"Some web hosts are blocked ({', '.join(blocked)}). Seed the crawler only "
                "with reachable hosts; a blocked seed is a silent empty crawl otherwise."
            )
        if not self.usable("pypi"):
            notes.append(
                "PyPI unreachable: optional accelerators cannot be installed. The stdlib "
                "path is the only path - which is why it is the default."
            )
        if not self.usable("filesystem_write"):
            notes.append(
                "No writable scratch directory: the SQLite index cannot be persisted. "
                "Run fully in memory and treat the index as ephemeral."
            )
        if not notes:
            notes.append("All probed capabilities are available; no degradation required.")
        return notes

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at,
            "duration_s": round(self.duration_s, 3),
            "environment": self.environment,
            "summary": self.summary,
            "degradations": self.degradations(),
            "results": [asdict(r) for r in self.results],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def to_markdown(self) -> str:
        lines = [
            "# Access capability report",
            "",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(self.started_at))}  ",
            f"Probe duration: {self.duration_s:.2f}s  ",
            f"Summary: " + ", ".join(f"{n} {s}" for s, n in sorted(self.summary.items())),
            "",
            "## Environment",
            "",
        ]
        for key, value in sorted(self.environment.items()):
            lines.append(f"- **{key}**: `{value}`")
        lines += ["", "## Probes", "",
                  "| Capability | Kind | Target | Status | Latency | Detail |",
                  "|---|---|---|---|---|---|"]
        for result in sorted(self.results, key=lambda r: (r.kind, r.name)):
            mark = {OK: "ok", DEGRADED: "degraded", BLOCKED: "**blocked**",
                    UNAUTHORIZED: "**unauthorized**", UNREACHABLE: "**unreachable**"}[result.status]
            target = result.target if len(result.target) < 52 else result.target[:49] + "..."
            lines.append(
                f"| {result.name} | {result.kind} | `{target}` | {mark} | "
                f"{result.latency_ms:.0f}ms | {result.detail[:90]} |"
            )
        lines += ["", "## Required degradations", ""]
        lines += [f"{i}. {note}" for i, note in enumerate(self.degradations(), 1)]
        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- probe bodies


def _timed(fn: Callable[[], tuple[str, str, dict[str, Any]]]) -> tuple[str, str, dict, float]:
    started = time.monotonic()
    try:
        status, detail, evidence = fn()
    except Exception as e:  # a probe must never take the pipeline down with it
        status, detail, evidence = UNREACHABLE, f"{type(e).__name__}: {e}"[:200], {}
    return status, detail, evidence, (time.monotonic() - started) * 1000


def _classify_http_error(e: Exception) -> tuple[str, str]:
    if isinstance(e, HttpError):
        if e.status in (401, 407):
            return UNAUTHORIZED, f"HTTP {e.status}"
        if e.status == 403:
            return BLOCKED, f"HTTP 403 (policy denial or missing scope)"
        return BLOCKED, f"HTTP {e.status}"
    if isinstance(e, TransportError):
        text = str(e)
        if "403" in text:
            return BLOCKED, "proxy refused CONNECT (403)"
        return UNREACHABLE, text[:160]
    return UNREACHABLE, str(e)[:160]


def probe_github_api(client: HttpClient) -> ProbeResult:
    def run():
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            resp = client.get("https://api.github.com/rate_limit", headers=headers)
        except Exception as e:
            status, detail = _classify_http_error(e)
            return status, detail, {"token_present": bool(token)}
        core = resp.json().get("resources", {}).get("core", {})
        if not token:
            return DEGRADED, "anonymous access (60 req/hr)", {"remaining": core.get("remaining")}
        return OK, f"{core.get('remaining')}/{core.get('limit')} requests remaining", {
            "token_present": True, "limit": core.get("limit"), "remaining": core.get("remaining"),
        }

    status, detail, evidence, ms = _timed(run)
    return ProbeResult("github_api", "github", "api.github.com", status, ms, detail, evidence)


def probe_github_repo_scope(client: HttpClient, slugs: tuple[str, ...]) -> ProbeResult:
    """Which repositories this token can actually see.

    A token that authenticates is not a token that can read what you need. In a
    scoped environment the difference shows up as a 403 on the first real call,
    long after the pipeline has decided the source is healthy.
    """

    def run():
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        headers = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        allowed, denied = [], []
        for slug in slugs:
            try:
                client.get(f"https://api.github.com/repos/{slug}", headers=headers)
                allowed.append(slug)
            except Exception as e:
                status, _ = _classify_http_error(e)
                denied.append(f"{slug} ({status})")
        if not allowed:
            return BLOCKED, f"no repository readable; denied: {', '.join(denied)}", {
                "allowed": allowed, "denied": denied}
        status = OK if not denied else DEGRADED
        return status, f"{len(allowed)} readable, {len(denied)} denied", {
            "allowed": allowed, "denied": denied}

    status, detail, evidence, ms = _timed(run)
    return ProbeResult("github_repo_scope", "github", ",".join(slugs), status, ms, detail, evidence)


def probe_github_raw(client: HttpClient) -> ProbeResult:
    def run():
        try:
            resp = client.get(
                "https://raw.githubusercontent.com/python/cpython/main/README.rst",
                allow_status=(404,),
            )
        except Exception as e:
            status, detail = _classify_http_error(e)
            return status, detail, {}
        if resp.status == 404:
            return DEGRADED, "reachable but probe path missing", {"status": 404}
        return OK, f"{len(resp.body)} bytes", {"status": resp.status}

    status, detail, evidence, ms = _timed(run)
    return ProbeResult("github_raw", "github", "raw.githubusercontent.com", status, ms,
                       detail, evidence)


def probe_web_host(client: HttpClient, url: str, name: str) -> ProbeResult:
    def run():
        try:
            resp = client.get(url, allow_status=(401, 403, 404, 429))
        except Exception as e:
            status, detail = _classify_http_error(e)
            return status, detail, {}
        if resp.status >= 400:
            return BLOCKED, f"HTTP {resp.status}", {"status": resp.status}
        return OK, f"HTTP {resp.status}, {len(resp.body)} bytes", {
            "status": resp.status, "content_type": resp.content_type}

    status, detail, evidence, ms = _timed(run)
    host = urllib.parse.urlsplit(url).netloc
    return ProbeResult(name, "web", host, status, ms, detail, evidence)


def probe_pypi(client: HttpClient) -> ProbeResult:
    def run():
        try:
            payload = client.get_json("https://pypi.org/pypi/pip/json")
        except Exception as e:
            status, detail = _classify_http_error(e)
            return status, detail, {}
        return OK, f"pip {payload['info']['version']} visible", {}

    status, detail, evidence, ms = _timed(run)
    return ProbeResult("pypi", "packages", "pypi.org", status, ms, detail, evidence)


def probe_filesystem(path: str | Path) -> ProbeResult:
    started = time.monotonic()
    target = Path(path)
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe_file = target / ".oodarag-write-probe"
        probe_file.write_text("ok", encoding="utf-8")
        readback = probe_file.read_text(encoding="utf-8")
        probe_file.unlink()
        import shutil

        free_mb = shutil.disk_usage(target).free // (1024 * 1024)
        status = OK if readback == "ok" else DEGRADED
        detail = f"writable, {free_mb} MB free"
        if free_mb < 100:
            status, detail = DEGRADED, f"writable but only {free_mb} MB free"
        evidence = {"free_mb": free_mb}
    except OSError as e:
        status, detail, evidence = BLOCKED, f"{type(e).__name__}: {e}"[:160], {}
    ms = (time.monotonic() - started) * 1000
    return ProbeResult("filesystem_write", "local", str(target), status, ms, detail, evidence)


def _environment_facts() -> dict[str, Any]:
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    return {
        "https_proxy": proxy or "none",
        "proxy_enabled": bool(proxy),
        "github_token": "present" if (os.environ.get("GITHUB_TOKEN")
                                      or os.environ.get("GH_TOKEN")) else "absent",
        "anthropic_key": "present" if os.environ.get("ANTHROPIC_API_KEY") else "absent",
        "voyage_key": "present" if os.environ.get("VOYAGE_API_KEY") else "absent",
        "hostname": socket.gethostname(),
        "numpy": "available" if _has_numpy() else "absent (pure-python scoring)",
    }


def _has_numpy() -> bool:
    try:
        import numpy  # noqa: F401
    except ImportError:
        return False
    return True


DEFAULT_WEB_TARGETS: tuple[tuple[str, str], ...] = (
    ("web_pypi", "https://pypi.org/project/requests/"),
    ("web_wikipedia", "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"),
    ("web_youtube", "https://www.youtube.com/"),
    ("web_ibm", "https://www.ibm.com/think/topics/retrieval-augmented-generation"),
    ("web_arxiv", "https://arxiv.org/abs/2005.11401"),
)


def probe_all(
    *,
    client: HttpClient | None = None,
    repo_slugs: tuple[str, ...] = (),
    web_targets: tuple[tuple[str, str], ...] = DEFAULT_WEB_TARGETS,
    scratch_dir: str | Path = ".oodarag",
    timeout: float = 12.0,
) -> AccessReport:
    """Run the full battery concurrently and return a report."""
    client = client or HttpClient(
        rate_per_sec=20.0, burst=20, timeout=timeout,
        retry=RetryPolicy(attempts=1, base_delay=0.5),
    )
    report = AccessReport(environment=_environment_facts())
    started = time.monotonic()

    jobs: list[Callable[[], ProbeResult]] = [
        lambda: probe_github_api(client),
        lambda: probe_github_raw(client),
        lambda: probe_pypi(client),
        lambda: probe_filesystem(scratch_dir),
    ]
    if repo_slugs:
        jobs.append(lambda: probe_github_repo_scope(client, repo_slugs))
    for name, url in web_targets:
        jobs.append(lambda n=name, u=url: probe_web_host(client, u, n))

    with ThreadPoolExecutor(max_workers=8) as pool:
        report.results = list(pool.map(lambda job: job(), jobs))

    report.duration_s = time.monotonic() - started
    blocked = [r.name for r in report.results if not r.usable]
    log.info("access probe complete", probes=len(report.results),
             blocked=len(blocked), secs=round(report.duration_s, 2))
    if blocked:
        log.warn("capabilities unavailable", blocked=",".join(blocked))
    return report
