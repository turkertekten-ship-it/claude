"""Rules about the health of the files themselves.

The other rule families in this package read what the user *did* - prompts
retyped, commands re-derived. This one reads what the user *left behind*,
because a working day is also a day of small deferrals: a `# FIXME` written at
18:40, a module that crossed six hundred lines without anyone deciding it
should, a new file that never acquired a test, a token pasted into a config
"just to check something". None of those is visible from inside the session
that produced it, and every one of them is trivially visible from outside it
once a night.

Four positions cost real code here.

**Findings are per file, not per occurrence.** Fourteen TODOs in one module is
one fact about one module; reported one row per marker it is fourteen rows that
push everything else off the page. The count is the finding, the first few lines
are its evidence, and a file loud enough to be a backlog rather than a note says
so by changing severity.

**The secret rule reads redaction markers, not secrets.** Every source runs its
text through `redact_secrets` before a detector sees it, so a credential sitting
in a workspace file reaches this module as `<redacted:github-token>`. That is
not a limitation to work around - it is the mechanism. The marker is proof that
the bytes on disk matched a credential pattern, which is exactly what the rule
needs to know, and the rule never has to hold the credential in order to say so.
Three things follow, and they are the reason that rule is written the way it is:
it must not re-read the file to "confirm" the hit, it must not quote the source
line around the marker (the redactor replaced what it matched, not whatever else
that line was carrying), and it must never propose an edit. An automated edit to
a file containing a live credential is how a credential gets committed a second
time, by a machine, at 3am, with nobody watching.

**A missing test is reported, never quietly written.** Creating a file that does
not exist is normally the one genuinely `safe` edit there is. Not here: a test
that asserts a module imports and nothing else reads as coverage to everybody
who later greps for one, so the skeleton this rule writes goes through review
with its emptiness stated in its own docstring.

**A rule that names the strings it hunts will always find itself.** This module
contains the literal text `TODO` and `<redacted:...>` because it cannot do its
job otherwise, and so does every test written against it. Both exclusions are
defaults rather than hard-coded, because a user whose repo is a linting tool has
the same problem and no way to patch this file.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from oodarag.reflect.detect.base import DetectContext, Detector, register
from oodarag.reflect.models import (
    KIND_COMMIT,
    KIND_FILE,
    EditOp,
    Evidence,
    Finding,
    Proposal,
    Signal,
)
from oodarag.util.logging import get_logger

log = get_logger("reflect.hygiene")

#: Deferral markers, matched case-sensitively. Folding case would report every
#: English sentence containing the word "bug", and prose is precisely where
#: these words are most often not debt at all.
DEFAULT_DEBT_MARKERS = ("TODO", "FIXME", "XXX", "HACK", "BUG")

#: Path prefixes that are test material. Debt markers inside a test are usually
#: describing the case under test rather than owing anybody work.
DEFAULT_TEST_PREFIXES = ("tests/", "test/")

#: Where source lives in a `src/` layout. When nothing in the tree matches,
#: `HygieneUntestedModule` falls back to the whole tree - see `_candidates`.
DEFAULT_SOURCE_PREFIXES = ("src/",)

#: Path fragments that make a credential-shaped hit a fixture rather than a
#: leak. Crude on purpose (a plain substring test, so `src/latest/` matches
#: "test"), which is why the rule counts what it skipped and says so out loud
#: instead of silently reporting less.
DEFAULT_FIXTURE_MARKERS = ("test", "fixture", "example", ".sample")

#: Extensions treated as source for the size rule. Data and markup formats are
#: deliberately absent: a 900-line YAML is a long list, not a long module, and
#: nobody refactors it by splitting it in two.
DEFAULT_CODE_EXTENSIONS = (
    ".bash", ".c", ".cc", ".cpp", ".cs", ".go", ".h", ".hpp", ".java", ".js", ".jsx",
    ".kt", ".lua", ".php", ".pl", ".py", ".rb", ".rs", ".scala", ".sh", ".sql", ".swift",
    ".ts", ".tsx", ".zsh",
)

#: Past this, a file is no longer read - it is navigated. The number is a
#: convention rather than a measurement, which is exactly why it is config.
DEFAULT_MAX_LINES = 600

#: This module's own path, so it stops finding its own vocabulary.
SELF_MODULE_SUFFIX = "oodarag/reflect/detect/hygiene.py"

#: The whole point of rule 2: this is what a credential looks like *after* the
#: source boundary redacted it. Both the tagged form (`<redacted:api-key>`) and
#: the bare one emitted by the generic key/value pattern are matched.
_REDACTION_RE = re.compile(r"<redacted(?::([a-z0-9][a-z0-9\-]*))?>")

#: Top-level definitions in a handful of languages, as a crude complexity proxy.
#: Column zero is doing the real work here: it is what makes this count the
#: file's structure rather than every nested closure inside it.
_DEFINITION_RE = re.compile(
    r"^(?:export\s+)?(?:public\s+|pub\s+|async\s+)*(def|class|function|func|fn)"
    r"\s+([A-Za-z_$][A-Za-z0-9_$]*)"
)

#: Cap on the test corpus held in memory while checking coverage. A repo with a
#: generated test suite must not turn one rule into the run's memory ceiling.
DEFAULT_MAX_TEST_CHARS = 2_000_000

_SKELETON_TEMPLATE = '''"""Test skeleton for {import_path}.

