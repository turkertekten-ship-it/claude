"""A small, well-behaved HTTP client built on urllib.

Why not `requests`: the core of this pipeline is dependency-free (ADR 0001),
and the two things `requests` would buy us here - connection pooling and a
nicer API - matter less than the things we need but would have to add anyway:
per-host rate limiting, retry policy that honours `Retry-After`, conditional
requests via ETag, hard response-size caps, and content-type gating.

The client is proxy-aware by default: urllib reads HTTPS_PROXY/HTTP_PROXY and
NO_PROXY from the environment, which is how this runs inside an egress-filtered
container without any special casing.
"""

from __future__ import annotations

import gzip
import io
import json
import random
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib
from dataclasses import dataclass, field
from typing import Any

from oodarag.util.logging import get_logger
from oodarag.util.ratelimit import TokenBucket

log = get_logger("http")

DEFAULT_UA = "oodarag/0.1 (+https://github.com/turkertekten-ship-it/claude; research pipeline)"
MAX_BYTES = 8 * 1024 * 1024  # 8 MiB: nothing useful to a text pipeline is bigger


class HttpError(Exception):
    def __init__(self, status: int, url: str, body: str = "", headers: dict[str, str] | None = None):
        super().__init__(f"HTTP {status} for {url}: {body[:300]}")
        self.status = status
        self.url = url
        self.body = body
        self.headers = headers or {}

    @property
    def retryable(self) -> bool:
        # 429 and 5xx are worth retrying; 408 is a server-side timeout.
        if self.status in (408, 425, 429) or 500 <= self.status < 600:
            return True
        # GitHub signals *both* primary quota exhaustion and secondary rate
        # limits with 403, not 429. Treating every 403 as permanent turns the
        # single most common GitHub failure mode into a hard failure halfway
        # through an ingest. Only retry the ones that actually say "rate limit",
        # so a genuine permission denial still fails fast.
        if self.status == 403:
            if self.headers.get("x-ratelimit-remaining") == "0":
                return True
            if "retry-after" in self.headers:
                return True
            body = self.body.lower()
            return any(marker in body for marker in
                       ("rate limit", "secondary rate", "abuse detection"))
        return False


class TransportError(Exception):
    """Network-level failure (DNS, TLS, connection reset, timeout)."""


@dataclass(slots=True)
class Response:
    url: str
    status: int
    headers: dict[str, str]
    body: bytes
    from_cache: bool = False
    elapsed_s: float = 0.0

    @property
    def text(self) -> str:
        charset = "utf-8"
        ctype = self.headers.get("content-type", "")
        if "charset=" in ctype:
            charset = ctype.split("charset=", 1)[1].split(";")[0].strip().strip('"') or "utf-8"
        try:
            return self.body.decode(charset, "replace")
        except LookupError:
            return self.body.decode("utf-8", "replace")

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8", "replace"))

    @property
    def content_type(self) -> str:
        return self.headers.get("content-type", "").split(";")[0].strip().lower()


@dataclass(slots=True)
class RetryPolicy:
    attempts: int = 4
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: float = 0.25

    def delay_for(self, attempt: int, retry_after: float | None = None) -> float:
        if retry_after is not None:
            return min(retry_after, self.max_delay)
        raw = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        return raw * (1.0 + random.uniform(-self.jitter, self.jitter))


@dataclass
class CircuitBreaker:
    """Stop paying the full retry cost for a host that is known unreachable.

    Retry policy assumes failures are transient. Egress policy is not: when a
    proxy refuses CONNECT to a host, every request to it fails identically for
    the life of the process, and each one costs the full attempt count plus
    backoff. Ingesting eight videos from a blocked domain took 129 seconds to
    produce nothing, and would have cost the same on every subsequent run.

    Connection-level failures are counted per host. After `threshold`
    consecutive ones with no success between, the circuit opens and further
    requests to that host fail immediately for `cooldown_s`; any success closes
    it. Only transport failures count - an HTTP error means the host answered,
    which is the opposite of unreachable.
    """

    threshold: int = 3
    cooldown_s: float = 300.0
    _failures: dict[str, int] = field(default_factory=dict, repr=False)
    _opened_at: dict[str, float] = field(default_factory=dict, repr=False)

    def is_open(self, host: str) -> bool:
        opened = self._opened_at.get(host)
        if opened is None:
            return False
        if time.monotonic() - opened >= self.cooldown_s:
            # Cooldown elapsed: let one probe through to see if it recovered.
            del self._opened_at[host]
            self._failures[host] = 0
            return False
        return True

    def record_failure(self, host: str) -> None:
        count = self._failures.get(host, 0) + 1
        self._failures[host] = count
        if count >= self.threshold and host not in self._opened_at:
            self._opened_at[host] = time.monotonic()
            log.warn("circuit opened; host treated as unreachable",
                     host=host, failures=count, cooldown_s=self.cooldown_s)

    def record_success(self, host: str) -> None:
        self._failures.pop(host, None)
        self._opened_at.pop(host, None)

    @property
    def open_hosts(self) -> list[str]:
        return sorted(self._opened_at)


