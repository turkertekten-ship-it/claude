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
        return {
            "url": url,
            "host": rules.host,
            "allowed": self.allows(url),
            "robots_status": rules.status,
            "allow_all": rules.allow_all,
            "disallow_all": rules.disallow_all,
            "crawl_delay": rules.crawl_delay,
            "sitemaps": rules.sitemaps[:5],
        }
