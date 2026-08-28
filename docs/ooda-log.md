# OODA log — prompt task division

One entry per cycle. Every cycle names the surprise: where reality diverged from
what the previous cycle assumed. A cycle with no surprise usually means Observe
was skipped.

Sources are cited inline by URL and read date. Nothing here is written from
memory of how Claude Code works.

---

## Cycle 1 — Observe: is the thing from the previous session actually live?

**Observe.** The `UserPromptSubmit` hook installed at the end of the previous
cycle fired on the very next prompt: the division directive arrived in the
session as injected context, ahead of the user's text. `--check` reports
installed in `/root/.claude`. 17 tests green.

**Orient.** The mechanism works. But "works" was proved only for the single
event I happened to know about. The scope claim I shipped — *user scope covers
everywhere* — was asserted from one table in one doc page, and one table is not
an enumeration.

**Decide.** Before building anything else, enumerate the whole hook surface.
Falsifier: if `UserPromptSubmit` really is the only relevant event, the rest of
this log is short.

**Act.** Re-read the hooks reference for every event, not just the one in use.

---

## Cycle 2 — Observe: the full hook surface

Source: <https://code.claude.com/docs/en/hooks>, read 2026-08-27.

**Observe.** Thirty hook events exist, not one. The ones that bear on this work:

| Event | Why it matters here |
|---|---|
| `UserPromptSubmit` | What is already in use — injects the directive per prompt |
| `SessionStart` | Fires on `startup`, `resume`, `clear`, `compact`, `fork` — can seed the directive before the first prompt |
| `PreCompact` / `PostCompact` | Compaction is where a mid-conversation instruction goes to die |
| `Stop` | Supports `permissionDecision: "deny"`, which blocks Claude from finishing and hands back a reason |
| `SubagentStart` / `SubagentStop` | Subagents are separate contexts that never saw the directive |
| `TaskCreated` / `TaskCompleted` | Both support `permissionDecision: "deny"` — a task can be rejected at creation or refused at completion |
| Plugin `hooks/hooks.json` | Hooks can ship inside a plugin, resolved against `${CLAUDE_PLUGIN_ROOT}` |

**Orient — the surprise, and it is a big one.** Two of them.

*First:* `TaskCreated` and `TaskCompleted` are hookable, and both can deny. The
previous cycle shipped a *reminder*. These events make the rule **enforceable**:
a task created without a checkable done-condition can be rejected at creation,
and a task cannot be quietly marked complete. That is the difference between
asking a session to divide work and requiring it.

*Second:* the docs state plainly that cloud sessions on Claude Code on the web
"don't read your local `~/.claude/settings.json`; hooks there come from the repo
and from your organization's server-managed settings." The previous cycle's
headline claim — user scope reaches everywhere — is therefore wrong for exactly
the surface the owner uses most. The repo is the durable route, not `~/.claude`.

*Contradiction worth recording rather than smoothing over:* this session **is** a
cloud session, and the hook **did** fire, installed only in `/root/.claude`. The
consistent reading is that the sentence means a developer's *laptop* config is
not uploaded to the cloud container; the container's own `~/.claude` is read
normally. Since a fresh container starts with an empty `~/.claude`, the
conclusion is unchanged: ship it in the repo.

*Also recorded:* two separate reads of the same page returned different field
names for `UserPromptSubmit` prompt rewriting — `updatedInput`/`blockReason` in
one, `updatedPrompt`/`permissionDecision` in the other. Both agree on
`additionalContext`. Design consequence: use only the fields both reads agree
on, and never build on prompt rewriting.

**Decide.** Stop treating this as one hook. Build a multi-event enforcement
system, distributable as a plugin, installable to every route. Falsifier: if the
plugin/skill/command surfaces turn out not to support what is needed, fall back
to settings-only installation.

**Act.** Research plugins, skills, slash commands and marketplaces next.

---

## Cycle 3 — Observe: plugins, skills, marketplaces

