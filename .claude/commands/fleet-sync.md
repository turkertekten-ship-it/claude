---
description: Check what the other concurrent sessions have actually pushed, read their diffs, and refresh FLEET.md.
allowed-tools: Bash, Read, Grep, Glob, Agent
---

Find out what the rest of the fleet has actually done — not what it is called.

1. Refresh the roster from the live source, not from `FLEET.md`:
   `mcp__Claude_Code_Remote__list_sessions` with `mine: true`.
2. `git fetch --all --prune` in each repository, then list remote branches with
   their last commit time.
3. For every branch that is not yours and has commits, **read the diff**. A
   branch you have not read is unread work, whatever its name promises.
4. Update `FLEET.md`: the roster, and an `## Observed` line per session with a
   `[src:ID]` tag, plus the matching ledger entry.
5. Flag any file that two branches have both touched. At this concurrency,
   silent clobbering is the likeliest failure mode.

Two rules for the write-up:

- A session title is a generated label. It establishes that the label exists,
  nothing more. Never expand one into a description of the work.
- A session's own status summary is its claim about itself. Record it as
  second-hand with the reporter named, or verify it from the diff.

If a repository holds no branch but your own, or the roster tool is not
available in this session, say exactly that and stop. An empty fleet is a
finding, and a roster reconstructed from memory is the failure this command
exists to prevent.

Finish with `python3 tools/verify_provenance.py`. The sync is done when the
verifier exits 0 and every session line in `FLEET.md` carries a tag that
resolves.
