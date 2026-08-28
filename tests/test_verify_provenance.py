#!/usr/bin/env python3
"""Tests for the provenance verifier.

A guard that has never been shown to fail is not a guard. Each case below
proves the verifier rejects one specific way of asserting something
unsupported, and accepts the well-formed equivalent.

Run: python3 tests/test_verify_provenance.py
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"
VERIFIER = REPO / "tools" / "verify_provenance.py"

sys.path.insert(0, str(REPO / "tools"))
import verify_provenance as vp  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def codes_for(fixture: str) -> list[str]:
    known, ledger_findings = vp.load_sources()
    assert not ledger_findings, f"ledger itself is invalid: {[str(f) for f in ledger_findings]}"
    return [f.code for f in vp.scan_markdown(FIXTURES / fixture, set(known))]


def main() -> int:
    print("verifier unit cases")
    check("clean fixture passes", codes_for("clean.md") == [], codes_for("clean.md"))
    check("unsourced claim is caught", "UNSOURCED_CLAIM" in codes_for("unsourced.md"))
    check("unknown source id is caught", "UNKNOWN_SOURCE" in codes_for("unknown_source.md"))
    check("false-memory phrase is caught", "FALSE_MEMORY" in codes_for("false_memory.md"))
    check(
        "false-memory is caught even without front matter",
        codes_for("false_memory.md") == ["FALSE_MEMORY"],
        codes_for("false_memory.md"),
    )
    check(
        "a phrase quoted in inline code is allowed",
        codes_for("clean.md") == [],
        codes_for("clean.md"),
    )
    check(
        "a backticked tag does not count as a citation",
        "UNSOURCED_CLAIM" in codes_for("code_tag_not_citation.md"),
        codes_for("code_tag_not_citation.md"),
    )
    check(
        "unenforced file is not tag-checked",
        "UNSOURCED_CLAIM" not in codes_for("unenforced.md"),
    )

    print("quantity cases")
    ledger = {
        "T-INLINE": {"id": "T-INLINE", "kind": "tool_output",
                     "collected_at": "2026-08-27", "method": "ran it",
                     "evidence": "the run reported 127 messages across 1 conversation"},
        "T-FILE": {"id": "T-FILE", "kind": "filesystem",
                   "collected_at": "2026-08-27", "method": "read it",
                   "evidence": "provenance/raw/sessions-2026-08-27T14-27Z.json"},
    }

    def q(line, led=ledger):
        return vp.check_quantities(line, led)

    check("a digit present in the evidence passes",
          q("Indexed 127 messages. [src:T-INLINE]") == [], q("Indexed 127 messages. [src:T-INLINE]"))
    check("a digit absent from the evidence is caught",
          q("Indexed 999 messages. [src:T-INLINE]") == ["999"], q("Indexed 999 messages. [src:T-INLINE]"))
    check("only the unsupported figure is reported",
          q("127 of 999 kept. [src:T-INLINE]") == ["999"], q("127 of 999 kept. [src:T-INLINE]"))
    check("a spelled-out count is not flagged",
          q("There were three commits. [src:T-INLINE]") == [],
          q("There were three commits. [src:T-INLINE]"))
    check("thousands separators are normalised",
          q("Saw 127 items. [src:T-INLINE]") == [])
    check("a digit inside inline code is not treated as a claim",
          q("Run `--limit 999` on it. [src:T-INLINE]") == [],
          q("Run `--limit 999` on it. [src:T-INLINE]"))
    check("a line with no source tag is not checked",
          q("Some number 999 with no tag.") == [])
    check("evidence naming a capture file is read, not just its path",
          q("Sessions began at 14:07Z. [src:T-FILE]") == [],
          q("Sessions began at 14:07Z. [src:T-FILE]"))
    check("an unsupported digit is still caught through a capture file",
          q("Saw 987654 sessions. [src:T-FILE]") == ["987654"],
          q("Saw 987654 sessions. [src:T-FILE]"))
    check("an unknown source id contributes no evidence but does not crash",
          q("Saw 42 things. [src:NOPE]", {}) == [], q("Saw 42 things. [src:NOPE]", {}))

    print("ledger cases")
    known, findings = vp.load_sources()
    check("real ledger parses cleanly", not findings, [str(f) for f in findings])
    check("real ledger is non-empty", len(known) > 0)
    check(
        "every ledger entry has the required fields",
        all(all(e.get(f) for f in vp.REQUIRED_FIELDS) for e in known.values()),
    )

    print("end-to-end cases")
    ok = subprocess.run(
        [sys.executable, str(VERIFIER), str(REPO)], capture_output=True, text=True
    )
    check("repository scan exits 0", ok.returncode == 0, ok.stderr.strip())

    bad = subprocess.run(
        [sys.executable, str(VERIFIER), str(FIXTURES / "unsourced.md")],
        capture_output=True,
        text=True,
    )
    check("a violating file exits 1", bad.returncode == 1, bad.returncode)
    check("violation is reported on stderr", "UNSOURCED_CLAIM" in bad.stderr)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