Written by the nightly reflect loop, which found no test file mentioning this
module. It asserts that the module imports and *nothing else* - it is a
placeholder for coverage, not coverage. Fill it in or delete it; leaving it as
it stands is the one option that actively misleads whoever greps for a test
next.
"""

from __future__ import annotations

import importlib
import unittest

MODULE = "{import_path}"


class {class_name}ImportTest(unittest.TestCase):
    def test_module_imports(self) -> None:
        self.assertIsNotNone(importlib.import_module(MODULE))


# TODO: replace the assertion above with real tests. The public callables
# of {module_rel} ({line_count} lines) are:
{names_block}
'''


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


def _cfg_str(config: dict[str, Any], key: str, default: str) -> str:
    value = config.get(key, default)
    return value.strip() if isinstance(value, str) and value.strip() else default


def _cfg_bool(config: dict[str, Any], key: str, default: bool) -> bool:
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return default


def _cfg_terms(config: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    """A tuple setting. An empty or unusable list means "keep the default".

    Switching a list off is done by disabling the rule, not by emptying its
    vocabulary - a marker list emptied by accident would silently turn the rule
    into a no-op that still reports itself as having run.
    """
    value = config.get(key)
    if isinstance(value, (list, tuple)) and value:
        terms = tuple(str(v).strip() for v in value if str(v).strip())
        if terms:
            return terms
    return default


def _bounded(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 3)


# -- signal and path helpers -------------------------------------------------


@dataclass(slots=True)
class _MarkerHit:
    """One line carrying a marker. The line, not the match, is the unit."""

    line: int
    marker: str
    text: str


@dataclass(slots=True)
class _Definition:
    line: int
    kind: str
    name: str


def rel_path(sig: Signal) -> str:
    """The signal's workspace-relative POSIX path, or "" if it has none.

    Absolute paths and anything containing `..` are dropped rather than
    normalized. Every downstream use - the finding key, an `EditOp.path`, the
    exclusion prefixes - is defined in terms of root-relative paths, and a rule
    that guessed at what an absolute path meant would be guessing about which
    file it is about to propose an edit to.
    """
    raw = (sig.uri or "").strip().replace("\\", "/")
    if not raw or "://" in raw or raw.startswith("git:"):
        return ""
    while raw.startswith("./"):
        raw = raw[2:]
    path = PurePosixPath(raw)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        return ""
    return path.as_posix()


def file_signals(ctx: DetectContext) -> list[Signal]:
    """One `KIND_FILE` signal per path, newest wins, in path order.

    Deduplicated because a cycle may observe the same tree twice (two sources,
    or one re-run) and a file reported twice would become the same finding
    twice with the same fingerprint - which the journal would then read as the
    finding having survived a night it never saw.
    """
    latest: dict[str, Signal] = {}
    for sig in ctx.by_kind(KIND_FILE):
        rel = rel_path(sig)
        if not rel:
            continue
        prev = latest.get(rel)
        if prev is None or (sig.ts, sig.ordinal) >= (prev.ts, prev.ordinal):
            latest[rel] = sig
    return [latest[key] for key in sorted(latest)]


def line_count(sig: Signal) -> int:
    """Lines in the observed file, trusting the source's count when it gave one."""
    raw = sig.metadata.get("line_count")
    if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0:
        return raw
    return len(sig.text.splitlines())


def path_stem(rel: str) -> str:
    return rel.rsplit("/", 1)[-1].rsplit(".", 1)[0]


