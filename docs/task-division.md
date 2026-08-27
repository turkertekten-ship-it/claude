# Divide every prompt into tasks

Every prompt submitted to Claude Code gets split into an explicit, numbered task
list before any work starts — in every project, every session and every terminal
on the machine.

The hook contract used here — the `UserPromptSubmit` event, its
`hookSpecificOutput.additionalContext` field, the exit-code semantics, and the
user-scope settings path — is taken from the Claude Code hooks reference at
<https://code.claude.com/docs/en/hooks>, read on 2026-08-27, not from memory.

## How it works

Two mechanisms, because they fail in different ways.

| Mechanism | File | What it does |
|---|---|---|
| `UserPromptSubmit` hook | `~/.claude/hooks/task_division_hook.py` | Runs once per submitted prompt, before the model sees it, and returns the division directive as `additionalContext` |
| User memory | `~/.claude/CLAUDE.md` | States the same rule as a standing instruction, so it still applies where hooks do not run |

The hook is the enforcement: it is executed by Claude Code itself on every
prompt, so it cannot be forgotten mid-conversation or lost when the context is
compacted. The memory block is the backstop.

The directive tells the session to restate the request as a numbered list of
tasks with checkable done-conditions, register anything longer than one task
with `TaskCreate`/`TaskUpdate`, and state explicitly when a request really is a
single atomic task rather than skipping the division silently.

## Install

```bash
python3 tools/install_task_division.py            # install for every project on this machine
python3 tools/install_task_division.py --check    # 0 installed, 1 not installed
python3 tools/install_task_division.py --dry-run  # print the resulting settings, write nothing
python3 tools/install_task_division.py --uninstall
```

The installer copies the hook into `~/.claude/hooks/`, so it keeps working if
this repository is moved or deleted. It backs up `settings.json` to
`~/.claude/backups/` before writing, preserves every unrelated setting and hook,
and is idempotent — re-running upgrades the entry in place instead of adding a
second one. It refuses to write at all if the existing `settings.json` is not
parseable, rather than overwriting a file it cannot read.

`CLAUDE_CONFIG_DIR` is honoured; `--home DIR` overrides the target directly.

## Scope: what "everywhere" does and does not cover

Claude Code reads hooks from three places:

| Scope | File | Reach |
|---|---|---|
| **User** | `~/.claude/settings.json` | Every project, session and terminal on this machine — this is what the installer targets |
| Project | `<repo>/.claude/settings.json` | That repository, for everyone who clones it |
| Local | `<repo>/.claude/settings.local.json` | That repository, this checkout only |

Honest limits:

- **Per machine.** One install covers every terminal on one machine. A second
  laptop needs its own run of the installer.
- **Fresh containers.** Cloud and web sessions start from a new container, so
  `~/.claude` is empty each time. This repository's own
  `.claude/settings.json` carries a `SessionStart` hook that runs
  `--check || install`, so a session started here bootstraps itself. Copy that
  hook into any other repository that should do the same.
- **Sessions already running** keep the settings they started with. Restart to
  pick up a fresh install.
- **Prompt-level only.** The hook fires on prompts you submit, not on turns
  driven by tools, subagents or scheduled triggers.

## Disabling it

```bash
export CLAUDE_TASK_DIVISION_DISABLE=1     # hook stops injecting, exits 0
python3 tools/install_task_division.py --uninstall   # remove it entirely
```

The hook exits 0 on every input it can be handed, including empty or malformed
stdin. This is deliberate: on `UserPromptSubmit`, exit code 2 blocks the prompt
*and erases it*, and a reminder about task division must never be able to cost
someone their prompt.

## Tests

```bash
python3 -m unittest discover -s tests -v      # or: make test
python3 tools/task_division_hook.py --selftest
```

`tests/test_task_division.py` proves the failure cases rather than the happy
path: junk on stdin never produces a non-zero exit, unrelated hooks and settings
survive installation, three installs leave exactly one entry, uninstall restores
the original files byte for byte, and an unparseable `settings.json` is left
untouched.
