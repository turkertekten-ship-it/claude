"""A small, well-behaved HTTP client built on urllib.

Why not `requests`: the core of this pipeline is dependency-free (ADR 0001),
and the two things `requests` would buy us here - connection pooling and a
nicer API - matter less than the things we need but would have to add anyway:
per-host rate limiting, retry policy that honours `Retry-After`, conditional
requests via ETag, hard response-size caps, and content-type gating.

Two decisions here are load-bearing rather than convenient.

The size cap is enforced twice: once on the bytes coming off the wire, and
again on the bytes coming out of the decoder. A cap applied only to the
compressed stream is not a cap at all - a gzip bomb declares a 1 KB
Content-Length, passes every check, and then expands to gigabytes of resident
memory inside `decompress`. The wire-side cap bounds how long we are willing to
stay on a socket; the decoded-side cap bounds what we are willing to hold.

The opener is assembled by hand instead of by `urllib.request.build_opener`,
which silently installs `file://`, `ftp://` and `data:` handlers. This client
fetches URLs discovered in untrusted HTML, so an opener that can read the local
disk turns one `<a href="file:///etc/passwd">` into an exfiltration primitive.
Requests are restricted to http/https at the call site *and* by the handler set,
because a redirect can change the scheme after the call site has had its say.

The client is proxy-aware by default: urllib reads HTTPS_PROXY/HTTP_PROXY and
NO_PROXY from the environment, which is how this runs inside an egress-filtered
container without any special casing.
"""

from __future__ import annotations

import email.utils
import io
import json
import random
import ssl
import string
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

#: Only these ever reach the network. `file:`, `data:` and `ftp:` are not
#: transports we want reachable from a link in a stranger's page.
ALLOWED_SCHEMES = frozenset({"http", "https"})

#: Error bodies are read for the exception message and nothing else, so they get
#: a much smaller budget than a real response.
MAX_ERROR_BYTES = 64 * 1024

#: ETags are kept per request URL. A crawl of a large site would otherwise grow
#: this dictionary for its whole run, so the oldest entries are dropped once it
#: is full: a missed conditional request costs one re-fetch, a leak costs the job.
MAX_ETAGS = 10_000

#: Ceiling on a server-supplied Retry-After. A misconfigured origin that asks us
#: to come back in a year must not park a worker for a year.
MAX_RETRY_AFTER_S = 3600.0

_DEFAULT_PORTS = {"http": 80, "https": 443}


class HttpError(Exception):
    def __init__(self, status: int, url: str, body: str = "",
                 headers: dict[str, str] | None = None):
        super().__init__(f"HTTP {status} for {url}: {body[:300]}")
        self.status = status
        self.url = url
        self.body = body
        self.headers = headers or {}

    @property
    def retryable(self) -> bool:
        # 429 and 5xx are worth retrying; 408 is a server-side timeout.
        return self.status in (408, 425, 429) or 500 <= self.status < 600


class TransportError(Exception):
    """Network-level failure (DNS, TLS, connection reset, timeout, oversize)."""


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

    @property
    def not_modified(self) -> bool:
        """True only for a served-from-cache 304, never for an empty 200."""
        return self.status == 304 and self.from_cache


