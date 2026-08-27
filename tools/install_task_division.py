#!/usr/bin/env python3
"""Install the task-division hook so it fires for every prompt on this machine.

Claude Code reads hooks from three scopes. Only the first is machine-wide:

    ~/.claude/settings.json          every project, every session, every terminal
    <project>/.claude/settings.json  that project, shared with collaborators
    <project>/.claude/settings.local.json   that project, just this checkout

This installer targets the user scope, and does three things there:

    hooks/task_division_hook.py   a copy of the hook, so it keeps working even
                                  if this repository is moved or deleted
    settings.json                 a UserPromptSubmit entry pointing at that copy
    CLAUDE.md                     a managed block stating the same rule, so it
                                  survives even where hooks are unavailable

Every step is idempotent: re-running upgrades in place rather than stacking a
second copy. Existing settings and unrelated hooks are preserved, and the
previous settings.json is backed up before any write.

Exit codes: 0 clean, 1 findings (--check only), 2 could not run.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import sys
import time
from pathlib import Path

MARKER = "claude-task-division"
HOOK_FILENAME = "task_division_hook.py"
HOOK_EVENT = "UserPromptSubmit"
BEGIN = f"<!-- BEGIN {MARKER} -->"
END = f"<!-- END {MARKER} -->"

MEMORY_BLOCK = f"""{BEGIN}
## Divide every prompt into tasks

Applies to every prompt, in every project, in every session.

Before any other work, restate the request as a numbered list of tasks, each
with an imperative subject and a checkable done-condition. Register a list of
more than one task with TaskCreate and keep it current with TaskUpdate. A
genuinely atomic request still gets a one-item list, stated explicitly - the
division is never skipped silently, and it belongs in the reply to the user
rather than in internal reasoning.

Maintained by tools/install_task_division.py in turkertekten-ship-it/claude.
Disable with CLAUDE_TASK_DIVISION_DISABLE=1, or remove this block.
{END}"""


def config_dir(explicit: str | None) -> Path:
    """Resolve the user-scope config directory Claude Code actually reads."""
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return Path.home().joinpath(".claude").resolve()


def load_settings(path: Path) -> dict:
    """Load settings.json, refusing to clobber a file we cannot parse."""
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise SystemExit(f"[task-division] {path} is not valid JSON ({exc}); refusing to overwrite it.")
    if not isinstance(data, dict):
        raise SystemExit(f"[task-division] {path} does not contain a JSON object; refusing to overwrite it.")
    return data


def is_ours(entry: object) -> bool:
    """True for a hook entry this installer owns, at any nesting depth."""
    return MARKER in json.dumps(entry) or HOOK_FILENAME in json.dumps(entry)


def strip_ours(settings: dict) -> tuple[dict, int]:
    """Remove previously installed entries, leaving everything else untouched."""
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return settings, 0
    entries = hooks.get(HOOK_EVENT)
    if not isinstance(entries, list):
        return settings, 0
    kept = [e for e in entries if not is_ours(e)]
    removed = len(entries) - len(kept)
    if kept:
        hooks[HOOK_EVENT] = kept
    else:
        hooks.pop(HOOK_EVENT, None)
    if not hooks:
        settings.pop("hooks", None)
    return settings, removed


def hook_entry(hook_path: Path) -> dict:
    # Identified on re-run by the script name in the command, so nothing
    # non-schema needs to be stashed inside the settings entry itself.
    command = f"python3 {shlex.quote(str(hook_path))}"
    return {
        "hooks": [
            {
                "type": "command",
                "command": command,
                "timeout": 10,
            }
        ]
    }


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest = path.parent / "backups" / f"{path.name}.{stamp}.bak"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def write_memory(path: Path, install: bool) -> str:
    """Add, refresh or remove the managed block in CLAUDE.md."""
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if BEGIN in existing and END in existing:
        head, _, rest = existing.partition(BEGIN)
        _, _, tail = rest.partition(END)
        stripped = (head.rstrip() + "\n" + tail.lstrip("\n")).strip()
        action = "refreshed"
    else:
        stripped = existing.strip()
        action = "added"

    if not install:
        if action == "added":
            return "absent"
        body = (stripped + "\n") if stripped else ""
        path.write_text(body, encoding="utf-8")
        return "removed"

    body = (stripped + "\n\n" + MEMORY_BLOCK + "\n") if stripped else (MEMORY_BLOCK + "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return action


def source_hook() -> Path:
    local = Path(__file__).resolve().parent / HOOK_FILENAME
    if not local.exists():
        raise SystemExit(f"[task-division] cannot find {local}; run this from a full checkout.")
    return local


def do_check(cfg: Path) -> int:
    settings_path = cfg / "settings.json"
    hook_path = cfg / "hooks" / HOOK_FILENAME
    findings = []
    if not hook_path.exists():
        findings.append(f"hook script missing: {hook_path}")
    settings = load_settings(settings_path)
    entries = settings.get("hooks", {}).get(HOOK_EVENT, []) if isinstance(settings.get("hooks"), dict) else []
    if not any(is_ours(e) for e in entries if isinstance(entries, list)):
        findings.append(f"no {HOOK_EVENT} entry in {settings_path}")
    memory = cfg / "CLAUDE.md"
    if not memory.exists() or BEGIN not in memory.read_text(encoding="utf-8"):
        findings.append(f"no managed block in {memory}")
    for line in findings:
        print(f"[task-division] MISSING {line}")
    if not findings:
        print(f"[task-division] installed and active for every prompt in {cfg}")
    return 1 if findings else 0


def do_install(cfg: Path, install: bool, dry_run: bool) -> int:
    settings_path = cfg / "settings.json"
    hook_path = cfg / "hooks" / HOOK_FILENAME
    verb = "install" if install else "uninstall"

    settings = load_settings(settings_path)
    settings, removed = strip_ours(settings)
    if install:
        settings.setdefault("hooks", {}).setdefault(HOOK_EVENT, []).append(hook_entry(hook_path))

    if dry_run:
        print(f"[task-division] dry run: would {verb} into {cfg}")
        print(f"[task-division] would remove {removed} existing entr{'y' if removed == 1 else 'ies'}")
        print(json.dumps(settings, indent=2))
        return 0

    cfg.mkdir(parents=True, exist_ok=True)
    saved = backup(settings_path)

    if install:
        hook_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_hook(), hook_path)
        hook_path.chmod(0o755)
    elif hook_path.exists():
        hook_path.unlink()

    if settings:
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    elif settings_path.exists():
        settings_path.write_text("{}\n", encoding="utf-8")

    memory_state = write_memory(cfg / "CLAUDE.md", install)

    print(f"[task-division] {verb}ed in {cfg}")
    if saved:
        print(f"[task-division] previous settings.json backed up to {saved}")
    print(f"[task-division] {HOOK_EVENT} entries replaced: {removed}")
    print(f"[task-division] CLAUDE.md block: {memory_state}")
    if install:
        print("[task-division] applies to every prompt in every project on this machine.")
        print("[task-division] sessions already running must be restarted to pick it up.")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--home", help="config directory to target (default: ~/.claude)")
    parser.add_argument("--check", action="store_true", help="report whether it is installed")
    parser.add_argument("--uninstall", action="store_true", help="remove hook, entry and memory block")
    parser.add_argument("--dry-run", action="store_true", help="print the resulting settings, write nothing")
    args = parser.parse_args(argv)

    cfg = config_dir(args.home)
    if args.check:
        return do_check(cfg)
    return do_install(cfg, install=not args.uninstall, dry_run=args.dry_run)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[task-division] could not run: {exc}", file=sys.stderr)
        sys.exit(2)
