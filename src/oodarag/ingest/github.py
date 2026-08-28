"""GitHub connector - the "repository builder".

Turns a repository into retrievable documents across five resource families:
code/docs files, the README, issues, pull requests, and releases. Each becomes
a `RawDocument` with enough metadata that the retriever can filter by path,
language, state or age, and enough provenance that every citation resolves to a
permalink pinned at a commit sha (not a branch, which moves under you).

Cost control is the whole game here. A large repository is tens of thousands of
API calls if you fetch naively, and the REST quota is 5,000/hour on a personal
token. Three things keep it cheap:

1. **Head-sha short circuit.** One call to compare the default branch head with
   the stored cursor. Unchanged? The entire file walk is skipped.
2. **One tree call, not N.** `git/trees?recursive=1` returns every path and blob
   sha in a single request; blob shas tell us which files changed without
   fetching any content.
3. **Raw over API for blobs.** `raw.githubusercontent.com` serves file bytes
   without consuming REST quota, with the API blob endpoint as fallback.

Three failure modes shape the rest of the module, and each one is a rule.

**The token is not a header on a shared client.** It is held here, marked
un-`repr`-able, and attached per request only to the hosts this client was
configured to talk to. Writing it into `HttpClient.default_headers` - the
obvious implementation - sends it to whatever host a `Link` header names next,
prints it in the `repr` of every dataclass that transitively holds the client,
and, when the caller passes a client it also uses for crawling strangers' HTML,
attaches a GitHub credential to every request that crawler ever makes. The
pagination walk therefore also refuses to follow a `next` link off the origin
it started on: an API that can redirect us anywhere is an API that can ask for
our token.

**A 403 is two different failures wearing one number.** GitHub reports its
primary quota as `403` with `x-ratelimit-remaining: 0` and its secondary
("abuse") limit as `403`/`429` with `Retry-After`; a missing scope or an
unauthorized SAML session is also `403`. Retrying the first is correct and
retrying the second is a slower way to fail, so they are told apart by their
headers before anything sleeps, and each raises a distinct error whose message
says which one happened. `404` gets the same treatment: GitHub answers `404`
rather than `403` for private objects, so the error says so instead of letting
an operator conclude the repository was deleted.

**A cursor that advances past work we did not do is silent data loss.** The head
sha is written back only when the file walk actually reached the end of the
tree: not when it was truncated by GitHub, not when it hit `max_files`, not when
the run died halfway. Otherwise the next run compares an unchanged head, skips
the walk entirely, and the files we never fetched are never fetched again. For
the same reason a blob sha is remembered only once its bytes are in hand - a
transient fetch failure that recorded the sha would mark that file "unchanged"
forever.
"""

from __future__ import annotations

import base64
import os
import re
import time
import urllib.parse
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.http import HttpClient, HttpError, Response, TransportError, urljoin
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets

log = get_logger("ingest.github")

API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"
API_VERSION = "2022-11-28"
JSON_ACCEPT = "application/vnd.github+json"
RAW_ACCEPT = "application/vnd.github.raw"

#: How many times a single request will wait out a rate limit before giving up.
#: Waiting forever turns a quota problem into a hung nightly job.
MAX_RATE_LIMIT_WAITS = 3

#: Longest one wait may be. GitHub's primary window is an hour, so a reset that
#: claims to be further away than this is a clock skew or a lying proxy.
MAX_RATE_LIMIT_SLEEP_S = 900.0

#: Wait for a secondary limit that names no reset time at all.
SECONDARY_LIMIT_SLEEP_S = 60.0

#: Pages one `paginate` call will walk. `max_items` already bounds the items,
#: but a server that answers every page with an empty list and a `next` link
#: bounds nothing, and that loop has to end on its own.
MAX_PAGES = 200

#: Bytes sniffed for a NUL before deciding a blob is binary. Enough to catch
#: every real binary format's header without holding the whole file to decide.
BINARY_SNIFF_BYTES = 8192

#: Longest path we will build a URL from. Real repositories do not come close.
MAX_PATH_LEN = 1024

#: Tree entry modes we refuse. A symlink is a `blob` whose content is the *path
#: it points at*, so ingesting one indexes a pointer as if it were a file - and
#: hands a repository a way to name paths outside itself. `160000` is a
#: submodule pointer, whose bytes live in another repository entirely.
SKIP_MODES = frozenset({"120000", "160000"})

# Extensions worth indexing as text. Everything else is either binary or noise.
TEXT_EXTENSIONS = frozenset("""
    .md .markdown .mdx .rst .txt .adoc .org
    .py .js .jsx .ts .tsx .mjs .cjs .go .rs .java .kt .kts .scala .rb .php .cs .swift
    .c .h .cc .cpp .hpp .hh .m .mm .sh .bash .zsh .fish .ps1 .sql .r .jl .lua .pl .ex .exs
    .html .css .scss .less .vue .svelte
    .json .yaml .yml .toml .ini .cfg .conf .properties .gradle .tf .tfvars
    .proto .graphql .gql .ipynb .dockerfile .mk .cmake .bzl
""".split())