@dataclass(slots=True)
class RetryPolicy:
    attempts: int = 4
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: float = 0.25

    def delay_for(self, attempt: int, retry_after: float | None = None) -> float:
        if retry_after is not None:
            return max(0.0, min(retry_after, self.max_delay))
        raw = min(self.base_delay * (2 ** (max(attempt, 1) - 1)), self.max_delay)
        # A jitter factor above 1.0 would otherwise produce a negative delay,
        # and `time.sleep` raises on those instead of returning immediately.
        return max(0.0, raw * (1.0 + random.uniform(-self.jitter, self.jitter)))


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
    max_etags: int = MAX_ETAGS
    _bucket: TokenBucket = field(init=False, repr=False)
    _etags: dict[str, str] = field(default_factory=dict, repr=False)
    _opener: Any = field(default=None, init=False, repr=False)
    #: "requests" counts exchanges *attempted*, so retries are included in it and
    #: `requests - retries` is the number of calls that got through first try.
    #: "errors" counts calls that ended in a raise, at most one per call.
    stats: dict[str, int] = field(default_factory=lambda: {
        "requests": 0, "retries": 0, "errors": 0, "not_modified": 0, "bytes": 0
    })

    def __post_init__(self) -> None:
        self._bucket = TokenBucket(self.rate_per_sec, self.burst)
        ctx = ssl.create_default_context()
        if not self.verify_tls:  # never used by default; here for local mitm debugging only
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        # Hand-rolled instead of build_opener(): see the module docstring. The
        # order matters only in that every handler urllib needs for http(s) is
        # present and nothing else is.
        opener = urllib.request.OpenerDirector()
        for handler in (
            urllib.request.ProxyHandler(),      # reads *_PROXY / NO_PROXY from env
            urllib.request.UnknownHandler(),
            urllib.request.HTTPHandler(),
            urllib.request.HTTPSHandler(context=ctx),
            urllib.request.HTTPDefaultErrorHandler(),
            _SafeRedirectHandler(),
            urllib.request.HTTPErrorProcessor(),
        ):
            opener.add_handler(handler)
        self._opener = opener

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
        try:
            return self._send(
                method, url, headers=headers, body=body,
                conditional=conditional, allow_status=allow_status,
            )
        except (HttpError, TransportError):
            # Counted in one place so every raise site agrees on what an error is:
            # one failed call, one increment, whatever it took to fail.
            self.stats["errors"] += 1
            raise

    def _send(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None,
        body: bytes | None,
        conditional: bool,
        allow_status: tuple[int, ...],
    ) -> Response:
        safe_url = redact_url(url)
        try:
            scheme = urllib.parse.urlsplit(url).scheme.lower()
        except ValueError as e:
            raise TransportError(f"unparseable URL: {safe_url} ({e})") from e
        if scheme not in ALLOWED_SCHEMES:
            raise TransportError(f"refusing scheme {scheme or '<none>'!r}: {safe_url}")

        hdrs = {
            "User-Agent": self.user_agent,
            "Accept-Encoding": "gzip, deflate",
            **self.default_headers,
            **(headers or {}),
        }
        if conditional and url in self._etags:
            hdrs["If-None-Match"] = self._etags[url]

        # A policy with no attempts would fall out of the loop with nothing to
        # raise; one attempt is the floor, since "do not try at all" is not a
        # retry policy, it is a bug in the caller's config.
        attempts = max(1, self.retry.attempts)
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            self._bucket.acquire()
            self.stats["requests"] += 1
            started = time.monotonic()
            req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
            try:
                with self._opener.open(req, timeout=self.timeout) as raw:
                    # HEAD carries the Content-Length of the body it is *not*
                    # sending; refusing it would break the one request whose
                    # entire job is to ask how big something is.
                    payload = self._read_capped(raw, check_declared=method.upper() != "HEAD")
                    resp_headers = {k.lower(): v for k, v in raw.headers.items()}
                    resp = Response(
                        url=raw.geturl(),
                        status=raw.status,
                        headers=resp_headers,
                        body=_decompress(payload, resp_headers.get("content-encoding", ""),
                                         self.max_bytes),
                        elapsed_s=time.monotonic() - started,
                    )
                self.stats["bytes"] += len(resp.body)
                if etag := resp.headers.get("etag"):
                    self._remember_etag(url, etag)
                return resp
            except urllib.error.HTTPError as e:
                resp_headers = {k.lower(): v for k, v in (e.headers or {}).items()}
                if e.code == 304:
                    _close(e)
                    self.stats["not_modified"] += 1
                    return Response(url, 304, resp_headers, b"", from_cache=True,
                                    elapsed_s=time.monotonic() - started)
                if e.code in allow_status:
                    payload = self._read_error(e)
                    body_out = _decompress_lenient(
                        payload, resp_headers.get("content-encoding", ""), self.max_bytes
                    )
                    self.stats["bytes"] += len(body_out)
                    return Response(url, e.code, resp_headers, body_out,
                                    elapsed_s=time.monotonic() - started)
                err = HttpError(e.code, safe_url,
                                self._read_error(e).decode("utf-8", "replace"), resp_headers)
                last_exc = err
                if not err.retryable or attempt == attempts:
                    raise err from e
                wait = self.retry.delay_for(attempt, _retry_after(resp_headers))
                self.stats["retries"] += 1
                log.warn("retrying", url=safe_url, status=e.code, attempt=attempt,
                         wait=round(wait, 2))
                time.sleep(wait)
            except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as e:
                last_exc = TransportError(f"{type(e).__name__}: {e} ({safe_url})")
                if attempt == attempts:
                    raise last_exc from e
                wait = self.retry.delay_for(attempt)
                self.stats["retries"] += 1
                log.warn("transport retry", url=safe_url, err=str(e)[:120], attempt=attempt,
                         wait=round(wait, 2))
                time.sleep(wait)
        # Unreachable: the final attempt of both branches returns or raises. Kept
        # so a future edit to the loop cannot turn a failure into a silent None.
        raise last_exc or TransportError(f"request failed: {safe_url}")

    def get(self, url: str, **kw: Any) -> Response:
        return self.request("GET", url, **kw)

    def get_json(self, url: str, **kw: Any) -> Any:
        headers = {"Accept": "application/json", **(kw.pop("headers", None) or {})}
        return self.get(url, headers=headers, **kw).json()

    def head(self, url: str, **kw: Any) -> Response:
        return self.request("HEAD", url, **kw)

    # ----------------------------------------------------------------- helpers

    def _remember_etag(self, url: str, etag: str) -> None:
        if url not in self._etags and len(self._etags) >= max(1, self.max_etags):
            # dicts iterate in insertion order, so this is the oldest entry.
            del self._etags[next(iter(self._etags))]
        self._etags[url] = etag

    def _read_capped(self, raw: Any, *, check_declared: bool = True) -> bytes:
        """Read at most max_bytes, so one pathological URL cannot exhaust memory."""
        if check_declared:
            declared = _int_or_none(raw.headers.get("content-length"))
            if declared is not None and declared > self.max_bytes:
                raise TransportError(
                    f"response too large: {declared} bytes > cap {self.max_bytes}"
                )
        buf = io.BytesIO()
        while True:
            chunk = raw.read(65536)
            if not chunk:
                break
            buf.write(chunk)
            # A declared length is a claim; this is the measurement.
            if buf.tell() > self.max_bytes:
                raise TransportError(f"response exceeded cap of {self.max_bytes} bytes")
        return buf.getvalue()

    def _read_error(self, e: Any) -> bytes:
        """Read a bounded prefix of an error body and close the connection.

        Error bodies are never handed to the pipeline as documents, so this
        truncates rather than raising: failing to read an error page must not
        replace the status code the caller actually needs to see.
        """
        limit = min(self.max_bytes, MAX_ERROR_BYTES)
        try:
            return e.read(limit + 1)[: limit]
        except Exception:
            return b""
        finally:
            _close(e)


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Follow redirects for safe methods only, and never carry credentials off-host.

    Three separate hazards, one handler. Replaying a POST against a URL the
    server chose is a write we never agreed to make. A redirect to `file:` or
    `data:` escapes the transport allowlist that `_send` enforced on the URL we
    were given. And urllib's own `redirect_request` copies every request header
    onto the new request, which quietly hands the Authorization header for
    api.github.com to whatever host a redirect names.

    Returning None means "not a redirect I will follow": urllib then falls
    through to HTTPDefaultErrorHandler and the 3xx surfaces as an HTTPError,
    which is what the caller should see. The inherited `http_error_30x` methods
    still enforce urllib's own chain limits (max_repeats, max_redirections), so
    a redirect loop terminates rather than spinning.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        if req.get_method() not in ("GET", "HEAD"):
            return None
        try:
            target = urllib.parse.urlsplit(newurl)
        except ValueError:
            return None
        if target.scheme.lower() not in ALLOWED_SCHEMES:
            return None
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is None:
            return None
        if _host_of(req.full_url) != _host_of(newurl):
            for name in list(new.headers):
                if name.lower() in ("authorization", "cookie", "proxy-authorization"):
                    del new.headers[name]
        return new


