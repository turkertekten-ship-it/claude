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

    print("\nreview reports without changing anything")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "CLAUDE.md"
        path.write_text(BASE)
        run("add", "--file", str(path), "--category", "output",
            "--never", "exceed a stated limit on length", "--because", "an answer ran over")
        clean = run("review", "--file", str(path))
        check("a single rule reviews clean", clean.returncode == 0, clean.stdout)
        check("and the size is reported", "1 rule(s)" in clean.stdout, clean.stdout[:80])

        before = path.read_text()
        run("add", "--file", str(path), "--category", "output",
            "--always", "exceed a stated limit on length when asked", "--because", "a reader wanted more")
        contra = run("review", "--file", str(path))
        check("an opposite rule in the same category is a contradiction",
              contra.returncode == 1 and "CONTRADICTION" in contra.stdout, contra.stdout[:200])

        run("add", "--file", str(path), "--category", "docs",
            "--never", "quote a score or a count you did not re-run", "--because", "numbers drift")
        run("add", "--file", str(path), "--category", "docs",
            "--never", "quote a count or a score you did not re-run yourself", "--because", "they drift")
        dup = run("review", "--file", str(path))
        check("a restatement is a near-duplicate",
              "NEAR-DUPLICATE" in dup.stdout, dup.stdout[:300])

        budget = run("review", "--file", str(path), "--max-words", "5", "--max-share", "1")
        check("a budget overrun fails", budget.returncode == 1, budget.returncode)
        check("and says what the budget was",
              "OVER BUDGET" in budget.stdout and "exceeds 5 words" in budget.stdout, budget.stdout[:200])
        check("review deletes nothing", len(lr.read_rules(path.read_text())) == 4,
              lr.read_rules(path.read_text()))

        gone = run("review", "--file", str(Path(tmp) / "nope.md"))
        check("a missing file exits 2", gone.returncode == 2, gone.returncode)

    print("\nan enforcement claim is itself a claim")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "CLAUDE.md"
        path.write_text(BASE)
        bogus = run("add", "--file", str(path), "--category", "x", "--never", "y",
                    "--because", "z", "--enforced-by", "tools/imaginary.py")
        check("naming a guard that does not exist is refused", bogus.returncode == 1, bogus.returncode)
        check("and says why", "does not exist" in bogus.stderr, bogus.stderr[:100])
        check("nothing was written", lr.read_rules(path.read_text()) == [])

        real = run("add", "--file", str(path), "--category", "guards", "--never",
                   "skip the suite", "--because", "it caught a real failure",
                   "--enforced-by", "githooks/pre-push")
        check("a real guard is accepted", real.returncode == 0, real.stderr[:120])
        check("and is recorded on the rule",
              "[enforced by: githooks/pre-push]" in path.read_text(), path.read_text()[-160:])

        run("add", "--file", str(path), "--category", "docs", "--never",
            "quote a number you did not re-run", "--because", "they drift")
        a = run("annotate", "2", "--file", str(path), "--enforced-by", "tools/verify_measurements.py")
        check("annotate names a guard on an existing rule", a.returncode == 0, a.stderr[:120])
        check("the tag is on rule 2",
              "verify_measurements" in lr.read_rules(path.read_text())[1], lr.read_rules(path.read_text())[1])
        twice = run("annotate", "2", "--file", str(path), "--enforced-by", "githooks/pre-push")
        check("annotating twice is refused", twice.returncode == 1, twice.returncode)
        missing = run("annotate", "99", "--file", str(path), "--enforced-by", "githooks/pre-push")
        check("annotating a rule that does not exist is refused", missing.returncode == 1)
        fake = run("annotate", "1", "--file", str(path), "--enforced-by", "tools/nope.py")
        check("annotate verifies the guard exists too", fake.returncode == 1, fake.stderr[:80])

        review = run("review", "--file", str(path))
        check("the review counts what is enforced",
              "2 enforced by a guard" in review.stdout, review.stdout[:220])

        run("add", "--file", str(path), "--category", "misc", "--never",
            "forget things", "--because", "memory fades")
        review2 = run("review", "--file", str(path))
        check("a rule with neither is counted as list-only",
              "1 in this list only" in review2.stdout, review2.stdout[:240])
        check("and the report says why that is weak",
              "weakest place a rule can live" in review2.stdout, review2.stdout[:300])

        print("\na rule that cannot be enforced can still be routed")
        routed = run("annotate", "3", "--file", str(path),
                     "--routed-to", ".claude/skills/ooda/SKILL.md")
        check("routing to a real document is accepted", routed.returncode == 0, routed.stderr[:120])
        check("and is recorded", "[routed to: .claude/skills/ooda/SKILL.md]" in path.read_text())
        review3 = run("review", "--file", str(path))
        check("the review counts it as routed, not enforced",
              "1 routed to where they are read" in review3.stdout and
              "0 in this list only" in review3.stdout, review3.stdout[:240])
        nowhere = run("annotate", "3", "--file", str(path), "--routed-to", "docs/imaginary.md")
        check("routing to a document that does not exist is refused",
              nowhere.returncode == 1, nowhere.returncode)
        both = run("annotate", "3", "--file", str(path),
                   "--routed-to", "CLAUDE.md", "--enforced-by", "githooks/pre-push")
        check("naming both a guard and a route at once is refused", both.returncode == 2, both.returncode)

    print("\na wrong rule is superseded, not deleted")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "CLAUDE.md"
        path.write_text(BASE)
        run("add", "--file", str(path), "--category", "guards",
            "--never", "ship a guard that matches prose", "--because", "it misfired")
        r = run("supersede", "1", "--file", str(path), "--category", "guards",
                "--never", "ship a guard that matches an open category in prose",
                "--because", "the first version condemned a guard that works")
        check("supersede exits 0", r.returncode == 0, r.stdout + r.stderr)
        rules = lr.read_rules(path.read_text())
        check("the old rule is still there", len(rules) == 2, rules)
        check("and is marked", "superseded by rule 2" in rules[0], rules[0])
        check("its reason survives", "it misfired" in rules[0], rules[0])
        check("the new rule is plain", "superseded" not in rules[1], rules[1])

        review = run("review", "--file", str(path))
        check("the pair is not reported as a contradiction",
              "CONTRADICTION" not in review.stdout, review.stdout)
        check("nor as a near-duplicate, though they overlap heavily",
              "NEAR-DUPLICATE" not in review.stdout, review.stdout)
        check("the superseded one is counted and named",
              "1 superseded" in review.stdout, review.stdout)

        again = run("supersede", "1", "--file", str(path), "--category", "guards",
                    "--never", "do a third thing", "--because", "a third reason")
        check("superseding it twice is refused",
              again.returncode == 1 and "already superseded" in again.stderr, again.stderr[:100])
        gone = run("supersede", "99", "--file", str(path), "--category", "x",
                   "--never", "y", "--because", "z")
        check("superseding a rule that does not exist is refused",
              gone.returncode == 1 and "no rule numbered" in gone.stderr, gone.stderr[:100])

        before = path.read_text()
        dry = run("supersede", "2", "--file", str(path), "--category", "x",
                  "--never", "y", "--because", "z", "--dry-run")
        check("--dry-run writes nothing", path.read_text() == before and dry.returncode == 0)

    print("\nprune removes what was retired, and nothing else")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "CLAUDE.md"
        path.write_text(BASE)
        empty = run("prune", "--file", str(path))
        check("nothing to prune is not an error", empty.returncode == 0, empty.returncode)
        check("and says so", "nothing superseded" in empty.stdout, empty.stdout[:80])

        run("add", "--file", str(path), "--category", "a", "--never", "one thing",
            "--because", "a reason")
        run("add", "--file", str(path), "--category", "b", "--never", "two thing",
            "--because", "b reason")
        run("supersede", "1", "--file", str(path), "--category", "a",
            "--never", "one thing, more precisely", "--because", "the first was too broad")
        before = path.read_text()
        dry = run("prune", "--file", str(path), "--dry-run")
        check("--dry-run writes nothing", path.read_text() == before and dry.returncode == 0)
        check("and names what it would remove", "1. [a]" in dry.stdout, dry.stdout[:120])

        run("prune", "--file", str(path))
        rules = lr.read_rules(path.read_text())
        check("the superseded rule is gone", len(rules) == 2, rules)
        check("the live rules survive", all("superseded" not in r for r in rules), rules)
        check("numbering is left alone, so the gap shows",
              rules[0].startswith("2.") and rules[1].startswith("3."), rules)
        check("the pre-existing document is untouched", "## House rules" in path.read_text())

    print("\nthe thresholds are the ones the real collisions sit at")
    check("contradiction threshold is 0.5", lr.CONTRADICTION == 0.5, lr.CONTRADICTION)
    check("near-duplicate threshold is 0.5", lr.NEAR_DUPLICATE == 0.5, lr.NEAR_DUPLICATE)
    check("overlap is symmetric", lr.overlap({"a","b"}, {"b","c"}) == lr.overlap({"b","c"}, {"a","b"}))
    check("an empty rule overlaps nothing", lr.overlap(set(), {"a"}) == 0.0)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
