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
    return "".join(ch for ch in text if ch in "\n\t" or not unicodedata.category(ch).startswith("C"))


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS_RE.sub(" ", text)
    text = _MULTI_NL_RE.sub("\n\n", text)
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def clean(text: str) -> str:
    return normalize_whitespace(normalize_unicode(text))


def tokenize(text: str, stem_words: bool = False) -> list[str]:
    """Lowercased content tokens, stopwords removed, single characters dropped.

    `stem_words=True` applies Porter stemming, matching what the FTS5 index
    does. Any stage that compares text against the lexical index must use it -
    see util/stemming.py for what happens when two stages disagree.
    """
    tokens = [
        t
        for t in (m.group(0).lower() for m in _TOKEN_RE.finditer(text))
        if len(t) > 1 and t not in STOPWORDS
    ]
    if not stem_words:
        return tokens
    from oodarag.util.stemming import stem

    return [stem(t) for t in tokens]


_COMPOUND_SEP_RE = re.compile(r"[.\-/]")


def is_compound(token: str) -> bool:
    """True when `_TOKEN_RE` glued this token together across `.`, `-` or `/`.

    FTS5's unicode61 treats all three as separators, so a compound is one term
    here and several there. Anything comparing tokens against the lexical index
    needs to know which side of that difference it is on.
    """
    return bool(_COMPOUND_SEP_RE.search(token))


def expand_compounds(tokens: list[str], stem_words: bool = False) -> list[str]:
    """The tokens, plus the parts of any compound among them.

    `_TOKEN_RE` deliberately keeps `snake_case`, `dotted.paths` and hyphenated
    words whole, because half this corpus is code and `oodarag.util.text` is one
    identifier rather than three words. That is right for the token *sequence*,
    which phrase scoring reads, and wrong for token *membership*, which coverage,
    IDF and the lexical query read - because FTS5's unicode61 tokenizer treats
    `.`, `-` and `/` as separators, so the lexical arm has always matched a
    quoted "in-process" against a document saying "in process" while the
    reranker scored that same document as containing neither. The lexical arm
    retrieved the chunk and the reranker then judged the query's most
    informative term absent, which is the disagreement this repairs.

    The compound is kept as well as split: dropping it would lose the exact-
    identifier match that the atomic form exists to provide.
    """
    expanded = list(tokens)
    seen = set(tokens)
    for token in tokens:
        if not _COMPOUND_SEP_RE.search(token):
            continue
        for part in _COMPOUND_SEP_RE.split(token):
            if len(part) < 2 or part in STOPWORDS:
                continue
            if stem_words:
                from oodarag.util.stemming import stem

                part = stem(part)
                if len(part) < 2 or part in STOPWORDS:
                    continue
            if part not in seen:
                seen.add(part)
                expanded.append(part)
    return expanded


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
    if estimate_tokens(text) <= max_tokens:
        return text
    return text[: max_tokens * 4].rsplit(" ", 1)[0] + " ..."


def heading_path(markdown: str, offset: int) -> list[str]:
    """The chain of markdown headings in effect at a character offset."""
    path: list[str] = []
    for m in _MD_HEADING_RE.finditer(markdown):
        if m.start() > offset:
            break
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
            # `\b` before the keyword would not match GITHUB_TOKEN= or
            # DB_PASSWORD=, because `_` is a word character and so presents no
            # boundary. Real configuration uses prefixed names almost
            # exclusively, so the naive form silently redacted nothing that
            # mattered. The value class is widened too: a password containing
            # @ or ! is still a password.
            r"(?i)(?<![A-Za-z0-9])[A-Za-z0-9_.\-]*"
            r"(api[_-]?key|secret|password|passwd|token|credential)"
            # (?!<redacted) so a value already replaced by a more specific rule
            # above is left alone - otherwise the generic rule overwrites
            # <redacted:github-token> with a vaguer marker and the report loses
            # which kind of credential was found.
            r"(\s*[:=]\s*)[\"']?(?!<redacted)[^\s\"']{8,}[\"']?",
            r"<redacted:\1>",
        ),
        (r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
         "<redacted:private-key>"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return text
