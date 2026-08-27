"""The workspace observed twice: as it is, and as it came to be.

Two sources share this module because they answer two halves of one question
about the same tree. `WorkspaceFileSource` reports *state* - the files as they
sit on disk tonight, which is what a rule needs to ask "does the path this
README links to still exist?". `GitHistorySource` reports *events* - what
changed and why, which is what a rule needs to ask "you renamed this module
three days ago, did the docs follow?". Neither answers the other's question,
and a loop that had only one of them would either propose fixes for files that
no longer exist or never notice that the file it is about to edit was rewritten
this afternoon.

Both are dominated by one risk: a nightly job that walks a developer machine
can trivially spend the night doing it. So the walker prunes hard rather than
filtering late - `node_modules`, virtualenvs, build output and the `.git`
object store are cut at the directory, before a single `stat` is spent inside
them - and the git side makes exactly one subprocess call regardless of how
many commits it reports. Per-commit `git show` calls are the classic version of
this mistake: 500 commits become 500 process spawns, each one a fresh chance to
block on a lock, a hook, or a credential prompt in a job with nobody watching.

The `.gitignore` support is a deliberate subset, not an attempt at git's real
matcher (see `GitIgnore`). The user already wrote down which parts of their tree
are noise; reading half of that statement is worth far more than reading none of
it, and the subset is built to fail towards reading *fewer* files rather than
more.
"""

from __future__ import annotations

import fnmatch
import os
import subprocess
import time
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.reflect.models import (
    ACTOR_HUMAN,
    ACTOR_MACHINE,
    KIND_COMMIT,
    KIND_FILE,
    Signal,
)
from oodarag.reflect.sources.base import Budget, SignalSource, safe_read_text
from oodarag.util.logging import get_logger

log = get_logger("reflect.workspace")

#: Per-file read cap. Anything larger in a source tree is generated, minified,
#: vendored or a data dump: expensive to read, and worthless to a rule that
#: reasons about prose and identifiers. Oversized files are skipped whole rather
#: than truncated, because half a lockfile is not a more useful observation than
#: none of it.
DEFAULT_MAX_FILE_BYTES = 400_000

#: Ceiling on files considered in one walk, so a repo that has grown a million
#: generated fixtures cannot turn the nightly job into a full disk scan.
DEFAULT_MAX_FILES = 20_000

DEFAULT_MAX_COMMITS = 500

#: Wall clock for the single git invocation. Long enough for a large history,
#: short enough that a stale index lock costs seconds rather than the run.
DEFAULT_GIT_TIMEOUT_S = 20.0

#: Directories that are never source material. `.git` is here *and* covered by
#: the dot-directory rule below on purpose: its exclusion must not depend on any
#: pattern file, since a `.gitignore` that failed to parse would otherwise feed
#: the loop a few thousand loose objects.
SKIP_DIRS = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".oodarag",
        ".pytest_cache",
        ".venv",
        ".data",
        "__pycache__",
        "build",
        "dist",
        "node_modules",
        "target",
        "vendor",
        "venv",
    }
)

#: Dot-directories are skipped wholesale (caches, tool state, credentials),
#: except the ones that hold things a human actually wrote and maintains.
KEEP_DOTDIRS = frozenset({".github"})

DOC_EXTS = frozenset({".md", ".markdown", ".mdx", ".rst", ".txt", ".adoc"})

CODE_EXTS = frozenset(
    {
        ".bash", ".c", ".cc", ".cfg", ".cpp", ".cs", ".css", ".go", ".h", ".hpp", ".html",
        ".ini", ".java", ".jl", ".js", ".json", ".jsx", ".kt", ".lua", ".php", ".pl", ".proto",
        ".py", ".r", ".rb", ".rs", ".scala", ".sh", ".sql", ".swift", ".tf", ".toml", ".ts",
        ".tsx", ".yaml", ".yml", ".zsh",
    }
)

#: Checking a monotonic clock costs more than stat-ing a file, so the walk
#: checks its budget every so often rather than every time round.
_BUDGET_CHECK_EVERY = 64

