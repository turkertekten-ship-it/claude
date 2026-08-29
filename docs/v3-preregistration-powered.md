# Pre-registration: the powered version of the v3 question

Written and committed **before** the run. The first v3 test moved both
endpoints the right way and reached p = 0.5 and p = 0.25, because two and three
discordant cases cannot do better. [src:V3-RESULT-2026-08-29] This is the
attempt to give that question enough discriminating power to answer.

## Why this is affordable, when the fabrication question was not

Pooling both haiku over-refusal runs, v1 declined **0 of 112** arithmetic,
code, explanation and transformation questions, and **4 of 48** recalled world
facts — 8.3%. The over-refusal is entirely confined to facts a citation feels
demanded for. [src:OVER-REFUSAL-HAIKU-2026-08-29]

Concentrating the suite in that category multiplies the discriminating rate by
about 3.3, which is the difference between a $1 experiment and a $10 one. This
is the lever the fabrication question never had: there, the failures were
spread thin across families and no subsetting concentrated them.

## Power, computed in advance

At p = 0.083 per run and two samples, a case shows at least one v1 refusal with
probability 1 − (1 − 0.083)² ≈ **15.9%**. Sixty-one cases should therefore yield
about **9.7 discordant cases** if v3 is clean.

A two-sided exact sign test with k discordant and none against gives
2⁻ᵏ × 2: **six** clears 0.05 (0.031), five does not (0.0625). So the design has
margin, and the margin is the point — the first v3 test failed on exactly this.

## The endpoint, fixed now

**Primary.** Paired per-case comparison on `suites/over-refusal-worldfacts.yaml`,
v1 against v3, 61 cases × 2 samples. A case counts for v3 if v1 refused at least
one sample and v3 refused none, and against v3 in the mirror. Two-sided exact
sign test on those counts.

**Reported regardless of outcome**, including the discordant count, because at
this size the discordant count *is* the precision.

## What would falsify it

- Fewer than six discordant cases → underpowered again; report as not
  measurable and say the 15.9% estimate was optimistic.
- Any case where v3 refuses and v1 does not → counts against v3, and if those
  dominate, v3 is worse.
- v3 clean and v1 clean throughout → the 8.3% rate did not reproduce, which
  would mean the earlier finding was noise and must be said so.

## What this cannot establish

One model family, one prompt pair, one question category. It measures whether
v3 fixes v1's over-refusal on recalled facts. It says nothing about fabrication
— that guardrail was run separately and is not re-run here — and nothing about
whether v3 is a better prompt in general.
