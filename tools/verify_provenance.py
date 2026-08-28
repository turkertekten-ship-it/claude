#!/usr/bin/env python3
"""Fail the build when a document asserts something it cannot source.

The rule this enforces is the operating rule of this repository: a factual
claim either carries a source tag that resolves to `provenance/sources.yaml`,
or it does not get written down.

Checks
  1. sources.yaml parses, every entry has the required fields, ids are unique,
     and any file path given as evidence exists.
  2. Every source tag in every scanned Markdown file resolves to a declared
     source. A tag inside `inline code` is an example, not a citation: it does
     not need to resolve, and it does not satisfy check 3.
  3. In files whose front matter says `provenance: enforced`, every claim line
     inside an `## Observed...` section carries a `[src:` tag.
  4. No file uses a false-memory phrase (of the "as we discussed" family).
     Those phrases assert a shared history that this repository has no record
     of, which is the exact failure mode being guarded against. A phrase
     wrapped in `inline code` is quoted rather than asserted, and is allowed.

Usage
  python3 tools/verify_provenance.py [path ...]     # defaults to repo root
Exit
  0 clean · 1 violations found · 2 could not run
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not a violation
    print("verify_provenance: PyYAML is required (pip install pyyaml)", file=sys.stderr)
    raise SystemExit(2)

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "provenance" / "sources.yaml"

REQUIRED_FIELDS = ("id", "kind", "collected_at", "method", "evidence")
VALID_KINDS = {"tool_output", "filesystem", "api", "user_statement", "repo_state"}

SRC_TAG = re.compile(r"\[src:([A-Za-z0-9._-]+)\]")
FRONT_MATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")

# Metasyntactic ids: `[src:ID]` in "State the fact + source: \"X happened.
# [src:ID]\"" is teaching the tag syntax, not citing anything. Every real id in
# the ledger is NAME-YYYY-MM-DD, so none of these can collide with one. They are
# still reported in enforced files -- shipping a placeholder into
# observations.md is its own mistake -- but under a code the prose grader can
# tell apart from an invented citation, which is what it was mistaking them for.
PLACEHOLDER_IDS = frozenset({
    "ID", "id", "Id", "IDS", "SRC", "src", "SRC-ID", "SOURCE", "SOURCE-ID",
    "SOURCE_ID", "TAG", "X", "XXX", "YYY", "ZZZ", "N", "NAME", "FOO", "BAR",
    "EXAMPLE", "PLACEHOLDER", "TODO", "...", "..", "-",
})

# Phrases that assert a conversation history this repository cannot show.
FALSE_MEMORY = [
    "as we discussed",
    "as discussed earlier",
    "in our previous chat",
    "in our last conversation",
    "per our last conversation",
    "you previously said",
    "you told me earlier",
    "as you mentioned earlier",
    "as you said before",
    "we agreed that",
    "recall that you",
    "from our earlier chats",
    "based on our past conversations",
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "archive", "fixtures",
             ".workbench"}

#: Verbatim captures are evidence, not assertions. A transcript that records a
#: model writing `[src:ID]`, or a page that contains the words `as we
#: discussed`, is quoting -- and demanding that a quotation resolve to this
#: repository's ledger is the same category error as demanding a source tag on
#: every line of conversational prose. Everything here is referenced by an
#: `evidence:` field in sources.yaml, never asserted as prose.
VERBATIM_DIRS = {REPO / "provenance" / "raw"}


class Finding:
    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def __str__(self) -> str:
        # A finding on a path outside the repository is exactly when output
        # matters most, and relative_to raises there. The guard dying while
        # reporting is worse than the finding it was reporting.
        try:
            rel = self.path.relative_to(REPO) if self.path.is_absolute() else self.path
        except ValueError:
            rel = self.path
        return f"{rel}:{self.line}: {self.code}: {self.message}"


def load_sources() -> tuple[dict, list[Finding]]:
    findings: list[Finding] = []
    if not LEDGER.exists():
        findings.append(Finding(LEDGER, 0, "NO_LEDGER", "provenance/sources.yaml is missing"))
        return {}, findings

    doc = yaml.safe_load(LEDGER.read_text()) or {}
    entries = doc.get("sources") or []
    if not isinstance(entries, list):
        findings.append(Finding(LEDGER, 0, "BAD_LEDGER", "top-level `sources:` must be a list"))
        return {}, findings

    known: dict[str, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            findings.append(Finding(LEDGER, 0, "BAD_ENTRY", f"not a mapping: {entry!r}"))
            continue
        sid = entry.get("id", "<missing id>")
        for field in REQUIRED_FIELDS:
            if not entry.get(field):
                findings.append(
                    Finding(LEDGER, 0, "MISSING_FIELD", f"source {sid} has no `{field}`")
                )
        kind = entry.get("kind")
        if kind and kind not in VALID_KINDS:
            findings.append(
                Finding(
                    LEDGER, 0, "BAD_KIND",
                    f"source {sid} kind={kind!r} not in {sorted(VALID_KINDS)}",
                )
            )
        if sid in known:
            findings.append(Finding(LEDGER, 0, "DUPLICATE_ID", f"source {sid} declared twice"))
        # Evidence that looks like a repo path must actually exist.
        evidence = str(entry.get("evidence", ""))
        if evidence.startswith("provenance/") and not (REPO / evidence.strip()).exists():
            findings.append(
                Finding(LEDGER, 0, "MISSING_EVIDENCE", f"source {sid} points at {evidence!r}, which does not exist")
            )
        if sid != "<missing id>":
            known[sid] = entry
    return known, findings


def is_enforced(text: str) -> bool:
    m = FRONT_MATTER.match(text)
    if not m:
        return False
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return False
    return isinstance(meta, dict) and meta.get("provenance") == "enforced"


def claim_lines(text: str):
    """Yield (lineno, line) for claim lines inside `## Observed...` sections.

    A claim line is a top-level bullet or a prose line. Indented continuations
    inherit their bullet's tag, headings introduce sections, and fenced blocks
    are verbatim evidence rather than assertions.

    Two holes were found here by an adversarial review and are both closed:

    - **A subheading used to end the section.** Any heading at all reset
      `in_section`, so a `### Detail` under `## Observed` switched the check
      off for everything below it. The section now ends only at a heading of
      the same depth or shallower, which is what "section" means.
    - **A fence marker anywhere toggled the state file-wide.** `FENCE` matched
      an indented ``` inside a list item, so one such line inverted the fence
      state for the rest of the file and every later claim was skipped as
      "verbatim evidence". The toggle now tracks the opening fence's indent and
      only a marker at that indent closes it.

    Both silently disabled the guard rather than failing loudly, which is the
    worst way for a guard to be wrong.
    """
    in_section = False
    section_depth = 0
    fence_indent: int | None = None
    for i, raw in enumerate(text.splitlines(), start=1):
        if FENCE.match(raw):
            indent = len(raw) - len(raw.lstrip())
            if fence_indent is None:
                fence_indent = indent
                continue
            if indent == fence_indent:
                fence_indent = None
            continue
        if fence_indent is not None:
            continue
        heading = HEADING.match(raw)
        if heading:
            depth = len(heading.group(1))
            title = heading.group(2).strip().lower()
            if title.startswith("observed"):
                in_section, section_depth = True, depth
            elif in_section and depth <= section_depth:
                in_section = False
            continue
        if not in_section:
            continue
        line = raw.rstrip()
        if not line.strip():
            continue
        if raw[:1].isspace():          # continuation of the bullet above
            continue
        if line.lstrip().startswith((">", "<!--", "|", "---")):
            continue
        yield i, line


def scan_markdown(path: Path, known: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8", errors="replace")

    for i, raw in enumerate(text.splitlines(), start=1):
        # Inline code spans are illustrative, not operative: a tag or phrase
        # shown in backticks is being described, so it neither needs to
        # resolve nor counts as a citation.
        bare = INLINE_CODE.sub("", raw)
        for sid in SRC_TAG.findall(bare):
            if sid in known:
                continue
            if sid in PLACEHOLDER_IDS:
                findings.append(
                    Finding(path, i, "PLACEHOLDER_SOURCE", f"[src:{sid}] is a syntax placeholder, not a citation")
                )
                continue
            findings.append(
                Finding(path, i, "UNKNOWN_SOURCE", f"[src:{sid}] is not declared in provenance/sources.yaml")
            )
        # A phrase inside `inline code` is being named, not asserted — the
        # doctrine has to be able to quote the phrases it bans.
        lowered = bare.lower()
        for phrase in FALSE_MEMORY:
            if phrase in lowered:
                findings.append(
                    Finding(path, i, "FALSE_MEMORY", f"asserts unrecorded history: {phrase!r}")
                )

    if is_enforced(text):
        for i, line in claim_lines(text):
            bare = INLINE_CODE.sub("", line)
            # A tag that PARSES, not the substring "[src:". Testing for the
            # substring meant a malformed citation -- `[src:` with no id and no
            # bracket -- satisfied the sourcing requirement here while the
            # SRC_TAG regex above never matched it, so it resolved against
            # nothing. An invented statistic carrying one passed the whole
            # guard and exited 0.
            if SRC_TAG.search(bare):
                continue
            if "[src:" in bare:
                findings.append(
                    Finding(path, i, "MALFORMED_SOURCE",
                            f"citation does not parse as [src:ID]: {line.strip()[:70]!r}")
                )
                continue
            findings.append(
                Finding(path, i, "UNSOURCED_CLAIM", f"claim without a source tag: {line.strip()[:70]!r}")
            )
    return findings


def markdown_files(targets: list[Path]):
    for target in targets:
        if target.is_file() and target.suffix == ".md":
            yield target
        elif target.is_dir():
            for path in sorted(target.rglob("*.md")):
                if any(part in SKIP_DIRS for part in path.parts):
                    continue
                if any(d in path.parents for d in VERBATIM_DIRS):
                    continue
                yield path


def main(argv: list[str]) -> int:
    targets = [Path(a).resolve() for a in argv[1:]] or [REPO]
    known, findings = load_sources()
    for path in markdown_files(targets):
        findings.extend(scan_markdown(path, set(known)))

    if not findings:
        scanned = len(list(markdown_files(targets)))
        print(f"verify_provenance: OK — {scanned} file(s), {len(known)} source(s), 0 violations")
        return 0

    for finding in sorted(findings, key=lambda f: (str(f.path), f.line)):
        print(str(finding), file=sys.stderr)
    print(f"\nverify_provenance: {len(findings)} violation(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
