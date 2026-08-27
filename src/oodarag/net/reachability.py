"""Classify *why* a host could not be reached, instead of reporting that it wasn't.

The distinction this module exists to preserve:

    "youtube.com is blocked by the proxy"        <- true, and nearly useless
    "youtube.com is refused at CONNECT;
     youtube.googleapis.com tunnels fine and
     answers with PERMISSION_DENIED until an
     API key is supplied"                        <- true, and actionable

Those are different barriers with different remedies. The first needs a network
policy change and cannot be worked around in code; the second needs a
credential and works the moment one is supplied. A pipeline that collapses both
into `except Exception: log("unreachable")` throws away the only bit that tells
an operator what to do next, and invites the next reader to conclude a whole
data source is impossible when it is merely unconfigured.

Egress here is an allowlist rather than a blocklist: unlisted hosts fail at the
proxy's CONNECT, before TLS, so no amount of retrying, mirroring, or third-party
proxying reaches them. Retrying an `EGRESS_BLOCKED` host is always wasted work,
which is why `Barrier.retryable` says so explicitly.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from oodarag.util.http import HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger

log = get_logger("reachability")

# Substrings that identify a proxy refusing to open the tunnel at all. urllib
# surfaces these as OSError/URLError with the proxy's status line in the text,
# which is the only place the distinction survives.
_TUNNEL_MARKERS = (
    "tunnel connection failed",
    "cannot connect to proxy",
    "proxy connect",
    "connect tunnel failed",
)

_DNS_MARKERS = (
    "name or service not known",
    "nodename nor servname",
    "temporary failure in name resolution",
    "getaddrinfo failed",
)


class Barrier(str, Enum):
    """Why a request did not produce usable data."""

    OPEN = "open"
    """The host answered. Data is available (subject to the endpoint's own rules)."""

    EGRESS_BLOCKED = "egress_blocked"
    """Refused at the proxy's CONNECT. Not on the allowlist; unreachable from here."""

    DNS_FAILURE = "dns_failure"
    """The name did not resolve. A typo, or a host that no longer exists."""

    AUTH_REQUIRED = "auth_required"
    """The host answered and demanded a credential. Supply one and it works."""

    FORBIDDEN = "forbidden"
    """The host answered and refused this caller even with a credential."""

    NOT_FOUND = "not_found"
    """The host answered; this path does not exist. The host itself is reachable."""

    BAD_REQUEST = "bad_request"
    """The host answered and rejected the request as malformed.

    Reported separately from UNKNOWN because it is the opposite conclusion: the
    host is definitively reachable and the fault is in what was asked, so the
    fix is in the caller rather than in the network or a credential."""

    RATE_LIMITED = "rate_limited"
    """The host answered and asked us to slow down. Retryable, later."""

    SERVER_ERROR = "server_error"
    """The host answered with a fault of its own. Retryable."""

    TIMEOUT = "timeout"
    """No answer within the deadline. Retryable."""

    UNKNOWN = "unknown"
    """Classification failed. Treated as non-retryable so it cannot spin."""

    @property
    def reachable(self) -> bool:
        """Did the bytes get to the service at all?

        Every barrier except the three transport-level ones means the host
        answered, which is what decides whether a credential could ever help.
        """
        return self not in (
            Barrier.EGRESS_BLOCKED,
            Barrier.DNS_FAILURE,
            Barrier.TIMEOUT,
        )

    @property
    def retryable(self) -> bool:
        """Is trying again ever worth a request?

        `EGRESS_BLOCKED` is deliberately false: an allowlist does not change
        between two attempts a second apart, so a retry loop over it only burns
        the budget that a reachable source needed.
        """
        return self in (Barrier.RATE_LIMITED, Barrier.SERVER_ERROR, Barrier.TIMEOUT)

    @property
    def remedy(self) -> str:
        """What a human would have to change for this to succeed."""
        return {
            Barrier.OPEN: "nothing; the host is reachable",
            Barrier.EGRESS_BLOCKED: "add the host to the network egress allowlist; "
                                    "no code change can reach it from here",
            Barrier.DNS_FAILURE: "check the hostname; it did not resolve",
            Barrier.AUTH_REQUIRED: "supply a credential for this host",
            Barrier.FORBIDDEN: "the credential used lacks access to this resource",
            Barrier.NOT_FOUND: "check the path; the host itself answered",
            Barrier.BAD_REQUEST: "the host answered; the request was malformed for this path",
            Barrier.RATE_LIMITED: "wait for the quota window to reset",
            Barrier.SERVER_ERROR: "retry later; the fault is upstream",
            Barrier.TIMEOUT: "retry, or raise the timeout",
            Barrier.UNKNOWN: "inspect the recorded detail; classification failed",
        }[self]


@dataclass(slots=True)
class Reachability:
    """One probe result, carrying enough to be quoted as evidence."""

    url: str
    barrier: Barrier
    status: int | None = None
    detail: str = ""
    elapsed_s: float = 0.0
    checked_at: float = field(default_factory=time.time)

    @property
    def ok(self) -> bool:
        return self.barrier is Barrier.OPEN

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "barrier": self.barrier.value,
            "reachable": self.barrier.reachable,
            "retryable": self.barrier.retryable,
            "status": self.status,
            "detail": self.detail,
            "remedy": self.barrier.remedy,
            "elapsed_s": round(self.elapsed_s, 3),
            "checked_at": self.checked_at,
        }

    def __str__(self) -> str:
        code = self.status if self.status is not None else "-"
        return f"{self.barrier.value:<15} {str(code):>4}  {self.url}"