Sources: <https://code.claude.com/docs/en/plugins>,
<https://code.claude.com/docs/en/plugins-reference>,
<https://code.claude.com/docs/en/plugin-marketplaces>,
<https://code.claude.com/docs/en/skills>, all read 2026-08-27.

**Observe.** A plugin is a directory with `.claude-plugin/plugin.json`; every
other component sits at the plugin *root*, never inside `.claude-plugin/`. Hooks
live in `hooks/hooks.json` and resolve `${CLAUDE_PLUGIN_ROOT}`,
`${CLAUDE_PLUGIN_DATA}` and `${CLAUDE_PROJECT_DIR}`. Hook `type` is not limited
to `command`: `http`, `mcp_tool`, `prompt` and `agent` all exist. A repository's
`.claude/settings.json` can carry `extraKnownMarketplaces` and `enabledPlugins`,
which auto-configure a marketplace and turn plugins on for anyone who trusts the
folder. A directory under `~/.claude/skills/` containing a manifest auto-loads as
`<name>@skills-dir` with no marketplace and no install step.

**Orient — the surprise.** `${CLAUDE_PLUGIN_DATA}` is a persistent directory that
survives plugin updates, and `enabledPlugins` in a repo turns this from "run an
installer on each machine" into "clone the repo and it is on". The previous
cycle's per-machine installer was solving the wrong shape of problem.

**Decide.** Ship as a plugin, install to many routes, and keep settings-based
installation as the route that does not depend on plugin machinery.

---

## Cycle 4 — Observe: prior art

Searched for existing task-decomposition hooks. Sources:
<https://github.com/anthropics/claude-code/issues/10225>,
<https://github.com/anthropics/claude-code/issues/53643>,
<https://github.com/anthropics/claude-code/issues/63360>,
<https://github.com/disler/claude-code-hooks-mastery>.

**Observe.** No existing implementation divides prompts into tasks via
`UserPromptSubmit`; the published examples cover validation, context injection
and formatting. Two open bug reports are directly threatening: #10225 claims
plugin `UserPromptSubmit` hooks *match but never execute*, and #53643 claims a
plugin contributing that hook writes `"UserPromptSubmit": null` into
`settings.json`. #63360 says Cowork does not run `~/.claude/settings.json` hooks
at all.

**Orient — the surprise.** The distribution mechanism chosen one cycle earlier
may not work. Believing either the docs or the bug reports would be guessing.
Both are second-hand relative to the binary actually installed here.

**Decide.** Do not choose a route on documentation. Test every route against the
real CLI and let the results decide. Falsifier: if plugin hooks do not fire,
plugins are demoted to a packaging convenience and settings become the enforcement
route.

---

## Cycle 5 — Act: build a headless probe harness

**Observe.** `claude` 2.1.247 is installed in this container and `claude -p`
runs headless and authenticated. `claude plugin validate` exists and works.

**Act.** Built a probe: a hook that appends a marker to a file, run under
`CLAUDE_CONFIG_DIR` pointed at a scratch config, driven by `claude -p`.

Results, each from an actual run:

| Route | Fires? |
|---|---|
| `~/.claude/settings.json` (user, via `CLAUDE_CONFIG_DIR`) | yes |
| `<project>/.claude/settings.json` (project) | yes |
| Plugin `hooks/hooks.json` via `--plugin-dir` | **yes** |
| Plugin `SessionStart` | yes |

**Orient — the surprise.** Bug #10225 does not reproduce on 2.1.247: plugin
`UserPromptSubmit` hooks fire. The threat that would have forced the design
sideways is not present in the version that matters. Recorded as a
version-specific observation, not a general claim — the issue may still be real
on other versions, which is a reason to keep the settings route working.

---

## Cycle 6 — Act: prove the payload reaches the model, not just the hook

**Observe.** Every result so far proves a *process* ran. None proves the model
ever saw the injected text — a hook can fire and its output can be discarded.

**Act.** Injected `additionalContext` containing a passphrase that appears
nowhere else — `QUILLFROST-7742` — then asked, in a separate headless run,
"What is the session passphrase?" The model answered `QUILLFROST-7742`.