def _close(fp: Any) -> None:
    """Close a response we are done with; sockets are not free to leak."""
    try:
        fp.close()
    except Exception:
        pass


def _int_or_none(value: str | None) -> int | None:
    # `str.isdigit()` is True for "²", which int() then refuses - hence try/except
    # rather than a guard, so a hostile Content-Length degrades instead of raising.
    if value is None:
        return None
    try:
        return int(value.strip())
    except (TypeError, ValueError):
        return None


def _coding(encoding: str) -> str:
    """The content coding actually applied, from a possibly multi-valued header."""
    codings = [c.strip().lower() for c in encoding.split(",") if c.strip()]
    codings = [c for c in codings if c != "identity"]
    if not codings:
        return ""
    last = codings[-1]
    return "gzip" if last == "x-gzip" else ("deflate" if last == "x-deflate" else last)


def _inflate(payload: bytes, wbits: int, max_bytes: int) -> bytes:
    """Bounded inflate. Raises TransportError if the decoded body busts the cap."""
    obj = zlib.decompressobj(wbits)
    out = obj.decompress(payload, max_bytes + 1)
    if len(out) > max_bytes or obj.unconsumed_tail:
        raise TransportError(f"decompressed response exceeded cap of {max_bytes} bytes")
    return out


def _decompress(payload: bytes, encoding: str, max_bytes: int = MAX_BYTES) -> bytes:
    """Decode a content coding, refusing to expand past `max_bytes`.

    A body that fails to decode is returned as-is: servers mislabel identity
    responses as gzip often enough that treating it as fatal would cost us real
    pages. A body that decodes to more than the cap is a different thing - the
    bytes exist and we refuse to hold them - so that one raises.
    """
    enc = _coding(encoding)
    if enc not in ("gzip", "deflate"):
        return payload
    try:
        if enc == "gzip":
            # zlib with wbits=47 rather than gzip.decompress: the gzip module
            # raises EOFError on a truncated stream, and half a page is worth
            # more to this pipeline than an exception on a nightly run.
            return _inflate(payload, 16 + zlib.MAX_WBITS, max_bytes)
        try:
            return _inflate(payload, zlib.MAX_WBITS, max_bytes)
        except zlib.error:
            # "deflate" means zlib-wrapped in the RFC and raw in the wild.
            return _inflate(payload, -zlib.MAX_WBITS, max_bytes)
    except (OSError, EOFError, zlib.error):
        return payload  # server lied about the encoding; take the bytes as-is


