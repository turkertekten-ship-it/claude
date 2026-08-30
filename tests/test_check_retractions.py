#!/usr/bin/env python3
"""A retracted claim must not be allowed to reappear, and a quote must be allowed.

An early check decided Claude Code ignored the output ceiling. That verdict
reached docs/parity.md and README.md, was retracted when the check turned out
to be looking for the wrong evidence, and the retraction reached those two
files and stopped -- `workbench doctor` repeated it for two more days, through
an audit, a security review and a green suite. Nothing connected a correction
to the places still asserting what it corrected.

Both directions matter. A guard that flags every mention would flag the
retraction notice itself, and the ledger, and this file.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if condition else 'FAIL'} {name}" + (f" {detail}" if not condition else ""))
    if not condition:
        FAILURES.append(name)


LEDGER = """sources:
  - id: FIXED-2026-01-02
    kind: filesystem
    collected_at: "2026-01-02T00:00Z"
    method: a probe
    evidence: a probe
    retracts:
      supersedes: BROKEN-2026-01-01
      phrases:
        - "the widget is broken"
"""


def run_in(tmp: Path, doc: str) -> subprocess.CompletedProcess:
    (tmp / "provenance").mkdir(parents=True, exist_ok=True)
    (tmp / "provenance" / "sources.yaml").write_text(LEDGER, encoding="utf-8")
    (tmp / "tools").mkdir(exist_ok=True)
    (tmp / "tools" / "check_retractions.py").write_text(
        (REPO / "tools" / "check_retractions.py").read_text(encoding="utf-8"), encoding="utf-8")
    (tmp / "README.md").write_text(doc, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp, timeout=60)
    subprocess.run(["git", "add", "-A"], cwd=tmp, timeout=60)
    return subprocess.run([sys.executable, str(tmp / "tools" / "check_retractions.py")],
                          cwd=tmp, capture_output=True, text=True, timeout=90)


def main() -> int:
    print("retracted-claim check")
    with tempfile.TemporaryDirectory(prefix="retract-") as raw:
        r = run_in(Path(raw), "All good here.\n")
        check("a clean tree passes", r.returncode == 0, r.stdout + r.stderr)

    with tempfile.TemporaryDirectory(prefix="retract-") as raw:
        r = run_in(Path(raw), "Note that the widget is broken and always was.\n")
        check("a reasserted retracted claim is REJECTED", r.returncode == 1,
              r.stdout + r.stderr)
        check("and names the file", "README.md" in r.stdout, r.stdout)
        check("and names the superseded entry", "BROKEN-2026-01-01" in r.stdout, r.stdout)

    with tempfile.TemporaryDirectory(prefix="retract-") as raw:
        r = run_in(Path(raw), "It no longer says `the widget is broken`.\n")
        check("the same phrase in inline code is a QUOTE, not a claim",
              r.returncode == 0, r.stdout + r.stderr)

    with tempfile.TemporaryDirectory(prefix="retract-") as raw:
        r = run_in(Path(raw), "assert 'the widget is broken' not in out  # retraction-quote\n")
        check("a guard naming the phrase it guards against is allowed",
              r.returncode == 0, r.stdout + r.stderr)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
