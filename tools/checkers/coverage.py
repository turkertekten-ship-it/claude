"""Does the code contain the capabilities the prose advertises?

This is the check the rest of the tool exists around. A README can say "hybrid
dense + BM25 retrieval fused with RRF" or "an eval harness with recall@k, MRR
and nDCG" without a single line of code behind either sentence, and nothing in a
normal build notices: the compiler does not read English, the test suite does not
know the sentence exists, and a reader has no way to tell a described capability
from an implemented one. That gap is where a project starts lying about itself,
usually without anyone deciding to.

The test applied here is deliberately weak, and that is the point. It does not
ask whether the retrieval is any good, or whether `rrf_fuse` does what its name
says. It asks the one question that can be answered from data alone: does any
identifier, string or comment anywhere in the Python tree even *mention* the
distinctive words the sentence uses? "BM25" is not a word that turns up by
accident. If the source never says it, in any spelling, then whatever the source
does, it is not the thing the sentence claims - and if the source does say it,
this checker has nothing further to contribute and stays quiet.

Everything else here is about not crying wolf, because a checker that flags
ordinary English gets switched off, and then it catches nothing at all:

* A sentence yields tokens only where it uses vocabulary ordinary prose does
  not: an acronym (BM25, RRF, nDCG), a metric name (recall@k, top-k), a word
  with a digit in it (sha256), or a word the author themselves put in backticks
  and thereby called code. Everything else - including "retrieval" and
  "pipeline", which describe an implementation and a description of one equally
  well - is stopworded. A sentence that yields no such token is not treated as a
  capability claim and is dropped in silence. That gate is not decoration: the
  ungated version of this rule flagged "unfamiliar", "synonyms", "briefly" and
  "inconvenient" on this repository's own documentation.
* One matching token is enough. The tokens of a sentence are alternatives, not
  requirements: the sentence is backed if the tree names any of them.
* Matching is substring, case-insensitive, and repeated against a form with the
  punctuation stripped out, so `recall@k` is satisfied by `recall_at_k` and
  `nDCG` by `ndcg`. Every one of those widenings makes a finding less likely.
* A section headed "roadmap", "planned" or "not yet built" is a section whose
  whole purpose is to describe what does not exist. Flagging it would be
  reporting the point of the sentence back at its author. Same for ADRs, whose
  job includes recording the option that was rejected, and for CHANGELOG and
  ROADMAP files.
* Paths, dotted names and commands inside backticks are left to the `paths`,
  `symbols` and `commands` checkers. Two findings for one defect is how a report
  becomes something a reader skims.

The cost of all that is stated rather than hidden: a docstring counts as source,
so a Python file that merely *discusses* a capability satisfies a claim to it.
This module is itself an instance - the paragraphs above name BM25, RRF and
nDCG, which is why running this checker on the repository that ships it cannot
find those particular words absent. Narrowing the search space to identifiers
would close that hole and open a worse one, since the most common way to be
wrong here is to declare a true sentence unsupported.

The manifest is the escape hatch for the case the heuristic cannot reach: when a
capability is genuinely implemented under a name the prose does not use, an
author can say so once, in `tools/checkers/coverage_manifest.json`, instead of
rewording the sentence. No such file is shipped: its absence is the normal case,
and the heuristic runs unaided. A manifest entry is read strictly - every symbol it
lists is required - precisely because it is a human's explicit statement about
one sentence rather than this module's guess about all of them.
"""

from __future__ import annotations

import json
import posixpath
import re
from dataclasses import dataclass
from typing import Iterator, Sequence

from tools.claims import RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

#: Read from the repository under review, not from this package, so that a
#: repository can carry its own vocabulary. Absent is the normal case.
MANIFEST_REL = "tools/checkers/coverage_manifest.json"

#: Below this, a "sentence" is a fragment - a table cell reading "not started",
#: a two-word label - and a fragment is not an advertisement.
MIN_WORDS = 4

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")

#: A heading that labels its section as describing unbuilt work. Everything
#: under it is exempt: a roadmap that says a thing does not exist yet is the
#: opposite of a false claim, and this repository's own README depends on the
#: distinction - its roadmap table names BM25, RRF, MRR and nDCG on purpose.
_ROADMAP_HEADING_RE = re.compile(
    r"planned|roadmap|not\s+yet|future|\bnext\b|todo|unbuilt|upcoming|wish\s*list",
    re.IGNORECASE,
)

