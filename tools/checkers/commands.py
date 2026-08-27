"""Do the commands this repository tells a reader to run actually work?

A README written in the imperative mood is a promise. `make test`,
`python -m thing`, `./scripts/setup.sh` - each one asserts that a reader who
types it gets a working result, and each one rots silently the moment the
target it names is renamed or deleted. No documentation build catches that,
because to a markdown renderer a dead command and a live one are the same grey
box.

The hard part is not finding the commands. It is deciding which lines inside a
code fence *are* commands. Fences hold ASCII pipeline diagrams, directory
trees, tables and captured output at least as often as they hold instructions,
and a checker that reads every such line as an instruction produces a page of
nonsense and gets switched off - after which it catches nothing at all. So the
first thing that happens to a candidate here is the resolution gate (CONTRACT
rule 6): if the leading token is not on PATH, not a target in the Makefile and
not a file in the repository, this was prose in a box, and nothing is said
about it.

What survives the gate is resolved statically first - a `make` target with no
rule, a `-m` module with no file behind it - and only then, and only when the
caller opted into `run_commands`, actually executed. Execution is fenced twice
over: the leading token must be in `config.command_allowlist`, and the text
must be free of the things that make running a stranger's documentation a bad
idea (`rm`, `sudo`, `curl`, a pipe, a redirect, a subshell). For `make` that
test reaches into the target's recipe, because `make clean` is only as safe as
the `rm -rf` it hides. Anything that would have needed to run to be decided and
did not run is UNVERIFIABLE with the reason attached - never a pass.
"""

from __future__ import annotations

import importlib.util
import os
import posixpath
import re
import shlex
import shutil
import sys
from dataclasses import dataclass, field
from typing import Iterator, Sequence

from tools.claims import RepoIndex, SourceFile
from tools.evidence import Claim, Evidence, Finding, Severity, Verdict
from tools.registry import CheckConfig, register

MAKEFILE_NAMES: tuple[str, ...] = ("Makefile", "makefile", "GNUmakefile")

# The contract fixes this shape, so a reader can re-derive every target we
# claim to have seen by grepping the same pattern.
_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+):")
_ASSIGN_RE = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*(\?=|::=|:=|\+=|=)\s*(.*)$")
_VAR_RE = re.compile(r"\$[({]([A-Za-z_][A-Za-z0-9_]*)[)}]")
_RECIPE_PREFIX_RE = re.compile(r"^[@+-]+")
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_TARGET_NAME_RE = re.compile(r"^[A-Za-z0-9_.\-/]+$")
_PY_RE = re.compile(r"^python(?:3(?:\.\d+)?)?$")

# Executing what a repository's own documentation tells you to execute is a
# real action. These are the shapes that make it an irreversible one: they are
# refused before the allowlist is even consulted.
_UNSAFE_WORDS = ("rm", "sudo", "curl", "wget", "npm", "mv", "dd", "chmod", "chown")
_UNSAFE_PHRASES = ("git push", "pip install")
_UNSAFE_CHARS = (">", "|", "&&", ";", "$(", "`")
# argv is handed to subprocess without a shell, so these stdlib modules are the
# remaining way a "safe-looking" command mutates the machine or never returns.
# `compileall` is here for a narrower reason: writing .pyc into the tree would
# break rule 8, and it is the one module that ignores PYTHONDONTWRITEBYTECODE.
_UNSAFE_MODULES = frozenset(
    {"pip", "venv", "ensurepip", "compileall", "http.server", "smtpd", "idlelib"}
)
_MUTATING_WORDS = frozenset(
    "install uninstall publish upload deploy release init bootstrap".split()
)

# `make sure the venv is active` is English, not a build invocation, and the
# resolution gate cannot catch it because `make` really is on PATH. Refusing to
# read a prose-shaped argument list as a goal is the only defence, and a missed
# broken target costs far less than a checker that flags a sentence.
_PROSE_GOALS = frozenset(
    "sure a an the it this that these those them us you your our my me "
    "is are was were do does did and or not".split()
)
_MAX_GOALS = 2


@dataclass(frozen=True, slots=True)
class _MakeTarget:
    name: str
    line: int
    recipes: tuple[tuple[int, str], ...] = ()


