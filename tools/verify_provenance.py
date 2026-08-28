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
  4. In enforced files, every number a claim writes IN DIGITS appears
     somewhere in the evidence it cites (the capture file itself, when the
     entry points at one). This is the part of "does the source actually
     support this?" that can be settled deterministically. It deliberately
     ignores spelled-out counts, which evidence usually supports by
     enumeration rather than by stating a figure.
  5. No file uses a false-memory phrase (of the "as we discussed" family).
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
# Bare digit runs on both sides. Anything cleverer trips over ISO timestamps
# ("...T14:07"), identifiers, and decimals, producing false alarms about
# formatting rather than real findings. A screening check must be quiet enough
# that a hit means something.
NUMBER = re.compile(r"\d+")

# Deliberately NOT expanding spelled-out numbers. "the three later commits" is
# supported by evidence that names three commits without ever writing "3", so
# expanding it only produces findings about prose style. Counting enumerated
# items is semantic work this check does not claim to do — that is the
# fact-checker's job.

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

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "archive", "fixtures"}


class Finding:
    def __init__(self, path: Path, line: int, code: str, message: str) -> None:
        self.path, self.line, self.code, self.message = path, line, code, message

    def __str__(self) -> str:
        rel = self.path.relative_to(REPO) if self.path.is_absolute() else self.path
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
    """
    in_section = False
    in_fence = False
    for i, raw in enumerate(text.splitlines(), start=1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        heading = HEADING.match(raw)
        if heading:
            title = heading.group(2).strip().lower()
            in_section = title.startswith("observed")
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


def evidence_text(entry: dict) -> str:
    """All text backing one ledger entry.

    When `evidence` names a capture under provenance/, the capture itself is
    the evidence — comparing against the file *path* would check nothing.
    """
    parts = [str(entry.get(field, "")) for field in ("evidence", "method", "note", "collected_at")]
    raw = str(entry.get("evidence", "")).strip()
    if raw.startswith("provenance/"):
        capture = REPO / raw
        if capture.exists() and capture.is_file():
            parts.append(capture.read_text(encoding="utf-8", errors="replace"))
    return " ".join(parts)


def numbers_in(text: str) -> set[str]:
    """Digits appearing in text, with thousands separators normalised away."""
    return set(NUMBER.findall(text.replace(",", "")))


def check_quantities(line: str, known: dict[str, dict]) -> list[str]:
    """Report numbers asserted in a claim that its own sources do not contain.

    The verifier is otherwise syntactic: it checks a tag resolves, never that
    the evidence supports the sentence. Numbers are the one part of that gap
    that can be closed deterministically — a count, a date, or a size either
    appears in the cited evidence or it does not.
    """
    bare = INLINE_CODE.sub("", line)
    tags = SRC_TAG.findall(bare)
    if not tags:
        return []

    claimed = numbers_in(SRC_TAG.sub("", bare))
    if not claimed:
        return []

    resolved = [known[t] for t in tags if t in known]
    if not resolved:
        # Nothing resolves, so there is no evidence to compare against. The
        # UNKNOWN_SOURCE finding is the real one; adding a quantity complaint
        # for every digit on the line would just bury it.
        return []

    evidence = " ".join(evidence_text(entry) for entry in resolved)
    supported = numbers_in(evidence)
    return sorted(claimed - supported)


def scan_markdown(path: Path, ledger: dict[str, dict]) -> list[Finding]:
    findings: list[Finding] = []
    known = set(ledger)
    text = path.read_text(encoding="utf-8", errors="replace")

    for i, raw in enumerate(text.splitlines(), start=1):
        # Inline code spans are illustrative, not operative: a tag or phrase
        # shown in backticks is being described, so it neither needs to
        # resolve nor counts as a citation.
        bare = INLINE_CODE.sub("", raw)
        for sid in SRC_TAG.findall(bare):
            if sid not in known:
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
            for missing in check_quantities(line, ledger):
                findings.append(
                    Finding(path, i, "UNSUPPORTED_QUANTITY",
                            f"claim asserts {missing!r}, absent from its cited evidence")
                )
            if "[src:" not in INLINE_CODE.sub("", line):
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
                if not any(part in SKIP_DIRS for part in path.parts):
                    yield path


def main(argv: list[str]) -> int:
    targets = [Path(a).resolve() for a in argv[1:]] or [REPO]
    known, findings = load_sources()
    for path in markdown_files(targets):
        findings.extend(scan_markdown(path, known))

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
