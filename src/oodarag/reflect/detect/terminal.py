"""Rules that read the shell history for work a file should be doing.

A terminal is where intent goes to die. The command that finally worked - the
one with the right four flags, in the right order, against the right path -
exists for as long as the scrollback does and then has to be derived again from
memory. Every night this module reads back what was actually typed and looks
for the three shapes that waste takes:

* a burst of near-identical commands in one session, which is somebody
  bisecting their way to the correct flags. The last one in the burst is the
  answer, and it is the only line of that burst worth keeping;
* one command typed byte-for-byte the same, five times, across several days -
  not a struggle but a routine, and a routine that lives in muscle memory is a
  routine nobody else on the project can run;
* a command followed immediately by its own undo, or by itself with `sudo` in
  front, which is friction of a kind no edit can fix.

The first two end in the same artifact: a named `make` target. That choice is
deliberate. The loop must not rewrite a command - a shell string is program
semantics it has no business interpreting - but it can copy one verbatim under
a name, which turns a thing you remember into a thing you invoke.

Three design positions cost real code here.

**Near-identical and byte-identical are different findings with different
evidence.** Folding them into one "repeated command" rule would report the
struggle and the routine as the same event, and the struggle's whole value is
in the *difference* between attempt one and attempt four.

**A Makefile is the user's file, so touching one is never `safe`.** Creating a
Makefile that does not exist cannot destroy information; adding a target to one
that does exist is an edit to a file whose contents someone depends on, and it
goes through review. The recipe is also copied with `$` doubled and refused
outright if it contains a `#`, because make would silently change what the
command means, and a wrong recipe is worse than no target.

**Exit codes are usually not there.** Shell history files record what was
typed, not what happened. Rather than emit nothing for the common case,
`terminal.failure_signature` falls back on a textual proxy - a command undone
or re-run under `sudo` - and reports it as an observation with no proposal
attached, because the fix for "this needed root" is a decision, not an edit.
"""

from __future__ import annotations

import re
import shlex
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.reflect.detect.base import DetectContext, Detector, jaccard, register
from oodarag.reflect.models import (
    KIND_COMMAND,
    EditOp,
    Evidence,
    Finding,
    Proposal,
    Signal,
)
from oodarag.util.logging import get_logger

log = get_logger("reflect.terminal")

#: Where derived targets are written. Overridable per rule, because a project
#: may keep its entry points in `Makefile.local` or somewhere stranger.
DEFAULT_MAKEFILE = "Makefile"

#: The heading the loop owns inside a Makefile. Owning a heading is what makes
#: appending to somebody else's build file additive rather than an edit of it,
#: and it gives every later night a stable anchor to append under.
MAKEFILE_SECTION = "# --- targets recorded by the nightly reflect loop ---"

MAKEFILE_HEADER = (
    "# Makefile started by the nightly reflect loop.\n"
    "#\n"
    "# Every target below is a command that was typed by hand more than once,\n"
    "# copied verbatim under a name. Rename, edit or delete freely.\n"
    "\n"
)

#: argv0s too cheap to be worth automating. Running `ls` forty times is not a
#: workflow with a missing name, it is how a terminal is used. The two-token
#: git entries are matched against the first *two* tokens, since `git` itself
#: is very much worth automating and `git status` is not.
DEFAULT_IGNORE_ARGV0S = (
    "cd",
    "ls",
    "ll",
    "pwd",
    "clear",
    "exit",
    "cat",
    "less",
    "vim",
    "nvim",
    "man",
    "echo",
    "history",
    "which",
    "top",
    "htop",
    "git status",
    "git log",
    "git diff",
)

#: Commands that only ever appear after something went wrong. Matched on token
#: prefixes, so `kill` does not match `killall` and `git reset` catches every
#: flavour of reset without enumerating them.
DEFAULT_UNDO_MARKERS = (
    "rm -rf",
    "git checkout --",
    "git reset",
    "kill",
    "pkill",
)

#: Wrappers that say how a command is run, not what it is. Skipped when naming
#: a target so `sudo docker compose up` becomes `docker-compose`, not `sudo-docker`.
_RUNNER_PREFIXES = frozenset({"sudo", "command", "env", "time", "nohup", "exec"})

_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_SLUG_RE = re.compile(r"[^a-z0-9]+")
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