#: A sentence that says the thing is not there. The heading rule catches the
#: labelled case; this catches the row that carries its own label ("not started;
#: nothing populates it"). Both only ever silence a finding.
_ABSENCE_RE = re.compile(
    r"\bnot\s+started\b"
    r"|\bnot\s+(?:yet\s+)?(?:been\s+)?(?:built|written|created|implemented|added|shipped|done)\b"
    r"|\bnot\s+yet\b|\bno\s+such\b|\bnothing\s+(?:populates|implements|backs|reads)\b"
    r"|\b(?:does|do|did|will|would|could|should)\s+not\s+(?:yet\s+)?exist"
    r"|\bthere\s+(?:is|are|was|were)\s+(?:deliberately\s+)?no\b"
    r"|\b(?:was|were|been)\s+(?:removed|deleted)\b"
    r"|\bno\s+longer\s+(?:exists?|there)\b"
    r"|\bnone\s+of\s+(?:those|these|them|the)\b|\bno\s+code\b|\bhad\s+none\b"
    r"|\bplanned\b|\broadmap\b|\bwould\s+be\b|\bwill\s+be\b",
    re.IGNORECASE,
)

#: How far from the sentence the disclaimer is allowed to be. Copied from the
#: `symbols` checker, for the same reason it needs one: a paragraph that lists
#: five capabilities and then says "none of those five had code" puts the
#: retraction on a different line from the list, and reading the list on its own
#: turns a repository's own honest accounting into a finding against it. This
#: repository's `provenance/observations.md` is exactly that paragraph.
_ABSENCE_WINDOW = 6

#: Files whose contents are, by convention, about other points in time. A
#: changelog describes a version the reader may not have; a roadmap describes
#: one nobody has.
_EXEMPT_FILENAMES = frozenset({"roadmap.md", "changelog.md", "changes.md", "history.md"})

#: A word, or several joined by the punctuation technical names use. `.` and `/`
#: are deliberately not joiners: `util/http.py` should yield `util` and `http`,
#: which are checkable, rather than one path-shaped token, which is the `paths`
#: checker's business and not this one's.
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[-@_][A-Za-z0-9]+)*")

#: Two adjacent capitals. One is a sentence opening or a proper noun; two is a
#: deliberate acronym - BM25, RRF, nDCG, HNSW, TF-IDF.
_ACRONYM_RE = re.compile(r"[A-Z]{2}")

#: A backtick span that is one bare word: `bm25`, `rrf_fuse`, `hash()`. A span
#: holding a path, a dotted name or a command belongs to another checker, and
#: `provenance/unknowns.md` would otherwise be read as a demand that the source
#: contain the word "unknowns".
_CODE_WORD_RE = re.compile(r"`([A-Za-z][A-Za-z0-9_-]*)(?:\(\))?`")

#: Segments joined the way technical names are joined. `.` and `/` are excluded
#: on purpose - see `_TOKEN_RE`.
_JOINER_RE = re.compile(r"[-@_]")

#: A single-letter segment, as in `top-k` and `recall@k`. It is the shape of a
#: parameterised metric and almost nothing else.
_LONE_LETTER_RE = re.compile(r"(?:^|[-@_])[A-Za-z](?:[-@_]|$)")

