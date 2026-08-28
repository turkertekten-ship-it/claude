#!/usr/bin/env python3
"""Tests for the measurement re-runner.

The defect it exists for is quiet: a number quoted in a document was true when
it was measured and is not true now, and nothing notices. Every case here is
about that being noticed.

Run: python3 tests/test_verify_measurements.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "verify_measurements.py"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def run(register: Path | None = None, *extra: str) -> subprocess.CompletedProcess:
    args = [sys.executable, str(TOOL), *extra]
    if register is not None:
        args += ["--register", str(register)]
    return subprocess.run(args, capture_output=True, text=True, cwd=REPO, timeout=300)


def write(path: Path, body: str) -> None:
    path.write_text("measurements:\n" + body)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        reg = Path(tmp) / "m.yaml"

        print("a measurement that still reproduces")
        write(reg, '  - id: OK\n    command: "python3 -c print(42)"\n    expect: "42"\n')
        r = run(reg)
        check("exits 0", r.returncode == 0, r.stdout + r.stderr)
        check("and says so", "still reproduce" in r.stdout, r.stdout[:120])

        print("\na measurement that has moved")
        write(reg, '  - id: MOVED\n    command: "python3 -c print(43)"\n    expect: "42"\n')
        r = run(reg)
        check("exits 1", r.returncode == 1, r.returncode)
        check("names the entry", "MOVED" in r.stdout, r.stdout[:160])
        check("shows what was expected", "'42'" in r.stdout, r.stdout[:160])
        check("shows what came back", "43" in r.stdout, r.stdout[:160])
        check("and says what to do", "Re-measure" in r.stderr, r.stderr[:160])

        print("\nan empty register is reported, not passed off as a pass")
        write(reg, "")
        r = run(reg)
        check("exits 0", r.returncode == 0, r.returncode)
        check("but says nothing is being checked",
              "not a pass" in r.stdout, r.stdout[:200])

        print("\na malformed or missing register cannot run")
        missing = run(Path(tmp) / "nope.yaml")
        check("a missing register exits 2", missing.returncode == 2, missing.returncode)
        (Path(tmp) / "bad.yaml").write_text("measurements: not-a-list\n")
        bad = run(Path(tmp) / "bad.yaml")
        check("a malformed register exits 2", bad.returncode == 2, bad.returncode)
        write(reg, '  - id: INCOMPLETE\n    command: "python3 -c print(1)"\n')
        incomplete = run(reg)
        check("an entry missing `expect` is a drift, not a pass",
              incomplete.returncode == 1, incomplete.returncode)

        print("\nthe real register is the one the suite runs")
        live = run()
        check("this repository's measurements reproduce", live.returncode == 0,
              live.stdout + live.stderr)
        check("and there are some", "measurement(s) still reproduce" in live.stdout,
              live.stdout[-120:])

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
