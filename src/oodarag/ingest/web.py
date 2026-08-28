"""Web connector: turns a crawl into RawDocuments.

The connector is a thin adapter on purpose. All the hard behaviour (robots,
dedupe, boilerplate removal, budgets) lives in `oodarag.scrape`, which is
usable on its own; this file only maps a crawl result onto the pipeline's
document contract and applies the two things every source must do before its
text enters an index: secret redaction and provenance stamping.

"Every" is meant field by field, and that is most of what this file is. A page's
title, its description and its headings are indexed, embedded and shown in
citations exactly like its body, so redacting `text` alone leaves a title like
"deploying with <a GitHub token>" sitting readable in the corpus, in the
answer that cites it, and in the log line that announced it. The seed URL gets
the same treatment before it becomes the state-store key and the `crawl_seed`
stamped on every document: `https://user:token@host/` is a credential, and the
key is written to disk and printed on every single run.

The other thing this file owes its caller is an honest zero. A crawl that
fetched nothing - robots said no, the host was down, every page was thin -
returns an empty iterator, which is indistinguishable from a site that has no
pages. So an empty crawl raises out of `fetch` and lands in the run's delta as a
failure with the crawler's own reasons attached, instead of being reported as a
successful ingest of nothing.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.scrape.crawler import CrawlConfig, Crawler, CrawlReport, CrawlResult
from oodarag.util.http import HttpClient, normalize_url, redact_url
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets, summarize

log = get_logger("ingest.web")

#: An arbitrary web page is worth less at rerank time than a repository's own
#: source of truth.
DEFAULT_AUTHORITY = 0.8

#: Headings kept per document, and the length of a synthesised description.
#: Both come off a stranger's page and both end up in metadata that is written
#: to disk once per document, so neither is allowed to be page-sized.
MAX_HEADINGS = 20
MAX_TITLE_CHARS = 300
#: Length of a description we synthesise, and the ceiling on one a page declared
#: for itself - a `<meta name="description">` is as long as its author felt like.
DESCRIPTION_CHARS = 200
MAX_DESCRIPTION_CHARS = 400


class CrawlProducedNothing(RuntimeError):
    """A crawl that ended with no documents at all.

    Raised out of `fetch`, which is precisely what puts it in the delta:
    `Connector.run` turns an exception from the source into `failed` plus an
    error string, holds the cursor's hash map instead of concluding that every
    page ever seen has been deleted, and still returns whatever it had.
    """


class WebConnector(Connector):
    """Crawl one or more seed URLs and yield documents.

    `authority` defaults below 1.0: an arbitrary web page is worth less at
    rerank time than a repository's own source of truth. Raise it for sites you
    actually trust (official docs), lower it for aggregators.

    `enumerates_source` stays at its default of False, and that is a statement
    about crawling rather than an omission. A crawl is a *sample*: budgets stop
    it early, robots hides parts of the site, a conditional GET means an
    unchanged page is never yielded at all, and a link that moved is a page the
    frontier simply never reaches. "I did not see it this time" and "it was
    deleted" are different sentences, and this connector is not entitled to the
    second one.
    """

    def __init__(
        self,
        seeds: list[str] | str,
        *,
        key: str | None = None,
        authority: float | None = DEFAULT_AUTHORITY,
        client: HttpClient | None = None,
        **crawl_options: Any,
    ) -> None:
        # A single URL passed as a string is iterable, and CrawlConfig would
        # take it: the crawl then has one seed per *character* and fetches
        # nothing. Cheaper to accept the shape than to debug the empty report.
        if isinstance(seeds, str):
            seeds = [seeds]
        seeds = [s for s in seeds if s]
        self.config = CrawlConfig(seeds=seeds, **crawl_options)
        self.client = client
        # The key is written into the state file and logged on every run, so a
        # token in the seed must not be able to reach it. See `_safe_seed`.
        self.key = key or f"web:{_safe_seed(seeds[0]) if seeds else 'empty'}"
        # Config plumbing spells "unset" as None; without this the None travels
        # into every document's metadata and then into the reranker's
        # arithmetic, where it is a TypeError a long way from here.
        self.authority = DEFAULT_AUTHORITY if authority is None else float(authority)
        self.seed_label = _safe_seed(seeds[0]) if seeds else ""
        self.last_report: dict[str, Any] = {}

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        crawler = Crawler(self.config, client=self.client)
        crawl = crawler.crawl()
        try:
            for result in crawl:
                yield self._document(result)
        finally:
            # `crawl` fills its report in its own `finally`, which does not run
            # until that generator is closed. Closing it here rather than
            # leaving it to the garbage collector is what makes `last_report`
            # true for a run that stopped early - `run(limit=...)`, or a
            # consumer that broke out of the loop.
            crawl.close()
            self.last_report = crawler.report.as_dict()
            log.info("web connector report", key=self.key, **{
                k: v for k, v in self.last_report.items()
                if k in ("fetched", "bytes", "duration_s", "stopped_by")
            })
        # Reached only when the crawl ran to exhaustion. A crawl where every
        # page came back 304 is the one honest empty result: nothing changed.
        if not crawler.report.fetched and not crawler.report.skipped.get("not_modified"):
            raise CrawlProducedNothing(_why_nothing(crawler.report))

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["last_report"] = self.last_report
        cursor["last_crawl_at"] = time.time()
        return cursor

    # ----------------------------------------------------------------- mapping

    def _document(self, result: CrawlResult) -> RawDocument:
        page = result.page
        text = redact_secrets(page.markdown or page.text)
        # Redacted *before* the summary is cut, not after: a truncation that
        # lands inside a token would otherwise leave a fragment too short for
        # the pattern to recognise on the way out.
        description = (
            page.meta.get("description")
            or page.meta.get("og:description")
            or summarize(redact_secrets(page.text), DESCRIPTION_CHARS)
        )
        return RawDocument(
            source_system="web",
            external_id=result.url,
            # The citation URI is the URL we actually fetched, never the
            # declared canonical: a reader following a citation must land on
            # the page the text came from. `canonical` is kept as metadata
            # and used for dedupe, which is what it is actually for.
            uri=result.url,
            title=redact_secrets(str(page.title or result.url))[:MAX_TITLE_CHARS],
            text=text,
            fetched_at=result.fetched_at,
            metadata={
                "depth": result.depth,
                "status": result.status,
                "content_type": result.content_type,
                "lang": page.lang,
                "canonical": page.canonical,
                "published": page.published,
                "word_count": page.word_count,
                "link_density": round(page.link_density, 4),
                "headings": [
                    redact_secrets(str(h[1]))[:MAX_TITLE_CHARS]
                    for h in page.headings[:MAX_HEADINGS]
                ],
                "description": redact_secrets(str(description))[:MAX_DESCRIPTION_CHARS],
                "authority": self.authority,
                "crawl_seed": self.seed_label,
            },
        )


def _safe_seed(seed: str) -> str:
    """A seed URL with any userinfo removed, even when it will not parse.

    `normalize_url` drops userinfo for URLs it can parse and hands back
    unchanged anything it cannot; `redact_url` has the same escape hatch - it
    returns the URL as given when `urlsplit` raises, which is exactly what
    `https://user:token@[::1/x` does. This string becomes the state-store key,
    the `crawl_seed` on every document and a field in every log line, so the
    last word here is syntactic: whatever sits between "//" and the last "@" of
    the authority goes, parseable or not.
    """
    url = redact_url(normalize_url(seed))
    scheme, sep, rest = url.partition("//")
    if not sep:
        return url
    authority, slash, path = rest.partition("/")
    if "@" not in authority:
        return url
    return f"{scheme}//<redacted>@{authority.rsplit('@', 1)[1]}{slash}{path}"


def _why_nothing(report: CrawlReport) -> str:
    """The crawler's own account of why it produced nothing, in one line.

    Without it the delta says "0 documents" and the operator's next move is to
    re-run the crawl under a debugger. The skip counters already know whether it
    was robots, the budget or a dead host.
    """
    parts = [f"stopped_by={report.stopped_by or 'nothing_queued'}", f"fetches={report.fetches}"]
    parts += [f"{reason}={count}" for reason, count in report.skipped.most_common(3)]
    if report.errors:
        parts.append(f"first_error={report.errors[0][1]}")
    return "crawl produced no documents (" + "; ".join(parts) + ")"