class CircuitOpenError(TransportError):
    """Raised instead of retrying a host already established as unreachable."""


@dataclass
class HttpClient:
    """Blocking HTTP client with retries, rate limiting and conditional GETs."""

    user_agent: str = DEFAULT_UA
    timeout: float = 30.0
    rate_per_sec: float = 5.0
    burst: int = 10
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    max_bytes: int = MAX_BYTES
    verify_tls: bool = True
    default_headers: dict[str, str] = field(default_factory=dict)
    breaker: CircuitBreaker = field(default_factory=CircuitBreaker)
    _bucket: TokenBucket = field(init=False, repr=False)
    _etags: dict[str, str] = field(default_factory=dict, repr=False)
    _opener: Any = field(default=None, init=False, repr=False)
    stats: dict[str, int] = field(default_factory=lambda: {
        "requests": 0, "retries": 0, "errors": 0, "not_modified": 0, "bytes": 0,
        "short_circuited": 0,
    })

    def __post_init__(self) -> None:
        self._bucket = TokenBucket(self.rate_per_sec, self.burst)
        ctx = ssl.create_default_context()
        if not self.verify_tls:  # never used by default; here for local mitm debugging only
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        handlers = [
            urllib.request.ProxyHandler(),          # reads *_PROXY / NO_PROXY from env
            urllib.request.HTTPSHandler(context=ctx),
            _NoRedirectOnPost(),
        ]
        self._opener = urllib.request.build_opener(*handlers)

    # ---------------------------------------------------------------- requests

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        body: bytes | None = None,
        conditional: bool = False,
        allow_status: tuple[int, ...] = (),
    ) -> Response:
        hdrs = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            **self.default_headers,
            **(headers or {}),
        }
        if conditional and url in self._etags:
            hdrs["If-None-Match"] = self._etags[url]

        host = urllib.parse.urlsplit(url).netloc
        if self.breaker.is_open(host):
            self.stats["short_circuited"] += 1
            raise CircuitOpenError(
                f"{host} is unreachable from this environment (circuit open); "
                f"skipped without retrying. See internal/CAPABILITY-PROTOCOL.md."
            )

        last_exc: Exception | None = None
        for attempt in range(1, self.retry.attempts + 1):
            self._bucket.acquire()
            started = time.monotonic()
            req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
            try:
                with self._opener.open(req, timeout=self.timeout) as raw:
                    payload = self._read_capped(raw)
                    resp_headers = {k.lower(): v for k, v in raw.headers.items()}
                    resp = Response(
                        url=raw.geturl(),
                        status=raw.status,
                        headers=resp_headers,
                        body=_decompress(payload, resp_headers.get("content-encoding", "")),
                        elapsed_s=time.monotonic() - started,
                    )
                self.stats["requests"] += 1
                self.stats["bytes"] += len(resp.body)
                self.breaker.record_success(host)
                if etag := resp.headers.get("etag"):
                    self._etags[url] = etag
                return resp
            except urllib.error.HTTPError as e:  # noqa: PERF203 - retry loop
                # The host answered, so it is reachable - whatever it said.
                self.breaker.record_success(host)
                resp_headers = {k.lower(): v for k, v in (e.headers or {}).items()}
                if e.code == 304:
                    self.stats["not_modified"] += 1
                    return Response(url, 304, resp_headers, b"", from_cache=True,
                                    elapsed_s=time.monotonic() - started)
                if e.code in allow_status:
                    payload = e.read() if hasattr(e, "read") else b""
                    return Response(url, e.code, resp_headers,
                                    _decompress(payload, resp_headers.get("content-encoding", "")),
                                    elapsed_s=time.monotonic() - started)
                err = HttpError(e.code, url, _safe_read(e), resp_headers)
                last_exc = err
                if not err.retryable or attempt == self.retry.attempts:
                    self.stats["errors"] += 1
                    raise err
                wait = self.retry.delay_for(attempt, _retry_after(resp_headers))
                self.stats["retries"] += 1
                log.warn("retrying", url=url, status=e.code, attempt=attempt, wait=round(wait, 2))
                time.sleep(wait)
            except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as e:
                last_exc = TransportError(f"{type(e).__name__}: {e} ({url})")
                if attempt == self.retry.attempts:
                    self.stats["errors"] += 1
                    self.breaker.record_failure(host)
                    raise last_exc from e
                wait = self.retry.delay_for(attempt)
                self.stats["retries"] += 1
                log.warn("transport retry", url=url, err=str(e)[:120], attempt=attempt,
                         wait=round(wait, 2))
                time.sleep(wait)
        raise last_exc or TransportError(f"request failed: {url}")

    def get(self, url: str, **kw: Any) -> Response:
        return self.request("GET", url, **kw)

    def get_json(self, url: str, **kw: Any) -> Any:
        headers = {"Accept": "application/json", **kw.pop("headers", {})}
        return self.get(url, headers=headers, **kw).json()

    def head(self, url: str, **kw: Any) -> Response:
        return self.request("HEAD", url, **kw)

    # ----------------------------------------------------------------- helpers

    def _read_capped(self, raw: Any) -> bytes:
        """Read at most max_bytes, so one pathological URL cannot exhaust memory."""
        declared = raw.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > self.max_bytes:
            raise TransportError(f"response too large: {declared} bytes > cap {self.max_bytes}")
        buf = io.BytesIO()
        while True:
            chunk = raw.read(65536)
            if not chunk:
                break
            buf.write(chunk)
            if buf.tell() > self.max_bytes:
                raise TransportError(f"response exceeded cap of {self.max_bytes} bytes")
        return buf.getvalue()


