#!/usr/bin/env python3
"""Re-run the measurements this repository quotes, and fail when they have moved.

A source is a snapshot. `verify_provenance.py` checks that a `[src:ID]` tag
resolves to a ledger entry; it has no way to know whether the number that entry
records is still the number the command produces. For a measurement of a file
that keeps being edited, "was true when captured" and "is true now" come apart
silently — and after fifteen loops of changes, four of the six scores quoted in
`observations.md` no longer reproduced.

So a quoted measurement is registered here with the command that produced it,
and the command is re-run. A claim that has drifted fails the suite instead of
sitting in the record looking sourced.

This does not replace the ledger. The ledger says what was seen and when; this
says whether it is still so.

Usage
  python3 tools/verify_measurements.py [--json] [--update]
Exit
  0 every measurement reproduces · 1 one or more moved · 2 could not run
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem
    print("verify_measurements: PyYAML is required", file=sys.stderr)
    raise SystemExit(2)

REPO = Path(__file__).resolve().parent.parent
REGISTER = REPO / "provenance" / "measurements.yaml"


def load(register: Path = REGISTER) -> list[dict]:
    if not register.exists():
        raise FileNotFoundError(str(register))
    doc = yaml.safe_load(register.read_text()) or {}
    entries = doc.get("measurements") or []
    if not isinstance(entries, list):
        raise ValueError("top-level `measurements:` must be a list")
    return entries


def run_one(entry: dict) -> tuple[bool, str]:
    command = entry.get("command")
    expect = str(entry.get("expect", ""))
    if not command or not expect:
        return False, "entry is missing `command` or `expect`"
    proc = subprocess.run(
        shlex.split(command), cwd=REPO, capture_output=True, text=True, timeout=300
    )
    output = proc.stdout + proc.stderr
    if expect in output:
        return True, expect
    # Quote back the line that was closest to what was expected, so a drift
    # reads as a number rather than as a wall of output.
    head = expect.split("/")[0].strip()
    nearby = [l.strip() for l in output.splitlines() if head[:2] in l or "/100" in l]
    return False, (nearby[0][:100] if nearby else output.strip().splitlines()[0][:100] if output.strip() else "no output")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="verify_measurements",
        description="Re-run quoted measurements. 0 reproduce, 1 drifted, 2 could not run.",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--register", default=str(REGISTER),
                        help="the register to check (default: provenance/measurements.yaml)")
    args = parser.parse_args(argv[1:])

    try:
        entries = load(Path(args.register))
    except (OSError, ValueError) as exc:
        print(f"verify_measurements: could not run: {exc}", file=sys.stderr)
        return 2

    if not entries:
        print("verify_measurements: the register is empty.")
        print("Nothing is being checked, which is the honest state of a register")
        print("nobody has added to — not a pass.")
        return 0

    results, drifted = [], 0
    for entry in entries:
        try:
            ok, actual = run_one(entry)
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"verify_measurements: {entry.get('id')} could not run: {exc}", file=sys.stderr)
            return 2
        results.append({"id": entry.get("id"), "ok": ok,
                        "expect": entry.get("expect"), "actual": actual})
        if not ok:
            drifted += 1

    if args.json:
        print(json.dumps({"results": results}, indent=2))
    else:
        for r in results:
            mark = "ok  " if r["ok"] else "MOVED"
            print(f"  {mark} {str(r['id']):<28} expected {r['expect']!r}"
                  + ("" if r["ok"] else f", got {r['actual']!r}"))
    if drifted:
        print(f"\nverify_measurements: {drifted} measurement(s) no longer reproduce.",
              file=sys.stderr)
        print("Re-measure and update both the register and the claim that cites it,",
              file=sys.stderr)
        print("or say in the claim what date it was true on.", file=sys.stderr)
        return 1
    print(f"\nverify_measurements: {len(results)} measurement(s) still reproduce")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
