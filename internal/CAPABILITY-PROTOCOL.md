# Capability protocol

> Probe before you plan. Degrade on purpose. Record what you learned.

This is the operating doctrine for any agent or pipeline working in this repo.
It exists because the most expensive failures in this project were not bugs in
logic - they were **assumptions about access** that turned out to be false, and
were only discovered halfway through work that then had to be redone.

## The three rules

### 1. Probe before you plan

Never write a plan whose first step is "fetch X" without first establishing that
X is reachable *from the place the code will run*. A blocked host discovered at
minute 40 invalidates the design; discovered at minute 2, it *is* the design
input.

Run `ooda preflight` (or `oodarag.access.probe.probe_all`) at the start of a
session and at the start of every OODA cycle. The result is data, not a message:
it is journalled, and `Decide` reads it.

### 2. Egress is per-path, not per-environment

**The single most important thing learned in this repo.** "Can I reach the
internet" is not one question. In this environment there are at least three
distinct egress paths with *different* policies:

| Path | Reaches | Blocked |
|---|---|---|
| Container HTTP (`curl`, `urllib`, the pipeline itself) | api.github.com, raw.githubusercontent.com, pypi.org | youtube.com, ibm.com, wikipedia.org, arxiv.org |
| Agent web search | Public web including YouTube, IBM, arXiv | - |
| Agent web fetch | Some hosts | ibm.com and others, by egress policy |

A capability being unavailable on one path says nothing about the others. When
the pipeline cannot reach a source, that does not mean the *research* cannot be
done - it means the research and the ingestion use different routes, and the
pipeline needs an offline hand-off (a manifest, a cached corpus) between them.

Corollary: never report "I cannot access X" until X has been tried on every path
available. And never assume a path works because a sibling path did.

### 3. Degrade explicitly, never silently

Every blocked capability maps to a named fallback that is written down before it
is needed (`AccessReport.degradations()`). A pipeline that quietly indexes three
of seven sources and answers confidently from the fragment is worse than one
that refuses, because nothing in its output reveals the gap.

Rules:
- A blocked source is recorded in the index metadata, not just in a log line.
- An answer built from a partial corpus says which sources were live.
- A silent empty result is always a bug. Empty must be *explained*: blocked,
  filtered, deduped, or genuinely absent.

## Escalation ladder

When a needed capability is unavailable, work down this ladder before reporting
a blocker. Stop at the first rung that works, and record which rung you used.

1. **Retry correctly.** Is it actually a hard failure? Rate limits, 403s that
   mean "slow down", and 5xx are transient. (GitHub signals rate limiting with
   *403*, not 429 - see ADR 0003.)
2. **Different endpoint, same source.** The REST API is blocked but raw content
   is not; the HTML page is blocked but the JSON API is not; the site is blocked
   but its sitemap or an official mirror is not.
3. **Different egress path.** Search instead of fetch. A tool the harness
   provides instead of the container's socket.
4. **Different authority.** Local git instead of the GitHub API. A checkout
   instead of a download.
5. **Offline hand-off.** Capture what the reachable path can see into a manifest
   or corpus file committed to the repo, so the pipeline can consume it later
   without the blocked path.
6. **Report, with evidence.** Name the exact probe, the exact status, and the
   rungs already tried. "Blocked" without evidence is not a finding.

## Verification standard

A capability is "available" only when it has been exercised end to end and the
outcome checked against something that could have disagreed.

- Prefer **observed ground truth** over self-reported success. The crawler
  proves it obeyed robots.txt by the web server's own request log showing the
  URL was never requested - not by a counter the crawler itself incremented.
- Prefer **differential checks** over golden files. Two independent readers of
  the same source must agree: the GitHub connector's bytes are checked against
  `git cat-file` on a local clone.
- A test whose expected values were copied from a previous run of the code under
  test proves only that the code still does what it did. Derive expectations, or
  observe them from a party with no stake in the outcome.
- Assert that each failure path actually fired. A dedupe rule that never
  triggered in the test suite is untested, not correct.

## Recording learnings

Anything learned about the environment goes into a file, not just into a reply:

- Environment facts -> `internal/ACCESS.md` (regenerate with `ooda preflight`).
- Durable behavioural rules -> this file.
- Decisions with trade-offs -> `docs/adr/`.
- Surprises that cost time -> `internal/LEARNINGS.md`, with the evidence.

If a lesson is not written down, it will be paid for again in the next session.
