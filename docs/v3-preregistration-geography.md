# Pre-registration: the geography hypothesis, tested rather than sliced

Written and committed **before** the run.

## Where the hypothesis came from, and why it is not yet a finding

The powered v3 run left one clean observation. v1's over-refusal is not spread
across recalled facts — it sits in geography. Of v1's runs there, 0 of 98
acronym, astronomy, chemistry, biology, physics and general-knowledge runs were
refused, and 5 of 24 geography runs were. [src:V3-POWERED-2026-08-29]

That was noticed **after** the data existed. Subsetting the same run to
geography would clear p < 0.05 immediately, and would be worthless: it is the
post-hoc slicing this repository exists to refuse, and it is tempting precisely
because it works. So the hypothesis is tested on forty questions written
afterwards, none reused.

## Power, sized against my own last mistake

The previous design was sized from four events, predicted 9.7 discordant cases
and produced 4. Estimating a rate from a handful of events is how a design
misses by a factor of two, so this one is sized to survive that error.

At the observed 20.8% per run and two samples, a case is discordant with
probability 1 − (1 − 0.208)² ≈ 37.3%; forty cases should yield about **15**.
If the true rate is **half** the observed one, the expectation is still about
**8**. Six clears 0.05. The design holds under a rate error of 2×, which is
exactly the error that spoiled the last one.

## The endpoint, fixed now

**Primary.** Paired per-case comparison on
`suites/over-refusal-geography.yaml`, v1 against v3, 40 cases × 2 samples. A
case counts for v3 if v1 refused at least one sample and v3 refused none, and
against v3 in the mirror. Two-sided exact sign test.

Reported with the discordant counts regardless of outcome.

## What would falsify it

- Fewer than six discordant → the geography concentration was itself noise
  from five events, and the honest report is that the hypothesis did not
  reproduce.
- Cases against v3 appearing → v3 is not strictly better, which nothing in
  141 cases so far has shown.
- v1 refusing nothing → the 20.8% rate was an artifact of those twelve
  particular questions, not a property of the category.

## What this cannot establish

One model family, one prompt pair, one category. It tests whether v3 fixes v1's
geography over-refusal. It says nothing about fabrication, and nothing about
whether v3 is a better prompt in general.