#: Ordinary English, plus the technical vocabulary so common that finding it in
#: the source proves nothing. The list is long on purpose: every word in it is a
#: finding this checker will never make, and the instruction is to under-flag.
#: A word earns its place here by being usable in a sentence about anything.
STOPWORDS: frozenset[str] = frozenset(
    """
    about above across after again against all almost along already also although always among
    amount another any anybody anyone anything anyway anywhere apart are area areas around
    aside back backs base based basic because been before begin behind being below beside best
    better between beyond both bring brought build builds built call called calls came cannot
    care case cases catch caught cause certain change changed changes check checked checking
    checks clear come comes coming common could course cover covers current currently
    deliberately depend depends describe describes description detail detailed details did
    differ different does doing done down draw drawn drop dropped due during each earlier early
    easier easily easy edge either else elsewhere empty enough entire entirely equal especially
    even ever every everybody everyone everything exactly example examples except exist exists
    expect expected extra fact fail failed fails fall far fast feel felt few fewer field fields
    fill final finally find finds first fits five fixed follow follows following force form
    former forms found four free from full fully further gave general generally get gets give
    given gives giving goes going gone good got great greater group groups grow half hand
    happen happens hard has have having held help helps hence her here herself high higher him
    himself his hold holds home how however idea ideas idle its itself just keep keeps kept kind
    kinds knew know known knows lack land large larger last late later latter lead leads learn
    least leave leaves left less let lets level levels lie life light like likely limit limits
    line lines list listed lists little live long longer look looking looks lost lot low lower
    made main major make makes making many mark marked matter may mean means meant meet member
    members mention mentioned mere merely middle might mind mine minor miss missing moment more
    moreover most mostly move moves much must myself name named names near nearly necessary need
    needed needs neither never nevertheless new newer next nine none nor normal normally not
    note noted notes nothing now nowhere number numbers obvious obviously off offer often old
    once one ones only onto open opens order orders other others otherwise ought our ours
    ourselves out outside over overall own part particular particularly parts pass passed past
    per perhaps period person piece place placed places plain please plus point points possible
    prefer preferred present pretty prevent previous probably problem problems provide provided
    provides put puts quick quickly quite rather reach read reader readers reading reads ready
    real really reason reasons receive recent recently refer refers regard relate related
    remain remains remove removed removes report reported reports require required requires
    rest result results return returns right room round rule rules run running runs said same
    saw say saying says second section sections see seem seems seen sees sell send sent series
    serve service services set sets seven several shall shape share she short should show shown
    shows side sides similar simple simply since single sit six size sizes small smaller some
    somebody somehow someone something sometimes somewhat somewhere soon sort sorts sound
    source sources space speak special specific specifically spend stage stages stand standard
    start started starting starts state stated states stay step steps still stop stopped stops
    story straight strong such suggest suggests sure surely take taken takes taking talk tell
    ten term terms text than that the their theirs them themselves then there therefore these
    they thing things think third this those though thought three through throughout thus time
    times today together told too took top total toward towards trouble true truly try trying
    turn turned turns twice two type types under understand unless until upon upper use used
    useful uses using usual usually value values various very via view views want wanted wants
    was way ways well went were what whatever when whenever where whether which while who whole
    whom whose why wide will wish with within without word words work worked working works
    world worse worst would write writes writing written wrong wrote year years yet you your
    yours yourself
    api apis architecture argument arguments behaviour behavior branch build builds capabilities
    capability class classes cli client clients code codes column columns command commands
    comment comments commit commits component components config configuration content contents
    context data database default defaults dependencies dependency design detail directory
    document documentation documents docs entry error errors event events feature features
    file files filename flag flags folder format formats framework function functions
    implement implementation implemented implements import imports index indexes info input
    inputs install installation instance integration interface interfaces item items json
    key keys layer layers library license line lines link links load loads local log logging
    logs loop main makefile manifest markdown method methods mode model models module modules
    name names node nodes note object objects operation operations option options output
    outputs package packages page pages parameter parameters parse parser path paths pipeline
    plugin plugins process processes program project projects property python quality query
    readme record records reference references release releases repo repos repository
    repositories request requests response responses result results retrieval return route
    routes row rows runtime schema script scripts search server servers service session setting
    settings setup source stage step storage store string strings structure suite support
    supported supports system systems table tables tag tags task tasks team template test
    tested testing tests text tool tools tree type update updated updates usage user users
    util utility utils validate validation value variable variables version versions view
    workflow wrapper
    adr adrs ascii bsd cd ci cpu email faq fixme gpl gpu gui ide ids ie io llm mit ml nb
    ok os pr prs ram rfc sdk ssd todo ui uri uris url urls utf ux vm vms wip
    """.split()
)


# ------------------------------------------------------------------- vocabulary


def _tokens(text: str) -> tuple[str, ...]:
    """The words in a sentence that ordinary prose would not have supplied.

    Compounds contribute themselves *and* their parts. That is deliberately
    generous in the direction of silence: every extra token is another chance
    for the source to satisfy the sentence, and the sentence is only reported
    when every one of them is absent.
    """
    marked = frozenset(w.lower() for w in _CODE_WORD_RE.findall(text))
    out: list[str] = []
    for match in _TOKEN_RE.finditer(text):
        raw = match.group(0)
        pieces = [raw, *_JOINER_RE.split(raw)] if _JOINER_RE.search(raw) else [raw]
        for piece in pieces:
            if piece not in out and _is_distinctive(piece, marked):
                out.append(piece)
    return tuple(out)


