"""The statistics needed to say whether a difference is real.

Small eval suites produce differences that look decisive and are not. Six
cases, four wins and two losses, is a 67% win rate -- and a fair coin produces
that or better about a third of the time. Reporting "67%" without that context
is how a prompt change gets adopted on noise.

Everything here is exact where it can be and stdlib-only throughout: an
inability to install SciPy should not be the reason a result goes unqualified.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class Interval:
    low: float
    high: float

    def __str__(self) -> str:
        return f"[{self.low:.3f}, {self.high:.3f}]"


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> Interval:
    """95% confidence interval for a proportion, Wilson score method.

    Chosen over the textbook normal approximation because eval suites are
    small and often land on 0/n or n/n, where the normal interval collapses to
    zero width and claims certainty from four data points.
    """
    if trials <= 0:
        return Interval(0.0, 1.0)
    p = successes / trials
    denom = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials))
    return Interval(max(0.0, centre - margin), min(1.0, centre + margin))


def sign_test(wins: int, losses: int) -> float:
    """Two-sided exact binomial p-value for paired wins against losses.

    This is exactly McNemar's exact test: both reduce to a binomial on the
    discordant pairs, and the concordant ones carry no information about which
    variant is better. :func:`mcnemar` below is the same arithmetic reached
    from a 2x2 pass/fail table, kept separate because that is the shape a
    grader run actually produces.

    Ties are excluded, which is the standard treatment: a tie carries no
    directional information. With ties dropped, the null hypothesis is that a
    non-tied pair is a coin flip.

    Returns 1.0 when there is nothing to test.
    """
    n = wins + losses
    if n == 0:
        return 1.0
    observed = max(wins, losses)
    tail = sum(math.comb(n, k) for k in range(observed, n + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def bootstrap_win_rate(outcomes: Sequence[str], winner_id: str,
                       iterations: int = 10000, seed: int = 0,
                       alpha: float = 0.05) -> Interval:
    """Percentile bootstrap CI for a win rate over per-case outcomes.

    ``outcomes`` holds one entry per case: the winning variant id, or ``TIE``.
    Ties count as half a win, the usual convention, so that a suite of all
    ties reports 0.5 rather than an undefined rate.
    """
    if not outcomes:
        return Interval(0.0, 1.0)
    rng = random.Random(seed)
    n = len(outcomes)

    def rate(sample: Sequence[str]) -> float:
        score = sum(1.0 if o == winner_id else 0.5 if o == "TIE" else 0.0 for o in sample)
        return score / len(sample)

    rates = sorted(rate([outcomes[rng.randrange(n)] for _ in range(n)])
                   for _ in range(iterations))
    lo = rates[int(alpha / 2 * iterations)]
    hi = rates[min(iterations - 1, int((1 - alpha / 2) * iterations))]
    return Interval(lo, hi)


def bradley_terry(pairs: Sequence[tuple[str, str]], iterations: int = 500,
                  tolerance: float = 1e-9) -> dict[str, float]:
    """Fit Bradley-Terry strengths from a list of ``(winner, loser)`` pairs.

    For more than two variants, counting each one's raw win rate is misleading
    because they do not all face the same opponents. Bradley-Terry solves for
    a strength per variant such that the predicted win probabilities match what
    was observed, using the standard MM update.

    Strengths are normalised to sum to 1, so they read as shares. A variant
    that never lost gets a large but finite strength -- the +1 smoothing keeps
    an undefeated arm from producing an infinity that swamps the table.
    """
    players = sorted({p for pair in pairs for p in pair})
    if not players:
        return {}
    wins: dict[str, float] = {p: 0.0 for p in players}
    meetings: dict[tuple[str, str], float] = {}
    for winner, loser in pairs:
        wins[winner] += 1.0
        key = tuple(sorted((winner, loser)))
        meetings[key] = meetings.get(key, 0.0) + 1.0

    strength = {p: 1.0 for p in players}
    for _ in range(iterations):
        updated: dict[str, float] = {}
        for p in players:
            denominator = 0.0
            for (a, b), count in meetings.items():
                if p not in (a, b):
                    continue
                other = b if p == a else a
                denominator += count / (strength[p] + strength[other])
            # +1 smoothing on both halves: an undefeated player would otherwise
            # diverge, and a winless one would collapse to zero.
            updated[p] = (wins[p] + 1.0) / (denominator + 1.0 / (strength[p] + 1.0)) \
                if denominator > 0 else strength[p]
        total = sum(updated.values()) or 1.0
        updated = {p: v / total for p, v in updated.items()}
        delta = max(abs(updated[p] - strength[p]) for p in players)
        strength = updated
        if delta < tolerance:
            break
    return dict(sorted(strength.items(), key=lambda kv: -kv[1]))


def required_pairs(effect: float = 0.7, power: float = 0.8, alpha: float = 0.05) -> int:
    """Roughly how many non-tied pairs are needed to detect a given win rate.

    A normal approximation to the sign test, rounded up. It is here so a suite
    author can be told "six cases cannot show this" before they run it, rather
    than after. Approximate by construction -- it is a planning number, not a
    result.
    """
    if effect <= 0.5:
        return 0
    z_alpha = 1.959963985  # two-sided 0.05
    z_beta = {0.8: 0.8416, 0.9: 1.2816, 0.95: 1.6449}.get(round(power, 2), 0.8416)
    numerator = (z_alpha * 0.5 + z_beta * math.sqrt(effect * (1 - effect))) ** 2
    return math.ceil(numerator / (effect - 0.5) ** 2)


def summarise_pairwise(outcomes: Sequence[str], a: str, b: str,
                       seed: int = 0) -> dict[str, object]:
    """Roll a list of per-case winners into a reportable comparison."""
    wins = sum(1 for o in outcomes if o == a)
    losses = sum(1 for o in outcomes if o == b)
    ties = sum(1 for o in outcomes if o == "TIE")
    errors = sum(1 for o in outcomes if o == "ERROR")
    # An unreadable verdict is not a tie, so it must not sit in the denominator
    # of a rate that treats ties as half a win. It is reported on its own.
    scored = wins + losses + ties
    p = sign_test(wins, losses)
    return {
        "a": a, "b": b, "wins_a": wins, "wins_b": losses, "ties": ties,
        "errors": errors,
        "decided": wins + losses,
        "win_rate_a_excluding_ties": (wins / (wins + losses)) if (wins + losses) else None,
        "win_rate_a_ties_as_half": (wins + 0.5 * ties) / scored if scored else None,
        "p_value_sign_test": round(p, 5),
        "significant_at_0.05": p < 0.05,
        "ci95_win_rate_a": str(bootstrap_win_rate(outcomes, a, seed=seed)),
        "pairs_needed_for_70pct_effect": required_pairs(),
    }


def mcnemar(both_pass: int, a_only: int, b_only: int, both_fail: int) -> dict[str, object]:
    """Exact McNemar test over a paired pass/fail table.

    Every variant answers the same cases, so the right comparison is
    case-by-case, not two independent pass rates. Cases where both variants
    passed, or both failed, tell you nothing about which is better -- only the
    discordant cells do.

    The exact binomial form is used rather than the chi-square approximation
    because a prompt suite has tens of cases, not thousands, and that is
    precisely where the approximation misleads.
    """
    discordant = a_only + b_only
    return {
        "both_pass": both_pass, "a_only": a_only,
        "b_only": b_only, "both_fail": both_fail,
        "discordant": discordant,
        "p_value_exact": round(sign_test(a_only, b_only), 5),
        "significant_at_0.05": sign_test(a_only, b_only) < 0.05,
        "note": ("no discordant pairs: the variants passed and failed the same "
                 "cases, so this suite cannot separate them"
                 if discordant == 0 else
                 f"{discordant} case(s) separated the variants"),
    }


def paired_table(a_results: dict[str, bool], b_results: dict[str, bool]) -> dict[str, object]:
    """Build and test the paired pass/fail table for two variants over shared cases."""
    shared = sorted(set(a_results) & set(b_results))
    both_pass = sum(1 for c in shared if a_results[c] and b_results[c])
    a_only = sum(1 for c in shared if a_results[c] and not b_results[c])
    b_only = sum(1 for c in shared if not a_results[c] and b_results[c])
    both_fail = sum(1 for c in shared if not a_results[c] and not b_results[c])
    result = mcnemar(both_pass, a_only, b_only, both_fail)
    result["cases"] = len(shared)
    return result
