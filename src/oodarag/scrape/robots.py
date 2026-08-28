"""robots.txt enforcement.

Scraping politely is not optional: a pipeline that ignores robots.txt gets the
IP blocked, and the corpus it built is not one you can defend using. This
module caches one policy per host and applies RFC 9309 semantics:

  * 2xx  -> parse and obey the rules;
  * 4xx  -> no restrictions, crawling is allowed;
  * 5xx / unreachable -> treat as *disallow all* by default. A site that cannot
    tell us its rules does not get crawled on the assumption they are permissive.

Crawl-Delay is honoured when present; otherwise the caller's own rate limit
applies. Sitemap directives are surfaced because they are the cheapest way to
discover a site's real page inventory without recursive crawling.

`urllib.robotparser` does the tokenising and the user-agent grouping, but two
of its decisions predate RFC 9309 and are wrong for our stated contract, so
this module overrides them (see `_longest_match_allows` and `_crawl_delay`).
"""

from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass, field
from urllib.robotparser import RobotFileParser

from oodarag.util.http import DEFAULT_UA, HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger

log = get_logger("robots")

#: Directives that count as "a rule line" for the purpose of group boundaries -
#: the same set `urllib.robotparser` uses to decide a new group has started.
_RULE_KEYS = frozenset({"allow", "disallow", "crawl-delay", "request-rate"})


def _rule_path(url: str) -> str:
    """The path form robots.txt rules are matched against, quoted exactly the
    way `urllib.robotparser` quotes its own rule paths so the two can be
    compared with `str.startswith`."""
    parsed = urllib.parse.urlparse(urllib.parse.unquote(url))
    path = urllib.parse.urlunparse(
        ("", "", parsed.path, parsed.params, parsed.query, parsed.fragment)
    )
    return urllib.parse.quote(path) or "/"


def _matching_entry(parser: RobotFileParser, user_agent: str):
    """The one group that applies to us: a named match first, then `*`."""
    for entry in parser.entries:
        if entry.applies_to(user_agent):
            return entry
    return parser.default_entry


def _matching_rule(parser: RobotFileParser, user_agent: str, url: str):
    """The rule line that decides `url`, or None when no rule matches.

    RFC 9309 section 2.2.2: the *most specific* match wins, measured by the
    length of the rule path, and an Allow wins a tie with a Disallow.
    `urllib.robotparser` instead returns the *first* matching line in file
    order, which gets the single most common real-world pattern backwards:

        Disallow: /docs/
        Allow: /docs/public/

    means "crawl /docs/public/" to every other crawler and "crawl nothing under
    /docs/" to a first-match parser. A docs site that carves out a public
    subtree that way yields zero pages instead of its whole public corpus.
    """
    entry = _matching_entry(parser, user_agent)
    if entry is None:
        return None
    path = _rule_path(url)
    best = None
    best_len = -1
    for line in entry.rulelines:
        if not (line.path == "*" or path.startswith(line.path)):
            continue
        length = len(line.path)
        # Strictly longer wins; on a tie the Allow wins, per the RFC.
        if length > best_len or (length == best_len and line.allowance and best is not None
                                 and not best.allowance):
            best, best_len = line, length
    return best


def _longest_match_allows(parser: RobotFileParser, user_agent: str, url: str) -> bool:
    rule = _matching_rule(parser, user_agent, url)
    # No group applies to us, or none of its rules match: access is granted.
    return True if rule is None else bool(rule.allowance)


def _crawl_delay(lines: list[str], user_agent: str) -> float | None:
    """Crawl-delay as a float, for the group that applies to `user_agent`.

    `urllib.robotparser` accepts a delay only when `line[1].strip().isdigit()`,
    so `Crawl-delay: 0.5` - a perfectly ordinary directive, and the one a busy
    site uses when a whole second between requests is more than it needs -
    parses to *no delay at all* and we hammer the host at our own rate. That is
    precisely the behaviour this module exists to prevent, so the value is
    re-read here with the same grouping rules and `float()` instead.
    """
    token = user_agent.split("/")[0].strip().lower()
    specific: float | None = None
    generic: float | None = None
    agents: list[str] = []
    in_rules = False
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            if in_rules:  # a user-agent line after a rule line starts a new group
                agents = []
                in_rules = False
            agents.append(value.lower())
            continue
        if key not in _RULE_KEYS:
            continue
        in_rules = True
        if key != "crawl-delay" or not agents:
            continue
        try:
            delay = float(value)
        except ValueError:
            continue
        if delay <= 0:
            continue
        if any(a and a != "*" and a in token for a in agents):
            if specific is None:  # first matching group wins, as in the stdlib
                specific = delay
        elif "*" in agents and generic is None:
            generic = delay
    return specific if specific is not None else generic


