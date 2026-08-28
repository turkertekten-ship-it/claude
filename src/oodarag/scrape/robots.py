"""robots.txt enforcement.

Scraping politely is not optional: a pipeline that ignores robots.txt gets its
IP blocked, and the corpus it built is not one you can defend using. This
module caches one policy per *origin* (scheme + host + port, as RFC 9309
requires - `http://x` and `https://x` are two different files) and gates every
fetch through it.

The status matrix is the part everyone gets wrong, so it is spelled out:

  * 2xx -> parse the body and obey the rules;
  * 401 / 403 -> **disallow all**. RFC 9309 files these under "unavailable" and
    would let us crawl anything; we deliberately do not. A server that puts its
    own rules behind auth is not inviting an anonymous crawler, and being wrong
    in the permissive direction is the expensive kind of wrong here;
  * any other 4xx -> no restrictions, crawling is allowed;
  * 5xx, unreachable, or a body we cannot parse -> **disallow all** by default
    (`on_error="deny"`). A site that cannot tell us its rules does not get
    crawled on the assumption that they were permissive.

Why the matcher is hand-written instead of `urllib.robotparser`: the stdlib
parser predates RFC 9309 and is wrong in three ways that silently change which
pages we fetch.

  1. It implements neither `*` nor `$` in path patterns, so `Disallow: /*.pdf$`
     matches nothing and we crawl precisely what the site asked us not to.
  2. It returns the *first* matching rule rather than the most specific one, so
     the standard `Disallow: /docs` + `Allow: /docs/public` pair blocks the
     subtree the site explicitly opened.
  3. It does not strip a leading UTF-8 BOM, so the BOM lands inside the first
     `User-agent` token and deletes the entire first group. On the common
     "BOM + `User-agent: *` + `Disallow: /`" file that turns a total block into
     a total allow.

Every one of those failures is invisible from the outside: the crawl looks like
it worked. That is worth ~120 lines of matcher.

Crawl-Delay is not in RFC 9309 at all, but sites still publish it and we still
honour it (clamped - see `MAX_CRAWL_DELAY_S`); otherwise the caller's own rate
limit applies. Sitemap directives are surfaced because they are the cheapest
way to discover a site's real page inventory without recursive crawling.
"""

from __future__ import annotations

import re
import time
import urllib.parse
from dataclasses import dataclass, field

from oodarag.util.http import DEFAULT_UA, HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets

log = get_logger("robots")

#: RFC 9309 s2.5 asks crawlers to parse at least 500 KiB of robots.txt and lets
#: them stop there. Past that a file is a mistake or an attack, and the tail of
#: it cannot be allowed to cost us CPU on every host we touch.
MAX_ROBOTS_BYTES = 500 * 1024

#: Rules kept from one file. Two thousand is already far past any real site and
#: keeps the per-URL match linear in something bounded.
MAX_RULES = 2000

#: Sitemap URLs kept from one file, for the same reason.
MAX_SITEMAPS = 50

#: A `Crawl-delay: 86400` - typo or spite - would otherwise park the crawler on
#: one host for a day inside `time.sleep`. We honour delays up to a minute and
#: treat anything beyond that as a refusal we cannot usefully wait out.
MAX_CRAWL_DELAY_S = 60.0

#: RFC 9309 s2.2.4: only CR, LF and CRLF end a line. `str.splitlines()` also
#: splits on FF, NEL, LS and PS, which would cut a path in half.
_LINE_RE = re.compile(r"\r\n|\r|\n")

#: Percent-encoding normalisation for path comparison (RFC 9309 s2.2.2 compares
#: after encoding reserved and non-ASCII octets). Applied to *both* sides, so
#: the pattern and the URL agree regardless of how either was written.
_PATH_SAFE = "/~:@!$&'()+,;=?"

_ALLOW_STATUS = (401, 403, 404, 410)

_DIRECTIVES = frozenset({"allow", "disallow", "crawl-delay"})

#: Everything a host may legitimately contain once urlsplit has lowercased it
#: and IDNA has run: letters, digits, dots, hyphens, and the brackets/colons of
#: an IPv6 literal. A space or a control character in there is a malformed URL,
#: not a host - handing it to urllib gets us a header-injection attempt at worst
#: and a confusing traceback at best.
_BAD_HOST_RE = re.compile(r"[^a-z0-9._~%\[\]:-]")


