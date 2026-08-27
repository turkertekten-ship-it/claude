"""Is every figure this repository states in prose traceable to its own code?

Prose is where numbers go to be believed. A sentence that says a queue drains at
five thousand an hour, that a buffer is eight mebibytes, or that a retrieval step
keeps the top five candidates reads as *measured* whether or not anybody measured
anything: precision is itself an implicit claim of provenance, and a reader has
no way to tell a figure that came from a constant in the code from one that came
from a plausible guess made while writing the sentence.

So this checker asks the narrowest question the repository can answer about
itself: does any literal in the Python source equal the stated figure? It
normalises the ways one quantity gets written on the two sides - digit grouping
in prose against underscores in a literal, a unit against the product of powers
of two that expands it, a percentage against the fraction - and it looks in the
module the sentence lives in before the rest of the tree, because a docstring's
figures nearly always come from the constants sitting beside it.

Everything else here exists to keep it quiet, and the admission test is where
most of that happens. A *figure* is a number that names its own dimension - a
unit, a scale word, a rate - or one that is the tail of a hyphenated name, the
`top-5` shape that reads as a tuned parameter. A number whose dimension is
merely the English noun beside it is a count, and this checker has no vocabulary
for counting: "sixteen Python files", "the other three thousand nine hundred and
ninety-nine", "a report where nine hundred lines of noise hide four real
problems" are all numbers nobody could trace to a constant, two of them are not
even assertions about this system, and reporting them is how a review tool
teaches its reader to skim past it.

The rules below the admission test reject the rest: years, version pins, section
and status numbers, digits welded into a name, and figures that already carry a
provenance tag and so have named their source without needing one in the code.
The trade throughout is deliberate. A missed figure costs one unbacked sentence;
a page of false positives costs the whole check, because that is the point at
which somebody switches it off and it catches nothing at all.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterator

from tools.claims import RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

#: How many of the searched files are named in the absence evidence. The full
#: count travels in the summary, so truncating the list loses nothing a reader
#: needs - and an absence record naming two hundred files is one nobody reads.
SEARCH_SAMPLE = 8

#: Units and scale words a figure may carry. Sorted longest-first when the
#: pattern is built, so `seconds` wins over `sec` over `s`: leftmost-first
#: alternation would otherwise read "5 seconds" as five of something called `s`.
_UNIT_WORDS: tuple[str, ...] = (
    "MiB", "KiB", "GiB", "TiB", "MB", "KB", "GB", "TB",
    "bytes", "byte", "bits", "bit",
    "ms", "seconds", "second", "secs", "sec",
    "minutes", "minute", "mins", "min",
    "hours", "hour", "hrs", "hr", "days", "day",
    "rps", "qps", "chars", "char", "tokens", "token", "pages", "page",
    "s", "b", "x", "k", "m",
)
#: Rates, which attach without a space: `5,000/hour`.
_RATE_WORDS: tuple[str, ...] = (
    "/hour", "/hours", "/second", "/seconds", "/sec", "/day", "/min", "/s", "/h",
)


def _longest_first(words: tuple[str, ...]) -> str:
    return "|".join(re.escape(w) for w in sorted(words, key=len, reverse=True))


#: A number as prose writes one: optional comma grouping, optional decimal part.
#: The lookbehind is doing most of the work in this module. A digit preceded by a
#: word character is inside a name - `BM25`, `blake2b`, `sha256`, `base64`,
#: `py311`, `h1` - and a name is not a quantity; a digit preceded by a dot is the
#: tail of a dotted number whose head was already matched.
_NUMBER_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)")

#: Matched immediately after a number, never searched for on its own.
_UNIT_AT_RE = re.compile(
    r"[ \t]?(?:%|" + _longest_first(_RATE_WORDS)
    + r"|(?:" + _longest_first(_UNIT_WORDS) + r")(?![A-Za-z0-9_]))",
    re.IGNORECASE,
)

#: Digit runs inside a string literal in code, so `"5,000/hour"` in a constant
#: counts as the source of the same figure in a sentence.
_DIGITS_RE = re.compile(r"\d[\d_,]*(?:\.\d+)?")

#: Tokens in code that contain a digit. Used only to answer "is this hyphenated
#: thing a name?" - `utf-8` and `top-5` are the same shape, and the only honest
#: way to tell them apart is that one of them is written in the code and the
#: other is not.
_CODE_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]*")

#: Spans that contain digits but assert nothing numeric. They are blanked before
#: scanning rather than filtered afterwards, because the point is that the digits
#: inside them were never a figure: a date is not twenty-seven of anything, an
#: issue reference is not a count, and a document's name is not a measurement.
_MASKS: tuple[re.Pattern[str], ...] = (
    re.compile(r"https?://\S+"),
    re.compile(r"\]\([^)\s]*\)"),                       # markdown link target
    re.compile(r"\d{4}-\d{2}-\d{2}"),                   # ISO date
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),        # clock time
    re.compile(r"\bv?\d+(?:\.\d+){2,}"),                # semver-shaped
    re.compile(r"\bv\d+(?:\.\d+)*\b", re.IGNORECASE),   # v2, v2.1
    re.compile(r"\bpy(?:thon)?\s*v?\d+(?:\.\d+)*", re.IGNORECASE),
    re.compile(r"#\d+"),                                # issue reference
    re.compile(
        r"(?:\b(?:ADR|RFC|PEP|ISO|IEEE|BCP|STD|CVE|section|chapter|appendix"
        r"|figure|table|step|item|rule|part|no\.)|§)\s*#?\s*\d+",
        re.IGNORECASE,
    ),
    # A standard's name, hyphenated. ISO-8601, SHA-256, RFC-7231, UTF-16, X-509
    # all match the `top-5` admission rule below - a trailing number turning a
    # word into a setting - and were read as tuned parameters whose value the
    # source ought to contain. They are names, and the number is part of the
    # name; requiring the code to contain 8601 for the word ISO-8601 is the
    # checker demanding evidence for a spelling.
    re.compile(r"\b(?:[A-Z]{2,}|[A-Z]-?[A-Z]*)\-\d+(?:-\d+)?\b"),
)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_TOC_TITLE_RE = re.compile(r"^(?:table of )?contents\b|^toc\b|^index$|^on this page\b")
#: A bullet that is nothing but a link to an anchor on the same page.
_ANCHOR_ONLY_RE = re.compile(r"^\[[^\]]*\]\(#[^)]*\)$")

#: A version pin is a name for a release, not a quantity, and the word itself is
#: the most reliable marker of one that survives every spelling of the number.
_VERSION_RE = re.compile(r"\bversions?\b", re.IGNORECASE)

#: Cues that make a three-digit number a status code rather than a count.
_STATUS_RE = re.compile(r"\bhttps?\b|\bstatus\b|\bcodes?\b|\bresponses?\b", re.IGNORECASE)

#: A claim that already cites its source. This repository's doctrine is that a
#: factual claim carries a `[src:ID]` tag resolving to `provenance/sources.yaml`,
#: so a tagged figure has answered this checker's question already - it is
#: traceable, just not to a literal. Whether the ID resolves is the `citations`
#: checker's question, and reporting the figure here would only double it.
_SOURCE_TAG_RE = re.compile(r"\[src:[^\]\s]+\]", re.IGNORECASE)


#: What a unit multiplies its number by. `KB`/`MB`/`GB` list both the decimal and
#: the binary expansion because code disagrees with itself about which one it
#: means, and this checker has no business picking a side: offering both can only
#: turn a finding into silence, never the reverse.
_MULTIPLY: dict[str, tuple[Decimal, ...]] = {
    "kib": (Decimal(1024),),
    "mib": (Decimal(1024) ** 2,),
    "gib": (Decimal(1024) ** 3,),
    "tib": (Decimal(1024) ** 4,),
    "kb": (Decimal(1000), Decimal(1024)),
    "mb": (Decimal(1000) ** 2, Decimal(1024) ** 2),
    "gb": (Decimal(1000) ** 3, Decimal(1024) ** 3),
    "tb": (Decimal(1000) ** 4, Decimal(1024) ** 4),
    "k": (Decimal(1000),),
    "m": (Decimal(1000) ** 2,),
    "s": (Decimal(1000),),
    "sec": (Decimal(1000),),
    "secs": (Decimal(1000),),
    "second": (Decimal(1000),),
    "seconds": (Decimal(1000),),
    "min": (Decimal(60), Decimal(60_000)),
    "mins": (Decimal(60), Decimal(60_000)),
    "minute": (Decimal(60), Decimal(60_000)),
    "minutes": (Decimal(60), Decimal(60_000)),
    "hr": (Decimal(60), Decimal(3600)),
    "hrs": (Decimal(60), Decimal(3600)),
    "hour": (Decimal(60), Decimal(3600)),
    "hours": (Decimal(60), Decimal(3600)),
    "day": (Decimal(24), Decimal(86_400)),
    "days": (Decimal(24), Decimal(86_400)),
}
#: A percentage in prose is routinely a fraction in code.
_DIVIDE: dict[str, tuple[Decimal, ...]] = {"%": (Decimal(100),)}


# ----------------------------------------------------------------- normalising


def _decimal(text: str) -> Decimal | None:
    """`400,000`, `400_000` and `400000` are one number written three ways."""
    try:
        return Decimal(text.replace(",", "").replace("_", ""))
    except InvalidOperation:
        return None


def _key(value: Decimal) -> str:
    """One spelling per value, so `5000`, `5E+3` and `5000.0` compare equal."""
    try:
        text = format(value.normalize(), "f")
    except (InvalidOperation, ValueError):
        return str(value)
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _candidates(value: Decimal, unit: str) -> frozenset[str]:
    keys = {_key(value)}
    for factor in _MULTIPLY.get(unit, ()):
        keys.add(_key(value * factor))
    for divisor in _DIVIDE.get(unit, ()):
        try:
            keys.add(_key(value / divisor))
        except (InvalidOperation, ZeroDivisionError):
            continue
    return frozenset(keys)


# --------------------------------------------------------------- the code side


def _fold(node: ast.AST) -> Decimal | None:
    """Evaluate the one expression shape a size constant is written in.

    `8 * 1024 * 1024` is the same assertion as `8388608`, and a checker that only
    reads bare literals reports the sentence describing it as unsourced. Only
    multiplication and exponentiation of integer literals are folded: anything
    that reaches a name is a value this checker cannot know without running the
    module, and running the module is not something a review tool gets to do.
    """
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, int):
            return None
        return Decimal(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _fold(node.operand)
        return None if inner is None else -inner
    if isinstance(node, ast.BinOp):
        left, right = _fold(node.left), _fold(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Mult):
            return left * right
        # Bounded: an unbounded exponent is a denial-of-service dressed as a
        # constant, and no size in a docstring needs more than this.
        if isinstance(node.op, ast.Pow) and 0 <= right <= 64 and right == right.to_integral_value():
            return left ** int(right)
    return None


def _docstring_nodes(tree: ast.AST) -> set[int]:
    """Docstrings, so their digits are not mistaken for the code's own.

    A docstring is a string literal to `ast` and prose to a reader. Harvesting it
    as supporting evidence would let a sentence cite itself, which is exactly the
    circularity this checker exists to detect.
    """
    out: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        first = node.body[0] if node.body else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            if isinstance(first.value.value, str):
                out.add(id(first.value))
    return out


def _literals(source: SourceFile) -> frozenset[str]:
    try:
        tree = ast.parse(source.text)
    except SyntaxError:
        return frozenset()  # unparseable: contributes nothing rather than guesses
    prose = _docstring_nodes(tree)
    keys: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp):
            folded = _fold(node)
            if folded is not None:
                keys.add(_key(folded))
            continue
        if not isinstance(node, ast.Constant):
            continue
        value = node.value
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            keys.add(_key(Decimal(value)))
        elif isinstance(value, float):
            keys.add(_key(Decimal(str(value))))
        elif isinstance(value, str) and id(node) not in prose:
            for run in _DIGITS_RE.findall(value):
                parsed = _decimal(run)
                if parsed is not None:
                    keys.add(_key(parsed))
    return frozenset(keys)


@dataclass(slots=True)
class _CodeIndex:
    """Every numeric literal in the Python sources, per file, plus their names."""

    per_file: dict[str, frozenset[str]]
    files: tuple[str, ...]
    tokens: frozenset[str]

    @classmethod
    def of(cls, repo: RepoIndex) -> _CodeIndex:
        per_file: dict[str, frozenset[str]] = {}
        tokens: set[str] = set()
        for source in repo.python:
            per_file[source.rel] = _literals(source)
            tokens.update(
                token.lower()
                for token in _CODE_TOKEN_RE.findall(source.text)
                if any(ch.isdigit() for ch in token)
            )
        return cls(per_file, tuple(sorted(per_file)), frozenset(tokens))

    def supports(self, keys: frozenset[str], citing: str) -> bool:
        """The citing module first: a docstring's figures come from beside it."""
        own = self.per_file.get(citing)
        if own is not None and own & keys:
            return True
        return any(
            self.per_file[rel] & keys for rel in self.files if rel != citing
        )


