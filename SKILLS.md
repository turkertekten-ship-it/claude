---
provenance: enforced
---

# Skills — what is installed, what it is for, and what was turned down

A skill is only useful if something routes to it. This file is that routing
layer: what is in `.claude/skills/`, which task hands off to which skill, and —
just as load-bearing — which well-reviewed skills were examined and **not**
installed, with the reason recorded so the question is not reopened blind.

Read [CLAUDE.md](CLAUDE.md) first. The rule there applies here: a claim about
what a skill does is sourced, or it is an open question.

## Observed — where these came from

- Anthropic's public skills repository holds exactly 19 skills at commit `3b3fad9`; `mcp-builder` ships a 4-file `reference/` directory and an `evaluation.py`, and `doc-coauthoring` is a single `SKILL.md`. [src:SKILLS-ANTHROPIC-2026-08-27]
- `floflo777/claude-rag-skills` at commit `d74f066` holds four skills under an MIT licence held by Ailog, and none of the four SKILL.md files carries YAML front matter, so Claude Code cannot index them as written. [src:SKILLS-AILOG-2026-08-27]
- A search of this account's own claude.ai skill library for RAG, ingestion, provenance and OODA terms returned nothing; the plugin catalogue returned ten plugins, all disabled, of which the relevant ones are commercial and need a vendor API key. [src:PLUGIN-CATALOG-2026-08-27]
- The container reaches `www.googleapis.com`, `github.com`, `api.github.com`, `raw.githubusercontent.com`, `pypi.org`, `files.pythonhosted.org`, `registry.npmjs.org` and `api.anthropic.com`; it does not reach `www.youtube.com`, `i.ytimg.com`, `huggingface.co`, `arxiv.org` or either IBM host. [src:EGRESS-2026-08-27]

## Installed

| Skill | Source | Routes from |
|---|---|---|
| [`ooda`](.claude/skills/ooda/SKILL.md) | this repository | Any task resting on facts not yet checked. The entry point. |
| [`mcp-builder`](.claude/skills/mcp-builder/SKILL.md) | `anthropics/skills@3b3fad9` | Exposing `oodarag` retrieval as an MCP server so sibling sessions can query the index instead of rebuilding it. |
| [`doc-coauthoring`](.claude/skills/doc-coauthoring/SKILL.md) | `anthropics/skills@3b3fad9` | Structured long-form documents — the ADRs under `docs/adr/`, and the sectioned installation guide a sibling session is writing. |
| [`rag-audit`](.claude/skills/rag-audit/SKILL.md) | `floflo777/claude-rag-skills@d74f066` (MIT, Ailog) | Reviewing `src/oodarag/` retrieval code against known anti-patterns before a stage is called done. |
| [`chunking-advisor`](.claude/skills/chunking-advisor/SKILL.md) | `floflo777/claude-rag-skills@d74f066` (MIT, Ailog) | Choosing chunk size, overlap and split boundary per document type during ingest design. |

Both Ailog skills were modified on the way in: front matter added so they
index at all, and a vendor-steer note appended. Each says so at its own
foot. The bodies are otherwise upstream's.

## Built by the fleet — routable, deliberately not merged here

Other sessions wrote skills that exist nowhere else. Each was read first-hand
at the commit named; none was inferred from its name. [src:FLEET-SKILLS-2026-08-27]

| Skill | Branch @ commit | What it actually does |
|---|---|---|
| `cherny` (+ `verifier` agent, `/verify-loop`) | `great-euler-6tx6y6@5c27418` | The Boris Cherny practice set, over a sourced corpus in `docs/cherny-practice.md`. Its rule: give Claude a way to verify the work before giving it the work. |
| `prompt-forge` (+ `prompt-critic`, `/prompt`, `/prompt-audit`) | `session-y42cyg@8b59cd6` | A seven-slot prompt specification with a linter and an adversarial reading pass — treats a bad result as a specification failure, not a model failure. |
| `workbench` (+ `blind-judge`, `/ab`, `/wb-doctor`) | `code-playground-parity-xw0snj@2794c4a` | Blind pairwise comparison of prompt or config variants, with significance. Ships a 10-module Python package, so it does not travel as a lone `SKILL.md`. |
| `/ultrareview` | `reverse-engineer-chat-setup-husv9h@abed75a` | The closing gate: re-verify provenance, tests and the diff before work is called finished. |

**Why they are listed rather than merged.** All four descend from the doctrine
root, so they *can* be merged [src:FLEET-BRANCHES-2026-08-27] — a trial merge
of one was run and then abandoned. It conflicted on seven files, and in the
merged unknowns register two different questions both claimed the id `U-7`
[src:LEDGER-ID-COLLISION-2026-08-27]. Merging ledgers that disagree about what
an id means produces exactly the failure `CLAUDE.md` names: two copies of a
rule set becoming two different rule sets. Which branch becomes the integration
branch is the owner's call, not a session's.

> Framing, not a claim: the practical effect is that `cherny`, `prompt-forge`
> and `workbench` are each usable only by the session that wrote them until
> someone decides where they land.

**Unknown ids need a shared allocator.** They are handed out per branch with no
common counter, so any two sessions opening a question at the same time collide
[src:LEDGER-ID-COLLISION-2026-08-27]. Prefixing by branch (`U-dxmflq-1`) or by
timestamp would remove the class of problem entirely.

## Routing table

Match the work in hand to the left column.

