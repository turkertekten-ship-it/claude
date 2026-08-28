#!/usr/bin/env python3
"""Divide every prompt into tasks — the engine behind the hooks.

One file, standard library only, no imports outside it. Hooks run as a
subprocess on every prompt, so this stays cheap to start and trivial to vendor:
the installer copies this single file, and the plugin bundles the same one.

It dispatches on the `hook_event_name` field of the payload Claude Code sends on
stdin, so one script serves every event it handles:

| Event | What it does |
|---|---|
| `UserPromptSubmit` | Injects the division directive into the prompt |
| `SessionStart` | Seeds the directive before the first prompt, and again after a compaction |
| `SubagentStart` | Carries the directive into subagent contexts, which never saw it |
| `PreCompact` | Records that a compaction is about to drop the directive |
| `Stop` | Checks the response actually contains a division, and can refuse the stop |
| `TaskCreated` | Checks the task carries a checkable done-condition |
| `TaskCompleted` | Checks a completion is accounted for |
| `SessionEnd` | Closes out the session's ledger entry |

Behaviour is verified against the real binary in `tests/test_integration.py`,
which drives `claude -p` and asserts on what the model does, not on JSON shape.

Contracts are taken from <https://code.claude.com/docs/en/hooks> and from
`anthropics/claude-code` `plugins/plugin-dev/skills/hook-development/SKILL.md`,
both read 2026-08-27 — and where those two disagree, from measuring the binary.

The disagreement is not academic. For `Stop`, the reference's
`hookSpecificOutput.permissionDecision: "deny"` is accepted and *ignored* on
2.1.247, while the plugin-dev skill's top-level `{"decision": "block"}` is
honoured. Sending only the documented form produced a refusal that had never
once worked. Denials therefore carry both forms; see `emit()`.

Prompt-rewriting fields are deliberately unused — two reads of the reference
disagreed on their names, and nothing here needs them.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

VERSION = "2.0.0"
MARKER = "claude-task-division"

# Events this engine answers. Anything else is acknowledged and ignored, so a
# stray registration can never turn into an error the user has to debug.
HANDLED = (
    "UserPromptSubmit",
    "SessionStart",
    "SubagentStart",
    "PreCompact",
    "Stop",
    "TaskCreated",
    "TaskCompleted",
    "SessionEnd",
)

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

SESSION_DIRECTIVE = """\
== standing directive for this session: divide every prompt into tasks ==

Every prompt in this session gets restated as a numbered list of tasks with
checkable done-conditions before any work starts, tracked with TaskCreate and
TaskUpdate where those tools exist. A genuinely atomic request still gets a
one-item list, stated explicitly rather than skipped.

If a task list from earlier in this session is still in flight — after a
compaction, a resume or a fork — recover it with TaskList and continue it rather
than starting a new one."""

COMPACT_DIRECTIVE = """\
== re-stating a directive that compaction may have dropped ==

This session divides every prompt into a numbered task list with checkable
done-conditions before any work starts. Any task list that was in flight before
the compaction is still in flight: recover it with TaskList rather than starting
over."""

SUBAGENT_DIRECTIVE = """\
== standing directive: divide your assignment into tasks ==

Before starting, restate your assignment as a numbered list of tasks, each with
a checkable done-condition, and report against that list. If the assignment is a
single atomic task, say so explicitly."""

STOP_REASON = """\
Your reply does not contain a task division, and every reply in this session
needs one.