# -------------------------------------------------------------- the prose side


@dataclass(frozen=True, slots=True)
class _Mention:
    """One figure as it was written, with every value it could be asserting."""

    text: str            # verbatim, e.g. "5,000/hour"
    unit: str            # normalised, "" when the number stands alone
    keys: frozenset[str]


def _masked(text: str) -> str:
    out = list(text)
    for pattern in _MASKS:
        for match in pattern.finditer(text):
            for index in range(match.start(), match.end()):
                out[index] = "\x00"
    return "".join(out)


def _token_around(text: str, start: int, end: int) -> str:
    """The hyphen-joined word a number sits in, if it sits in one."""
    left, right = start, end
    while left > 0 and (text[left - 1].isalnum() or text[left - 1] in "_-"):
        left -= 1
    while right < len(text) and (text[right].isalnum() or text[right] in "_-"):
        right += 1
    return text[left:right]


def _is_hyphen_tail(text: str, start: int) -> bool:
    """Is this the number in `top-5` - a name whose last part is the value?

    A trailing number turns a word into a setting: `top-5`, `n-3`, `stage-2`.
    The mirror image, a number leading a compound, is the opposite - "a
    4,000-file repository" counts a hypothetical, it does not configure
    anything - which is why only this side is admitted.
    """
    return start >= 2 and text[start - 1] == "-" and text[start - 2].isalpha()