def _is_distinctive(token: str, marked: frozenset[str]) -> bool:
    """Would this word have to be *about* something to appear in a sentence?

    The plain-English rule the spec of this checker starts from - any lowercase
    word of four letters or more that is not in a stopword list - cannot be made
    safe by lengthening the list, because English does not run out of words:
    tried on this repository it demanded that the source contain "unfamiliar"
    and "briefly". So an ordinary word counts only when the author marked it as
    code with backticks, which is them asserting the symbol exists, or when it
    carries a digit, which ordinary words do not.
    """
    low = token.lower()
    plain = _JOINER_RE.sub("", low)
    if low in STOPWORDS or plain in STOPWORDS or not any(c.isalpha() for c in token):
        return False
    if len(token) >= 2 and _ACRONYM_RE.search(token):
        return True  # BM25, RRF, nDCG, TF-IDF
    if _JOINER_RE.search(token):
        # `recall@k`, `top-k`, `nDCG@10`. Without the guard this rule swallows
        # every hyphenated English adjective - "project-agnostic", "read-only" -
        # and every citation tag like "U-3", and starts demanding the source
        # contain them.
        letters = sum(1 for c in token if c.isalpha())
        return letters >= 3 and bool(any(c.isdigit() for c in token) or _LONE_LETTER_RE.search(token))
    if len(token) < 4:
        return False
    return low in marked or any(c.isdigit() for c in token)


def _variants(token: str) -> tuple[str, ...]:
    """Spellings of one token that the source might legitimately use.

    Source code renames punctuation rather than dropping it - `recall@k` becomes
    `recall_at_k`, `top-k` becomes `top_k` - so the `@` is expanded as well as
    stripped, and both forms are looked for in a copy of the source with its own
    punctuation removed.
    """
    low = token.lower()
    plain = re.sub(r"[^a-z0-9]", "", low)
    spelled = re.sub(r"[^a-z0-9]", "", low.replace("@", "at"))
    out = [v for v in (plain, spelled) if v]
    # A plural in prose is routinely a singular in code (`chunks` / `Chunk`).
    for form in list(out):
        if form.endswith("s") and len(form) >= 5 and form[:-1] not in out:
            out.append(form[:-1])
    return tuple(out)


@dataclass(frozen=True, slots=True)
class _Haystack:
    """Every Python file under the source roots, twice: as written, and squashed.

    Identifiers, strings and comments are all in scope. Narrowing to identifiers
    would be more precise about what "implemented" means and far more likely to
    be wrong, and being wrong here means accusing a true sentence.
    """

    text: str
    squashed: str
    file_count: int

    @classmethod
    def of(cls, sources: Sequence[SourceFile]) -> _Haystack:
        joined = "\n".join(s.text for s in sources).lower()
        return cls(joined, re.sub(r"[^a-z0-9]+", "", joined), len(sources))

    def has(self, token: str) -> bool:
        if token.lower() in self.text:
            return True
        return any(v in self.squashed for v in _variants(token))


# ---------------------------------------------------------------------- filters


def _fenced_lines(source: SourceFile) -> frozenset[int]:
    out: set[int] = set()
    for fence in source.fences():
        span = len(fence.body.split("\n")) if fence.body else 0
        out.update(range(fence.start_line - 1, fence.start_line + span + 1))
    return frozenset(out)


def _roadmap_lines(source: SourceFile) -> frozenset[int]:
    """Lines under a heading that announces unbuilt work, the heading included.

    The enclosing headings are tracked as a stack rather than just the nearest
    one, because a subsection of a roadmap is still roadmap: "### Reranking"
    under "## Not yet built" describes nothing that exists either.
    """
    fenced = _fenced_lines(source)
    out: set[int] = set()
    stack: list[tuple[int, bool]] = []
    for lineno, raw in enumerate(source.lines, start=1):
        match = _HEADING_RE.match(raw.strip()) if lineno not in fenced else None
        if match:
            level = len(match.group(1))
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, bool(_ROADMAP_HEADING_RE.search(match.group(2)))))
        if any(flagged for _, flagged in stack):
            out.add(lineno)
    return frozenset(out)


def _exempt_file(rel: str) -> bool:
    parts = rel.split("/")
    # An architecture decision record's job includes writing down the option
    # that was rejected and the one that is not built yet.
    if any(part.lower() == "adr" for part in parts[:-1]):
        return True
    return parts[-1].lower() in _EXEMPT_FILENAMES


