# Wilson-E/automation — the DOE "Directive" layer, read first-hand

Collected 2026-08-28. `git clone --depth 1 https://github.com/Wilson-E/automation`
into `/home/user/wilson/automation`, HEAD `2023e3a`.

Its `CLAUDE.md` opens: "following the DOE Framework (Directive, Orchestration,
Execution) inspired by Nick Saraev's approach to AI automation" — the fourth
third-party DOE implementation read in this session, and the first with a
directive layer split into a global file plus one per automation.

## What the directive layer contains

```
$ ls directives/
email-triage.md  global.md  latin-learning.md  research.md
```

`global.md` is cross-cutting: Principles (safety first, transparency, graceful
failure, privacy), Error Handling, Logging. Each of the other three is a single
automation's Goal, Guardrails, and Output Format. `email-triage.md` guardrails:

```
1. **Never delete emails.** Only apply labels.
2. **Never send replies.** Classification only.
3. **Never mark emails as read.** The user decides when they have read something.
4. **Never move emails to trash or spam.** Leave that to Gmail's built-in filters.
5. **Archive noise is optional** and controlled by `archive_noise` in config.json (default: false).
```

## What reads them

Nothing.

```
$ grep -rn "directive" --include="*.py" .
$ echo $?
0                                  # no matches; no Python file mentions the word

$ grep -rln "directive" . --exclude-dir=.git
./agents/research/agent.md
./CLAUDE.md
```

The only cross-reference is prose pointing at prose — `agents/research/agent.md`
line 20: "The synthesis step should follow the output format defined in the
directive (summary, key findings, sources, confidence)."

Of the five email guardrails, one has a corresponding line in code, and it is
the optional one:

```
$ grep -n "guardrail\|archive_noise\|delete\|trash" workflows/email_triage.py skills/gmail_label.py
workflows/email_triage.py:29:    archive_noise = config.get("archive_noise", False)
workflows/email_triage.py:62:            should_archive = archive_noise and category == "noise"
```

The four hard "Never" rules hold because no skill calls those Gmail methods —
not because anything checks. In the document they read exactly like the one
that is wired.

## Debugging Rules, quoted in full from CLAUDE.md

```
- When something isn't working, add logging first before changing code. Identify the exact failure point from logs before attempting fixes.
- When running background services (launch agents, daemons), always force unbuffered stdout/stderr so logs actually appear.
- When using third party libraries (PyObjC, etc.), verify the actual API exists before using it. Check with a quick one-liner test in the shell rather than assuming method names from docs or memory.
- When a UI element gets stuck or a callback isn't firing, wrap the entire callback chain in try/except so failures are visible, not silent. Silent exceptions are the most common cause of "stuck" UI.
- Check for duplicate processes before debugging behavior issues.
- When iterating on a fix, don't keep trying variations of the same broken approach. After 2 failed attempts at the same strategy, step back, add more logging, and verify assumptions.
```