def _normalize_path(text: str) -> str:
    try:
        return urllib.parse.quote(urllib.parse.unquote(text), safe=_PATH_SAFE)
    except (UnicodeError, ValueError):  # pragma: no cover - quote is very forgiving
        return text


def product_token(user_agent: str) -> str:
    """The RFC 9309 product token hidden inside a full User-Agent header.

    `"oodarag/0.1 (+https://example)"` -> `"oodarag"`. Group selection matches
    this token, not the header: a site writes `User-agent: oodarag`, never the
    version and comment we send on the wire.
    """
    head = user_agent.strip().split("/", 1)[0]
    return head.split()[0].lower() if head.split() else ""


@dataclass(slots=True)
class _Rule:
    """One Allow/Disallow line, pre-split on `*` for linear-time matching."""

    pattern: str
    allow: bool
    parts: list[str]
    anchored: bool
    length: int

    def matches(self, target: str) -> bool:
        """Glob match without a regex engine: no backtracking, so a pattern of
        forty `*` costs the same as one."""
        parts = self.parts
        if len(parts) == 1:
            return target == parts[0] if self.anchored else target.startswith(parts[0])
        if not target.startswith(parts[0]):
            return False
        pos = len(parts[0])
        for part in parts[1:-1]:
            if not part:
                continue
            found = target.find(part, pos)
            if found < 0:
                return False
            pos = found + len(part)
        last = parts[-1]
        if self.anchored:
            return len(target) - pos >= len(last) and target.endswith(last)
        return not last or target.find(last, pos) >= 0


def _make_rule(value: str, allow: bool) -> _Rule | None:
    """Compile one path pattern, or None if it is not one.

    An empty value is the documented "no restriction" form of `Disallow:` and
    carries no rule at all; a value that does not start with `/` or `*` is not
    a path-pattern per the RFC grammar and is dropped rather than guessed at.
    """
    value = value.strip()
    if not value or not value.startswith(("/", "*")):
        return None
    anchored = value.endswith("$")
    body = value[:-1] if anchored else value
    body = re.sub(r"\*+", "*", body)  # "**" and "*" match the same strings
    parts = [_normalize_path(p) for p in body.split("*")]
    return _Rule(value, allow, parts, anchored, len(value))


@dataclass(slots=True)
class RobotsTxt:
    """One parsed robots.txt, already resolved down to the group that applies
    to us. Keeping the other groups would only invite matching the wrong one
    later."""

    agent: str
    rules: list[_Rule] = field(default_factory=list)
    crawl_delay: float | None = None
    sitemaps: list[str] = field(default_factory=list)
    truncated: bool = False

    def allowance(self, url: str) -> tuple[bool, str]:
        """(allowed, reason) for a URL, by RFC 9309 s2.2.2 precedence: the
        longest matching pattern wins, and Allow beats Disallow on a tie."""
        target = match_target(url)
        best: _Rule | None = None
        for rule in self.rules:
            if not rule.matches(target):
                continue
            if best is None or rule.length > best.length:
                best = rule
            elif rule.length == best.length and rule.allow and not best.allow:
                best = rule
        if best is None:
            return True, "no_matching_rule"
        return best.allow, f"{'allow' if best.allow else 'disallow'}:{best.pattern}"


def match_target(url: str) -> str:
    """The string a robots.txt pattern is matched against: path plus query, with
    the fragment dropped (a fragment is never sent to the server)."""
    parts = urllib.parse.urlsplit(url)
    target = parts.path or "/"
    if parts.query:
        target = f"{target}?{parts.query}"
    return _normalize_path(target)


