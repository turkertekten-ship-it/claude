#!/usr/bin/env python3
"""Report ledger measurements whose subject has changed since they were taken.

The failure this exists for happened here. A ledger entry recorded that the
operating prompt was 573 tokens, measuring `prompts/base-operator.md`. Later
that same session, promoting a new prompt replaced that file with a longer one.
Nothing connected the two, so the measurement went on being published as a fact
about the current prompt while describing a file that had been renamed out from
under it. [src:STALE-CLAIMS-AUDIT-2026-08-29]

An earlier attempt to mechanise fact-checking failed and was deleted, because
the errors it hunted were relational and a corpus-membership test cannot see a
relation [src:FIGURE-CHECK-FAILS-2026-08-29]. This one is narrower on purpose,
and narrow enough to work: it compares a recorded fingerprint against the
current one. That is arithmetic, not judgement.

**How to use it.** An entry that measures a file records what it measured:

    measures:
      prompts/base-operator.md: "sha256:7d60c7f8..."

The field is optional and additive -- `verify_provenance.py` enforces only the
required fields, so unannotated entries are unaffected. Annotate an entry when
changing the file would make the claim WRONG, not merely when the entry
mentions a path. Fifty of ninety entries here name a file; only a few measure
one.

What it cannot do: tell you an unannotated measurement went stale, or recover a
hash nobody recorded. Retro-fitting today's hash to an old entry would assert a
file state nobody observed, which is the thing this repository exists to
refuse.

Exit 0 when every annotated measurement still matches, 1 when any has drifted,
2 when it cannot run.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
LEDGER = REPO / "provenance" / "sources.yaml"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str]) -> int:
    if not LEDGER.exists():
        print("provenance/sources.yaml is missing", file=sys.stderr)
        return 2
    try:
        entries = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))["sources"]
    except (yaml.YAMLError, KeyError, TypeError) as exc:
        print(f"ledger will not parse: {exc}", file=sys.stderr)
        return 2

    annotated = [e for e in entries if e.get("measures")]
    print("Ledger measurements against the files they measured")
    print("=" * 68)
    print(f"{len(annotated)} of {len(entries)} entries record what they measured.")
    print()

    drifted = 0
    for entry in annotated:
        for rel, recorded in entry["measures"].items():
            path = REPO / rel
            if not path.exists():
                print(f"[GONE ] {entry['id']}")
                print(f"        {rel} no longer exists; the measurement describes nothing")
                drifted += 1
                continue
            current = digest(path)
            if current == recorded:
                print(f"[ok   ] {entry['id']}  {rel}")
                continue
            print(f"[STALE] {entry['id']}")
            print(f"        {rel} has changed since this was measured")
            print(f"        recorded {recorded[:23]}…  now {current[:23]}…")
            print(f"        The claim may still be true of the OLD file. It is not")
            print(f"        evidence about the current one until it is re-measured.")
            drifted += 1

    print()
    if drifted:
        print(f"check_measurements: {drifted} measurement(s) describe a file that has changed.")
        print("Re-measure, or say in the entry which file version the number is about.")
        return 1
    print("check_measurements: every recorded measurement still matches its file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
