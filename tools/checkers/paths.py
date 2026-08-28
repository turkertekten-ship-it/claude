"""Does every filesystem path this repository names in its own prose exist?

Prose points at files constantly: a README table naming the module that
implements each row, a docstring deferring to an ADR, a Makefile comment naming
the goldens its target reads. Every one of those is a checkable assertion, and
every one of them rots silently - renaming a file does not rewrite the sentence
that named it, and no normal test suite notices.

The hard part is not resolving a path, it is deciding what counts as one.
English is full of tokens shaped like paths that are not: `application/json`,
`read/write`, `and/or`, `2 requests/second`. And this repository's own doctrine
warns that a name is not its contents - `PLAN.md` in a skill document is an
illustration of that rule, not a file the document expects to find; `robots.txt`
in a crawler docstring is a protocol artifact on someone else's host. So the
admission test here is deliberately narrower than "looks like a path":

    a directory separator, *and* either a known file suffix or a trailing slash.

That combination is what the four counter-examples above all fail, and it costs
only references this checker would have had to guess about anyway. A checker
that reports guesses is a checker somebody switches off, and a switched-off
checker catches nothing at all.
"""

from __future__ import annotations

import configparser
import posixpath
import re
from dataclasses import dataclass
from typing import Iterator

from tools.claims import RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

#: Files whose raw text is scanned as well as their prose. Both name paths in
#: comments and in string values, and neither is markdown or Python, so neither
#: is reachable through `prose_claims()` or `comment_claims()`.
CONFIG_FILES = ("Makefile", "pyproject.toml")

#: Suffixes that make a token a filename rather than an English word with a dot.
#: `.jsonl` precedes `.json` only for readability; the anchor decides the match.
_SUFFIX_RE = re.compile(
    r"\.(?:jsonl|json|md|py|toml|yaml|yml|txt|sh|rst|cfg|ini|lock)$", re.IGNORECASE
)

#: A markdown link with a relative target, its optional title dropped. Targets
#: are matched by pattern because the brackets survive whitespace splitting.
_LINK_RE = re.compile(r"\[[^\]\n]*\]\(\s*([^()\s]+?)(?:\s+[\"'][^\"'\n]*[\"'])?\s*\)")

#: Words that introduce a path in prose. They widen what is *looked at* and
#: never what is *reported*: "in read/write mode" and "declared in robots.txt"
#: both match this pattern, and neither names a file in the tree. The structural
#: test below stays the only thing that admits a token.
_CUE_RE = re.compile(
    r"\b(?:see|in|at|under|inside|within|into|from)\s+(\S+)", re.IGNORECASE
)

#: A character from this set means the author was showing a shape, not naming a
#: file: `<name>` and `{env}` are placeholders, `$VAR` is a variable, `*` is a
#: glob, and a colon covers both `https://` and `github:owner/repo`.
_PLACEHOLDER_CHARS = frozenset("<>{}[]()$*?|%\\&:!=\"'`^~")

#: Prose that asserts a path is *absent*. Absence evidence agrees with such a
#: sentence, so CONTRADICTED there would be this checker inventing a conflict -
#: CONTRACT.md rule 4. The window is several lines wide because the clause that
#: says "did not exist" is routinely not on the line that holds the path: this
#: repository's own `provenance/observations.md` spreads one such list over four.
_ABSENCE_RE = re.compile(
    r"\b(?:does|do|did|will|would|could|should)\s+not\s+(?:yet\s+)?exist"
    r"|\bnever\s+exist"
    r"|\bno\s+such\b"
    r"|\bnone\s+of\s+(?:them|those|these|which)\s+exist"
    r"|\bnothing\s+exists?\b"
    r"|\bthere\s+(?:is|are|was|were)\s+(?:deliberately\s+)?no\b"
    r"|\bnot\s+(?:yet\s+)?(?:been\s+)?(?:created|written|invented|added|implemented)\b"
    r"|\buncreated\b"
    r"|\bmissing\b"
    r"|\b(?:was|were|been)\s+(?:removed|deleted)\b"
    r"|\bno\s+longer\s+(?:exists?|there)\b",
    re.IGNORECASE,
)
_ABSENCE_WINDOW = 6

_BULLET_RE = re.compile(r"\s*(?:[-*+]|\d+\.)\s+")

