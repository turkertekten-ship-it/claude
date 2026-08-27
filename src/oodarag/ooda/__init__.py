"""The loop: Observe, Orient, Decide, Act.

Decide is deterministic by construction — see policy.py and rules.py. No
language model is reachable from this package.
"""

from oodarag.ooda.act import Brief, DecisionJournal, render_brief
from oodarag.ooda.policy import (
    Action,
    PolicyEngine,
    Rule,
    Signal,
    State,
    journal_line,
)
from oodarag.ooda.rules import default_ruleset

__all__ = [
    "Action", "Brief", "DecisionJournal", "PolicyEngine", "Rule", "Signal",
    "State", "default_ruleset", "journal_line", "render_brief",
]