def _asserts_absence(source: SourceFile, line: int) -> bool:
    rows = source.lines
    low = max(0, line - 1 - _ABSENCE_WINDOW)
    window = " ".join(rows[low : line + _ABSENCE_WINDOW])
    return _ABSENCE_RE.search(" ".join(window.split())) is not None


def _eligible(claim: Claim, source: SourceFile) -> bool:
    if claim.kind == "heading":
        # A heading is a label. It says a topic exists, not that code does, and
        # reading content into a name is the exact move this repository's
        # doctrine forbids.
        return False
    if len(claim.text.split()) < MIN_WORDS:
        return False
    return not _asserts_absence(source, claim.line)


# --------------------------------------------------------------------- manifest


def _load_manifest(repo: RepoIndex, rel: str) -> tuple[dict[str, tuple[str, ...]], str]:
    """The optional overrides, or the reason they could not be read."""
    source = repo.get(rel)
    if source is None:
        return {}, ""
    try:
        data = json.loads(source.text)
    except (json.JSONDecodeError, ValueError) as e:
        return {}, f"{type(e).__name__}: {e}"
    if not isinstance(data, dict):
        return {}, f"expected a JSON object mapping claim substrings to symbol lists, got {type(data).__name__}"
    out: dict[str, tuple[str, ...]] = {}
    for key in sorted(data):
        value = data[key]
        symbols = [str(v) for v in value if str(v).strip()] if isinstance(value, list) else []
        # A key with nothing behind it cannot make a claim unsupported, and
        # guessing what the author meant by an empty list is not this module's
        # job. It is dropped, not reported.
        if key.strip() and symbols:
            out[key] = tuple(symbols)
    return out, ""


def _manifest_match(manifest: dict[str, tuple[str, ...]], text: str) -> str:
    """The most specific key the sentence contains, or "".

    Longest match wins so that a general entry and a refinement of it can
    coexist; ties break on the key itself, so two equally long keys always
    resolve the same way.
    """
    lowered = text.lower()
    hits = [k for k in manifest if k.lower() in lowered]
    return min(sorted(hits), key=lambda k: (-len(k), k)) if hits else ""


# ------------------------------------------------------------------ search space


def _roots(repo: RepoIndex, config: CheckConfig) -> tuple[str, ...]:
    out: list[str] = []
    for candidate in config.source_roots:
        normalised = posixpath.normpath(candidate) if candidate else "."
        # An absolute or escaping root names the host's filesystem; nothing in
        # this tree can honestly be searched for under it.
        if normalised.startswith(("/", "..")) or normalised in out:
            continue
        if normalised != "." and not repo.exists(normalised):
            continue
        out.append(normalised)
    return tuple(out)


def _python_under(repo: RepoIndex, roots: Sequence[str]) -> list[SourceFile]:
    """Every source file under the roots - not only the Python ones.

    A capability is not made false by being implemented in another language. A
    Dockerfile, a CI workflow, a shell script, a SQL migration or a JS bundle
    can all be the real implementation of a sentence in the README, and every
    one of those files is already in `repo.files`. Searching only `repo.python`
    reported them as advertised-but-unimplemented, which in a polyglot
    repository is most of what the README describes.

    Markdown is excluded: prose repeating prose is not evidence of code.
    """
    return [
        source for source in repo.files
        if not source.is_markdown
        and any(root == "." or source.rel.startswith(f"{root}/") for root in roots)
    ]


@dataclass(frozen=True, slots=True)
class _Candidate:
    claim: Claim
    tokens: tuple[str, ...]
    key: str  # the manifest key that supplied the tokens, else ""

    @property
    def from_manifest(self) -> bool:
        return bool(self.key)


def _candidates(repo: RepoIndex, manifest: dict[str, tuple[str, ...]]) -> list[_Candidate]:
    """Every prose sentence that asserts something checkable, in file order.

    At most one candidate per line: a table row that says the same thing in two
    cells is one assertion, and a reader told about it twice trusts the report
    less, not more.
    """
    out: list[_Candidate] = []
    seen: set[tuple[str, int]] = set()
    for source in repo.markdown:
        if _exempt_file(source.rel):
            continue
        roadmap = _roadmap_lines(source)
        for claim in source.prose_claims():
            if claim.line in roadmap or (claim.path, claim.line) in seen:
                continue
            if not _eligible(claim, source):
                continue
            key = _manifest_match(manifest, claim.text)
            tokens = manifest[key] if key else _tokens(claim.text)
            if not tokens:
                continue  # no distinctive vocabulary: an ordinary sentence, not a claim
            seen.add((claim.path, claim.line))
            out.append(_Candidate(claim, tuple(tokens), key))
    return out