Restate the request as a numbered list of tasks, each with an imperative subject
and a done-condition somebody else could check, and say which ones you have
finished. If this request really was a single atomic task, say so explicitly and
give the one-item list — that counts, and silence does not."""

# Signals that a division is present. Deliberately broad: a false negative here
# blocks a reply that was fine, which is far worse than a false positive.
NUMBERED = re.compile(r"^[ \t]{0,3}(\d+)[.)][ \t]+\S", re.M)
TABLE_ROW = re.compile(r"^[ \t]{0,3}\|.*\|", re.M)
CHECKBOX = re.compile(r"^[ \t]{0,3}[-*][ \t]+\[[ xX]\]", re.M)
TASK_REF = re.compile(r"\bTasks?\s*#?\s*\d+\b|\bTaskCreate\b|\bTaskUpdate\b|\bTaskList\b", re.I)
# A one-item list under a "Task list:" heading is exactly what the directive
# asks for when a request is atomic. An earlier version missed it and refused a
# reply that had done the right thing, so the header counts as a signal.
TASK_HEADER = re.compile(
    r"^[ \t]{0,3}[#>*_\s]*\b(task list|tasks|task division|task breakdown|division of work|"
    r"task table|plan of tasks)\b",
    re.I | re.M,
)
DONE_CONDITION = re.compile(r"done[- ]condition|done when|complete when|finished when", re.I)
ATOMIC = re.compile(
    r"single atomic task|one atomic task|atomic task|one-item list|"
    r"single task|one task[,:.]|is one task",
    re.I,
)


# --------------------------------------------------------------------------
# state, config and the ledger
# --------------------------------------------------------------------------


def state_dir() -> Path:
    """Where per-session state and the ledger live.

    An explicit override wins, then the plugin's persistent data directory when
    running as a plugin (it survives plugin updates), then the config directory.
    The override exists because the runtime sets `CLAUDE_PLUGIN_DATA` itself for
    plugin hooks, so it is the only way to point the ledger at a known place.
    """
    override = os.environ.get("CLAUDE_TASK_DIVISION_STATE_DIR", "").strip()
    if override:
        return Path(override)
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA", "").strip()
    if plugin_data:
        return Path(plugin_data)
    config = os.environ.get("CLAUDE_CONFIG_DIR", "").strip()
    base = Path(config) if config else Path.home() / ".claude"
    return base / "task-division"


DEFAULT_CONFIG = {
    # off | warn | enforce. enforce is the only mode that can refuse a stop.
    "mode": "enforce",
    # Replies shorter than this are never challenged; a one-line answer to a
    # one-line question does not need a task table.
    "min_response_chars": 400,
    # Hard ceiling on refusals per session, so a disagreement about what counts
    # as a division can never become a loop.
    "max_denials_per_session": 2,
    # Task-shape checks are advisory. Enforcement is offered but is *not
    # honoured* by 2.1.247 — a denied TaskCreated is created anyway — so this
    # only changes the wording the transcript sees. See docs/open-items.md.
    "enforce_task_quality": False,
    "log_events": True,
}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    path = state_dir() / "config.json"
    try:
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                cfg.update({k: v for k, v in loaded.items() if k in DEFAULT_CONFIG})
    except Exception:
        pass  # a broken config must not break the session

    env_mode = os.environ.get("CLAUDE_TASK_DIVISION_MODE", "").strip().lower()
    if env_mode in ("off", "warn", "enforce"):
        cfg["mode"] = env_mode
    if os.environ.get("CLAUDE_TASK_DIVISION_DISABLE", "") not in ("", "0", "false"):
        cfg["mode"] = "off"
    return cfg


def _write(path: Path, text: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except Exception:
        pass


def log_event(cfg: dict, kind: str, detail: dict) -> None:
    if not cfg.get("log_events", True):
        return
    try:
        path = state_dir() / "ledger.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "kind": kind}
        entry.update(detail)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def session_file(payload: dict, suffix: str) -> Path:
    session = str(payload.get("session_id") or "nosession")
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session)[:80]
    return state_dir() / "sessions" / f"{safe}.{suffix}"


# --------------------------------------------------------------------------
# dedupe: several routes may install the same hook
# --------------------------------------------------------------------------


def prompt_fingerprint(payload: dict) -> str:
    """Identify one prompt, so two installed routes inject the directive once."""
    text = ""
    for key in ("prompt", "prompt_text", "user_prompt"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            text = value
            break
    raw = f"{payload.get('session_id', '')}|{payload.get('prompt_id', '')}|{text}"
    return hashlib.sha1(raw.encode("utf-8", "replace")).hexdigest()[:16]


def claim_once(payload: dict, kind: str) -> bool:
    """True if this process is the first to handle this prompt.

    Returns True on any failure: injecting twice is a cosmetic problem, and
    failing to inject is the problem the whole thing exists to prevent.
    """
    try:
        directory = state_dir() / "claims"
        directory.mkdir(parents=True, exist_ok=True)
        claim = directory / f"{kind}.{prompt_fingerprint(payload)}"
        # O_EXCL makes this atomic between concurrent hook processes.
        fd = os.open(str(claim), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        _sweep(directory)
        return True
    except FileExistsError:
        return False
    except Exception:
        return True


def _sweep(directory: Path, max_age: int = 86400) -> None:
    try:
        cutoff = time.time() - max_age
        for entry in directory.iterdir():
            if entry.is_file() and entry.stat().st_mtime < cutoff:
                entry.unlink(missing_ok=True)
    except Exception:
        pass


# --------------------------------------------------------------------------
# division detection
# --------------------------------------------------------------------------


def looks_divided(text: str) -> bool:
    """Does this reply contain something a reader would recognise as a division?"""
    if not text or not text.strip():
        return False
    if len(NUMBERED.findall(text)) >= 2:
        return True
    if len(CHECKBOX.findall(text)) >= 2:
        return True
    if len(TABLE_ROW.findall(text)) >= 3:
        return True
    if TASK_REF.search(text):
        return True
    if ATOMIC.search(text):
        return True
    # A single item is a valid division when it is presented as one.
    has_item = bool(NUMBERED.search(text) or CHECKBOX.search(text) or len(TABLE_ROW.findall(text)) >= 2)
    if has_item and TASK_HEADER.search(text):
        return True
    if has_item and DONE_CONDITION.search(text):
        return True
    return False


def task_quality(subject: str, description: str) -> list:
    """Findings about a task's shape. Empty means it is well formed."""
    findings = []
    subject = (subject or "").strip()
    description = (description or "").strip()
    if not subject:
        findings.append("the task has no subject")
    elif len(subject.split()) < 2:
        findings.append(f"the subject {subject!r} is not an imperative phrase")
    if not description:
        findings.append("the task has no description, so it states no done-condition")
    elif len(description) < 20:
        findings.append("the description is too short to contain a checkable done-condition")
    return findings


