# WebFetch captures — the DOE framework attributed to Nick Saraev

Fetched by the main session at approximately 2026-08-27T16:05Z. These hosts
were reachable when every other external host was refused: `raw.githubusercontent.com`
answered, `nicksaraev.com` and `youtube.com` did not
(see `egress-2026-08-27T15-20Z.md`).

**What these are.** Third-party repositories that document, implement, or index
a framework they attribute to Nick Saraev. Reading them establishes what those
authors wrote. It does not establish what Saraev said: none of them is his
property, and his own pages could not be reached.

---

## 1. Pvragon/ai-workspace-reference — team-lib/context/indexed/nick-saraev-doe-framework.md

URL: https://raw.githubusercontent.com/Pvragon/ai-workspace-reference/762e7476aa128f02b7d8fd100b034e0a7001ca59/team-lib/context/indexed/nick-saraev-doe-framework.md

Returned content, as reproduced by the fetch tool:

    # DOE Framework Reference: Core Content

    ## The Three Layers

    **Layer 1: Directive** - "The What"
    High-level natural language Markdown instructions stored in `/directives` folder,
    specifying goal, inputs, process steps, tools, edge cases, success criteria, and guardrails.

    **Layer 2: Orchestration** - "The Who / When"
    The AI agent itself (not a file), executing the PTMRO Loop: Planning, Tools, Memory,
    Reflection, Orchestration. It reads directives, selects actions, invokes scripts,
    and evaluates results.

    **Layer 3: Execution** - "The How"
    Deterministic Python scripts in `/execution` folder that perform actual work with
    guaranteed consistency. Scripts feature single responsibility, standard I/O,
    error handling, logging, and API encapsulation.

    ## Core Problem Statement

    "You cannot run a million dollar a month operation on a system that only works most
    of the time." Error compounding demonstrates this: at 90% per-step success over five
    steps yields 59% overall success rate (0.9^5 = 0.59).

    ## Key Sources

    | Title | URL | Date |
    | the n8n killer? AGENTIC WORKFLOWS: Full Beginner's Guide | https://www.youtube.com/watch?v=bA-WmidVSGo | 2025-11-25 |
    | DON'T build AI automations, build agentic workflows! (Google Antigravity) | https://www.youtube.com/watch?v=MxyRjL7NG18 | 2026-01-08 |
    | Agents vs Workflows - Pick the Right Tool or Pay the Price | https://www.youtube.com/watch?v=5rNu19PfgFg | [undated] |

    ## Self-Annealing Process

    When errors occur: Catch -> Read -> Diagnose -> Fix -> Rewrite -> Retry.
    "These systems are anti-fragile - they benefit from shocks rather than breaking under them."

The quoted sentences inside that file are presented by its author as quotations
from the videos listed. The videos themselves were not reachable, so the
quotations were not checked against them.

---

## 2. Vibe-Marketer/Agentic-Workflows-Template — README.md

URL: https://raw.githubusercontent.com/Vibe-Marketer/Agentic-Workflows-Template/main/README.md

Attribution line, verbatim:

    "Based on Nick Saraev's DOE framework. Refined for clarity and self-improvement."

Structure described:

    1. Directives   - Plain English instructions stored in `directives/*.md`
    2. Orchestration - AI makes decisions about which workflow to use
    3. Execution     - Python scripts in `execution/*.py` perform the actual work

---

## 3. datacraftdevelopment/ClaudeAgent_v3 — README.md

URL: https://raw.githubusercontent.com/datacraftdevelopment/ClaudeAgent_v3/main/README.md

Structure described:

    **Layer 1: Directives** - Markdown SOPs describing what should happen
    **Layer 2: Orchestration** - Claude reads directives, makes decisions, handles errors
    **Layer 3: Execution** - Deterministic Python scripts perform the actual work

Stated rationale:

    "Visual tools struggle with custom logic and debugging complex workflows, while
    LLMs hallucinate endpoints and compound errors across multiple steps. By separating
    concerns - Claude handles orchestration, Python handles deterministic work - the
    system achieves reliability without sacrificing flexibility."

This README does not name Saraev in the text returned by the fetch. The
attribution to him for this repository comes from a separate line quoted by a
research subagent, which was not independently confirmed here.

---

## What three independent repositories agree on

The same three layers, in the same order, with the same division of labour:
natural-language directives, an LLM orchestrator, deterministic scripts. Two of
the three name Saraev. That convergence makes the framework's existence and
shape well attested among third parties; it leaves the attribution itself
resting on their word.
