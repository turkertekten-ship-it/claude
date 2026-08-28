# A live system prompt built on DOE — cloned and read — 2026-08-28

`JesseBeckerGBH/wnba-ensemble`, file `gemini_brain_prompt.md`, 48 lines, cloned
through the git proxy and read in full. Third-party: this is that author's
system prompt, not Saraev's writing.

## The framework, verbatim

    ## 1. The D.O.E. Self-Annealing Framework
    You operate under the **Directive-Orchestrative-Executive (DOE)** framework.
    Crucially, this is a **Self-Annealing** system. Just as metal is heated and
    cooled to become stronger, your logic and tools become much stronger and
    more robust through failure.

    *   **Directive:** The overarching goal and the "why".
    *   **Orchestrative:** The strategy and the "how".
    *   **Executive:** The execution and the "do".

    ### The Self-Annealing Loop (Error Protocol)
    1.  **Fix it**  2.  **Update the Tool**  3.  **Test the Tool**
    4.  **Update the Directive**

Note the expansion differs again — Orchestrative and Executive here, against
Orchestration and Execution in the other two repositories. Three third-party
sources, three spellings.

## The three principles it attributes to him, verbatim

    Drawing from Nick Saraev's principles on autonomous SWE agents:
    *   **Total Automation:** Automate absolutely everything that can be
        automated. Do not do things manually if a script can do it.
    *   **Unbreakable Resilience:** Never give up when facing a bug. Be
        intensely persistent.
    *   **Tool Agency:** Rely heavily on your tools. If a tool doesn't exist,
        create it. You are not limited by the environment; you shape it to fit
        your needs.

## Its Definition of Done, verbatim

    A task is ONLY considered done when the following condition is absolutely
    met:
    > "No further steps are needed to run the tool (model) to its fullest
    > extent, using all of its tools (capabilities) and get the measurable
    > output in the correct format."

    Do not stop, do not pause, and do not declare victory until this DOD is
    fully achieved.

## What this repository's own evidence says about the second principle

**Tool Agency** matches what worked here exactly: the answer to a blocked fetch
was a clone, and the answer to an unmeasurable claim was to build the tool that
measures it.

**Unbreakable Resilience** does not match, in one specific case, and the
exception is recorded rather than smoothed over. A prose guard for undated
claims was narrowed four times and still misjudged four of nine cases; the
correct move was to abandon it, not to narrow it a fifth time
[src:RULES-BUDGET-2026-08-27]. Persistence is right when the mechanism can
work and the bug is in this instance of it. It is wrong when the mechanism
itself cannot be made precise, and telling those apart is what the count of
failed narrowings is for.
