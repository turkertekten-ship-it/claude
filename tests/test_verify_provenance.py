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


def verbatim_cases() -> None:
    """A capture that QUOTES a banned phrase is evidence, not an assertion.

    provenance/raw/ holds verbatim tool output. A transcript recording a model
    writing `[src:ID]`, or a fetched page containing `as we discussed`, is
    quoting. Demanding that a quotation resolve to this repository's ledger is
    the same category error as demanding a source tag on conversational prose --
    and it fired on a real captured eval report before this exclusion existed.
    """
    print("verbatim capture cases")
    raw = REPO / "provenance" / "raw"
    probe = raw / "_verifier_probe.md"
    probe.write_text(
        "# capture\n\nA model wrote: [src:NOT-A-REAL-ID] and said as we discussed.\n",
        encoding="utf-8",
    )
    try:
        scanned = [p for p in vp.markdown_files([REPO])]
        check("provenance/raw/ is not scanned for claims", probe not in scanned)
        # But the same content IS caught anywhere else.
        elsewhere = REPO / "docs" / "_verifier_probe.md"
        elsewhere.write_text(probe.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            known, _ = vp.load_sources()
            codes = [f.code for f in vp.scan_markdown(elsewhere, set(known))]
            check("the same content outside raw/ is still caught",
                  "UNKNOWN_SOURCE" in codes and "FALSE_MEMORY" in codes, str(codes))
            check("and docs/ is still scanned", elsewhere in vp.markdown_files([REPO]))
        finally:
            elsewhere.unlink(missing_ok=True)
    finally:
        probe.unlink(missing_ok=True)


def main() -> int:
    verbatim_cases()
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