**Orient.** End-to-end confirmed: `hookSpecificOutput.additionalContext` from
`UserPromptSubmit` reaches the model's view of the prompt. This also yields a
reusable integration-test harness — assert on model behaviour, not on JSON shape.

**Decide.** Rebuild around the enforceable events (`Stop`, `TaskCreated`,
`TaskCompleted`) and the multi-route installer, with integration tests that drive
the real binary.

---

## Cycle 7 — Act: rebuild as a multi-event engine

**Decide.** One file, dispatching on `hook_event_name`, so a single script serves
every event and the installer has exactly one artefact to copy.

**Act.** Wrote `tools/task_division.py`: handlers for `UserPromptSubmit`,
`SessionStart` (including `reason=compact`), `SubagentStart`, `PreCompact`,
`Stop`, `TaskCreated`, `TaskCompleted`, `SessionEnd`; a config file with
`mode=off|warn|enforce`; a JSONL ledger; and atomic per-prompt dedupe so
overlapping install routes inject once.

**Orient — the surprise.** The selftest passed, then failed when run a second
time. Dedupe claims persist on disk, and the test used fixed session ids, so the
second run collided with state the first run left behind. A test that only
passes on a clean machine is not a test. Fixed with per-run ids, and running it
twice is now part of the routine.

---

## Cycle 8 — Act: install to every route

**Act.** Rewrote the installer around five routes — `user`, `project`, `local`,
`skills-dir`, `plugin` — each idempotent, each backed up, each removable. The
plugin route also writes `.claude-plugin/marketplace.json` at the repo root.

`claude plugin validate --strict` passes on the generated plugin with no
warnings. All five routes install, `--check` reports green, and `--uninstall`
restores what was there.

---

## Cycle 9 — Act: prove the directive works on a session that is not this one

**Act.** Installed into a scratch config and ran `claude -p` against it with a
question that invites undivided prose.

**Observe.** The reply opened with a numbered task list and an explicit "(One
atomic task.)". The ledger recorded `session-start`, `inject`, `stop-ok`.

**Orient.** The mechanism works on a session that never saw this conversation.

---

## Cycle 10 — Act: prove the enforcement, not just the reminder

**Act.** Asked for two paragraphs of flowing prose — a request that pulls
against dividing.

**Observe.** The model's first reply was undivided prose. The `Stop` hook denied
it. The model revised, and the delivered reply opened with `**Task list:**`.
Ledger: `stop-denied`, twice, `chars: 2992`.

**Orient — the surprise, and it matters twice over.**

*First:* the injected directive alone was **not** enough. Told to write flowing
prose, the model followed the prompt and skipped the division.

> **Correction, from cycle 15.** This entry originally continued: "Only the
> `Stop` refusal produced it." That was wrong, and it was wrong in the specific
> way this log exists to catch — a conclusion drawn from a contaminated run. The
> `UserPromptSubmit` hook was also active during it (see cycle 14 for why), and
> a later clean run showed the refusal does *not* revise a reply in headless
> mode. The first half of the claim survives: the directive alone did not
> produce a division here. The second half does not. Left in place rather than
> rewritten, because a log that quietly edits its own mistakes is not evidence.

*Second:* `stop-denied` fired **twice** for one reply — `used: 1` then `used: 2`
— against a settings file with exactly one registration per event. The runtime
invokes `Stop` more than once per turn, so a single undivided reply spent the
entire two-refusal budget at once.

---

## Cycle 11 — Act: fix the double-spend, and find the real cause

**Decide.** Decide once per message, then replay that decision.

**Observe.** The first fix — read the record, then write it — did not work,
and the timestamps said why: both invocations landed in the *same second*. They
run concurrently, so check-then-write loses the race.

**Act.** Replaced it with an atomic `O_CREAT|O_EXCL` claim: the winner decides
and writes the verdict, the loser waits briefly and mirrors it. Proved with two
real processes racing on the same message — both return `deny`, one refusal is
spent.

**Orient.** Two bugs in this area now, both found by looking at a ledger rather
than by reasoning about the code. Neither would have shown up in a unit test
written from the design.

