#!/usr/bin/env python3
"""Repair a copy of the chat ingester affected by KI-1.

KI-1: conversations were keyed on `sessionId` alone. Subagent transcripts carry
their PARENT's sessionId, so each transcript file overwrote the previous one and
the run still reported a full message count. See KNOWN_ISSUES.md.

This exists because the fix has to reach copies on branches nobody here can push
to. It is deliberately conservative:

  * it does nothing if the copy already passes its own selfcheck
  * it refuses to write unless the patched file PASSES selfcheck afterwards, so
    a copy is never left worse than it was found
  * it patches text it has matched exactly, and reports rather than guesses when
    the code has drifted

Usage
  python3 tools/fix_ki1.py [path/to/ingest_chat_archive.py] [--write]
Exit
  0 already sound, or patched successfully · 1 needs a manual fix · 2 could not run
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent / "ingest_chat_archive.py"

# The affected shape, as shipped in e37b4c2.
AFFECTED = """        session = record.get("sessionId") or path.stem
        conv = grouped.setdefault(
            session,
            Conversation(id=f"cc:{session}", kind="claude_code", title=None, source_file=rel),
        )
        uuid = record.get("uuid") or f"{session}:{lineno}"
"""

REPAIRED = """        session = record.get("sessionId") or path.stem
        # KI-1: subagent transcripts carry their PARENT's sessionId, so the
        # session alone is not unique across files. Key on the file too.
        key = session if path.stem == session else f"{session}:{path.stem}"
        conv = grouped.setdefault(
            key,
            Conversation(id=f"cc:{key}", kind="claude_code", title=None, source_file=rel),
        )
        uuid = record.get("uuid") or f"{key}:{lineno}"
"""


sys.path.insert(0, str(Path(__file__).resolve().parent))
from fleet_probe import probe_source  # noqa: E402


def is_sound(source: str) -> bool:
    """True if this source keeps two transcripts that share a sessionId.

    Deliberately NOT the copy's own `selfcheck` subcommand: an affected copy
    predates that subcommand, so asking it would report "invalid choice" and
    the fix could never be verified. Behaviour is the oracle, not the CLI.
    """
    sound, _ = probe_source(source)
    return sound


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("target", nargs="?", default=str(DEFAULT))
    parser.add_argument("--write", action="store_true", help="apply the fix in place")
    args = parser.parse_args(argv[1:])

    target = Path(args.target).resolve()
    if not target.is_file():
        print(f"fix_ki1: no such file: {target}", file=sys.stderr)
        return 2

    source = target.read_text(encoding="utf-8")

    if is_sound(source):
        print(f"{target}: already sound — both transcripts survive, nothing to do.")
        return 0

    if AFFECTED not in source:
        print(f"{target}: affected (selfcheck fails), but the code has drifted from")
        print("the shape this patcher knows, so it will not guess.")
        print()
        print("Fix by hand: key each conversation on the session AND the transcript")
        print("file, then build the conversation id and message ids from that key:")
        print()
        print('    key = session if path.stem == session else f"{session}:{path.stem}"')
        print()
        print("Re-run `selfcheck` afterwards, and re-ingest — stored counts do not")
        print("correct themselves.")
        return 1

    patched = source.replace(AFFECTED, REPAIRED, 1)

    # Prove the patch works before touching the real file.
    if not is_sound(patched):
        print(f"{target}: the patch does not fix the behaviour; refusing to write.",
              file=sys.stderr)
        return 1

    if not args.write:
        print(f"{target}: affected by KI-1. The fix applies cleanly and is")
        print("verified by behaviour. Re-run with --write to apply it.")
        return 0

    shutil.copy2(target, target.with_suffix(target.suffix + ".ki1.bak"))
    target.write_text(patched, encoding="utf-8")

    if not is_sound(target.read_text(encoding="utf-8")):
        print(f"{target}: wrote the patch but the behaviour is still wrong.", file=sys.stderr)
        return 1

    print(f"{target}: patched. Both transcripts now survive; original kept as "
          f"{target.name}.ki1.bak")
    print()
    print("Re-ingest your archive. Stored counts do not correct themselves, so an")
    print("index built before this fix is still incomplete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
