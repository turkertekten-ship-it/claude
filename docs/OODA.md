# The OODA loop

## Why a loop and not a cron job

The expensive failure in a retrieval system is not "the index is stale". It is
"the index is stale and nothing noticed".

A scheduled re-index runs whether or not it is needed, and is silent whether or
not it worked. It cannot tell you that one source has been failing for three
days, that 12% of chunks have no vector, that the corpus grew enough to
invalidate its own term statistics, or that retrieval quality dropped after the
last change. Each of those is invisible until someone asks a question and gets a
wrong answer, and by then the cause is a week old.

The loop measures, decides on the measurement, acts, and writes down both.

## The phases

### Observe - gather evidence, change nothing

Probes what this environment can reach (`access/probe.py`) and runs every
connector, collecting per-source deltas: new, changed, unchanged, failed, and the
errors. Journalled before anything acts on it.

Reachability is observed every cycle, not assumed once at startup, because it
changes: tokens expire, policies tighten, hosts go down.

### Orient - turn counts into a situation

Twelve new documents is a number. "The corpus grew 30% and the term statistics no
longer describe it" is a situation a policy can act on. Orient computes:

- embedding coverage, and whether any vectors are from a different embedding space
- corpus growth since the statistics were last fitted
- per-source health: failure rate, consecutive failures, hours since last success
- degradations implied by blocked capabilities
- the previous cycle's eval pass rate, for regression detection

Source health is *stateful* - `consecutive_failures` is what separates a blip
from a broken source, and it only exists because Orient persists it.

### Decide - rules, not a model

`ooda/policy.py` holds every rule as a condition, an action, a priority, and the
evidence that fired it. Rules rather than a learned policy because "why did it
re-crawl at 3am and burn the quota" needs an answer, and "the policy said so,
here is the rule and the measurement" is one.

Priority order encodes what matters: **integrity outranks freshness**. An index
that cannot answer correctly is worse than one that is merely out of date, so
missing vectors (100) and a mismatched embedding space (95) outrank a stale
source (50). Every threshold lives in one `Thresholds` dataclass so the policy is
tunable and reviewable in one place.

### Act - execute within a budget, record the outcome

Actions run in priority order up to `max_actions_per_cycle`; the rest are
recorded as deferred rather than dropped. Every outcome carries status and
duration. A failing action is caught and journalled - one bad action does not end
the cycle.

An alert is a durable journal entry, not a print statement. It is what a human,
or the next cycle, reads.

### Closing the loop

An eval that runs *inside* a cycle produces a pass rate the Decide phase could
not have seen. Rather than waiting a full cycle for that to matter, the loop
re-decides on the updated situation and acts on any regression alert immediately.
That is the difference between a loop and a pipeline with four stages.

## The journal

Every phase writes to a `journal` table keyed by cycle:

```bash
ooda journal --limit 20        # what happened
ooda journal --cycle 7 --json  # everything about one cycle
```

A cycle is fully reconstructible from it: what was observed, what that meant,
what was decided and why, what was done and whether it worked. This is the
auditability that makes an autonomous loop something you can leave running.

## Running it

```bash
ooda loop --cycles 1              # one cycle
ooda loop --cycles 10 --interval 300
ooda loop --dry-run               # decide and explain, act on nothing
```

`--dry-run` is the right first move against a new corpus: it shows what the
policy *would* do, which is the fastest way to find a threshold set wrong.
