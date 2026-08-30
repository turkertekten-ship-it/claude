#!/usr/bin/env python3
"""Find text still repeating a claim the ledger has retracted.

A correction propagates only as far as whoever makes it happens to look. That
is not a hypothesis here. An early check decided Claude Code ignored the output
ceiling, and that verdict reached `docs/parity.md` and `README.md` as a
platform defect. It was retracted when the row was rewritten -- the harness had
looked for truncation where the platform refuses -- and the retraction reached
those two files and stopped. `workbench doctor` went on telling every new
session the platform was broken, for two more days, through a fact-check audit,
a security review and a green test suite. [src:DOCTOR-STALE-TWO-2026-08-29]

Nothing connected the retraction to the places repeating it, because every
other check in this repository examines the artifact in front of it and none
asks whether some OTHER artifact still says the opposite.

This does ask. An entry that overturns an earlier finding records the phrasing
that should no longer appear:

    retracts:
      supersedes: SOME-EARLIER-FINDING-2026-01-01
      phrases:
        - "the widget is broken"

and every tracked file is searched for those phrases. The ledger entry that
declares the retraction is skipped -- it must quote what it retracts -- as is
`provenance/raw/`, which holds verbatim captures.

Deliberately a string search. The earlier attempt to mechanise fact-checking
died because relational errors need judgement [src:FIGURE-CHECK-FAILS-2026-08-29];
a retracted phrase reappearing is not a judgement, it is a grep, and a grep is
a thing a tool can be trusted with.

What it cannot do, stated after an adversarial review rather than from
intent, because the limits I first wrote were narrower than the real ones:

- It cannot catch a retracted claim restated in different words. The phrase
  list is only as good as the phrases someone thought to write down, and five
  phrases across three entries is what exists today.
- Matching is whitespace-collapsed and case-insensitive over a three-line
  window, so an ordinary line wrap no longer hides a phrase — but one split
  across four or more lines is reported as "spanning more lines than the
  window" rather than located precisely.
- `retraction-quote` is an unauthenticated opt-out. Any line carrying that
  token is exempt, so it silences as easily as it excuses.
- Symlinks and non-textual files are skipped, and so is anything under a
  directory named in SKIP_COMPONENTS.

Exit 0 when nothing repeats a retracted claim, 1 when something does, 2 when it
cannot run.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "provenance" / "sources.yaml"
#: Same rule verify_provenance uses: backticked text is quoted, not claimed.
INLINE_CODE = re.compile(r"`[^`]*`")
#: Directory NAMES, matched component-wise rather than as path prefixes.
SKIP_COMPONENTS = {"raw", ".workbench", ".git", "__pycache__", "venv", ".venv"}


#: Extensions worth searching. A retracted claim lives in prose or in code,
#: not in a PNG, and hashing every byte of the tree would be slow and noisy.
TEXTUAL = {".md", ".py", ".yaml", ".yml", ".sh", ".txt", ".json", ".toml", ".cfg"}


def _norm(text: str) -> str:
    """Collapse whitespace and case, so a line wrap is not a hiding place."""
    return " ".join(text.split()).lower()


def _windows(text: str, span: int = 3) -> list[str]:
    """Overlapping groups of lines, so a wrapped phrase is still one string."""
    lines = text.splitlines()
    if not lines:
        return []
    return [" ".join(lines[i:i + span]) for i in range(len(lines))]


def searchable_files() -> list[Path]:
    """Every textual file in the tree, tracked or not.

    This used to shell out to `git ls-files`, and that blindness bit the tool
    on its first day: its own source was untracked when it was run, so it never
    searched itself, reported clean, and went red the moment it was committed.
    The likeliest place a retracted claim is re-asserted is a document someone
    has just written and not yet staged -- exactly what git does not list.

    Walking the tree also fixes two silent drops: filenames git quotes and
    octal-escapes because they are not ASCII, and the prefix match that treated
    `provenance/rawdata.md` as if it were inside `provenance/raw/`.
    """
    files: list[Path] = []
    for path in REPO.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if path.suffix not in TEXTUAL:
            continue
        rel = path.relative_to(REPO)
        # Component-wise, so `rawdata.md` and `.workbenchers/` are not skipped.
        if any(part in SKIP_COMPONENTS for part in rel.parts):
            continue
        files.append(path)
    return sorted(files)


def main(argv: list[str]) -> int:
    if not LEDGER.exists():
        print("provenance/sources.yaml is missing", file=sys.stderr)
        return 2
    try:
        entries = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))["sources"]
    except (yaml.YAMLError, KeyError, TypeError) as exc:
        print(f"ledger will not parse: {exc}", file=sys.stderr)
        return 2

    if not isinstance(entries, list):
        print("ledger `sources` is not a list", file=sys.stderr)
        return 2
    declared = []
    for e in entries:
        if not isinstance(e, dict):
            print(f"ledger entry is not a mapping: {e!r:.60}", file=sys.stderr)
            return 2
        # Key ABSENT means unannotated. Key present and empty means someone
        # started an annotation and it did not parse -- a mis-indented block
        # yields None, and treating that as "unannotated" is the silent
        # demotion this check exists to prevent.
        if "retracts" not in e:
            continue
        block = e["retracts"]
        if block is None:
            print(f"{e.get('id','?')}: `retracts` is empty — a half-written "
                  f"annotation, not an absent one", file=sys.stderr)
            return 2
        if not isinstance(block, dict):
            print(f"{e.get('id','?')}: `retracts` must be a mapping, got "
                  f"{type(block).__name__}", file=sys.stderr)
            return 2
        phrases = block.get("phrases")
        if isinstance(phrases, str):
            print(f"{e.get('id','?')}: `phrases` must be a list; a bare string "
                  f"would be matched one character at a time", file=sys.stderr)
            return 2
        if not phrases:
            print(f"{e.get('id','?')}: declares `retracts` with no phrases — "
                  f"a retraction nobody can check", file=sys.stderr)
            return 2
        declared.append(e)
    files = searchable_files()
    if not files:
        print("no searchable files found; run this inside the repository", file=sys.stderr)
        return 2

    print("Retracted claims, and whether anything still repeats them")
    print("=" * 68)
    print(f"{len(declared)} of {len(entries)} entries declare a retraction; "
          f"{len(files)} file(s) searched.")
    print()

    hits = 0
    for entry in declared:
        block = entry["retracts"]
        phrases = block.get("phrases") or []
        superseded = block.get("supersedes", "?")
        for phrase in phrases:
            found = []
            for path in files:
                try:
                    text = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if _norm(phrase) not in _norm(text):
                    continue
                # The ledger must quote what it retracts.
                if path == LEDGER:
                    continue
                # A phrase can be QUOTED rather than asserted, and the first
                # real run of this tool flagged two such quotations: a
                # regression test naming the phrase it guards against, and a
                # correctly-dated historical note. verify_provenance already
                # settles this -- a phrase in inline code is named, not
                # asserted -- so the same convention applies here, plus an
                # explicit marker for source files, which have no backticks.
                # Whitespace-collapsed and case-insensitive, because the
                # phrases are 20-45 characters and every prose file here is
                # hard-wrapped at ~76 columns: an ordinary line break defeated
                # exact matching, as did a sentence-initial capital.
                flat = _norm(text)
                needle = _norm(phrase)
                asserting = []
                seen_anywhere = False
                for window in _windows(text):
                    if needle not in _norm(window):
                        continue
                    seen_anywhere = True
                    if "retraction-quote" in window:
                        continue
                    # Strip the quoted spans and re-test, so a line that both
                    # asserts and quotes is still caught.
                    if needle not in _norm(INLINE_CODE.sub(" ", window)):
                        continue
                    asserting.append(window)
                if not asserting and not seen_anywhere and needle in flat:
                    # Present in the file but in no window: it spans more lines
                    # than the window covers. Report rather than print a false
                    # "nothing repeats this".
                    #
                    # The condition matters. An earlier version omitted
                    # `not seen_anywhere`, so this fired whenever the
                    # exemptions had removed every window -- silently
                    # overriding both exemptions and reporting quotations as
                    # assertions.
                    asserting.append("(spanning more lines than the window)")
                if not asserting:
                    continue
                found.append(path.relative_to(REPO))
            if not found:
                print(f"[ok   ] {entry['id']}  — nothing repeats {phrase!r}")
                continue
            print(f"[STALE] {entry['id']} retracted {superseded}")
            print(f"        but {phrase!r} still appears in:")
            for rel in found:
                print(f"          {rel}")
            hits += len(found)

    print()
    if hits:
        print(f"check_retractions: {hits} place(s) still assert a retracted claim.")
        print("A correction that reaches one file and not the others is not a correction.")
        return 1
    print("check_retractions: nothing repeats a retracted claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