@dataclass(slots=True)
class _Makefile:
    source: SourceFile
    rel: str
    targets: dict[str, _MakeTarget] = field(default_factory=dict)
    order: list[str] = field(default_factory=list)
    phony: frozenset[str] = frozenset()

    @property
    def default_goal(self) -> str:
        return self.order[0] if self.order else ""


# --------------------------------------------------------------------- parsing


def _load_makefile(repo: RepoIndex) -> _Makefile | None:
    for name in MAKEFILE_NAMES:
        source = repo.get(name)
        if source is not None:
            return _parse_makefile(source)
    return None


def _parse_makefile(source: SourceFile) -> _Makefile:
    """Targets, their recipe lines, and enough variable expansion to read them.

    `$(PY) -m oodarag.cli` is unresolvable as written; expanding it is the
    difference between checking the recipe and skipping it as prose. Variables
    that cannot be expanded are deliberately left as `$(NAME)` so the leading
    token fails the resolution gate rather than being guessed at.
    """
    variables: dict[str, str] = {"MAKE": "make"}
    targets: dict[str, _MakeTarget] = {}
    recipes: dict[str, list[tuple[int, str]]] = {}
    order: list[str] = []
    lines: dict[str, int] = {}
    phony: set[str] = set()
    current: str | None = None
    pending: list[str] = []
    pending_line = 0

    for lineno, raw in enumerate(source.lines, start=1):
        if raw.startswith("\t"):
            body = _RECIPE_PREFIX_RE.sub("", raw[1:].strip()).strip()
            if current is None:
                continue
            if not pending:
                if not body or body.startswith("#"):
                    continue
                pending_line = lineno
            if body.endswith("\\"):
                pending.append(body[:-1].strip())
                continue
            pending.append(body)
            joined = _expand(" ".join(p for p in pending if p).strip(), variables)
            pending = []
            if joined:
                recipes[current].append((pending_line, joined))
            continue

        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue  # a blank line does not end a rule in make, so `current` stands

        if m := _ASSIGN_RE.match(raw):
            name, op, value = m.group(1), m.group(2), m.group(3).strip()
            if op == "?=" and name in variables:
                pass
            elif op == "+=":
                variables[name] = f"{variables.get(name, '')} {value}".strip()
            else:
                variables[name] = value
            current = None
            continue

        if (t := _TARGET_RE.match(raw)) and not raw[t.end():].startswith("="):
            name = t.group(1)
            if name == ".PHONY":
                phony.update(raw.split(":", 1)[1].split())
                current = None
                continue
            if name.startswith("."):  # .SUFFIXES and friends are directives, not goals
                current = None
                continue
            if name not in recipes:
                recipes[name] = []
                order.append(name)
                lines[name] = lineno
            current = name
            continue

        current = None

    for name in order:
        targets[name] = _MakeTarget(name, lines[name], tuple(recipes[name]))
    return _Makefile(source, source.rel, targets, order, frozenset(phony))


def _expand(text: str, variables: dict[str, str], depth: int = 4) -> str:
    for _ in range(depth):
        expanded = _VAR_RE.sub(lambda m: variables.get(m.group(1), m.group(0)), text)
        if expanded == text:
            break
        text = expanded
    return text


# ------------------------------------------------------------------ resolution


def _decomment(text: str) -> str:
    """Drop a trailing `# note` the way a shell would.

    `make demo   # ingest -> index` is one command and one comment, and letting
    the comment reach the safety scan would see the `>` in the arrow and refuse
    to run a command that has no redirect in it at all.
    """
    quote = ""
    for idx, char in enumerate(text):
        if quote:
            if char == quote:
                quote = ""
        elif char in "'\"":
            quote = char
        elif char == "#" and (idx == 0 or text[idx - 1].isspace()):
            return text[:idx].rstrip()
    return text


def _split(command: str) -> list[str]:
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:  # unbalanced quotes: this was never a command line
        return []
    while tokens and _ENV_ASSIGN_RE.match(tokens[0]):
        tokens.pop(0)  # `PYTHONPATH=. python3 -m x` - the interpreter is the real head
    return tokens


