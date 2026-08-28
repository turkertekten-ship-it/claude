#!/usr/bin/env python3
"""Tests for the output checker.

Two properties carry the tool. First, it must catch the failure that caused it
to exist: an 80-word limit met with 86 words. Second, it must never claim more
than it checked — a constraint it could not interpret has to appear in the
unchecked list rather than vanish.

Run: python3 tests/test_check_output.py
"""

import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "check_output.py"

sys.path.insert(0, str(REPO / "tools"))
import check_output as co  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def rules(prompt: str, output: str) -> dict[str, bool]:
    return {c.rule: c.ok for c in co.check(prompt, output).checks}


SLOTTED = """## CONTEXT
The existing module has 400 lines and 12 functions.

## TASK
Summarise it.

## CONSTRAINTS
One paragraph of continuous prose. No bullet points, no headings, no bold labels.
Under 80 words. Keep the numbers.

## OUTPUT CONTRACT
A single paragraph. No preamble.
"""


def main() -> int:
    print("the failure that caused the tool to exist")
    over = " ".join(["word"] * 86)
    r = co.check(SLOTTED, over)
    maxes = [c for c in r.checks if c.rule == "MAX_COUNT"]
    check("the word limit is checked", len(maxes) == 1, [c.demand for c in maxes])
    check("86 words against 80 fails", maxes and not maxes[0].ok, maxes[0].detail if maxes else "")
    check("and the count is reported", maxes and "86 words" in maxes[0].detail)
    check("80 words passes", co.check(SLOTTED, " ".join(["word"] * 80)).checks[0].ok
          or rules(SLOTTED, " ".join(["word"] * 80))["MAX_COUNT"])

    print("\nevery constraint in a multi-clause sentence runs")
    got = rules(SLOTTED, "# Heading\n\n- a bullet\n\n**bold label** text")
    for rule in ("NO_LISTS", "NO_HEADINGS", "NO_BOLD_LABELS"):
        check(f"{rule} was evaluated", rule in got, sorted(got))
    check("all three fail on the offending text",
          not any(got.get(r, True) for r in ("NO_LISTS", "NO_HEADINGS", "NO_BOLD_LABELS")), got)

    print("\na number describing the input is not a limit on the answer")
    r = co.check(SLOTTED, " ".join(["word"] * 50))
    demands = [c.demand for c in r.checks]
    check("400 lines from CONTEXT is not read as a constraint",
          not any("400" in d for d in demands), demands)
    check("the prompt was recognised as slotted", r.scoped)

    print("\nthe same demand stated twice is one check")
    counts = [c.rule for c in co.check(SLOTTED, "one paragraph here").checks]
    check("ONE_PARAGRAPH appears once", counts.count("ONE_PARAGRAPH") == 1, counts)
    check("NO_PREAMBLE appears once", counts.count("NO_PREAMBLE") == 1, counts)

    print("\nan unslotted prompt is scanned whole, and says so")
    r = co.check("Write it in under 5 words.", "one two three")
    check("the limit is still found", any(c.rule == "MAX_COUNT" for c in r.checks))
    check("and the report flags the wider scope", not r.scoped)

    print("\nthe other checkable forms")
    check("exclamation marks", rules("## CONSTRAINTS\nNo exclamation marks.", "Hi!")["NO_EXCLAMATION"] is False)
    check("forbidden word", rules('## CONSTRAINTS\nNo "please".', "Please do it.")["FORBIDDEN_WORD"] is False)
    check("one code block, satisfied",
          rules("## OUTPUT CONTRACT\nOne python code block.", "```python\nx = 1\n```")["ONE_CODE_BLOCK"])
    check("one code block, violated",
          rules("## OUTPUT CONTRACT\nOne python code block.",
                "```\na\n```\n```\nb\n```")["ONE_CODE_BLOCK"] is False)
    check("valid JSON, satisfied",
          rules("## OUTPUT CONTRACT\nReturn valid JSON.", '{"a": 1}')["VALID_JSON"])
    check("valid JSON, violated",
          rules("## OUTPUT CONTRACT\nReturn valid JSON.", "{a: 1,}")["VALID_JSON"] is False)
    check("JSON inside a fence still parses",
          rules("## OUTPUT CONTRACT\nReturn valid JSON.", '```json\n{"a": 1}\n```')["VALID_JSON"])
    check("preamble caught",
          rules("## OUTPUT CONTRACT\nNo preamble.", "Here is the summary you asked for.")["NO_PREAMBLE"] is False)
    check("exact count",
          rules("## CONSTRAINTS\nExactly 3 lines.", "a\nb")["EXACT_COUNT"] is False)

    print("\nwhat it could not check is shown, not swallowed")
    r = co.check(SLOTTED, "a paragraph")
    check("the uninterpretable constraint is listed", r.unchecked, r.unchecked)
    check("and it is the one about the numbers",
          any("numbers" in u.lower() for u in r.unchecked), r.unchecked)

    print("\nexit codes")
    with tempfile.TemporaryDirectory() as tmp:
        pp, op = Path(tmp) / "p.md", Path(tmp) / "o.txt"
        pp.write_text(SLOTTED)
        op.write_text(" ".join(["word"] * 20) )
        good = subprocess.run([sys.executable, str(TOOL), str(pp), str(op)],
                              capture_output=True, text=True, timeout=60)
        check("0 when every checkable constraint holds", good.returncode == 0, good.stdout[:200])
        op.write_text(" ".join(["word"] * 200))
        bad = subprocess.run([sys.executable, str(TOOL), str(pp), str(op)],
                             capture_output=True, text=True, timeout=60)
        check("1 on a failure", bad.returncode == 1, bad.returncode)
        gone = subprocess.run([sys.executable, str(TOOL), str(pp), str(Path(tmp) / "nope")],
                              capture_output=True, text=True, timeout=60)
        check("2 when a file is missing", gone.returncode == 2, gone.returncode)
        js = subprocess.run([sys.executable, str(TOOL), str(pp), str(op), "--json"],
                            capture_output=True, text=True, timeout=60)
        import json
        payload = json.loads(js.stdout)
        check("--json carries checks and unchecked",
              "checks" in payload and "unchecked" in payload, sorted(payload))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