@dataclass(slots=True)
class HostRules:
    host: str
    parser: RobotFileParser | None
    allow_all: bool
    disallow_all: bool
    crawl_delay: float | None
    sitemaps: list[str] = field(default_factory=list)
    fetched_at: float = 0.0
    status: int = 0


@dataclass
class RobotsPolicy:
    """Per-host robots.txt cache and gate."""

    client: HttpClient
    user_agent: str = DEFAULT_UA
    ttl_s: float = 3600.0
    on_error: str = "deny"  # "deny" (RFC-conservative) or "allow"
    obey: bool = True
    _cache: dict[str, HostRules] = field(default_factory=dict, repr=False)

    def _origin(self, url: str) -> str:
        p = urllib.parse.urlsplit(url)
        return f"{p.scheme}://{p.netloc}"

    def rules_for(self, url: str) -> HostRules:
        origin = self._origin(url)
        cached = self._cache.get(origin)
        if cached and (time.time() - cached.fetched_at) < self.ttl_s:
            return cached
        rules = self._fetch(origin)
        self._cache[origin] = rules
        return rules

    def _fetch(self, origin: str) -> HostRules:
        robots_url = f"{origin}/robots.txt"
        host = urllib.parse.urlsplit(origin).netloc
        try:
            resp = self.client.get(robots_url, allow_status=(401, 403, 404, 410))
        except (HttpError, TransportError) as e:
            log.warn("robots unreachable", host=host, err=str(e)[:160], policy=self.on_error)
            deny = self.on_error == "deny"
            return HostRules(host, None, allow_all=not deny, disallow_all=deny,
                             crawl_delay=None, fetched_at=time.time(), status=0)

        if resp.status in (401, 403):
            # Access to the rules themselves is restricted: treat as full disallow.
            return HostRules(host, None, False, True, None, fetched_at=time.time(),
                             status=resp.status)
        if resp.status >= 400:
            return HostRules(host, None, True, False, None, fetched_at=time.time(),
                             status=resp.status)

        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            lines = resp.text.splitlines()
            parser.parse(lines)
        except Exception as e:
            log.warn("robots unparseable", host=host, err=str(e)[:120])
            return HostRules(host, None, True, False, None, fetched_at=time.time(),
                             status=resp.status)

        try:
            delay = _crawl_delay(lines, self.user_agent)
            if delay is None:
                delay = parser.crawl_delay(self.user_agent) or parser.crawl_delay("*")
        except Exception:
            delay = None
        sitemaps = list(parser.site_maps() or [])
        return HostRules(host, parser, False, False, float(delay) if delay else None,
                         sitemaps, time.time(), resp.status)

    def allows(self, url: str) -> bool:
        if not self.obey:
            return True
        rules = self.rules_for(url)
        if rules.disallow_all:
            return False
        if rules.allow_all or rules.parser is None:
            return True
        try:
            return _longest_match_allows(rules.parser, self.user_agent, url)
        except Exception:
            return self.on_error != "deny"

    def crawl_delay(self, url: str) -> float:
        return self.rules_for(url).crawl_delay or 0.0

    def sitemaps(self, url: str) -> list[str]:
        return self.rules_for(url).sitemaps

    def explain(self, url: str) -> dict[str, object]:
        """Why a URL was allowed or blocked - surfaced in the crawl report so a
        thin crawl is diagnosable instead of mysterious."""
        rules = self.rules_for(url)
        rule = ""
        if rules.parser is not None:
            matched = _matching_rule(rules.parser, self.user_agent, url)
            if matched is not None:
                rule = str(matched)
        return {
            "url": url,
            "host": rules.host,
            "allowed": self.allows(url),
            "robots_status": rules.status,
            "allow_all": rules.allow_all,
            "disallow_all": rules.disallow_all,
            "crawl_delay": rules.crawl_delay,
            "sitemaps": rules.sitemaps[:5],
            # The deciding line itself, because "allowed: false" with no rule
            # beside it sends the reader back to robots.txt to guess which of
            # forty Disallow lines was the one that mattered.
            "rule": rule,
        }