def _resolution(token: str, repo: RepoIndex, mk: _Makefile | None) -> str:
    """Why this leading token is a command at all, or "" if it is not one."""
    if not token:
        return ""
    if found := shutil.which(token):
        return f"{token!r} is on PATH at {found}"
    if mk is not None and (token in mk.targets or token in mk.phony):
        return f"{token!r} is a target in {mk.rel}"
    rel = token[2:] if token.startswith("./") else token
    if rel and repo.exists(rel):
        return f"{token!r} is a file in the repository"
    return ""


def _goals(tokens: Sequence[str], mk: _Makefile | None) -> list[str] | None:
    """The targets a `make` invocation names, or None if it should be ignored."""
    goals: list[str] = []
    for tok in tokens[1:]:
        if tok in ("-C", "--directory", "-f", "--file", "--makefile", "-o", "-W"):
            return None  # names a Makefile we are not reading; guessing would be a fabrication
        if tok.startswith("-") or "=" in tok:
            continue  # a switch, or a command-line variable override
        if not _TARGET_NAME_RE.match(tok) or tok.lower() in _PROSE_GOALS:
            return None
        goals.append(tok)
    if len(goals) > _MAX_GOALS:
        return None
    if not goals and mk is not None and mk.default_goal:
        return [mk.default_goal]
    return goals


def _module_of(tokens: Sequence[str]) -> str:
    if not tokens or not _PY_RE.match(posixpath.basename(tokens[0])):
        return ""
    for idx, tok in enumerate(tokens[1:], start=1):
        if tok == "-m" and idx + 1 < len(tokens):
            return tokens[idx + 1]
    return ""


def _module_paths(module: str, roots: Sequence[str]) -> list[str]:
    stem = module.replace(".", "/")
    out: list[str] = []
    for root in roots:
        for tail in (f"{stem}.py", f"{stem}/__init__.py"):
            rel = posixpath.normpath(posixpath.join(root, tail))
            if rel not in out:
                out.append(rel)
    return out


def _locate_module(module: str, repo: RepoIndex, config: CheckConfig) -> tuple[str, list[str]]:
    """One of found / missing / unknown, plus the paths that were searched.

    "missing" is reserved for the case with positive evidence behind it: the
    top-level package is this repository's own, so the absent submodule is a
    broken promise rather than something the reader was told to install first.
    A name that is nowhere - not here, not in the stdlib, not importable - is
    "unknown", because an optional dependency and a typo look identical from
    inside a checker.
    """
    candidates = _module_paths(module, config.source_roots)
    for rel in candidates:
        if repo.exists(rel):
            return "found", candidates
    top = module.split(".")[0]
    if top != module and any(repo.exists(rel) for rel in _module_paths(top, config.source_roots)):
        return "missing", candidates
    if top in sys.stdlib_module_names:
        return "found", candidates
    try:
        # Top-level only: find_spec on a dotted name imports the parent package,
        # and a checker must not execute the code it is reviewing.
        if importlib.util.find_spec(top) is not None:
            return "found", candidates
    except Exception:
        return "unknown", candidates
    return "unknown", candidates


# ----------------------------------------------------------------- run safety


def _unsafe_reason(text: str, mk: _Makefile | None, depth: int = 0) -> str:
    lowered = text.lower()
    for phrase in _UNSAFE_PHRASES:
        if phrase in lowered:
            return f"the text contains {phrase!r}"
    for word in _UNSAFE_WORDS:
        # Word boundaries, so `/bin/rm` is caught and `transform` is not.
        if re.search(rf"(?<![\w-]){re.escape(word)}(?![\w-])", lowered):
            return f"the text contains {word!r}"
    for char in _UNSAFE_CHARS:
        if char in text:
            return f"the text contains {char!r}, which needs a shell"

    tokens = _split(text)
    if not tokens:
        return "the command line could not be parsed"
    if (module := _module_of(tokens)) and module.split(".")[0] in _UNSAFE_MODULES:
        return f"`-m {module}` changes the environment or does not return"
    if any(tok.lower() in _MUTATING_WORDS for tok in tokens[1:]):
        return "an argument names a mutating action"

    if posixpath.basename(tokens[0]) == "make" and mk is not None and depth < 1:
        # `make clean` is exactly as safe as the recipe it hides.
        for goal in _goals(tokens, mk) or []:
            target = mk.targets.get(goal)
            if target is None:
                continue
            for _, recipe in target.recipes:
                if reason := _unsafe_reason(recipe, mk, depth + 1):
                    return f"target {goal!r} runs `{recipe}`: {reason}"
    return ""


