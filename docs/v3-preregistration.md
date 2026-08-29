# Pre-registration: does v3 reduce over-refusal without buying fabrication?

Written and committed **before** the runs it analyses. Six earlier experiments
in this repository came back null, one came back void, and one reversed a claim
I had already published. The temptation to pick the endpoint after seeing the
data is exactly what this file removes.

## The change under test

`prompts/base-operator-v3.md` is `prompts/base-operator.md` plus one section,
"What the sourcing rule is about". Nothing else differs.

It exists because v1 over-refuses roughly 1 answerable question in 40 on
`claude-haiku-4-5`, declining universally-known facts on the grounds that it
cannot source them. [src:OVER-REFUSAL-HAIKU-2026-08-29]

The clause is written from the mechanism — a sourcing rule applied where it was
never aimed — and names none of the questions that failed. v2 was written
against specific audited failures, and fixed two cases on the set its rules came
from and none on fourteen held out. [src:V2-OVERFIT-2026-08-27] Naming the
cases is how that happens.

## Endpoints, fixed in advance

**Primary — over-refusal.** Pass rate on `suites/over-refusal-haiku.yaml`,
forty answerable questions where declining is wrong, v3 against v1, two samples
each. v1's measured rate is 78/80. A directional prediction: v3 answers more of
them. Reported as the paired difference with the count of discordant cases,
because at this size the discordant count is the whole precision story — 4
discordant against 0 floors a two-sided sign test at p = 0.125, and 2 floors it
at 0.5.

**Guardrail — fabrication.** Pass rate on `suites/fabrication-powered.yaml`,
one sample per case rather than three, v3 against v1. **If v3 fabricates more,
it is rejected regardless of what the primary shows.** A prompt that answers
more questions by being less careful is not an improvement; it is the trade
undone.

One sample per case is deliberately weak. It can detect a large regression and
cannot detect a small one, and it is not being asked to: the powered version of
that question is answered already, and re-running it at full power costs $8.66
to re-establish a null.

## What would falsify the change

- v3 over-refuses at the same rate or worse → the clause does not work, and
  the mechanism reading behind it is wrong.
- v3 fabricates more on the traps → rejected on the guardrail, whatever the
  primary says.
- Both endpoints move by less than their discordant-case floor → the honest
  report is "not measurable at this size", not "a small improvement".

## What this cannot establish

One model family. `claude-haiku-4-5` only, because that is where both effects
were measured. A clause that helps here may not transfer, which is the same
limitation every other result in this repository carries.

Nothing about whether v3 is a better prompt in general. It is being measured on
two specific failure modes, not read for quality.

## Commands

```bash
python3 -m workbench run suites/over-refusal-v3.yaml       # primary
python3 -m workbench run suites/fabrication-v3-guard.yaml  # guardrail
```
