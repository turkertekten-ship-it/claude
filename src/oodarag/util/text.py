"""Text normalization, tokenization and structure parsing.

Everything here is deterministic and language-agnostic enough for the mixed
corpus this pipeline targets: prose (video transcripts), markdown (docs), code
(GitHub), and dialogue (chat transcripts).
"""

from __future__ import annotations

import re
import unicodedata

# Words, numbers, and code identifiers. Keeps `snake_case` and `dotted.paths`
# together as single tokens, which matters a lot when the corpus is half code.
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+(?:[.\-/][A-Za-z0-9_]+)*")
_WS_RE = re.compile(r"[ \t\f\v]+")
_MULTI_NL_RE = re.compile(r"\n{3,}")
_SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])|\n{2,}")
_MD_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"^```")

STOPWORDS = frozenset(
    """
    a an the and or but if then than so because as of at by for with about into
    over after before between out against during without within along across
    to from in on off up down is are was were be been being am do does did doing
    have has had having i you he she it we they them his her its our their this
    that these those there here what which who whom how when where why not no
    can will just should now also very much more most other some such only own
    same too s t don t re ve ll d m o y
    """.split()
)


def normalize_unicode(text: str) -> str:
    """NFKC-fold and strip control characters, preserving newlines and tabs."""
    text = unicodedata.normalize("NFKC", text)
    # A carriage return is a line break, not a character to delete. It was being
    # dropped here - `\r` is category Cc - and this runs *before*
    # `normalize_whitespace`, whose own `\r` handling therefore never saw one.
    # On a `\r`-only transcript (classic Mac exports, terminal captures) the
    # lines either side were glued: "Done.\rNext" became "Done.Next", which
    # `tokenize` reads as the single token "done.next" because the tokenizer
    # deliberately keeps dotted paths together. Neither "done" nor "next" is
    # then in the index, so the passage cannot be retrieved by either word.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return "".join(ch for ch in text if ch in "\n\t" or not unicodedata.category(ch).startswith("C"))


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS_RE.sub(" ", text)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def clean(text: str) -> str:
    return normalize_whitespace(normalize_unicode(text))


def tokenize(text: str) -> list[str]:
    """Lowercased content tokens, stopwords removed, single characters dropped."""
    return [
        t
        for t in (m.group(0).lower() for m in _TOKEN_RE.finditer(text))
        if len(t) > 1 and t not in STOPWORDS
    ]


def tokenize_all(text: str) -> list[str]:
    """Every token, including stopwords - used for phrase-level matching."""
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def char_ngrams(token: str, n: int = 4) -> list[str]:
    """Character n-grams of a padded token; gives the embedder subword robustness
    so `chunking` and `chunked` land near each other without a learned model."""
    if len(token) <= n:
        return [f"^{token}$"]
    padded = f"^{token}$"
    return [padded[i : i + n] for i in range(len(padded) - n + 1)]


def split_sentences(text: str) -> list[str]:
    parts = [p.strip() for p in _SENT_RE.split(text) if p and p.strip()]
    return parts or ([text.strip()] if text.strip() else [])


