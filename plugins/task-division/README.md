# task-division

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