| When you are… | Use | Because |
|---|---|---|
| starting anything in an unfamiliar repo, or the request assumes something exists | `ooda` | Most fabrication is Orient running on an empty Observe. |
| deciding how to split a corpus into chunks | `chunking-advisor` | Addresses the "chunks lose context" failure mode named in `README.md`. |
| reviewing retrieval code before calling a stage done | `rag-audit` | Reads the code that is present rather than the design that was intended. |
| giving another session programmatic access to the index | `mcp-builder` | Sibling sessions run in separate containers and cannot read each other. |
| ingesting a contract or deal document | `chunking-advisor`, Legal/Contracts branch | The owner's own corpus is a numbered transaction set; clauses are the unit of meaning, not sections. See [docs/design/chunking.md](docs/design/chunking.md). |
| writing an ADR, a spec, or a sectioned guide | `doc-coauthoring` | Structured co-authoring rather than a wall of generated prose. |
| setting up how a task will be worked, or about to trust unchecked output | `cherny` *(fleet)* | Builds the check before the work, so "it looks done" stops being the completion signal. |
| writing or rewriting any prompt, or briefing a subagent | `prompt-forge` *(fleet)* | Most disappointing output is a specification failure; this makes the gaps visible instead of guessed. |
| claiming one prompt or config is better than another | `workbench` *(fleet)* | You wrote the new one, so of course it reads better. Measure it blind. |
| calling a branch finished | `/ultrareview` *(fleet)* | A review that only reads the code has not checked the claims. |
| about to write a claim you have not checked | `/fact-check`, then `unknowns.md` | The claim is not ready to be written down. |
| wondering what this container can reach | `tools/probe_egress.py` | Measured in seconds; guessed at for hours. |

## Examined and turned down

Recording a rejection is worth as much as recording an install: it stops the
same candidate being re-evaluated from its name every time someone sees it.

| Candidate | Why not |
|---|---|
| `discernment-nudge` (`anthropics/skills`) | Its own "When not to" section excludes code the user will run, and excludes users who already asked for verification and sourcing. Both describe the standing instructions here, so it would self-suppress on nearly every turn. [src:DISCERNMENT-REJECTED-2026-08-27] |
| `rag-scaffold` (Ailog) | Leads with LangChain and LlamaIndex and offers a hosted "RAG-as-a-Service" option. [src:SKILLS-AILOG-2026-08-27] Generating a dependency-heavy scaffold contradicts design principle 1 in `README.md`, and `src/oodarag/` is already past the scaffold stage. |
| `rag-eval` (Ailog) | Its Mode 2 benchmarks against the vendor's own API and needs an Ailog key. [src:SKILLS-AILOG-2026-08-27] Mode 1 measures what `README.md` already commits to measuring — recall@k, MRR, nDCG, citation coverage — so adopting it would mean two eval harnesses disagreeing. |
| `tavily`, `brightdata-plugin` | Both are disabled, commercial, and require a vendor API key that is not present here. [src:PLUGIN-CATALOG-2026-08-27] Bright Data does advertise YouTube extraction, which is the live blocker — but the YouTube Data API is already reachable from this container and costs nothing to try first. [src:YOUTUBE-API-REACHABLE-2026-08-27] Revisit only if a key exists and the API path has been tried and failed. |
| design and artifact skills (`canvas-design`, `theme-factory`, `brand-guidelines`, `frontend-design`, `algorithmic-art`, `slack-gif-creator`, `web-artifacts-builder`) | No visual surface in either repository. [src:SKILLS-ANTHROPIC-2026-08-27] |
| `docx`, `pdf`, `pptx`, `xlsx`, `skill-creator`, `claude-api` | Already available in this environment; vendoring a second copy creates two versions to keep in step. |

## Where these are installed, and what that reaches

Committing a skill to `.claude/skills/` here reaches sessions opened **in this
repository** and nothing else. The owner's most-repeated request is the
opposite of that — a sibling session derived it from the goal corpus as P4,
"all prompts, all chats, all terminals", graded Strong from four independent
goals [src:OWNER-PROFILE-SIBLING-2026-08-27].

So the four vendored skills are also installed at user scope:

```bash
python3 tools/install_skills_user_scope.py            # show the plan
python3 tools/install_skills_user_scope.py --apply    # install into ~/.claude/skills/
```

They were installed and confirmed indexed — all four appeared as invocable
skills in the session's own listing, not merely as files on disk.
[src:USER-SCOPE-INSTALL-2026-08-27] `ooda` is deliberately excluded: it belongs
to the doctrine, which `tools/install_user_scope.py` on
`reverse-engineer-chat-setup-husv9h` installs instead. The two installers are
complementary and neither replaces the other.

**What that does not reach**, stated rather than implied
[src:USER-SCOPE-INSTALL-2026-08-27]:

- **claude.ai web conversations.** They do not read `~/.claude/`. No script
  changes that; a skill needed there has to be pasted into a Project's custom
  instructions by hand.
- **The next container.** `~/.claude` is not persistent, so a fresh session
  starts without these. That is why this ships as a committed script rather
  than as a one-time action — running it is a step, not a memory.

## Adding one

Vendor it, do not link it — a skill that changes upstream underneath you is a
skill you have not read. Record the upstream commit in
`provenance/sources.yaml`, keep the licence file, note any local modification
inside the skill itself, add a row to both tables above, and run
`bash tests/run_all.sh`.
