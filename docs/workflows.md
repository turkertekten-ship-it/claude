# Workflows and subagents

The doctrine in `CLAUDE.md` is a set of rules. This is how those rules get
executed — the repeatable entry points, and the agents that do the fanning-out.

## Why both

A rule that lives only in a prompt gets skipped under pressure. Each workflow
below pins one phase of the OODA loop to a command, so the phase either ran or
it did not — and each ends by running the verifier, so a workflow cannot report
success over an unsourced claim.

Subagents exist for a narrower reason: **separation of phase**. An agent that
only enumerates cannot talk itself into a conclusion, and an agent auditing a
document it did not write has no stake in the claims holding up. Splitting
those roles out is what stops Observe collapsing into Orient.

## Workflows

Invoke as slash commands. Definitions in `.claude/commands/`.

| Command | Phase | What it produces |
|---|---|---|
| `/observe <target>` | Observe | a sourced inventory, including explicit absences |
| `/ooda-loop <task>` | all four | evidence, a named surprise, a falsifiable decision, a verified result |
| `/fact-check [path]` | audit | the specific unsupported lines, and their fixes |
| `/source <finding>` | capture | a well-formed ledger entry a claim can cite |
| `/fleet-sync` | Observe | what the other sessions have actually pushed, read from diffs |
| `/ingest-chats [query]` | Observe | the real contents of the chat index, or the fact that it is empty |
| `/verify-loop <task>` | Decide | the check a task must pass, built and watched failing, wired as a gate |

## Subagents

Definitions in `.claude/agents/`.

**`observer`** — enumerates and stops. It is told not to interpret, and its
output format has no place to put a conclusion. Use it for breadth: sweeping a
repository, an environment, or a dataset when you need the inventory rather
than the reading.

**`fact-checker`** — audits a document against `provenance/sources.yaml` and
reports the lines that outrun their evidence. It catches what the verifier
structurally cannot: whether a tag that *resolves* actually supports the
specific claim attached to it.

**`verifier`** — runs the checks on work it did not do, and is given no tool
that can edit what it judges. Where `fact-checker` audits documents, `verifier`
audits behaviour: it locates the check, runs it itself rather than trusting
reported output, and asks separately whether the check actually covers the
claim. It is told that "I ran the checks, they pass, and they cover the claim"
is a complete answer, because a reviewer asked to find gaps will otherwise
manufacture them.

## How they fit together

```
/ooda-loop
   |
   Observe  -> observer subagent (breadth) -> verify the load-bearing parts yourself
   |            captures land in provenance/sources.yaml + raw/
   Orient   -> grade every claim: verified | second-hand | unknown
   |            name the surprise
   Decide   -> one decision, plus what would falsify it
   |
   Act      -> do it, capture the result
   |
   /fact-check -> fact-checker subagent, before anything is published
   |
   /verify-loop -> verifier subagent, before anything is called done
   |
   bash tests/run_all.sh
```

## The rule that survives delegation

**A subagent's report is second-hand.** It is another process's claim about
what it saw, exactly like another session's status line. Verify anything
load-bearing yourself before writing it down as fact, and when you do cite an
agent's finding, name it as the reporter.

Delegation multiplies reach. It does not multiply evidence.
