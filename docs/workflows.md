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

## Skills

Skills differ from commands in when they load. A command runs because someone
typed it; a skill loads because its `description` matched the situation. So a
skill is the right home for a procedure that should apply *whether or not
anyone remembers to invoke it*.

| Skill | Loads when |
|---|---|
| `ooda` | a request rests on facts that have not been checked |
| `researching-before-acting` | a task needs the ground established first, or a source looks unreachable |

`researching-before-acting` is the wider procedure: research from every
reachable source before starting, route the findings through the loop, and
treat an open item as a reason to continue rather than a reason to caveat. It
also carries the barrier taxonomy — the distinction between a host refused at
the network layer and one that answered and asked for a credential — because
collapsing those is the most common way a usable source gets written off.

**Skills must be committed here to exist in a cloud session.**
[src:SKILL-LOAD-PATHS-2026-08-27] A skill in a personal `~/.claude/skills/` is
invisible to every session that clones this repository, which is all of them.
That is why both skills live in `.claude/skills/` under version control.

Run `make skills` to discover and lint every SKILL.md reachable from here. The
lint separates what the runtime rejects — a `name` outside its character set or
length, a reserved word, a missing description — from what is only guidance,
because a skill that cannot load and a skill that is merely verbose are
different problems.

## Tooling the workflows call

| Command | Answers |
|---|---|
| `make reachability` | what this container can fetch, and which barrier stops the rest |
| `make skills` | which skills exist, and which could never trigger |
| `make test` | every unit test, both doctrine suites, and the provenance verifier |
| `make demo` | the whole pipeline end to end, with no network and no credentials |
| `python3 -m oodarag.cli loop --cycles 1` | one OODA cycle over the corpus, with all four artifacts |

The last one is the loop as code rather than as procedure: it observes the
index, orients on what that means, states a decision with its falsifier, acts,
and reports all four. It is the same discipline `/ooda-loop` applies to a task,
applied to a corpus.

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
   bash tests/run_all.sh
```

## The rule that survives delegation

**A subagent's report is second-hand.** It is another process's claim about
what it saw, exactly like another session's status line. Verify anything
load-bearing yourself before writing it down as fact, and when you do cite an
agent's finding, name it as the reporter.

Delegation multiplies reach. It does not multiply evidence.
