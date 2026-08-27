# Divide every prompt into tasks

Every prompt gets restated as an explicit, numbered task list with checkable
done-conditions before any work starts — in every project, every session and
every terminal — and a reply that skipped the division gets challenged.

Nothing below is written from memory of how Claude Code behaves. Every claim is
either sourced to <https://code.claude.com/docs/en/hooks> (read 2026-08-27) or
verified against the installed CLI, version 2.1.247. Where the two disagree, the
binary wins and the disagreement is recorded.

---

## What it does

`tools/task_division.py` is one script that dispatches on the `hook_event_name`
it receives on stdin, so a single registration serves every event:

| Event | Behaviour |
|---|---|
| `UserPromptSubmit` | Injects the division directive before the model sees the prompt |
| `SessionStart` | Seeds it before the first prompt, and re-seeds after a compaction (`reason=compact`) |
| `SubagentStart` | Carries it into subagent contexts, which never saw the original |
| `PreCompact` | Records the compaction; never blocks one |
| `Stop` | Challenges a substantial reply containing no division |
| `TaskCreated` | Flags a task with no imperative subject or no checkable done-condition |
| `TaskCompleted` | Flags a completion that never says what makes it done |
| `SessionEnd` | Closes the session's ledger entry |

## What is actually verified

| Claim | How it was checked | Result |
|---|---|---|
| The hook runs on every prompt | Marker file written from a headless run | fires |
| Its output reaches the *model*, not just the runtime | Injected a passphrase present nowhere else, then asked for it | model answered `QUILLFROST-7742` |
| It changes behaviour in sessions that never saw this work | Fresh config, fresh session, ordinary question | reply came back divided |
| Plugin-provided hooks fire | `--plugin-dir` with a generated plugin | fires — bug [#10225](https://github.com/anthropics/claude-code/issues/10225) does not reproduce on 2.1.247 |
| Project-scope hooks fire | `.claude/settings.json` in the launch directory | fires |
| The runtime accepts a `Stop` refusal | `--output-format stream-json`, read the `hook_response` | `permissionDecision: deny`, `outcome: success` |
| The plugin is well formed | `claude plugin validate --strict` | passes, no warnings |

Reproduce all of it with `make e2e`.

## Where it installs

There is no single place that reaches every session, so the installer writes to
several. The engine deduplicates per prompt, so overlapping routes inject once.

| Route | Location | Reach |
|---|---|---|
| `user` | `~/.claude/settings.json` | every project on this machine |
| `project` | `<repo>/.claude/settings.json` | everyone who clones the repo, including cloud sessions whose `~/.claude` starts empty |
| `local` | `<repo>/.claude/settings.local.json` | this checkout only |
| `skills-dir` | `~/.claude/skills/task-division/` | auto-loads as `task-division@skills-dir` next session, no marketplace step |
| `plugin` | `<repo>/plugins/task-division/` | distributable; also writes `.claude-plugin/marketplace.json` |

```bash
python3 tools/install_task_division.py               # user, project, skills-dir, plugin
python3 tools/install_task_division.py --route all   # add local
python3 tools/install_task_division.py --check       # 0 installed, 1 not
python3 tools/install_task_division.py --dry-run
python3 tools/install_task_division.py --uninstall
```

The project route registers
`python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/task_division.py" hook`, not an
absolute path, so a committed `settings.json` still works after somebody clones
the repository somewhere else.

This repository registers the marketplace but deliberately does **not** set
`enabledPlugins` for itself: its project settings already run the hooks, and
enabling the plugin here as well would run every hook twice for no benefit.
Elsewhere:

```bash
/plugin marketplace add turkertekten-ship-it/claude
/plugin install task-division@turkertekten-tools
```

## Limits, stated plainly

- **A refused `Stop` needs a next turn.** The runtime accepts the refusal — that
  is verified — but in `claude -p` there is no next turn: exactly one assistant
  message is produced and the reply is delivered unrevised. So in headless
  one-shot mode the refusal is recorded and not acted on, and
  `UserPromptSubmit` injection is what actually changes behaviour there.
  `tests/test_integration.py` asserts this limit, and will fail loudly if it
  ever stops being true.
- **Injection alone is not enough either.** Asked for "flowing prose, no lists",
  a model that had received the directive still skipped the division. The two
  mechanisms cover different failures; neither covers both.
- **Cloud sessions don't read your laptop's `~/.claude`.** The docs say so
  explicitly, which is why the project route matters more than the user route
  for work done through Claude Code on the web. A cloud container's *own*
  `~/.claude` is read normally — this was checked — but it starts empty.
- **Cowork does not run `~/.claude` hooks at all**, per
  [#63360](https://github.com/anthropics/claude-code/issues/63360). Unverified
  here; recorded as second-hand.
- **Per machine, per clone.** One install covers one machine. Another laptop
  needs its own run, or a clone of a repository carrying the project route.
- **Sessions already running keep the settings they started with.** Restart to
  pick up a fresh install.
- **Integration tests talk to a live API** and are mildly flaky for that reason;
  each session is retried once before a test is failed.

## Configuration

```bash
python3 tools/task_division.py config                      # show effective config
python3 tools/task_division.py config mode=warn            # advise, never refuse
python3 tools/task_division.py config mode=off             # disable
python3 tools/task_division.py config min_response_chars=800
python3 tools/task_division.py config enforce_task_quality=true   # deny vacuous tasks
python3 tools/task_division.py log -n 20                   # what it has done
python3 tools/task_division.py verify "1. a" "2. b"        # 0 divided, 1 not
```

| Key | Default | Meaning |
|---|---|---|
| `mode` | `enforce` | `off`, `warn` (advise only), or `enforce` (may refuse a stop) |
| `min_response_chars` | `400` | Shorter replies are never challenged |
| `max_denials_per_session` | `2` | Hard ceiling, so a disagreement cannot loop |
| `enforce_task_quality` | `false` | Whether shapeless tasks are denied or merely flagged |
| `log_events` | `true` | Write the JSONL ledger |

Environment overrides, per shell: `CLAUDE_TASK_DIVISION_MODE=off|warn|enforce`,
`CLAUDE_TASK_DIVISION_DISABLE=1`, and `CLAUDE_TASK_DIVISION_STATE_DIR` to place
the ledger somewhere known (the runtime sets `CLAUDE_PLUGIN_DATA` itself for
plugin hooks, so this is the only way to pin it).

## Safety properties

- **The hook can never cost you a prompt.** Exit 2 on `UserPromptSubmit` blocks
  the prompt *and erases it*, so the engine exits 0 on everything it can be
  handed — empty stdin, malformed JSON, an unparseable config, an unknown event.
- **One reply spends at most one refusal.** The runtime can invoke `Stop` twice
  for a single turn, *concurrently*; the decision is claimed with an atomic
  `O_CREAT|O_EXCL` file so the second invocation replays the first's verdict.
- **A one-item list counts.** The directive tells the model to give a one-item
  list when a request is atomic, so the detector recognises one — under a
  "Task list:" heading, alongside a done-condition, or with an explicit
  statement that the request is atomic. An earlier version did not, and refused
  a live reply that had done exactly the right thing.
- **Installing never damages settings it did not write.** Unrelated hooks and
  keys are preserved, `settings.json` is backed up first, re-running replaces
  rather than stacks, and an unparseable settings file is left untouched.

## Tests

```bash
make test    # 45 unit tests, no network, isolated from the real ~/.claude
make e2e     # 6 integration tests driving the real claude binary
python3 tools/task_division.py selftest
```

The unit suite proves failure cases, not the happy path: junk on stdin never
exits non-zero, three installs leave one entry, two concurrent `Stop` processes
spend one refusal, uninstall restores the original files byte for byte, and an
unparseable `settings.json` is left alone. The selftest is run twice in CI
because the first version of it passed once and failed on the second run —
state it had written itself.
