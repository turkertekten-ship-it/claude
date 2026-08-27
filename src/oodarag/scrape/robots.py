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

**Rule precedence is longest-match, not first-match.** RFC 9309 resolves a path
against the most *specific* matching rule, with `Allow` winning a tie. Python's
`urllib.robotparser` instead takes the first matching line in file order, so for

    Disallow: /private/
    Allow: /private/public-bit

it refuses `/private/public-bit`, which the site explicitly permits. The error
is in the safe direction — nothing forbidden gets fetched — but it silently
shrinks a crawl, and a thin crawl with no stated reason is the failure this
module's `explain()` exists to prevent. `RuleSet` below implements the RFC
precedence; the stdlib parser is retained only for Crawl-Delay and Sitemap,
where it is correct.
"""

from __future__ import annotations

import time
import urllib.parse
from dataclasses import dataclass, field
from urllib.robotparser import RobotFileParser

from oodarag.util.http import DEFAULT_UA, HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger

log = get_logger("robots")


@dataclass(slots=True)
class Rule:
    """One Allow or Disallow line, kept with its specificity."""

    allow: bool
    pattern: str

    @property
    def specificity(self) -> int:
        """Path length, per RFC 9309. Wildcards count as the characters given."""
        return len(self.pattern)


class RuleSet:
    """The Allow/Disallow rules of the group that applies to one user agent.

    Matching follows RFC 9309: the rule with the longest pattern wins, and
    `Allow` wins a tie. An empty `Disallow:` is a no-op permitting everything,
    which is how sites express "no restrictions" without an empty file.
    """

    def __init__(self, rules: list[Rule] | None = None) -> None:
        self.rules = rules or []

    def __len__(self) -> int:
        return len(self.rules)

    @classmethod
    def parse(cls, text: str, user_agent: str) -> RuleSet:
        """Select the group for `user_agent`, falling back to the `*` group.

        A specific match beats `*`, which is what lets a site give this crawler
        different rules from everyone else.
        """
        groups: dict[str, list[Rule]] = {}
        current: list[str] = []
        starting_group = False

        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            field_name, _, value = line.partition(":")
            field_name = field_name.strip().lower()
            value = value.strip()

            if field_name == "user-agent":
                # Consecutive User-agent lines share one group of rules.
                if not starting_group:
                    current = []
                    starting_group = True
                current.append(value.lower())
                groups.setdefault(value.lower(), [])
            elif field_name in ("allow", "disallow"):
                starting_group = False
                if not current:
                    continue  # a rule before any User-agent line belongs to nobody
                if field_name == "disallow" and not value:
                    continue  # "Disallow:" with no path restricts nothing
                if not value:
                    continue
                for agent in current:
                    groups.setdefault(agent, []).append(
                        Rule(allow=field_name == "allow", pattern=value)
                    )

        ua = user_agent.lower()
        for agent, rules in groups.items():
            if agent != "*" and agent and agent in ua:
                return cls(rules)
        return cls(groups.get("*", []))

    def allows(self, path: str) -> bool:
        """Longest matching rule decides; Allow wins a tie; no match allows."""
        best: Rule | None = None
        for rule in self.rules:
            if not _pattern_matches(rule.pattern, path):
                continue
            if best is None or rule.specificity > best.specificity:
                best = rule
            elif rule.specificity == best.specificity and rule.allow:
                best = rule  # Allow wins an equal-length tie
        return True if best is None else best.allow

    def matched(self, path: str) -> Rule | None:
        """The rule that decided, for `explain()`."""
        best: Rule | None = None
        for rule in self.rules:
            if not _pattern_matches(rule.pattern, path):
                continue
            if best is None or rule.specificity > best.specificity:
                best = rule
            elif rule.specificity == best.specificity and rule.allow:
                best = rule
        return best


def _pattern_matches(pattern: str, path: str) -> bool:
    """RFC 9309 path matching: `*` is any sequence, `$` anchors the end."""
    anchored = pattern.endswith("$")
    if anchored:
        pattern = pattern[:-1]
    if "*" not in pattern:
        return path == pattern if anchored else path.startswith(pattern)

    segments = pattern.split("*")
    if not path.startswith(segments[0]):
        return False
    cursor = len(segments[0])
    for segment in segments[1:-1]:
        if not segment:
            continue
        found = path.find(segment, cursor)
        if found < 0:
            return False
        cursor = found + len(segment)
    tail = segments[-1]
    if not tail:
        return not anchored or cursor == len(path)
    if anchored:
        return path.endswith(tail) and len(path) - len(tail) >= cursor
    return path.find(tail, cursor) >= 0


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
    ruleset: RuleSet | None = None


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
            parser.parse(resp.text.splitlines())
        except Exception as e:
            log.warn("robots unparseable", host=host, err=str(e)[:120])
            return HostRules(host, None, True, False, None, fetched_at=time.time(),
                             status=resp.status)

        delay = None
        try:
            delay = parser.crawl_delay(self.user_agent) or parser.crawl_delay("*")
        except Exception:
            delay = None
        sitemaps = list(parser.site_maps() or [])
        return HostRules(host, parser, False, False, float(delay) if delay else None,
                         sitemaps, time.time(), resp.status,
                         ruleset=RuleSet.parse(resp.text, self.user_agent))

    def allows(self, url: str) -> bool:
        if not self.obey:
            return True
        rules = self.rules_for(url)
        if rules.disallow_all:
            return False
        if rules.allow_all:
            return True
        if rules.ruleset is not None:
            path = urllib.parse.urlsplit(url).path or "/"
            if query := urllib.parse.urlsplit(url).query:
                path = f"{path}?{query}"
            return rules.ruleset.allows(path)
        if rules.parser is None:
            return True
        try:
            return bool(rules.parser.can_fetch(self.user_agent, url))
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
        path = urllib.parse.urlsplit(url).path or "/"
        decided = rules.ruleset.matched(path) if rules.ruleset else None
        return {
            "url": url,
            "host": rules.host,
            "allowed": self.allows(url),
            "robots_status": rules.status,
            "allow_all": rules.allow_all,
            "disallow_all": rules.disallow_all,
            "crawl_delay": rules.crawl_delay,
            "sitemaps": rules.sitemaps[:5],
            # The specific line that decided, so "why was this skipped?" has an
            # answer that is not "robots.txt, somehow".
            "matched_rule": (
                f"{'Allow' if decided.allow else 'Disallow'}: {decided.pattern}"
                if decided else None
            ),
            "rules_in_group": len(rules.ruleset) if rules.ruleset else 0,
        }
