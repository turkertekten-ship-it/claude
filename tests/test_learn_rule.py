#!/usr/bin/env python3
"""Tests for the learned-rules appender.

The rule this guards is the one that makes the section worth having: a rule
without a `because` cannot be reviewed later, so it is refused rather than
written. The rest is bookkeeping that has to be right — numbering, duplicates,
and not swallowing the section that follows.

Run: python3 tests/test_learn_rule.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "learn_rule.py"

sys.path.insert(0, str(REPO / "tools"))
import learn_rule as lr  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOL), *args],
                          capture_output=True, text=True, timeout=60)


BASE = """# Doctrine

Some standing instructions.

## House rules

- Be careful.
"""


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "CLAUDE.md"
        path.write_text(BASE)

        print("a first rule creates the section")
        r = run("add", "--file", str(path), "--category", "tests",
                "--never", "skip the suite", "--because", "a guard nobody ran is not a guard")
        check("exit 0", r.returncode == 0, r.stderr[:120])
        text = path.read_text()
        check("the section exists", lr.SECTION in text)
        check("the rule is numbered 1", "1. [tests] Never skip the suite," in text, text[-200:])
        check("it carries its reason", "because a guard nobody ran is not a guard." in text)
        check("the pre-existing content survives", "## House rules" in text and "Be careful." in text)

        print("\na second rule appends and increments")
        run("add", "--file", str(path), "--category", "git",
            "--always", "fetch before assuming remote state", "--because", "the fleet moves")
        rules = lr.read_rules(path.read_text())
        check("two rules are recorded", len(rules) == 2, rules)
        check("the second is numbered 2", rules[1].startswith("2. [git] Always"), rules[1])
        check("the following heading is not swallowed", "## House rules" in path.read_text())

        print("\nthe things it refuses")
        dup = run("add", "--file", str(path), "--category", "tests",
                  "--never", "skip the suite.", "--because", "A GUARD NOBODY RAN IS NOT A GUARD")
        check("a duplicate is refused", dup.returncode == 1, dup.returncode)
        check("and says it is already recorded", "already recorded" in dup.stderr, dup.stderr[:80])
        check("the duplicate was not written", len(lr.read_rules(path.read_text())) == 2)

        empty = run("add", "--file", str(path), "--category", "x",
                    "--never", "do a thing", "--because", "   ")
        check("an empty reason is refused", empty.returncode == 1, empty.returncode)
        check("and explains why a reason is required",
              "cannot be" in empty.stderr and "reviewed" in empty.stderr, empty.stderr[:100])

        both = run("add", "--file", str(path), "--category", "x",
                   "--never", "a", "--always", "b", "--because", "c")
        check("always and never together are refused", both.returncode == 2, both.returncode)

        missing = run("add", "--file", str(Path(tmp) / "nope.md"), "--category", "x",
                      "--never", "a", "--because", "b")
        check("a missing file exits 2", missing.returncode == 2, missing.returncode)

        print("\ndry run writes nothing")
        before = path.read_text()
        dry = run("add", "--file", str(path), "--category", "style",
                  "--always", "use short sentences", "--because", "they are read",
                  "--dry-run")
        check("exit 0", dry.returncode == 0)
        check("it says what it would do", "would append" in dry.stdout, dry.stdout[:80])
        check("the file is untouched", path.read_text() == before)

        print("\nlisting is honest about an empty section")
        fresh = Path(tmp) / "fresh.md"
        fresh.write_text("# Nothing here\\n")
        listing = run("list", "--file", str(fresh))
        check("exit 0 on a file with no rules", listing.returncode == 0, listing.returncode)
        check("and it says so plainly", "no learned rules yet" in listing.stdout, listing.stdout[:80])
        check("without inventing an example", "1." not in listing.stdout, listing.stdout[:80])

        full = run("list", "--file", str(path))
        check("listing prints both rules", full.stdout.count(". [") == 2, full.stdout)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
