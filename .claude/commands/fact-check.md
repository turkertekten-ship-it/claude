---
description: Audit a document, diff, or write-up for claims that outrun the evidence behind them.
argument-hint: [path or "the working tree diff"]
allowed-tools: Bash, Read, Grep, Glob, Agent
---

Audit this for unsupported claims: **$ARGUMENTS** (default: `git diff HEAD` plus
every Markdown file changed on this branch).

1. Run `python3 tools/verify_provenance.py` on the target. That is the
   mechanical floor — it catches unresolved tags and unsourced lines in
   enforced files, and nothing else.
2. Dispatch the `fact-checker` subagent over the same target for the judgement
   pass the verifier cannot do: whether a cited source actually supports the
   specific claim made, and whether anything second-hand has been written up as
   verified.
3. Pay particular attention to:
   - a name or title expanded into content
   - a plan or intention reported as a completed action
   - counts, dates, and quantities with no capture behind them
   - hedges standing in for evidence
4. For each finding, take the cheapest honest fix: get a source, downgrade the
   claim and name the reporter, or move it to `provenance/unknowns.md`.

Report what you changed. If nothing was unsupported, say so plainly — do not
manufacture findings to look thorough, which is the same failure you are
auditing for.
