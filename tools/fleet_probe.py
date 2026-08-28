#!/usr/bin/env python3
"""Test every remote branch's copy of the chat ingester for KI-1 behaviour.

The obvious approach — run each copy's `selfcheck` subcommand — is wrong, and
was wrong here: a copy that carries the fix but predates the subcommand exits
non-zero for "invalid choice" and looks defective. "Has no detector" is not
"is defective".

So this imports each copy and exercises the behaviour directly: two transcripts
that share a sessionId, as a parent and its subagent do. If both survive, the
copy is sound, whatever subcommands it happens to have.

Usage
  python3 tools/fleet_probe.py [--repo PATH] [--tool REPO/RELATIVE/PATH]
Exit
  0 every present copy is sound · 1 at least one is affected · 2 could not run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_TOOL = "tools/ingest_chat_archive.py"
SESSION = "PROBE-SESSION"

PROBE = '''
import importlib.util, json, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("target", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
# @dataclass resolves its module through sys.modules, so a module built by
# module_from_spec must be registered there before exec_module runs.
sys.modules["target"] = mod
spec.loader.exec_module(mod)

root = Path(sys.argv[2])
(root / "subagents").mkdir(exist_ok=True)
base = {"type": "user", "sessionId": "SESSION_ID", "timestamp": "2026-01-01T00:00:00Z"}
(root / "SESSION_ID.jsonl").write_text(json.dumps(
    {**base, "uuid": "p1", "message": {"role": "user", "content": "parent"}}) + "\\n")
(root / "subagents" / "agent-a.jsonl").write_text(json.dumps(
    {**base, "uuid": "c1", "message": {"role": "user", "content": "child"}}) + "\\n")

convs = []
report = mod.Report()
for p in sorted(root.rglob("*.jsonl")):
    convs += mod.parse_claude_code_jsonl(p, report)

ids = {c.id for c in convs}
msgs = sum(len(c.messages) for c in convs)
print(json.dumps({"conversations": len(ids), "messages": msgs}))
'''.replace("SESSION_ID", SESSION)


def probe_source(source: str) -> tuple[bool, str]:
    """Return (sound, detail) for one copy's source text."""
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        target = tmpdir / "target.py"
        target.write_text(source, encoding="utf-8")
        runner = tmpdir / "runner.py"
        runner.write_text(PROBE, encoding="utf-8")
        work = tmpdir / "work"
        work.mkdir()
        result = subprocess.run(
            [sys.executable, str(runner), str(target), str(work)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            tail = (result.stderr or "").strip().splitlines()
            return False, f"probe error: {tail[-1] if tail else 'unknown'}"
        try:
            data = json.loads(result.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            return False, "probe produced no result"
        ok = data["conversations"] == 2 and data["messages"] == 2
        return ok, f"{data['conversations']} conversation(s), {data['messages']} message(s)"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--repo", default=str(REPO))
    parser.add_argument("--tool", default=DEFAULT_TOOL)
    args = parser.parse_args(argv[1:])
    repo = Path(args.repo)

    subprocess.run(["git", "-C", str(repo), "fetch", "--all", "--prune"],
                   capture_output=True, timeout=180)
    refs = subprocess.run(
        ["git", "-C", str(repo), "for-each-ref", "--format=%(refname:short)",
         "refs/remotes/origin"], capture_output=True, text=True, timeout=60,
    ).stdout.split()

    status = 0
    print(f"{'BRANCH':<46} {'COPY':<8} {'KI-1':<10} DETAIL")
    for ref in refs:
        if ref.endswith("/HEAD"):
            continue
        branch = ref.split("/", 1)[1] if "/" in ref else ref
        show = subprocess.run(["git", "-C", str(repo), "show", f"{ref}:{args.tool}"],
                              capture_output=True, text=True, timeout=60)
        if show.returncode != 0:
            print(f"{branch:<46} {'absent':<8} {'-':<10}")
            continue
        sound, detail = probe_source(show.stdout)
        verdict = "sound" if sound else "AFFECTED"
        if not sound:
            status = 1
        print(f"{branch:<46} {'present':<8} {verdict:<10} {detail}")

    print()
    print("Every present copy keeps both transcripts." if status == 0
          else "At least one copy silently discards a transcript.")
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
