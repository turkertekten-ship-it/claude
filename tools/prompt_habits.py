#!/usr/bin/env python3
"""Score the prompts you have actually written, and name the habit that costs most.

`prompt_forge.py` judges one prompt. This judges a corpus of them - the messages
already in the chat index built by `ingest_chat_archive.py` - and answers a
different question: not "is this prompt good" but "what do I get wrong every
time".

That distinction is the point. A single low score is a bad afternoon. The same
rule firing on four fifths of everything you have ever written is a habit, and
it is worth more to fix one habit than to polish one prompt.

What it does not do: rewrite anything, or send anything anywhere. It reads a
local SQLite index and prints.

Usage
  python3 tools/prompt_habits.py [--db PATH] [--profile chat] [--min-words N]
                                 [--worst N] [--json] [--since ISO8601]
Exit
  0 clean, or an empty index reported as such · 1 findings · 2 could not run
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompt_forge as pf  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
# Installed into ~/.claude/tools/, this file's parent.parent is not the
# repository, so the index is elsewhere. The environment variable is how the
# installed copy is pointed at it.
DEFAULT_DB = Path(os.environ.get("PROMPT_HABITS_DB") or REPO / "archive" / "index.db")

USER_ROLES = ("user", "human")

# Text that is in the index as a user turn but was not typed by the owner as a
# prompt. Counting these would make the corpus statistics describe the harness
# rather than the person.
NOT_A_PROMPT = (
    "<system-reminder>", "<command-name>", "<local-command-stdout>",
    "[Request interrupted", "<user-prompt-submit-hook>", "Caveat: The messages below",
    "<task-notification>", "<wake reason=", "tool_use_id", "<untrusted_external_data>",
    "Web search results for query:", "A session-scoped Stop hook is now active",
)


def looks_like_a_prompt(text: str, min_words: int) -> bool:
    stripped = text.strip()
    if not stripped or len(stripped.split()) < min_words:
        return False                       # "yes", "go on", "thanks" - not prompts
    if stripped.startswith("/"):
        return False                       # a slash command is an invocation
    return not any(marker in stripped for marker in NOT_A_PROMPT)


def load_prompts(db: Path, min_words: int, since: str | None) -> tuple[list[dict], dict[str, int]]:
    """Return the owner's prompts, and a count of what was left out and why.

    The index stores tool results as user turns, because that is what they are
    at the protocol level - a `tool_result` block sent in the user role. Scoring
    them would produce statistics about the harness wearing the owner's name,
    which is worse than no statistics. `block_types` separates them exactly, so
    the filter uses that rather than guessing from the text.
    """
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        query = (
            "SELECT m.id, m.text, m.timestamp, m.conversation_id, m.block_types, c.title "
            "FROM messages m LEFT JOIN conversations c ON c.id = m.conversation_id "
            f"WHERE lower(m.role) IN ({','.join('?' * len(USER_ROLES))})"
        )
        params: list[str] = list(USER_ROLES)
        if since:
            query += " AND m.timestamp >= ?"
            params.append(since)
        rows = conn.execute(query + " ORDER BY m.timestamp", params).fetchall()
    finally:
        conn.close()

    seen, out = set(), []
    excluded = {"tool_result": 0, "harness_or_short": 0, "duplicate": 0}
    for row in rows:
        text = row["text"] or ""
        if "tool_result" in (row["block_types"] or ""):
            excluded["tool_result"] += 1
            continue
        if not looks_like_a_prompt(text, min_words):
            excluded["harness_or_short"] += 1
            continue
        key = " ".join(text.split())[:400]
        if key in seen:                     # the same prompt re-sent is one habit
            excluded["duplicate"] += 1
            continue
        seen.add(key)
        out.append({
            "id": row["id"], "text": text, "timestamp": row["timestamp"],
            "conversation": row["title"] or row["conversation_id"],
        })
    excluded["total_user_turns"] = len(rows)
    return out, excluded


def audit(prompts: list[dict], profile: str) -> dict:
    reports = []
    for item in prompts:
        report = pf.analyse(item["text"], profile, item["id"])
        reports.append((item, report))

    scores = [r.score for _, r in reports]
    rule_hits: dict[str, int] = {}
    for _, report in reports:
        for rule in {f.rule for f in report.findings}:
            rule_hits[rule] = rule_hits.get(rule, 0) + 1

    severity_of = {}
    for _, report in reports:
        for f in report.findings:
            severity_of.setdefault(f.rule, f.severity)

    total = len(reports) or 1
    habits = sorted(
        (
            {
                "rule": rule,
                "prompts": count,
                "share": round(100 * count / total),
                "severity": severity_of.get(rule, "warn"),
                "cost": count * pf.WEIGHTS[severity_of.get(rule, "warn")],
            }
            for rule, count in rule_hits.items()
        ),
        key=lambda h: (-h["cost"], h["rule"]),
    )
    worst = sorted(reports, key=lambda pair: pair[1].score)
    return {
        "prompts": len(reports),
        "mean": round(statistics.mean(scores), 1) if scores else 0,
        "median": round(statistics.median(scores), 1) if scores else 0,
        "grades": {g: sum(1 for _, r in reports if r.grade == g) for g in "ABCDF"},
        "habits": habits,
        "worst": worst,
        "reports": reports,
    }


def fix_for(rule: str) -> str:
    if rule.startswith("NO_"):
        key = rule[3:]
        slot = pf.SLOT_BY_KEY.get(key)
        if slot:
            return f"add {slot.hint}"
    hazard = pf.HAZARD_BY_ID.get(rule)
    return hazard.fix if hazard else ""


def render(result: dict, worst_n: int) -> str:
    ex = result.get("excluded", {})
    lines = [
        f"{result['prompts']} prompts scored — mean {result['mean']}, median {result['median']}",
        (f"of {ex.get('total_user_turns', 0)} user turns: "
         f"{ex.get('tool_result', 0)} were tool results, "
         f"{ex.get('harness_or_short', 0)} harness text or too short, "
         f"{ex.get('duplicate', 0)} repeats") if ex else "",
        "grades: " + "  ".join(f"{g} {n}" for g, n in result["grades"].items()),
        "",
        "habits, most expensive first (share of your prompts affected)",
    ]
    for habit in result["habits"][:12]:
        lines.append(f"  {habit['share']:>3}%  {habit['rule']:<15} {habit['severity']:<6} "
                     f"{habit['prompts']} prompt(s)")
    if result["habits"]:
        top = result["habits"][0]
        lines += [
            "",
            f"the one to fix: {top['rule']} — it is in {top['share']}% of what you write.",
            f"  {fix_for(top['rule'])}",
        ]
    if worst_n and result["worst"]:
        lines += ["", f"lowest scoring {min(worst_n, len(result['worst']))}:"]
        for item, report in result["worst"][:worst_n]:
            excerpt = " ".join(item["text"].split())[:90]
            when = (item["timestamp"] or "")[:16]
            lines.append(f"  {report.score:>3}/100  {when}  {excerpt}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="prompt_habits",
        description="Score your own prompt history and name the habit that costs most.",
    )
    parser.add_argument("--db", default=str(DEFAULT_DB), help="index built by ingest_chat_archive.py")
    parser.add_argument("--profile", default="chat", choices=sorted(pf.PROFILES))
    parser.add_argument("--min-words", type=int, default=5,
                        help="shorter turns are acknowledgements, not prompts (default 5)")
    parser.add_argument("--worst", type=int, default=5, help="how many low scorers to list")
    parser.add_argument("--since", default=None, help="only prompts at or after this ISO timestamp")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv[1:])

    db = Path(args.db)
    if not db.exists():
        print(f"prompt_habits: no index at {db}")
        print("Nothing has been scored, because nothing has been indexed. Build it with:")
        print("  python3 tools/ingest_chat_archive.py ingest --include-projects")
        print("If the index is elsewhere, pass --db PATH or set PROMPT_HABITS_DB.")
        print("An absent index is not a failure; it is the reason there is no report.")
        return 0

    try:
        prompts, excluded = load_prompts(db, args.min_words, args.since)
    except sqlite3.Error as exc:
        print(f"prompt_habits: could not read {db}: {exc}", file=sys.stderr)
        return 2

    if not prompts:
        print(f"prompt_habits: the index at {db} holds no message that looks like a prompt.")
        print("Every user turn was empty, a slash command, harness text, or shorter than")
        print(f"--min-words ({args.min_words}). Nothing was scored and nothing is being guessed at.")
        return 0

    result = audit(prompts, args.profile)
    result["excluded"] = excluded
    if args.json:
        print(json.dumps({
            "prompts": result["prompts"], "mean": result["mean"], "median": result["median"],
            "grades": result["grades"], "habits": result["habits"],
            "excluded": excluded,
            "worst": [
                {"score": r.score, "timestamp": i["timestamp"],
                 "excerpt": " ".join(i["text"].split())[:120]}
                for i, r in result["worst"][:args.worst]
            ],
        }, indent=2))
    else:
        print(render(result, args.worst))
    return 1 if result["habits"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