---

## Cycle 12 — Act: a unit suite that isolates itself

**Act.** Rewrote the suite around a temporary `CLAUDE_CONFIG_DIR` per test, so
nothing reads or writes the real `~/.claude`. 45 tests: every handler, the
division-detection truth table, config precedence, all five installer routes,
the v1 upgrade path, and the concurrency case as two real processes.

**Orient — the surprise.** One failure: `verify "1. a" "2. b"` reported *not
divided*. The command joined its arguments with spaces, and the detector is
line-based, so two tasks arrived as one line. The test was right and the tool
was wrong — the kind of result that only appears when the CLI is exercised the
way somebody would actually type it.

---

## Cycle 13 — Act: integration tests that assert on behaviour

**Decide.** Unit tests prove the engine emits the right JSON; they cannot prove
Claude Code reads it. Drive the real binary and assert on what the model does.

**Act.** Six tests behind `TASK_DIVISION_E2E=1`. Each runs with its own config
directory *and* its own working directory.

**Orient — the surprise.** The working directory mattered, and had been silently
wrong all along. See the next cycle.

---

## Cycle 14 — Observe: the earlier experiments were contaminated

**Observe.** The plugin test failed with "the plugin's UserPromptSubmit hook
never ran", though a direct probe in cycle 5 had proved plugin hooks fire. Two
separate causes, and both were mine:

1. The runtime sets `CLAUDE_PLUGIN_DATA` itself for plugin hooks, so the
   engine's ledger went to the runtime's directory and the test looked in a
   different one. The plugin was working perfectly.
2. The repository's own `.claude/settings.json` carried a `SessionStart`
   bootstrap that ran the installer. Every earlier `claude -p` launched from
   the repository therefore installed the project route into the *real*
   repository mid-experiment — which is why the cycle-10 "stop only" run had a
   `UserPromptSubmit` hook active, and why a later install reported replacing
   eight entries nobody remembered writing.

**Orient — the surprise.** A convenience feature added in the previous session
was silently rewriting the state of the experiments. Nothing in the code was
wrong; the *test rig* was wrong, and it had been producing plausible results.

**Act.** Added `CLAUDE_TASK_DIVISION_STATE_DIR` so the ledger can be pinned;
gave every live test its own working directory; replaced the bootstrap with the
project route registering the engine directly through `${CLAUDE_PROJECT_DIR}`.

---

## Cycle 15 — Observe: what a refused `Stop` actually does

**Decide.** Settle whether the refusal changes the delivered reply, with no
`UserPromptSubmit` hook anywhere near the experiment.

**Observe.** Clean stop-only config, fresh working directory. The ledger
recorded `stop-denied`. The delivered reply was 1877 bytes; the message the hook
had judged was 1876 — the same text, plus a newline. Nothing was revised.

Then, through `--output-format stream-json`: `hook_started` for `Stop`,
`hook_response` carrying `"permissionDecision": "deny"`, `outcome: success`,
`exit_code: 0` — and exactly **one** `assistant` event in the whole stream.

**Orient.** The runtime accepts the refusal. It simply has nowhere to put it:
the docs say a blocked `Stop` "fires the `Stop` hook again on the next turn",
and `claude -p` has no next turn. So `Stop` enforcement is real where another
turn follows, and inert in one-shot headless mode.

> **Correction, from cycle 22.** Wrong, and wrong for a reason worth keeping.
> Headless mode has next turns perfectly well. The refusal was ignored because
> it was sent in the field the *reference* documents, which this version does
> not act on. `outcome: success` in the event stream — which is what I read this
> conclusion off — only means the hook process exited 0. It says nothing about
> whether the payload did anything. Two wrong conclusions in a row from the same
> underlying bug, each one plausible, each one built on an observation that was
> real but did not mean what I took it to mean.

This also falsifies the second half of cycle 10, which is corrected in place
above rather than deleted.

**Act.** Wrote the limit into the documentation and into a test that asserts it,
so the day it stops being true, the suite says so.

