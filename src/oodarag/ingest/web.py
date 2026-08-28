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
from oodarag.util.dates import to_timestamp
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
        self.source_system = "web"
        self.authority = authority
        self.last_report: dict[str, Any] = {}

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        crawler = Crawler(self.config, client=self.client)
        for result in crawler.crawl():
            page = result.page
            text = redact_secrets(page.markdown or page.text)
            yield RawDocument(
                source_system="web",
                external_id=result.url,
                # The citation URI is the URL we actually fetched, never the
                # declared canonical: a reader following a citation must land on
                # the page the text came from. `canonical` is kept as metadata
                # and used for dedupe, which is what it is actually for.
                uri=result.url,
                title=page.title or result.url,
                text=text,
                fetched_at=result.fetched_at,
                # The page's own <time datetime> or meta date when it has one.
                source_updated_at=to_timestamp(page.published),
                metadata={
                    "depth": result.depth,
                    "status": result.status,
                    "content_type": result.content_type,
                    "lang": page.lang,
                    "canonical": page.canonical,
                    "published": page.published,
                    "word_count": page.word_count,
                    "link_density": round(page.link_density, 4),
                    "headings": [h[1] for h in page.headings[:20]],
                    "description": page.meta.get("description")
                    or page.meta.get("og:description")
                    or summarize(page.text, 200),
                    "authority": self.authority,
                    "crawl_seed": self.config.seeds[0] if self.config.seeds else "",
                },
            )
        self.last_report = crawler.report.as_dict()
        log.info("web connector report", key=self.key, **{
            k: v for k, v in self.last_report.items() if k in ("fetched", "bytes", "duration_s")
        })

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["last_report"] = self.last_report
        cursor["last_crawl_at"] = time.time()
        return cursor