#: Anything credential-shaped is never proposed as an automatic edit, whatever
#: the risk tier would otherwise have been. A redaction marker counts: the
#: source stripped a live token out of this line, so the line is about a secret
#: even though the secret itself is gone.
_CREDENTIAL_RE = re.compile(
    r"(?i)(?:<redacted|\b(?:api[_-]?key|secret|password|passwd|token|credential"
    r"|private[_-]?key|\.env)\b)"
)


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
    if isinstance(value, (list, tuple)):
        terms = tuple(str(v).strip().lower() for v in value if str(v).strip())
        if terms or value == []:
            # An explicitly empty list means "ignore nothing", which is a
            # legitimate thing to configure and must not silently reset.
            return terms
    return default


# -- command shapes ----------------------------------------------------------


def flatten(text: str) -> str:
    """Whitespace-normalized command text. This is the byte-identity key."""
    return " ".join((text or "").split())


def tokens(text: str) -> list[str]:
    """Shell-aware split, degrading to whitespace splitting.

    `shlex` is what makes `git commit -m "wip fix"` three arguments instead of
    five, which matters for similarity: quoted prose would otherwise dominate
    the token set of every commit command. Unbalanced quotes are common in
    history files (a truncated line, a multi-line entry) and are not an error.
    """
    flat = flatten(text)
    if not flat:
        return []
    try:
        parts = shlex.split(flat)
    except ValueError:
        parts = flat.split()
    return [p for p in parts if p]


def effective_tokens(text: str) -> list[str]:
    """Tokens with leading `FOO=bar` environment assignments dropped."""
    parts = tokens(text)
    index = 0
    while index < len(parts) and _ENV_ASSIGN_RE.match(parts[index]):
        index += 1
    return parts[index:]


def argv0(text: str) -> str:
    """The program being run, ignoring environment assignments in front of it."""
    parts = effective_tokens(text)
    return parts[0].lower() if parts else ""


def is_ignored(text: str, ignore: frozenset[str]) -> bool:
    """Whether this command is on the do-not-automate list.

    Both the argv0 and the first two tokens are checked, so an ignore list can
    name a whole program (`ls`) or one subcommand of an interesting one
    (`git status`) without a second config key.
    """
    parts = [p.lower() for p in effective_tokens(text)]
    if not parts:
        return True
    return parts[0] in ignore or " ".join(parts[:2]) in ignore


def _leaf(token: str) -> str:
    """The nameable part of an argument: basename, extension removed."""
    leaf = token.rstrip("/").rsplit("/", 1)[-1]
    return leaf.split(".", 1)[0] or leaf


def slug(text: str) -> str:
    """Lowercase, [a-z0-9-] only. Anything else becomes a single hyphen."""
    return _SLUG_RE.sub("-", text.lower()).strip("-")


def derive_target_name(command: str, max_len: int = 40) -> str:
    """A make target name for a command: program plus one distinguishing token.

    `pytest -q tests/unit` becomes `pytest-tests`, not `pytest`, because a name
    that only says the program collides with the next finding about the same
    program and tells the reader nothing about which invocation it wrapped.
    Non-flag arguments are preferred over flags for that second half, since a
    subcommand or a path says far more than `-q` does.
    """
    parts = effective_tokens(command)
    while parts and parts[0].lower() in _RUNNER_PREFIXES:
        parts = parts[1:]
    if not parts:
        return ""
    base = slug(_leaf(parts[0]))
    if not base:
        return ""
    rest = parts[1:]
    ordered = [t for t in rest if not t.startswith("-")] + [t for t in rest if t.startswith("-")]
    distinguishing = ""
    for token in ordered:
        candidate = slug(_leaf(token.lstrip("-")))
        if candidate and candidate != base and not candidate.isdigit():
            distinguishing = candidate
            break
    name = f"{base}-{distinguishing}" if distinguishing else base
    return name[:max_len].strip("-")


def makefile_has_target(text: str, name: str) -> bool:
    """Whether the Makefile already defines this target.

    Distinguishes a rule (`build:`) from an assignment (`build := ...`), which
    otherwise look identical to a line-start match and would make the loop
    propose a target that shadows one of the user's variables.
    """
    if not name:
        return False
    pattern = re.compile(rf"^{re.escape(name)}[ \t]*:+[ \t]*", re.MULTILINE)
    for match in pattern.finditer(text):
        if text[match.end() : match.end() + 1] != "=":
            return True
    return False