#: An `owner/repo` slug: two segments, no file suffix, no trailing slash. The
#: shape overlaps with a real relative path, which is why it is only ever
#: consulted *after* local resolution has already failed.
_SLUG_RE = re.compile(r"`([A-Za-z0-9][\w.-]*/[A-Za-z0-9][\w.-]*)`")
#: How far around a claim to look for the slug that scopes it. A doc names the
#: repository once in a heading and then refers to "its `tools/`" for several
#: lines afterwards, so the window has to outlive the sentence.
_SLUG_WINDOW = 8

#: `owner/repo` and `packages/api` are the same shape, so shape alone cannot
#: decide. The window must also say it is talking about a repository - otherwise
#: any two-segment directory reference in a comment scopes the paths around it
#: to an imaginary other project, and the reference is reported unverifiable
#: instead of being checked.
_REPO_CUE_RE = re.compile(
    r"\brepositor(?:y|ies)\b|\brepos?\b|github\.com|\bupstream\b|\bsibling\b|\borigin\b",
    re.IGNORECASE,
)


def _own_slug(repo: RepoIndex) -> str:
    """This repository's own `owner/repo`, from git's origin remote.

    Read from `.git/config` rather than asked of `git`, because a checker must
    not shell out to inspect the thing it is checking. An unreadable or
    remote-less config yields "", which disables the cross-repository rule
    entirely - the rule needs to know what "this repository" is called before it
    can tell that a slug names a different one.
    """
    config_path = repo.root / ".git" / "config"
    if not config_path.is_file():
        return ""
    parser = configparser.ConfigParser()
    try:
        parser.read(config_path, encoding="utf-8")
    except (configparser.Error, OSError, UnicodeDecodeError):
        return ""
    for section in parser.sections():
        if section.replace('"', "").strip() != "remote origin":
            continue
        url = parser[section].get("url", "").strip()
        if not url:
            continue
        tail = url.rstrip("/").removesuffix(".git")
        tail = tail.split("://")[-1].split("@")[-1]
        parts = [p for p in tail.replace(":", "/").split("/") if p]
        if len(parts) >= 2:
            return f"{parts[-2]}/{parts[-1]}"
    return ""


def _foreign_slug(source: SourceFile | None, line: int, own: str) -> str:
    """A repository slug near `line` that is not this repository's own.

    `claude-ai`'s CLAUDE.md points at `turkertekten-ship-it/claude` and then
    names that repository's directories. Those are true statements about another
    tree. Reporting them as missing files here would be the checker inventing a
    contradiction out of a reference it simply was not given the tree for.
    """
    if source is None or not own:
        return ""
    rows = source.lines
    lo = max(0, line - 1 - _SLUG_WINDOW)
    window = "\n".join(rows[lo : line + _SLUG_WINDOW])
    if not _REPO_CUE_RE.search(window):
        return ""
    for candidate in _SLUG_RE.findall(window):
        if candidate == own or _SUFFIX_RE.search(candidate) or candidate.endswith("/"):
            continue
        return candidate
    return ""


def _in_sibling(token: str, slug: str, config: CheckConfig) -> str:
    """Where `token` resolves under a supplied sibling repository, or ""."""
    from pathlib import Path as _Path

    wanted = slug.split("/")[-1]
    base = token.rstrip("/") or token
    for root in config.sibling_roots:
        root_path = _Path(root)
        if root_path.name != wanted:
            continue
        for candidate in (base, posixpath.join("src", base)):
            if (root_path / candidate).exists():
                return str(root_path / candidate)
    return ""


@dataclass(slots=True)
class _Tree:
    """Every existing path, plus every tail of one.

    Prose abbreviates. The README's module table writes `util/http.py` for
    `src/oodarag/util/http.py`, because the package prefix is noise to a reader
    who already knows where the source lives. Resolving against the tails of
    real paths is what stops that abbreviation from reading as a broken link -
    and the abbreviation is common enough that without this the checker would
    report nine of them on its own repository.
    """

    tails: frozenset[str]

    @classmethod
    def of(cls, repo: RepoIndex) -> _Tree:
        tails: set[str] = set()
        for rel in sorted(repo.all_paths):
            parts = rel.split("/")
            for start in range(len(parts)):
                tails.add("/".join(parts[start:]))
        return cls(frozenset(tails))


