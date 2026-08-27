"""Blind pairwise comparison.

The failure this exists to prevent: you build a new prompt, you compare it
against the old one, and you grade the comparison yourself. You already know
which is which, so you find the new one better. So does a model judge, if you
tell it which arm is the new one -- and telling it is easy to do by accident,
because variant names leak through labels, through model names in the text,
and through the order you present the candidates in.

Three mechanisms, all of them cheap:

**Identity stripping.** Before a candidate reaches a judge, every string that
identifies its origin is replaced with a neutral token: the variant id, the
model id and its aliases, the backend name, and any extra redactions the suite
declares. The judge sees ``[REDACTED]``, and the report records how many
substitutions were made, so a leak is visible rather than assumed absent.

**Position swap.** Every pair is judged twice: once with candidate A first,
once with B first. A win counts only when both orders agree. When they do not,
the pair is a tie -- the judge preferred a position, not an answer. This costs
exactly double and is the difference between a measurement and a vibe.

**Sealed mapping.** Which candidate is which is held in a mapping that the
judging code never passes to the judge. It is applied after every judgement is
in, at scoring time.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence

from .backend import Backend, Request
from .errors import GraderError

REDACTION = "[REDACTED]"

PAIRWISE_SCHEMA = {
    "type": "object",
    "properties": {
        "winner": {"type": "string", "enum": ["FIRST", "SECOND", "TIE"]},
        "reason": {"type": "string"},
    },
    "required": ["winner", "reason"],
    "additionalProperties": False,
}

PAIRWISE_SYSTEM = (
    "Please act as an impartial judge comparing two candidate responses to the "
    "same task. You do not know which system produced either candidate, and "
    "you must not guess. Judge only against the stated criterion.\n\n"
    "Avoid any position biases and ensure that the order in which the "
    "responses were presented does not influence your decision. Do not allow "
    "the length of the responses to influence your evaluation. Do not favor "
    "certain names. Be as objective as possible.\n\n"
    "Further rules:\n"
    "- Confidence is not correctness. An assertive wrong answer loses.\n"
    "- If the two are equally good, or differ only in style, answer TIE. TIE "
    "is a real verdict, not a failure to decide.\n"
    "- In `reason`, quote the specific span of the candidate that decided it. "
    "A reason that could have been written without reading the candidates is "
    "not a reason.\n\n"
    "Return only the requested JSON object."
)

#: The three bias-suppression sentences above are copied from the judge prompt
#: shipped with FastChat's MT-Bench (`pair-v2`). They are worth including and
#: worth not trusting: in the MT-Bench measurements, judges carrying that exact
#: instruction still preferred a padded, information-free rewrite of an answer
#: over the original in 91.3% of trials (Claude-v1 and GPT-3.5; GPT-4, 8.7%).
#: The instruction is cheap. The position swap below is what actually works.


@dataclass
class Candidate:
    """One side of a comparison, with its identity held separately from its text."""

    variant_id: str
    text: str
    model: str = ""
    #: Populated by :func:`blind_text`; counts what had to be hidden.
    redactions: int = 0

    def fingerprint(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:12]


@dataclass
class PairJudgement:
    """The outcome of judging one pair, after both orders have been run."""

    case_id: str
    left: str                  # variant id
    right: str                 # variant id
    winner: str                # variant id, or "TIE"
    agreed: bool               # did both orders give the same answer?
    orders: list[dict[str, Any]] = field(default_factory=list)
    cost_usd: float = 0.0
    redactions: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id, "left": self.left, "right": self.right,
            "winner": self.winner, "agreed": self.agreed,
            "orders": self.orders, "cost_usd": round(self.cost_usd, 6),
            "redactions": self.redactions,
        }


def identity_tokens(variant_ids: Iterable[str], models: Iterable[str],
                    extra: Sequence[str] = ()) -> list[str]:
    """Every string that could tell a judge which arm it is looking at.

    Model ids are expanded to their family aliases, because a candidate that
    says "as Claude Haiku I would" identifies itself just as surely as one
    tagged with its variant name.
    """
    tokens: set[str] = set()
    for vid in variant_ids:
        if vid:
            tokens.add(vid)
            tokens.add(vid.replace("-", " "))
            tokens.add(vid.replace("_", " "))
    for model in models:
        if not model:
            continue
        tokens.add(model)
        # claude-haiku-4-5-20251001 -> claude-haiku-4-5, claude-haiku, haiku
        parts = model.split("-")
        for cut in range(2, len(parts)):
            tokens.add("-".join(parts[:cut]))
        if len(parts) >= 2:
            tokens.add(parts[1])
    tokens.update(t for t in extra if t)
    # Longest first: redact "claude-haiku-4-5" before the bare "haiku" inside it.
    return sorted({t for t in tokens if len(t) >= 3}, key=len, reverse=True)


def blind_text(text: str, tokens: Sequence[str]) -> tuple[str, int]:
    """Replace every identity token with :data:`REDACTION`; return the count."""
    redacted = text
    total = 0
    for token in tokens:
        pattern = re.compile(re.escape(token), re.IGNORECASE)
        redacted, n = pattern.subn(REDACTION, redacted)
        total += n
    return redacted, total


def seal(candidates: Sequence[Candidate], seed: str) -> tuple[list[Candidate], dict[str, str]]:
    """Shuffle candidates deterministically and label them by position.

    Returns the shuffled list plus a mapping ``{"C1": variant_id, ...}``. The
    mapping is the sealed envelope: nothing downstream of this call passes it
    to a judge.
    """
    rng = random.Random(seed)
    order = list(candidates)
    rng.shuffle(order)
    mapping = {f"C{i + 1}": c.variant_id for i, c in enumerate(order)}
    return order, mapping


def _ask(backend: Backend, criterion: str, first: str, second: str,
         model: str | None, repeat: int) -> tuple[str, str, float]:
    prompt = (
        f"CRITERION\n{criterion}\n\n"
        f"CANDIDATE FIRST\n<<<FIRST\n{first}\nFIRST\n\n"
        f"CANDIDATE SECOND\n<<<SECOND\n{second}\nSECOND\n\n"
        "Which candidate better satisfies the criterion? Answer FIRST, SECOND "
        "or TIE."
    )
    completion = backend.complete(Request(
        prompt=prompt, system=PAIRWISE_SYSTEM, model=model,
        json_schema=PAIRWISE_SCHEMA, tools="", repeat=repeat,
    ))
    payload = completion.structured
    if payload is None:
        try:
            payload = json.loads(completion.text)
        except (json.JSONDecodeError, ValueError):
            # Not a tie -- a tie is a verdict, and manufacturing one here would
            # bury a broken judge inside a plausible-looking null result.
            payload = {"winner": "ERROR",
                       "reason": f"unparseable judge output: {completion.text[:200]}"}
    winner = str(payload.get("winner", "")).upper()
    if winner not in ("FIRST", "SECOND", "TIE"):
        # Never coerce an unreadable verdict into a tie: a tie is a judgement
        # the judge made, and silently manufacturing them hides a broken judge
        # behind a plausible-looking null result.
        winner = "ERROR"
    return winner, str(payload.get("reason", "")), completion.cost_usd or 0.0


def judge_pair(backend: Backend, criterion: str, a: Candidate, b: Candidate,
               case_id: str, tokens: Sequence[str], model: str | None = None,
               seed: str = "") -> PairJudgement:
    """Judge ``a`` against ``b`` blind, in both orders.

    A win is recorded only if the judge picks the same candidate in both
    presentations. Disagreement between the two orders is reported as a tie
    and flagged ``agreed=False``, which is the position-bias signal: a suite
    where most pairs disagree is measuring the judge, not the variants.
    """
    if backend is None:
        raise GraderError("blind comparison needs a judge backend")

    a_text, a_red = blind_text(a.text, tokens)
    b_text, b_red = blind_text(b.text, tokens)

    # Order 1: a first. Order 2: b first. Same criterion, same texts.
    w1, r1, c1 = _ask(backend, criterion, a_text, b_text, model, repeat=0)
    w2, r2, c2 = _ask(backend, criterion, b_text, a_text, model, repeat=1)

    # Translate positional verdicts back into variant ids. Each order gets its
    # own map, because "FIRST" means a different variant in each presentation.
    pick1 = {"FIRST": a.variant_id, "SECOND": b.variant_id,
             "TIE": "TIE", "ERROR": "ERROR"}[w1]
    pick2 = {"FIRST": b.variant_id, "SECOND": a.variant_id,
             "TIE": "TIE", "ERROR": "ERROR"}[w2]

    if "ERROR" in (pick1, pick2):
        winner, agreed = "ERROR", False
    else:
        agreed = pick1 == pick2
        winner = pick1 if agreed else "TIE"

    return PairJudgement(
        case_id=case_id, left=a.variant_id, right=b.variant_id,
        winner=winner, agreed=agreed,
        orders=[
            {"presented_first": a.variant_id, "verdict": w1, "resolved": pick1, "reason": r1},
            {"presented_first": b.variant_id, "verdict": w2, "resolved": pick2, "reason": r2},
        ],
        cost_usd=c1 + c2,
        redactions=a_red + b_red,
    )


def position_bias_rate(judgements: Sequence[PairJudgement]) -> float:
    """Share of pairs where swapping the order changed the verdict.

    Zero means the judge was reading the answers. Approaching one means it was
    reading the layout, and the comparison should not be reported as a result.
    """
    scored = [j for j in judgements if j.winner != "ERROR"]
    if not scored:
        return 0.0
    return sum(1 for j in scored if not j.agreed) / len(scored)


def identical_pair_control(backend: Backend, criterion: str, text: str,
                           model: str | None = None) -> dict[str, Any]:
    """Show the judge the same answer twice. It must call a tie.

    This is the cheapest possible test of whether blinding actually works, and
    it is a real check rather than a formality: a judge shown two byte-identical
    candidates has nothing to go on except signals that should not be there.
    If it picks a winner, something in the payload is still distinguishing the
    two slots -- residual identity, or raw position preference -- and every
    comparison in the run is suspect.

    Runs before the real comparisons so a leak is caught before the budget is
    spent, not after the numbers are written up.
    """
    w1, r1, c1 = _ask(backend, criterion, text, text, model, repeat=0)
    w2, r2, c2 = _ask(backend, criterion, text, text, model, repeat=1)
    passed = w1 == "TIE" and w2 == "TIE"
    return {
        "control": "identical-pair",
        "passed": passed,
        "verdicts": [w1, w2],
        "reasons": [r1[:300], r2[:300]],
        "cost_usd": c1 + c2,
        "detail": (
            "the judge tied two identical candidates, as it must"
            if passed else
            f"the judge picked a winner ({w1}/{w2}) between two IDENTICAL "
            f"candidates. Blinding is leaking or the judge is reading position. "
            f"Do not trust this run's comparisons."
        ),
    }


def length_summary(candidates: Sequence[Candidate]) -> dict[str, int]:
    """Character counts per variant, so a length confound is visible.

    Judges have a measured preference for longer answers, so a win rate should
    never be read without knowing whether the winner was also systematically
    the wordier one.
    """
    return {c.variant_id: len(c.text) for c in candidates}


def same_family(model_a: str, model_b: str) -> bool:
    """Do two model ids come from the same family? Used to warn about self-judging.

    A judge from the same family as a candidate is measured to favour it. The
    workbench does not refuse the configuration -- sometimes it is the only
    model available -- but it does say so in the report.
    """
    def family(model: str) -> str:
        parts = (model or "").split("-")
        return parts[1] if len(parts) >= 2 else (model or "")
    return bool(model_a) and bool(model_b) and family(model_a) == family(model_b)
