#!/usr/bin/env python3
"""The stale-measurement check must reject drift and accept a match.

Written after a ledger entry recording "the operating prompt is 573 tokens"
survived the promotion that replaced the file it measured. The guard is only
real once it has been watched rejecting something, so this watches it in both
directions against a temporary ledger rather than the repository's own.
"""

from __future__ import annotations

import hashlib
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


def run_against(ledger_text: str, tmp: Path) -> subprocess.CompletedProcess:
    """Run the checker against a throwaway repository containing one entry."""
    (tmp / "provenance").mkdir(parents=True, exist_ok=True)
    (tmp / "provenance" / "sources.yaml").write_text(ledger_text, encoding="utf-8")
    (tmp / "tools").mkdir(exist_ok=True)
    (tmp / "tools" / "check_measurements.py").write_text(
        (REPO / "tools" / "check_measurements.py").read_text(encoding="utf-8"), encoding="utf-8")
    return subprocess.run([sys.executable, str(tmp / "tools" / "check_measurements.py")],
                          capture_output=True, text=True, timeout=60)


def entry(path: str, sha: str) -> str:
    return (
        "sources:\n"
        "  - id: PROBE-2026-01-01\n"
        "    kind: filesystem\n"
        '    collected_at: "2026-01-01T00:00Z"\n'
        "    method: a probe\n"
        "    evidence: a probe\n"
        "    measures:\n"
        f'      {path}: "sha256:{sha}"\n'
    )


def main() -> int:
    print("stale-measurement check")
    with tempfile.TemporaryDirectory(prefix="meascheck-") as raw:
        tmp = Path(raw)
        subject = tmp / "prompts"
        subject.mkdir()
        target = subject / "thing.md"
        target.write_text("the measured content\n", encoding="utf-8")
        good = hashlib.sha256(target.read_bytes()).hexdigest()

        r = run_against(entry("prompts/thing.md", good), tmp)
        check("an unchanged file passes", r.returncode == 0, r.stdout + r.stderr)
        check("and says so", "still matches" in r.stdout, r.stdout)

        target.write_text("the content, edited later\n", encoding="utf-8")
        r = run_against(entry("prompts/thing.md", good), tmp)
        check("a changed file is REJECTED", r.returncode == 1, r.stdout + r.stderr)
        check("and names the entry", "PROBE-2026-01-01" in r.stdout, r.stdout)
        check("and says the claim is not evidence about the current file",
              "not" in r.stdout and "current one" in r.stdout, r.stdout)

        target.unlink()
        r = run_against(entry("prompts/thing.md", good), tmp)
        check("a deleted file is REJECTED", r.returncode == 1, r.stdout + r.stderr)
        check("and says the measurement describes nothing",
              "describes nothing" in r.stdout, r.stdout)

        r = run_against("sources:\n  - id: X\n    kind: filesystem\n"
                        '    collected_at: "2026-01-01T00:00Z"\n'
                        "    method: m\n    evidence: e\n", tmp)
        check("an unannotated ledger is not an error", r.returncode == 0, r.stdout + r.stderr)

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} case(s): {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