# -- the shared Makefile proposal --------------------------------------------


def _is_safe_relpath(relpath: str) -> bool:
    path = Path(relpath)
    return bool(relpath) and not path.is_absolute() and ".." not in path.parts


def _recipe_from(command: str) -> str:
    """A command as a make recipe line, or "" when it cannot be one honestly.

    `$` is doubled because make expands single ones, so `for f in *.py; do echo
    $f; done` copied verbatim would run with `$f` already eaten. `#` is refused
    rather than escaped: make treats it as a comment even inside a recipe, and
    the ways to smuggle one through change what the shell sees. A recipe the
    loop is not certain of is a recipe it should not write.
    """
    recipe = flatten(command)
    if not recipe or "#" in recipe or _CONTROL_RE.search(recipe):
        return ""
    return recipe.replace("$", "$$")


def _target_block(name: str, recipe: str, comment: str) -> str:
    lines = []
    if comment:
        lines.append(f"# {flatten(comment)[:160]}")
    lines.extend([f".PHONY: {name}", f"{name}:", f"\t{recipe}"])
    return "\n".join(lines) + "\n"


def _makefile_anchor(existing: str) -> str:
    """Where a new target goes in a Makefile that already exists.

    The loop's own heading first, so every night's additions stay together and
    a reader can see at a glance which targets they did not write. Failing
    that, the project's own `.PHONY` line - matched whole, because a Makefile
    with several of them should not have the loop guessing at which one.
    """
    if MAKEFILE_SECTION in existing:
        return MAKEFILE_SECTION
    for line in existing.splitlines():
        if line.startswith(".PHONY"):
            return line.rstrip()
    return MAKEFILE_SECTION


def makefile_target_proposals(
    finding: Finding,
    ctx: DetectContext,
    *,
    command: str,
    makefile: str,
    title: str,
    rationale: str,
    comment: str = "",
    impact: float = 0.5,
) -> list[Proposal]:
    """Propose one make target wrapping `command`, or nothing.

    Shared by both retyping rules on purpose. The risk of "write a line into
    the file that says how this project is built" is a property of the *file*,
    not of the rule that noticed the command, so deciding it twice is two
    chances to decide it differently:

    * absent Makefile  -> `create`, risk `safe`   - nothing can be lost;
    * present Makefile -> `ensure_section`, risk `review` - it is theirs;
    * anything credential-shaped -> `manual`, always.

    Returns [] rather than a duplicate when the target name is taken or the
    command already appears in the file: re-proposing something the user has
    already done by hand is how a report teaches people to stop reading it.
    """
    if not _is_safe_relpath(makefile):
        log.warn("makefile is not a workspace-relative path", path=makefile)
        return []
    recipe = _recipe_from(command)
    if not recipe:
        log.debug("command cannot be expressed as a recipe", rule=finding.rule_id)
        return []
    if argv0(command) == "make":
        return []  # wrapping a make target in a make target achieves nothing
    name = derive_target_name(command)
    if not name:
        return []

    existing = ctx.read_text(makefile)
    if existing is not None:
        if makefile_has_target(existing, name):
            log.debug("makefile target already exists", path=makefile, target=name)
            return []
        if flatten(command) in existing:
            log.debug("command already scripted", path=makefile, target=name)
            return []

    risk = "review" if existing is not None else "safe"
    if _CREDENTIAL_RE.search(command):
        # Never automate an edit that writes a credential-shaped string into a
        # file that gets committed. The right home for it is a decision.
        risk = "manual"
        rationale += " Mentions a credential, so this is left entirely to you."

    note = f"{finding.rule_id}: {name}"
    if existing is None:
        edit = EditOp(
            path=makefile,
            op="create",
            text=MAKEFILE_HEADER + MAKEFILE_SECTION + "\n\n" + _target_block(name, recipe, comment),
            note=note,
        )
    else:
        edit = EditOp(
            path=makefile,
            op="ensure_section",
            anchor=_makefile_anchor(existing),
            text=_target_block(name, recipe, comment),
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
            effort=0.15,  # four lines in one file
        )
    ]


# -- evidence helpers --------------------------------------------------------


