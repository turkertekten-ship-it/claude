# Open items

Everything that was ever in doubt about this mechanism, and where each item now
stands. An item is only **closed** when something was actually run and the
result recorded. Items that could not be tested here say so, name why, and give
the falsifier that would settle them.

Environment for every result below: `claude` 2.1.247, Linux container, headless
`claude -p` unless stated otherwise.

---

## Closed

### 1. Which `Stop` payload does the runtime honour?

Two sources documented two different contracts:

| Form | Source | Result |
|---|---|---|
| `hookSpecificOutput.permissionDecision: "deny"` | <https://code.claude.com/docs/en/hooks> | **ignored** |
| top-level `{"decision": "block", "reason": ...}` | `anthropics/claude-code` `plugins/plugin-dev/skills/hook-development/SKILL.md` | **honoured** |
| both together | — | honoured |

Measured by counting `assistant` events in `--output-format stream-json`: the
documented form ends the session after one turn, the other sends the model back
for another. This mattered enormously — the engine had been emitting only the
documented form, so `Stop` enforcement had never once worked, and the earlier
conclusion that "headless mode has no next turn" was a misreading of my own bug.

The engine now sends **both** forms. Verified afterwards end to end: 2594
characters of undivided prose were refused, the model revised, and the delivered
reply opened with a numbered task and a done-condition.

### 2. Do plugin `UserPromptSubmit` hooks execute? ([#10225](https://github.com/anthropics/claude-code/issues/10225))

Reported against 2.0.24: registered, matched, never executed. **Does not
reproduce on 2.1.247** — the hook fires from `--plugin-dir` and from a
marketplace install. The issue is closed as a duplicate. Recorded with versions
because the settings route exists partly as insurance against this class of bug.

### 3. Does a plugin contributing that hook corrupt settings? ([#53643](https://github.com/anthropics/claude-code/issues/53643))

Reported: `"UserPromptSubmit": null` written into `settings.json`. **Does not
reproduce.** After `claude plugin marketplace add` and `claude plugin install`,
the settings file contained only `extraKnownMarketplaces` and `enabledPlugins`,
both well formed, with no null hook keys.

### 4. Does the marketplace install path work, not just `--plugin-dir`?

Yes, end to end: `marketplace add` → `install` → a session whose reply opened
with a "## Task breakdown" and per-task done-conditions. Ledger recorded
`session-start`, `inject`, `stop-ok`.

### 5. Does the `/divide` skill actually load?

Yes. After the `skills-dir` route installed it, the skill appeared in a live
session's skill list as `task-division:divide` — the plugin-namespaced form,
which also confirms the directory loaded as a plugin rather than a bare skill.

### 6. Does the directive reach a **subagent**, or only the hook?

It reaches the subagent. A passphrase present nowhere else — `MARLINGROVE-3318`
— was injected through `SubagentStart` and came back out of an `Explore`
subagent.

**Worth knowing:** the subagent reported the passphrase *and* flagged it as a
likely prompt-injection pattern, noting it was not part of its real system
prompt. That is correct behaviour on its part, and it is a genuine limit on this
delivery route: a subagent may treat an injected directive as suspicious rather
than authoritative. The subagent directive is therefore written as plain
operating guidance, and the mechanism does not depend on subagents obeying it.

---

### 7. Which contract do `TaskCreated` / `TaskCompleted` honour? — *neither*

Headless sessions have no task tools, so the first attempt at this was
inconclusive. It was then settled from an **interactive** session, which does
have them, by running the falsifier written for it: `enforce_task_quality=true`,
then create a deliberately shapeless task.

**Result: the denial is ignored.** The hook fired — `task-shape` appears in the
ledger with the findings — and the task was created anyway, with both payload
forms sent. Same for `TaskCompleted`. So unlike `Stop`, these events do not
appear to honour a refusal at all on 2.1.247.

The denial is still sent, so the check starts working the day the event honours
it, and the advisory `systemMessage` reaches the transcript either way. The
config key's comment says plainly that enforcement here does not bite.

Two further findings came out of the same run, both bugs of mine:

- **The payload keys are not the documented ones.** A live `TaskCreated` carries
  `cwd, hook_event_name, prompt_id, session_id, task_description, task_id,
  task_subject, transcript_path`. The reference says `task_title`; the runtime
  sends `task_subject`. Reading the documented name found nothing, so *every*
  task ever created was reported as having "no subject" — a check that looked
  like it was working and was reading an absent field.
- **`completion_notes` does not exist.** `TaskCompleted` carries exactly the
  same keys as `TaskCreated`. The intended check — "say what makes this task
  done" — is unimplementable, and a check against a field that never arrives
  would have flagged every completion forever. `TaskCompleted` is now
  observational: it logs and emits nothing.

---

## Open, with the reason and the falsifier

### 8. Does `SessionStart` re-seed after a compaction?

**Unverified.** `SessionStart` is confirmed to fire — the ledger records it on
every session — but only ever with `reason: ""`. Triggering a real compaction
requires filling a context window, which a one-shot headless run cannot do.

*Falsifier:* in a long interactive session that compacts, the ledger should gain
a `session-start` entry with `"reason": "compact"`. If it does not, the
compaction path is dead code and the directive is lost at exactly the moment it
is most needed.

### 9. Does Cowork run these hooks? ([#63360](https://github.com/anthropics/claude-code/issues/63360))

**Not verifiable here** — no Cowork in this environment. The issue is closed as
not planned/duplicate, and reports that neither `UserPromptSubmit` nor `Stop`
fired, with the root cause given as a sandbox/host mismatch: "Cowork sessions run
in a Linux sandbox while the hooks config and scripts live on the host Mac."

That root cause suggests, but does not establish, that the **project** route
might fare better than the user route there, since a repo-carried hook lives
inside the sandbox rather than on the host. Untested. Recorded as a lead, not a
finding.

*Falsifier:* open a Cowork session on a repository carrying the project route
and check whether the ledger gains an `inject` entry.

### 10. The two repositories' branch divergence

`turkertekten-ship-it/claude` has no `main`. Its default branch is
`claude/rag-system-data-pipeline-rdkde9`; the doctrine files — `CLAUDE.md`,
`provenance/`, `prompts/`, `tools/verify_provenance.py` — live only on the
unmerged `claude/review-chat-archive-zrynr4`. This work is based on the default
branch, so the provenance verifier could not be run against it.

**Not resolved deliberately.** Merging another session's branch, or choosing a
default branch, is the owner's decision, not this session's. Recorded so it is
not mistaken for an oversight.

### 11. The pinned marketplace ref in `claude-ai`

`claude-ai/.claude/settings.json` pins the marketplace to
`ref: claude/goal-prompt-task-division-0ghozd`, because the plugin exists only on
that branch. It works today.

*Action when that branch merges:* drop the `ref` so the marketplace tracks the
default branch. Left pinned rather than pointed at a branch that does not yet
carry the plugin, which would fail silently.

### 12. What belongs in `claude-ai` versus `claude` (unknown **U-5**)

Untouched by this work, and still open in the doctrine repository's
`provenance/unknowns.md`. This work followed the interim convention — tooling in
`claude`, a pointer from `claude-ai` — without settling the question.
