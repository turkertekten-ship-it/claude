"""HTML to clean text/markdown, using only `html.parser` from the stdlib.

The job has three parts, and skipping any one of them is what makes naive
scrapers produce unusable RAG corpora:

1. **Parse** tolerantly. Real HTML is malformed; a parser that trusts nesting
   will drop half a page. We build a small tree with explicit recovery rules.
2. **Strip boilerplate.** Nav bars, cookie banners and footers are the same on
   every page of a site. Left in, they dominate term statistics and every
   query retrieves the footer. We remove them structurally (tag + role) and
   then by link density, which catches the ones without semantic markup.
3. **Preserve structure.** Headings, lists and code fences carry the meaning a
   chunker needs to split on. Flattening to a wall of text throws that away.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any

from oodarag.util.http import urljoin
from oodarag.util.text import clean

VOID_TAGS = frozenset(
    "area base br col embed hr img input link meta param source track wbr".split()
)
# Dropped outright: they never carry page content.
DROP_TAGS = frozenset(
    "script style noscript svg canvas iframe object embed template form button select "
    "textarea input label dialog audio video map area picture source track".split()
)
# Structural boilerplate: dropped unless the page has nothing else.
BOILERPLATE_TAGS = frozenset("nav header footer aside menu".split())
BLOCK_TAGS = frozenset(
    "p div section article main h1 h2 h3 h4 h5 h6 ul ol li pre blockquote table tr "
    "figure figcaption dl dt dd hr br address details summary".split()
)
HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

# class/id substrings that mark chrome rather than content
_NOISE_ATTR_RE = re.compile(
    r"(^|[-_ ])(nav|navbar|menu|sidebar|side-?bar|footer|masthead|breadcrumb|pagination|pager|"
    r"cookie|consent|gdpr|banner|advert|\bads?\b|promo|newsletter|subscribe|social|share|"
    r"related|recommend|comment|disqus|popup|modal|overlay|skip-?link|toolbar|widget|"
    r"site-?header|global-?header|utility|legal|copyright)([-_ ]|$)",
    re.I,
)
_CONTENT_ATTR_RE = re.compile(
    r"(^|[-_ ])(content|main|article|post|entry|body|story|markdown|prose|doc|documentation|"
    r"readme|text)([-_ ]|$)",
    re.I,
)


@dataclass(slots=True)
class Link:
    url: str
    text: str
    rel: str = ""
    nofollow: bool = False


@dataclass(slots=True)
class ExtractedPage:
    url: str
    title: str
    text: str
    markdown: str
    #: Every link in the document, including the navigation that was stripped
    #: from the text. This is the crawl frontier: a site's nav is how you find
    #: its pages, so discarding it for *text* must not discard it for *discovery*.
    links: list[Link] = field(default_factory=list)
    #: Links inside the extracted main content only. Used for link density.
    content_links: list[Link] = field(default_factory=list)
    headings: list[tuple[int, str]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    lang: str = ""
    canonical: str = ""
    published: str = ""
    jsonld: list[Any] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def link_density(self) -> float:
        """Fraction of the extracted body text that sits inside links.

        Measured over content links only. Counting navigation links here would
        make every page look like boilerplate and the signal would be useless.
        """
        if not self.text:
            return 0.0
        link_chars = sum(len(link.text) for link in self.content_links)
        return min(1.0, link_chars / max(1, len(self.text)))

    def outgoing(self, *, follow_only: bool = True) -> list[str]:
        return [link.url for link in self.links if not (follow_only and link.nofollow)]


@dataclass(slots=True)
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)  # Node | str
    parent: Any = None

    def add(self, child: Any) -> None:
        if isinstance(child, Node):
            child.parent = self
        self.children.append(child)

    @property
    def classes(self) -> str:
        return f"{self.attrs.get('class', '')} {self.attrs.get('id', '')}".strip()

    def text_len(self) -> int:
        total = 0
        for c in self.children:
            total += len(c) if isinstance(c, str) else c.text_len()
        return total

    def link_text_len(self) -> int:
        if self.tag == "a":
            return self.text_len()
        return sum(c.link_text_len() for c in self.children if isinstance(c, Node))

    def count_tags(self, tags: frozenset[str]) -> int:
        n = 1 if self.tag in tags else 0
        return n + sum(c.count_tags(tags) for c in self.children if isinstance(c, Node))

    def iter_nodes(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter_nodes()


class _TreeBuilder(HTMLParser):
    """Tolerant tree builder.

    Recovery rules that matter in practice:
      * unknown/void tags never open a scope;
      * a block-level start tag implicitly closes an open `<p>`;
      * a `</x>` with no matching open tag is ignored rather than unwinding
        the stack (the single most common cause of truncated extractions);
      * a matching `</x>` closes every element opened inside it.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("[document]")
        self.stack: list[Node] = [self.root]
        self.raw_scripts: list[tuple[dict[str, str], str]] = []
        self._script_attrs: dict[str, str] | None = None
        self._script_buf: list[str] = []

    @property
    def current(self) -> Node:
        return self.stack[-1]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attr_map = {k.lower(): (v or "") for k, v in attrs}
        if tag == "script":
            self._script_attrs = attr_map
            self._script_buf = []
            return
        if tag in VOID_TAGS:
            self.current.add(Node(tag, attr_map))
            return
        if tag == "p" and self.current.tag == "p":
            self.stack.pop()
        elif tag in BLOCK_TAGS and self.current.tag == "p" and tag != "p":
            self.stack.pop()
        elif tag == "li" and self.current.tag == "li":
            self.stack.pop()
        node = Node(tag, attr_map)
        self.current.add(node)
        self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.current.add(Node(tag.lower(), {k.lower(): (v or "") for k, v in attrs}))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "script":
            if self._script_attrs is not None:
                self.raw_scripts.append((self._script_attrs, "".join(self._script_buf)))
                self._script_attrs = None
                self._script_buf = []
            return
        if tag in VOID_TAGS:
            return
        for idx in range(len(self.stack) - 1, 0, -1):
            if self.stack[idx].tag == tag:
                del self.stack[idx:]
                return
        # No matching open tag: stray close, ignore it.

    def handle_data(self, data: str) -> None:
        if self._script_attrs is not None:
            self._script_buf.append(data)
            return
        if any(n.tag == "pre" for n in self.stack):
            # Inside <pre>, whitespace *is* the content: line breaks and
            # indentation are what make a code block readable.
            self.current.add(data)
        elif data.strip():
            self.current.add(data)
        elif data:
            # Whitespace between inline elements is a real word boundary:
            # dropping it welds "read the" + "docs" into "read thedocs".
            self.current.add(" ")


