#!/usr/bin/env python3
"""Tests for the installer's staleness check.

What runs in every other terminal is the installed copy, not this repository.
Until this check existed, the two stayed in step only because somebody
remembered to re-run the installer — which is the failure mode this repository
exists to guard against, one level up.

Every case runs against a temporary prefix, so the real ~/.claude is untouched.

Run: python3 tests/test_install_check.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALLER = REPO / "tools" / "install_prompt_system.sh"

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def run(*args: str, prefix: Path, bindir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(INSTALLER), *args, "--prefix", str(prefix), "--bin-dir", str(bindir)],
        capture_output=True, text=True, cwd=REPO, timeout=300,
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        prefix, bindir = Path(tmp) / "claude", Path(tmp) / "bin"

        print("a machine with nothing installed is not 'stale'")
        fresh = run("--check", prefix=prefix, bindir=bindir)
        check("exit 0", fresh.returncode == 0, fresh.stdout[-200:])
        check("and it says what to run", "Run: bash tools" in fresh.stdout, fresh.stdout[:120])
        check("a read-only check writes nothing", not prefix.exists() and not bindir.exists(),
              f"{prefix.exists()=} {bindir.exists()=}")

        print("\ninstalling, then checking")
        install = run(prefix=prefix, bindir=bindir)
        check("install exits 0", install.returncode == 0, install.stdout[-300:])
        after = run("--check", prefix=prefix, bindir=bindir)
        check("a fresh install is in sync", after.returncode == 0, after.stdout[-200:])
        check("every file is compared, markdown included",
              after.stdout.count("same") >= 10, after.stdout)

        print("\ndrift is caught, in either kind of file")
        tool = prefix / "tools" / "prompt_forge.py"
        tool.write_text(tool.read_text() + "\n# drift\n")
        drifted = run("--check", prefix=prefix, bindir=bindir)
        check("a drifted tool fails", drifted.returncode == 1, drifted.returncode)
        check("and is named", "DRIFTED  tools/prompt_forge.py" in drifted.stdout, drifted.stdout)

        doc = prefix / "commands" / "prompt.md"
        doc.write_text(doc.read_text() + "\nextra\n")
        both = run("--check", prefix=prefix, bindir=bindir)
        check("a drifted command is caught too",
              "DRIFTED  commands/prompt.md" in both.stdout, both.stdout)
        check("the count is reported", "2 file(s) differ" in both.stdout, both.stdout[-300:])

        (prefix / "tools" / "learn_rule.py").unlink()
        missing = run("--check", prefix=prefix, bindir=bindir)
        check("a missing file is caught", "MISSING  tools/learn_rule.py" in missing.stdout,
              missing.stdout)

        print("\nreinstalling repairs it")
        run(prefix=prefix, bindir=bindir)
        repaired = run("--check", prefix=prefix, bindir=bindir)
        check("back in sync", repaired.returncode == 0, repaired.stdout[-200:])

        print("\nthe rewrite is part of the comparison, not a false difference")
        installed_cmd = (prefix / "commands" / "prompt.md").read_text()
        source_cmd = (REPO / ".claude" / "commands" / "prompt.md").read_text()
        check("the installed copy differs from source by the rewrite",
              installed_cmd != source_cmd)
        check("and the check still calls it the same",
              "same     commands/prompt.md" in repaired.stdout, repaired.stdout)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