def parse_robots(text: str, token: str) -> RobotsTxt:
    """Parse robots.txt and keep only the group that applies to `token`.

    Never raises: a robots.txt is remote input, and a nightly job that dies on a
    stray byte is worse than one that crawls a site conservatively.
    """
    truncated = False
    if len(text) > MAX_ROBOTS_BYTES:
        cut = text.rfind("\n", 0, MAX_ROBOTS_BYTES)
        text = text[: cut if cut > 0 else MAX_ROBOTS_BYTES]
        truncated = True
    # RFC 9309 s2.3: a leading BOM must be ignored. Left in place it becomes
    # part of the first field name and silently voids the first group.
    text = text.lstrip("\ufeff")

    groups: dict[str, list[tuple[str, str]]] = {}
    sitemaps: list[str] = []
    current: list[str] = []
    reading_agents = False

    for raw in _LINE_RE.split(text):
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        name, _, value = line.partition(":")
        name = name.strip().lower()
        value = value.strip()
        if name == "user-agent":
            if not reading_agents:
                current = []
                reading_agents = True
            agent = value.lower()
            # Deduplicated: `User-agent: *` stacked a thousand times over one
            # rule block would otherwise store that block a thousand times.
            if agent and agent not in current:
                current.append(agent)
                groups.setdefault(agent, [])
        elif name in _DIRECTIVES:
            reading_agents = False
            for agent in current:  # one line can belong to several stacked agents
                groups[agent].append((name, value))
        elif name == "sitemap":
            # Independent of user-agent by definition, so it is collected even
            # from outside any group.
            if len(sitemaps) < MAX_SITEMAPS and _is_fetchable(value):
                sitemaps.append(value)

    selected = token if token in groups else "*"
    directives = groups.get(selected, [])
    rules: list[_Rule] = []
    delay: float | None = None
    for name, value in directives:
        if name == "crawl-delay":
            delay = _parse_delay(value, delay)
        elif len(rules) < MAX_RULES:
            rule = _make_rule(value, allow=name == "allow")
            if rule is not None:
                rules.append(rule)
    if delay is None and selected != "*":
        # Our own group said nothing about pacing; the wildcard group still
        # speaks for us. An explicit `Crawl-delay: 0` in our group does not
        # fall through here, which is the whole point of the `is None` test.
        for name, value in groups.get("*", []):
            if name == "crawl-delay":
                delay = _parse_delay(value, delay)
    return RobotsTxt(selected if selected in groups else "", rules, delay, sitemaps, truncated)


def _parse_delay(value: str, current: float | None) -> float | None:
    try:
        delay = float(value)
    except ValueError:
        return current
    if delay != delay or delay < 0 or delay == float("inf"):  # NaN, negative, inf
        return current
    if delay > MAX_CRAWL_DELAY_S:
        log.warn("crawl-delay clamped", asked=delay, using=MAX_CRAWL_DELAY_S)
        return MAX_CRAWL_DELAY_S
    return delay


def _is_fetchable(url: str) -> bool:
    """A Sitemap: line is a URL we will hand straight to the HTTP client, so a
    `file:///etc/passwd` there must not survive parsing."""
    return url.lower().startswith(("http://", "https://"))


@dataclass(slots=True)
class HostRules:
    host: str
    robots: RobotsTxt | None
    allow_all: bool
    disallow_all: bool
    crawl_delay: float | None
    sitemaps: list[str] = field(default_factory=list)
    fetched_at: float = 0.0
    status: int = 0
    reason: str = ""
    token: str = ""


