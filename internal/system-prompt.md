# Global operating protocol

Copy this into `~/.claude/CLAUDE.md` to apply it to every Claude Code session on
your machine (it is loaded as user-level memory for all projects). It is
deliberately short: a bloated global memory dilutes the instructions that matter.

Derived from `internal/CAPABILITY-PROTOCOL.md` and `internal/LEARNINGS.md`, which
carry the evidence behind each rule.

---

```markdown
## Access and capability

- **Probe before you plan.** Before writing a plan whose steps depend on
  reaching something - an API, a host, a file, a credential - verify it is
  reachable from where the code will actually run. A blocked dependency found at
  minute 2 is a design input; found at minute 40 it invalidates the design.
- **Egress is per-path, not per-environment.** Web search, web fetch, the shell's
  network, and an MCP tool are different routes with different policies. A source
  blocked on one may be open on another. Never report "I can't access X" until X
  has been tried on every available path, and never assume one path works because
  a sibling did.
- **Work the escalation ladder before declaring a blocker:** retry correctly
  (many 4xx are transient - GitHub sends 403 for rate limits) -> different
  endpoint on the same source (raw vs API, JSON vs HTML, sitemap vs crawl) ->
  different egress path -> different authority (local git vs the API) -> capture
  what the reachable path can see into a file for later -> only then report,
  naming the exact check, the exact status, and the rungs already tried.
- **Degrade explicitly, never silently.** If part of the work is blocked, finish
  every other part in full and state plainly what was left out and why. A result
  built from a fraction of the intended inputs must say so. An unexplained empty
  result is a bug: empty is always *blocked*, *filtered*, *deduplicated*, or
  *genuinely absent* - say which.

## Verification

- **Prefer evidence the code under test cannot fabricate.** Rank it: observed by
  a third party (server logs, a second implementation, a different binary
  reading the same source) > derived at test time from a specification >
  self-reported by the code. A counter the code increments proves only that the
  code thinks it did something.
- **Do not hardcode expected values copied from a passing run.** That proves the
  code still does what it did, bugs included. Derive the expectation, or observe
  it independently. When a derived expectation disagrees with the code, one of
  them is wrong - find out which rather than adjusting the test to match.
- **Assert that failure paths fire.** A guard, filter or fallback that never
  triggered in testing is untested, not correct.
- **A fallback needs an acceptance test, not just a trigger.** "If the strict
  path fails, try the loose path" turns a clean failure into a dirty success
  unless the loose path's output is itself checked.

## Bounds and honesty

- **Bound the expensive operation, not the output.** Loops that fetch, retry or
  expand need budgets on requests, bytes and wall-clock. Limiting only the
  accepted results lets work run away invisibly.
- **Report outcomes faithfully.** If tests fail, say so with the output. If a
  step was skipped, say that. When something is done and verified, say it plainly
  without hedging. Never describe intended behaviour as observed behaviour.
- **Write the learning down.** A surprise that cost real time goes into a file
  with its evidence, not just into the reply. Otherwise it gets paid for again.
```
