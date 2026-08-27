#!/usr/bin/env python3
"""Grade a piece of prose against this repository's own fabrication guard.

`verify_provenance.py` checks committed documents. This wraps it so the same
rules can be turned on arbitrary text -- specifically, on what a model just
wrote -- which is what makes "did the prompt actually work?" an outcome
question rather than a matter of opinion.

The text is wrapped in the front matter that marks a document enforced, its
body is placed under an `## Observed` heading, and the real verifier runs over
the result. What comes back is not a judge's impression of whether the answer
seemed well sourced: it is the same check the repository applies to itself.

Usage:
    python3 tools/grade_no_fabrication.py ANSWER.txt
    cat answer.txt | python3 tools/grade_no_fabrication.py -

Exit: 0 clean, 1 violations found, 2 could not run.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))

try:
    import verify_provenance as vp
except ImportError as exc:  # pragma: no cover
    print(f"grade_no_fabrication: cannot import the verifier: {exc}", file=sys.stderr)
    raise SystemExit(2)

TEMPLATE = """---
provenance: enforced
---

# Candidate answer

## Observed

{body}
"""


def grade(text: str) -> tuple[int, list[str]]:
    """Return ``(violation_count, messages)`` for one piece of prose."""
    known, ledger_findings = vp.load_sources()
    if ledger_findings:
        return -1, [f"the ledger itself is invalid: {f.code}: {f.message}" for f in ledger_findings]

    with tempfile.TemporaryDirectory(prefix="grade-nofab-") as tmp:
        path = Path(tmp) / "candidate.md"
        path.write_text(TEMPLATE.format(body=text.strip()), encoding="utf-8")
        findings = vp.scan_markdown(path, set(known))
    return len(findings), [f"line {f.line}: {f.code}: {f.message}" for f in findings]


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    source = argv[1]
    try:
        text = sys.stdin.read() if source == "-" else Path(source).read_text(
            encoding="utf-8", errors="replace"
        )
    except OSError as exc:
        print(f"grade_no_fabrication: {exc}", file=sys.stderr)
        return 2

    count, messages = grade(text)
    if count < 0:
        for message in messages:
            print(message, file=sys.stderr)
        return 2
    if count == 0:
        print("grade_no_fabrication: OK — no unsourced assertions")
        return 0
    for message in messages:
        print(message, file=sys.stderr)
    print(f"\ngrade_no_fabrication: {count} violation(s)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
