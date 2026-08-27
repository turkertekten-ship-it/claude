#!/usr/bin/env python3
"""Install prompt task division along every route Claude Code will read.

There is no single place that reaches every session, so this installs to
several, and the engine deduplicates so overlapping routes inject once.

    user        ~/.claude/settings.json          every project on this machine
    project     <repo>/.claude/settings.json     everyone who clones the repo,
                                                 including cloud sessions whose
                                                 ~/.claude starts empty
    local       <repo>/.claude/settings.local.json   this checkout only
    skills-dir  ~/.claude/skills/task-division/  auto-loads as a plugin next
                                                 session, no marketplace needed
    plugin      <repo>/plugins/task-division/    distributable, plus a
                                                 marketplace entry at the repo root

Every route is idempotent, backs up what it overwrites, preserves settings it
did not put there, and can be removed again with --uninstall.

Exit codes: 0 clean, 1 findings (--check), 2 could not run.
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
ENGINE = "task_division.py"
LEGACY_ENGINES = ("task_division_hook.py",)
PLUGIN_NAME = "task-division"
MARKETPLACE_NAME = "turkertekten-tools"

# Every event the engine answers. One command serves them all: the engine
# dispatches on hook_event_name, so the registration is identical per event.
EVENTS = (
    "UserPromptSubmit",
    "SessionStart",
    "SubagentStart",
    "PreCompact",
    "Stop",
    "TaskCreated",
    "TaskCompleted",
    "SessionEnd",
)

ROUTES = ("user", "project", "local", "skills-dir", "plugin")

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

SKILL_BODY = """---
name: divide
description: Divide a request into a numbered task list with checkable done-conditions. Use when a request bundles several pieces of work, when asked to plan or break something down, or before starting any multi-step task.
argument-hint: [request to divide]
---

# Divide a request into tasks

Divide the following request into tasks. If no request is given below, divide
the user's most recent request instead.

$ARGUMENTS

## How to divide it

1. **List the tasks.** Number them. Each task gets an imperative subject - the
   verb first - and a done-condition somebody else could check without asking
   you what you meant. "Improve error handling" is not a task. "Return 422 with
   the field name on invalid input, covered by a test" is.
2. **Order them by dependency**, not by how interesting they are. If task 3
   needs task 1's output, say so.
3. **Register them.** More than one task means one `TaskCreate` call per task,
   then `TaskUpdate` to `in_progress` before starting each and `completed` only
   once its done-condition actually holds. Where those tools are unavailable,
   keep the numbered list in the reply and track progress there.
4. **Say what you are not doing.** Scope you are dropping stays on the list,
   marked dropped, with the reason. Silent narrowing is the failure this whole
   mechanism exists to prevent.
5. **Name the uncertainty.** A task you cannot yet size becomes a task to find
   out, with its own done-condition.

If the request genuinely is one atomic task, say so explicitly and give the
one-item list. That is a valid division. Skipping the division is not.

The list goes in your reply to the user, not in internal reasoning.
"""

PLUGIN_README = """# task-division

Divides every prompt into an explicit, numbered task list with checkable
done-conditions - and checks that it actually happened.

## What it does

| Event | Behaviour |
|---|---|
| `UserPromptSubmit` | Injects the division directive before the model sees the prompt |
| `SessionStart` | Seeds it before the first prompt, and re-seeds after a compaction |
| `SubagentStart` | Carries it into subagent contexts |
| `Stop` | Refuses to finish a substantial reply that contains no division |
| `TaskCreated` / `TaskCompleted` | Flags tasks with no checkable done-condition |

The `Stop` check is what makes it enforcement rather than a reminder. It is
bounded: short replies are never challenged, and there is a hard per-session
ceiling on refusals so a disagreement can never become a loop.

## Configuration

```bash
python3 scripts/task_division.py config mode=warn          # advise, never refuse
python3 scripts/task_division.py config mode=off           # disable
python3 scripts/task_division.py config min_response_chars=800
python3 scripts/task_division.py log                       # what it has done
```