def _should_drop(node: Node, aggressive: bool) -> bool:
    if node.tag in DROP_TAGS:
        return True
    if node.attrs.get("hidden") is not None and node.attrs.get("hidden") != "false":
        return True
    if node.attrs.get("aria-hidden") == "true":
        return True
    if "display:none" in node.attrs.get("style", "").replace(" ", "").lower():
        return True
    role = node.attrs.get("role", "").lower()
    if role in {"navigation", "banner", "contentinfo", "complementary", "search", "dialog", "alert"}:
        return True
    if aggressive:
        if node.tag in BOILERPLATE_TAGS:
            return True
        blob = node.classes
        if blob and _NOISE_ATTR_RE.search(blob) and not _CONTENT_ATTR_RE.search(blob):
            return True
    return False


def _prune(node: Node, aggressive: bool) -> None:
    kept: list[Any] = []
    for child in node.children:
        if isinstance(child, str):
            kept.append(child)
            continue
        if _should_drop(child, aggressive):
            continue
        _prune(child, aggressive)
        kept.append(child)
    node.children = kept


def _find_main(root: Node) -> Node:
    """Pick the subtree most likely to be the article body.

    Semantic markup wins if it carries enough text. Otherwise score candidates
    by text length minus link text (boilerplate is mostly links), with a bonus
    for paragraph count and content-ish class names.
    """
    for node in root.iter_nodes():
        if node.tag == "main" or node.attrs.get("role") == "main":
            if node.text_len() > 200:
                return node
    articles = [n for n in root.iter_nodes() if n.tag == "article" and n.text_len() > 200]
    if articles:
        return max(articles, key=lambda n: n.text_len())

    best, best_score = root, -1.0
    for node in root.iter_nodes():
        if node.tag in {"[document]", "html", "body"}:
            continue
        text_len = node.text_len()
        if text_len < 140:
            continue
        link_len = node.link_text_len()
        paragraphs = node.count_tags(frozenset({"p"}))
        score = (text_len - 1.5 * link_len) + 60.0 * paragraphs
        blob = node.classes
        if blob and _CONTENT_ATTR_RE.search(blob):
            score *= 1.35
        if blob and _NOISE_ATTR_RE.search(blob):
            score *= 0.45
        # Prefer the tighter container when two nodes score alike (parent chains
        # otherwise always win by containing their own children).
        depth = 0
        p = node.parent
        while p is not None:
            depth += 1
            p = p.parent
        score *= 1.0 + min(depth, 12) * 0.01
        if score > best_score:
            best, best_score = node, score
    return best