def _decompress_lenient(payload: bytes, encoding: str, max_bytes: int) -> bytes:
    """As `_decompress`, but an oversize error body is dropped, not raised.

    Used only for allowed non-2xx responses, where the status is the payload the
    caller cares about and a bomb in the error page must not mask it.
    """
    try:
        return _decompress(payload, encoding, max_bytes)
    except TransportError:
        log.warn("oversize error body discarded", bytes=len(payload))
        return b""


def _retry_after(headers: dict[str, str]) -> float | None:
    """Honour Retry-After, and GitHub's x-ratelimit-reset when the quota is spent.

    RFC 9110 allows both delta-seconds and an HTTP-date; real servers send both,
    and a date already in the past means "now", not "negative seconds ago".
    """
    if ra := headers.get("retry-after"):
        ra = ra.strip()
        seconds = _int_or_none(ra)
        if seconds is None and (parsed := email.utils.parsedate_tz(ra)) is not None:
            seconds = int(email.utils.mktime_tz(parsed) - time.time())
        if seconds is not None:
            return _sane_delay(seconds)
    if headers.get("x-ratelimit-remaining") == "0" and (reset := headers.get("x-ratelimit-reset")):
        try:
            return _sane_delay(float(reset) - time.time() + 1.0)
        except (TypeError, ValueError):
            return None
    return None


def _sane_delay(seconds: float) -> float:
    return max(0.0, min(float(seconds), MAX_RETRY_AFTER_S))


def redact_url(url: str) -> str:
    """Drop userinfo before a URL reaches a log line or an exception message.

    `https://user:token@host/path` is a credential, and exception strings end up
    in journals, reports and issue bodies that get copied around.
    """
    try:
        parts = urllib.parse.urlsplit(url)
        if not parts.netloc or "@" not in parts.netloc:
            return url
        host = parts.netloc.rsplit("@", 1)[1]
        return urllib.parse.urlunsplit(
            (parts.scheme, f"<redacted>@{host}", parts.path, parts.query, parts.fragment)
        )
    except ValueError:
        return url