---

## Cycle 16 — Observe: the detector was refusing correct replies

**Observe.** A live reply opened with `**Task list:**` followed by one numbered
task and "(One atomic task.)" — precisely what the directive asks for when a
request is atomic. `looks_divided` returned False. It required two numbered
items, and had no idea what a heading was.

**Orient — the surprise.** The enforcement half was punishing the exact
behaviour the instruction half asks for. Worse, this had been happening during
the runs used to justify earlier conclusions.

**Act.** Taught the detector about task-list headings, done-condition phrasing,
and bare `Task 1` / `tasks 2–5` references. Added the exact offending live reply
to the truth table as a regression case.

---

## Cycle 17 — Act: make the project route survive being cloned

**Observe.** The project route was writing an absolute path into a file meant to
be committed. On anyone else's machine that path does not exist.

**Act.** Project and local routes now register
`"${CLAUDE_PROJECT_DIR}/.claude/hooks/task_division.py"`. A test asserts the
committed settings contain no machine-specific path.

---

## Cycle 18 — Act: wire the repository

**Act.** Installed all four default routes for real: project hooks committed to
this repository, the plugin built at `plugins/task-division/`, a marketplace at
`.claude-plugin/marketplace.json`, the user route in `~/.claude`, and a
`skills-dir` copy that auto-loads next session.

The marketplace is registered in project settings but `enabledPlugins` is
deliberately left unset here: the project route already runs the hooks, and
enabling the plugin as well would run every hook twice for nothing.

`claude plugin validate --strict` passes. `--check` is green on every route.

---

## Cycle 19 — Orient: what this actually amounts to

Two mechanisms, and the honest summary is that neither is sufficient alone:

- **Injection** changes what the model does, verified by a passphrase that
  existed nowhere but the hook's output. It fails when the prompt itself pulls
  against dividing.
- **Refusal** is accepted by the runtime, verified in its own event stream. It
  fails when there is no next turn to spend.

Together they cover a session that forgot and a session that was talked out of
it. The one thing neither covers is a runtime that does not run hooks at all,
which is the reported state of Cowork.

**The pattern across nineteen cycles.** Every real bug came from watching
something run, and none came from reading the code: the selftest that passed
once, the refusal budget spent twice, the concurrent processes, the contaminated
working directory, the detector refusing a correct reply. The design was
plausible each time. The ledger was not.

---

## Cycle 20 — Act: tell the truth in the documentation

**Act.** Rewrote `docs/task-division.md` around what was verified and how, with
the limits stated rather than implied — headless refusal, cloud config, Cowork,
per-machine reach, and the flakiness of tests that talk to a live API.

**Falsifier for the whole thing.** If `make e2e` stops passing, one of the
claims above has expired. That is the point of writing them as tests.

---

## Cycle 21 — Observe: read what Anthropic itself says about writing hooks

Source: `anthropics/claude-code`,
`plugins/plugin-dev/skills/hook-development/SKILL.md`, read 2026-08-28.

**Observe.** Anthropic's own hook-development guidance documents the `Stop`
contract as:

```json
{"decision": "approve|block", "reason": "Why continuing or stopping"}
```

The public hooks reference documents it as
`hookSpecificOutput.permissionDecision: "deny"` with
`permissionDecisionReason`. These are not the same field, not the same nesting,
and not the same vocabulary.

**Orient — the surprise.** Every `Stop` refusal shipped so far used the second
form. If the runtime only reads the first, the enforcement half of this system
has never done anything, and cycle 15's "no next turn in headless mode" was a
misdiagnosis of my own bug rather than a property of the product.

**Decide.** Do not pick by authority. Measure. Falsifier: run the same session
under each payload and count assistant turns — a refusal that works produces
more than one.

---

## Cycle 22 — Act: measure which `Stop` payload the runtime honours

**Act.** Three variants, same prompt, same everything else, blocking once each:

| Variant | Payload | `assistant` turns | Verdict |
|---|---|---|---|
| A | `hookSpecificOutput.permissionDecision: "deny"` | 1 | ignored |
| B | top-level `{"decision": "block", "reason": …}` | 3 | **honoured** |
| C | both together | 3 | honoured |

