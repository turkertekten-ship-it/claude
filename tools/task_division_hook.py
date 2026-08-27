#!/usr/bin/env python3
"""UserPromptSubmit hook: divide every prompt into tasks.

Claude Code runs this once per submitted prompt, before the model sees it, and
adds what it prints to the model's view of that prompt. Installed in user scope
(``~/.claude/settings.json``) it therefore fires for every prompt, in every
project, in every session and terminal on the machine.

Contract (from the Claude Code hooks reference):

- stdin  : a JSON object carrying at least ``session_id``, ``cwd``,
           ``hook_event_name`` and the submitted ``prompt``.
- stdout : a JSON object whose ``hookSpecificOutput.additionalContext`` is added
           to the model's understanding of the prompt before it is processed.
- exit 0 : proceed. Exit 2 would *block the prompt and erase it*, so this hook
           exits 0 unconditionally - a task-division reminder must never be able
           to cost someone their prompt.

Run ``python3 task_division_hook.py --selftest`` to check it end to end.
"""

from __future__ import annotations

import json
import os
import sys

VERSION = "1.0.0"
MARKER = "claude-task-division"
HOOK_EVENT = "UserPromptSubmit"

DIRECTIVE = """\
== standing directive: divide the prompt into tasks ==

This applies to the prompt just submitted, and to every prompt in every session.
Do this first, before any other work or tool call.

1. Restate the request as a numbered list of tasks. Every task needs an
   imperative subject and a done-condition somebody else could check.
2. If the list has more than one task, register each one with TaskCreate, then
   keep it current with TaskUpdate: in_progress before you begin a task,
   completed only once its done-condition actually holds. Where the task tools
   are not available, keep the numbered list in your reply and track progress
   there instead.
3. If the request genuinely is one atomic task, say so and give the one-item
   list. Never skip the division silently.
4. Work the tasks in order. Work discovered mid-flight becomes a new task
   rather than something done off the list.
5. Scope you decide to drop stays on the list, marked dropped, with the reason.

The division is part of your reply to the user, not internal reasoning."""


def build_context(payload: dict) -> str:
    """Return the text handed back to the model for this prompt."""
    cwd = str(payload.get("cwd") or "").strip()
    where = f"\n\nWorking directory for this prompt: {cwd}" if cwd else ""
    return f"{DIRECTIVE}{where}"


def read_payload(stream) -> dict:
    """Parse the hook payload, tolerating empty or malformed stdin."""
    try:
        raw = stream.read()
    except Exception:
        return {}
    if not raw or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_output(payload: dict, verbose: bool = False) -> dict:
    specific = {
        "hookEventName": HOOK_EVENT,
        "additionalContext": build_context(payload),
    }
    if verbose:
        specific["systemMessage"] = f"task division active (v{VERSION})"
    return {"hookSpecificOutput": specific}


def main(argv: list[str]) -> int:
    if "--version" in argv:
        print(VERSION)
        return 0
    if "--selftest" in argv:
        return selftest()

    # An escape hatch that is honest about itself: set the variable and the
    # directive stops being injected, rather than being quietly weakened.
    if os.environ.get("CLAUDE_TASK_DIVISION_DISABLE", "") not in ("", "0", "false"):
        return 0

    payload = read_payload(sys.stdin)
    verbose = os.environ.get("CLAUDE_TASK_DIVISION_VERBOSE", "") not in ("", "0", "false")
    print(json.dumps(build_output(payload, verbose=verbose)))
    return 0


def selftest() -> int:
    """Prove the two properties that matter: valid shape, and never fatal."""
    failures = []

    out = build_output({"cwd": "/tmp/x", "prompt": "hi"})
    if out["hookSpecificOutput"]["hookEventName"] != HOOK_EVENT:
        failures.append("hookEventName is not UserPromptSubmit")
    if "TaskCreate" not in out["hookSpecificOutput"]["additionalContext"]:
        failures.append("directive lost its TaskCreate instruction")
    if "/tmp/x" not in out["hookSpecificOutput"]["additionalContext"]:
        failures.append("cwd not carried into the context")

    import io

    for bad in ("", "   ", "not json", "[1,2,3]", "null"):
        if read_payload(io.StringIO(bad)) != {}:
            failures.append(f"malformed stdin not coerced to empty dict: {bad!r}")

    try:
        json.dumps(build_output(read_payload(io.StringIO(""))))
    except Exception as exc:  # pragma: no cover - defensive
        failures.append(f"output not serialisable on empty input: {exc}")

    for line in failures:
        print(f"FAIL {line}", file=sys.stderr)
    print("selftest: " + ("FAILED" if failures else "ok"))
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        # Never block a prompt because the reminder broke.
        sys.exit(0)
