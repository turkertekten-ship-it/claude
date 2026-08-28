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


def safe_url(url: str) -> str:
    """A URL with its query string and userinfo removed, for logs and errors.

    An API key travels in a query string often enough that printing a raw URL
    is a credential leak with a long tail: it reaches log files, exception
    text, and any bug report pasted from either. The path is what identifies
    the request; the secret is what does not need to be in the message.
    """
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return "&lt;unparseable url&gt;"
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    redacted = urllib.parse.urlunsplit((parts.scheme, host, parts.path, "", ""))
    return redacted + ("?…" if parts.query else "")


class HttpError(Exception):
    def __init__(self, status: int, url: str, body: str = "", headers: dict[str, str] | None = None):
        super().__init__(f"HTTP {status} for {safe_url(url)}: {body[:300]}")
        self.status = status
        self.url = url
        self.body = body
        self.headers = headers or {}

    @property
    def retryable(self) -> bool:
        # 429 and 5xx are worth retrying; 408 is a server-side timeout.
        return self.status in (408, 425, 429) or 500 <= self.status < 600


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
    _bucket: TokenBucket = field(init=False, repr=False)
    _etags: dict[str, str] = field(default_factory=dict, repr=False)
    _opener: Any = field(default=None, init=False, repr=False)
    stats: dict[str, int] = field(default_factory=lambda: {
        "requests": 0, "retries": 0, "errors": 0, "not_modified": 0, "bytes": 0
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
            _SafeRedirectHandler(),
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
                if etag := resp.headers.get("etag"):
                    self._etags[url] = etag
                return resp
            except urllib.error.HTTPError as e:  # noqa: PERF203 - retry loop
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


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow redirects for safe methods only, and never carry credentials off-origin.

    Two separate rules. A POST is not silently replayed against a location the
    caller did not choose. And an `Authorization` header is stripped when the
    scheme, host or port changes, because urllib will otherwise hand a bearer
    token to whatever a redirect points at — which is a credential disclosure
    triggered by a remote server, not by anything the caller did.
    """

    #: Headers that identify the caller and must not cross an origin boundary.
    CREDENTIAL_HEADERS = ("authorization", "proxy-authorization", "cookie")

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        if req.get_method() not in ("GET", "HEAD"):
            return None
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is None:
            return None
        if _same_origin(req.full_url, newurl):
            return new
        for header in self.CREDENTIAL_HEADERS:
            new.headers.pop(header.capitalize(), None)
            new.headers.pop(header, None)
            new.unredirected_hdrs.pop(header.capitalize(), None)
            new.unredirected_hdrs.pop(header, None)
        return new


def _same_origin(a: str, b: str) -> bool:
    """Scheme, host and port all equal — the boundary credentials stop at."""
    try:
        pa, pb = urllib.parse.urlsplit(a), urllib.parse.urlsplit(b)
    except ValueError:
        return False
    return (pa.scheme, pa.hostname, pa.port) == (pb.scheme, pb.hostname, pb.port)


#: A compressed response may not expand past this multiple of its own size.
#: Text compresses at roughly 3-5x; a "zip bomb" is engineered for thousands.
#: Unbounded decompression turns a small malicious response into an
#: out-of-memory kill, which is a denial of service that needs no credentials
#: and no unusual access — only a server willing to send the bytes.
MAX_DECOMPRESSED_RATIO = 50
#: A floor, so that small responses are not penalised by the ratio alone.
MAX_DECOMPRESSED_FLOOR = 1 << 20  # 1 MiB


def _decompress(payload: bytes, encoding: str) -> bytes:
    enc = encoding.lower().strip()
    limit = max(MAX_DECOMPRESSED_FLOOR, len(payload) * MAX_DECOMPRESSED_RATIO)
    try:
        if enc == "gzip":
            return _bounded(zlib.decompressobj(16 + zlib.MAX_WBITS), payload, limit)
        if enc == "deflate":
            try:
                return _bounded(zlib.decompressobj(), payload, limit)
            except zlib.error:
                return _bounded(zlib.decompressobj(-zlib.MAX_WBITS), payload, limit)
    except (OSError, zlib.error):
        return payload  # server lied about the encoding; take the bytes as-is
    return payload


def _bounded(decompressor, payload: bytes, limit: int) -> bytes:
    """Decompress, stopping at `limit` bytes rather than at exhaustion."""
    out = decompressor.decompress(payload, limit)
    if decompressor.unconsumed_tail:
        raise HttpError(
            0, "&lt;decompression&gt;",
            f"refused: response expands past {limit} bytes "
            f"({MAX_DECOMPRESSED_RATIO}x its compressed size)")
    return out


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