def extension(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1]
    # A leading dot is a name, not an extension: ".gitignore" has none.
    return "." + name.rsplit(".", 1)[-1].lower() if "." in name[1:] else ""


def has_prefix(rel: str, prefixes: Iterable[str]) -> bool:
    lower = rel.lower()
    return any(lower.startswith(p.lower()) for p in prefixes if p)


def is_test_path(rel: str, prefixes: Iterable[str]) -> bool:
    """Under a test directory, or named like a test. Both spellings are common."""
    if has_prefix(rel, prefixes):
        return True
    name = rel.rsplit("/", 1)[-1].lower()
    return name.startswith("test_") or name.endswith(("_test.py", "_tests.py"))


def top_level_definitions(text: str, limit: int = 500) -> list[_Definition]:
    out: list[_Definition] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line or line[0].isspace():
            continue  # indented or blank: a nested definition, not the file's shape
        match = _DEFINITION_RE.match(line)
        if match:
            out.append(_Definition(line=number, kind=match.group(1), name=match.group(2)))
            if len(out) >= limit:
                break
    return out


#: Comment openers a debt marker sits behind. Deliberately excludes "-" and "*",
#: which are markdown bullets far more often than they are comment syntax.
_COMMENT_OPENER_RE = re.compile(r"(?:^|\s)(?:#|//|/\*|<!--|;;?)(?:\s|$)")


def looks_like_a_marker(line: str, match: re.Match[str]) -> bool:
    """Whether a matched word is a debt marker or just the word in a sentence.

    "TODO" appearing in prose about deferred work - a README describing what
    this very rule looks for, a changelog entry, a style guide - is not a
    backlog item, and reporting it produces a finding that can never be
    resolved because there is nothing there to fix. A real marker either carries
    its conventional punctuation (`TODO:`, `TODO(alice):`) or sits behind a
    comment opener.
    """
    if line[match.end() : match.end() + 1] in {":", "("}:
        return True
    return bool(_COMMENT_OPENER_RE.search(line[: match.start()]))


def marker_pattern(markers: Iterable[str]) -> re.Pattern[str]:
    """One word-boundaried alternation over literal markers, longest first."""
    ordered = sorted({m.strip() for m in markers if m and m.strip()}, key=len, reverse=True)
    if not ordered:
        return re.compile(r"(?!x)x")  # matches nothing, and never None-checks downstream
    body = "|".join(re.escape(m) for m in ordered)
    return re.compile(rf"(?<![A-Za-z0-9_])(?:{body})(?![A-Za-z0-9_])")


def _quote(rel: str, number: int, text: str, max_chars: int) -> str:
    flat = " ".join(text.split())
    if len(flat) > max_chars:
        flat = flat[: max_chars - 3] + "..."
    return f"{rel}:{number}: {flat}" if flat else f"{rel}:{number}"


# -- rules -------------------------------------------------------------------


