---
name: preflight
description: Probe what this environment can actually reach before planning any work that depends on network, GitHub or the filesystem - and map each blocked capability to its named fallback. Use at the start of a session, before adding or enabling a source, when a crawl or connector returns nothing, when a fetch fails with 403 / proxy CONNECT refused / tunnel errors, or whenever the answer to "can I reach X?" would change the plan. Not for retrieval-quality questions (use eval-gate).
---

# Preflight: probe before you plan

Doctrine: `internal/CAPABILITY-PROTOCOL.md`. It is not a suggestion. The most
expensive failures in this repo were not logic bugs, they were **assumptions
about access** discovered at minute 40 instead of minute 2.

## Run it

```bash
cd /home/user/claude && PYTHONPATH=src python3 -m oodarag.cli preflight
```

Takes ~2s. Read-only: it opens no index and writes nothing unless you pass
`--out`.

Useful variants:

```bash
PYTHONPATH=src python3 -m oodarag.cli preflight --json          # machine-readable
PYTHONPATH=src python3 -m oodarag.cli preflight --strict        # exit 1 if anything is blocked
PYTHONPATH=src python3 -m oodarag.cli preflight --out internal/ACCESS.md
PYTHONPATH=src python3 -m oodarag.cli preflight --repo owner/repo   # probe extra repo scope
```

`--out internal/ACCESS.md` is how the environment record is regenerated. Only
write it when the user asked for it — it is a tracked file.

## Reading the report

Four sections. Read them bottom-up.

1. **Summary** — `N blocked, M ok`.
2. **Environment** — `github_token`, `anthropic_key`, `voyage_key`, `numpy`,
   `https_proxy`. `anthropic_key: absent` is normal and not a failure: the
   generator falls back from Claude to `extractive`, and every answer stays
   grounded and cited. `numpy: absent` means pure-Python scoring — slower, same
   numbers.
3. **Probes table** — per capability: `ok` / `degraded` / `blocked` /
   `unauthorized` / `unreachable`, with latency and evidence (rate-limit
   budget, byte counts, HTTP status).
4. **Required degradations** — the only section that is actionable. Each
   blocked capability maps to a *named* fallback. Quote it into your plan.

Baseline observed in this container (2026-08-28): **4 blocked, 6 ok**.
`github_api`, `github_raw`, `github_repo_scope`, `filesystem_write`, `pypi` and
`web_pypi` were ok; `web_wikipedia`, `web_youtube`, `web_ibm` and `web_arxiv`
were blocked with `proxy refused CONNECT (403)`. If your run matches, nothing
has changed and you can plan against it. If it does not, the environment moved
and the plan must move with it.

## The named fallbacks

Do not invent your own. These are the ones `AccessReport.degradations()` emits
and the pipeline is built around:

| Blocked | Named fallback |
|---|---|
| `github_api` | `LocalGitConnector` over an existing checkout. Repo metadata, issues and PRs will be missing — say so. |
| `github_raw` (API still ok) | File bodies come from the REST blob endpoint, which costs API quota. Lower `max_files`. |
| Every `web` probe | The web connector cannot contribute at all. Use offline corpora only and mark web-sourced answers *unavailable*, not stale. |
| Some `web` probes | Seed the crawler **only** with reachable hosts. A blocked seed is a silent empty crawl. |
| `pypi` | No optional accelerators. The stdlib path is the only path — which is why it is the default. |
| `filesystem_write` | The SQLite index cannot be persisted. Run in memory, treat the index as ephemeral. |

A blocked host is not a reason to stop. It is a reason to route differently and
to say in the output which route was used.

## Egress is per-path, not per-environment

The single most important thing learned in this repo. "Can I reach the
internet" is not one question — these are separate routes with separate
policies:

| Path | Typically reaches | Typically blocked |
|---|---|---|
| Container HTTP (`urllib`, `curl`, the pipeline itself) | api.github.com, raw.githubusercontent.com, pypi.org | youtube.com, ibm.com, wikipedia.org, arxiv.org |
| Agent web search | public web, including the hosts above | — |
| Agent web fetch | some hosts | ibm.com and others, by policy |

So when the pipeline cannot reach a source, the *research* may still be
possible — over a different route, with an offline hand-off (a manifest or
cached corpus committed to the repo) between the route that can see it and the
pipeline that cannot. `corpus/ibm-technology/manifest.json` exists for exactly
this reason.

Never report "I cannot access X" until X has been tried on every available
path, and never assume one path works because a sibling did.

## Escalation ladder

Work down it before declaring a blocker. Stop at the first rung that works and
**record which rung you used**.

1. **Retry correctly.** Is it actually hard? Rate limits, 5xx and some 403s are
   transient. GitHub signals rate limiting with **403, not 429** (ADR 0003).
2. **Different endpoint, same source.** REST blocked but raw open; HTML blocked
   but JSON open; site blocked but sitemap or an official mirror open.
3. **Different egress path.** Search instead of fetch; a harness tool instead of
   the container socket.
4. **Different authority.** Local git instead of the GitHub API; a checkout
   instead of a download.
5. **Offline hand-off.** Capture what the reachable path can see into a
   manifest or corpus file in the repo, so the pipeline consumes it later
   without the blocked path.
6. **Report, with evidence.** Name the exact probe, the exact status, and the
   rungs already tried. "Blocked" without evidence is not a finding.

## Distinguishing permanent from transient

`proxy refused CONNECT (403)` is a **policy denial**. It will not pass on
retry, and retrying it burns wall-clock: a single blocked host costs ~25s of
backoff in an index run before the HTTP client's circuit breaker opens it
(`circuit opened; host treated as unreachable ... cooldown_s=300`). Detect it
once, take the fallback, stop paying for it. Contrast with a 5xx or a rate
limit, where retry is the correct move.

## After the probe

- Blocked capability that the plan depends on → change the plan now, and say in
  the plan which rung of the ladder you took.
- Blocked capability the plan does not depend on → note it and move on.
- Enabling a `[[source]]` → probe its host **first**; see the `add-source` skill.
- Environment fact that surprised you and cost time → it belongs in
  `internal/LEARNINGS.md` with its evidence, not only in your reply.
