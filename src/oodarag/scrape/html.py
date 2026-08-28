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

Two rules keep this honest when a page fights back. Boilerplate removal always
errs towards keeping: a footer left in a document costs a few junk tokens, an
article thrown away costs the document. And nothing in here may raise on a
hostile document - the depth cap, the JSON guard and the fallback page exist so
that one adversarial page cannot end a nightly crawl.
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
    "p div section article main h1 h2 h3 h4 h5 h6 ul ol li pre blockquote table tr td th "
    "figure figcaption dl dt dd hr br address details summary".split()
)
HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

#: ARIA roles that mean "this region is chrome". Matched per token, because
#: `role="banner navigation"` is legal and `role in {...}` misses it.
DROP_ROLES = frozenset("navigation banner contentinfo complementary search dialog alert".split())

#: Href prefixes that are not fetchable documents. The http/https check after
#: resolution is the real gate; this one keeps them out of the link *text* path
#: too, and documents the intent.
SKIP_HREF_PREFIXES = ("javascript:", "mailto:", "tel:", "#", "data:", "about:", "blob:")

#: Start tags whose closing tag is optional in HTML, and what an opening one
#: implicitly closes. Real pages leave every one of these out: without the rule,
#: `<td>a<td>b` nests the second cell inside the first and the row collapses to
#: a single column. `p` is in every set because a paragraph cannot span a cell
#: or a list item boundary.
IMPLICIT_CLOSE = {
    "p": frozenset({"p"}),
    "li": frozenset({"li", "p"}),
    "dt": frozenset({"dt", "dd", "p"}),
    "dd": frozenset({"dt", "dd", "p"}),
    "td": frozenset({"td", "th", "p"}),
    "th": frozenset({"td", "th", "p"}),
    "tr": frozenset({"tr", "td", "th", "p"}),
    "option": frozenset({"option"}),
}

#: Nesting past this is decoration, never content, and every walk in this module
#: is recursive: 5000 nested `<div>`s in a fuzzed page must not become a
#: RecursionError halfway through a crawl. Deeper elements still enter the tree,
#: they just stop opening new scopes.
MAX_TREE_DEPTH = 100

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
_HEADING_MARK_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_BACKTICKS_RE = re.compile(r"`+")


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
    links: list[Link] = field(default_factory=list)
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
        """Link text on the page, as a fraction of the text we kept.

        `links` spans the whole document and `text` only the article, so this is
        a ratio between two different scopes and is clamped at 1.0. Read it as a
        smell rather than a measurement: a page whose value pins at 1.0 is
        mostly anchors, and its extraction is worth looking at by hand.
        """
        if not self.text:
            return 0.0
        link_chars = sum(len(link.text) for link in self.links)
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
      * a start tag whose close tag is optional (`li`, `td`, `tr`, `dd`) closes
        the open one, and a block-level start tag closes an open `<p>`;
      * a `</x>` with no matching open tag is ignored rather than unwinding
        the stack (the single most common cause of truncated extractions);
      * a matching `</x>` closes every element opened inside it;
      * past `MAX_TREE_DEPTH` elements are attached but never opened, which
        bounds the recursion every later pass over the tree performs.
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
        if closes := IMPLICIT_CLOSE.get(tag):
            while len(self.stack) > 1 and self.current.tag in closes:
                self.stack.pop()
        elif tag in BLOCK_TAGS and self.current.tag == "p":
            self.stack.pop()
        node = Node(tag, attr_map)
        self.current.add(node)
        if len(self.stack) < MAX_TREE_DEPTH:
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


def _parse(html: str) -> _TreeBuilder:
    """Build a tree from `html`, keeping whatever survives a parse failure."""
    parser = _TreeBuilder()
    try:
        parser.feed(html)
        parser.close()
    except Exception:
        pass  # tolerant by design: keep whatever tree we managed to build
    return parser


def _has_ancestor(node: Node, tag: str) -> bool:
    parent = node.parent
    while parent is not None:
        if parent.tag == tag:
            return True
        parent = parent.parent
    return False