def _spread_evidence(signals: list[Signal], limit: int) -> list[Evidence]:
    """One quote per day, earliest first.

    Five quotes from five days is an argument that this is a routine; five
    quotes from one afternoon is the same quote five times.
    """
    seen: set[str] = set()
    out: list[Evidence] = []
    for sig in sorted(signals, key=lambda s: (s.ts, s.ordinal)):
        if sig.day in seen:
            continue
        seen.add(sig.day)
        out.append(Evidence.from_signal(sig))
        if len(out) >= limit:
            break
    return out


def _sequence_evidence(run: list[Signal], limit: int) -> list[Evidence]:
    """The attempt sequence, keeping the last one whatever the cap.

    The final attempt is the whole point of the finding - it is the command
    that worked - so a long run drops from the middle, never from the end.
    """
    if limit <= 0:
        return []
    numbered = list(enumerate(run, start=1))
    if len(numbered) > limit:
        numbered = numbered[: limit - 1] + numbered[-1:]
    total = len(run)
    return [
        Evidence.from_signal(sig, quote=f"attempt {index}/{total}: {flatten(sig.text)[:160]}")
        for index, sig in numbered
    ]


def _occasions(signals: list[Signal]) -> tuple[set[str], set[str]]:
    return ({s.session or s.day for s in signals}, {s.day for s in signals})


# -- rules -------------------------------------------------------------------


@dataclass(slots=True)
class _Attempt:
    """One command, pre-tokenized. Built once per signal, compared many times."""

    signal: Signal
    text: str
    argv0: str
    tokens: frozenset[str] = field(default_factory=frozenset)


@register
class TerminalRetryLoop(Detector):
    """A burst of near-identical commands is somebody deriving flags by hand.

    Byte-identical repeats are deliberately *not* part of a run: re-running the
    same command is waiting for something to change, which is a different
    problem and belongs to `terminal.repeated_command`. What this rule looks
    for is the shape where each attempt differs slightly from the last, because
    that difference is the user searching, and the search terminates in an
    answer worth keeping.
    """

    rule_id = "terminal.retry_loop"
    title = "Command flags re-derived by hand"
    severity = "high"
    consumes = (KIND_COMMAND,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.min_attempts = max(2, _cfg_int(self.config, "min_attempts", 3))
        self.sim_threshold = _cfg_float(self.config, "sim_threshold", 0.6)
        self.max_gap_s = _cfg_float(self.config, "max_gap_s", 900.0)
        self.min_tokens = _cfg_int(self.config, "min_tokens", 2)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 6)
        self.makefile = _cfg_str(self.config, "makefile", DEFAULT_MAKEFILE)
        # Ignored here as well as in `repeated_command`: a make target that
        # wraps `cd` or `vim` is not a fix, however hard the flags were.
        self.ignore = frozenset(_cfg_terms(self.config, "ignore", DEFAULT_IGNORE_ARGV0S))

    # -- detection -----------------------------------------------------------

    def _attempts(self, signals: list[Signal]) -> list[_Attempt]:
        out: list[_Attempt] = []
        for sig in signals:
            parts = effective_tokens(sig.text)
            if len(parts) < self.min_tokens or is_ignored(sig.text, self.ignore):
                continue
            out.append(
                _Attempt(
                    signal=sig,
                    text=flatten(sig.text),
                    argv0=parts[0].lower(),
                    tokens=frozenset(p.lower() for p in parts),
                )
            )
        return out

    def _links(self, prev: _Attempt, cur: _Attempt) -> float:
        """Similarity when `cur` continues `prev`'s search, 0.0 otherwise."""
        if prev.argv0 != cur.argv0 or prev.text == cur.text:
            return 0.0
        gap = cur.signal.ts - prev.signal.ts
        if gap < 0 or gap > self.max_gap_s:
            return 0.0
        similarity = jaccard(set(prev.tokens), set(cur.tokens))
        return similarity if similarity >= self.sim_threshold else 0.0

    def _runs(self, attempts: list[_Attempt]) -> Iterator[tuple[list[Signal], list[float]]]:
        """Maximal chains of consecutive linked attempts.

        A chain, not a pair: four attempts at one command are one struggle
        reported once, and emitting a finding per adjacent pair would report the
        middle attempts twice and shout loudest about the worst afternoon.
        """
        run: list[Signal] = []
        sims: list[float] = []
        prev: _Attempt | None = None
        for cur in attempts:
            if prev is not None:
                similarity = self._links(prev, cur)
                if similarity:
                    if not run:
                        run, sims = [prev.signal], []
                    run.append(cur.signal)
                    sims.append(similarity)
                    prev = cur
                    continue
            if len(run) >= self.min_attempts:
                yield run, sims
            run, sims = [], []
            prev = cur
        if len(run) >= self.min_attempts:
            yield run, sims

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        for session, signals in sorted(ctx.sessions(KIND_COMMAND).items()):
            for run, sims in self._runs(self._attempts(signals)):
                yield self._finding(session, run, sims)

    def _finding(self, session: str, run: list[Signal], sims: list[float]) -> Finding:
        settled = flatten(run[-1].text)
        program = argv0(settled)
        mean_sim = sum(sims) / len(sims) if sims else 0.0
        span = round(max(0.0, run[-1].ts - run[0].ts), 1)
        confidence = 0.4 + 0.3 * mean_sim + 0.1 * (len(run) - self.min_attempts)
        return Finding(
            rule_id=self.rule_id,
            title=f"Re-derived `{program}` flags over {len(run)} attempts",
            detail=(
                f"{len(run)} near-identical `{program}` commands in a row (mean token "
                f"similarity {mean_sim:.2f}) within {span:.0f}s. That is the invocation "
                f'being derived by hand; the one that stuck was: "{settled}". Named in '
                f"{self.makefile} it never has to be derived again."
            ),
            severity=self.severity,
            confidence=round(min(0.95, max(0.0, confidence)), 3),
            key=settled,
            targets=[self.makefile],
            evidence=_sequence_evidence(run, self.max_evidence),
            tags=["terminal", "retry", "makefile"],
            metadata={
                "session": session,
                "argv0": program,
                "attempts": len(run),
                "similarity": round(mean_sim, 3),
                "span_s": span,
                "first_command": flatten(run[0].text),
                "settled_command": settled,
            },
        )

    # -- proposal ------------------------------------------------------------

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        settled = str(finding.metadata.get("settled_command", "")).strip()
        if not settled:
            return ()
        attempts = int(finding.metadata.get("attempts", 0) or 0)
        return makefile_target_proposals(
            finding,
            ctx,
            command=settled,
            makefile=self.makefile,
            title=f"Wrap the invocation that worked in a {self.makefile} target",
            rationale=(
                f"Took {attempts} attempts to get right. A named target is the difference "
                f"between remembering the flags and running the thing."
            ),
            comment=f"settled on after {attempts} attempts by hand",
            impact=min(0.85, 0.4 + 0.1 * attempts),
        )