def _clean(token: str) -> str:
    """Strip what prose wraps a path in, but never what changes its meaning.

    Leading dots survive on purpose: `./x` and `../x` mean different things, and
    normalising them here would hide the difference from resolution.
    """
    token = token.strip().split("#", 1)[0]
    token = token.lstrip("`'\"([{")
    return token.rstrip("`'\")]}.,;:!?")


def _is_path_like(token: str) -> bool:
    return "/" in token and (bool(_SUFFIX_RE.search(token)) or token.endswith("/"))


#: A first segment that is a hostname: `github.com/robots.txt`,
#: `example.org/index.html`, `docs.python.org/3/library`. These are URLs written
#: without their scheme, so they name a resource on another host and no
#: repository-relative lookup can decide anything about them. The scheme test in
#: `_PLACEHOLDER_CHARS` catches `https://...` but not the bare form.
_HOSTLIKE_RE = re.compile(
    r"^(?:[A-Za-z0-9-]+\.)+(?:com|org|net|io|dev|edu|gov|int|mil|co|ai|sh|me|"
    r"info|xyz|app|cloud|test|local|localhost)$",
    re.IGNORECASE,
)


def _is_excluded(token: str) -> bool:
    """Tokens no repository-relative lookup can honestly decide."""
    if token.startswith(("/", "~")):
        return True  # an absolute path names the host's filesystem, not this tree
    if "..." in token:
        return True  # an elision, as in `curl ... | sh`
    if _HOSTLIKE_RE.match(token.split("/", 1)[0]):
        return True  # a URL with its scheme left off
    return any(ch in _PLACEHOLDER_CHARS for ch in token)


def _tokens(text: str) -> list[tuple[str, bool]]:
    """Path-shaped tokens in `text`, as (token, came_from_link_syntax).

    Link targets are collected first, so a token written both ways on one line
    keeps the stronger provenance.
    """
    linked = _LINK_RE.findall(text)
    seen: dict[str, bool] = {}
    for candidate in [*linked, *_CUE_RE.findall(text), *text.split()]:
        token = _clean(candidate)
        if token:
            seen.setdefault(token, candidate in linked)
    return list(seen.items())


def _is_demonstration(token: str, from_link: bool, source: SourceFile | None) -> bool:
    """Is a `./`-prefixed token a command being shown rather than a file cited?

    In running prose `./x` is nearly always a command someone is demonstrating -
    `./scripts/setup.sh`, `./run.sh` - and the script it names belongs to the
    example rather than to this tree. The one place the prefix reliably names a
    real file is a markdown link target, where it addresses a sibling document.
    Elsewhere the prefix is read as a hint that the author was showing a shape,
    for the same reason a `<name>` segment is.
    """
    if not token.startswith(("./", "../")):
        return False
    return not (from_link and source is not None and source.is_markdown)


def _is_indented_code(source: SourceFile | None, claim: Claim) -> bool:
    """An indented block is an example, the way a fenced one is.

    `prose_claims()` already drops fenced blocks; four-space blocks are the other
    way markdown marks something as illustrative, and paths inside them are
    routinely invented for the example. Indented *bullets* are exempt - nesting
    a list is not quoting code.

    The same convention holds inside a Python docstring, which is why this is
    not restricted to markdown any more: a docstring that draws a directory tree
    indents it, and the identical block that is exempt in a README was an ERROR
    one file over. For Python the baseline is the surrounding prose rather than
    column zero, because a docstring inside a class is itself indented.
    """
    if source is None:
        return False
    raw = source.line_text(claim.line)
    indent = len(raw) - len(raw.lstrip())
    if indent < 4 or _BULLET_RE.match(raw) is not None:
        return False
    if source.is_markdown:
        return True
    return indent >= _prose_indent(source, claim.line) + 4


def _prose_indent(source: SourceFile, line: int) -> int:
    """The indentation the surrounding prose sits at.

    Taken as the smallest indentation among the nearby non-blank lines, so a
    docstring nested two levels deep is measured against its own left margin
    rather than against column zero.
    """
    rows = source.lines
    lo, hi = max(0, line - 1 - 6), min(len(rows), line + 6)
    indents = [len(r) - len(r.lstrip()) for r in rows[lo:hi] if r.strip()]
    return min(indents) if indents else 0


