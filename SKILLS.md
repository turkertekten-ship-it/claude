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

## Adding one

Vendor it, do not link it — a skill that changes upstream underneath you is a
skill you have not read. Record the upstream commit in
`provenance/sources.yaml`, keep the licence file, note any local modification
inside the skill itself, add a row to both tables above, and run
`bash tests/run_all.sh`.
