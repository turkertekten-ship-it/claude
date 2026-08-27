<!-- source: https://oodarag.example/handbook/ooda-loop -->
# The OODA Loop Applied to a Retrieval Pipeline

The OODA loop is a four-phase decision cycle: Observe, Orient, Decide, Act. It
was formulated by the fighter pilot and strategist John Boyd, and its value is
not speed for its own sake but the discipline of separating what is true from
what it means and from what to do about it.

## Observe

Observation collects facts and passes no judgement. For a retrieval pipeline
that means index statistics, the per-source ingest deltas from the last run,
the age of each source, the error list, and the most recent evaluation report.
The rule that gives this phase its value is to enumerate before interpreting.
Most fabricated conclusions come from an Orient step running on an empty
Observe.

## Orient

Orientation scores the observations into a small number of judgements:
staleness, quality, error rate, and coverage gaps. This is where a surprise is
named. Every cycle should record where reality diverged from expectation, and a
cycle with no surprise usually means Observe was skipped.

## Decide

Decision maps the orientation onto a bounded list of actions: reingest a stale
source, reindex after a chunker change, retune a threshold, backfill a gap,
raise an alert, or do nothing. Deciding is kept a pure function of the
orientation, with no input from the network and no writes, so a policy change
can be tested without an index. Doing nothing is a real decision and must be
representable, otherwise the loop invents work to justify itself.

## Act

Act is the only phase permitted to mutate anything, and every action returns a
result that becomes an observation on the next cycle. A dry run mode executes
Observe, Orient and Decide and stops before Act, which is how a new policy is
reviewed before it is trusted.

## Why the phases stay separate

Collapsing Orient into Observe produces confident readings of data nobody
gathered. Collapsing Decide into Act produces changes that cannot be reviewed
before they happen. Keeping the four phases as separate functions, each with
its own artifact, is what makes the loop auditable after the fact.
