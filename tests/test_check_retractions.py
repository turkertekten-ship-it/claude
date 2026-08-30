#!/usr/bin/env python3
"""A retracted claim must not be allowed to reappear, and a quote must be allowed.

The fixture phrase is deliberately unlike anything in the repository. The
first version reused the tool docstring's own example, and since the tool
searches every file including its own source, three cases failed on a
collision between the test fixture and the documentation.

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
        - "the flange was over-torqued"
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
        r = run_in(Path(raw), "Note that the flange was over-torqued and always was.\n")
        check("a reasserted retracted claim is REJECTED", r.returncode == 1,
              r.stdout + r.stderr)
        check("and names the file", "README.md" in r.stdout, r.stdout)
        check("and names the superseded entry", "BROKEN-2026-01-01" in r.stdout, r.stdout)

    with tempfile.TemporaryDirectory(prefix="retract-") as raw:
        r = run_in(Path(raw), "It no longer says `the flange was over-torqued`.\n")
        check("the same phrase in inline code is a QUOTE, not a claim",
              r.returncode == 0, r.stdout + r.stderr)

    with tempfile.TemporaryDirectory(prefix="retract-") as raw:
        r = run_in(Path(raw), "assert 'the flange was over-torqued' not in out  # retraction-quote\n")
        check("a guard naming the phrase it guards against is allowed",
              r.returncode == 0, r.stdout + r.stderr)

    # Every evasion an adversarial review demonstrated. Each was exit 0 before.
    evasions = [
        ("a line wrap", "The harness found that the flange was\nover-torqued, sadly.\n"),
        ("a sentence-initial capital", "The flange was over-torqued. Everyone knows.\n"),
        ("a double space", "Note that the  flange was over-torqued.\n"),
        ("asserting AND quoting on one line",
         "the flange was over-torqued, which is why `the flange was over-torqued` was retracted.\n"),
    ]
    for label, doc in evasions:
        with tempfile.TemporaryDirectory(prefix="retract-") as raw:
            r = run_in(Path(raw), doc)
            check(f"{label} does not hide a retracted claim", r.returncode == 1,
                  r.stdout + r.stderr)

    # An untracked file is the likeliest place a retracted claim reappears, and
    # the tool was blind to exactly that on its first day -- including to its
    # own source, which is why the suite went red the moment it was committed.
    with tempfile.TemporaryDirectory(prefix="retract-") as raw:
        tmp = Path(raw)
        r = run_in(tmp, "clean\n")
        (tmp / "NOTES.md").write_text("the flange was over-torqued\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(tmp / "tools" / "check_retractions.py")],
                           cwd=tmp, capture_output=True, text=True, timeout=90)
        check("an UNTRACKED file is still searched", r.returncode == 1,
              r.stdout + r.stderr)

    # "2 when it cannot run" was false for every malformed input.
    malformed = [
        ("sources that is not a list", "sources: 3\n"),
        ("an entry that is not a mapping", "sources:\n  - just a string\n"),
        ("retracts that is not a mapping",
         'sources:\n  - id: X\n    kind: filesystem\n    collected_at: "2026-01-01T00:00Z"\n'
         "    method: m\n    evidence: e\n    retracts: nonsense\n"),
        ("phrases as a bare string",
         'sources:\n  - id: X\n    kind: filesystem\n    collected_at: "2026-01-01T00:00Z"\n'
         "    method: m\n    evidence: e\n    retracts:\n      supersedes: Y\n"
         '      phrases: "the flange was over-torqued"\n'),
        ("a retraction with no phrases",
         'sources:\n  - id: X\n    kind: filesystem\n    collected_at: "2026-01-01T00:00Z"\n'
         "    method: m\n    evidence: e\n    retracts:\n      supersedes: Y\n"),
    ]
    for label, ledger in malformed:
        with tempfile.TemporaryDirectory(prefix="retract-") as raw:
            tmp = Path(raw)
            (tmp / "provenance").mkdir(parents=True)
            (tmp / "provenance" / "sources.yaml").write_text(ledger, encoding="utf-8")
            (tmp / "tools").mkdir()
            (tmp / "tools" / "check_retractions.py").write_text(
                (REPO / "tools" / "check_retractions.py").read_text(encoding="utf-8"),
                encoding="utf-8")
            (tmp / "README.md").write_text("hello\n", encoding="utf-8")
            r = subprocess.run([sys.executable, str(tmp / "tools" / "check_retractions.py")],
                               cwd=tmp, capture_output=True, text=True, timeout=90)
            check(f"{label} exits 2, not 1", r.returncode == 2,
                  f"got {r.returncode}: {(r.stdout + r.stderr)[:150]}")

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