def _render(node: Node, base_url: str, links: list[Link], headings: list[tuple[int, str]],
            depth: int = 0, list_stack: tuple[str, ...] = ()) -> str:
    """Render a pruned subtree to markdown."""
    tag = node.tag
    if tag == "a":
        href = node.attrs.get("href", "").strip()
        text = clean(_inline_text(node))
        if href and not href.lower().startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
            rel = node.attrs.get("rel", "").lower()
            try:
                absolute = urljoin(base_url, href)
            except ValueError:
                absolute = href
            if absolute.startswith(("http://", "https://")):
                links.append(Link(absolute, text, rel, "nofollow" in rel))
        return text

    if tag == "pre":
        body = _inline_text(node, preserve=True).strip("\n")
        lang = ""
        for n in node.iter_nodes():
            cls = n.attrs.get("class", "")
            if m := re.search(r"language-([A-Za-z0-9+#-]+)", cls):
                lang = m.group(1)
                break
        return f"\n\n```{lang}\n{body}\n```\n\n"

    if tag in HEADING_TAGS:
        text = clean(_inline_text(node))
        if not text:
            return ""
        level = HEADING_TAGS[tag]
        headings.append((level, text))
        return f"\n\n{'#' * level} {text}\n\n"

    if tag == "li":
        marker = "1." if list_stack and list_stack[-1] == "ol" else "-"
        indent = "  " * max(0, len(list_stack) - 1)
        inner = "".join(
            _render(c, base_url, links, headings, depth + 1, list_stack) if isinstance(c, Node) else c
            for c in node.children
        )
        inner = re.sub(r"\n{2,}", "\n", inner).strip()
        return f"\n{indent}{marker} {inner}" if inner else ""

    if tag in ("ul", "ol"):
        inner = "".join(
            _render(c, base_url, links, headings, depth + 1, (*list_stack, tag))
            if isinstance(c, Node) else c
            for c in node.children
        )
        return f"\n{inner}\n"

    if tag == "blockquote":
        inner = clean(_inline_text(node))
        return "\n\n" + "\n".join(f"> {line}" for line in inner.split("\n") if line) + "\n\n"

    if tag == "br":
        return "\n"
    if tag == "hr":
        return "\n\n---\n\n"
    if tag == "img":
        alt = node.attrs.get("alt", "").strip()
        return f" [image: {alt}] " if alt else " "

    if tag == "tr":
        cells = [clean(_inline_text(c)) for c in node.children
                 if isinstance(c, Node) and c.tag in ("td", "th")]
        return "\n| " + " | ".join(cells) + " |" if cells else ""
    if tag == "table":
        inner = "".join(
            _render(c, base_url, links, headings, depth + 1, list_stack) if isinstance(c, Node) else ""
            for c in node.children
        )
        return f"\n\n{inner.strip()}\n\n"

    inner = "".join(
        _render(c, base_url, links, headings, depth + 1, list_stack) if isinstance(c, Node) else c
        for c in node.children
    )
    if tag in BLOCK_TAGS or tag == "[document]":
        return f"\n\n{inner.strip()}\n\n" if inner.strip() else ""
    return inner


_FENCE_RE = re.compile(r"^```", re.MULTILINE)


def _tidy(markdown: str) -> str:
    """Normalise whitespace outside fenced code blocks.

    Code fences are left byte-for-byte: collapsing runs of spaces inside a
    Python snippet changes what the snippet means.
    """
    parts = markdown.split("```")
    for i in range(0, len(parts), 2):  # even indices are outside fences
        block = parts[i]
        block = "\n".join(line.rstrip() for line in block.split("\n"))
        block = re.sub(r"[ \t]{2,}", " ", block)
        block = re.sub(r"\n{3,}", "\n\n", block)
        parts[i] = block
    joined = "```".join(parts)
    return re.sub(r"\n{3,}", "\n\n", joined).strip()


def _inline_text(node: Node, preserve: bool = False) -> str:
    out: list[str] = []
    for c in node.children:
        if isinstance(c, str):
            out.append(c)
        elif c.tag == "br":
            out.append("\n")
        elif c.tag == "img":
            alt = c.attrs.get("alt", "").strip()
            out.append(f" [image: {alt}] " if alt else " ")
        else:
            out.append(_inline_text(c, preserve))
    joined = "".join(out)
    return joined if preserve else clean(joined)