def _should_drop(node: Node, aggressive: bool) -> bool:
    if node.tag in DROP_TAGS:
        return True
    if node.tag == "title":
        # Already captured as metadata, and rendering it again puts the site
        # name in front of the body text of every short page.
        return True
    if node.attrs.get("hidden") is not None and node.attrs.get("hidden") != "false":
        return True
    if node.attrs.get("aria-hidden") == "true":
        return True
    if "display:none" in node.attrs.get("style", "").replace(" ", "").lower():
        return True
    if DROP_ROLES.intersection(node.attrs.get("role", "").lower().split()):
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


def _content_len(node: Node) -> float:
    """Text that is not link text - the quantity boilerplate is poor in."""
    return node.text_len() - 1.5 * node.link_text_len()


def _widen(node: Node) -> Node:
    """Climb out of a candidate whose parent carries strictly more prose.

    Scoring picks a single node, so a page whose paragraphs hang directly off
    `<body>` has no container to win with: the best-scoring node is one
    paragraph and the other nine are silently dropped. Climbing while the parent
    is richer in non-link text puts the siblings back, and stops as soon as what
    the parent adds is mostly anchors - which is exactly what a nav or a footer
    is. Erring this way keeps a footer; erring the other way loses the article.
    """
    best, score = node, _content_len(node)
    parent = node.parent
    # `<head>` is metadata, not prose: a stray string in it (the tail of a CSS
    # rule that closed early, say) must not drag the whole document in.
    while parent is not None and best.tag != "body":
        parent_score = _content_len(parent)
        if parent_score <= score:
            break
        best, score = parent, parent_score
        parent = parent.parent
    return best


def _find_main(root: Node) -> Node:
    """Pick the subtree most likely to be the article body.

    Semantic markup wins if it carries enough text. Otherwise score candidates
    by text length minus link text (boilerplate is mostly links), with a bonus
    for paragraph count and content-ish class names.
    """
    for node in root.iter_nodes():
        if node.tag == "main" or "main" in node.attrs.get("role", "").lower().split():
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
    return _widen(best)