@register
class TerminalRepeatedCommand(Detector):
    """The same command, byte for byte, on several different days.

    The multi-day requirement is what separates a routine from an afternoon.
    Twenty runs of one command in one sitting is a debugging session and will
    not happen again; five runs spread over a week is a step in how this project
    is worked on, and a step that only exists in one person's memory is a step
    nobody else can take.
    """

    rule_id = "terminal.repeated_command"
    title = "Command retyped by hand across days"
    severity = "medium"
    consumes = (KIND_COMMAND,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.min_runs = max(2, _cfg_int(self.config, "min_runs", 5))
        self.min_days = max(1, _cfg_int(self.config, "min_days", 2))
        self.min_tokens = _cfg_int(self.config, "min_tokens", 1)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 4)
        self.makefile = _cfg_str(self.config, "makefile", DEFAULT_MAKEFILE)
        self.ignore = frozenset(_cfg_terms(self.config, "ignore", DEFAULT_IGNORE_ARGV0S))

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        groups: dict[str, list[Signal]] = {}
        for sig in ctx.by_kind(KIND_COMMAND):
            text = flatten(sig.text)
            if not text or len(effective_tokens(text)) < self.min_tokens:
                continue
            if is_ignored(text, self.ignore):
                continue
            groups.setdefault(text, []).append(sig)

        for command, signals in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            if len(signals) < self.min_runs:
                continue
            sessions, days = _occasions(signals)
            if len(days) < self.min_days:
                continue
            yield self._finding(command, signals, sessions, days)

    def _finding(
        self, command: str, signals: list[Signal], sessions: set[str], days: set[str]
    ) -> Finding:
        runs = len(signals)
        confidence = (
            0.5 + 0.05 * (runs - self.min_runs) + 0.1 * (len(days) - self.min_days)
        )
        return Finding(
            rule_id=self.rule_id,
            title=f'Retyped {runs} times: "{command[:70]}"',
            detail=(
                f'Typed by hand {runs} times across {len(days)} days: "{command}". A command '
                f"that survives that long is part of how this project is worked on, and it "
                f"is currently written down only in muscle memory."
            ),
            severity=self.severity,
            confidence=round(min(0.9, max(0.0, confidence)), 3),
            key=command,
            targets=[self.makefile],
            evidence=_spread_evidence(signals, self.max_evidence),
            tags=["terminal", "routine", "makefile"],
            metadata={
                "command": command,
                "argv0": argv0(command),
                "runs": runs,
                "days": len(days),
                "sessions": len(sessions),
            },
        )

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        command = str(finding.metadata.get("command", "")).strip() or finding.key
        if not command:
            return ()
        runs = int(finding.metadata.get("runs", 0) or 0)
        days = int(finding.metadata.get("days", 0) or 0)
        return makefile_target_proposals(
            finding,
            ctx,
            command=command,
            makefile=self.makefile,
            title=f"Name a recurring command in {self.makefile}",
            rationale=(
                f"Typed {runs} times over {days} days. Named once, it becomes something "
                f"the next person on this project can run without being told."
            ),
            comment=f"typed by hand {runs} times over {days} days",
            impact=min(0.8, 0.3 + 0.05 * runs),
        )