def _carries_source(source: SourceFile, line: int) -> bool:
    """Does the sentence at `line` cite a source, here or on the line it wraps to?

    Markdown wraps, and a citation trails the clause it belongs to, so the tag
    for a figure routinely lands at the start of the next line. Reading only the
    claim's own line would report exactly the sentences that did the right thing.
    """
    return any(
        _SOURCE_TAG_RE.search(source.line_text(candidate))
        for candidate in (line, line + 1)
    )


def _fenced_lines(source: SourceFile) -> frozenset[int]:
    """Lines inside a fence, in markdown *and* in a docstring that shows code."""
    out: set[int] = set()
    for fence in source.fences():
        span = len(fence.body.split("\n")) if fence.body else 0
        out.update(range(fence.start_line - 1, fence.start_line + span + 1))
    return frozenset(out)


def _toc_lines(source: SourceFile) -> frozenset[int]:
    """Lines under a "Contents" heading, up to the next heading of its level.

    A table of contents restates the headings below it, so its numbers are
    already excluded once as headings; catching them here as well is what stops
    the restatement from being read as a fresh assertion.
    """
    if not source.is_markdown:
        return frozenset()
    out: set[int] = set()
    active = False
    depth = 0
    for lineno, raw in enumerate(source.lines, start=1):
        heading = _HEADING_RE.match(raw.strip())
        if heading:
            level = len(heading.group(1))
            if _TOC_TITLE_RE.search(heading.group(2).strip().lower()):
                active, depth = True, level
            elif active and level <= depth:
                active = False
            continue
        if active:
            out.add(lineno)
    return frozenset(out)