# --------------------------------------------------------------------------
# output helpers
# --------------------------------------------------------------------------


def emit(event, *, context="", message="", decision="", reason="", also_block=False):
    """Build a hook response.

    `also_block` adds the top-level `decision`/`reason` pair alongside the
    `hookSpecificOutput` fields. Both forms are documented, by different
    sources, and only one of them works:

        permissionDecision: deny   (code.claude.com/docs/en/hooks)  -> IGNORED
        decision: block            (anthropics/claude-code plugin-dev skill) -> honoured

    Measured on 2.1.247 by counting assistant turns in `--output-format
    stream-json`: with only the first form the session ends after one turn; with
    the second, or with both together, the model is sent back for another turn.
    Sending both is deliberate — the pair that works today is not the pair the
    reference documents, so pinning to either alone is a bet on which one a
    future version keeps.
    """
    specific = {"hookEventName": event}
    if context:
        specific["additionalContext"] = context
    if message:
        specific["systemMessage"] = message
    if decision:
        specific["permissionDecision"] = decision
        if reason:
            specific["permissionDecisionReason"] = reason
    output = {"hookSpecificOutput": specific}
    if decision == "deny" and also_block:
        output["decision"] = "block"
        if reason:
            output["reason"] = reason
    return output


# --------------------------------------------------------------------------
# handlers
# --------------------------------------------------------------------------