#: Whole filenames that are text but whose extension says nothing useful.
#: Matched against the lowercased basename, which is why `.env.example` lives
#: here and not in TEXT_EXTENSIONS: the extension of `.env.example` is
#: `.example`, so listing it as an extension could never match anything.
TEXT_FILENAMES = frozenset({
    "dockerfile", "makefile", "license", "notice", "codeowners", "readme",
    "changelog", "contributing", ".env.example",
})

# Files that are technically text but carry no retrievable meaning.
SKIP_PATH_RE = re.compile(
    r"(^|/)(\.git|node_modules|vendor|third_party|dist|build|out|target|\.venv|venv|"
    r"__pycache__|\.mypy_cache|\.pytest_cache|\.next|\.nuxt|coverage|htmlcov)(/|$)"
    r"|(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|"
    r"go\.sum|composer\.lock|Gemfile\.lock|uv\.lock|\.min\.(js|css))$"
    r"|\.(min|bundle|generated|pb|_pb2)\.",
    re.I,
)

LANGUAGE_BY_EXT = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin",
    ".rb": "ruby", ".php": "php", ".cs": "csharp", ".swift": "swift", ".c": "c",
    ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp", ".sh": "bash", ".bash": "bash",
    ".sql": "sql", ".md": "markdown", ".rst": "rst", ".html": "html", ".css": "css",
    ".yaml": "yaml", ".yml": "yaml", ".json": "json", ".toml": "toml", ".tf": "terraform",
    ".proto": "protobuf", ".ipynb": "jupyter", ".lua": "lua", ".r": "r", ".jl": "julia",
}

#: GitHub's own rule for owner and repository names. Enforced because both are
#: interpolated straight into an API path: `owner="..%2f.."` is a request for a
#: different endpoint than the one this code appears to call.
_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

#: A subset of `git check-ref-format`, plus the characters that would change the
#: shape of the URL a ref is pasted into.
_REF_BAD_RE = re.compile(r"\.\.|@\{|//|[\s~^:?*\[\]\\#%&\x00-\x1f\x7f]|^[-/]|/$")

_SHA_RE = re.compile(r"^[0-9a-f]{7,64}$")

_TEST_PATH_RE = re.compile(r"(^|/)(tests?|spec)/|_test\.|test_|\.spec\.", re.I)

#: One `<uri>` plus the parameters that follow it, up to the next link. Written
#: this way rather than by splitting the header on commas because a URI is
#: allowed to contain one and a `next` link that loses its query string is a
#: pagination walk that restarts from page one.
_LINK_RE = re.compile(r"<([^>]*)>([^<]*)")


# ------------------------------------------------------------------- exceptions


class GitHubError(Exception):
    """A GitHub API failure this connector has classified.

    Classified is the point: the callers below decide whether to swallow a
    failure by *type*, and "the file is not there" and "the quota is gone" call
    for opposite reactions.
    """

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class AuthError(GitHubError):
    """401 - the credential itself was rejected."""


class AccessDeniedError(GitHubError):
    """403 that is *not* a rate limit: scope, SSO or repository policy."""


class NotFoundError(GitHubError):
    """404 - absent, or present and invisible to this credential."""


class RateLimitError(GitHubError):
    """Primary or secondary rate limit that outlasted our willingness to wait."""


# ---------------------------------------------------------------------- helpers


def _host_of(url: str) -> str:
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower()
    except ValueError:
        return ""