def _run_env(repo: RepoIndex, config: CheckConfig) -> dict[str, str]:
    env = dict(os.environ)
    roots = [str((repo.root / root).resolve()) for root in config.source_roots]
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([*roots, existing] if existing else roots)
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # a review must not leave __pycache__ behind
    return env


# -------------------------------------------------------------------- checker


@dataclass
class CommandChecker:
    name: str = "commands"
    description: str = "Do the documented and Makefile commands resolve, and do they run?"

    def check(self, repo: RepoIndex, config: CheckConfig) -> Iterator[Finding]:
        mk = _load_makefile(repo)
        collected: list[Finding] = []

        # Documentation first: a command addressed to a reader is the promise,
        # and reaching a recipe through it attaches the doc that pointed there.
        for source in repo.markdown:
            for fence in source.fences():
                for line, command in fence.commands:
                    claim = Claim(source.line_text(line).strip(), source.rel, line,
                                  kind="command", context=fence.lang)
                    collected.extend(self._inspect(command, claim, repo, config, mk,
                                                   from_doc=True, depth=0, context=()))

        if mk is not None:
            for name in sorted(mk.targets, key=lambda n: mk.targets[n].line):
                for line, recipe in mk.targets[name].recipes:
                    claim = Claim(mk.source.line_text(line).strip(), mk.rel, line,
                                  kind="make_recipe", context=name)
                    collected.extend(self._inspect(recipe, claim, repo, config, mk,
                                                   from_doc=False, depth=1, context=()))

        seen: set[tuple[str, str, int, str]] = set()
        for finding in collected:
            key = (finding.code, finding.claim.path, finding.claim.line, finding.detail)
            if key in seen:  # the same recipe reached from a doc and from the Makefile scan
                continue
            seen.add(key)
            yield finding

    # ------------------------------------------------------------------ internals

    def _inspect(self, command: str, claim: Claim, repo: RepoIndex, config: CheckConfig,
                 mk: _Makefile | None, *, from_doc: bool, depth: int,
                 context: tuple[Evidence, ...]) -> list[Finding]:
        command = _decomment(command)
        tokens = _split(command)
        if not tokens:
            return []
        reason = _resolution(tokens[0], repo, mk)
        if not reason:
            return []  # rule 6: an unresolvable head means this line was never a command

        here = Evidence.at(claim.path, claim.line, claim.text,
                           summary=f"{claim.path}:{claim.line} - {reason}")
        findings: list[Finding] = []

        if posixpath.basename(tokens[0]) == "make":
            findings.extend(self._check_make(tokens, command, claim, repo, config, mk,
                                             depth=depth, here=here, context=context))
        elif module := _module_of(tokens):
            findings.extend(self._check_module(module, claim, repo, config,
                                               here=here, context=context))

        if from_doc and not findings:
            findings.extend(self._maybe_run(tokens, command, claim, repo, config, mk, here=here))
        return findings

    def _check_make(self, tokens: list[str], command: str, claim: Claim, repo: RepoIndex,
                    config: CheckConfig, mk: _Makefile | None, *, depth: int,
                    here: Evidence, context: tuple[Evidence, ...]) -> list[Finding]:
        goals = _goals(tokens, mk)
        if goals is None:
            return []
        findings: list[Finding] = []
        for goal in goals:
            if mk is None:
                findings.append(Finding(
                    checker=self.name, code="MAKE_TARGET_MISSING",
                    verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=claim,
                    evidence=[here, *context, Evidence.absent(
                        "no makefile at the repository root", MAKEFILE_NAMES)],
                    detail=f"`make {goal}` is documented, but this repository has no makefile.",
                    remedy=f"Add a Makefile with a `{goal}:` rule, or drop the command.",
                ))
                continue
            target = mk.targets.get(goal)
            if target is None:
                if goal in mk.phony:
                    continue  # declared but ruleless: too weak a signal to call broken
                findings.append(Finding(
                    checker=self.name, code="MAKE_TARGET_MISSING",
                    verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=claim,
                    evidence=[here, *context, Evidence.absent(
                        f"{mk.rel} defines {len(mk.order)} targets and {goal!r} is not among "
                        f"them: {', '.join(mk.order) or '(none)'}", (mk.rel,))],
                    detail=f"`make {goal}` is documented, but {mk.rel} has no `{goal}:` rule.",
                    remedy=f"Add a `{goal}:` rule to {mk.rel}, or correct the command.",
                ))
                continue
            if depth == 0:
                # Depth 1: documenting `make X` also promises whatever X runs.
                for line, recipe in target.recipes:
                    sub = Claim(mk.source.line_text(line).strip(), mk.rel, line,
                                kind="make_recipe", context=goal)
                    findings.extend(self._inspect(recipe, sub, repo, config, mk,
                                                  from_doc=False, depth=depth + 1,
                                                  context=(here,)))
        return findings

    def _check_module(self, module: str, claim: Claim, repo: RepoIndex, config: CheckConfig,
                      *, here: Evidence, context: tuple[Evidence, ...]) -> list[Finding]:
        status, searched = _locate_module(module, repo, config)
        if status == "found":
            return []
        if status == "missing" and searched:
            return [Finding(
                checker=self.name, code="MODULE_MISSING",
                verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=claim,
                evidence=[here, *context, Evidence.absent(
                    f"no file backs `-m {module}` under source roots "
                    f"{', '.join(config.source_roots)}", tuple(searched))],
                detail=f"`python -m {module}` is documented, but no module file exists for it.",
                remedy=f"Create {searched[0]}, or correct the module name.",
            )]
        return [Finding(
            checker=self.name, code="MODULE_UNRESOLVED",
            verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=claim,
            detail=(f"`-m {module}` is not under {', '.join(config.source_roots)}, not in the "
                    "standard library and not importable here; it may come from a dependency "
                    "the reader is told to install first, so this is not called broken."),
        )]

    def _maybe_run(self, tokens: list[str], command: str, claim: Claim, repo: RepoIndex,
                   config: CheckConfig, mk: _Makefile | None, *, here: Evidence) -> list[Finding]:
        head = tokens[0]
        if head not in config.command_allowlist and posixpath.basename(head) not in config.command_allowlist:
            return []  # never a candidate for execution; the static pass was the whole check
        if not config.run_commands:
            return [Finding(
                checker=self.name, code="COMMAND_NOT_RUN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=claim,
                detail=(f"`{command}` resolves statically but was not executed: run_commands is "
                        "off, so whether it exits zero is not known."),
            )]
        if reason := _unsafe_reason(command, mk):
            return [Finding(
                checker=self.name, code="COMMAND_NOT_RUN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=claim,
                detail=(f"`{command}` was not executed because {reason}; a review tool must not "
                        "take an irreversible action to be thorough."),
            )]
        ran = Evidence.ran(tokens, cwd=repo.root, timeout=config.command_timeout,
                           env=_run_env(repo, config))
        if ran.exit_code is None:
            return [Finding(
                checker=self.name, code="COMMAND_NOT_RUN",
                verdict=Verdict.UNVERIFIABLE, severity=Severity.INFO, claim=claim,
                detail=(f"`{command}` did not produce an exit status "
                        f"({ran.output.splitlines()[-1] if ran.output else 'no output'})."),
            )]
        if ran.exit_code != 0:
            return [Finding(
                checker=self.name, code="COMMAND_FAILS",
                verdict=Verdict.CONTRADICTED, severity=Severity.ERROR, claim=claim,
                evidence=[here, ran],
                detail=f"`{command}` is documented as working; it exited {ran.exit_code}.",
                remedy="Fix the command or the documentation - the stderr is attached.",
            )]
        return []  # rule 5: a command that works is not news


register(CommandChecker())
