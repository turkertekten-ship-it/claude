"""robots.txt enforcement, per RFC 9309.

Scraping politely is not optional: a pipeline that ignores robots.txt gets the
IP blocked, and the corpus it built is not one you can defend using.

**Why this does not use `urllib.robotparser`.** The stdlib parser returns the
*first* rule that matches a path. RFC 9309 section 2.2.2 requires the *most
specific* rule to win - the one with the longest path pattern - with `Allow`
breaking ties. The difference is not academic. This is an extremely common
shape for a real robots.txt:

    Disallow: /docs/
    Allow: /docs/public/

Under first-match, `/docs/public/guide` is forbidden and a crawler skips the
entire documentation tree it was pointed at. Under longest-match, which is what
the site operator meant and what Google and Bing implement, it is allowed.

Group selection follows section 2.2.1, which is where three defects lived at
once (L90): the product token is matched *whole* and case-insensitively rather
than as a substring of the user-agent string, and every group naming it is
combined rather than the first one winning. All three of the bugs that fix
replaced pointed the same way - at fetching more than the site allowed.

Status handling follows the RFC:

  * 2xx -> parse and obey;
  * 4xx -> no restrictions, crawling is allowed;
  * 401/403 -> the rules themselves are access-controlled: full disallow;
  * 5xx / unreachable -> full disallow by default. A site that cannot state its
    rules does not get crawled on the assumption they are permissive.
"""

from __future__ import annotations

import re
import time
import urllib.parse
from dataclasses import dataclass, field

from oodarag.util.http import DEFAULT_UA, HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger

log = get_logger("robots")


@dataclass(slots=True)
class Rule:
    allow: bool
    pattern: str
    regex: re.Pattern[str]

    @property
    def specificity(self) -> int:
        """RFC 9309 orders by the length of the path pattern."""
        return len(self.pattern)


@dataclass(slots=True)
class Group:
    agents: list[str] = field(default_factory=list)
    rules: list[Rule] = field(default_factory=list)
    crawl_delay: float | None = None


def _compile(pattern: str) -> re.Pattern[str]:
    """Translate a robots path pattern into a regex.

    Only two metacharacters exist in the spec: `*` (any sequence) and a
    trailing `$` (end of path). Everything else is literal, so it must be
    escaped - a path containing `.` or `+` is otherwise a wildcard by accident.
    """
    anchored_end = pattern.endswith("$")
    body = pattern[:-1] if anchored_end else pattern
    out = ["^"]
    for char in body:
        out.append(".*" if char == "*" else re.escape(char))
    if anchored_end:
        out.append("$")
    return re.compile("".join(out))


def parse_robots(text: str) -> tuple[list[Group], list[str]]:
    """Parse robots.txt into user-agent groups plus the sitemap list.

    Consecutive `User-agent` lines share one group, which is how a file says
    "these rules apply to all of these agents".
    """
    groups: list[Group] = []
    sitemaps: list[str] = []
    current: Group | None = None
    last_line_was_agent = False

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field_name, _, value = line.partition(":")
        field_name = field_name.strip().lower()
        value = value.strip()

        if field_name == "user-agent":
            if current is None or not last_line_was_agent:
                current = Group()
                groups.append(current)
            current.agents.append(value.lower())
            last_line_was_agent = True
            continue

        last_line_was_agent = False
        if field_name == "sitemap":
            if value:
                sitemaps.append(value)
            continue
        if current is None:
            continue  # rule before any user-agent line: not addressed to anyone
        if field_name in ("allow", "disallow"):
            if field_name == "disallow" and not value:
                continue  # "Disallow:" with no value means allow everything
            if not value:
                continue
            current.rules.append(Rule(field_name == "allow", value, _compile(value)))
        elif field_name == "crawl-delay":
            try:
                current.crawl_delay = float(value)
            except ValueError:
                pass
    return groups, sitemaps


