<!-- source: https://oodarag.example/handbook/citations-and-abstention -->
# Citations, Verification and Honest Abstention

The worst output a retrieval system can produce is not a wrong answer. It is a
confident wrong answer carrying a real-looking source, because it survives a
skim, it is unfalsifiable at a glance, and it travels into whatever it is
pasted into.

## Extractive answers

The default generator is extractive: every sentence of the answer is copied
verbatim from a retrieved chunk, and every citation carries the exact quote it
was copied from. This removes the mechanism by which a fabrication could occur.
There is no step capable of emitting a sentence the corpus does not contain.
The cost is real: extraction cannot summarize, cannot combine two half-answers
into one sentence, and sometimes reads like a list of quotations, which is what
it is.

## Verification by containment

Citations are verified rather than trusted, and the check is deliberately
adversarial towards the code that produced them. A citation survives only if it
names a chunk that was actually retrieved, its quote is a non-empty substring
of that chunk's body text, and its document identifier and URI agree with the
chunk's own document. A plausible URL bolted onto a genuine quote is precisely
the failure a reader is least able to catch.

Quotes are matched against the chunk body, never against the indexed text,
because the context header is written by the chunker. Quoting it would
attribute our own words to the source document. Failed citations are dropped,
never repaired: a silently corrected citation is a claim nobody checked.

## Abstention

When the best available evidence scores below the confidence floor, the answer
is an abstention with no citations attached. An honest abstention is a correct
answer. The abstention text names the score it saw and the floor it was
measured against, so a reader can tell "nothing relevant was retrieved" from
"the floor is set too high" without opening the metrics.

If every citation fails verification, the pipeline abstains rather than
shipping the prose with the sources quietly stripped off. From the outside,
an answer with no surviving provenance is indistinguishable from an invention.