def classify_exception(exc: BaseException) -> tuple[Barrier, str]:
    """Map a transport or HTTP failure onto a barrier.

    Ordering matters: a proxy CONNECT refusal is reported by urllib as a
    generic OSError whose *message* is the only evidence, so it is matched
    before the broader transport cases.
    """
    text = str(exc).lower()

    if isinstance(exc, HttpError):
        return _classify_status(exc.status), f"HTTP {exc.status}: {exc.body[:200]}"

    if any(m in text for m in _TUNNEL_MARKERS):
        return Barrier.EGRESS_BLOCKED, str(exc)[:300]
    if any(m in text for m in _DNS_MARKERS):
        return Barrier.DNS_FAILURE, str(exc)[:300]
    if "timed out" in text or "timeout" in text:
        return Barrier.TIMEOUT, str(exc)[:300]
    if isinstance(exc, TransportError):
        # A TLS or connection reset from a host that *is* on the allowlist is
        # not the same as being blocked, but from here it is equally unusable.
        return Barrier.UNKNOWN, str(exc)[:300]
    return Barrier.UNKNOWN, f"{type(exc).__name__}: {exc}"[:300]


def _classify_status(status: int) -> Barrier:
    if status in (401, 407):
        return Barrier.AUTH_REQUIRED
    if status == 403:
        # A 403 that reached the service is an authorization answer, not an
        # egress refusal. Callers that need the finer reading (Google's
        # "unregistered callers" means *supply a key*) get it from the body.
        return Barrier.FORBIDDEN
    if status == 404:
        return Barrier.NOT_FOUND
    if status == 429:
        return Barrier.RATE_LIMITED
    if 500 <= status < 600:
        return Barrier.SERVER_ERROR
    if 200 <= status < 400:
        return Barrier.OPEN
    if 400 <= status < 500:
        # Any other 4xx still proves the host answered. Reporting it as UNKNOWN
        # would say "could not classify" about the one thing a probe is for.
        return Barrier.BAD_REQUEST
    return Barrier.UNKNOWN


def _refine_with_body(barrier: Barrier, body: str) -> tuple[Barrier, str]:
    """Promote a 403 to AUTH_REQUIRED when the service says a key is missing.

    Google's APIs answer an unauthenticated call with HTTP 403 and
    `PERMISSION_DENIED` / "without established identity". That is a credential
    problem, not an authorization one, and the remedy differs.
    """
    if barrier is not Barrier.FORBIDDEN:
        return barrier, body[:200]
    lowered = body.lower()
    signals = (
        "unregistered callers",
        "without established identity",
        "api key",
        "credential",
        "permission_denied",
    )
    if any(s in lowered for s in signals):
        return Barrier.AUTH_REQUIRED, body[:200]
    return barrier, body[:200]


def probe(url: str, client: HttpClient | None = None, *, timeout: float = 12.0) -> Reachability:
    """Ask one URL what stands between this process and its data.

    Probing uses a single attempt with retries disabled: the question is what
    the barrier *is*, and retrying a blocked host to find out it is still
    blocked only costs time.
    """
    own = client is None
    if own:
        client = HttpClient(timeout=timeout, rate_per_sec=20.0, burst=20)
        client.retry.attempts = 1
    assert client is not None

    started = time.monotonic()
    try:
        resp = client.get(url, allow_status=tuple(range(400, 600)))
    except (HttpError, TransportError, OSError) as exc:
        barrier, detail = classify_exception(exc)
        status = exc.status if isinstance(exc, HttpError) else None
        return Reachability(url, barrier, status, detail, time.monotonic() - started)

    barrier = _classify_status(resp.status)
    barrier, detail = _refine_with_body(barrier, resp.text[:400])
    return Reachability(url, barrier, resp.status, detail, resp.elapsed_s)


def probe_all(urls: list[str], *, timeout: float = 12.0) -> list[Reachability]:
    """Probe several URLs with one client, preserving input order."""
    client = HttpClient(timeout=timeout, rate_per_sec=20.0, burst=20)
    client.retry.attempts = 1
    results = [probe(u, client) for u in urls]
    blocked = sum(1 for r in results if r.barrier is Barrier.EGRESS_BLOCKED)
    log.info("reachability probe", probed=len(results), blocked=blocked)
    return results


def render_table(results: list[Reachability]) -> str:
    """A fixed-width table, so a probe run can be pasted into a source ledger."""
    if not results:
        return "(no hosts probed)"
    width = max(len(r.url) for r in results)
    lines = [
        f"{'URL'.ljust(width)}  {'BARRIER':<15} {'CODE':>4}  REMEDY",
        f"{'-' * width}  {'-' * 15} {'-' * 4}  {'-' * 40}",
    ]
    for r in results:
        code = str(r.status) if r.status is not None else "-"
        lines.append(f"{r.url.ljust(width)}  {r.barrier.value:<15} {code:>4}  {r.barrier.remedy}")
    return "\n".join(lines)


def render_json(results: list[Reachability]) -> str:
    return json.dumps([r.as_dict() for r in results], indent=2)