def _collect_meta(root: Node, raw_scripts: list[tuple[dict[str, str], str]],
                  base_url: str) -> tuple[dict[str, Any], str, str, str, list[Any], str]:
    meta: dict[str, Any] = {}
    title = ""
    lang = ""
    canonical = ""
    published = ""
    jsonld: list[Any] = []

    for node in root.iter_nodes():
        if node.tag == "html":
            lang = node.attrs.get("lang", "") or lang
        elif node.tag == "title" and not title:
            title = clean(_inline_text(node))
        elif node.tag == "meta":
            name = (node.attrs.get("property") or node.attrs.get("name") or "").lower()
            content = node.attrs.get("content", "").strip()
            if name and content:
                meta[name] = content
        elif node.tag == "link" and "canonical" in node.attrs.get("rel", "").lower():
            href = node.attrs.get("href", "").strip()
            if href:
                canonical = urljoin(base_url, href)
        elif node.tag == "time" and not published:
            published = node.attrs.get("datetime", "").strip()

    for attrs, body in raw_scripts:
        if "ld+json" in attrs.get("type", "").lower() and body.strip():
            try:
                jsonld.append(json.loads(body))
            except json.JSONDecodeError:
                continue

    title = meta.get("og:title") or title
    published = (
        meta.get("article:published_time") or meta.get("date") or meta.get("dc.date") or published
    )
    return meta, title, lang, canonical, jsonld, published


def extract(html: str, url: str = "", *, aggressive: bool = True,
            min_words: int = 25, max_fallback_link_density: float = 0.35) -> ExtractedPage:
    """Extract clean markdown, links and metadata from an HTML document.

    If aggressive boilerplate removal leaves too little text - a page whose
    article is wrapped in a `class="sidebar"` div, say - we retry conservatively
    rather than return an empty page.

    That retry needs a guard. A genuinely near-empty page ("Redirecting...", a
    stub, a 404 body) *also* trips the retry, and the conservative pass then
    happily returns the navigation bar, the cookie banner and the footer as if
    they were the article. The page now looks substantial, sails past every
    downstream length filter, and poisons the index with chrome that is
    identical on every page of the site.

    So the fallback is only accepted if it is both longer *and* not mostly
    links. Boilerplate is overwhelmingly link text; real prose is not.
    """
    parser = _TreeBuilder()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass  # tolerant by design: keep whatever tree we managed to build
    root = parser.root

    meta, title, lang, canonical, jsonld, published = _collect_meta(root, parser.raw_scripts, url)

    def build(aggr: bool) -> ExtractedPage:
        import copy

        tree = copy.deepcopy(root)
        _prune(tree, aggr)
        main = _find_main(tree)
        content_links: list[Link] = []
        headings: list[tuple[int, str]] = []
        markdown = _render(main, url or canonical, content_links, headings)
        markdown = _tidy(markdown)
        text = clean(re.sub(r"^#{1,6}\s+", "", markdown, flags=re.MULTILINE))
        # Walk the ORIGINAL tree, not the pruned one: the nav and footer we just
        # removed from the text are exactly where a site publishes its page
        # inventory. Pruning them out of the frontier would strand the crawler
        # on the seed page.
        all_links: list[Link] = []
        seen: set[str] = set()
        for node in root.iter_nodes():
            if node.tag != "a":
                continue
            href = node.attrs.get("href", "").strip()
            if not href or href.lower().startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
                continue
            try:
                absolute = urljoin(url or canonical, href)
            except ValueError:
                continue
            if not absolute.startswith(("http://", "https://")) or absolute in seen:
                continue
            seen.add(absolute)
            rel = node.attrs.get("rel", "").lower()
            all_links.append(Link(absolute, clean(_inline_text(node)), rel, "nofollow" in rel))
        return ExtractedPage(
            url=url, title=title, text=text, markdown=markdown, links=all_links,
            content_links=content_links, headings=headings, meta=meta, lang=lang,
            canonical=canonical, published=published, jsonld=jsonld,
        )

    page = build(aggressive)
    if aggressive and len(page.text.split()) < min_words:
        fallback = build(False)
        richer = len(fallback.text.split()) > len(page.text.split())
        mostly_chrome = fallback.link_density > max_fallback_link_density
        if richer and not mostly_chrome:
            return fallback
    return page