def urljoin(base: str, link: str) -> str:
    """Absolutize `link` against `base`, degrading to "" on a malformed pair.

    `urllib.parse.urljoin` raises ValueError on inputs like `http://[::1` - and
    the links this is fed come out of other people's HTML.
    """
    try:
        return urllib.parse.urljoin(base, link)
    except ValueError:
        return ""


# Percent-escapes of these are redundant per RFC 3986 6.2.2.2 and are decoded;
# everything else keeps its escape, only normalized to uppercase hex.
_UNRESERVED = frozenset(string.ascii_letters + string.digits + "-._~")
_HEXDIGITS = frozenset(string.hexdigits)
_PATH_SAFE = "/:@&=+$,;~*'()!-._"


def _normalize_path(path: str) -> str:
    """Canonicalize percent-encoding without changing what the path *means*.

    Decoding blindly and re-quoting - `quote(unquote(path))` - turns `/a%2Fb`
    into `/a/b`, which is a different resource on the origin and a different
    scope for the crawler. Escaped delimiters stay escaped here; only escapes
    that carry no meaning are folded away.
    """
    out: list[str] = []
    i, n = 0, len(path)
    while i < n:
        ch = path[i]
        esc = path[i + 1 : i + 3]
        if ch == "%" and len(esc) == 2 and esc[0] in _HEXDIGITS and esc[1] in _HEXDIGITS:
            decoded = chr(int(esc, 16))
            out.append(decoded if decoded in _UNRESERVED else f"%{esc.upper()}")
            i += 3
        else:
            out.append(urllib.parse.quote(ch, safe=_PATH_SAFE))
            i += 1
    return "".join(out)


def canonical_host(host: str) -> str:
    """Lowercased, punycoded, trailing-dot-free host, or "" if there isn't one.

    `example.com.` and `example.com` are the same host to DNS, and `Bücher.de`
    and `xn--bcher-kva.de` are the same host to everything. Two spellings of one
    host means one page crawled twice, or a same-site check that says no to a
    URL that is in fact on-site.
    """
    h = host.strip().rstrip(".").lower()
    if not h or ":" in h:  # empty, or an IPv6 literal that IDNA must not touch
        return h
    try:
        return h.encode("idna").decode("ascii")
    except (UnicodeError, ValueError):
        return h  # over-long label, empty label, or an underscore: leave it alone


def _host_of(url: str) -> str:
    try:
        return canonical_host(urllib.parse.urlsplit(url).hostname or "")
    except ValueError:
        return ""


def normalize_url(url: str, *, drop_fragment: bool = True, drop_query: bool = False) -> str:
    """Canonical form used for crawl dedupe.

    Lowercases scheme/host, punycodes IDNs, drops userinfo, the default port and
    the fragment, sorts query parameters, and strips common tracking params so
    `?utm_source=...` does not make a page look new.

    A URL this cannot parse is handed back unchanged rather than guessed at: the
    frontier's scheme check will drop it, whereas inventing a host would invent
    a fetch.
    """
    raw = url.strip()
    try:
        parts = urllib.parse.urlsplit(raw)
        port = parts.port  # property: raises on a non-numeric or out-of-range port
        host = canonical_host(parts.hostname or "")
    except ValueError:
        return raw
    if not host:
        return raw
    scheme = parts.scheme.lower() or "https"
    netloc = f"[{host}]" if ":" in host else host
    if port and port != _DEFAULT_PORTS.get(scheme):
        netloc = f"{netloc}:{port}"
    path = _normalize_path(parts.path)
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
    """Whether two URLs are in the same crawl scope. Fails closed.

    This gates the frontier, so "I could not parse it" has to mean "out of
    scope": a parse failure that returned True would let a malformed link walk
    the crawler off the site it was pointed at.
    """
    ha, hb = _host_of(a), _host_of(b)
    if not ha or not hb:
        return False
    if ha == hb:
        return True
    if not include_subdomains:
        return False
    return ha.endswith("." + hb) or hb.endswith("." + ha)
