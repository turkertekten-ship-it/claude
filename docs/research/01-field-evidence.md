---
provenance: enforced
---

# What the evidence says about AI in investment firms

> Framing, not a claim: this document exists to settle one question before any
> design work happens — *where has this actually worked, and where has it
> reliably not?* Everything below is a finding with a source. The design
> decisions that follow from it are argued separately, in the design document,
> so that a reader who disagrees with the design can still use the evidence.

The short version: the industry's own surveys say AI disappoints in exactly the
places where it is most often pitched, and works in the places nobody
demonstrates on stage. A system designed against the pitch will be abandoned. A
system designed against the evidence has a chance.

## Observed — where AI is rated ineffective

- In S&P Global Market Intelligence's 2026 private equity survey, a majority of managers rated AI **ineffective for deal sourcing** — 64%. [src:PE-AI-SURVEY-2026]
- A larger majority, 75%, rated it **ineffective for portfolio monitoring**. [src:PE-AI-SURVEY-2026]
- Those are the two use cases most heavily marketed to fund managers, and they are the two the managers themselves rank lowest. [src:PE-AI-SURVEY-2026]

## Observed — where AI is rated effective

- Due diligence shows the **highest integration** of any function surveyed, at 31% somewhat or fully integrated. [src:PE-AI-SURVEY-2026]
- Deloitte found the most traction in strategy and market assessment (40%), target screening (35%) and diligence (35%). [src:PE-AI-SURVEY-2026]
- In fund administration specifically, the pattern reported is that AI is strongest on **document-heavy processes** — extraction and onboarding — and acts only as a **supporting layer on the numerical core**, where the platform and its deterministic controls do the heavy lifting. [src:FUNDADMIN-AI-2026]

> Reading, not a finding: the common shape of both results is that the model
> reads documents and does not decide numbers. That line is the whole design in
> one sentence, and it is an interpretation of the findings above rather than
> one of them.

## Observed — why most attempts fail

- MIT's 2026 study reported that approximately **95% of enterprise GenAI pilots delivered no measurable P&L impact**, across 52 executive interviews, 153 leader surveys and 300 public deployments. [src:MIT-PILOT-FAILURE-2026]
- **Data readiness** was identified as the single largest driver of failure, and as the root cause that gets discovered latest in a pilot's timeline. [src:MIT-PILOT-FAILURE-2026]
- The organisations that succeeded shared one pattern: **agents connected to real institutional data, not chatbots with system prompts**. [src:MIT-PILOT-FAILURE-2026]
- External vendor tools succeeded roughly **twice as often as internal builds**. [src:MIT-PILOT-FAILURE-2026]
- The stated adoption barriers are not technical: lack of expertise (49%), data privacy (43%), model accuracy (38%). [src:PE-AI-SURVEY-2026]
- Deloitte's top two blockers are **data security (67%)** and data quality or availability (65%). [src:PE-AI-SURVEY-2026]

> The vendor-success finding cuts against building anything at all, and it is
> recorded here rather than quietly dropped. The argument for building in this
> particular case is made in the design document, and it rests on one fact the
> MIT sample does not cover: no vendor sells a Turkish-language SPK obligation
> monitor with TMS 29 restatement built in. Where a vendor does cover a job —
> fund accounting, custody, audit — the evidence says buy it.

## Observed — what the canonical success actually did

- EQT's Motherbrain was founded in **2016** and supports the whole investment lifecycle rather than a single task. [src:EQT-MOTHERBRAIN-2026]
- What it ingests is the *thought record* of an investment: meeting notes, people in common, numbers, presentations and emails. [src:EQT-MOTHERBRAIN-2026]
- EQT's own account emphasises that data alone is not enough, and that the system is built to **support rather than replace** human decision-making, through collaboration between engineers, data scientists and dealmakers. [src:EQT-MOTHERBRAIN-2026]

> Second-hand, and self-reported: these descriptions come from EQT's own pages.
> No independent evaluation of Motherbrain's effect on returns was found. The
> reason it is still worth recording is the *shape* of the claim, not its size —
> a ten-year programme with an embedded engineering team is what the canonical
> success actually costs, which is the relevant fact for a firm considering a
> six-week version of it.

## Observed — the fund-operations picture

- 98% of investor relations professionals are reported to use AI at least weekly, with about a third of firms moving AI into full production by mid-2026. [src:FUNDADMIN-AI-2026]
- 78% of fund accountants expect AI to play a major role in their work, yet 66% still name **manual data entry** as their top headache, attributed to tools that are not genuinely integrated. [src:FUNDADMIN-AI-2026]

> These percentages come from vendors marketing their own products and are
> recorded as low-confidence. The qualitative pattern — enthusiasm high,
> integration low, manual entry still the bottleneck — recurs across
> independent vendors, which is why it is kept at all. Treat the numbers as
> directional and the pattern as real.

## What this rules in and out

Read together, the findings point one way. The three things the evidence
supports building are document extraction with verified provenance, obligation
and regulatory-change tracking, and diligence support — all of them
document-shaped. The three things the evidence says not to build are an
AI deal-sourcing engine, an AI portfolio-monitoring dashboard, and anything
that lets a language model compute a number that ends up in a report.

The design document takes that as its starting constraint rather than
re-arguing it.
