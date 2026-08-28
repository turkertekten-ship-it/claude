#!/usr/bin/env python3
"""Tests for the delegation linter.

Its job is to speak at the moment a Task prompt is sent, and to stay quiet
otherwise. Both halves matter: a hook that fires on everything is noise, and
noise is ignored, which is the same end state as not existing.

The failure case demonstrated here is the real one — the prompts this session
actually sent to its subagents, every one of which was missing an acceptance
test. One of them is replayed verbatim.

Run: python3 tests/test_lint_delegation.py
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "lint_delegation.py"

sys.path.insert(0, str(REPO / "tools"))
import lint_delegation as ld  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def run(payload) -> subprocess.CompletedProcess:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run([sys.executable, str(TOOL)], input=text,
                          capture_output=True, text=True, timeout=60)


# Sent to a subagent by this session on 2026-08-27, quoted from the transcript.
REAL_DELEGATION = (
    "Determine whether Nick Saraev teaches, uses, or published anything called "
    '"CLEAR" (as a prompting or automation framework). Search his site, YouTube, '
    "and newsletter. Report what you find."
)

COMPLETE = """ROLE: You are an inventory agent.
CONTEXT: The repository was cloned an hour ago; a grep for the term returned nothing.
TASK: List every file under tools/ that imports sqlite3.
CONSTRAINTS: Read only. At most 200 words. Do not summarise the files.
OUTPUT: A markdown table of path and line number, nothing else.
ACCEPTANCE: Correct only when every listed line contains the word sqlite3, and rerunning the grep adds no rows.
IF YOU CANNOT: If tools/ does not exist, say so and stop; do not search elsewhere.
"""


def main() -> int:
    print("a real delegation with no acceptance test is reported")
    r = run({"tool_name": "Task",
             "tool_input": {"subagent_type": "observer", "prompt": REAL_DELEGATION}})
    check("it exits 0 — advice, not a gate", r.returncode == 0, r.stderr)
    check("it names the missing acceptance test", "NO_ACCEPTANCE" in r.stdout, r.stdout)
    check("it names the agent", "observer" in r.stdout, r.stdout)
    check("it says it did not block", "not blocked" in r.stdout, r.stdout)

    print("\na complete prompt is passed over in silence")
    r = run({"tool_name": "Task", "tool_input": {"subagent_type": "observer", "prompt": COMPLETE}})
    check("nothing is printed", r.stdout.strip() == "", r.stdout)
    check("and it exits 0", r.returncode == 0, r.stderr)

    print("\nit speaks only for delegations")
    for payload in ({"tool_name": "Bash", "tool_input": {"command": "ls"}},
                    {"tool_name": "Task", "tool_input": {"prompt": "   "}},
                    {"tool_name": "Task", "tool_input": {}},
                    {"tool_name": "Task"},
                    {}):
        r = run(payload)
        check(f"silent on {json.dumps(payload)[:40]}",
              r.stdout.strip() == "" and r.returncode == 0, r.stdout + r.stderr)
    r = run("")
    check("silent on an empty payload", r.stdout.strip() == "" and r.returncode == 0, r.stdout)

    print("\nan unreadable payload is reported as could-not-run, not as clean")
    r = run("{not json")
    check("exit 2", r.returncode == 2, r.stdout + r.stderr)
    check("and it says so on stderr", "could not read" in r.stderr, r.stderr)
    r = run("[1, 2, 3]")
    check("a non-object payload is exit 2", r.returncode == 2, r.stdout + r.stderr)

    print("\nthe two load-bearing slots are what break the silence")
    missing_escape = COMPLETE.replace(
        "IF YOU CANNOT: If tools/ does not exist, say so and stop; do not search elsewhere.\n", "")
    r = run({"tool_name": "Task", "tool_input": {"prompt": missing_escape}})
    check("a missing escape clause is reported", "NO_ESCAPE" in r.stdout, r.stdout)
    missing_acceptance = COMPLETE.replace(
        "ACCEPTANCE: Correct only when every listed line contains the word sqlite3, "
        "and rerunning the grep adds no rows.\n", "")
    r = run({"tool_name": "Task", "tool_input": {"prompt": missing_acceptance}})
    check("a missing acceptance test is reported", "NO_ACCEPTANCE" in r.stdout, r.stdout)

    print("\nthe hook this repository installs points at this tool")
    settings = json.loads((REPO / ".claude" / "settings.json").read_text())
    pre = settings.get("hooks", {}).get("PreToolUse", [])
    check("a PreToolUse hook exists", bool(pre), settings.get("hooks", {}).keys())
    check("it matches Task", any(e.get("matcher") == "Task" for e in pre), pre)
    check("it runs lint_delegation.py",
          any("lint_delegation.py" in h.get("command", "")
              for e in pre for h in e.get("hooks", [])), pre)

    print("\nthe module reports its own reasons")
    check("the docstring says it does not block", "does not block" in (ld.__doc__ or ""))

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