# --------------------------------------------------------------------- checker


@dataclass
class CoverageChecker:
    name: str = "coverage"
    description: str = "Capabilities described in prose are named somewhere in the Python source."
    manifest_rel: str = MANIFEST_REL

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        roots = _roots(repo, config)
        if not roots:
            return  # nowhere to look: "not found" would be a guess, not an observation

        manifest, manifest_error = _load_manifest(repo, self.manifest_rel)
        if manifest_error:
            yield self._manifest_unreadable(repo, manifest_error)

        candidates = _candidates(repo, manifest)
        if not candidates:
            return

        sources = _python_under(repo, roots)
        if not sources:
            yield Finding(
                checker=self.name, code="NO_PYTHON_SOURCE",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO,
                claim=candidates[0].claim,
                detail=(f"no Python files under source roots {', '.join(roots)}, so the "
                        f"{len(candidates)} capability claim(s) in this repository's prose were "
                        "not checked against code."),
            )
            return

        haystack = _Haystack.of(sources)
        for candidate in candidates:
            missing = tuple(t for t in candidate.tokens if not haystack.has(t))
            if not missing:
                continue
            if candidate.from_manifest or len(missing) == len(candidate.tokens):
                yield self._unsupported(candidate, missing, roots, haystack)

    # ----------------------------------------------------------------- verdicts

    def _unsupported(self, candidate: _Candidate, missing: tuple[str, ...],
                     roots: tuple[str, ...], haystack: _Haystack) -> Finding:
        """One sentence whose vocabulary appears nowhere in the tree.

        The tokens go in the summary verbatim so the reader can re-run the
        search by hand and get the same answer. A finding a reader cannot
        reproduce is an opinion.
        """
        listed = ", ".join(sorted(missing))
        where = ", ".join(roots)
        if candidate.from_manifest:
            detail = (f"{self.manifest_rel} requires {listed} for any claim containing "
                      f"{candidate.key!r}, and the Python source under {where} names "
                      f"{'none of them' if len(missing) == len(candidate.tokens) else 'only some of them'}.")
            summary = (f"{listed} required by {self.manifest_rel} but absent from "
                       f"{haystack.file_count} source file(s) under {where}")
            remedy = (f"implement {missing[0]}, or correct the sentence, or update "
                      f"{self.manifest_rel} if the capability ships under another name.")
        else:
            detail = (f"this sentence advertises {listed}, and no identifier, string or comment "
                      f"in the {haystack.file_count} source file(s) under {where} mentions any of "
                      "them in any spelling.")
            summary = (f"none of {listed} appear in {haystack.file_count} source file(s) under "
                       f"{where}, searched case-insensitively and with punctuation stripped")
            remedy = (f"implement it, move the sentence under a roadmap heading, or map the claim "
                      f"to the symbols that do back it in {self.manifest_rel}.")
        return Finding(
            checker=self.name, code="CAPABILITY_UNSUPPORTED",
            verdict=Verdict.UNSUPPORTED, severity=Severity.WARN, claim=candidate.claim,
            evidence=[
                Evidence.at(candidate.claim.path, candidate.claim.line, candidate.claim.text,
                            summary=f"{candidate.claim.locator} advertises {listed}"),
                Evidence.absent(summary, roots),
            ],
            detail=detail,
            remedy=remedy,
        )

    def _manifest_unreadable(self, repo: RepoIndex, reason: str) -> Finding:
        source = repo.get(self.manifest_rel)
        line, text = 1, ""
        if source is not None:
            for lineno, raw in enumerate(source.lines, start=1):
                if raw.strip():
                    line, text = lineno, raw.strip()
                    break
        return Finding(
            checker=self.name, code="MANIFEST_UNREADABLE",
            verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO,
            claim=Claim(text, self.manifest_rel, line, kind="config"),
            detail=(f"{self.manifest_rel} could not be read as a JSON object ({reason}), so its "
                    "claim-to-symbol overrides were not applied; the heuristic was used instead."),
        )


register(CoverageChecker())
