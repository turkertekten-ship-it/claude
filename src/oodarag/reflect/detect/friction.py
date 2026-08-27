"""Rules that turn re-typing into something written down once.

The most expensive thing in a working day is not a slow command; it is a
decision that has already been made being made again. Every night this module
reads back the prompts the user actually typed and looks for three shapes of
that waste:

* the same standing instruction given across three separate sessions ("always
  run make test before committing") - a project convention that lives in
  someone's short-term memory instead of in a file;
* the same request rephrased immediately after itself inside one session,
  which means the first phrasing did not land and the *second* one is the
  phrasing worth keeping;
* a prompt that opens by correcting the previous answer ("no, use ruff") -
  the single highest-signal sentence in any transcript, because it is the user
  stating a preference the system provably did not have.

All three end in the same place: one line in the project memory file, so the
instruction is given once to a file instead of forever to a chat box.

Two design positions cost real code here and are worth stating.

**Grouping happens on a stemmed, filler-stripped, polarity-tagged form of the
prompt rather than on the prompt.** Nobody types a standing preference the same
way twice, so exact grouping finds nothing and the rule is dead weight. But a
normalizer loose enough to fold "never squash" into "always squash" would make
the loop write the opposite of the user's preference into the user's own memory
file, which is far worse than finding nothing. Hence `normalize_instruction`:
modality and politeness out, light stemming on, negation carried explicitly
because the shared stopword list eats "not" and "don't" on the way past.

**Nothing in here rewrites prose.** The only edit these rules ever propose is a
bullet under a heading the loop itself owns - the file created outright when it
is absent (`safe`), a section ensured when it is not (`review`). A rule that
mines somebody's words is precisely the rule that should not also be trusted to
edit them.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from oodarag.reflect.detect.base import (
    DetectContext,
    Detector,
    jaccard,
    normalize_phrase,
    register,
    words,
)
from oodarag.reflect.models import (
    ACTOR_ASSISTANT,
    KIND_PROMPT,
    KIND_REPLY,
    RISK_ORDER,
    EditOp,
    Evidence,
    Finding,
    Proposal,
    Signal,
)
from oodarag.util.logging import get_logger
from oodarag.util.text import STOPWORDS

log = get_logger("reflect.friction")

#: Where a project's standing instructions live. Overridable per rule via the
#: `memory_file` setting, because not every project calls it the same thing.
DEFAULT_MEMORY_FILE = "CLAUDE.md"

#: Headings the loop owns. Owning a heading is what makes appending to someone
#: else's file an additive operation rather than an edit of their prose.
CONVENTIONS_HEADING = "## Conventions learned by the nightly loop"
CORRECTIONS_HEADING = "## Corrections"

MEMORY_HEADER = (
    "# Project memory\n"
    "\n"
    "Notes the nightly reflect loop learned by watching how this project is\n"
    "actually worked on. Everything below is an observation, not a rule you are\n"
    "stuck with - edit or delete freely.\n"
    "\n"
)

#: Cues that mark a prompt as an instruction rather than a question or a piece
#: of narration. Deliberately short: missing one costs a single finding, while
#: treating every sentence as an instruction costs the report its credibility.
DEFAULT_INSTRUCTION_CUES = (
    "always",
    "never",
    "please",
    "make sure",
    "remember",
    "use",
    "don't",
    "do not",
    "prefer",
    "stop",
    "avoid",
)

#: Openings that make a short prompt a question or an acknowledgement rather
#: than a directive. Only consulted for prompts with no explicit cue.
_QUESTION_OPENERS = frozenset(
    """
    what why how when where who whom which whose is are was were do does did
    can could should would will shall may might am if i we you it he she they
    there this that these those the a an ok okay sure thanks thank yes no yeah
    yep nope hi hello hey maybe perhaps
    """.split()
)

#: Leading modality and politeness, removed before grouping. "Please always
#: remember to run the tests" and "run the tests" are one instruction, and a
#: fingerprint that disagrees splits one finding into three.
_LEAD_FILLER = (
    "also",
    "always",
    "and",
    "be sure to",
    "can you",
    "could you",
    "from now on",
    "going forward",
    "i want you to",
    "i would like you to",
    "i'd like you to",
    "in future",
    "in the future",
    "just",
    "kindly",
    "let's",
    "lets",
    "make sure that you",
    "make sure to",
    "make sure you",
    "make sure",
    "note that",
    "please",
    "remember to",
    "remember",
    "so",
    "we should",
    "would you",
    "you must",
    "you need to",
    "you should",
)

#: Negation carried as a key prefix rather than as tokens, so "don't rebase"
#: and "never rebase" group together while "rebase" stays a different idea.
_NEGATION_CUES = ("never", "don't", "dont", "do not", "no longer")
_NEGATION_TOKENS = frozenset({"never", "don", "dont", "longer"})

#: Phrases that mark a prompt as a repair of the previous answer.
DEFAULT_CORRECTION_MARKERS = (
    "no,",
    "nope",
    "actually",
    "i meant",
    "i said",
    "that's not",
    "thats not",
    "not what",
    "wrong",
    "don't",
    "do not",
    "stop",
    "instead",
    "again,",
    "revert",
    "undo",
)

#: Anything that looks like a credential is never proposed as an automatic
#: edit, whatever the risk tier would otherwise have been.
_CREDENTIAL_RE = re.compile(
    r"(?i)(?:<redacted|\b(?:api[_\- ]?key|secret|password|passwd|token|credential"
    r"|private[_-]?key|\.env)\b)"
)

# Clause boundaries. A correction is usually "<complaint>. <the actual
# instruction>", and only the second half is worth writing down.
_CLAUSE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+|\s*\n+\s*|\s+[-—–]{1,2}\s+")

# Suffix stripping leaves a doubled consonant behind ("committing" ->
# "committ"); undoubling it is what makes it meet "commit".
_DOUBLED_END_RE = re.compile(r"([bdfglmnprt])\1$")

_MIN_STEM_CHARS = 3
_STRIP_CHARS = " \t,.;:!?-\"'`*"


# -- configuration helpers ---------------------------------------------------


def _cfg_int(config: dict[str, Any], key: str, default: int) -> int:
    """Read an int setting, falling back on anything unusable.

    Rule config arrives from JSON written by a human, so a string, a null or a
    typo are all normal. A nightly run must not die because a threshold was
    quoted.
    """
    try:
        return int(config[key])
    except (KeyError, TypeError, ValueError):
        return default


def _cfg_float(config: dict[str, Any], key: str, default: float) -> float:
    try:
        return float(config[key])
    except (KeyError, TypeError, ValueError):
        return default


def _cfg_str(config: dict[str, Any], key: str, default: str) -> str:
    value = config.get(key, default)
    return value.strip() if isinstance(value, str) and value.strip() else default


def _cfg_terms(config: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = config.get(key)
    if isinstance(value, (list, tuple)) and value:
        terms = tuple(str(v) for v in value if str(v).strip())
        if terms:
            return terms
    return default


# -- phrase machinery --------------------------------------------------------


def _term_pattern(term: str) -> str:
    """Word-boundaried pattern for one literal cue, tolerant of spacing.

    Tolerant of the apostrophe too: "dont" is typed as often as "don't", and a
    rule that only knew one of them would find half the corrections.
    """
    body = r"\s+".join(re.escape(part).replace("'", "'?") for part in term.lower().split())
    tail = r"(?![a-z0-9])" if term[-1].isalnum() else ""
    return f"(?:{body}{tail})"


def _compile_terms(terms: Iterable[str]) -> re.Pattern[str]:
    """One alternation over literal cues, longest first so "make sure to" wins."""
    ordered = sorted({t.lower().strip() for t in terms if t and t.strip()}, key=len, reverse=True)
    if not ordered:
        return re.compile(r"(?!x)x")  # matches nothing, and never None-checks downstream
    body = "|".join(_term_pattern(t) for t in ordered)
    return re.compile(rf"(?<![a-z0-9])(?:{body})")


_NEGATION_RE = _compile_terms(_NEGATION_CUES)
_LEAD_FILLER_RE = re.compile(
    r"^(?:"
    + "|".join(_term_pattern(t) for t in sorted(_LEAD_FILLER, key=len, reverse=True))
    + rf")[{re.escape(_STRIP_CHARS)}]*"
)


def flatten(text: str) -> str:
    return " ".join((text or "").split())


def strip_lead_filler(text: str) -> str:
    """Drop leading politeness and modality, repeatedly and boundedly."""
    out = text.lstrip(_STRIP_CHARS)
    for _ in range(4):  # "please always make sure you ..." is about as deep as this gets
        stripped = _LEAD_FILLER_RE.sub("", out, count=1)
        if stripped == out:
            break
        out = stripped
    return out.strip()


def stem_token(token: str) -> str:
    """Strip one inflectional suffix. Deliberately crude, deliberately local.

    A real stemmer is a dependency and a rabbit hole; all that is needed here is
    for "committing", "commits" and "commit" to land on one bucket. Tokens are
    left alone when they are short, non-alphabetic (paths, flags, identifiers)
    or would be stemmed down to a stub.
    """
    if len(token) <= 4 or not token.isalpha():
        return token
    for suffix in ("ing", "ed"):
        if token.endswith(suffix):
            base = _DOUBLED_END_RE.sub(r"\1", token[: -len(suffix)])
            return base if len(base) >= _MIN_STEM_CHARS else token
    if token.endswith("s") and not token.endswith(("ss", "us", "is")):
        base = token[:-1]
        return base if len(base) >= _MIN_STEM_CHARS else token
    return token


def normalize_instruction(text: str, max_words: int = 40) -> str:
    """The grouping key for an instruction: what it asks, not how it was typed.

    Negation is a prefix rather than a token because the shared stopword list
    swallows "not" and tokenizes "don't" into two stopwords. Without the prefix
    "don't force push" and "force push" would share a fingerprint - and the loop
    would then write one of them into the user's memory file having counted the
    other.
    """
    flat = flatten(text).lower()
    if not flat:
        return ""
    negated = bool(_NEGATION_RE.search(flat))
    phrase = normalize_phrase(strip_lead_filler(flat), max_words=max_words)
    stems = [stem_token(t) for t in phrase.split() if t not in _NEGATION_TOKENS]
    if not stems:
        return ""
    return ("not " if negated else "") + " ".join(stems)


def content_words(text: str) -> set[str]:
    """Content words for similarity: stopwords dropped, inflections collapsed.

    Stemmed for the same reason `normalize_instruction` stems - and it must be
    the *same* reason, or the two halves of this module disagree about whether
    two prompts are the same thought. Unstemmed, "run the tests before pushing"
    and "run tests before you push" overlap on two words out of five and score
    0.4, which is under every sensible threshold; stemmed they score 0.75 and
    are recognised as the restatement they obviously are.
    """
    return {stem_token(w) for w in words(text) if len(w) > 1 and w not in STOPWORDS}


def _representative(signals: list[Signal]) -> str:
    """The phrasing the user reached for most often, shortest wins ties."""
    counts = Counter(flatten(s.text) for s in signals)
    return max(counts.items(), key=lambda kv: (kv[1], -len(kv[0])))[0]


def _spread_evidence(signals: list[Signal], limit: int) -> list[Evidence]:
    """One quote per session, earliest first.

    Four quotes from four days is an argument; four quotes from one afternoon
    is the same quote four times.
    """
    seen: set[str] = set()
    out: list[Evidence] = []
    for sig in sorted(signals, key=lambda s: (s.ts, s.ordinal)):
        bucket = sig.session or sig.day
        if bucket in seen:
            continue
        seen.add(bucket)
        out.append(Evidence.from_signal(sig))
        if len(out) >= limit:
            break
    return out


def _occasions(signals: list[Signal]) -> tuple[set[str], set[str]]:
    return ({s.session or s.day for s in signals}, {s.day for s in signals})


# -- the shared memory-file proposal -----------------------------------------


def _is_safe_relpath(relpath: str) -> bool:
    path = Path(relpath)
    return bool(relpath) and not path.is_absolute() and ".." not in path.parts


def _bullet(instruction: str, max_chars: int = 500) -> str:
    """One markdown list item, or "" for something not worth writing down."""
    body = flatten(instruction).lstrip("-*+ ").strip()
    if not body or len(body) > max_chars:
        return ""
    if body[-1] not in ".!?:;":
        body += "."
    return f"- {body[0].upper()}{body[1:]}"


def already_documented(existing: str, instruction: str) -> bool:
    """Whether the file already says this, verbatim or in another phrasing.

    Both checks matter: the substring catches a line the loop wrote last month,
    the normalized comparison catches the user having written the same rule in
    their own words - and re-proposing something the user already did by hand is
    how an assistant teaches people to stop reading its suggestions.
    """
    flat = flatten(instruction).lower().rstrip(".")
    if not flat:
        return True
    if flat in flatten(existing).lower():
        return True
    target = normalize_instruction(instruction)
    if not target:
        return True
    for line in existing.splitlines():
        candidate = line.strip().lstrip("-*+> ").strip()
        if candidate and normalize_instruction(candidate) == target:
            return True
    return False


def memory_file_proposals(
    finding: Finding,
    ctx: DetectContext,
    *,
    instruction: str,
    memory_file: str,
    heading: str,
    title: str,
    rationale: str,
    min_risk: str = "safe",
    impact: float = 0.5,
) -> list[Proposal]:
    """Propose one bullet in the project memory file.

    Shared by every rule in this module on purpose. The risk tier of "write a
    line into the file the user reads every day" is a property of the *file*,
    not of the rule that found the line, so deciding it in three places is three
    chances to decide it differently:

    * absent file  -> `create`, risk `safe`  - nothing can be lost;
    * present file -> `ensure_section`, risk `review` - it is the user's file;
    * anything credential-shaped -> `manual`, always.
    """
    entry = _bullet(instruction)
    if not entry:
        return []
    if not _is_safe_relpath(memory_file):
        log.warn("memory_file is not a workspace-relative path", path=memory_file)
        return []

    existing = ctx.read_text(memory_file)
    if existing is not None and already_documented(existing, instruction):
        log.debug("instruction already documented", path=memory_file, rule=finding.rule_id)
        return []

    risk = "review" if existing is not None else "safe"
    if _CREDENTIAL_RE.search(instruction):
        # Never automate a file edit that mentions a credential, even a
        # redacted one: the correct action is a human deciding where it goes.
        risk = "manual"
        rationale += " Mentions a credential, so this is left entirely to you."
    if RISK_ORDER.get(risk, 2) < RISK_ORDER.get(min_risk, 2):
        risk = min_risk

    note = f"{finding.rule_id}: {finding.key[:80]}"
    if existing is None:
        edit = EditOp(
            path=memory_file,
            op="create",
            text=MEMORY_HEADER + heading + "\n\n" + entry + "\n",
            note=note,
        )
    else:
        edit = EditOp(
            path=memory_file,
            op="ensure_section",
            anchor=heading,
            text=entry + "\n",
            note=note,
        )
    return [
        Proposal(
            finding=finding,
            title=title,
            rationale=rationale,
            edits=[edit],
            risk=risk,
            impact=round(max(0.0, min(1.0, impact)), 3),
            effort=0.1,  # one line in one file
        )
    ]


# -- rules -------------------------------------------------------------------


@register
class FrictionRepeatedInstruction(Detector):
    """An instruction given in N separate sessions is a convention, not a request.

    Repeats *inside* one session are somebody rephrasing themselves and belong
    to `friction.reformulation`; only repeats across sessions or days prove the
    preference outlived the conversation that produced it.
    """

    rule_id = "friction.repeated_instruction"
    title = "Standing instruction repeated across sessions"
    severity = "high"
    consumes = (KIND_PROMPT,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.min_sessions = _cfg_int(self.config, "min_sessions", 3)
        self.min_words = _cfg_int(self.config, "min_words", 3)
        self.max_words = _cfg_int(self.config, "max_words", 60)
        self.short_max_words = _cfg_int(self.config, "short_max_words", 12)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 4)
        self.memory_file = _cfg_str(self.config, "memory_file", DEFAULT_MEMORY_FILE)
        self.section = _cfg_str(self.config, "section", CONVENTIONS_HEADING)
        self.cue_re = _compile_terms(_cfg_terms(self.config, "cues", DEFAULT_INSTRUCTION_CUES))

    # -- detection -----------------------------------------------------------

    def instruction_cue(self, text: str) -> str:
        """The cue that makes this prompt an instruction, "" when it is not.

        Returns "short" for the cue-less case: a brief, verb-first, non-question
        prompt ("run make test before you commit") is an instruction even though
        it is too polite to say "always".
        """
        lower = flatten(text).lower()
        if not lower or lower.startswith("/") or "```" in lower:
            return ""  # slash commands and pasted code are not preferences
        tokens = words(lower)
        if not (self.min_words <= len(tokens) <= self.max_words):
            return ""
        match = self.cue_re.search(lower)
        if match:
            return match.group(0).strip()
        if (
            len(tokens) <= self.short_max_words
            and not lower.endswith("?")
            and tokens[0].isalpha()
            and tokens[0] not in _QUESTION_OPENERS
        ):
            return "short"
        return ""

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        groups: dict[str, list[Signal]] = {}
        cues: dict[str, str] = {}
        for sig in ctx.by_kind(KIND_PROMPT):
            if sig.actor == ACTOR_ASSISTANT:
                continue
            cue = self.instruction_cue(sig.text)
            if not cue:
                continue
            key = normalize_instruction(sig.text)
            if not key:
                continue
            groups.setdefault(key, []).append(sig)
            if cue != "short":
                cues.setdefault(key, cue)

        for key, signals in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            sessions, days = _occasions(signals)
            occasions = max(len(sessions), len(days))
            if occasions < self.min_sessions:
                continue
            yield self._finding(key, signals, occasions, sessions, days, cues.get(key, ""))

    def _finding(
        self,
        key: str,
        signals: list[Signal],
        occasions: int,
        sessions: set[str],
        days: set[str],
        cue: str,
    ) -> Finding:
        instruction = _representative(signals)
        confidence = 0.5 + 0.1 * (occasions - self.min_sessions) + (0.05 if cue else 0.0)
        return Finding(
            rule_id=self.rule_id,
            title=f'Repeated instruction: "{instruction[:80]}"',
            detail=(
                f"Given {len(signals)} times across {len(sessions)} sessions and "
                f"{len(days)} days: \"{instruction}\". A preference retyped every day is a "
                f"project convention that has not been written down; {self.memory_file} is "
                f"where it stops being retyped."
            ),
            severity=self.severity,
            confidence=round(min(0.95, confidence), 3),
            key=key,
            targets=[self.memory_file],
            evidence=_spread_evidence(signals, self.max_evidence),
            tags=["friction", "memory", "convention"],
            metadata={
                "instruction": instruction,
                "normalized": key,
                "occurrences": len(signals),
                "sessions": len(sessions),
                "days": len(days),
                "cue": cue,
            },
        )

    # -- proposal ------------------------------------------------------------

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        instruction = str(finding.metadata.get("instruction", "")).strip()
        if not instruction:
            return ()
        occasions = max(
            int(finding.metadata.get("sessions", 0) or 0),
            int(finding.metadata.get("days", 0) or 0),
        )
        return memory_file_proposals(
            finding,
            ctx,
            instruction=instruction,
            memory_file=self.memory_file,
            heading=self.section,
            title=f"Record a standing convention in {self.memory_file}",
            rationale=(
                f"Typed in {occasions} separate sessions. Written down once, it stops "
                f"being typed at all - and it applies to work you have not started yet."
            ),
            impact=min(0.9, 0.4 + 0.1 * occasions),
        )


@register
class FrictionReformulation(Detector):
    """Consecutive near-identical prompts: the first attempt did not land.

    The interesting artifact is the *last* phrasing - the one that finally
    worked - which is why the finding is keyed on it and why a long run of
    restatements is worth writing down while a single retry is only worth
    reporting.
    """

    rule_id = "friction.reformulation"
    title = "Prompt restated because the first attempt did not land"
    severity = "medium"
    consumes = (KIND_PROMPT,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.sim_threshold = _cfg_float(self.config, "sim_threshold", 0.6)
        self.window_s = _cfg_float(self.config, "window_s", 1800.0)
        self.min_words = _cfg_int(self.config, "min_words", 3)
        self.min_content_words = _cfg_int(self.config, "min_content_words", 2)
        self.min_attempts_for_proposal = _cfg_int(self.config, "min_attempts_for_proposal", 3)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 4)
        self.memory_file = _cfg_str(self.config, "memory_file", DEFAULT_MEMORY_FILE)
        self.section = _cfg_str(self.config, "section", CONVENTIONS_HEADING)

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        for session, signals in sorted(ctx.sessions(KIND_PROMPT).items()):
            usable = [
                (sig, cw)
                for sig in signals
                if sig.actor != ACTOR_ASSISTANT
                and len(words(sig.text)) >= self.min_words
                and len(cw := content_words(sig.text)) >= self.min_content_words
            ]
            for run, sims in self._runs(usable):
                yield self._finding(session, run, sims)

    def _runs(
        self, usable: list[tuple[Signal, set[str]]]
    ) -> Iterable[tuple[list[Signal], list[float]]]:
        """Maximal chains of consecutive similar prompts.

        A chain, not a pair: three restatements of one request are one problem
        reported once, and emitting a finding per adjacent pair would report the
        middle prompt twice and score the worst sessions the loudest.
        """
        run: list[Signal] = []
        sims: list[float] = []
        prev: tuple[Signal, set[str]] | None = None
        for sig, cw in usable:
            if prev is not None:
                similarity = jaccard(prev[1], cw)
                gap = sig.ts - prev[0].ts
                if similarity >= self.sim_threshold and 0 <= gap <= self.window_s:
                    if not run:
                        run = [prev[0]]
                        sims = []
                    run.append(sig)
                    sims.append(similarity)
                    prev = (sig, cw)
                    continue
            if len(run) >= 2:
                yield run, sims
            run, sims = [], []
            prev = (sig, cw)
        if len(run) >= 2:
            yield run, sims

    def _finding(self, session: str, run: list[Signal], sims: list[float]) -> Finding:
        final = run[-1]
        restatements = len(run) - 1
        mean_sim = sum(sims) / len(sims) if sims else 0.0
        key = normalize_instruction(final.text) or normalize_instruction(run[0].text)
        span = round(max(0.0, final.ts - run[0].ts), 1)
        confidence = 0.35 + 0.35 * mean_sim + 0.1 * (restatements - 1)
        return Finding(
            rule_id=self.rule_id,
            title=f'Asked {len(run)} times in one session: "{flatten(final.text)[:70]}"',
            detail=(
                f"{len(run)} near-identical prompts (mean similarity {mean_sim:.2f}) within "
                f"{span:.0f}s of each other. The first phrasing did not land; the one that "
                f'did was: "{flatten(final.text)}"'
            ),
            severity=self.severity,
            confidence=round(min(0.9, confidence), 3),
            key=key or f"session:{session}",
            targets=[self.memory_file],
            evidence=[Evidence.from_signal(s) for s in run[: self.max_evidence]],
            tags=["friction", "reformulation"],
            metadata={
                "session": session,
                "attempts": len(run),
                "restatements": restatements,
                "similarity": round(mean_sim, 3),
                "span_s": span,
                "accepted_phrasing": flatten(final.text),
            },
        )

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        attempts = int(finding.metadata.get("attempts", 0) or 0)
        if attempts < self.min_attempts_for_proposal:
            # One retry is noise worth reporting and not worth acting on: the
            # phrasing that worked has not proven it will be needed again.
            return ()
        phrasing = str(finding.metadata.get("accepted_phrasing", "")).strip()
        if not phrasing:
            return ()
        return memory_file_proposals(
            finding,
            ctx,
            instruction=phrasing,
            memory_file=self.memory_file,
            heading=self.section,
            title=f"Record the phrasing that finally worked in {self.memory_file}",
            rationale=(
                f"Asked {attempts} times before it landed. Recording the phrasing that "
                f"worked means the next attempt starts from it."
            ),
            # Always `review`: this is a guess about what the user meant, not an
            # instruction they ever stated in as many words.
            min_risk="review",
            impact=min(0.75, 0.3 + 0.1 * attempts),
        )


@register
class FrictionCorrection(Detector):
    """A prompt that repairs the previous answer states a preference we lacked.

    Corrections are the cheapest supervision in the whole system: the user has
    already done the work of noticing the mistake and saying what should have
    happened. All this rule has to do is not lose it - strip the annoyance off
    the front, group the repeats, and put the remainder somewhere it will be
    read before the same mistake is made again.
    """

    rule_id = "friction.correction"
    title = "Correction of a previous answer"
    severity = "high"
    consumes = (KIND_PROMPT, KIND_REPLY)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.min_count = _cfg_int(self.config, "min_count", 1)
        self.escalate_at = _cfg_int(self.config, "escalate_at", 2)
        self.min_instruction_words = _cfg_int(self.config, "min_instruction_words", 2)
        self.max_words = _cfg_int(self.config, "max_words", 80)
        self.marker_window_chars = _cfg_int(self.config, "marker_window_chars", 120)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 4)
        self.memory_file = _cfg_str(self.config, "memory_file", DEFAULT_MEMORY_FILE)
        self.section = _cfg_str(self.config, "section", CORRECTIONS_HEADING)
        self.marker_re = _compile_terms(
            _cfg_terms(self.config, "markers", DEFAULT_CORRECTION_MARKERS)
        )

    # -- extraction ----------------------------------------------------------

    def marker_in(self, text: str) -> tuple[str, bool] | None:
        """(marker, opened_with_it) for a corrective prompt, else None.

        The marker has to be near the front. "wrong" in the fifth paragraph of a
        design brief is a word; "wrong" in the first clause after an answer is a
        verdict on that answer.
        """
        lower = flatten(text).lower()
        if not lower:
            return None
        match = self.marker_re.search(lower[: max(1, self.marker_window_chars)])
        if not match:
            return None
        return match.group(0).strip(), match.start() == 0

    def instruction_from(self, text: str) -> str:
        """The durable half of a correction: the marker and the complaint removed.

        "No, that's wrong. Use ruff for linting." carries exactly one thing worth
        keeping, and it is not the first four words. Clauses are dropped from the
        front while they say nothing once their markers are gone; everything from
        the first substantive clause onward is kept, because that is where the
        instruction starts and it may well run to the end of the message.
        """
        kept: list[str] = []
        for clause in _CLAUSE_SPLIT_RE.split(text):
            clause = flatten(clause)
            if not clause:
                continue
            if kept:
                kept.append(clause)
                continue
            body = self._strip_marker_head(clause)
            if len(content_words(body)) >= self.min_instruction_words:
                kept.append(body)
        return flatten(" ".join(kept))

    def _strip_marker_head(self, clause: str) -> str:
        out = clause.strip(_STRIP_CHARS)
        for _ in range(4):
            match = self.marker_re.match(out.lower())
            if not match:
                break
            out = out[match.end() :].lstrip(_STRIP_CHARS)
        return out.strip()

    # -- detection -----------------------------------------------------------

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        groups: dict[str, list[tuple[Signal, Signal | None, str, bool]]] = {}
        for _session, signals in sorted(ctx.sessions(KIND_PROMPT, KIND_REPLY).items()):
            previous: Signal | None = None
            for sig in signals:
                if sig.kind != KIND_PROMPT or sig.actor == ACTOR_ASSISTANT:
                    previous = sig
                    continue
                answered = previous is not None and previous.kind == KIND_REPLY
                corrected = previous if answered else None
                previous = sig
                if corrected is None:
                    continue  # nothing was said yet, so nothing is being corrected
                if len(words(sig.text)) > self.max_words:
                    continue
                marker = self.marker_in(sig.text)
                if marker is None:
                    continue
                instruction = self.instruction_from(sig.text)
                if len(content_words(instruction)) < self.min_instruction_words:
                    continue  # pure annoyance, no preference to learn from
                key = normalize_instruction(instruction)
                if not key:
                    continue
                groups.setdefault(key, []).append((sig, corrected, instruction, marker[1]))

        for key, hits in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            if len(hits) < self.min_count:
                continue
            yield self._finding(key, hits)

    def _finding(
        self, key: str, hits: list[tuple[Signal, Signal | None, str, bool]]
    ) -> Finding:
        signals = [h[0] for h in hits]
        instruction = Counter(h[2] for h in hits).most_common(1)[0][0]
        sessions, days = _occasions(signals)
        opened = any(h[3] for h in hits)
        confidence = 0.45 + 0.15 * (len(hits) - 1) + (0.05 if opened else 0.0)
        evidence = _spread_evidence(signals, max(1, self.max_evidence - 1))
        first_reply = hits[0][1]
        if first_reply is not None:
            evidence.append(
                Evidence.from_signal(first_reply, quote=f"corrected reply: {first_reply.preview}")
            )
        return Finding(
            rule_id=self.rule_id,
            title=f'Correction: "{instruction[:80]}"',
            detail=(
                f"Corrected a previous answer {len(hits)} times across {len(sessions)} "
                f'sessions: "{instruction}". A correction is a preference the system did '
                f"not have; recorded once in {self.memory_file}, it does not have to be "
                f"given again."
            ),
            severity=self.severity if len(hits) >= self.escalate_at else "medium",
            confidence=round(min(0.9, confidence), 3),
            key=key,
            targets=[self.memory_file],
            evidence=evidence,
            tags=["friction", "correction", "memory"],
            metadata={
                "instruction": instruction,
                "normalized": key,
                "occurrences": len(hits),
                "sessions": len(sessions),
                "days": len(days),
                "opened_with_marker": opened,
            },
        )

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        instruction = str(finding.metadata.get("instruction", "")).strip()
        if not instruction:
            return ()
        count = int(finding.metadata.get("occurrences", 1) or 1)
        return memory_file_proposals(
            finding,
            ctx,
            instruction=instruction,
            memory_file=self.memory_file,
            heading=self.section,
            title=f"Record a correction in {self.memory_file}",
            rationale=(
                f"Stated as a correction {count} time(s) after an answer went the other "
                f"way. Recording it is the difference between correcting it once and "
                f"correcting it every time."
            ),
            impact=min(0.9, 0.5 + 0.1 * count),
        )