@register
class HygieneDebtMarker(Detector):
    """TODO/FIXME/XXX/HACK/BUG, counted per file rather than per line.

    Observation only, deliberately. A marker is a note somebody left for
    themselves in the one place they were certain to see it again; the loop's
    job is to make sure they do see it again, not to decide what it meant. The
    only judgement the rule makes is about volume: past `loud_threshold` in a
    single file, a scattering of notes has become a backlog, and that is a
    different fact about the file, so the severity changes to say so.
    """

    rule_id = "hygiene.debt_marker"
    title = "Deferred work marked in the source"
    severity = "low"
    consumes = (KIND_FILE,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.markers = _cfg_terms(self.config, "markers", DEFAULT_DEBT_MARKERS)
        self.loud_threshold = _cfg_int(self.config, "loud_threshold", 5)
        self.max_quotes = _cfg_int(self.config, "max_quotes", 3)
        self.max_quote_chars = _cfg_int(self.config, "max_quote_chars", 160)
        self.exclude_prefixes = _cfg_terms(self.config, "exclude_prefixes", DEFAULT_TEST_PREFIXES)
        self.exclude_self = _cfg_bool(self.config, "exclude_self", True)
        self.marker_re = marker_pattern(self.markers)

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        for sig in file_signals(ctx):
            rel = rel_path(sig)
            if has_prefix(rel, self.exclude_prefixes):
                continue
            if self.exclude_self and rel.endswith(SELF_MODULE_SUFFIX):
                continue
            hits = self._hits(sig.text)
            if hits:
                yield self._finding(sig, rel, hits)

    def _hits(self, text: str) -> list[_MarkerHit]:
        """Marked lines. One hit per line however many markers it uses.

        A line reading `# TODO/FIXME: rewrite this` is one deferral, and
        counting it twice would let a single loud comment trip the threshold
        that is supposed to mean "there are five separate things here".
        """
        out: list[_MarkerHit] = []
        for number, line in enumerate(text.splitlines(), start=1):
            match = self.marker_re.search(line)
            if match and looks_like_a_marker(line, match):
                out.append(_MarkerHit(line=number, marker=match.group(0), text=line.strip()))
        return out

    def _finding(self, sig: Signal, rel: str, hits: list[_MarkerHit]) -> Finding:
        counts = Counter(hit.marker for hit in hits)
        breakdown = ", ".join(f"{marker} x{n}" for marker, n in counts.most_common())
        loud = len(hits) >= self.loud_threshold
        detail = (
            f"{len(hits)} marked lines in {rel} ({breakdown}). "
            + (
                "That is a backlog living in comments, where nothing tracks it and "
                "nobody reviews it."
                if loud
                else "Left where they are, these are only visible to whoever next opens "
                "the file."
            )
        )
        return Finding(
            rule_id=self.rule_id,
            title=f"{len(hits)} deferral markers in {rel}",
            detail=detail,
            severity="medium" if loud else self.severity,
            # A literal string match is strong evidence that the marker is
            # there; the residual doubt is only ever whether it still means
            # anything, which no amount of scanning settles.
            confidence=_bounded(0.55 + 0.05 * len(hits), high=0.9),
            key=rel,
            targets=[rel],
            evidence=[
                Evidence.from_signal(
                    sig, quote=_quote(rel, hit.line, hit.text, self.max_quote_chars)
                )
                for hit in hits[: max(1, self.max_quotes)]
            ],
            tags=["hygiene", "debt"],
            metadata={
                "path": rel,
                "count": len(hits),
                "markers": dict(counts),
                "loud": loud,
                "loud_threshold": self.loud_threshold,
                "line_count": line_count(sig),
                "first_line": hits[0].line,
            },
        )


@register
class HygieneLeakedSecret(Detector):
    """Credential-shaped strings in workspace files, seen through their redaction.

    Read the module docstring before changing anything here. The rule matches
    `<redacted:...>` markers, and a marker in a signal means the *file on disk*
    matched a credential pattern at the moment it was read - the loop is
    holding proof of a leak without ever holding the leak.

    There is no `propose`, and adding one would be a mistake rather than an
    improvement: every edit this loop makes is written through a backup and a
    diff in the review queue, so an "automatic removal" of a live token would
    copy it into two more files on its way out. The action is stated in the
    finding instead - rotate first, because a credential that has been on disk
    long enough for a nightly job to find it should be assumed read.
    """

    rule_id = "hygiene.leaked_secret"
    title = "Credential-shaped string in a workspace file"
    severity = "critical"
    consumes = (KIND_FILE,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.fixture_markers = _cfg_terms(
            self.config, "fixture_markers", DEFAULT_FIXTURE_MARKERS
        )
        self.max_quotes = _cfg_int(self.config, "max_quotes", 3)
        self.exclude_self = _cfg_bool(self.config, "exclude_self", True)

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        fixture_files = 0
        fixture_hits = 0
        pending: list[tuple[Signal, str, list[_MarkerHit]]] = []

        for sig in file_signals(ctx):
            rel = rel_path(sig)
            if self.exclude_self and rel.endswith(SELF_MODULE_SUFFIX):
                continue
            if sig.metadata.get("redacted") is False:
                # The observer redacted nothing here, so any marker in this text
                # is the file's own content - it defines or documents the
                # markers rather than having been scrubbed of a secret. Absent
                # metadata means "unknown" and falls through to matching.
                continue
            hits = self._hits(sig.text)
            if not hits:
                continue
            if self._is_fixture(rel):
                # Counted rather than dropped: "we ignored four of these" is a
                # sentence the user may want to argue with, and silently
                # reporting less on a critical rule is not a thing to do
                # quietly.
                fixture_files += 1
                fixture_hits += len(hits)
                continue
            pending.append((sig, rel, hits))

        if fixture_hits:
            log.info(
                "credential markers in fixture-like paths were not reported",
                files=fixture_files, matches=fixture_hits,
            )
        for sig, rel, hits in pending:
            yield self._finding(sig, rel, hits, fixture_files, fixture_hits)

    def _hits(self, text: str) -> list[_MarkerHit]:
        out: list[_MarkerHit] = []
        for number, line in enumerate(text.splitlines(), start=1):
            match = _REDACTION_RE.search(line)
            if match:
                kind = match.group(1) or "unspecified"
                out.append(_MarkerHit(line=number, marker=match.group(0), text=kind))
        return out

    def _is_fixture(self, rel: str) -> bool:
        lower = rel.lower()
        return any(fragment in lower for fragment in self.fixture_markers)

    def _finding(
        self,
        sig: Signal,
        rel: str,
        hits: list[_MarkerHit],
        fixture_files: int,
        fixture_hits: int,
    ) -> Finding:
        kinds = sorted({hit.text for hit in hits})
        return Finding(
            rule_id=self.rule_id,
            title=f"Credential-shaped string in {rel}",
            detail=(
                f"{len(hits)} line(s) of {rel} matched a credential pattern "
                f"({', '.join(kinds)}) when the file was read. The loop redacts at the "
                f"source boundary, so it holds the shape of the secret and never the "
                f"secret - which also means it cannot tell you whether this one is still "
                f"live. Treat it as live: rotate the credential first, then remove it "
                f"from the file and from the history that carries the file. No edit is "
                f"proposed here on purpose."
            ),
            severity=self.severity,
            # High, not certain: the pattern proves the shape and nothing else.
            # A documented example or a hex blob of the right length matches too.
            confidence=_bounded(0.7 + 0.05 * len(hits), high=0.95),
            key=rel,
            targets=[rel],
            evidence=[
                # Line number and marker only. The redactor replaced what it
                # matched, not whatever else the line was carrying, so quoting
                # the source line risks printing the second secret nothing
                # matched - and this text is written to a report on disk.
                Evidence.from_signal(sig, quote=f"{rel}:{hit.line}: {hit.marker}")
                for hit in hits[: max(1, self.max_quotes)]
            ],
            tags=["hygiene", "security", "secret"],
            metadata={
                "path": rel,
                "action": "rotate-and-remove",
                "count": len(hits),
                "kinds": kinds,
                "lines": [hit.line for hit in hits[:20]],
                "fixture_files_skipped": fixture_files,
                "fixture_matches_skipped": fixture_hits,
            },
        )


@register
class HygieneUntestedModule(Detector):
    """A source module no test file so much as mentions.

    Coverage tooling answers this question properly and this rule does not try
    to compete with it: it asks the far weaker question "does any test in this
    tree name this module at all", because that one can be answered from the
    signals already collected, without running anything. The weakness is
    deliberate and one-directional - a loose match marks a module *covered* and
    stays quiet. Nagging about a module that is in fact tested is how a nightly
    report gets ignored wholesale; missing one is how it merely gets ignored
    once.

    Size is the ranking signal. A 500-line module nobody tests is a different
    problem from a 20-line one, so `line_count` scales confidence and tiny
    modules drop out entirely.
    """

    rule_id = "hygiene.untested_module"
    title = "Source module with no test that mentions it"
    severity = "medium"
    consumes = (KIND_FILE,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.source_prefixes = _cfg_terms(
            self.config, "source_prefixes", DEFAULT_SOURCE_PREFIXES
        )
        self.test_prefixes = _cfg_terms(self.config, "test_prefixes", DEFAULT_TEST_PREFIXES)
        self.extensions = _cfg_terms(self.config, "extensions", (".py",))
        self.min_lines = _cfg_int(self.config, "min_lines", 20)
        self.big_module_lines = _cfg_int(self.config, "big_module_lines", 400)
        self.test_dir = _cfg_str(self.config, "test_dir", "tests")
        self.max_test_chars = _cfg_int(self.config, "max_test_chars", DEFAULT_MAX_TEST_CHARS)
        self.max_todo_names = _cfg_int(self.config, "max_todo_names", 12)

    # -- detection -----------------------------------------------------------

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        files = file_signals(ctx)
        tests = [sig for sig in files if is_test_path(rel_path(sig), self.test_prefixes)]
        blob = self._test_blob(tests)
        churn = self._churn(ctx)

        candidates = self._candidates(files)
        stems = Counter(path_stem(rel_path(sig)) for sig in candidates)

        for sig in candidates:
            rel = rel_path(sig)
            stem = path_stem(rel)
            import_path = self._import_path(rel)
            if self._is_mentioned(blob, rel, stem, import_path):
                continue
            lines = line_count(sig)
            if lines < self.min_lines:
                continue
            yield self._finding(
                sig, rel, stem, import_path, lines, churn.get(rel, []),
                ambiguous=stems[stem] > 1,
            )

    def _candidates(self, files: list[Signal]) -> list[Signal]:
        """Source modules worth asking the question about.

        The `src/` prefix is applied only when the tree actually has one. A
        flat package laid out at the repo root is a normal Python project, and
        a rule that silently found nothing there would look identical to a rule
        that found nothing wrong.
        """
        usable = [
            sig
            for sig in files
            if extension(rel_path(sig)) in self.extensions
            and not rel_path(sig).endswith("__init__.py")
            and not is_test_path(rel_path(sig), self.test_prefixes)
        ]
        under_src = [sig for sig in usable if has_prefix(rel_path(sig), self.source_prefixes)]
        if under_src:
            return under_src
        log.debug("no source prefix matched; considering the whole tree", files=len(usable))
        return usable

    def _test_blob(self, tests: list[Signal]) -> str:
        """Every test path and body, lowercased, as one searchable string.

        One blob rather than a search per (module, test) pair: the question is
        "does anything mention this", and a repo with 300 modules and 300 tests
        would otherwise be 90,000 regex passes over whole files.
        """
        parts: list[str] = []
        total = 0
        for sig in tests:
            chunk = rel_path(sig) + "\n" + sig.text
            if total + len(chunk) > self.max_test_chars:
                log.debug("test corpus truncated for coverage check", chars=total)
                break
            parts.append(chunk.lower())
            total += len(chunk)
        return "\n".join(parts)

    def _import_path(self, rel: str) -> str:
        """`src/pkg/mod.py` -> `pkg.mod`, or "" when that is not a dotted name."""
        body = rel
        for prefix in self.source_prefixes:
            if body.lower().startswith(prefix.lower()):
                body = body[len(prefix) :]
                break
        body = body.rsplit(".", 1)[0]
        parts = [p for p in body.split("/") if p]
        if not parts or not all(p.isidentifier() for p in parts):
            return ""
        return ".".join(parts)

    def _is_mentioned(self, blob: str, rel: str, stem: str, import_path: str) -> bool:
        """Whether any test file refers to *this module*, rather than to its name.

        A bare word-boundary search for the stem is far too loose, and fails in
        the direction that makes the rule useless: `html.py` was reported as
        covered because an unrelated HTTP test contained the string
        "text/html", and `web.py` because "web" is an ordinary English word.
        The rule then falls silent about exactly the modules it exists to find,
        with nothing to show that it did.

        So a mention has to look like a reference: the dotted import path, the
        file path, or the stem qualified by the package directory that contains
        it. `scrape/html` and `scrape.html` are references; `text/html` is not.
        """
        if not stem:
            return True  # no name to look for: stay quiet rather than guess
        if not blob:
            # A tree with no tests in it mentions nothing, and that is the case
            # this rule exists for - not the one it should fall silent on.
            return False
        for needle in self._needles(rel, stem, import_path):
            if needle and needle in blob:
                return True
        return False

    def _needles(self, rel: str, stem: str, import_path: str) -> list[str]:
        """Every spelling a test could plausibly use to name this module."""
        rel = rel.lower().replace("\\", "/")
        stem = stem.lower()
        out = [rel, rel.removesuffix(".py")]
        if import_path:
            out.append(import_path.lower())
        parent = rel.rsplit("/", 2)[-2] if rel.count("/") >= 1 else ""
        if parent:
            # The qualified tail is what an import or a patch target looks like.
            out.append(f"{parent}/{stem}")
            out.append(f"{parent}.{stem}")
        return out

    def _churn(self, ctx: DetectContext) -> dict[str, list[Signal]]:
        """Paths touched by commits in the window.

        `KIND_COMMIT` is optional input: when it is absent the rule works
        exactly as before, and when it is present an untested module that also
        changed this week outranks one nobody has opened in a year.
        """
        out: dict[str, list[Signal]] = {}
        for sig in ctx.by_kind(KIND_COMMIT):
            paths = sig.metadata.get("files")
            if not isinstance(paths, (list, tuple)):
                continue
            for path in paths:
                if isinstance(path, str) and path:
                    out.setdefault(path.replace("\\", "/"), []).append(sig)
        return out

    def _finding(
        self,
        sig: Signal,
        rel: str,
        stem: str,
        import_path: str,
        lines: int,
        commits: list[Signal],
        ambiguous: bool = False,
    ) -> Finding:
        names = [d for d in top_level_definitions(sig.text) if not d.name.startswith("_")]
        suggested = self._suggested_test(rel, ambiguous)
        weight = min(1.0, lines / max(1, self.big_module_lines))
        evidence = [
            Evidence.from_signal(
                sig,
                quote=(
                    f"{rel}: {lines} lines, {len(names)} public definitions, "
                    f'no test mentions "{import_path or stem}"'
                ),
            )
        ]
        if commits:
            recent = max(commits, key=lambda s: s.ts)
            evidence.append(Evidence.from_signal(recent, quote=recent.preview))
        return Finding(
            rule_id=self.rule_id,
            title=f"No test mentions {rel} ({lines} lines)",
            detail=(
                f"{rel} is {lines} lines with {len(names)} public definitions, and no file "
                f"under {self.test_dir}/ names it or imports it"
                + (f" (changed in {len(commits)} commit(s) this window)" if commits else "")
                + f". A skeleton at {suggested} would at least make the gap visible to the "
                f"next person who looks for one."
            ),
            severity=self.severity,
            # Absence of a mention is weaker evidence than presence of one, and
            # it gets weaker the smaller the module is - so size carries most of
            # the number, and recent churn nudges it.
            confidence=_bounded(0.3 + 0.45 * weight + min(0.1, 0.02 * len(commits)), high=0.85),
            key=rel,
            targets=[rel],
            evidence=evidence,
            tags=["hygiene", "tests"],
            metadata={
                "module": rel,
                "stem": stem,
                "import_path": import_path,
                "line_count": lines,
                "public_names": [f"{d.kind} {d.name}" for d in names[: self.max_todo_names]],
                "public_count": len(names),
                "suggested_test": suggested,
                "recent_commits": len(commits),
            },
        )

    def _suggested_test(self, rel: str, ambiguous: bool = False) -> str:
        """Where the missing test would go.

        Qualified by the parent directory when two candidate modules share a
        stem. Both `ingest/base.py` and `sources/base.py` would otherwise
        propose `tests/test_base.py`, and the second `create` would fail its own
        precondition against the file the first one wrote an hour earlier - one
        finding silently losing its fix to another is exactly the kind of thing
        nobody notices in a report they skim.
        """
        name = path_stem(rel)
        if ambiguous:
            parent = rel.rsplit("/", 2)[-2] if "/" in rel else ""
            if parent:
                name = f"{parent}_{name}"
        safe = re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_") or "module"
        directory = self.test_dir.strip("/") or "tests"
        return f"{directory}/test_{safe}.py"

    # -- proposal ------------------------------------------------------------

    def propose(self, finding: Finding, ctx: DetectContext) -> Iterable[Proposal]:
        rel = str(finding.metadata.get("module", ""))
        import_path = str(finding.metadata.get("import_path", ""))
        test_path = str(finding.metadata.get("suggested_test", ""))
        if not (rel and import_path and test_path):
            # Without a dotted import path there is no skeleton to write that
            # would actually run; the finding stands on its own.
            return ()
        if ctx.exists(test_path):
            # Somebody's file is already there and does not mention the module.
            # Appending to it is a guess about their layout; leave it to them.
            log.debug("suggested test path is taken", path=test_path, rule=self.rule_id)
            return ()
        lines = int(finding.metadata.get("line_count", 0) or 0)
        names = [str(n) for n in finding.metadata.get("public_names", []) if str(n).strip()]
        text = _test_skeleton(rel, import_path, lines, names)
        return [
            Proposal(
                finding=finding,
                title=f"Add a test skeleton for {rel}",
                rationale=(
                    f"{rel} has no test that names it. This creates {test_path} with an "
                    f"import assertion and the list of public callables to cover. It is "
                    f"marked for review rather than applied: a file that only proves the "
                    f"module imports looks like coverage to every later reader, so it "
                    f"should exist because you decided it should."
                ),
                edits=[
                    EditOp(
                        path=test_path,
                        op="create",
                        text=text,
                        note=f"{self.rule_id}: {rel}",
                    )
                ],
                # Creating a file destroys nothing, but this one makes a claim
                # about the repo that a human has to agree with. See the class
                # docstring.
                risk="review",
                impact=_bounded(0.3 + 0.4 * min(1.0, lines / max(1, self.big_module_lines))),
                effort=0.5,  # the skeleton is free; the tests it asks for are not
            )
        ]


@register
class HygieneOversizedModule(Detector):
    """A source file past the size anyone reads in one sitting.

    Observation only, and it will stay that way: splitting a module is a
    judgement about what belongs together, which is the one thing this loop has
    no evidence about. What it can do is put the number in front of somebody
    once, with the top-level definition count beside it - a file that is long
    because it holds forty small functions is a different file from one that is
    long because it holds three enormous ones, and the pair of numbers
    distinguishes them at a glance without pretending to be a complexity metric.
    """

    rule_id = "hygiene.oversized_module"
    title = "Source file past the readable size"
    severity = "low"
    consumes = (KIND_FILE,)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.max_lines = _cfg_int(self.config, "max_lines", DEFAULT_MAX_LINES)
        self.extensions = _cfg_terms(self.config, "extensions", DEFAULT_CODE_EXTENSIONS)
        self.exclude_prefixes = _cfg_terms(self.config, "exclude_prefixes", ())
        self.max_named = _cfg_int(self.config, "max_named", 3)

    def detect(self, ctx: DetectContext) -> Iterable[Finding]:
        for sig in file_signals(ctx):
            rel = rel_path(sig)
            if extension(rel) not in self.extensions:
                continue
            if self.exclude_prefixes and has_prefix(rel, self.exclude_prefixes):
                continue
            lines = line_count(sig)
            if lines <= self.max_lines:
                continue
            yield self._finding(sig, rel, lines)

    def _finding(self, sig: Signal, rel: str, lines: int) -> Finding:
        defs = top_level_definitions(sig.text)
        kinds = Counter(d.kind for d in defs)
        over = lines - self.max_lines
        evidence = [
            Evidence.from_signal(
                sig,
                quote=(
                    f"{rel}: {lines} lines ({over} over {self.max_lines}), "
                    f"{len(defs)} top-level definitions"
                ),
            )
        ]
        evidence.extend(
            Evidence.from_signal(sig, quote=f"{rel}:{d.line}: {d.kind} {d.name}")
            for d in defs[: max(0, self.max_named)]
        )
        return Finding(
            rule_id=self.rule_id,
            title=f"{rel} is {lines} lines",
            detail=(
                f"{rel} is {lines} lines, {over} past the {self.max_lines}-line mark, with "
                f"{len(defs)} top-level definitions. Nothing here says it is wrong - only "
                f"that it is the kind of file people navigate rather than read, and that "
                f"nobody chose that."
            ),
            severity=self.severity,
            # The line count is a fact; that it matters is the guess, and the
            # guess gets safer the further past the threshold the file is.
            confidence=_bounded(0.4 + 0.4 * (lines / max(1, self.max_lines) - 1), low=0.4,
                                high=0.9),
            key=rel,
            targets=[rel],
            evidence=evidence,
            tags=["hygiene", "size"],
            metadata={
                "path": rel,
                "line_count": lines,
                "max_lines": self.max_lines,
                "over_by": over,
                "top_level_definitions": len(defs),
                "defs": kinds.get("def", 0) + kinds.get("function", 0) + kinds.get("fn", 0),
                "classes": kinds.get("class", 0),
            },
        )


# -- the test skeleton -------------------------------------------------------


def _class_name(module_rel: str) -> str:
    parts = [p for p in re.split(r"[^A-Za-z0-9]+", path_stem(module_rel)) if p]
    name = "".join(p[:1].upper() + p[1:] for p in parts)
    return name if name and name[0].isalpha() else "Module"


def _test_skeleton(module_rel: str, import_path: str, lines: int, names: list[str]) -> str:
    """The body of the proposed test file.

    Written as one template rather than assembled: the file a human is asked to
    approve should be readable in the diff, and a skeleton stitched together
    from fragments reads like output rather than like something somebody meant.
    """
    listed = names or ["(no public top-level definitions found)"]
    names_block = "\n".join(f"#   - {name}" for name in listed)
    return _SKELETON_TEMPLATE.format(
        import_path=import_path,
        class_name=_class_name(module_rel),
        module_rel=module_rel,
        line_count=lines,
        names_block=names_block,
    )