class _NoRedirectOnPost(urllib.request.HTTPRedirectHandler):
    """Follow redirects for safe methods only; never silently replay a POST."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        if req.get_method() not in ("GET", "HEAD"):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _decompress(payload: bytes, encoding: str) -> bytes:
    enc = encoding.lower().strip()
    try:
        if enc == "gzip":
            return gzip.decompress(payload)
        if enc == "deflate":
            try:
                return zlib.decompress(payload)
            except zlib.error:
                return zlib.decompress(payload, -zlib.MAX_WBITS)
    except (OSError, zlib.error):
        return payload  # server lied about the encoding; take the bytes as-is
    return payload


def _safe_read(e: Any) -> str:
    try:
        return e.read().decode("utf-8", "replace")
    except Exception:
        return ""


def _retry_after(headers: dict[str, str]) -> float | None:
    """Honour Retry-After, and GitHub's x-ratelimit-reset when the quota is spent."""
    if (ra := headers.get("retry-after")) and ra.strip().isdigit():
        return float(ra.strip())
    if headers.get("x-ratelimit-remaining") == "0" and (reset := headers.get("x-ratelimit-reset")):
        try:
            return max(0.0, float(reset) - time.time()) + 1.0
        except ValueError:
            return None
    return None


def urljoin(base: str, link: str) -> str:
    return urllib.parse.urljoin(base, link)


def normalize_url(url: str, *, drop_fragment: bool = True, drop_query: bool = False) -> str:
    """Canonical form used for crawl dedupe.

    Lowercases scheme/host, drops the default port and the fragment, sorts query
    parameters, and strips common tracking params so `?utm_source=...` does not
    make a page look new.
    """
    parts = urllib.parse.urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    host = parts.hostname or ""
    netloc = host.lower()
    if parts.port and not ((scheme == "https" and parts.port == 443) or (scheme == "http" and parts.port == 80)):
        netloc = f"{netloc}:{parts.port}"
    path = urllib.parse.quote(urllib.parse.unquote(parts.path), safe="/%:@&=+$,~()!*'")
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    query = ""
    if parts.query and not drop_query:
        tracking = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
                    "gclid", "fbclid", "ref", "ref_src", "mc_cid", "mc_eid"}
        pairs = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
                 if k.lower() not in tracking]
        query = urllib.parse.urlencode(sorted(pairs))
    fragment = "" if drop_fragment else parts.fragment
    return urllib.parse.urlunsplit((scheme, netloc, path or "/", query, fragment))


def same_site(a: str, b: str, *, include_subdomains: bool = True) -> bool:
    ha = (urllib.parse.urlsplit(a).hostname or "").lower()
    hb = (urllib.parse.urlsplit(b).hostname or "").lower()
    if not ha or not hb:
        return False
    if ha == hb:
        return True
    if not include_subdomains:
        return False
    return ha.endswith("." + hb) or hb.endswith("." + ha)