#: ASCII record/unit separators. Nothing a human types into a commit message
#: contains them, which is the entire reason `git log` can be parsed at all:
#: newlines, tabs and blank lines all appear inside real commit bodies.
_RS = "\x1e"
_US = "\x1f"

_PRETTY = f"%H{_US}%at{_US}%an{_US}%s{_US}%b{_RS}"

#: Cap on paths recorded per commit. A vendor bump touching 8,000 files says
#: nothing more than its first 200 paths do, and the whole list would be copied
#: into every report and journal entry that quotes the signal.
MAX_FILES_PER_COMMIT = 200


# -- .gitignore --------------------------------------------------------------


@dataclass(slots=True)
class _Pattern:
    glob: str
    anchored: bool
    dir_only: bool


class GitIgnore:
    """A deliberate subset of `.gitignore`, not an implementation of it.

    Supported: comments and blank lines, exact names, `*`/`?`/`[...]` globs via
    `fnmatch`, a leading `/` (or any interior one) anchoring a pattern to the
    root, and a trailing `/` restricting it to directories. Not supported:
    negation (`!`), `**` as distinct from `*`, and per-directory ignore files
    below the root.

    The direction of the error is chosen rather than accidental. An unsupported
    negation line is dropped instead of approximated, so the exclusion it was
    meant to punch a hole in still stands and the walker reads *fewer* files
    than git would. Missing a file costs one observation; descending into a
    directory the user deliberately excluded - a vendored checkout, a data dump,
    a scratch copy of somebody's secrets - costs the reason the ignore file
    exists. Exclusion of `.git` itself never comes from here at all: it is
    unconditional in the walker, whatever this file does or does not say.
    """

    __slots__ = ("patterns",)

    def __init__(self, patterns: list[_Pattern] | None = None) -> None:
        self.patterns: list[_Pattern] = patterns if patterns is not None else []

    @classmethod
    def load(cls, path: Path) -> GitIgnore:
        """Parse an ignore file, or return an empty matcher if it is unreadable."""
        text = safe_read_text(path)
        if not text:
            return cls()
        patterns: list[_Pattern] = []
        for raw in text.split("\n"):
            line = raw.strip()
            # "!" is a negation we do not implement; see the class docstring for
            # why dropping it is safer than half-honouring it.
            if not line or line.startswith("#") or line.startswith("!"):
                continue
            dir_only = line.endswith("/")
            body = line.rstrip("/")
            anchored = body.startswith("/") or "/" in body
            body = body.lstrip("/")
            if body:
                patterns.append(_Pattern(glob=body, anchored=anchored, dir_only=dir_only))
        return cls(patterns)

    def __len__(self) -> int:
        return len(self.patterns)

    def match(self, rel: str, is_dir: bool = False) -> bool:
        """Whether a root-relative POSIX path is ignored."""
        rel = rel.strip("/")
        if not rel or not self.patterns:
            return False
        segments = rel.split("/")
        # Test every ancestor prefix as well as the path itself: that is what
        # makes "build/" ignore "build/gen/index.html" even when the walker
        # reached the file without pruning the directory first.
        for depth in range(1, len(segments) + 1):
            partial = "/".join(segments[:depth])
            leaf = segments[depth - 1]
            # Anything above the last segment is a directory by construction.
            partial_is_dir = is_dir or depth < len(segments)
            for pat in self.patterns:
                if pat.dir_only and not partial_is_dir:
                    continue
                if fnmatch.fnmatch(partial if pat.anchored else leaf, pat.glob):
                    return True
        return False


# -- files -------------------------------------------------------------------


