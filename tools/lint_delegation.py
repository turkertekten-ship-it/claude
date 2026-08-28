#!/usr/bin/env python3
"""Lint the prompt a Task delegation is about to send, at the moment it is sent.

Measured on this session's own transcript, every one of the ten prompts it sent
to subagents was missing an acceptance test, and half were missing context
[src:DELEGATION-HABITS-2026-08-28]. One of those research delegations came back
"no evidence Saraev uses CLEAR", which was recorded as settled and later
overturned by a single clone - the episode rule 17 is written from. An
acceptance line stating what a negative would have to show is the thing that was
absent.

The repository already owned the linter that catches this. Nothing ran it on the
prompts it was itself sending, because a delegation prompt is typed into a tool
call rather than saved to a file.

This runs as a PreToolUse hook on Task. It reports and does not block: hook
output reaches the model at the moment of the decision, which is where advice is
actually read, and blocking would spend turns rewriting prompts on a rule class
that fires on real prompts that are fine. If the record later shows the advice
being ignored, that is the evidence for escalating it to a block - and the
escalation belongs in the loop log with that evidence, not before it.

Silent unless the prompt has an error-severity finding, or is missing the
acceptance test or the escape clause - the two slots this repository treats as
load-bearing rather than optional.

Usage
  echo '<PreToolUse JSON>' | python3 tools/lint_delegation.py [--profile task]
Exit
  0 always: this is advice, not a gate. 2 if the payload could not be read.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prompt_forge as pf  # noqa: E402

DELEGATION_TOOLS = ("Task", "Agent")
LOAD_BEARING = ("ACCEPTANCE", "ESCAPE")


def prompt_from(payload: dict) -> tuple[str, str]:
    """The delegation prompt and the agent it is going to, or ("", "")."""
    if payload.get("tool_name") not in DELEGATION_TOOLS:
        return "", ""
    tool_input = payload.get("tool_input") or {}
    prompt = tool_input.get("prompt") or ""
    return (prompt if isinstance(prompt, str) else ""), str(tool_input.get("subagent_type") or "")


def worth_reporting(report: pf.Report) -> bool:
    if any(f.severity == "error" for f in report.findings):
        return True
    return any(not report.slots_present.get(slot, False) for slot in LOAD_BEARING)


def render(report: pf.Report, agent: str) -> str:
    counts = report.counts()
    missing = [k for k, v in report.slots_present.items() if not v]
    head = (f"lint_delegation: this prompt to `{agent or 'a subagent'}` scores "
            f"{report.score}/100 ({report.grade}) — "
            f"{counts['error']} error / {counts['warn']} warn / {counts['info']} info")
    lines = [head]
    if missing:
        lines.append(f"  missing slots: {', '.join(missing)}")
    seen = set()
    for finding in report.findings:
        if finding.rule in seen:
            continue
        seen.add(finding.rule)
        if finding.severity == "error" or finding.rule in {f"NO_{s}" for s in LOAD_BEARING}:
            lines.append(f"  {finding.rule:<15} {finding.fix}")
    lines.append("  advisory: the delegation was not blocked. Send it, or fix it first.")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Lint a Task delegation's prompt. Always exits 0; 2 if the payload is unreadable.")
    ap.add_argument("--profile", default="task", choices=sorted(pf.PROFILES))
    args = ap.parse_args(argv[1:])

    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"lint_delegation: could not read the hook payload: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("lint_delegation: hook payload was not an object", file=sys.stderr)
        return 2

    prompt, agent = prompt_from(payload)
    if not prompt.strip():
        return 0
    report = pf.analyse(prompt, profile=args.profile, source="delegation")
    if worth_reporting(report):
        print(render(report, agent))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