**Orient — the surprise, and it is the largest one in this log.** The documented
form does nothing. The `Stop` check had been shipping, passing its own tests,
recording refusals in its ledger, and reporting `outcome: success` — while
having no effect whatsoever on any session. The tests were green because they
asserted on the JSON the engine produced, not on whether anything happened.

**Act.** The engine now sends both forms. Verified immediately afterwards on a
clean stop-only config: 2594 characters of undivided prose, refused, revised,
and the delivered reply opened `1. Write a flowing-prose explanation …
**Done-condition:** …`. Ledger: `stop-denied`, then `stop-ok`.

The headless "limitation" documented in cycle 15 and written into the docs was
deleted, because it was never real. The test that asserted it has been replaced
by one that counts assistant turns — the test that would have caught this.

---

## Cycle 23 — Act: apply the same doubt to the task events

**Observe.** `TaskCreated` and `TaskCompleted` are documented exactly as `Stop`
was, so the same doubt applies. Ran the same three-variant probe.

**Result: inconclusive, for a reason worth recording.** The task tools do not
exist in headless `claude -p` sessions — all three runs came back "there is no
`TaskCreate` tool available in this environment" — so the hook never fired.

**Decide.** Send both forms for these events too, marked in the code as
inference from the `Stop` result rather than measurement, with the falsifier
written into `docs/open-items.md`. Guessing silently would have been the easy
option; guessing out loud is the honest one.

---

## Cycle 24 — Act: close the distribution questions

Three things that had been asserted rather than tested:

- **`claude plugin marketplace add` → `install`** works end to end, and the
  installed plugin's hooks fire: the session's reply came back under a
  "## Task breakdown" heading with per-task done-conditions.