def estimate_tokens(text: str) -> int:
    """Cheap token estimate (~4 chars/token for English, ~3 for code).

    Deliberately an estimate: importing a real tokenizer would break the
    zero-dependency promise, and every budget in this pipeline is a soft budget
    with headroom. See docs/adr/0001-zero-dependency-core.md.
    """
    if not text:
        return 0
    words = text.count(" ") + text.count("\n") + 1
    return max(words, len(text) // 4)


def truncate_tokens(text: str, max_tokens: int) -> str:
    """Cut `text` down to at most `max_tokens`, measured by `estimate_tokens`.

    The postcondition is the point: whatever comes back estimates at or under
    the budget it was given.
    """
    if max_tokens <= 0:
        return ""
    if estimate_tokens(text) <= max_tokens:
        return text
    # The estimate is max(separators + 1, chars / 4), so cutting on characters
    # alone only satisfies one of its two arms. On separator-dense text - a
    # transcript with one word per line, which is one of the corpora this
    # package targets - `truncate_tokens(t, 10)` returned a string estimating
    # 22 tokens, so a caller sizing a model context by these functions overran
    # it by more than 2x on exactly the input it was budgeting for.
    budget = max_tokens - 1  # the " ..." marker costs one separator
    cut = text[: budget * 4]
    separators = 0
    for i, ch in enumerate(cut):
        if ch in " \n":
            separators += 1
            if separators >= budget:
                cut = cut[:i]
                break
    head = cut.rsplit(" ", 1)[0] if " " in cut else cut
    return f"{head} ..." if head else "..."


def _fence_spans(text: str) -> list[tuple[int, int]]:
    """Character ranges covered by fenced code blocks, fence lines included.

    An unclosed fence runs to the end of the document - the same assumption
    `split_markdown_sections` makes when it stops emitting boundaries.
    """
    spans: list[tuple[int, int]] = []
    start: int | None = None
    offset = 0
    for line in text.split("\n"):
        if _CODE_FENCE_RE.match(line):
            if start is None:
                start = offset
            else:
                spans.append((start, offset + len(line) + 1))
                start = None
        offset += len(line) + 1
    if start is not None:
        spans.append((start, offset))
    return spans


def heading_path(markdown: str, offset: int) -> list[str]:
    """The chain of markdown headings in effect at a character offset."""
    # A `#` line inside a fenced code block is a comment, not a heading.
    # `split_markdown_sections` already knew that when choosing its boundaries;
    # this function did not, so a shell block containing `# install deps` was
    # read as a level-1 heading, which cleared the real chain and relabelled
    # every section after the fence. The path is what goes into a chunk's
    # context header, which is embedded and indexed, so the retriever ended up
    # citing a section the document does not contain.
    fences = _fence_spans(markdown)
    path: list[str] = []
    for m in _MD_HEADING_RE.finditer(markdown):
        if m.start() > offset:
            break
        if any(lo <= m.start() < hi for lo, hi in fences):
            continue
        level = len(m.group(1))
        del path[level - 1 :]
        path.append(m.group(2).strip())
    return path


def split_markdown_sections(text: str) -> list[tuple[list[str], str, int]]:
    """Split markdown into (heading_path, body, char_offset) sections.

    Fenced code blocks are never split across sections - a heading-looking line
    inside a fence is just a comment.
    """
    lines = text.split("\n")
    in_fence = False
    boundaries: list[int] = []
    offset = 0
    offsets: list[int] = []
    for line in lines:
        offsets.append(offset)
        offset += len(line) + 1
    for idx, line in enumerate(lines):
        if _CODE_FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence and _MD_HEADING_RE.match(line):
            boundaries.append(idx)
    if not boundaries or boundaries[0] != 0:
        boundaries.insert(0, 0)
    sections: list[tuple[list[str], str, int]] = []
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(lines)
        body = "\n".join(lines[start:end]).strip()
        if body:
            sections.append((heading_path(text, offsets[start]), body, offsets[start]))
    return sections


def summarize(text: str, max_chars: int = 240) -> str:
    """First-sentence summary used for context headers and previews."""
    flat = " ".join(clean(text).split())
    if len(flat) <= max_chars:
        return flat
    cut = flat[:max_chars]
    return cut.rsplit(" ", 1)[0] + "..."


def redact_secrets(text: str) -> str:
    """Strip credential-shaped strings before anything is written to an index.

    The chat and GitHub connectors read material that can contain live tokens;
    an index is a file that gets copied around, so it must never carry them.
    """
    patterns = [
        (r"\b(gh[pousr]_[A-Za-z0-9]{16,})", "<redacted:github-token>"),
        (r"\b(sk-ant-[A-Za-z0-9_\-]{16,})", "<redacted:anthropic-key>"),
        (r"\b(sk-[A-Za-z0-9]{32,})", "<redacted:api-key>"),
        (r"\b(AKIA[0-9A-Z]{16})\b", "<redacted:aws-key-id>"),
        (r"\b(xox[abposr]-[A-Za-z0-9\-]{10,})", "<redacted:slack-token>"),
        (r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]{20,}", r"\1 <redacted>"),
        (
            # The optional quote after the key name is not cosmetic. Without it
            # the separator had to follow the word immediately, so `password =
            # hunter2hunter2` was redacted but `{"password": "hunter2hunter2"}`
            # was not - and a JSON config blob is the single most common shape a
            # credential is leaked in, in the chat logs and repository files
            # these connectors read straight into the index.
            r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b([\"']?\s*[:=]\s*)"
            r"[\"']?[A-Za-z0-9._\-]{12,}[\"']?",
            r"\1\2<redacted>",
        ),
        (r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
         "<redacted:private-key>"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text
