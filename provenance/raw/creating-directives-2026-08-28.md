# `docs/creating_directives.md` — cloned and read — 2026-08-28

`datacraftdevelopment/ClaudeAgent_v3`, cloned through the git proxy. A
third-party implementation whose README describes the same three layers as the
DOE material; the file below is that author's guidance on writing a directive.
Read first-hand. Not Saraev's words.

## Its central claim, verbatim

    You don't write directives manually. You have a conversation with Claude
    Code and let it build everything for you.

## The context the author is asked to supply, verbatim table

    | Context Type | Example |
    | **Goal**        | "I want to convert PDFs to markdown for RAG" |
    | **Examples**    | Paste sample inputs/outputs |
    | **Past work**   | "I've done this before using PyMuPDF" |
    | **Edge cases**  | "Some PDFs are scanned images, need OCR" |
    | **Constraints** | "Must run in under 5 minutes" |
    | **Preferences** | "Output to Google Sheets, not local files" |

## Its four tips, verbatim headings and text

    ### Be Specific About Outputs
    Instead of "scrape the data", say "scrape product name, price, and URL into
    a CSV with these column headers".

    ### Share Failures
    If you've tried this before and it failed, share what went wrong. Claude
    will design around those issues.

    ### Start Small
    Get one simple case working, then expand.

    ### Let Claude Test
    Don't skip the testing step. Let Claude run the script and hit real errors —
    that's how the directive gets hardened.

## What is new against this repository's seven slots

Four of the six context types map onto existing slots: Goal to TASK, Edge cases
to ESCAPE and CONSTRAINTS, Constraints to CONSTRAINTS, Preferences and Examples
to OUTPUT and the `NO_EXAMPLE` rule.

**Past work does not.** The CONTEXT slot asks for "what is already true", and
its hint never asks what the author has already tried. Nothing in the seven
slots, in the `/prompt` command, or in the portable preamble asks for a prior
attempt or a known failure — the one category of context a model cannot obtain
for itself and will otherwise re-derive, often by proposing the thing that
already failed.