def _asserts_absence(source: SourceFile | None, line: int) -> bool:
    if source is None:
        return False
    rows = source.lines
    lo = max(0, line - 1 - _ABSENCE_WINDOW)
    window = " ".join(rows[lo : line + _ABSENCE_WINDOW])
    return _ABSENCE_RE.search(" ".join(window.split())) is not None


def _resolutions(token: str, citing: str, config: CheckConfig) -> list[str]:
    """Every repo-relative spelling of `token` worth probing, in a fixed order."""
    base = token.rstrip("/") or token
    out: list[str] = []

    def add(candidate: str) -> None:
        candidate = posixpath.normpath(candidate)
        if candidate not in out and not candidate.startswith(".."):
            out.append(candidate)

    add(base)
    for root in config.source_roots:
        add(posixpath.join(root, base))
    # A docstring saying `scrape/robots.py` inside src/oodarag/models.py means
    # its sibling, not a top-level directory of the same name.
    add(posixpath.join(posixpath.dirname(citing.replace("\\", "/")), base))
    return out


@dataclass
class PathsChecker:
    name: str = "paths"
    description: str = "Every path named in the repo's own prose resolves in the tree."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        tree = _Tree.of(repo)
        own_slug = _own_slug(repo)
        seen: set[tuple[str, int, str]] = set()

        for claim, source in _claims(repo):
            if _is_indented_code(source, claim):
                continue
            for token, from_link in _tokens(claim.text):
                if not _is_path_like(token) or _is_excluded(token):
                    continue
                if _is_demonstration(token, from_link, source):
                    continue
                key = (claim.path, claim.line, token)
                if key in seen:
                    continue
                seen.add(key)

                tried = _resolutions(token, claim.path, config)
                if any(repo.exists(candidate) for candidate in tried):
                    continue
                if token.rstrip("/") in tree.tails:
                    continue
                if _asserts_absence(source, claim.line):
                    continue

                if slug := _foreign_slug(source, claim.line, own_slug):
                    if _in_sibling(token, slug, config):
                        continue  # verified against the sibling tree that was supplied
                    yield Finding(
                        checker=self.name,
                        code="PATH_IN_OTHER_REPO",
                        verdict=Verdict.UNVERIFIABLE,
                        severity=Severity.INFO,
                        claim=claim,
                        detail=(
                            f"{token!r} is named here alongside {slug!r}, which is not this "
                            f"repository ({own_slug!r}), so it is a claim about that tree. "
                            f"Pass --sibling <path-to-{slug.split('/')[-1]}> to check it."
                        ),
                    )
                    continue

                yield Finding(
                    checker=self.name,
                    code="PATH_MISSING",
                    verdict=Verdict.CONTRADICTED,
                    severity=Severity.ERROR,
                    claim=claim,
                    evidence=[
                        Evidence.at(
                            claim.path,
                            claim.line,
                            claim.text,
                            summary=f"{claim.path}:{claim.line} refers to {token}",
                        ),
                        Evidence.absent(
                            f"nothing resolves {token!r}: tried "
                            + ", ".join(tried)
                            + ", and no path in the tree ends with it",
                            searched=[str(repo.root)],
                        ),
                    ],
                    detail=f"{token!r} is referenced here but is not in the tree",
                    remedy=f"create {token}, or correct the reference",
                )


def _claims(repo: RepoIndex) -> Iterator[tuple[Claim, SourceFile | None]]:
    """Claims paired with the file they came from, in a fixed order.

    The source file travels with the claim because two of the guards - the
    indented-example test and the absence-window test - need the lines around
    the claim, and re-opening the file per claim would defeat `RepoIndex`.
    """
    for claim in repo.prose_claims():
        yield claim, repo.get(claim.path)
    for claim in repo.comment_claims():
        yield claim, repo.get(claim.path)
    for rel in CONFIG_FILES:
        source = repo.get(rel)
        if source is None:
            continue
        for lineno, raw in enumerate(source.lines, start=1):
            line = raw.strip()
            if line:
                yield Claim(line, rel, lineno, kind="config"), source


register(PathsChecker())
