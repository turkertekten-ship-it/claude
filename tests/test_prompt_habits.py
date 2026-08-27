#!/usr/bin/env python3
"""Tests for the corpus auditor.

The failure this guards against is subtle and would be invisible in the output:
the chat index stores tool results as user turns, so an auditor that does not
filter them reports statistics about the harness under the owner's name. Every
case below is built around that.

Run: python3 tests/test_prompt_habits.py
"""

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TOOL = REPO / "tools" / "prompt_habits.py"

sys.path.insert(0, str(REPO / "tools"))
import prompt_habits as ph  # noqa: E402

FAILURES: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


SCHEMA = """
CREATE TABLE conversations (id TEXT PRIMARY KEY, title TEXT);
CREATE TABLE messages (
    id TEXT PRIMARY KEY, conversation_id TEXT, seq INTEGER, role TEXT,
    text TEXT, timestamp TEXT, block_types TEXT, source_file TEXT
);
"""

ROWS = [
    # id, role, text, block_types
    ("m1", "user", "Refactor all the modules and make it clean.", "<str>"),
    ("m2", "user", "total 16\ndrwxr-xr-x 4 root root 4096 Aug 27 14:11 .", "tool_result"),
    ("m3", "user", "Web search results for query: \"something\"\n\nLinks: [...]", "<str>"),
    ("m4", "user", "ok", "<str>"),
    ("m5", "user", "/prompt fix this", "<str>"),
    ("m6", "user",
     "You are a release engineer. Context: Python 3.11. Write the workflow at "
     "ci.yml. Constraints: no third-party actions. Output: one YAML block. "
     "Acceptance: the job name is checks. If it exists already, say so and stop.",
     "<str>"),
    ("m7", "user", "Refactor all the modules and make it clean.", "<str>"),   # repeat
    ("m8", "assistant", "Refactor all the modules yourself.", "<str>"),       # not a user turn
]


def build_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO conversations VALUES ('c1', 'a conversation')")
    for i, (mid, role, text, blocks) in enumerate(ROWS):
        conn.execute(
            "INSERT INTO messages VALUES (?,?,?,?,?,?,?,?)",
            (mid, "c1", i, role, text, f"2026-08-27T10:{i:02d}:00Z", blocks, "t.jsonl"),
        )
    conn.commit()
    conn.close()


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "index.db"
        build_db(db)

        print("the corpus is the owner's turns and nothing else")
        prompts, excluded = ph.load_prompts(db, min_words=5, since=None)
        texts = [p["text"] for p in prompts]
        check("a real prompt is kept", any("Refactor all the modules" in t for t in texts))
        check("a well-formed prompt is kept", any("release engineer" in t for t in texts))
        check("a tool result is excluded", not any("drwxr-xr-x" in t for t in texts))
        check("search-result text is excluded", not any("Web search results" in t for t in texts))
        check("an acknowledgement is excluded", "ok" not in texts)
        check("a slash command is excluded", not any(t.startswith("/") for t in texts))
        check("an assistant turn is excluded", not any("yourself" in t for t in texts))
        check("a repeat counts once", len(prompts) == 2, texts)

        print("\nwhat was left out is counted, not silently dropped")
        check("tool results are counted", excluded["tool_result"] == 1, excluded)
        check("harness and short turns are counted", excluded["harness_or_short"] == 3, excluded)
        check("repeats are counted", excluded["duplicate"] == 1, excluded)
        check("the total is reported", excluded["total_user_turns"] == 7, excluded)

        print("\nthe audit ranks habits by what they cost")
        result = ph.audit(prompts, "chat")
        check("both prompts scored", result["prompts"] == 2, result["prompts"])
        rules = [h["rule"] for h in result["habits"]]
        check("the vague prompt's rules surface", "VAGUE_QUALITY" in rules, rules)
        check("the clean prompt does not add errors",
              all(h["severity"] != "error" or h["prompts"] == 1 for h in result["habits"]))
        check("shares are percentages of the corpus",
              all(0 <= h["share"] <= 100 for h in result["habits"]))
        check("a fix is offered for the top habit", ph.fix_for(rules[0]) != "", rules[0])
        check("slot rules get their slot's hint", "imperative" in ph.fix_for("NO_TASK"))

        print("\nabsent input is reported, never invented")
        missing = subprocess.run(
            [sys.executable, str(TOOL), "--db", str(Path(tmp) / "nope.db")],
            capture_output=True, text=True, timeout=60,
        )
        check("a missing index exits clean", missing.returncode == 0, missing.returncode)
        check("and says so plainly", "no index at" in missing.stdout, missing.stdout[:80])

        empty = Path(tmp) / "empty.db"
        conn = sqlite3.connect(empty)
        conn.executescript(SCHEMA)
        conn.execute("INSERT INTO messages VALUES ('x','c',0,'user','ls -la','t','tool_result','f')")
        conn.commit()
        conn.close()
        none_found = subprocess.run(
            [sys.executable, str(TOOL), "--db", str(empty)],
            capture_output=True, text=True, timeout=60,
        )
        check("an index of only tool results scores nothing", none_found.returncode == 0)
        check("and explains why", "looks like a prompt" in none_found.stdout, none_found.stdout[:120])

        real = subprocess.run(
            [sys.executable, str(TOOL), "--db", str(db), "--json"],
            capture_output=True, text=True, timeout=60,
        )
        import json
        payload = json.loads(real.stdout)
        check("--json reports the exclusions", payload["excluded"]["tool_result"] == 1, payload.get("excluded"))
        check("--json reports the habits", len(payload["habits"]) > 0)
        check("findings exit 1", real.returncode == 1, real.returncode)

    print()
    if FAILURES:
        print(f"{len(FAILURES)} case(s) failed: {', '.join(FAILURES)}")
        return 1
    print("all cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