def _as_int(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _bump(counter: dict[str, int], key: str) -> None:
    counter[key] = counter.get(key, 0) + 1


def _next_link(link_header: str) -> str | None:
    """The `rel="next"` target of an RFC 8288 Link header, or None.

    Written against what servers send rather than what the RFC suggests: `rel`
    may sit in any parameter position (not just the first), may be unquoted or
    single-quoted, and may carry several space-separated values. Getting any of
    those wrong does not raise - it silently ends pagination at page one, which
    is why this is a function with its own tests rather than an inline `in`.
    """
    for match in _LINK_RE.finditer(link_header):
        uri = match.group(1).strip()
        if not uri:
            continue
        # Everything up to the comma that ends this link belongs to this URI;
        # what follows is the next link's parameters, and mistaking one for the
        # other is how `rel="next", <...>; rel="last"` reads as no next at all.
        for param in match.group(2).split(",")[0].split(";"):
            name, sep, value = param.partition("=")
            if not sep or name.strip().lower() != "rel":
                continue
            if "next" in value.strip().strip("\"'").lower().split():
                return uri
    return None


def _valid_ref(ref: str) -> bool:
    """Whether a ref is safe to paste into an API path.

    `..` is the interesting one: `/repos/o/r/commits/../../../user` is a
    different endpoint, and the ref can come from a CLI flag.
    """
    return bool(ref) and not _REF_BAD_RE.search(ref) and not ref.endswith(".lock")


def _safe_repo_path(path: str) -> bool:
    """Whether a path from the tree API may be used to build a URL.

    The tree comes back from a server, and this connector's whole job is to
    interpolate what that server says into other URLs. A path is only ever a
    relative, forward-slashed, non-empty sequence of real segments; anything
    that could climb out of the repository (`..`), reroot (`/x`, `C:\\x`) or
    change what a shell or a filesystem sees (`\\`, NUL, newline) is dropped
    rather than sanitized, because a sanitized path is a different file.
    """
    if not path or len(path) > MAX_PATH_LEN:
        return False
    if any(ch in path for ch in ("\x00", "\\", "\n", "\r")):
        return False
    if path.startswith(("/", "~", ".git/")) or re.match(r"^[A-Za-z]:", path):
        return False
    return all(seg not in ("", ".", "..") for seg in path.split("/"))


def _compile_patterns(patterns: tuple[str, ...], label: str) -> tuple[re.Pattern[str], ...]:
    """Compile path filters once, dropping the ones that are not regexes.

    A typo in a `--exclude` flag is a bad filter, not a reason for the nightly
    run to end with a traceback and no documents.
    """
    compiled: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled.append(re.compile(pattern, re.I))
        except re.error as e:
            log.warn("ignoring unusable path filter", kind=label, pattern=pattern, err=str(e))
    return tuple(compiled)


# ----------------------------------------------------------------------- client


@dataclass(repr=False)
class GitHubClient:
    """Thin REST wrapper: auth, pagination, quota awareness.

    The token is held here and nowhere else. In particular it is never written
    into `HttpClient.default_headers`, which would (a) put it in the `repr` of
    the client and of everything holding one, (b) send it to every host that
    client is ever pointed at, including one named by a `Link` header, and (c)
    permanently modify a client the caller may have handed us for other work.
    """

    #: `repr=False` twice over: the dataclass `repr` is off entirely below, and
    #: the field is marked so that turning it back on cannot leak the token.
    token: str | None = field(default=None, repr=False)
    client: HttpClient | None = None
    api_root: str = API_ROOT
    raw_root: str = RAW_ROOT
    max_rate_limit_waits: int = MAX_RATE_LIMIT_WAITS
    max_rate_limit_sleep_s: float = MAX_RATE_LIMIT_SLEEP_S
    _auth_hosts: frozenset[str] = field(default_factory=frozenset, init=False, repr=False)

    def __post_init__(self) -> None:
        self.token = (
            self.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or None
        )
        if self.client is None:
            # 10 rps is well inside GitHub's guidance and leaves headroom for
            # concurrent tooling using the same token.
            self.client = HttpClient(rate_per_sec=10.0, burst=15)
        # Exactly the two hosts this client was configured for. Anything else -
        # a redirect target, a `Link` header, a raw host belonging to a
        # different deployment - gets the request without the credential.
        self._auth_hosts = frozenset(
            host for host in (_host_of(self.api_root), _host_of(self.raw_root)) if host
        )

    def __repr__(self) -> str:
        return f"GitHubClient(api_root={self.api_root!r}, authenticated={self.authenticated})"

    @property
    def authenticated(self) -> bool:
        return bool(self.token)

    @property
    def http(self) -> HttpClient:
        if self.client is None:  # pragma: no cover - __post_init__ always sets one
            self.client = HttpClient(rate_per_sec=10.0, burst=15)
        return self.client

    # -- request -------------------------------------------------------------

    def _headers_for(self, url: str, accept: str) -> dict[str, str]:
        headers = {"Accept": accept, "X-GitHub-Api-Version": API_VERSION}
        if self.token and _host_of(url) in self._auth_hosts:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _url(self, path: str, params: Mapping[str, Any] | None = None) -> str:
        url = path if path.startswith(("http://", "https://")) else f"{self.api_root}{path}"
        query = {k: v for k, v in (params or {}).items() if v is not None}
        if query:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{urllib.parse.urlencode(query)}"
        return url

    def request(self, url: str, *, accept: str = JSON_ACCEPT,
                allow_status: tuple[int, ...] = ()) -> Response:
        """One exchange, with GitHub's 403-shaped rate limits waited out."""
        waits = 0
        while True:
            try:
                return self.http.get(
                    url, headers=self._headers_for(url, accept), allow_status=allow_status
                )
            except HttpError as e:
                delay = self._rate_limit_delay(e)
                if delay is None:
                    raise self._classify(e) from e
                if waits >= max(0, self.max_rate_limit_waits):
                    raise RateLimitError(
                        f"rate limited by GitHub at {e.url} and still limited after "
                        f"{waits} wait(s); giving up rather than holding the run open",
                        status=e.status,
                    ) from e
                waits += 1
                log.warn("rate limited, waiting for the reset", url=e.url, status=e.status,
                         wait_s=round(delay, 1), attempt=waits)
                time.sleep(delay)

    def _rate_limit_delay(self, e: HttpError) -> float | None:
        """Seconds to wait for `e` to clear, or None if `e` is not a rate limit.

        A 403 with no rate-limit signal at all is a permissions failure. Waiting
        on one is not conservative, it is an hour of sleeping before the same
        error, so the default answer here is None.
        """
        if e.status not in (403, 429):
            return None
        headers = e.headers or {}
        if (retry_after := _as_int(headers.get("retry-after"))) is not None:
            return self._bounded(retry_after)
        if (headers.get("x-ratelimit-remaining") or "").strip() == "0":
            reset = _as_float(headers.get("x-ratelimit-reset"))
            if reset is None:
                return self._bounded(SECONDARY_LIMIT_SLEEP_S)
            # +1s of slack: waking on the exact reset second races the origin.
            return self._bounded(reset - time.time() + 1.0)
        body = (e.body or "").lower()
        if e.status == 429 or "rate limit" in body or "abuse detection" in body:
            return self._bounded(SECONDARY_LIMIT_SLEEP_S)
        return None

    def _bounded(self, seconds: float) -> float:
        return max(0.0, min(float(seconds), max(0.0, self.max_rate_limit_sleep_s)))

    def _scrub(self, text: str) -> str:
        """Redact credential shapes, and then this credential specifically.

        `redact_secrets` matches shapes it knows, which is everything except the
        format that shipped last quarter - GitHub's fine-grained `github_pat_`
        tokens are not in its table today. The one credential we can identify
        with certainty is our own, so it is removed by value as well. A proxy
        that echoes an Authorization header back inside an error body is not a
        hypothetical, and this message ends up in logs, deltas and reports.
        """
        cleaned = redact_secrets(text)
        if self.token and self.token in cleaned:
            cleaned = cleaned.replace(self.token, "<redacted:github-token>")
        return cleaned

    def _classify(self, e: HttpError) -> GitHubError:
        """Turn a status into an error that says what an operator should do."""
        detail = " ".join(self._scrub(e.body or "")[:200].split())
        if e.status == 401:
            return AuthError(
                f"401 from {e.url}: the GitHub credential was rejected (invalid, expired or "
                f"revoked). {detail}".strip(),
                status=401,
            )
        if e.status == 403:
            remaining = (e.headers or {}).get("x-ratelimit-remaining", "?")
            return AccessDeniedError(
                f"403 from {e.url}: authenticated but not permitted - a missing token scope, a "
                f"SAML session that was never authorized, or repository policy. This is not a "
                f"rate limit (x-ratelimit-remaining={remaining}). {detail}".strip(),
                status=403,
            )
        if e.status == 404:
            hint = (
                "the configured token cannot see it"
                if self.authenticated
                else "it is private and no token is configured - GitHub answers 404, not 403, "
                     "for objects a caller is not allowed to know exist"
            )
            return NotFoundError(
                f"404 from {e.url}: the repository, ref or path does not exist, or {hint}. "
                f"{detail}".strip(),
                status=404,
            )
        return GitHubError(f"HTTP {e.status} from {e.url}: {detail}".strip(), status=e.status)

    # -- json ----------------------------------------------------------------

    def get(self, path: str, **params: Any) -> Any:
        return self._json(self.request(self._url(path, params)))

    def _json(self, resp: Response) -> Any:
        try:
            return resp.json()
        except ValueError as e:
            raise GitHubError(
                f"malformed JSON from {resp.url}: {type(e).__name__}", status=resp.status
            ) from e

    def paginate(self, path: str, *, per_page: int = 100, max_items: int = 1000,
                 **params: Any) -> Iterator[dict[str, Any]]:
        """Walk `Link: rel="next"` pagination, bounded three separate ways.

        By `max_items`, by `MAX_PAGES`, and by refusing to visit a URL twice - a
        `next` link that points back at a page we already read is a cycle, and
        one that yields no items would otherwise spin forever without ever
        tripping the item budget.
        """
        if max_items <= 0:
            return
        query = dict(params)
        query["per_page"] = max(1, min(per_page, 100, max_items))
        url: str | None = self._url(path, query)
        origin = _host_of(url or "")
        seen: set[str] = set()
        yielded = 0
        while url and yielded < max_items and len(seen) < MAX_PAGES:
            if url in seen:
                log.warn("pagination loop; stopping", repo_url=url, pages=len(seen))
                return
            seen.add(url)
            resp = self.request(url)
            try:
                payload = self._json(resp)
            except GitHubError as e:
                log.warn("unreadable page; stopping pagination", err=str(e)[:160])
                return
            items = payload if isinstance(payload, list) else []
            if isinstance(payload, dict):
                found = payload.get("items")
                items = found if isinstance(found, list) else []
            for item in items:
                if not isinstance(item, dict):
                    continue  # a page of nulls is a bad page, not a bad run
                yield item
                yielded += 1
                if yielded >= max_items:
                    return
            url = self._next_page(resp, url, origin)

    def _next_page(self, resp: Response, current: str, origin: str) -> str | None:
        """The next page URL, if it is one we are willing to send a token to."""
        raw = _next_link(resp.headers.get("link", "") or "")
        if not raw:
            return None
        nxt = urljoin(current, raw)
        if not nxt or urllib.parse.urlsplit(nxt).scheme not in ("http", "https"):
            return None
        if _host_of(nxt) != origin:
            log.warn("refusing an off-origin pagination link",
                     origin=origin, host=_host_of(nxt) or "<none>")
            return None
        return nxt

    def rate_limit(self) -> dict[str, Any]:
        try:
            core = self.get("/rate_limit")
            resources = core.get("resources", {}) if isinstance(core, dict) else {}
            return resources.get("core", {}) if isinstance(resources, dict) else {}
        except (GitHubError, TransportError) as e:
            return {"error": str(e)[:200]}


# -------------------------------------------------------------------- connector


@dataclass
class GitHubConnector(Connector):
    """Ingest one repository.

    `resources` selects what to pull. Defaults cover the material that actually
    answers questions about a codebase: the files and the README. Issues and PRs
    are opt-in because they are large and often noisier than they are useful.

    `enumerates_source` stays False (the base class default) and must: a run
    that short-circuits on an unchanged head, or stops at `max_files`, has seen
    a fraction of the repository, and the base class would otherwise read that
    fraction as the repository's whole inventory.
    """

    owner: str = ""
    repo: str = ""
    ref: str | None = None                       # defaults to the repo's default branch
    resources: tuple[str, ...] = ("repo", "readme", "files")
    include_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    max_file_bytes: int = 400_000
    max_files: int = 3000
    max_issues: int = 200
    max_commits: int = 200
    authority: float = 1.2                        # a repo is authoritative about itself
    gh: GitHubClient = field(default_factory=GitHubClient)
    stats: dict[str, Any] = field(default_factory=dict)
    _includes: tuple[re.Pattern[str], ...] = field(default=(), init=False, repr=False)
    _excludes: tuple[re.Pattern[str], ...] = field(default=(), init=False, repr=False)

    def __post_init__(self) -> None:
        if not _NAME_RE.match(self.owner or "") or not _NAME_RE.match(self.repo or ""):
            raise ValueError(
                f"GitHubConnector needs a plain owner and repo name, got "
                f"{self.owner!r}/{self.repo!r}"
            )
        if self.ref is not None and not _valid_ref(self.ref):
            raise ValueError(f"refusing unsafe ref {self.ref!r}")
        self.key = f"github:{self.owner}/{self.repo}"
        self._includes = _compile_patterns(self.include_paths, "include")
        self._excludes = _compile_patterns(self.exclude_paths, "exclude")

    # ------------------------------------------------------------------ helpers

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}"

    def _permalink(self, path: str, sha: str, line: int | None = None) -> str:
        anchor = f"#L{line}" if line else ""
        return f"https://github.com/{self.slug}/blob/{sha}/{urllib.parse.quote(path)}{anchor}"

    def _wanted_path(self, path: str, size: int) -> tuple[bool, str]:
        if SKIP_PATH_RE.search(path):
            return False, "skip_pattern"
        if size > self.max_file_bytes:
            return False, "too_large"
        lowered = path.lower()
        base = lowered.rsplit("/", 1)[-1]
        ext = "." + base.rsplit(".", 1)[-1] if "." in base else ""
        if ext not in TEXT_EXTENSIONS and base not in TEXT_FILENAMES:
            return False, "not_text"
        if self._excludes and any(p.search(path) for p in self._excludes):
            return False, "excluded"
        if self._includes and not any(p.search(path) for p in self._includes):
            return False, "not_included"
        return True, ""

    def _reject_bytes(self, data: bytes) -> str:
        """Why these bytes are not a document, or "" if they are.

        Both checks are properties of the content rather than of the fetch, so a
        caller may remember the blob sha and never ask for them again.
        """
        if len(data) > self.max_file_bytes:
            return "too_large"
        if b"\x00" in data[:BINARY_SNIFF_BYTES]:
            return "binary"
        return ""

    def _decode_b64(self, content: Any) -> tuple[bytes | None, str]:
        """Decode base64 API content, refusing oversize input *before* decoding.

        4 encoded characters carry 3 bytes, so the encoded length bounds the
        decoded one without allocating it. Line breaks inflate the estimate a
        little, which errs towards refusing a file just under the cap - the safe
        direction when the alternative is decoding an attacker-chosen size.
        """
        if not isinstance(content, str) or not content.strip():
            return None, "empty"
        if len(content) // 4 * 3 > self.max_file_bytes:
            return None, "too_large"
        try:
            data = base64.b64decode(content)
        except ValueError:  # binascii.Error is a ValueError
            return None, "failed"
        # `b64decode` discards characters outside its alphabet instead of
        # raising, so a body of pure junk decodes to nothing at all. Emitting
        # that as a document would put an empty file in the index and record its
        # sha as successfully read.
        return (data, "") if data else (None, "failed")

    def _fetch_blob(self, path: str, sha: str, ref: str) -> tuple[str | None, str]:
        """Raw first (free), API blob second (costs quota but always works).

        Returns `(text, reason)`. A None text with reason "failed" is transient
        and the caller must *not* remember the sha; every other reason is a
        property of the bytes and is safe to remember. A rate limit is neither -
        it is re-raised, because the next 3,000 files would hit it too.
        """
        raw_url = (
            f"{self.gh.raw_root}/{self.slug}/{urllib.parse.quote(ref, safe='')}/"
            f"{urllib.parse.quote(path)}"
        )
        try:
            resp = self.gh.request(raw_url, accept=RAW_ACCEPT, allow_status=(404,))
            if resp.status == 200:
                reason = self._reject_bytes(resp.body)
                return (None, reason) if reason else (resp.text, "")
        except RateLimitError:
            raise
        except (GitHubError, TransportError) as e:
            log.debug("raw fetch failed, falling back to the API", path=path, err=str(e)[:120])

        try:
            blob = self.gh.get(f"/repos/{self.slug}/git/blobs/{sha}")
        except RateLimitError:
            raise
        except (GitHubError, TransportError) as e:
            log.warn("blob fetch failed", path=path, err=str(e)[:160])
            return None, "failed"
        if not isinstance(blob, dict):
            return None, "failed"
        encoding = blob.get("encoding")
        content = blob.get("content")
        if encoding == "base64":
            data, reason = self._decode_b64(content)
            if data is None:
                return None, reason
            reason = self._reject_bytes(data)
            return (None, reason) if reason else (data.decode("utf-8", "replace"), "")
        if encoding in ("utf-8", "utf8", "text", None) and isinstance(content, str) and content:
            reason = self._reject_bytes(content.encode("utf-8", "replace"))
            return (None, reason) if reason else (content, "")
        # `"encoding": "none"` is GitHub's answer for a blob too big to inline.
        return None, "unsupported_encoding"

    # -------------------------------------------------------------------- fetch

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        cursor = cursor if isinstance(cursor, dict) else {}
        counts: dict[str, int] = {}
        skipped: dict[str, int] = {}
        # Reset first: a run that dies on the very first call must not leave the
        # previous run's head sha in `stats` for `next_cursor` to write back.
        self.stats = {}

        meta = self.gh.get(f"/repos/{self.slug}")
        if not isinstance(meta, dict):
            raise GitHubError(f"{self.slug}: repository metadata was not an object")
        ref = self.ref or meta.get("default_branch") or "main"
        if not isinstance(ref, str) or not _valid_ref(ref):
            raise GitHubError(f"{self.slug}: refusing unusable ref {ref!r}")
        head_sha = self._resolve_head(ref)
        self.stats = {
            "ref": ref,
            "head_sha": head_sha,
            "default_branch": meta.get("default_branch"),
            "files_complete": False,
        }

        if "repo" in self.resources:
            yield self._repo_document(meta, ref, head_sha)
            counts["repo"] = 1

        if "readme" in self.resources:
            if (doc := self._readme_document(head_sha)) is not None:
                yield doc
                counts["readme"] = 1

        if "files" in self.resources:
            prior = cursor.get("blob_shas")
            prior_blobs: dict[str, str] = prior if isinstance(prior, dict) else {}
            if cursor.get("head_sha") == head_sha and prior_blobs:
                # Nothing moved since last run; the base class would report every
                # file "unchanged" anyway, so skip the fetch entirely.
                log.info("head unchanged, skipping file walk", repo=self.slug, sha=head_sha[:8])
                skipped["head_unchanged"] = len(prior_blobs)
                self.stats["blob_shas"] = dict(prior_blobs)
                self.stats["files_complete"] = True
            else:
                yield from self._walk_files(
                    head_sha, ref, prior_blobs, bool(cursor.get("force_refetch")), counts, skipped
                )

        if "issues" in self.resources or "pulls" in self.resources:
            want_pulls = "pulls" in self.resources
            want_issues = "issues" in self.resources
            n = 0
            since = cursor.get("issues_since")
            # Stamped before the walk, not after: an issue updated while we page
            # through would otherwise fall in the gap between the two times and
            # never be seen again.
            walked_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for issue in self.gh.paginate(
                f"/repos/{self.slug}/issues", state="all", since=since,
                sort="updated", direction="desc", max_items=self.max_issues,
            ):
                is_pr = "pull_request" in issue
                if (is_pr and not want_pulls) or (not is_pr and not want_issues):
                    continue
                yield self._issue_document(issue)
                n += 1
            counts["issues_and_pulls"] = n
            self.stats["issues_since"] = walked_at

        if "commits" in self.resources:
            n = 0
            for commit in self.gh.paginate(
                f"/repos/{self.slug}/commits", sha=ref, max_items=self.max_commits,
            ):
                yield self._commit_document(commit)
                n += 1
            counts["commits"] = n

        if "releases" in self.resources:
            n = 0
            for release in self.gh.paginate(f"/repos/{self.slug}/releases", max_items=100):
                if doc := self._release_document(release):
                    yield doc
                    n += 1
            counts["releases"] = n

        self.stats["counts"] = counts
        self.stats["skipped"] = skipped
        # One field rather than `**counts`: "repo" is both a resource name and
        # the field naming the repository, and that collision raised TypeError
        # at the very end of every default run - after all the work, and after
        # the last document had already been yielded.
        log.info("github fetch complete", repo=self.slug, counts=counts, skipped=skipped)

    def _resolve_head(self, ref: str) -> str:
        """The commit sha `ref` points at, or an error.

        Never falls back to the ref name. A cursor holding "main" compares equal
        to "main" on every later run, which turns the head-sha short circuit
        into "this repository never changes again".
        """
        head = self.gh.get(f"/repos/{self.slug}/commits/{urllib.parse.quote(ref, safe='/')}")
        sha = head.get("sha") if isinstance(head, dict) else None
        if not isinstance(sha, str) or not _SHA_RE.match(sha):
            raise GitHubError(
                f"{self.slug}: no commit sha for ref {ref!r}; refusing to use the ref name as a "
                f"cursor, which would make every later run look unchanged"
            )
        return sha

    def _walk_files(self, head_sha: str, ref: str, prior_blobs: dict[str, str], force: bool,
                    counts: dict[str, int], skipped: dict[str, int]) -> Iterator[RawDocument]:
        """One tree call, then blobs for the paths whose sha moved."""
        blob_shas: dict[str, str] = {}
        emitted = 0
        complete = True

        tree = self.gh.get(f"/repos/{self.slug}/git/trees/{head_sha}", recursive="1")
        entries = tree.get("tree") if isinstance(tree, dict) else None
        if isinstance(tree, dict) and tree.get("truncated"):
            # Marked incomplete, not just logged: the paths beyond the cut are
            # not in this walk, and advancing the head sha past them would mean
            # the next run skips the walk and never looks for them again.
            log.warn("tree truncated by GitHub; some files will be missed", repo=self.slug)
            skipped["tree_truncated"] = 1
            complete = False

        for entry in entries or []:
            if not isinstance(entry, dict) or entry.get("type") != "blob":
                continue
            if str(entry.get("mode") or "") in SKIP_MODES:
                _bump(skipped, "symlink_or_submodule")
                continue
            path = entry.get("path")
            if not isinstance(path, str) or not _safe_repo_path(path):
                log.warn("refusing an unsafe path from the tree API", repo=self.slug,
                         path=str(path)[:120])
                _bump(skipped, "unsafe_path")
                continue
            size = _as_int(entry.get("size")) or 0
            ok, reason = self._wanted_path(path, size)
            if not ok:
                _bump(skipped, reason)
                continue
            blob_sha = entry.get("sha")
            if not isinstance(blob_sha, str) or not _SHA_RE.match(blob_sha):
                _bump(skipped, "bad_sha")
                continue
            # Blob sha is git's own content hash: if it matches the last run we
            # already have this file's bytes and never fetch them.
            if not force and prior_blobs.get(path) == blob_sha:
                blob_shas[path] = blob_sha
                _bump(skipped, "blob_unchanged")
                continue
            if emitted >= self.max_files:
                # Budget spent. The sha is deliberately *not* recorded, so the
                # next run sees this path as still owed and picks up where this
                # one stopped instead of writing it off as unchanged.
                _bump(skipped, "max_files")
                complete = False
                continue
            text, reason = self._fetch_blob(path, blob_sha, head_sha)
            if text is None:
                _bump(skipped, reason)
                if reason == "failed":
                    complete = False
                else:
                    blob_shas[path] = blob_sha
                continue
            blob_shas[path] = blob_sha
            emitted += 1
            yield self._file_document(path, text, size, head_sha, blob_sha, ref)

        counts["files"] = emitted
        self.stats["blob_shas"] = blob_shas
        self.stats["files_complete"] = complete

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        # Only a walk that reached the end of the tree may advance the head sha.
        # Anything else - truncated, budget-capped, aborted - leaves the old one
        # in place so the next run walks again instead of short-circuiting past
        # files it never fetched.
        if self.stats.get("files_complete") and (sha := self.stats.get("head_sha")):
            cursor["head_sha"] = sha
        if ref := self.stats.get("ref"):
            cursor["ref"] = ref
        if (blobs := self.stats.get("blob_shas")) is not None:
            cursor["blob_shas"] = blobs
        if since := self.stats.get("issues_since"):
            cursor["issues_since"] = since
        cursor.pop("force_refetch", None)
        cursor["last_stats"] = {
            "counts": self.stats.get("counts", {}),
            "skipped": self.stats.get("skipped", {}),
            "files_complete": bool(self.stats.get("files_complete")),
        }
        return cursor

    # ---------------------------------------------------------------- documents

    def _base_meta(self, kind: str, head_sha: str = "") -> dict[str, Any]:
        return {
            "kind": kind,
            "repo": self.slug,
            "owner": self.owner,
            "authority": self.authority,
            **({"commit": head_sha} if head_sha else {}),
        }

    def _repo_document(self, meta: dict[str, Any], ref: str, head_sha: str) -> RawDocument:
        topics = meta.get("topics") or []
        if not isinstance(topics, list):
            topics = []
        body = "\n".join(
            filter(None, [
                f"# {meta.get('full_name', self.slug)}",
                meta.get("description") or "",
                f"\nPrimary language: {meta.get('language') or 'unknown'}",
                f"Default branch: {meta.get('default_branch')}",
                f"Topics: {', '.join(str(t) for t in topics) if topics else 'none'}",
                f"License: {(meta.get('license') or {}).get('spdx_id') or 'none'}",
                f"Stars: {meta.get('stargazers_count', 0)} | Forks: {meta.get('forks_count', 0)}"
                f" | Open issues: {meta.get('open_issues_count', 0)}",
                f"Homepage: {meta.get('homepage') or 'none'}",
                f"Created: {meta.get('created_at')} | Last push: {meta.get('pushed_at')}",
            ])
        )
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#repo",
            uri=meta.get("html_url") or f"https://github.com/{self.slug}",
            title=f"{self.slug} - repository overview",
            # Redacted like every other body: a description or a homepage is
            # attacker-supplied text that lands in the index unchanged.
            text=redact_secrets(body),
            metadata={
                **self._base_meta("repo", head_sha),
                "ref": ref,
                "stars": meta.get("stargazers_count", 0),
                "language": meta.get("language"),
                "topics": topics,
                "license": (meta.get("license") or {}).get("spdx_id"),
                "pushed_at": meta.get("pushed_at"),
            },
        )

    def _readme_document(self, head_sha: str) -> RawDocument | None:
        try:
            # Pinned to the commit we are ingesting: without `ref` the API
            # answers with the default branch's README while the permalink below
            # claims it came from `head_sha`.
            readme = self.gh.get(f"/repos/{self.slug}/readme", ref=head_sha)
        except RateLimitError:
            raise
        except (GitHubError, TransportError) as e:
            log.debug("no readme", repo=self.slug, err=str(e)[:100])
            return None
        if not isinstance(readme, dict):
            return None
        path = readme.get("path") or "README.md"
        if not isinstance(path, str) or not _safe_repo_path(path):
            return None
        if readme.get("encoding") != "base64":
            return None
        data, _ = self._decode_b64(readme.get("content"))
        if data is None or self._reject_bytes(data):
            return None
        return RawDocument(
            source_system="github",
            # Stable across edits on purpose. Keying this on the blob sha - the
            # obvious thing, since the sha is right there - makes every README
            # edit a brand new document and reports the previous one as removed.
            external_id=f"{self.slug}#readme",
            uri=self._permalink(path, head_sha),
            title=f"{self.slug} - {path}",
            text=redact_secrets(data.decode("utf-8", "replace")),
            metadata={
                **self._base_meta("readme", head_sha),
                "path": path,
                "language": "markdown",
                "blob_sha": readme.get("sha", ""),
            },
        )

    def _file_document(self, path: str, text: str, size: int, head_sha: str,
                       blob_sha: str, ref: str) -> RawDocument:
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#file:{path}",
            uri=self._permalink(path, head_sha),
            title=f"{self.slug}/{path}",
            text=redact_secrets(text),
            metadata={
                **self._base_meta("file", head_sha),
                "path": path,
                "dir": path.rsplit("/", 1)[0] if "/" in path else "",
                "filename": path.rsplit("/", 1)[-1],
                "ext": ext,
                "language": LANGUAGE_BY_EXT.get(ext, "text"),
                "size": size,
                "blob_sha": blob_sha,
                "ref": ref,
                "is_doc": ext in {".md", ".markdown", ".rst", ".txt", ".adoc", ".mdx"},
                "is_test": bool(_TEST_PATH_RE.search(path)),
            },
        )

    def _issue_document(self, issue: dict[str, Any]) -> RawDocument:
        is_pr = "pull_request" in issue
        number = issue.get("number")
        raw_labels = issue.get("labels") or []
        labels = [
            str(lbl.get("name", "")) for lbl in raw_labels if isinstance(lbl, dict)
        ] if isinstance(raw_labels, list) else []
        parts = [
            f"# {'PR' if is_pr else 'Issue'} #{number}: {issue.get('title','')}",
            f"State: {issue.get('state')} | Author: {(issue.get('user') or {}).get('login')}"
            f" | Comments: {issue.get('comments', 0)}",
            f"Labels: {', '.join(labels) if labels else 'none'}",
            f"Opened: {issue.get('created_at')} | Updated: {issue.get('updated_at')}",
            "",
            issue.get("body") or "(no description)",
        ]
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#{'pr' if is_pr else 'issue'}:{number}",
            uri=issue.get("html_url") or "",
            # The title is indexed and shown in citations exactly like the body,
            # so it gets redacted exactly like the body.
            title=redact_secrets(
                f"{self.slug} {'PR' if is_pr else 'issue'} #{number}: {issue.get('title','')}"
            ),
            text=redact_secrets("\n".join(parts)),
            metadata={
                **self._base_meta("pull_request" if is_pr else "issue"),
                "number": number,
                "state": issue.get("state"),
                "labels": labels,
                "author": (issue.get("user") or {}).get("login"),
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "comment_count": issue.get("comments", 0),
            },
        )

    def _commit_document(self, commit: dict[str, Any]) -> RawDocument:
        info = commit.get("commit") or {}
        info = info if isinstance(info, dict) else {}
        sha = str(commit.get("sha") or "")
        message = info.get("message") or ""
        author = info.get("author") or {}
        author = author if isinstance(author, dict) else {}
        subject = message.splitlines()[0][:80] if message else ""
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#commit:{sha}",
            uri=commit.get("html_url") or "",
            title=redact_secrets(f"{self.slug} commit {sha[:8]}: {subject}"),
            text=redact_secrets(f"# Commit {sha[:8]}\n\nAuthor: {author.get('name')}"
                                f"\nDate: {author.get('date')}\n\n{message}"),
            metadata={
                **self._base_meta("commit"),
                "sha": sha,
                "author": author.get("name"),
                "date": author.get("date"),
            },
        )

    def _release_document(self, release: dict[str, Any]) -> RawDocument | None:
        body = release.get("body") or ""
        if not isinstance(body, str) or not body.strip():
            return None
        tag = str(release.get("tag_name") or "")
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#release:{tag}",
            uri=release.get("html_url") or "",
            title=redact_secrets(
                f"{self.slug} release {tag}: {release.get('name') or ''}".strip()
            ),
            text=redact_secrets(
                f"# Release {tag}\n\nPublished: {release.get('published_at')}\n\n{body}"
            ),
            metadata={
                **self._base_meta("release"),
                "tag": tag,
                "prerelease": release.get("prerelease", False),
                "published_at": release.get("published_at"),
            },
        )