def _render(node: Node, headings: list[tuple[int, str]], list_stack: tuple[str, ...] = ()) -> str:
    """Render a pruned subtree to markdown."""
    tag = node.tag
    if tag == "a":
        # Anchors are collected from the unpruned document elsewhere; here we
        # only need their text, on one line whatever they wrap.
        return _flat(node)

    if tag == "pre":
        body = _inline_text(node, preserve=True).strip("\n")
        lang = ""
        for n in node.iter_nodes():
            cls = n.attrs.get("class", "")
            if m := re.search(r"language-([A-Za-z0-9+#-]+)", cls):
                lang = m.group(1)
                break
        # The fence has to out-run any backtick run in the body, or a snippet
        # *about* markdown closes its own code block and the rest of the page
        # is parsed as code.
        longest = max((len(run) for run in _BACKTICKS_RE.findall(body)), default=0)
        fence = "`" * max(3, longest + 1)
        return f"\n\n{fence}{lang}\n{body}\n{fence}\n\n"

    if tag in HEADING_TAGS:
        text = _flat(node)
        if not text:
            return ""
        level = HEADING_TAGS[tag]
        headings.append((level, text))
        return f"\n\n{'#' * level} {text}\n\n"

    if tag == "li":
        marker = "1." if list_stack and list_stack[-1] == "ol" else "-"
        indent = "  " * max(0, len(list_stack) - 1)
        inner = "".join(
            _render(c, headings, list_stack) if isinstance(c, Node) else c
            for c in node.children
        )
        inner = re.sub(r"\n{2,}", "\n", inner).strip()
        return f"\n{indent}{marker} {inner}" if inner else ""

    if tag in ("ul", "ol"):
        inner = "".join(
            _render(c, headings, (*list_stack, tag)) if isinstance(c, Node) else c
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
        cells = [_flat(c) for c in node.children
                 if isinstance(c, Node) and c.tag in ("td", "th")]
        return "\n| " + " | ".join(cells) + " |" if cells else ""
    if tag == "table":
        inner = "".join(
            _render(c, headings, list_stack) if isinstance(c, Node) else ""
            for c in node.children
        )
        return f"\n\n{inner.strip()}\n\n"

    inner = "".join(
        _render(c, headings, list_stack) if isinstance(c, Node) else c
        for c in node.children
    )
    if tag in BLOCK_TAGS or tag == "[document]":
        return f"\n\n{inner.strip()}\n\n" if inner.strip() else ""
    return inner


_FENCE_RE = re.compile(r"^(`{3,})")
# Leading whitespace is load-bearing (it nests list items); only runs that
# follow real text are collapsed.
_INNER_RUN_RE = re.compile(r"(?<=\S)[ \t]{2,}")


def _tidy(markdown: str) -> str:
    """Normalise whitespace outside fenced code blocks.

    Code fences are left byte-for-byte: collapsing runs of spaces inside a
    Python snippet changes what the snippet means. Fences are tracked line by
    line rather than by splitting on ``` - a page that merely *mentions* a fence
    in prose would otherwise flip the parity and leave the whole rest of the
    document unnormalised.
    """
    out: list[str] = []
    fence = ""
    for raw in markdown.split("\n"):
        opener = _FENCE_RE.match(raw)
        if fence:
            out.append(raw)
            if opener and raw.strip() == fence:
                fence = ""
            continue
        if opener:
            fence = opener.group(1)
            out.append(raw.rstrip())
            continue
        line = _INNER_RUN_RE.sub(" ", raw.rstrip())
        if not line and out and not out[-1]:
            continue
        out.append(line)
    return "\n".join(out).strip()


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
        elif not preserve and c.tag in BLOCK_TAGS:
            # A block boundary is a word boundary: without this,
            # <blockquote><p>a</p><p>b</p></blockquote> reads as "ab".
            out.append(f"\n{_inline_text(c)}\n")
        else:
            out.append(_inline_text(c, preserve))
    joined = "".join(out)
    return joined if preserve else clean(joined)


def _flat(node: Node) -> str:
    """Inline text on a single line, for contexts where a newline is syntax."""
    return " ".join(_inline_text(node).split())


@dataclass(slots=True)
class _DocMeta:
    """Everything read from the document *before* boilerplate removal."""

    meta: dict[str, Any] = field(default_factory=dict)
    title: str = ""
    lang: str = ""
    canonical: str = ""
    published: str = ""
    jsonld: list[Any] = field(default_factory=list)
    base: str = ""


def _read_meta(node: Node, meta: dict[str, Any]) -> None:
    content = node.attrs.get("content", "").strip()
    charset = node.attrs.get("charset", "").strip()
    if not charset and node.attrs.get("http-equiv", "").strip().lower() == "content-type":
        if "charset=" in content.lower():
            charset = content.lower().split("charset=", 1)[1].split(";")[0].strip().strip('"')
    if charset:
        # Our caller decoded these bytes with the charset from the HTTP header
        # and cannot see what the document itself claims. Surfacing the claim is
        # the only way anyone ever explains a page full of U+FFFD.
        meta.setdefault("charset", charset.lower())
    name = (node.attrs.get("property") or node.attrs.get("name") or "").strip().lower()
    if name and content:
        # First tag wins, here and for title/canonical/base: a repeated meta at
        # the end of a hostile document must not overwrite the real one.
        meta.setdefault(name, content)


def _collect_meta(root: Node, raw_scripts: list[tuple[dict[str, str], str]],
                  url: str) -> _DocMeta:
    info = _DocMeta()
    canonical_href = ""

    for node in root.iter_nodes():
        tag = node.tag
        if tag == "html":
            if not info.lang:
                info.lang = node.attrs.get("lang", "").strip()
        elif tag == "base":
            if not info.base:
                href = node.attrs.get("href", "").strip()
                resolved = urljoin(url, href) if href else ""
                # A `<base>` we cannot fetch (javascript:, about:) would poison
                # every relative link on the page, so it is simply not a base.
                if resolved.startswith(("http://", "https://")):
                    info.base = resolved
        elif tag == "title":
            # `<svg><title>` names an icon; it is not the name of the page.
            if not info.title and not _has_ancestor(node, "svg"):
                info.title = _flat(node)
        elif tag == "meta":
            _read_meta(node, info.meta)
        elif tag == "link":
            if not canonical_href and "canonical" in node.attrs.get("rel", "").lower().split():
                canonical_href = node.attrs.get("href", "").strip()
        elif tag == "time":
            if not info.published:
                info.published = node.attrs.get("datetime", "").strip()

    if canonical_href:
        # Resolved after the walk: `<base>` is allowed to appear after the link.
        info.canonical = urljoin(info.base or url, canonical_href)

    for attrs, body in raw_scripts:
        if "ld+json" in attrs.get("type", "").lower() and body.strip():
            try:
                info.jsonld.append(json.loads(body))
            except (ValueError, RecursionError):
                # RecursionError, not just JSONDecodeError: `[[[[...` a few
                # thousand deep is valid JSON that blows the C stack limit.
                continue

    info.title = info.meta.get("og:title") or info.title
    info.published = (
        info.meta.get("article:published_time") or info.meta.get("date")
        or info.meta.get("dc.date") or info.published
    )
    return info


def _collect_links(root: Node, base_url: str) -> list[Link]:
    """Every fetchable anchor in the document, in document order, deduplicated."""
    links: list[Link] = []
    seen: set[str] = set()
    for node in root.iter_nodes():
        if node.tag != "a":
            continue
        href = node.attrs.get("href", "").strip()
        if not href or href.lower().startswith(SKIP_HREF_PREFIXES):
            continue
        absolute = urljoin(base_url, href)
        # The scheme check is the real gate: urljoin resolves `file:` and
        # `ftp:` happily, and a redirect-chasing crawler must never see them.
        if not absolute.startswith(("http://", "https://")) or absolute in seen:
            continue
        seen.add(absolute)
        rel = node.attrs.get("rel", "").lower()
        links.append(Link(absolute, _flat(node), rel, "nofollow" in rel.split()))
    return links


def _build(root: Node, url: str, info: _DocMeta, links: list[Link],
           aggressive: bool) -> ExtractedPage:
    """Prune, pick the article, render. `root` is consumed (pruned in place)."""
    _prune(root, aggressive)
    main = _find_main(root)
    headings: list[tuple[int, str]] = []
    markdown = _tidy(_render(main, headings))
    text = clean(_HEADING_MARK_RE.sub("", markdown))
    return ExtractedPage(
        url=url, title=info.title, text=text, markdown=markdown, links=list(links),
        headings=headings, meta=info.meta, lang=info.lang, canonical=info.canonical,
        published=info.published, jsonld=info.jsonld,
    )


def extract(html: str, url: str = "", *, aggressive: bool = True,
            min_words: int = 25) -> ExtractedPage:
    """Extract clean markdown, links and metadata from an HTML document.

    If aggressive boilerplate removal leaves too little text (a page that *is*
    a nav list, or one whose article is wrapped in a `class="sidebar"` div),
    we retry conservatively rather than return an empty page.
    """
    # A byte-order mark survives decoding as U+FEFF, where it sits in front of
    # the doctype and is content rather than markup.
    html = html.lstrip("\ufeff")
    doc = _parse(html)
    info = _collect_meta(doc.root, doc.raw_scripts, url)
    # Links come from the whole document and before pruning: a crawler needs the
    # nav we are about to throw away in order to find the next page.
    links = _collect_links(doc.root, info.base or url or info.canonical)

    try:
        page = _build(doc.root, url, info, links, aggressive)
        if aggressive and len(page.text.split()) < min_words:
            # The pruned tree is gone by now, so the conservative pass reparses.
            # A second parse is cheaper than deep-copying a hostile tree.
            fallback = _build(_parse(html).root, url, info, links, False)
            if len(fallback.text.split()) > len(page.text.split()):
                return fallback
        return page
    except Exception:
        # Rendering is best effort. A document that defeats it still has a
        # title, a canonical and its links, and a nightly job that returns those
        # beats one that dies on a single adversarial page.
        return ExtractedPage(
            url=url, title=info.title, text="", markdown="", links=list(links),
            meta=info.meta, lang=info.lang, canonical=info.canonical,
            published=info.published, jsonld=info.jsonld,
        )