def _select_group(groups: list[Group], user_agent: str) -> Group | None:
    """Pick the rules addressing us, else the wildcard's, merging duplicates.

    Matching is on the product token and it is exact, per RFC 9309 section
    2.2.1: a `User-agent: oodarag` line applies to `oodarag/0.1 (+https://...)`
    and a `User-agent: rag` line does not. This used to also accept any agent
    string that was a *substring* of the full user-agent, which failed open -
    our UA carries a project URL, so `User-agent: claude` or `User-agent:
    github` selected another crawler's group, and whenever that group was more
    permissive than `*` we crawled what the site had forbidden us.

    Groups naming the same token are combined, which the same section requires
    and which the previous first-wins search did not do: a file with two
    `User-agent: *` blocks had every rule in the second one silently dropped.
    Both defects pointed the same way, at more fetching than the site allowed.
    """
    ua_token = user_agent.lower().split("/", 1)[0].strip()

    def addresses(group: Group) -> bool:
        # A file that writes its own version in the line ("User-agent:
        # oodarag/0.1") still names us; compare token against token.
        return any(agent.split("/", 1)[0].strip() == ua_token
                   for agent in group.agents if agent)

    chosen = [g for g in groups if addresses(g)]
    if not chosen:
        chosen = [g for g in groups if "*" in g.agents]
    if not chosen:
        return None
    if len(chosen) == 1:
        return chosen[0]

    merged = Group(agents=list(chosen[0].agents))
    for group in chosen:
        merged.rules.extend(group.rules)
    # Crawl-delay is an extension the RFC does not define, so merging it has no
    # spec answer. Take the longest any block asked for: the politeness reading.
    delays = [g.crawl_delay for g in chosen if g.crawl_delay is not None]
    merged.crawl_delay = max(delays) if delays else None
    return merged


@dataclass(slots=True)
class HostRules:
    host: str
    group: Group | None
    allow_all: bool
    disallow_all: bool
    sitemaps: list[str] = field(default_factory=list)
    fetched_at: float = 0.0
    status: int = 0

    @property
    def crawl_delay(self) -> float | None:
        return self.group.crawl_delay if self.group else None

    def allows(self, path: str) -> bool:
        if self.disallow_all:
            return False
        if self.allow_all or self.group is None or not self.group.rules:
            return True
        winner: Rule | None = None
        for rule in self.group.rules:
            if not rule.regex.match(path):
                continue
            if winner is None or rule.specificity > winner.specificity:
                winner = rule
            elif rule.specificity == winner.specificity and rule.allow:
                winner = rule  # RFC 9309: Allow wins an exact-length tie
        return winner.allow if winner else True


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
        parts = urllib.parse.urlsplit(url)
        return f"{parts.scheme}://{parts.netloc}"

    @staticmethod
    def _path_of(url: str) -> str:
        parts = urllib.parse.urlsplit(url)
        path = parts.path or "/"
        return f"{path}?{parts.query}" if parts.query else path

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
                             fetched_at=time.time(), status=0)

        if resp.status in (401, 403):
            return HostRules(host, None, False, True, fetched_at=time.time(), status=resp.status)
        if resp.status >= 400:
            return HostRules(host, None, True, False, fetched_at=time.time(), status=resp.status)

        try:
            groups, sitemaps = parse_robots(resp.text)
        except Exception as e:
            log.warn("robots unparseable", host=host, err=str(e)[:120])
            return HostRules(host, None, True, False, fetched_at=time.time(), status=resp.status)

        group = _select_group(groups, self.user_agent)
        return HostRules(host, group, allow_all=group is None, disallow_all=False,
                         sitemaps=sitemaps, fetched_at=time.time(), status=resp.status)

    def allows(self, url: str) -> bool:
        if not self.obey:
            return True
        return self.rules_for(url).allows(self._path_of(url))

    def crawl_delay(self, url: str) -> float:
        return self.rules_for(url).crawl_delay or 0.0

    def sitemaps(self, url: str) -> list[str]:
        return self.rules_for(url).sitemaps

    def explain(self, url: str) -> dict[str, object]:
        """Why a URL was allowed or blocked - surfaced in the crawl report so a
        thin crawl is diagnosable instead of mysterious."""
        rules = self.rules_for(url)
        path = self._path_of(url)
        matched = []
        if rules.group:
            matched = [
                {"rule": ("Allow" if r.allow else "Disallow"), "pattern": r.pattern,
                 "specificity": r.specificity}
                for r in rules.group.rules if r.regex.match(path)
            ]
        return {
            "url": url,
            "host": rules.host,
            "allowed": self.allows(url),
            "robots_status": rules.status,
            "allow_all": rules.allow_all,
            "disallow_all": rules.disallow_all,
            "crawl_delay": rules.crawl_delay,
            "matched_rules": matched,
            "sitemaps": rules.sitemaps[:5],
        }
