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
      supersedes: MAX-OUTPUT-TOKENS-NOT-HONOURED-2026-08-27
      phrases:
        - "records it as a FAIL"

and every tracked file is searched for those phrases. The ledger entry that
declares the retraction is skipped -- it must quote what it retracts -- as is
`provenance/raw/`, which holds verbatim captures.

Deliberately a string search. The earlier attempt to mechanise fact-checking
died because relational errors need judgement [src:FIGURE-CHECK-FAILS-2026-08-29];
a retracted phrase reappearing is not a judgement, it is a grep, and a grep is
a thing a tool can be trusted with.

What it cannot do: catch a retracted claim restated in different words. The
phrase list is only as good as the phrases someone thought to write down.

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
SKIP_DIRS = {"provenance/raw", ".workbench", ".git"}


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO,
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return []
    files = []
    for rel in out.stdout.splitlines():
        if any(rel.startswith(d) for d in SKIP_DIRS):
            continue
        path = REPO / rel
        if path.is_file():
            files.append(path)
    return files


def main(argv: list[str]) -> int:
    if not LEDGER.exists():
        print("provenance/sources.yaml is missing", file=sys.stderr)
        return 2
    try:
        entries = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))["sources"]
    except (yaml.YAMLError, KeyError, TypeError) as exc:
        print(f"ledger will not parse: {exc}", file=sys.stderr)
        return 2

    declared = [e for e in entries if e.get("retracts")]
    files = tracked_files()
    if not files:
        print("no tracked files found; run this inside the repository", file=sys.stderr)
        return 2

    print("Retracted claims, and whether anything still repeats them")
    print("=" * 68)
    print(f"{len(declared)} of {len(entries)} entries declare a retraction; "
          f"{len(files)} tracked file(s) searched.")
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
                if phrase not in text:
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
                asserting = [
                    line for line in text.splitlines()
                    if phrase in line
                    and "retraction-quote" not in line
                    and phrase not in " ".join(INLINE_CODE.findall(line))
                ]
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