class WorkspaceFileSource(SignalSource):
    """The project tree as `KIND_FILE` signals, one per readable text file.

    Signals are `ACTOR_MACHINE`: a file's contents are an observation of state,
    not an act somebody performed, and rules that count what the *user* did must
    be able to exclude them without enumerating source keys.

    `skipped` counts files passed over as unreadable, binary, oversized or
    ignored. It is reset per `collect` and exists for observability; nothing
    downstream depends on it.
    """

    key = "workspace:files"
    kinds = (KIND_FILE,)

    def __init__(
        self,
        root: Path | str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.root = Path(root).expanduser() if root is not None else Path.cwd()
        self.config = config or {}
        self.max_file_bytes = _positive_int(
            self.config.get("max_file_bytes"), DEFAULT_MAX_FILE_BYTES
        )
        self.max_files = _positive_int(self.config.get("max_files"), DEFAULT_MAX_FILES)
        self.use_gitignore = bool(self.config.get("use_gitignore", True))
        self.skipped = 0

    def available(self) -> bool:
        try:
            return self.root.is_dir()
        except OSError:
            return False

    def collect(self, since: float, budget: Budget) -> Iterator[Signal]:
        self.skipped = 0
        ignore = GitIgnore.load(self.root / ".gitignore") if self.use_gitignore else GitIgnore()
        seen = 0
        ordinal = 0
        for path, rel in self._walk(ignore):
            if seen % _BUDGET_CHECK_EVERY == 0 and budget.expired():
                log.debug("workspace walk cut short", files=seen, signals=ordinal)
                return
            seen += 1
            if seen > self.max_files:
                log.warn("workspace file cap hit", cap=self.max_files, root=str(self.root))
                return
            sig = self._signal(path, rel, since, ordinal)
            if sig is None:
                continue
            yield sig
            ordinal += 1
        log.debug(
            "workspace scanned", root=str(self.root), files=seen,
            signals=ordinal, skipped=self.skipped, patterns=len(ignore),
        )

    # -- walking -------------------------------------------------------------

    def _walk(self, ignore: GitIgnore) -> Iterator[tuple[Path, str]]:
        """Yield (absolute path, root-relative POSIX path) in a stable order.

        Sorted rather than filesystem order so `ordinal` means the same thing on
        two machines, and `followlinks=False` so a symlink pointing at `/` does
        not make the walk unbounded.
        """
        try:
            walker = os.walk(self.root, topdown=True, onerror=_on_walk_error, followlinks=False)
            for dirpath, dirnames, filenames in walker:
                rel_dir = _rel_posix(Path(dirpath), self.root)
                # In place, because os.walk only honours pruning if the list it
                # handed us is the list it reads back.
                dirnames[:] = sorted(
                    name for name in dirnames if not _skip_dir(name, _join(rel_dir, name), ignore)
                )
                for name in sorted(filenames):
                    rel = _join(rel_dir, name)
                    if ignore.match(rel, is_dir=False):
                        self.skipped += 1
                        continue
                    yield Path(dirpath) / name, rel
        except OSError as e:  # the root vanished mid-walk, or is not readable
            log.warn("workspace walk failed", root=str(self.root), err=str(e)[:200])

    def _signal(self, path: Path, rel: str, since: float, ordinal: int) -> Signal | None:
        try:
            info = path.stat()
        except OSError:  # broken symlink, race with a build, permissions
            self.skipped += 1
            return None
        if since and info.st_mtime < since:
            return None
        if info.st_size > self.max_file_bytes:
            self.skipped += 1
            log.debug("workspace file too large", path=rel, size=info.st_size)
            return None
        text = safe_read_text(path, max_bytes=self.max_file_bytes)
        if not text:
            # Binary, unreadable, or genuinely empty - the three are
            # indistinguishable here and none of them carries an observation.
            self.skipped += 1
            return None
        ext = _extension(rel)
        return Signal(
            kind=KIND_FILE,
            source=self.key,
            text=text,
            ts=info.st_mtime,
            uri=rel,
            session="workspace",
            ordinal=ordinal,
            actor=ACTOR_MACHINE,
            # Built literally rather than through `as_metadata`: detectors index
            # these keys unconditionally, and an extension-less file must still
            # answer metadata["ext"] rather than raise.
            metadata={
                "size": info.st_size,
                "mtime": round(info.st_mtime, 3),
                "ext": ext,
                "line_count": len(text.splitlines()),
                "is_doc": ext in DOC_EXTS,
                "is_code": ext in CODE_EXTS,
                "is_test": "test" in rel.lower(),
                "depth": rel.count("/"),
            },
        )


# -- git ---------------------------------------------------------------------


@dataclass(slots=True)
class _Commit:
    """One commit as `git log` reported it, before it becomes a Signal."""

    sha: str
    ts: float
    author: str
    subject: str
    body: str
    files: list[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    truncated_files: bool = False


class GitHistorySource(SignalSource):
    """Commits in the window as `KIND_COMMIT` signals, from one `git log` call.

    A commit is `ACTOR_HUMAN`: whatever tooling produced the diff, a person
    decided the change was worth recording and wrote a sentence about why. That
    sentence is frequently the only place the intent behind a day's work exists
    in writing, which makes it worth as much to the detectors as a chat prompt.
    """

    key = "git:log"
    kinds = (KIND_COMMIT,)

    def __init__(
        self,
        root: Path | str | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.root = Path(root).expanduser() if root is not None else Path.cwd()
        self.config = config or {}
        self.max_commits = _positive_int(self.config.get("max_commits"), DEFAULT_MAX_COMMITS)
        self.timeout_s = _positive_float(self.config.get("timeout_s"), DEFAULT_GIT_TIMEOUT_S)

    def available(self) -> bool:
        # A worktree and a submodule have a `.git` *file* rather than a
        # directory, so this tests for the entry, not for its type.
        try:
            return (self.root / ".git").exists()
        except OSError:
            return False

    def collect(self, since: float, budget: Budget) -> Iterator[Signal]:
        if budget.expired():
            return
        raw = self._git_log(since)
        if not raw.strip():
            return
        commits = _parse_log(raw)
        for index, commit in enumerate(commits):
            if index % _BUDGET_CHECK_EVERY == 0 and budget.expired():
                return
            body = commit.body.strip()
            text = f"{commit.subject}\n\n{body}" if body else commit.subject
            yield Signal(
                kind=KIND_COMMIT,
                source=self.key,
                text=text,
                ts=commit.ts,
                uri=f"git:{commit.sha[:12]}",
                session="git",
                ordinal=index,
                actor=ACTOR_HUMAN,
                metadata={
                    "sha": commit.sha,
                    "author": commit.author,
                    "subject": commit.subject,
                    "files": commit.files,
                    "insertions": commit.insertions,
                    "deletions": commit.deletions,
                },
            )
        log.debug("git history read", root=str(self.root), commits=len(commits))

    def _git_log(self, since: float) -> str:
        """The one and only subprocess call. Every failure degrades to "".

        `--numstat` rather than `--name-only` because it costs the same walk of
        the diff and additionally yields the line counts, which would otherwise
        need a second pass over the same history.
        """
        argv = [
            "git",
            # Non-ASCII paths come back verbatim instead of C-quoted octal.
            "-c", "core.quotepath=false",
            "log",
            f"-n{self.max_commits}",
            "--no-color",
            "--no-renames",  # keeps every numstat path a plain path
            "--numstat",
            f"--pretty=format:{_PRETTY}",
        ]
        if since > 0:
            # Local time, matching git's own default interpretation. `run()`
            # re-filters on ts anyway, so a boundary disagreement costs nothing.
            argv.append("--since=" + time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(since)))
        try:
            proc = subprocess.run(  # noqa: S603 - fixed argv, never shell=True
                argv,
                cwd=str(self.root),
                capture_output=True,
                text=True,
                errors="replace",  # a commit message in some other encoding is not fatal
                timeout=self.timeout_s,
                check=False,
            )
        except FileNotFoundError:
            log.debug("git is not installed", root=str(self.root))
            return ""
        except subprocess.TimeoutExpired:
            log.warn("git log timed out", root=str(self.root), timeout_s=self.timeout_s)
            return ""
        except (OSError, ValueError) as e:
            log.warn("git log could not run", root=str(self.root), err=str(e)[:200])
            return ""
        if proc.returncode != 0:
            # Not a repository, an empty repository, a broken gitfile: all normal
            # conditions for a directory somebody pointed the loop at.
            log.debug(
                "git log failed", root=str(self.root), rc=proc.returncode,
                err=(proc.stderr or "").strip()[:200],
            )
            return ""
        return proc.stdout or ""


def _parse_log(raw: str) -> list[_Commit]:
    """Split `git log --numstat` output into commits.

    The layout is awkward and worth spelling out. `--pretty=format:` emits the
    header for commit N (ending in our record separator), then the numstat block
    for commit N, then the header for commit N+1. Splitting on the separator
    therefore yields chunks that each begin with the *previous* commit's file
    list and end with the *current* commit's header - so each chunk is cut at its
    first line containing a unit separator, and the front half is attributed
    backwards.
    """
    commits: list[_Commit] = []
    for chunk in raw.split(_RS):
        stat_lines, header = _split_chunk(chunk)
        if commits and stat_lines:
            _apply_numstat(commits[-1], stat_lines)
        commit = _parse_header(header)
        if commit is not None:
            commits.append(commit)
    return commits


def _split_chunk(chunk: str) -> tuple[list[str], str]:
    lines = chunk.split("\n")
    for index, line in enumerate(lines):
        if _US in line:
            return lines[:index], "\n".join(lines[index:])
    return lines, ""  # the tail after the final record is numstat only


def _parse_header(text: str) -> _Commit | None:
    if not text.strip():
        return None
    parts = text.split(_US, 4)
    if len(parts) < 5:
        log.debug("unparsable git record", head=text[:80].replace("\n", " "))
        return None
    sha = parts[0].strip()
    if not _looks_like_sha(sha):
        log.debug("git record without a sha", head=sha[:40])
        return None
    return _Commit(
        sha=sha,
        ts=_parse_epoch(parts[1]),
        author=parts[2].strip(),
        subject=parts[3].strip(),
        body=parts[4],
    )


def _apply_numstat(commit: _Commit, lines: list[str]) -> None:
    """Fold ``<added>\\t<removed>\\t<path>`` lines into the commit they describe.

    Binary files report "-" for both counts; the path still matters, so it is
    kept and only the arithmetic is skipped.
    """
    for line in lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        path = parts[2].strip()
        if not path:
            continue
        commit.insertions += _int_or_zero(parts[0])
        commit.deletions += _int_or_zero(parts[1])
        if len(commit.files) < MAX_FILES_PER_COMMIT:
            commit.files.append(path)
        else:
            commit.truncated_files = True


# -- helpers -----------------------------------------------------------------


def _skip_dir(name: str, rel: str, ignore: GitIgnore) -> bool:
    if name in SKIP_DIRS:
        return True
    if name.startswith(".") and name not in KEEP_DOTDIRS:
        return True
    return ignore.match(rel, is_dir=True)


def _on_walk_error(e: OSError) -> None:
    """os.walk swallows errors by default; this at least records them."""
    log.debug("workspace directory unreadable", err=str(e)[:200])


def _rel_posix(path: Path, root: Path) -> str:
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()
    return "" if rel == "." else rel


def _join(rel_dir: str, name: str) -> str:
    return f"{rel_dir}/{name}" if rel_dir else name


def _extension(rel: str) -> str:
    name = rel.rsplit("/", 1)[-1]
    # A leading dot is a name, not an extension: ".gitignore" has none.
    return "." + name.rsplit(".", 1)[-1].lower() if "." in name[1:] else ""


def _looks_like_sha(value: str) -> bool:
    return len(value) >= 7 and all(ch in "0123456789abcdefABCDEF" for ch in value)


def _parse_epoch(raw: str) -> float:
    try:
        return float(raw.strip())
    except (TypeError, ValueError):
        log.debug("git record with an unreadable timestamp", raw=raw[:40])
        return 0.0


def _int_or_zero(raw: str) -> int:
    try:
        return int(raw.strip())
    except (TypeError, ValueError):
        return 0


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _positive_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default