`CLAUDE_TASK_DIVISION_MODE=off|warn|enforce` overrides per shell;
`CLAUDE_TASK_DIVISION_DISABLE=1` turns it off entirely.
"""


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def engine_source() -> Path:
    path = repo_root() / "tools" / ENGINE
    if not path.exists():
        raise SystemExit(f"[task-division] cannot find {path}; run from a full checkout.")
    return path


def config_dir(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return (Path.home() / ".claude").resolve()


def load_json(path: Path, what: str) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise SystemExit(f"[task-division] {path} is not valid JSON ({exc}); refusing to overwrite {what}.")
    if not isinstance(data, dict):
        raise SystemExit(f"[task-division] {path} is not a JSON object; refusing to overwrite {what}.")
    return data


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest = path.parent / "backups" / f"{path.name}.{stamp}.bak"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def is_ours(entry: object) -> bool:
    blob = json.dumps(entry)
    return MARKER in blob or ENGINE in blob or any(name in blob for name in LEGACY_ENGINES)


def hook_entry(engine_path: str) -> dict:
    # Identified on re-run by the engine filename inside the command, so nothing
    # non-schema needs to be stashed in the settings entry itself.
    return {"hooks": [{"type": "command", "command": f"python3 {engine_path} hook", "timeout": 15}]}


def strip_ours(settings: dict) -> int:
    """Remove entries this installer owns from every event. Returns the count."""
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        return 0
    removed = 0
    for event in list(hooks.keys()):
        entries = hooks.get(event)
        if not isinstance(entries, list):
            continue
        kept = [entry for entry in entries if not is_ours(entry)]
        removed += len(entries) - len(kept)
        if kept:
            hooks[event] = kept
        else:
            hooks.pop(event, None)
    if not hooks:
        settings.pop("hooks", None)
    return removed


def add_ours(settings: dict, engine_path: str) -> None:
    hooks = settings.setdefault("hooks", {})
    for event in EVENTS:
        hooks.setdefault(event, []).append(hook_entry(engine_path))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if data:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    elif path.exists():
        path.write_text("{}\n", encoding="utf-8")


def write_memory(path: Path, install: bool) -> str:
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
        path.write_text((stripped + "\n") if stripped else "", encoding="utf-8")
        return "removed"

    body = (stripped + "\n\n" + MEMORY_BLOCK + "\n") if stripped else (MEMORY_BLOCK + "\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return action


def copy_engine(dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / ENGINE
    shutil.copy2(engine_source(), dest)
    dest.chmod(0o755)
    for legacy in LEGACY_ENGINES:
        (dest_dir / legacy).unlink(missing_ok=True)
    return dest


def remove_engine(dest_dir: Path) -> None:
    for name in (ENGINE, *LEGACY_ENGINES):
        (dest_dir / name).unlink(missing_ok=True)


def build_plugin(root: Path, engine_rel: str = "scripts") -> None:
    """Write a complete, validatable plugin at root."""
    (root / ".claude-plugin").mkdir(parents=True, exist_ok=True)
    manifest = {
        "$schema": "https://json.schemastore.org/claude-code-plugin.json",
        "name": PLUGIN_NAME,
        "displayName": "Task Division",
        "description": "Divides every prompt into a numbered task list with checkable done-conditions, and refuses to finish a reply that skipped it.",
        "version": "2.0.0",
        "author": {"name": "Turker Tekten"},
        "repository": "https://github.com/turkertekten-ship-it/claude",
        "license": "MIT",
        "keywords": ["tasks", "planning", "hooks", "workflow", "decomposition"],
    }
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    engine_path = "${CLAUDE_PLUGIN_ROOT}/" + engine_rel + "/" + ENGINE
    hooks = {"hooks": {}}
    for event in EVENTS:
        hooks["hooks"][event] = [hook_entry(f'"{engine_path}"')]
    (root / "hooks").mkdir(parents=True, exist_ok=True)
    (root / "hooks" / "hooks.json").write_text(json.dumps(hooks, indent=2) + "\n", encoding="utf-8")

    skill_dir = root / "skills" / "divide"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(SKILL_BODY, encoding="utf-8")

    copy_engine(root / engine_rel)
    (root / "README.md").write_text(PLUGIN_README, encoding="utf-8")


def write_marketplace(root: Path, plugin_rel: str) -> Path:
    directory = root / ".claude-plugin"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "marketplace.json"
    data = {
        "$schema": "https://json.schemastore.org/claude-code-marketplace.json",
        "name": MARKETPLACE_NAME,
        "owner": {"name": "Turker Tekten"},
        "description": "Session tooling for the sessions working on these repositories.",
        "plugins": [
            {
                "name": PLUGIN_NAME,
                "source": f"./{plugin_rel}",
                "description": "Divide every prompt into tasks, and enforce that it happened.",
                "category": "workflow",
                "keywords": ["tasks", "planning", "hooks"],
            }
        ],
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------


def route_settings(
    settings_path: Path,
    hooks_dir: Path,
    install: bool,
    dry_run: bool,
    label: str,
    command_path: str | None = None,
) -> list:
    """Shared implementation for the three settings-file routes.

    `command_path` lets the project routes register
    `${CLAUDE_PROJECT_DIR}/.claude/hooks/...` instead of an absolute path, so a
    committed `.claude/settings.json` still works after somebody clones the
    repository somewhere else.
    """
    notes = []
    settings = load_json(settings_path, label)
    removed = strip_ours(settings)
    if install:
        add_ours(settings, command_path or shlex.quote(str(hooks_dir / ENGINE)))

    if dry_run:
        notes.append(f"would write {settings_path} ({removed} existing entries replaced)")
        return notes

    saved = backup(settings_path)
    if saved:
        notes.append(f"backed up {settings_path.name} to {saved}")
    if install:
        copy_engine(hooks_dir)
    else:
        remove_engine(hooks_dir)
    write_json(settings_path, settings)
    notes.append(f"{'wrote' if install else 'cleaned'} {settings_path} ({removed} entries replaced)")
    return notes


def do_user(cfg: Path, install: bool, dry_run: bool) -> list:
    notes = route_settings(cfg / "settings.json", cfg / "hooks", install, dry_run, "user settings")
    if not dry_run:
        notes.append(f"CLAUDE.md block: {write_memory(cfg / 'CLAUDE.md', install)}")
    return notes


PROJECT_COMMAND = '"${CLAUDE_PROJECT_DIR}/.claude/hooks/' + ENGINE + '"'


def do_project(project: Path, install: bool, dry_run: bool) -> list:
    return route_settings(
        project / ".claude" / "settings.json",
        project / ".claude" / "hooks",
        install,
        dry_run,
        "project settings",
        command_path=PROJECT_COMMAND,
    )


def do_local(project: Path, install: bool, dry_run: bool) -> list:
    return route_settings(
        project / ".claude" / "settings.local.json",
        project / ".claude" / "hooks",
        install,
        dry_run,
        "local settings",
        command_path=PROJECT_COMMAND,
    )


def do_skills_dir(cfg: Path, install: bool, dry_run: bool) -> list:
    root = cfg / "skills" / PLUGIN_NAME
    if dry_run:
        return [f"would build skills-dir plugin at {root}"]
    if not install:
        shutil.rmtree(root, ignore_errors=True)
        return [f"removed {root}"]
    build_plugin(root)
    return [f"built skills-dir plugin at {root} (loads as {PLUGIN_NAME}@skills-dir next session)"]


def do_plugin(project: Path, install: bool, dry_run: bool) -> list:
    root = project / "plugins" / PLUGIN_NAME
    if dry_run:
        return [f"would build plugin at {root} and marketplace at {project}/.claude-plugin"]
    if not install:
        shutil.rmtree(root, ignore_errors=True)
        (project / ".claude-plugin" / "marketplace.json").unlink(missing_ok=True)
        return [f"removed {root} and its marketplace entry"]
    build_plugin(root)
    market = write_marketplace(project, f"plugins/{PLUGIN_NAME}")
    notes = [f"built plugin at {root}", f"wrote marketplace {market}"]

    # Register the marketplace for anyone who trusts this folder, so they can
    # install the plugin elsewhere with one command. Deliberately *not*
    # `enabledPlugins`: this repository already registers the hooks through its
    # project settings, and enabling the plugin here too would run every hook
    # twice for no benefit.
    settings_path = project / ".claude" / "settings.json"
    settings = load_json(settings_path, "project settings")
    settings.setdefault("extraKnownMarketplaces", {})[MARKETPLACE_NAME] = {
        "source": {"source": "github", "repo": "turkertekten-ship-it/claude"}
    }
    write_json(settings_path, settings)
    notes.append(f"registered marketplace {MARKETPLACE_NAME} in {settings_path}")
    return notes


# --------------------------------------------------------------------------
# check
# --------------------------------------------------------------------------


def check_route(route: str, cfg: Path, project: Path) -> list:
    findings = []
    if route in ("user", "project", "local"):
        if route == "user":
            settings_path, hooks_dir = cfg / "settings.json", cfg / "hooks"
        elif route == "project":
            settings_path, hooks_dir = project / ".claude" / "settings.json", project / ".claude" / "hooks"
        else:
            settings_path, hooks_dir = project / ".claude" / "settings.local.json", project / ".claude" / "hooks"
        if not (hooks_dir / ENGINE).exists():
            findings.append(f"{route}: engine missing at {hooks_dir / ENGINE}")
        settings = load_json(settings_path, route)
        hooks = settings.get("hooks", {})
        hooks = hooks if isinstance(hooks, dict) else {}
        missing = [
            event
            for event in EVENTS
            if not any(is_ours(entry) for entry in hooks.get(event, []) if isinstance(hooks.get(event), list))
        ]
        if missing:
            findings.append(f"{route}: {settings_path} missing events: {', '.join(missing)}")
        if route == "user":
            memory = cfg / "CLAUDE.md"
            if not memory.exists() or BEGIN not in memory.read_text(encoding="utf-8"):
                findings.append(f"user: no managed block in {memory}")
    elif route == "skills-dir":
        root = cfg / "skills" / PLUGIN_NAME
        if not (root / ".claude-plugin" / "plugin.json").exists():
            findings.append(f"skills-dir: no plugin at {root}")
    elif route == "plugin":
        root = project / "plugins" / PLUGIN_NAME
        if not (root / ".claude-plugin" / "plugin.json").exists():
            findings.append(f"plugin: no plugin at {root}")
        if not (project / ".claude-plugin" / "marketplace.json").exists():
            findings.append(f"plugin: no marketplace at {project / '.claude-plugin'}")
    return findings


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------


DISPATCH = {
    "user": lambda cfg, project, install, dry: do_user(cfg, install, dry),
    "project": lambda cfg, project, install, dry: do_project(project, install, dry),
    "local": lambda cfg, project, install, dry: do_local(project, install, dry),
    "skills-dir": lambda cfg, project, install, dry: do_skills_dir(cfg, install, dry),
    "plugin": lambda cfg, project, install, dry: do_plugin(project, install, dry),
}

DEFAULT_ROUTES = ("user", "project", "skills-dir", "plugin")


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--route",
        action="append",
        choices=(*ROUTES, "all"),
        help=f"route to install (repeatable). Default: {', '.join(DEFAULT_ROUTES)}",
    )
    parser.add_argument("--home", help="config directory (default: ~/.claude or $CLAUDE_CONFIG_DIR)")
    parser.add_argument("--project", help="project directory (default: this repository)")
    parser.add_argument("--check", action="store_true", help="report what is installed")
    parser.add_argument("--uninstall", action="store_true", help="remove every selected route")
    parser.add_argument("--dry-run", action="store_true", help="say what would happen, write nothing")
    args = parser.parse_args(argv)

    cfg = config_dir(args.home)
    project = Path(args.project).expanduser().resolve() if args.project else repo_root()

    routes = args.route or list(DEFAULT_ROUTES)
    if "all" in routes:
        routes = list(ROUTES)
    seen = []
    for route in routes:
        if route not in seen:
            seen.append(route)
    routes = seen

    if args.check:
        findings = []
        for route in routes:
            findings.extend(check_route(route, cfg, project))
        for line in findings:
            print(f"[task-division] MISSING {line}")
        if not findings:
            print(f"[task-division] installed on {', '.join(routes)} (config {cfg}, project {project})")
        return 1 if findings else 0

    install = not args.uninstall
    print(f"[task-division] {'install' if install else 'uninstall'}: {', '.join(routes)}")
    print(f"[task-division] config dir {cfg}")
    print(f"[task-division] project    {project}")
    for route in routes:
        for note in DISPATCH[route](cfg, project, install, args.dry_run):
            print(f"[task-division]   {route}: {note}")

    if install and not args.dry_run:
        print("[task-division] sessions already running must restart to pick this up.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[task-division] could not run: {exc}", file=sys.stderr)
        sys.exit(2)