@dataclass(slots=True)
class _Hit:
    """One occasion on which a command appears to have gone wrong."""

    signal: Signal
    reason: str  # exit | sudo | undo
    follow: Signal | None = None
    code: int | None = None


@register
class TerminalFailureSignature(Detector):
    """Commands that keep failing, by exit status where it exists and by repair
    behaviour where it does not.

    This rule proposes nothing, and that is the point. The cause of a repeated
    failure is outside the history file - a missing dependency, a permission, a
    stale container - and the fix is a judgement about the environment. What the
    loop can honestly contribute is the observation, with the evidence attached,
    so the judgement is made from data rather than from a vague sense that
    something has been annoying lately.
    """

    rule_id = "terminal.failure_signature"
    title = "Command that repeatedly needed repair"
    severity = "medium"
    consumes = (KIND_COMMAND,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.min_failures = max(1, _cfg_int(self.config, "min_failures", 2))
        # The proxy fires at one hit by default while a real exit code needs
        # two: a non-zero status is cheap and often meaningless (grep found
        # nothing), whereas re-running something under sudo is deliberate.
        self.min_proxy_hits = max(1, _cfg_int(self.config, "min_proxy_hits", 1))
        self.max_gap_s = _cfg_float(self.config, "max_gap_s", 300.0)
        self.max_evidence = _cfg_int(self.config, "max_evidence", 4)
        self.ignore = frozenset(_cfg_terms(self.config, "ignore", DEFAULT_IGNORE_ARGV0S))
        self.undo_markers = tuple(
            tuple(m.split()) for m in _cfg_terms(self.config, "undo_markers", DEFAULT_UNDO_MARKERS)
        )

    # -- the two signatures ---------------------------------------------------

    @staticmethod
    def exit_code(sig: Signal) -> int | None:
        """The recorded exit status, or None when the source did not record one.

        Booleans are refused rather than coerced: `{"exit": False}` from a JSON
        source means "did not fail", and reading it as status 0 by accident is
        the kind of quiet type pun that makes a rule wrong once a year.
        """
        raw = sig.metadata.get("exit") if isinstance(sig.metadata, dict) else None
        if raw is None or isinstance(raw, bool):
            return None
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    def is_undo(self, text: str) -> bool:
        parts = [p.lower() for p in effective_tokens(text)]
        return any(parts[: len(marker)] == list(marker) for marker in self.undo_markers if marker)

    @staticmethod
    def is_sudo_retry(first: str, second: str) -> bool:
        """Whether `second` is `first` again, under sudo."""
        after = [p.lower() for p in effective_tokens(second)]
        if not after or after[0] != "sudo":
            return False
        after = after[1:]
        while after and after[0].startswith("-"):
            after = after[1:]  # `sudo -E make install` is still the same command
        before = [p.lower() for p in effective_tokens(first)]
        return bool(before) and after == before

    # -- detection ------------------------------------------------------------

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        hits: dict[str, list[_Hit]] = {}
        for _session, signals in sorted(ctx.sessions(KIND_COMMAND).items()):
            for index, sig in enumerate(signals):
                text = flatten(sig.text)
                if not text or is_ignored(text, self.ignore):
                    continue
                code = self.exit_code(sig)
                if code is not None:
                    if code != 0:
                        hits.setdefault(text, []).append(_Hit(sig, "exit", code=code))
                    # A source that reports status is believed: no proxy needed,
                    # and no double-counting of one failure as two.
                    continue
                follow = signals[index + 1] if index + 1 < len(signals) else None
                reason = self._proxy_reason(sig, follow)
                if reason and follow is not None:
                    hits.setdefault(text, []).append(_Hit(sig, reason, follow=follow))

        for command, group in sorted(hits.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            failures = [h for h in group if h.reason == "exit"]
            proxies = [h for h in group if h.reason != "exit"]
            if len(failures) >= self.min_failures or len(proxies) >= self.min_proxy_hits:
                yield self._finding(command, group, failures, proxies)

    def _proxy_reason(self, sig: Signal, follow: Signal | None) -> str:
        if follow is None:
            return ""
        gap = follow.ts - sig.ts
        if gap < 0 or gap > self.max_gap_s:
            return ""
        if self.is_sudo_retry(sig.text, follow.text):
            return "sudo"
        if self.is_undo(follow.text):
            return "undo"
        return ""

    def _finding(
        self, command: str, group: list[_Hit], failures: list[_Hit], proxies: list[_Hit]
    ) -> Finding:
        signals = [h.signal for h in group]
        sessions, days = _occasions(signals)
        codes = sorted({h.code for h in failures if h.code is not None})
        mode = "exit status" if failures else "repair behaviour"
        if failures:
            detail = (
                f"Exited non-zero {len(failures)} times (status {codes or 'unknown'}) across "
                f"{len(days)} days."
            )
        else:
            kinds = sorted({h.reason for h in proxies})
            detail = (
                f"Followed immediately by {' and '.join(kinds)} {len(proxies)} time(s) across "
                f"{len(days)} days. No exit status was recorded, so this is inferred from what "
                f"was typed next rather than observed."
            )
        confidence = 0.35 + 0.15 * (len(group) - 1) + (0.1 if failures else 0.0)
        return Finding(
            rule_id=self.rule_id,
            title=f'Kept going wrong: "{command[:70]}"',
            detail=(
                f'{detail} "{command}" is costing more than it looks like on the surface; '
                f"the fix is a decision about the environment, not an edit, so this is "
                f"reported and nothing is proposed."
            ),
            severity=self.severity,
            confidence=round(min(0.85, max(0.0, confidence)), 3),
            key=command,
            targets=[],
            evidence=self._evidence(group),
            tags=["terminal", "failure", mode.replace(" ", "-")],
            metadata={
                "command": command,
                "argv0": argv0(command),
                "mode": mode,
                "occurrences": len(group),
                "exit_failures": len(failures),
                "proxy_hits": len(proxies),
                "exit_codes": codes,
                "reasons": sorted({h.reason for h in group}),
                "sessions": len(sessions),
                "days": len(days),
            },
        )

    def _evidence(self, group: list[_Hit]) -> list[Evidence]:
        """The command, and for a proxy hit the thing typed straight after it.

        The follow-up is the whole argument for a proxy finding, so quoting the
        failing command alone would leave the reader unable to check the rule's
        reasoning - which is the one thing evidence is for.
        """
        out: list[Evidence] = []
        for hit in sorted(group, key=lambda h: (h.signal.ts, h.signal.ordinal)):
            if len(out) >= max(1, self.max_evidence):
                break
            if hit.reason == "exit":
                quote = f"exit {hit.code}: {flatten(hit.signal.text)[:140]}"
                out.append(Evidence.from_signal(hit.signal, quote=quote))
                continue
            out.append(Evidence.from_signal(hit.signal))
            if hit.follow is not None and len(out) < max(1, self.max_evidence):
                label = "re-run as root" if hit.reason == "sudo" else "then undone by"
                out.append(
                    Evidence.from_signal(
                        hit.follow, quote=f"{label}: {flatten(hit.follow.text)[:140]}"
                    )
                )
        return out
