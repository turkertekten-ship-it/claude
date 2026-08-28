"""Web connector: turns a crawl into RawDocuments.

The connector is a thin adapter on purpose. All the hard behaviour (robots,
dedupe, boilerplate removal, budgets) lives in `oodarag.scrape`, which is
usable on its own; this file only maps a crawl result onto the pipeline's
document contract and applies the two things every source must do before its
text enters an index: secret redaction and provenance stamping.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.scrape.crawler import Crawler, CrawlConfig
from oodarag.util.http import HttpClient
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets, summarize

log = get_logger("ingest.web")


class WebConnector(Connector):
    """Crawl one or more seed URLs and yield documents.

    `authority` defaults below 1.0: an arbitrary web page is worth less at
    rerank time than a repository's own source of truth. Raise it for sites you
    actually trust (official docs), lower it for aggregators.
    """

    def __init__(
        self,
        seeds: list[str],
        *,
        key: str | None = None,
        authority: float = 0.8,
        client: HttpClient | None = None,
        **crawl_options: Any,
    ) -> None:
        self.config = CrawlConfig(seeds=seeds, **crawl_options)
        self.client = client
        self.key = key or f"web:{seeds[0] if seeds else 'empty'}"
        self.authority = authority
        self.last_report: dict[str, Any] = {}
        self._not_modified: set[str] = set()

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        self._not_modified = set()
        crawler = Crawler(self.config, client=self.client)
        try:
            for result in crawler.crawl():
                page = result.page
                text = redact_secrets(page.markdown or page.text)
                description = (
                    page.meta.get("description")
                    or page.meta.get("og:description")
                    or summarize(page.text, 200)
                )
                yield RawDocument(
                    source_system="web",
                    external_id=result.url,
                    # The citation URI is the URL we actually fetched, never the
                    # declared canonical: a reader following a citation must land on
                    # the page the text came from. `canonical` is kept as metadata
                    # and used for dedupe, which is what it is actually for.
                    uri=result.url,
                    # Redaction covered the body only, and the body is not the
                    # only field that reaches an index: the title is hashed into
                    # `Document.content_hash` and printed in every context
                    # header and citation, and the description is stored
                    # alongside it. A key pasted into a page's <title> or its
                    # og:description walked straight through.
                    title=redact_secrets(page.title) or result.url,
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
                        "headings": [redact_secrets(h[1]) for h in page.headings[:20]],
                        "description": redact_secrets(description),
                        "authority": self.authority,
                        "crawl_seed": self.config.seeds[0] if self.config.seeds else "",
                    },
                )
        finally:
            # `Connector.run(limit=...)` abandons this generator, and an
            # abandoned generator never reaches a trailing statement: the crawl
            # report was lost exactly when a run was cut short, which is one of
            # the cases the report exists for. `crawler.report` is complete
            # enough to publish at any point, and a `finally` block still runs
            # when the consumer stops iterating or the crawl raises.
            self.last_report = crawler.report.as_dict()
            self._not_modified = set(crawler.report.not_modified)
            log.info("web connector report", key=self.key, **{
                k: v for k, v in self.last_report.items() if k in ("fetched", "bytes", "duration_s")
            })

    def unchanged_external_ids(self) -> set[str]:
        """URLs the server answered 304 to on the last crawl.

        `external_id` for this connector is the URL, so a not-modified response
        names the document directly. Conditional GETs are the crawler's main
        saving on a re-crawl, and without this the saving read as a deletion of
        every page that had not changed.
        """
        return set(self._not_modified)

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["last_report"] = self.last_report
        cursor["last_crawl_at"] = time.time()
        return cursor
