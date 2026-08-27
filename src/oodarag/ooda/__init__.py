"""The control loop that keeps the index worth querying.

Every other package here runs when something calls it. This one decides when
something should be called: it reads the corpus's own state - how old each
source is, whether the indexes still describe the store, what the goldens say
about answer quality - and turns that into a short list of actions with reasons
attached.

The four phases are exported as separate, separately-testable pieces because
that separation is the entire design. `decide` in particular is a pure function
of `(Orientation, Observation)`, so the policy can be exercised against literal
dataclasses with no pipeline, no network and no index in sight; the scoring
formulas (`staleness_score`, `quality_score`, `index_deficit`) are public for
the same reason. See `loop.py` for why each boundary is drawn where it is.
"""

from __future__ import annotations

from oodarag.ooda.loop import (
    ACTION_VALUE,
    DEFAULT_REFRESH_INTERVAL_S,
    ERROR_RATE_ALERT,
    Action,
    CycleReport,
    LoopPolicy,
    Observation,
    OodaLoop,
    Orientation,
    index_deficit,
    quality_score,
    staleness_score,
)

__all__ = [
    "ACTION_VALUE",
    "Action",
    "CycleReport",
    "DEFAULT_REFRESH_INTERVAL_S",
    "ERROR_RATE_ALERT",
    "LoopPolicy",
    "Observation",
    "OodaLoop",
    "Orientation",
    "index_deficit",
    "quality_score",
    "staleness_score",
]
