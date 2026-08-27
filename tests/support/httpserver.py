"""A controllable HTTP server for hermetic end-to-end tests.

Mocking `urllib` would test our mock. This serves real HTTP on a loopback port
so the client, the robots parser, the extractor and the crawler are all
exercised over a real socket - including the parts that only misbehave against
a real server: chunked reads, gzip, 304s, redirect chains and slow responses.

127.0.0.1 is in NO_PROXY, so these tests never touch the egress proxy and run
identically in CI and in an air-gapped container.
"""

from __future__ import annotations

import gzip
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable


@dataclass
class Route:
    body: str | bytes = ""
    status: int = 200
    content_type: str = "text/html; charset=utf-8"
    headers: dict[str, str] = field(default_factory=dict)
    delay_s: float = 0.0
    gzip_body: bool = False
    etag: str | None = None
    #: Called with the hit count; return a Route to override this response.
    #: Used to test "fails twice then succeeds" retry behaviour.
    dynamic: Callable[[int], "Route | None"] | None = None


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "oodaragtest/1.0"

    def log_message(self, *args: Any) -> None:  # silence per-request stderr noise
        pass

    def _resolve(self) -> Route | None:
        routes: dict[str, Route] = self.server.routes  # type: ignore[attr-defined]
        path = self.path
        route = routes.get(path)
        if route is None and "?" in path:
            route = routes.get(path.split("?", 1)[0])
        return route

    def _respond(self, method: str) -> None:
        server = self.server  # type: ignore[assignment]
        with server.lock:  # type: ignore[attr-defined]
            server.hits[self.path] = server.hits.get(self.path, 0) + 1  # type: ignore[attr-defined]
            hit_count = server.hits[self.path]  # type: ignore[attr-defined]
            server.request_log.append((method, self.path))  # type: ignore[attr-defined]

        route = self._resolve()
        if route is None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", "9")
            self.end_headers()
            if method != "HEAD":
                self.wfile.write(b"not found")
            return

        if route.dynamic is not None:
            route = route.dynamic(hit_count) or route
        if route.delay_s:
            time.sleep(route.delay_s)

        if route.etag and self.headers.get("If-None-Match") == route.etag:
            self.send_response(304)
            self.send_header("ETag", route.etag)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        body = route.body.encode("utf-8") if isinstance(route.body, str) else route.body
        headers = dict(route.headers)
        if route.gzip_body:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"

        self.send_response(route.status)
        self.send_header("Content-Type", route.content_type)
        self.send_header("Content-Length", str(len(body)))
        if route.etag:
            self.send_header("ETag", route.etag)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        if method != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:
        self._respond("GET")

    def do_HEAD(self) -> None:
        self._respond("HEAD")

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(length)
        self._respond("POST")


class TestSite:
    """A live server you can point the crawler at.

    Usage:
        with TestSite({"/": Route(body=html)}) as site:
            crawl(site.url("/"))
    """

    def __init__(self, routes: dict[str, Route] | None = None) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.server.routes = dict(routes or {})       # type: ignore[attr-defined]
        self.server.hits = {}                          # type: ignore[attr-defined]
        self.server.request_log = []                   # type: ignore[attr-defined]
        self.server.lock = threading.Lock()            # type: ignore[attr-defined]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def port(self) -> int:
        return self.server.server_address[1]

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def url(self, path: str = "/") -> str:
        return f"{self.origin}{path}"

    def add(self, path: str, route: Route) -> None:
        self.server.routes[path] = route  # type: ignore[attr-defined]

    @property
    def hits(self) -> dict[str, int]:
        return dict(self.server.hits)  # type: ignore[attr-defined]

    @property
    def requests(self) -> list[tuple[str, str]]:
        return list(self.server.request_log)  # type: ignore[attr-defined]

    def fetched_paths(self) -> set[str]:
        return {p.split("?", 1)[0] for m, p in self.requests if m == "GET"}

    def __enter__(self) -> "TestSite":
        self.thread.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def page(title: str, body: str, *, links: list[str] | None = None, canonical: str = "",
         nofollow: list[str] | None = None, boilerplate: bool = True) -> str:
    """Build a realistic HTML page: nav, footer, cookie banner and all."""
    chrome_top = """
    <header class="site-header"><div class="logo">ACME</div></header>
    <nav class="global-nav"><ul>
      <li><a href="/">Home</a></li><li><a href="/about">About</a></li>
      <li><a href="/pricing">Pricing</a></li><li><a href="/careers">Careers</a></li>
    </ul></nav>
    <div class="cookie-consent">We use cookies. <button>Accept all cookies</button></div>
    """ if boilerplate else ""
    chrome_bottom = """
    <aside class="sidebar"><h4>Related</h4><ul>
      <li><a href="/related-1">Related one</a></li><li><a href="/related-2">Related two</a></li>
    </ul></aside>
    <footer class="site-footer">
      <p>Copyright 2026 ACME Corp. All rights reserved.</p>
      <a href="/terms">Terms</a> <a href="/privacy">Privacy</a>
    </footer>
    """ if boilerplate else ""
    # Crawl links live in the page chrome, not in the article body. That is
    # where real sites put navigation, and it keeps a page's *text* independent
    # of its outbound links - otherwise two pages with identical prose but
    # different navigation are not byte-identical and content dedupe cannot fire.
    link_html = "".join(f'<li><a href="{href}">link to {href}</a></li>' for href in (links or []))
    nofollow_html = "".join(
        f'<li><a href="{href}" rel="nofollow">nofollow {href}</a></li>' for href in (nofollow or [])
    )
    pager = (f'<nav class="pager"><ul>{link_html}{nofollow_html}</ul></nav>'
             if (links or nofollow) else "")
    canonical_tag = f'<link rel="canonical" href="{canonical}">' if canonical else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="description" content="Description of {title}.">
<meta property="og:title" content="{title}">
{canonical_tag}
<script>var tracking = "SHOULD_NOT_APPEAR_IN_TEXT";</script>
<style>.hidden {{ display:none }} /* CSS_SHOULD_NOT_APPEAR */</style>
</head><body>
{chrome_top}
<main id="content">
  <article>
    <h1>{title}</h1>
    {body}
    <p>See the <a href="/glossary">glossary</a> for definitions.</p>
  </article>
</main>
{pager}
{chrome_bottom}
<script>console.log("ALSO_SHOULD_NOT_APPEAR");</script>
</body></html>"""


def prose(words: int, seed: str = "lorem") -> str:
    """Deterministic filler with enough unique terms to be retrievable."""
    vocab = ["retrieval", "augmented", "generation", "pipeline", "embedding", "vector",
             "chunk", "index", "corpus", "query", "rerank", "citation", "evaluation",
             "grounding", "context", "document", "hybrid", "lexical", "semantic", "recall"]
    out = []
    for i in range(words):
        out.append(vocab[(i + len(seed)) % len(vocab)])
    return "<p>" + " ".join(out) + "</p>"
