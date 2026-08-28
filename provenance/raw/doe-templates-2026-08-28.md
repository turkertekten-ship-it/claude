# Directive and learnings templates — cloned and read — 2026-08-28

`Vibe-Marketer/Agentic-Workflows-Template`, cloned through the git proxy. Its
README states: "Based on Nick Saraev's DOE framework. Refined for clarity and
self-improvement." Reading the repository establishes what its author wrote,
not what Saraev said; his own pages remain unreachable.

Two files are prompt-relevant and were not visible through the fetch tool's
summary of the README.

## 1. `directives/_TEMPLATE.md` — the directive format, with a rule about growth

The required part is short: Goal, Trigger Phrases, Quick Start, What It Does
(numbered steps), Output (Deliverable and Location). Then, verbatim:

    <!-- ═══════════════════════════════════════════════════════════════════
         EVERYTHING BELOW IS OPTIONAL
         Add sections as you discover edge cases, not upfront
         ═══════════════════════════════════════════════════════════════════ -->

Optional sections that follow include Prerequisites (API keys, dependencies).

It also carries a version tag shared with its script:

    <!-- DOE-VERSION: 2025.12.17-a -->

and `REFERENCE.md` states: "The agent MUST check version alignment before
execution. Mismatches indicate drift and require review."

## 2. `learnings/_TEMPLATE.md` — a register of what was tried and rejected

Verbatim opening:

    This document captures approaches that were tested but not selected, and
    why. Prevents re-discovering dead ends.

Its structure: a Current Implementation section naming the winning approach, the
directive it lives in and why it won; then Tested Alternatives, each with a name,
a `Tested:` date, and a `Result:` of Failed, Partial Success, or "Works but not
selected", followed by what the approach was.

## Why these two matter here

The first states, as a rule about writing a directive, the thing this
repository's linter learned by breaking it: sections are added when an edge case
forces one, not upfront. The formulation is sharper than the one in
`docs/prompting.md`, which says only to fill a slot where it changes the answer.

The second names an artifact this repository does not have. `learn_rule` records
rules; nothing records an approach that was tried and rejected. This session has
already produced two — a prose-matching guard backed out in loop seventeen, and
a keyword harvest of the loop log that proved unreliable in loop twenty-three —
and both survive only as paragraphs in a loop log.