def on_user_prompt_submit(payload, cfg):
    if not claim_once(payload, "prompt"):
        return None  # another installed route already injected for this prompt
    cwd = str(payload.get("cwd") or "").strip()
    context = DIRECTIVE + (f"\n\nWorking directory for this prompt: {cwd}" if cwd else "")
    log_event(cfg, "inject", {"event": "UserPromptSubmit", "session": payload.get("session_id")})
    return emit("UserPromptSubmit", context=context)


def on_session_start(payload, cfg):
    """Seed the directive at every session start, including after a compaction.

    Deliberately *not* deduplicated, and deliberately not relying on
    `session_start_reason`. Measured on 2.1.247: a real compaction fires
    `PreCompact` with `trigger: "manual"` and then a `SessionStart` whose reason
    is **empty**, not the documented `"compact"`. An earlier version keyed a
    special compaction directive off that value, which therefore never ran, and
    deduplicated session starts — which risked swallowing the re-seed at exactly
    the moment the directive has just been dropped from context.

    Seeding twice is harmless. Failing to re-seed after a compaction is the
    failure this handler exists to prevent, so the trade goes that way, and the
    session directive itself carries the recovery wording for every start.
    """
    # `source`, not the documented `session_start_reason`: a live SessionStart
    # payload carries cwd, hook_event_name, session_id, source, transcript_path
    # (plus model and prompt_id after a compaction). Reading the documented name
    # produced an empty reason for every start, which is what made the
    # compaction branch look like dead code.
    reason = _first(payload, "source", "session_start_reason", "reason").strip().lower()
    context = COMPACT_DIRECTIVE if reason in ("compact", "postcompact") else SESSION_DIRECTIVE
    log_event(
        cfg,
        "session-start",
        {"reason": reason, "session": payload.get("session_id"), "keys": sorted(payload.keys())},
    )
    return emit("SessionStart", context=context)


def on_subagent_start(payload, cfg):
    log_event(cfg, "subagent-start", {"agent_type": payload.get("agent_type")})
    return emit("SubagentStart", context=SUBAGENT_DIRECTIVE)


def on_pre_compact(payload, cfg):
    # Never block a compaction: running out of context is worse than losing the
    # directive, and SessionStart fires again with reason "compact" to restore it.
    log_event(cfg, "pre-compact", {"trigger": payload.get("trigger")})
    return emit("PreCompact")


def on_session_end(payload, cfg):
    log_event(cfg, "session-end", {"session": payload.get("session_id")})
    return None


def _stop_record(payload, message):
    digest = hashlib.sha1(message.encode("utf-8", "replace")).hexdigest()[:16]
    session = re.sub(r"[^A-Za-z0-9_.-]", "_", str(payload.get("session_id") or "nosession"))[:80]
    return state_dir() / "stop" / f"{session}.{digest}"