def _skip_claim(claim: Claim, source: SourceFile, fenced: frozenset[int],
                toc: frozenset[int]) -> bool:
    raw = source.line_text(claim.line)
    if claim.kind == "heading":
        return True
    if claim.line in fenced or claim.line in toc:
        return True
    if _ANCHOR_ONLY_RE.match(claim.text.strip()):
        return True
    if raw.lstrip().startswith((">>>", "...")):
        return True  # a doctest is code that happens to be indented into prose
    if _VERSION_RE.search(claim.text) or _VERSION_RE.search(raw):
        return True
    if _carries_source(source, claim.line):
        return True
    # "5" alone in a table cell asserts nothing on its own; the assertion, if
    # there is one, is in the row header this checker cannot reliably read.
    return not any(ch.isalpha() for ch in claim.text)


def _mentions(claim: Claim, source: SourceFile, tokens: frozenset[str]) -> list[_Mention]:
    text = claim.text
    raw = source.line_text(claim.line)
    status_context = _STATUS_RE.search(raw) is not None
    out: list[_Mention] = []

    for match in _NUMBER_RE.finditer(_masked(text)):
        digits = match.group(1)
        value = _decimal(digits)
        if value is None:
            continue
        unit_match = _UNIT_AT_RE.match(text, match.end())
        unit = unit_match.group(0).strip().lower() if unit_match else ""
        end = unit_match.end() if unit_match else match.end()

        # The admission test. Without a dimension of its own a number is a count
        # of whatever noun follows it, and no literal in the tree can confirm or
        # deny a count - so the honest move is not to raise the subject.
        if not unit and not _is_hyphen_tail(text, match.start()):
            continue
        token = _token_around(text, match.start(), match.end())
        if any(ch.isalpha() for ch in token) and token.lower() in tokens:
            continue  # `utf-8` is a name the code already uses; `top-5` is not
        if digits.startswith("0") and len(digits) > 1 and "." not in digits:
            continue  # `run-007` is an identifier; quantities carry no padding
        integral = value == value.to_integral_value()
        if not unit and integral:
            if Decimal(1900) <= value <= Decimal(2100):
                continue  # a year
            if status_context and Decimal(100) <= value <= Decimal(599):
                continue  # an HTTP status code
        out.append(
            _Mention(text[match.start():end], unit, _candidates(value, unit))
        )
    return out