@dataclass
class RobotsPolicy:
    """Per-origin robots.txt cache and gate."""

    client: HttpClient
    user_agent: str = DEFAULT_UA
    ttl_s: float = 3600.0
    on_error: str = "deny"  # "deny" (conservative) or "allow"
    obey: bool = True
    max_entries: int = 512
    _cache: dict[str, HostRules] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        # A typo'd policy must not silently become the permissive one.
        self.on_error = "allow" if str(self.on_error).strip().lower() == "allow" else "deny"

    @property
    def agent_token(self) -> str:
        return product_token(self.user_agent)

    # ------------------------------------------------------------------ origin

    def _origin(self, url: str) -> str | None:
        """Cache key and robots.txt location: scheme + host + non-default port.

        Lowercased so `HTTPS://Example.COM` and `https://example.com` share one
        entry, default ports dropped so `:443` does not fetch the file twice,
        and userinfo stripped so a `https://user:token@host/` seed cannot leak
        the credential into the robots URL, the cache key, a log line or the
        crawl report.
        """
        try:
            parts = urllib.parse.urlsplit(url)
            scheme = parts.scheme.lower()
            if scheme not in ("http", "https"):
                return None
            host = (parts.hostname or "").lower()
            if not host:
                return None
            if not host.isascii():
                host = host.encode("idna").decode("ascii").lower()
            if _BAD_HOST_RE.search(host):
                return None
            netloc = f"[{host}]" if ":" in host else host
            port = parts.port
        except (UnicodeError, ValueError):
            return None
        if port is not None and port != (443 if scheme == "https" else 80):
            netloc = f"{netloc}:{port}"
        return f"{scheme}://{netloc}"

    # ------------------------------------------------------------------- cache

    def clear_cache(self) -> None:
        self._cache.clear()

    def _store(self, origin: str, rules: HostRules) -> None:
        if len(self._cache) >= self.max_entries and origin not in self._cache:
            self._prune()
        self._cache[origin] = rules

    def _prune(self) -> None:
        """Bound the cache. A crawl that wanders across thousands of hosts must
        not turn this dict into the process's memory profile."""
        now = time.time()
        fresh = {k: v for k, v in self._cache.items() if now - v.fetched_at < self.ttl_s}
        if len(fresh) >= self.max_entries:
            # `sorted` is stable and dicts keep insertion order, so equal
            # timestamps evict oldest-inserted first rather than arbitrarily.
            ordered = sorted(fresh.items(), key=lambda kv: kv[1].fetched_at)
            fresh = dict(ordered[len(ordered) // 2 :])
        self._cache = fresh

    def rules_for(self, url: str) -> HostRules:
        origin = self._origin(url)
        if origin is None:
            # Not a URL we can ask a robots.txt about, and asking anyway would
            # hand `file:///robots.txt` straight to the opener.
            reason = ("unusable_host" if _scheme_of(url) in ("http", "https")
                      else "unsupported_scheme")
            return HostRules("", None, False, True, None, reason=reason,
                             fetched_at=time.time(), token=self.agent_token)
        token = self.agent_token
        cached = self._cache.get(origin)
        # A changed user_agent invalidates the entry: the cached rules were
        # resolved down to one group, and that group may no longer be ours.
        if cached and cached.token == token and (time.time() - cached.fetched_at) < self.ttl_s:
            return cached
        rules = self._fetch(origin, token)
        self._store(origin, rules)
        return rules

    # ----------------------------------------------------------------- fetching

    def _fetch(self, origin: str, token: str) -> HostRules:
        robots_url = f"{origin}/robots.txt"
        host = origin.split("://", 1)[1]
        try:
            resp = self.client.get(robots_url, allow_status=_ALLOW_STATUS)
        except HttpError as e:
            # Statuses outside `_ALLOW_STATUS` arrive here instead: a 400 or a
            # 451 is still "robots.txt unavailable", not "host unreachable".
            return self._from_status(host, e.status, token, str(e))
        except TransportError as e:
            return self._unavailable(host, 0, token, "unreachable", str(e))
        except Exception as e:  # the client's contract is the two above; failing
            # closed beats taking a nightly run down with an unexpected type.
            log.error("robots fetch crashed", host=host, err=f"{type(e).__name__}: {e}"[:160])
            return self._unavailable(host, 0, token, "fetch_error", type(e).__name__)

        if resp.status < 200 or resp.status >= 300:
            return self._from_status(host, resp.status, token, "")

        try:
            robots = parse_robots(resp.text, token)
        except Exception as e:  # pragma: no cover - parse_robots is total
            return self._unavailable(host, resp.status, token, "unparseable", str(e))

        reason = f"group:{robots.agent}" if robots.agent else "no_group"
        if not robots.rules and _looks_like_html(resp):
            # A soft 404: the site serves a page at /robots.txt. Same outcome as
            # a real 404 (no rules), but say so, or the crawl report claims the
            # site published an empty policy.
            reason = "html_no_rules"
            log.warn("robots looks like html", host=host, status=resp.status)
        if robots.truncated:
            log.warn("robots truncated", host=host, cap=MAX_ROBOTS_BYTES)
        return HostRules(host, robots, False, False, robots.crawl_delay, list(robots.sitemaps),
                         time.time(), resp.status, reason, token)

    def _from_status(self, host: str, status: int, token: str, detail: str) -> HostRules:
        if status in (401, 403):
            # The rules themselves are behind auth: treat as a full disallow.
            return HostRules(host, None, False, True, None, fetched_at=time.time(),
                             status=status, reason="restricted", token=token)
        if 400 <= status < 500:
            return HostRules(host, None, True, False, None, fetched_at=time.time(),
                             status=status, reason="unavailable", token=token)
        why = "server_error" if 500 <= status < 600 else "bad_status"
        return self._unavailable(host, status, token, why, detail)

    def _unavailable(self, host: str, status: int, token: str, why: str, detail: str) -> HostRules:
        deny = self.on_error == "deny"
        log.warn("robots unavailable", host=host, status=status, why=why,
                 err=redact_secrets(detail)[:160], policy=self.on_error)
        return HostRules(host, None, allow_all=not deny, disallow_all=deny, crawl_delay=None,
                         fetched_at=time.time(), status=status, reason=why, token=token)

    # ------------------------------------------------------------------ queries

    def _decide(self, rules: HostRules, url: str) -> tuple[bool, str]:
        if rules.disallow_all:
            return False, rules.reason or "disallow_all"
        if rules.allow_all or rules.robots is None:
            return True, rules.reason or "allow_all"
        if not rules.robots.rules:
            # Nothing to match against: "the file said nothing" and "the file
            # was a 404 page" are both allow-all, and the report should say which.
            return True, rules.reason or "no_matching_rule"
        try:
            return rules.robots.allowance(url)
        except Exception as e:  # pragma: no cover - allowance is total
            log.warn("robots match failed", host=rules.host, err=str(e)[:120])
            return self.on_error != "deny", "match_error"

    def allows(self, url: str) -> bool:
        if not self.obey:
            return True  # deliberately before rules_for: no fetch, no cache entry
        return self._decide(self.rules_for(url), url)[0]

    def crawl_delay(self, url: str) -> float:
        """Seconds to wait between hits, 0.0 when the site asked for nothing.

        The conflation of "no Crawl-delay" with "Crawl-delay: 0" is deliberate
        here: both mean "our own rate limit governs", which is what the caller
        does with the number. Read `rules_for(url).crawl_delay is None` when the
        distinction actually matters - reporting, mostly.
        """
        if not self.obey:
            return 0.0
        return self.rules_for(url).crawl_delay or 0.0

    def sitemaps(self, url: str) -> list[str]:
        """Sitemap URLs, even when `obey` is off: this is inventory discovery,
        not rule enforcement, and it is per seed rather than per fetched page."""
        return list(self.rules_for(url).sitemaps)

    def explain(self, url: str) -> dict[str, object]:
        """Why a URL was allowed or blocked - surfaced in the crawl report so a
        thin crawl is diagnosable instead of mysterious."""
        if not self.obey:
            origin = self._origin(url) or ""
            return {
                "url": url, "host": origin.partition("://")[2], "allowed": True,
                "reason": "robots_disabled", "obey": False, "robots_status": 0,
                "allow_all": True, "disallow_all": False, "crawl_delay": None,
                "sitemaps": [], "sitemap_count": 0, "agent": self.agent_token,
            }
        rules = self.rules_for(url)
        allowed, reason = self._decide(rules, url)
        return {
            "url": url,
            "host": rules.host,
            "allowed": allowed,
            "reason": reason,
            "obey": True,
            "robots_status": rules.status,
            "allow_all": rules.allow_all,
            "disallow_all": rules.disallow_all,
            "crawl_delay": rules.crawl_delay,
            "sitemaps": rules.sitemaps[:5],
            "sitemap_count": len(rules.sitemaps),
            "agent": rules.robots.agent if rules.robots else "",
        }


def _scheme_of(url: str) -> str:
    try:
        return urllib.parse.urlsplit(url).scheme.lower()
    except ValueError:
        return ""


def _looks_like_html(resp: object) -> bool:
    ctype = getattr(resp, "content_type", "") or ""
    if ctype in ("text/html", "application/xhtml+xml"):
        return True
    body = getattr(resp, "body", b"") or b""
    return body[:512].lstrip().lower().startswith((b"<!doctype", b"<html"))
