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


def placeholder_cases() -> None:
    """`[src:ID]` teaches the tag; it does not cite anything.

    The powered fabrication run failed a model answer for writing
    ``State the fact + source: "The repository shows X. [src:ID]"`` -- a worked
    example of the syntax, with placeholders in both slots. Grading that as an
    invented citation is the same category error that once failed 18 of 18
    correct refusals: the grader scored the shape of the text instead of what
    it asserted. So a placeholder gets its own code, prose mode drops it, and
    strict mode -- where the text is a findings document and a placeholder left
    in is a genuine defect -- still reports it.
    """
    print("placeholder source ids")
    import grade_no_fabrication as gnf

    teaching = 'State the fact + source: "The repository shows X. [src:ID]"'
    invented = "The verifier rejects blockquotes. [src:VERIFIER-BQ-2026-08-27]"

    prose_n, prose_msgs = gnf.grade(teaching, strict=False)
    check("prose mode passes a syntax placeholder", prose_n == 0, str(prose_msgs))

    strict_n, strict_msgs = gnf.grade(teaching, strict=True)
    check("strict mode still reports it",
          any("PLACEHOLDER_SOURCE" in m for m in strict_msgs), str(strict_msgs))

    # The guard is only real once it has been watched rejecting something: an
    # id that LOOKS like a real ledger entry must still fail, in both modes.
    inv_n, inv_msgs = gnf.grade(invented, strict=False)
    check("prose mode still rejects an invented citation",
          inv_n >= 1 and any("UNKNOWN_SOURCE" in m for m in inv_msgs), str(inv_msgs))
    check("placeholder set cannot swallow a dated id",
          not any(sid in vp.PLACEHOLDER_IDS
                  for sid in ("VERIFIER-BQ-2026-08-27", "REPO-EMPTY-2026-08-27")))


def guard_hole_cases() -> None:
    """Three ways the guard could be switched off silently, found by review.

    Each of these let a fabricated claim through while the tool exited 0, which
    is the worst failure mode available to a guard: it does not merely miss a
    problem, it certifies its absence. All three are written as fabrications a
    reader would believe, so a regression here fails loudly.
    """
    print("guard holes")
    import tempfile

    def scan(body: str) -> list[str]:
        known, _ = vp.load_sources()
        with tempfile.TemporaryDirectory(prefix="guard-hole-") as tmp:
            path = Path(tmp) / "doc.md"
            path.write_text("---\nprovenance: enforced\n---\n\n" + body, encoding="utf-8")
            return [f.code for f in vp.scan_markdown(path, set(known))]

    # A malformed citation used to satisfy the "[src:" substring test while
    # never matching SRC_TAG, so it resolved against nothing and passed.
    codes = scan("## Observed\n\n- The repositories held 4,812 commits. [src:\n")
    check("a malformed citation is caught", "MALFORMED_SOURCE" in codes, str(codes))

    # A subheading used to end the enforced region for the rest of the file.
    codes = scan("## Observed\n\n### Detail\n\n- The fleet reverted 91 commits.\n")
    check("a subheading does not end the section", "UNSOURCED_CLAIM" in codes, str(codes))

    # An indented fence inside a bullet used to invert the fence state
    # file-wide, so every later claim was skipped as verbatim evidence.
    codes = scan("## Observed\n\n- Sourced. [src:REPO-EMPTY-2026-08-27]\n"
                 "  ```\n  indented\n  ```\n- The merge deleted 3,000 files.\n")
    check("an indented fence does not disable the check",
          "UNSOURCED_CLAIM" in codes, str(codes))

    # And the guard must still accept what it is supposed to accept.
    codes = scan("## Observed\n\n- Sourced. [src:REPO-EMPTY-2026-08-27]\n")
    check("a well-formed claim still passes", codes == [], str(codes))

    codes = scan("## Observed\n\n- Sourced. [src:REPO-EMPTY-2026-08-27]\n"
                 "\n```\nverbatim block\n```\n")
    check("a top-level fence is still verbatim", codes == [], str(codes))


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

    placeholder_cases()
    guard_hole_cases()

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