def _recall_stop(payload, message):
    """Claim the right to decide about this message.

    Returns None if this process is the first to see it and should decide, or
    the decision already made if another process got there first.

    Observed on 2.1.247: the two Stop invocations for one turn run
    *concurrently* — both landed in the same second. A read-then-write check
    loses that race and spends two refusals on one reply, so the claim is taken
    with O_CREAT|O_EXCL, which is atomic.
    """
    try:
        record = _stop_record(payload, message)
        record.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(str(record), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
            return None  # we won the claim; ours is the deciding process
        except FileExistsError:
            pass
        # Someone else is deciding. Wait briefly for them to write the verdict.
        for _ in range(20):
            text = record.read_text(encoding="utf-8").strip()
            if text:
                return text == "deny"
            time.sleep(0.05)
        # Undecided in time: say nothing rather than deny twice. A concurrent
        # deny still reaches the runtime from the process that made it.
        return False
    except Exception:
        return None


def _remember_stop(payload, message, denied):
    try:
        _write(_stop_record(payload, message), "deny" if denied else "allow")
    except Exception:
        pass


def on_stop(payload, cfg):
    """The teeth: refuse to finish a reply that never divided the work."""
    if cfg["mode"] == "off":
        return None

    message = ""
    for key in ("last_assistant_message", "last_message", "assistant_message"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            message = value
            break

    stop_reason = str(payload.get("stop_reason") or "end_turn")
    if stop_reason not in ("end_turn", ""):
        return None  # mid-turn stops are not a finished reply
    if len(message.strip()) < int(cfg["min_response_chars"]):
        return None  # short answers do not owe a task table
    if looks_divided(message):
        log_event(cfg, "stop-ok", {"chars": len(message)})
        return None

    # Observed on 2.1.247: the runtime can invoke the Stop hook more than once
    # for a single turn. Without this, one undivided reply would spend the whole
    # refusal budget at once. Decide once per message and replay that decision.
    decided = _recall_stop(payload, message)
    if decided is not None:
        log_event(cfg, "stop-replay", {"denied": decided})
        return emit("Stop", decision="deny", reason=STOP_REASON) if decided else None

    counter = session_file(payload, "denials")
    try:
        used = int(counter.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        used = 0
    if used >= int(cfg["max_denials_per_session"]):
        _remember_stop(payload, message, False)
        log_event(cfg, "stop-exhausted", {"used": used})
        return emit(
            "Stop",
            message="task division missing; refusal budget for this session is spent",
        )

    _write(counter, str(used + 1))
    log_event(cfg, "stop-denied", {"used": used + 1, "chars": len(message)})

    if cfg["mode"] == "warn":
        _remember_stop(payload, message, False)
        return emit("Stop", message="No task division found in this reply.")
    _remember_stop(payload, message, True)
    return emit("Stop", decision="deny", reason=STOP_REASON, also_block=True)


def _first(payload, *names):
    """First non-empty value among several candidate key names.

    The payload key for a task's subject is not what the reference says: a live
    TaskCreate whose subject was set still reported "the task has no subject",
    so `task_title` was absent. The ledger records the keys actually seen, which
    is how the real names get established rather than guessed.
    """
    for name in names:
        value = payload.get(name)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def on_task_created(payload, cfg):
    subject = _first(payload, "task_title", "task_subject", "subject", "title", "name")
    description = _first(payload, "task_description", "description", "task_body", "body")
    findings = task_quality(subject, description)
    if not findings:
        return None
    detail = "; ".join(findings)
    log_event(cfg, "task-shape", {"findings": findings, "keys": sorted(payload.keys())})
    if cfg["mode"] == "enforce" and cfg.get("enforce_task_quality"):
        # Sent, but do not expect it to bite: measured on 2.1.247, a TaskCreated
        # denial is ignored in both forms — the task is created regardless. Kept
        # so the check starts working the day the event honours it, and so the
        # advisory systemMessage below still reaches the transcript.
        return emit(
            "TaskCreated",
            decision="deny",
            reason=f"This task is not checkable: {detail}. Give it an imperative "
            f"subject and a description stating a done-condition, then create it again.",
            also_block=True,
        )
    return emit("TaskCreated", message=f"task division: {detail}")


def on_task_completed(payload, cfg):
    """Observational only, and deliberately so.

    The design here was to require a completion to say what makes the task done.
    The payload makes that impossible: measured on 2.1.247, `TaskCompleted`
    carries exactly `cwd, hook_event_name, prompt_id, session_id,
    task_description, task_id, task_subject, transcript_path` — there is no
    `completion_notes` field, despite the reference documenting one. A check
    against a field that never arrives would flag every completion forever,
    which is worse than not checking.
    """
    log_event(cfg, "task-completed", {"task": payload.get("task_id")})
    return None


DISPATCH = {
    "UserPromptSubmit": on_user_prompt_submit,
    "SessionStart": on_session_start,
    "SubagentStart": on_subagent_start,
    "PreCompact": on_pre_compact,
    "SessionEnd": on_session_end,
    "Stop": on_stop,
    "TaskCreated": on_task_created,
    "TaskCompleted": on_task_completed,
}


# --------------------------------------------------------------------------
# entry points
# --------------------------------------------------------------------------


def read_payload(stream):
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


def run_hook(payload, cfg, forced_event=""):
    event = forced_event or str(payload.get("hook_event_name") or "UserPromptSubmit")
    if cfg["mode"] == "off":
        return None
    handler = DISPATCH.get(event)
    if handler is None:
        return None
    return handler(payload, cfg)


def cmd_hook(argv):
    forced = ""
    if "--event" in argv:
        index = argv.index("--event")
        if index + 1 < len(argv):
            forced = argv[index + 1]
    payload = read_payload(sys.stdin)
    cfg = load_config()
    try:
        output = run_hook(payload, cfg, forced)
    except Exception as exc:
        log_event(cfg, "error", {"error": str(exc)})
        return 0
    if output:
        print(json.dumps(output))
    return 0


def cmd_verify(argv):
    """Check text for a division. 0 divided, 1 not. For CI and for testing.

    Arguments are joined with newlines, not spaces: the detector is line-based,
    so `verify "1. a" "2. b"` must read as two lines and not as one.
    """
    text = sys.stdin.read() if not argv else "\n".join(argv)
    if looks_divided(text):
        print("divided")
        return 0
    print("not divided")
    return 1


def cmd_log(argv):
    path = state_dir() / "ledger.jsonl"
    if not path.exists():
        print(f"no ledger yet at {path}")
        return 0
    limit = 20
    if "-n" in argv:
        index = argv.index("-n")
        if index + 1 < len(argv):
            try:
                limit = int(argv[index + 1])
            except ValueError:
                pass
    lines = path.read_text(encoding="utf-8").splitlines()
    counts = {}
    for line in lines:
        try:
            kind = json.loads(line).get("kind", "?")
        except Exception:
            continue
        counts[kind] = counts.get(kind, 0) + 1
    print(f"{len(lines)} events in {path}")
    for kind, count in sorted(counts.items(), key=lambda item: -item[1]):
        print(f"  {count:5d}  {kind}")
    print("--- most recent ---")
    for line in lines[-limit:]:
        print(f"  {line}")
    return 0


def cmd_config(argv):
    cfg = load_config()
    if argv:
        path = state_dir() / "config.json"
        for pair in argv:
            if "=" not in pair:
                print(f"expected key=value, got {pair!r}", file=sys.stderr)
                return 2
            key, _, value = pair.partition("=")
            if key not in DEFAULT_CONFIG:
                print(f"unknown key {key!r}; known: {', '.join(sorted(DEFAULT_CONFIG))}", file=sys.stderr)
                return 2
            if value.lower() in ("true", "false"):
                cfg[key] = value.lower() == "true"
            elif value.isdigit():
                cfg[key] = int(value)
            else:
                cfg[key] = value
        _write(path, json.dumps(cfg, indent=2) + "\n")
        print(f"wrote {path}")
    print(json.dumps(cfg, indent=2))
    return 0


def cmd_selftest(_argv):
    import io

    failures = []

    def check(condition, label):
        if not condition:
            failures.append(label)

    cfg = dict(DEFAULT_CONFIG)

    # Unique per run: dedupe claims and denial counters persist on disk, so a
    # fixed id would make the second run of this selftest fail against state the
    # first run left behind. Caught by running it twice, which is the point.
    run_id = f"selftest-{os.getpid()}-{time.time_ns()}"
    prompt = {"cwd": "/tmp/x", "session_id": run_id, "prompt": "p"}

    out = on_user_prompt_submit(dict(prompt), cfg)
    check(bool(out), "UserPromptSubmit produced no output")
    if out:
        specific = out["hookSpecificOutput"]
        check(specific["hookEventName"] == "UserPromptSubmit", "wrong hookEventName")
        check("TaskCreate" in specific["additionalContext"], "directive lost TaskCreate")
        check("/tmp/x" in specific["additionalContext"], "cwd not carried")

    repeat = on_user_prompt_submit(dict(prompt), cfg)
    check(repeat is None, "dedupe failed: the same prompt injected twice")

    check(looks_divided("1. do a thing\n2. do another"), "numbered list not detected")
    check(looks_divided("This is a single atomic task."), "atomic declaration not detected")
    check(looks_divided("Task #3 created"), "task reference not detected")
    check(not looks_divided("Sure, here is the answer to your question."), "false positive")

    long_bare = "x" * 900
    denied = on_stop({"session_id": run_id + "-a", "last_assistant_message": long_bare}, cfg)
    check(
        bool(denied) and denied["hookSpecificOutput"].get("permissionDecision") == "deny",
        "Stop did not deny an undivided reply",
    )
    ok = on_stop({"session_id": run_id + "-b", "last_assistant_message": "1. a\n2. b\n" + long_bare}, cfg)
    check(ok is None, "Stop denied a divided reply")
    short = on_stop({"session_id": run_id + "-c", "last_assistant_message": "yes"}, cfg)
    check(short is None, "Stop challenged a short reply")

    # Observed on 2.1.247: the runtime can call Stop twice for one turn. The
    # same reply must therefore decide once and spend one refusal, not two.
    same = {"session_id": run_id + "-d", "last_assistant_message": long_bare}
    first, again = on_stop(dict(same), cfg), on_stop(dict(same), cfg)
    check(
        bool(first) and first["hookSpecificOutput"].get("permissionDecision") == "deny",
        "first Stop on an undivided reply did not deny",
    )
    check(
        bool(again) and again["hookSpecificOutput"].get("permissionDecision") == "deny",
        "second Stop for the same reply changed its decision",
    )
    try:
        spent = int((state_dir() / "sessions" / f"{run_id}-d.denials").read_text(encoding="utf-8"))
    except Exception:
        spent = -1
    check(spent == 1, f"one reply spent {spent} refusals, expected 1")

    # Across distinct replies the budget must actually run out, or a
    # disagreement about what counts as a division becomes an infinite loop.
    budget_session = run_id + "-e"
    ceiling = int(cfg["max_denials_per_session"])
    outcomes = [
        on_stop({"session_id": budget_session, "last_assistant_message": long_bare + str(i)}, cfg)
        for i in range(ceiling + 2)
    ]
    denials = sum(
        1 for o in outcomes if o and o["hookSpecificOutput"].get("permissionDecision") == "deny"
    )
    check(denials == ceiling, f"refusal budget not honoured: {denials} denials, ceiling {ceiling}")

    for bad in ("", "   ", "not json", "[1,2,3]", "null"):
        check(read_payload(io.StringIO(bad)) == {}, f"malformed stdin not coerced: {bad!r}")

    off = dict(cfg, mode="off")
    check(run_hook({"hook_event_name": "UserPromptSubmit"}, off) is None, "off mode still emitted")
    check(run_hook({"hook_event_name": "Nonsense"}, cfg) is None, "unknown event not ignored")

    for line in failures:
        print(f"FAIL {line}", file=sys.stderr)
    print(f"selftest: {'FAILED' if failures else 'ok'} ({len(failures)} failures)")
    return 1 if failures else 0


COMMANDS = {
    "hook": cmd_hook,
    "verify": cmd_verify,
    "log": cmd_log,
    "config": cmd_config,
    "selftest": cmd_selftest,
}


def main(argv):
    if argv and argv[0] in ("--version", "-V"):
        print(VERSION)
        return 0
    if argv and argv[0] == "--selftest":
        return cmd_selftest(argv[1:])
    if argv and argv[0] in COMMANDS:
        return COMMANDS[argv[0]](argv[1:])
    return cmd_hook(argv)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Exception:
        # A hook must never be the reason a prompt or a turn fails.
        sys.exit(0)