- **Bug [#53643](https://github.com/anthropics/claude-code/issues/53643)**
  (a plugin contributing `UserPromptSubmit` writing `"UserPromptSubmit": null`
  into `settings.json`) **does not reproduce** — after the install the file held
  only well-formed `extraKnownMarketplaces` and `enabledPlugins`.
- **The `/divide` skill loads.** It appeared in a live session's skill list as
  `task-division:divide` — the namespaced form, which also proves the
  `skills-dir` directory loaded as a plugin and not as a bare skill.

Both referenced issues are now closed as duplicates upstream; #10225 was filed
against 2.0.24 and does not reproduce on 2.1.247.

---

## Cycle 25 — Act: does the directive reach a subagent, or only the hook?

**Observe.** `subagent-start` appeared in the ledger with `agent_type: Explore`.
That proves a process ran. It does not prove the subagent saw anything — the
same distinction that mattered in cycle 6.

**Act.** Injected `MARLINGROVE-3318` through `SubagentStart` and asked an
`Explore` subagent to report the passphrase it had been given. It came back.

**Orient — an unexpected and welcome surprise.** The subagent reported the
passphrase *and* flagged it as a likely prompt-injection pattern, noting it was
not part of its real system prompt. That is correct behaviour from the subagent,
and it is a genuine limit on this delivery route: context injected at
`SubagentStart` arrives, but may be treated as suspicious rather than
authoritative. Recorded in the docs rather than glossed, and the mechanism does
not depend on subagents complying.

---

## Cycle 26 — Orient: what is left, and why each thing is left

Everything that was ever in doubt now lives in `docs/open-items.md`, closed or
open, and an open item carries the reason it could not be settled here plus the
falsifier that would settle it. Four remain open, none of them silently:

- the `TaskCreated`/`TaskCompleted` contract — task tools absent from headless
  sessions;
- `SessionStart` re-seeding after compaction — a one-shot run cannot fill a
  context window;
- Cowork — not present in this environment; the upstream issue's stated root
  cause is a sandbox/host split, which *hints* the project route may survive
  there, and a hint is not a finding;
- the two repositories' branch divergence, and the marketplace `ref` pinned to
  this branch — both the owner's decisions, not this session's.

**The pattern, now unmistakable.** Every significant error in this log came from
an observation that was real and did not mean what it appeared to mean: a
selftest that passed, a hook that exited 0, a refusal the runtime "accepted", a
reply that looked undivided. The fix each time was to measure the *effect*
rather than the *event* — count the turns, read the passphrase back, check what
actually changed on disk. A hook that runs is not a hook that works.

---

## Cycle 27 — Act: close the task-event question from a session that has task tools

**Observe.** Cycle 23 left the `TaskCreated` contract open because headless
sessions have no task tools. This session does. The falsifier had already been
written down, so it was simply run: `enforce_task_quality=true`, then create a
deliberately shapeless task.

**Result.** The hook fired — `task-shape` in the ledger — and the task was
**created anyway**, with both payload forms sent. `TaskCompleted` likewise. So
unlike `Stop`, these events do not honour a refusal on 2.1.247. The inference
made in cycle 23 was the right precaution and the wrong prediction, which is
exactly why it was labelled as inference.

**Orient — two more of my own bugs, surfaced by the same run.**

The first finding was not the denial at all: the hook reported *"the task has no
subject"* for a task whose subject was plainly set. Logging the payload keys
settled it — a live `TaskCreated` carries `task_subject`, while the reference
documents `task_title`. Reading the documented name found nothing, so every task
ever created had been reported as subject-less. The check looked like it was
working; it was reading a field that never arrives.

The second: `TaskCompleted` carries exactly the same keys — no
`completion_notes`, despite the reference documenting one. The intended check
("say what makes this task done") is unimplementable, and against an absent
field it would have flagged every completion forever. That handler is now
observational: it logs and emits nothing. Deleting a check is the right move
when the data it needs does not exist.

**The recurring shape, one more time.** Three sources of truth — the reference,
Anthropic's own plugin-dev skill, and the running binary — and the binary is the
only one that has been right every time. Everything in this system that was
wrong for more than five minutes was wrong because something *plausible* was
believed instead of measured.

---

## Cycle 28 — Act: force a compaction, and find the third wrong field name

**Observe.** Cycle 26 listed the post-compaction re-seed as unverifiable because
a one-shot run cannot fill a context window. That was a failure of imagination:
a compaction can be *asked for*. `-p --continue` builds a conversation, `/compact`
compacts it.

First attempt: "Not enough messages to compact" — but `PreCompact` fired, with
`trigger: "manual"`. Six turns later the compaction ran for real, and a
`SessionStart` followed it — with `reason: ""`.

**Orient — the third field-name mismatch, and the worst-hidden one.** Logging
the payload keys settled it: a live `SessionStart` carries `cwd,
hook_event_name, session_id, source, transcript_path`, plus `model` and
`prompt_id` after a compaction. The reason lives in **`source`**. The reference
documents `session_start_reason`, which is simply not sent.

So the compaction branch had never run — every start read as reasonless. Reading
`source` gives `"compact"` after a compaction and `"resume"` under `--continue`,
both now in the ledger.

**A second bug, found while fixing the first.** Session starts were being
deduplicated. A compaction fires `SessionStart` again in the same session, so
that dedupe could swallow the re-seed at exactly the moment the directive has
just been dropped from context — the one moment it exists for. Session starts
are no longer deduplicated at all: seeding twice is free, missing the re-seed is
not. And the recovery wording now sits in *every* session directive, so it no
longer depends on any field name being right.

**Orient — the shape of all four field bugs.** `task_title` → `task_subject`.
`completion_notes` → does not exist. `session_start_reason` → `source`.
`permissionDecision: deny` → `decision: block`. Every one of them was read from
the reference, and every one produced code that ran cleanly, exited 0, logged
happily, and did nothing. A hook that runs is not a hook that works — and a
field that parses is not a field that arrives.

**What is left.** Three items, none of them silent: Cowork, which is not in this
environment; and the branch divergence plus the pinned marketplace ref, which
are the owner's decisions and not this session's to make. Each carries its
falsifier in `docs/open-items.md`.
