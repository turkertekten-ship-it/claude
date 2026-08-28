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
        # Specific formats first, so the marker names the credential that leaked.
        # Every entry here is a *prefixed* format: a vendor that publishes a
        # recognizable prefix is one we can match without guessing, which is why
        # this table grows by prefix rather than by entropy heuristics.
        (r"\b(gh[pousr]_[A-Za-z0-9]{16,})", "<redacted:github-token>"),
        # Fine-grained PATs. A separate entry because the underscore-separated
        # body does not match the classic pattern above, and a format shipping
        # after this table was written is the normal way a redactor goes stale.
        (r"\b(github_pat_[A-Za-z0-9_]{20,})", "<redacted:github-token>"),
        (r"\b(sk-ant-[A-Za-z0-9_\-]{16,})", "<redacted:anthropic-key>"),
        (r"\b(AIza[0-9A-Za-z_\-]{35,})", "<redacted:google-api-key>"),
        (r"\b([sprk]k_(?:live|test)_[A-Za-z0-9]{16,})", "<redacted:stripe-key>"),
        (r"\b(npm_[A-Za-z0-9]{30,})", "<redacted:npm-token>"),
        (r"\b(pypi-[A-Za-z0-9_\-]{16,})", "<redacted:pypi-token>"),
        (r"\b(eyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,})",
         "<redacted:jwt>"),
        # Hyphens and underscores are inside the class: "sk-proj-..." is the
        # common OpenAI form and a class of bare alphanumerics stops at the
        # first hyphen, leaving the secret half of the string in the clear.
        (r"\b(sk-[A-Za-z0-9_\-]{24,})", "<redacted:api-key>"),
        (r"\b(AKIA[0-9A-Z]{16})\b", "<redacted:aws-key-id>"),
        (r"\b(x(?:ox[abposr]|app)-[A-Za-z0-9\-]{10,})", "<redacted:slack-token>"),
        (r"(?i)\b(bearer)\s+[A-Za-z0-9._\-]{20,}", r"\1 <redacted>"),
        # Backstop for formats with no recognizable prefix. Applied last, and
        # separately below, because it needs to look at what it captured: an
        # unquoted right-hand side that is just a Python identifier is a
        # variable reference, not a secret. Without that check, ordinary source
        # code like `token = self.agent_token` reads as a credential, and a
        # rule that reports a critical finding on every such line is a rule
        # nobody keeps switched on.
        (r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----",
         "<redacted:private-key>"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    return _ASSIGNMENT_RE.sub(_redact_assignment, text)


#: `name = value` where the name suggests a credential. The value is checked by
#: `_redact_assignment` rather than by the pattern, because whether it is a
#: secret depends on what it looks like, not on where it sits.
_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|passwd|token)\b(\s*[:=]\s*)"
    r"([\"']?)([A-Za-z0-9._\-]{12,})(\3)"
)

#: A dotted attribute access: `self.agent_token`, `os.environ`, `cfg.db.pw`.
#: Never a credential; always a reference to where one lives.
_ATTRIBUTE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")

#: A bare identifier carrying no digits: `agent_token`, `password`. Real
#: credentials in the wild are mixed-case or contain digits; a digit-free
#: snake_case word after `token =` is a variable name.
_PLAIN_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z_]*$")


def _looks_like_a_reference(value: str) -> bool:
    return bool(_ATTRIBUTE_RE.match(value) or _PLAIN_NAME_RE.match(value))


def _redact_assignment(match: re.Match[str]) -> str:
    """Redact unless the right-hand side is plainly a variable, not a value.

    Quoted values are always redacted: nobody writes `token = "agent_token"`
    meaning a reference. Unquoted ones are judged on shape, and ties go to
    redaction - a needlessly redacted variable name costs a moment of
    confusion, a missed credential costs the credential.
    """
    name, sep, quote, value, _close = match.groups()
    if not quote and _looks_like_a_reference(value):
        return match.group(0)
    return f"{name}{sep}{quote}<redacted>{quote}"
