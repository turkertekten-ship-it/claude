"""Does every provenance citation resolve to a recorded source?

The doctrine this repository works under is that a factual claim is either
sourced or it is not written down. A claim carries a tag, the id in that tag
resolves to an entry in `provenance/sources.yaml`, and a question nobody can
answer yet becomes a `U-<n>` entry in `provenance/unknowns.md` rather than a
guess. A tag whose id resolves to nothing is exactly the failure that rule
exists to prevent: to a reader it looks identical to a sourced claim, and the
only way to find out otherwise is to go and look, which is the work the tag was
supposed to have already done.

Two decisions shape everything below.

The first is that the reader for `sources.yaml` is deliberately tiny - a
top-level `sources:` list of `- id:` mappings, plus the flat `id: mapping`
shape, and nothing else. Only the standard library is available, and half a
YAML parser is worse than none, because the half that fails fails silently.

The second follows from the first: **a reader that understood nothing must say
so, not accuse.** If this one comes up empty against a file that plainly has
content, every tag in the repository suddenly looks unresolved, and the report
fills with ERRORs produced by fifty lines of string handling rather than by
anything wrong with the repository. That case is UNVERIFIABLE. Keeping it
distinct from a genuinely unrecorded id is the entire reason this is a checker
and not a grep.

Neither convention is universal, so a repository that uses neither is left
alone: no tags and no `provenance/` store means no findings, not a lecture
about a convention its authors never adopted. For the same reason unknown ids
are only resolved when `provenance/unknowns.md` exists - without it, a token
shaped like one is just a token.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterator

from tools.claims import RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

#: Where the source store may live. Probed in this order; both are named in the
#: absence evidence when neither exists, because "no store" is only a fact if
#: you say what you looked for.
SOURCE_STORES = ("provenance/sources.yaml", "provenance/sources.yml")
UNKNOWNS_FILE = "provenance/unknowns.md"

_TAG_RE = re.compile(r"\[src:([A-Za-z0-9_.-]+)\]")
_UNKNOWN_RE = re.compile(r"\b(U-\d+)\b")

#: An id that stands in for an id rather than being one. Doctrine has to write
#: the convention down somewhere, and writing it down means writing a tag out
#: with a placeholder in it - this repository's own skill document has one in a
#: table row. Reporting those would be reporting the rule for breaking the rule.
#: The list is closed on purpose: a real id is only dropped if someone names a
#: source `foo`, which costs one miss, where guessing costs the whole report.
_PLACEHOLDER_ID_RE = re.compile(
    r"^(?:[A-Za-z]{1,6}-)?"
    r"(?:ID|IDS|N|NN|X|XX|XXX|Y|Z|SRC|SOURCE|SOURCE_ID|TODO|TBD|FOO|BAR|BAZ|EXAMPLE)$",
    re.IGNORECASE,
)

#: The same character set the tag regex admits: an id the reader cannot spell
#: back into a tag could never have matched one, so it is not an entry.
_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_TOP_KEY_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(.*)$")
_ITEM_ID_RE = re.compile(r"^\s*(?:-\s+)?id\s*:\s*(.+?)\s*$")

#: How many citation sites one aggregate finding quotes before it stops. The
#: cap keeps a report readable; the exact count travels as measured evidence.
_MAX_SITES = 5


@dataclass(slots=True)
class _Ref:
    """One id as it was actually written, with the line it was written on."""

    ident: str
    claim: Claim


@dataclass(slots=True)
class _Store:
    """What the subset reader made of the source store.

    `has_content` is tracked separately from `ids` because the difference
    between them is the finding: content with no ids is a file this reader did
    not understand, while no content at all is a store with nothing in it.
    """

    rel: str
    ids: dict[str, int] = field(default_factory=dict)
    has_content: bool = False
    first_line: int = 1
    first_text: str = ""


# ------------------------------------------------------------------- scanning


def _fenced_lines(source: SourceFile) -> frozenset[int]:
    """Lines inside a fenced block, which is where conventions get illustrated.

    A fence is how markdown says "this is an example". A tag shown inside one is
    a demonstration of the format, not a claim being sourced, and the same span
    arithmetic `prose_claims()` uses is reused here so the two agree about where
    a fence ends.
    """
    out: set[int] = set()
    for fence in source.fences():
        span = len(fence.body.split("\n")) if fence.body else 0
        out.update(range(fence.start_line - 1, fence.start_line + span + 1))
    return frozenset(out)


def _citable(source: SourceFile) -> Iterator[tuple[int, str]]:
    """Places in one file where a citation could honestly have been written.

    Python is read through its comments and docstrings only. A tag inside a
    string literal is nearly always a fixture or a pattern - this checker's own
    tests are full of them - and a checker that reports its own test data is a
    checker whose first true finding nobody believes.
    """
    if source.is_python:
        for claim in source.comment_claims():
            yield claim.line, claim.text
        return
    fenced = _fenced_lines(source) if source.is_markdown else frozenset()
    for lineno, raw in enumerate(source.lines, start=1):
        if lineno not in fenced:
            yield lineno, raw


def _scan(repo: RepoIndex) -> tuple[list[_Ref], list[_Ref]]:
    """Every citation and every unknown-id reference, in file then line order."""
    tags: list[_Ref] = []
    unknowns: list[_Ref] = []
    seen: set[tuple[str, int, str]] = set()

    for source in repo.files:
        for lineno, text in _citable(source):
            stripped = text.strip()
            if not stripped:
                continue
            claim: Claim | None = None
            for ident, bucket in [
                *((i, tags) for i in _TAG_RE.findall(stripped)),
                *((i, unknowns) for i in _UNKNOWN_RE.findall(stripped)),
            ]:
                if bucket is tags and _PLACEHOLDER_ID_RE.match(ident):
                    continue
                key = (source.rel, lineno, ident)
                if key in seen:
                    continue
                seen.add(key)
                if claim is None:
                    claim = Claim(stripped, source.rel, lineno, kind="citation")
                bucket.append(_Ref(ident, claim))
    return tags, unknowns


# ------------------------------------------------------- the subset yaml reader


def _scalar(raw: str) -> str:
    """The value half of a `key: value` line, unwrapped the few ways YAML allows."""
    value = raw.strip()
    if value[:1] in ("'", '"'):
        quote = value[0]
        end = value.find(quote, 1)
        return value[1:end] if end > 0 else value[1:]
    return value.split(" #", 1)[0].strip()


def _read_store(source: SourceFile) -> _Store:
    """Read ids out of the two shapes this store is actually written in.

    Nothing here tries to be YAML. It looks for the documented shape, then for
    the flat one, and reports what it found - including finding nothing, which
    the caller turns into UNVERIFIABLE rather than into accusations.
    """
    body = [
        (lineno, raw)
        for lineno, raw in enumerate(source.lines, start=1)
        if raw.strip() and not raw.lstrip().startswith("#")
    ]
    store = _Store(rel=source.rel, has_content=bool(body))
    if body:
        store.first_line, store.first_text = body[0][0], body[0][1].strip()

    # Shape A: a top-level `sources:` key owning a list of mappings. List items
    # may sit at the parent's indentation or below it - both are valid YAML and
    # both appear in the wild - so a leading dash keeps the block open.
    in_sources = False
    for lineno, raw in body:
        item = raw.lstrip().startswith("- ")
        if not raw[:1].isspace() and not item:
            head = _TOP_KEY_RE.match(raw)
            in_sources = bool(head) and head.group(1) == "sources" and not head.group(2).strip()
            continue
        if not in_sources:
            continue
        if found := _ITEM_ID_RE.match(raw):
            ident = _scalar(found.group(1))
            if _ID_RE.match(ident):
                store.ids.setdefault(ident, lineno)

    # Shape B: the store is itself the mapping, one id per top-level key. This
    # is all-or-nothing on purpose. A document where *some* top-level key owns
    # an indented mapping is not a flat id store - `records:` above a list of
    # entries has that shape too - and reading ids out of it would invent a
    # source named `records` and then report every real citation as unresolved
    # against it. Either the whole file is a mapping of mappings or this reader
    # did not understand the file, which is a different finding entirely.
    if not store.ids:
        candidates: dict[str, int] = {}
        for index, (lineno, raw) in enumerate(body):
            if raw[:1].isspace():
                continue
            head = _TOP_KEY_RE.match(raw)
            following = body[index + 1][1] if index + 1 < len(body) else ""
            owns_mapping = (
                head is not None
                and not head.group(2).strip()
                and following[:1].isspace()
                and not following.lstrip().startswith("- ")
            )
            if not owns_mapping:
                candidates.clear()  # a scalar, a list, or a shape not covered here
                break
            if head.group(1) != "sources":
                candidates.setdefault(head.group(1), lineno)
        store.ids.update(candidates)
    return store


def _preview(ids: list[str], limit: int = 12) -> str:
    head = ", ".join(ids[:limit])
    return head if len(ids) <= limit else f"{head}, ... ({len(ids)} total)"


# -------------------------------------------------------------------- findings


@dataclass
class CitationsChecker:
    name: str = "citations"
    description: str = "Every provenance citation resolves to an entry in the source store."

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        tags, unknown_refs = _scan(repo)
        store_file = next((f for f in (repo.get(rel) for rel in SOURCE_STORES) if f), None)
        unknowns_file = repo.get(UNKNOWNS_FILE)

        # A repository that cites nothing and keeps no provenance store is not
        # violating this convention, it is not using it. Say nothing at all.
        if not tags and store_file is None and unknowns_file is None:
            return

        store = _read_store(store_file) if store_file is not None else None

        if store is None:
            if tags:
                yield self._store_missing(repo, tags)
        elif not store.ids:
            # The reader failed, or the store is empty. Either way the honest
            # report is "not established", never "every tag is broken".
            if store.has_content or tags:
                yield self._unreadable(store, tags)
        else:
            for ref in tags:
                if ref.ident not in store.ids:
                    yield self._unresolved(ref, store)
            cited = {ref.ident for ref in tags}
            for ident, lineno in sorted(store.ids.items()):
                if ident not in cited:
                    yield self._uncited(repo, store, ident, lineno)

        if unknowns_file is not None:
            recorded = set(_UNKNOWN_RE.findall(unknowns_file.text))
            for ref in unknown_refs:
                if ref.ident not in recorded:
                    yield self._unknown_missing(ref)

    # Each builder below attaches the observation its verdict rests on: where
    # the id was written, and where the lookup for it went.

    def _unresolved(self, ref: _Ref, store: _Store) -> Finding:
        return Finding(
            checker=self.name,
            code="SRC_UNRESOLVED",
            verdict=Verdict.CONTRADICTED,
            severity=Severity.ERROR,
            claim=ref.claim,
            evidence=[
                Evidence.at(
                    ref.claim.path,
                    ref.claim.line,
                    ref.claim.text,
                    summary=f"{ref.claim.locator} cites {ref.ident}",
                ),
                Evidence.absent(
                    f"{store.rel} records no entry with id {ref.ident!r}; "
                    f"it records {_preview(sorted(store.ids))}",
                    searched=[store.rel],
                ),
            ],
            detail=f"the citation {ref.ident!r} resolves to no entry in {store.rel}",
            remedy=f"record {ref.ident} in {store.rel}, or correct the citation",
        )

    def _store_missing(self, repo: RepoIndex, tags: list[_Ref]) -> Finding:
        # One finding, not one per tag: the repository has a single defect here
        # - there is no store - and repeating it per citation would bury it.
        sites = [
            Evidence.at(
                ref.claim.path,
                ref.claim.line,
                ref.claim.text,
                summary=f"{ref.claim.locator} cites {ref.ident}",
            )
            for ref in tags[:_MAX_SITES]
        ]
        return Finding(
            checker=self.name,
            code="SRC_STORE_MISSING",
            verdict=Verdict.CONTRADICTED,
            severity=Severity.ERROR,
            claim=tags[0].claim,
            evidence=[
                *sites,
                Evidence.absent(
                    "no source store exists to resolve these against",
                    searched=list(SOURCE_STORES),
                ),
                Evidence.measured(
                    "citations with nowhere to resolve",
                    value=len(tags),
                    path=str(repo.root),
                ),
            ],
            detail=(
                f"{len(tags)} citation(s) are written, but neither "
                f"{' nor '.join(SOURCE_STORES)} exists"
            ),
            remedy=f"create {SOURCE_STORES[0]} with an entry per cited id, or drop the citations",
        )

    def _unreadable(self, store: _Store, tags: list[_Ref]) -> Finding:
        reason = (
            "the narrow reader used here found no entries in it - it understands a "
            "top-level `sources:` list of `- id:` mappings and a flat mapping of id "
            "to mapping, and nothing else"
            if store.has_content
            else "it records no entries at all"
        )
        evidence = [
            Evidence.measured("citations left unresolved", value=len(tags), path=store.rel)
        ]
        if store.has_content:
            evidence.insert(
                0,
                Evidence.at(
                    store.rel,
                    store.first_line,
                    store.first_text,
                    summary=f"first content line of {store.rel}",
                ),
            )
        return Finding(
            checker=self.name,
            code="SRC_STORE_UNREADABLE",
            verdict=Verdict.UNVERIFIABLE,
            severity=Severity.WARN,
            claim=Claim(store.first_text, store.rel, store.first_line, kind="citation"),
            evidence=evidence,
            detail=(
                f"{store.rel} exists but {reason}; the {len(tags)} citation(s) in this "
                "repository are recorded as unchecked rather than as unresolved, because "
                "a reader that understood nothing is not evidence that they resolve to nothing"
            ),
            remedy=f"write {store.rel} as a `sources:` list of `- id:` entries, or check it by hand",
        )

    def _uncited(self, repo: RepoIndex, store: _Store, ident: str, lineno: int) -> Finding:
        source = repo.get(store.rel)
        text = source.line_text(lineno).strip() if source else ident
        return Finding(
            checker=self.name,
            code="SRC_UNCITED",
            verdict=Verdict.UNSUPPORTED,
            severity=Severity.INFO,
            claim=Claim(text, store.rel, lineno, kind="citation"),
            evidence=[
                Evidence.at(
                    store.rel,
                    lineno,
                    text,
                    summary=f"{store.rel}:{lineno} records {ident}",
                ),
                Evidence.measured(
                    f"text files scanned for a citation of {ident}",
                    value=len(repo.files),
                    path=str(repo.root),
                ),
                Evidence.absent(
                    f"nothing in the tree cites {ident}",
                    searched=[str(repo.root)],
                ),
            ],
            detail=f"{ident} is recorded in {store.rel} but no claim cites it",
            remedy=f"cite {ident} where the observation it backs is written, or drop the entry",
        )

    def _unknown_missing(self, ref: _Ref) -> Finding:
        # UNSUPPORTED, not CONTRADICTED: the file was read and does not mention
        # the id, which is the absence of a record, not a record saying otherwise.
        return Finding(
            checker=self.name,
            code="UNKNOWN_UNRESOLVED",
            verdict=Verdict.UNSUPPORTED,
            severity=Severity.WARN,
            claim=ref.claim,
            evidence=[
                Evidence.at(
                    ref.claim.path,
                    ref.claim.line,
                    ref.claim.text,
                    summary=f"{ref.claim.locator} refers to {ref.ident}",
                ),
                Evidence.absent(
                    f"no line of {UNKNOWNS_FILE} contains {ref.ident}",
                    searched=[UNKNOWNS_FILE],
                ),
            ],
            detail=f"{ref.ident} is referred to here but is not recorded in {UNKNOWNS_FILE}",
            remedy=f"record {ref.ident} in {UNKNOWNS_FILE}, or correct the reference",
        )


register(CitationsChecker())