def _claims(repo: RepoIndex) -> Iterator[tuple[Claim, SourceFile]]:
    """Prose and docstrings, paired with the file they came from.

    Ordinary `#` comments are left out. They sit inside the code they describe,
    where a reader checks the figure against the line below it for free, and
    including them would double the volume of this check for the least
    load-bearing numbers in the repository.
    """
    for claim in repo.prose_claims():
        source = repo.get(claim.path)
        if source is not None:
            yield claim, source
    for claim in repo.comment_claims():
        if claim.kind != "docstring":
            continue
        source = repo.get(claim.path)
        if source is not None:
            yield claim, source


@dataclass
class NumbersChecker:
    name: str = "numbers"
    description: str = "Every figure stated in prose matches a literal in the code."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        index = _CodeIndex.of(repo)
        fenced: dict[str, frozenset[int]] = {}
        toc: dict[str, frozenset[int]] = {}
        seen: set[tuple[str, int, str]] = set()

        for claim, source in _claims(repo):
            if source.rel not in fenced:
                fenced[source.rel] = _fenced_lines(source)
                toc[source.rel] = _toc_lines(source)
            if _skip_claim(claim, source, fenced[source.rel], toc[source.rel]):
                continue

            for mention in _mentions(claim, source, index.tokens):
                key = (claim.path, claim.line, mention.text)
                if key in seen:
                    continue
                seen.add(key)

                if not index.files:
                    # Nothing to trace anything to. Saying so once beats either
                    # asserting the figures are fine or repeating this per line.
                    yield Finding(
                        checker=self.name,
                        code="NUMBER_UNSOURCED",
                        verdict=Verdict.UNVERIFIABLE,
                        severity=Severity.INFO,
                        claim=claim,
                        detail=(
                            "the repository has no Python sources, so there is no "
                            "literal any stated figure could be traced to"
                        ),
                    )
                    return

                if index.supports(mention.keys, claim.path):
                    continue

                yield Finding(
                    checker=self.name,
                    code="NUMBER_UNSOURCED",
                    verdict=Verdict.UNSUPPORTED,
                    severity=Severity.WARN,
                    claim=claim,
                    evidence=[
                        Evidence.at(
                            claim.path,
                            claim.line,
                            claim.text,
                            summary=f"{claim.path}:{claim.line} states {mention.text!r}",
                        ),
                        Evidence.absent(
                            f"no literal equal to {mention.text!r} "
                            f"({', '.join(sorted(mention.keys))}) in any of "
                            f"{len(index.files)} python files searched",
                            searched=index.files[:SEARCH_SAMPLE],
                        ),
                    ],
                    detail=f"{mention.text!r} is stated here and appears in no Python literal",
                    remedy="cite the constant this figure comes from, or record it as an open question",
                )


register(NumbersChecker())
