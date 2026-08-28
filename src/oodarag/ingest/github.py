"""GitHub connector - the "repository builder".

Turns a repository into retrievable documents across five resource families:
code/docs files, the README, issues, pull requests, and releases. Each becomes
a `RawDocument` with enough metadata that the retriever can filter by path,
language, state or age, and enough provenance that every citation resolves to a
permalink pinned at a commit sha (not a branch, which moves under you).

Cost control is the whole game here. A large repository is tens of thousands of
API calls if you fetch naively, and the REST quota is 5,000/hour on a personal
token. Three things keep it cheap:

1. **Head-sha short circuit.** One call to compare the default branch head with
   the stored cursor. Unchanged? The entire file walk is skipped.
2. **One tree call, not N.** `git/trees?recursive=1` returns every path and blob
   sha in a single request; blob shas tell us which files changed without
   fetching any content.
3. **Raw over API for blobs.** `raw.githubusercontent.com` serves file bytes
   without consuming REST quota, with the API blob endpoint as fallback.
"""

from __future__ import annotations

import base64
import os
import re
import time
import urllib.parse
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.http import (HttpClient, HttpError, TransportError,
                               _same_origin, safe_url)
from oodarag.util.logging import get_logger
from oodarag.util.text import redact_secrets

log = get_logger("ingest.github")

API_ROOT = "https://api.github.com"
RAW_ROOT = "https://raw.githubusercontent.com"

# Extensions worth indexing as text. Everything else is either binary or noise.
TEXT_EXTENSIONS = frozenset("""
    .md .markdown .mdx .rst .txt .adoc .org
    .py .js .jsx .ts .tsx .mjs .cjs .go .rs .java .kt .kts .scala .rb .php .cs .swift
    .c .h .cc .cpp .hpp .hh .m .mm .sh .bash .zsh .fish .ps1 .sql .r .jl .lua .pl .ex .exs
    .html .css .scss .less .vue .svelte
    .json .yaml .yml .toml .ini .cfg .conf .env.example .properties .gradle .tf .tfvars
    .proto .graphql .gql .ipynb .dockerfile .mk .cmake .bzl
""".split())

# Files that are technically text but carry no retrievable meaning.
SKIP_PATH_RE = re.compile(
    r"(^|/)(\.git|node_modules|vendor|third_party|dist|build|out|target|\.venv|venv|"
    r"__pycache__|\.mypy_cache|\.pytest_cache|\.next|\.nuxt|coverage|htmlcov)(/|$)"
    r"|(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|"
    r"go\.sum|composer\.lock|Gemfile\.lock|uv\.lock|\.min\.(js|css))$"
    r"|\.(min|bundle|generated|pb|_pb2)\.",
    re.I,
)

LANGUAGE_BY_EXT = {
    ".py": "python", ".js": "javascript", ".jsx": "javascript", ".ts": "typescript",
    ".tsx": "typescript", ".go": "go", ".rs": "rust", ".java": "java", ".kt": "kotlin",
    ".rb": "ruby", ".php": "php", ".cs": "csharp", ".swift": "swift", ".c": "c",
    ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".hpp": "cpp", ".sh": "bash", ".bash": "bash",
    ".sql": "sql", ".md": "markdown", ".rst": "rst", ".html": "html", ".css": "css",
    ".yaml": "yaml", ".yml": "yaml", ".json": "json", ".toml": "toml", ".tf": "terraform",
    ".proto": "protobuf", ".ipynb": "jupyter", ".lua": "lua", ".r": "r", ".jl": "julia",
}


class GitHubError(Exception):
    pass


@dataclass
class GitHubClient:
    """Thin REST wrapper: auth, pagination, quota awareness."""

    token: str | None = None
    client: HttpClient | None = None
    api_root: str = API_ROOT

    def __post_init__(self) -> None:
        self.token = self.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if self.client is None:
            # 10 rps is well inside GitHub's guidance and leaves headroom for
            # concurrent tooling using the same token.
            self.client = HttpClient(rate_per_sec=10.0, burst=15, default_headers=headers)
        else:
            self.client.default_headers.update(headers)

    @property
    def authenticated(self) -> bool:
        return bool(self.token)

    def get(self, path: str, **params: Any) -> Any:
        url = path if path.startswith("http") else f"{self.api_root}{path}"
        if params:
            url = f"{url}?{urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})}"
        return self.client.get_json(url)

    def paginate(self, path: str, *, per_page: int = 100, max_items: int = 1000,
                 **params: Any) -> Iterator[dict[str, Any]]:
        """Walk `Link: rel="next"` pagination, bounded by `max_items`."""
        url = path if path.startswith("http") else f"{self.api_root}{path}"
        query = {k: v for k, v in params.items() if v is not None}
        query["per_page"] = per_page
        url = f"{url}?{urllib.parse.urlencode(query)}"
        yielded = 0
        while url and yielded < max_items:
            resp = self.client.get(url, headers={"Accept": "application/vnd.github+json"})
            payload = resp.json()
            items = payload if isinstance(payload, list) else payload.get("items", [])
            for item in items:
                yield item
                yielded += 1
                if yielded >= max_items:
                    return
            # The Link header is a server-supplied URL that this client then
            # fetches WITH the bearer token attached. _SafeRedirectHandler
            # strips credentials across origins on a redirect; following a
            # Link header walks around that protection, because it is a fresh
            # request rather than a redirect. TLS makes a hostile
            # api.github.com unlikely rather than impossible, and the cost of
            # pinning the origin is one comparison.
            nxt = _next_link(resp.headers.get("link", ""))
            if nxt and not _same_origin(url, nxt):
                log.warn("refusing cross-origin pagination",
                         from_url=safe_url(url), to_url=safe_url(nxt))
                return
            url = nxt

    def rate_limit(self) -> dict[str, Any]:
        try:
            return self.get("/rate_limit").get("resources", {}).get("core", {})
        except (HttpError, TransportError) as e:
            return {"error": str(e)[:200]}


def _next_link(link_header: str) -> str | None:
    for part in link_header.split(","):
        segments = part.split(";")
        if len(segments) < 2:
            continue
        if 'rel="next"' in segments[1].replace(" ", "").replace("'", '"'):
            return segments[0].strip().strip("<>")
    return None


@dataclass
class GitHubConnector(Connector):
    """Ingest one repository.

    `resources` selects what to pull. Defaults cover the material that actually
    answers questions about a codebase: the files and the README. Issues and PRs
    are opt-in because they are large and often noisier than they are useful.
    """

    owner: str = ""
    repo: str = ""
    ref: str | None = None                       # defaults to the repo's default branch
    resources: tuple[str, ...] = ("repo", "readme", "files")
    include_paths: tuple[str, ...] = ()
    exclude_paths: tuple[str, ...] = ()
    max_file_bytes: int = 400_000
    max_files: int = 3000
    max_issues: int = 200
    max_commits: int = 200
    authority: float = 1.2                        # a repo is authoritative about itself
    gh: GitHubClient = field(default_factory=GitHubClient)
    stats: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.owner or not self.repo:
            raise ValueError("GitHubConnector requires owner and repo")
        self.key = f"github:{self.owner}/{self.repo}"

    # ------------------------------------------------------------------ helpers

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}"

    def _permalink(self, path: str, sha: str, line: int | None = None) -> str:
        anchor = f"#L{line}" if line else ""
        return f"https://github.com/{self.slug}/blob/{sha}/{path}{anchor}"

    def _wanted_path(self, path: str, size: int) -> tuple[bool, str]:
        if SKIP_PATH_RE.search(path):
            return False, "skip_pattern"
        if size > self.max_file_bytes:
            return False, "too_large"
        lowered = path.lower()
        base = lowered.rsplit("/", 1)[-1]
        ext = "." + base.rsplit(".", 1)[-1] if "." in base else ""
        known_no_ext = base in {"dockerfile", "makefile", "license", "notice", "codeowners",
                                "readme", "changelog", "contributing"}
        if ext not in TEXT_EXTENSIONS and not known_no_ext:
            return False, "not_text"
        if self.exclude_paths and any(re.search(p, path, re.I) for p in self.exclude_paths):
            return False, "excluded"
        if self.include_paths and not any(re.search(p, path, re.I) for p in self.include_paths):
            return False, "not_included"
        return True, ""

    def _fetch_blob(self, path: str, sha: str, ref: str) -> str | None:
        """Raw first (free), API blob second (costs quota but always works)."""
        raw_url = f"{RAW_ROOT}/{self.slug}/{ref}/{urllib.parse.quote(path)}"
        try:
            resp = self.gh.client.get(raw_url, allow_status=(404, 403))
            if resp.status == 200:
                if b"\x00" in resp.body[:8192]:
                    return None  # binary despite the extension
                return resp.text
        except (HttpError, TransportError) as e:
            log.debug("raw fetch failed, falling back to API", path=path, err=str(e)[:120])
        try:
            blob = self.gh.get(f"/repos/{self.slug}/git/blobs/{sha}")
            if blob.get("encoding") == "base64":
                data = base64.b64decode(blob.get("content", ""))
                if b"\x00" in data[:8192]:
                    return None
                return data.decode("utf-8", "replace")
            return blob.get("content")
        except (HttpError, TransportError, ValueError) as e:
            log.warn("blob fetch failed", path=path, err=str(e)[:160])
            return None

    # -------------------------------------------------------------------- fetch

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        counts: dict[str, int] = {}
        skipped: dict[str, int] = {}

        meta = self.gh.get(f"/repos/{self.slug}")
        ref = self.ref or meta.get("default_branch") or "main"
        head = self.gh.get(f"/repos/{self.slug}/commits/{ref}")
        head_sha = head.get("sha", ref)
        self.stats = {"ref": ref, "head_sha": head_sha, "default_branch": meta.get("default_branch")}

        if "repo" in self.resources:
            yield self._repo_document(meta, ref, head_sha)
            counts["repo"] = 1

        if "readme" in self.resources:
            if (doc := self._readme_document(head_sha)) is not None:
                yield doc
                counts["readme"] = 1

        if "files" in self.resources:
            unchanged_head = cursor.get("head_sha") == head_sha
            prior_blobs: dict[str, str] = cursor.get("blob_shas", {})
            if unchanged_head and prior_blobs:
                # Nothing moved since last run; the base class would report every
                # file "unchanged" anyway, so skip the fetch entirely.
                log.info("head unchanged, skipping file walk", repo=self.slug, sha=head_sha[:8])
                skipped["head_unchanged"] = len(prior_blobs)
            else:
                blob_shas: dict[str, str] = {}
                emitted = 0
                tree = self.gh.get(f"/repos/{self.slug}/git/trees/{head_sha}", recursive="1")
                if tree.get("truncated"):
                    log.warn("tree truncated by GitHub; some files will be missed",
                             repo=self.slug)
                    skipped["tree_truncated"] = 1
                for entry in tree.get("tree", []):
                    if entry.get("type") != "blob":
                        continue
                    path = entry.get("path", "")
                    size = int(entry.get("size") or 0)
                    ok, reason = self._wanted_path(path, size)
                    if not ok:
                        skipped[reason] = skipped.get(reason, 0) + 1
                        continue
                    if emitted >= self.max_files:
                        skipped["max_files"] = skipped.get("max_files", 0) + 1
                        continue
                    blob_sha = entry.get("sha", "")
                    blob_shas[path] = blob_sha
                    # Blob sha is git's own content hash: if it matches the last
                    # run we already have this file's bytes and never fetch them.
                    if prior_blobs.get(path) == blob_sha and not cursor.get("force_refetch"):
                        skipped["blob_unchanged"] = skipped.get("blob_unchanged", 0) + 1
                        continue
                    text = self._fetch_blob(path, blob_sha, head_sha)
                    if text is None:
                        skipped["binary_or_failed"] = skipped.get("binary_or_failed", 0) + 1
                        continue
                    emitted += 1
                    yield self._file_document(path, text, size, head_sha, blob_sha, ref)
                counts["files"] = emitted
                self.stats["blob_shas"] = blob_shas

        if "issues" in self.resources or "pulls" in self.resources:
            want_pulls = "pulls" in self.resources
            want_issues = "issues" in self.resources
            n = 0
            since = cursor.get("issues_since")
            for issue in self.gh.paginate(
                f"/repos/{self.slug}/issues", state="all", since=since,
                sort="updated", direction="desc", max_items=self.max_issues,
            ):
                is_pr = "pull_request" in issue
                if (is_pr and not want_pulls) or (not is_pr and not want_issues):
                    continue
                yield self._issue_document(issue)
                n += 1
            counts["issues_and_pulls"] = n
            self.stats["issues_since"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if "commits" in self.resources:
            n = 0
            for commit in self.gh.paginate(
                f"/repos/{self.slug}/commits", sha=ref, max_items=self.max_commits,
            ):
                yield self._commit_document(commit)
                n += 1
            counts["commits"] = n

        if "releases" in self.resources:
            n = 0
            for release in self.gh.paginate(f"/repos/{self.slug}/releases", max_items=100):
                if doc := self._release_document(release):
                    yield doc
                    n += 1
            counts["releases"] = n

        self.stats["counts"] = counts
        self.stats["skipped"] = skipped
        log.info("github fetch complete", repo=self.slug, **counts)

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["head_sha"] = self.stats.get("head_sha", cursor.get("head_sha"))
        cursor["ref"] = self.stats.get("ref", cursor.get("ref"))
        if blobs := self.stats.get("blob_shas"):
            cursor["blob_shas"] = blobs
        if since := self.stats.get("issues_since"):
            cursor["issues_since"] = since
        cursor.pop("force_refetch", None)
        cursor["last_stats"] = {"counts": self.stats.get("counts", {}),
                                "skipped": self.stats.get("skipped", {})}
        return cursor

    # ---------------------------------------------------------------- documents

    def _base_meta(self, kind: str, head_sha: str = "") -> dict[str, Any]:
        return {
            "kind": kind,
            "repo": self.slug,
            "owner": self.owner,
            "authority": self.authority,
            **({"commit": head_sha} if head_sha else {}),
        }

    def _repo_document(self, meta: dict[str, Any], ref: str, head_sha: str) -> RawDocument:
        topics = meta.get("topics") or []
        body = "\n".join(
            filter(None, [
                f"# {meta.get('full_name', self.slug)}",
                meta.get("description") or "",
                f"\nPrimary language: {meta.get('language') or 'unknown'}",
                f"Default branch: {meta.get('default_branch')}",
                f"Topics: {', '.join(topics) if topics else 'none'}",
                f"License: {(meta.get('license') or {}).get('spdx_id') or 'none'}",
                f"Stars: {meta.get('stargazers_count', 0)} | Forks: {meta.get('forks_count', 0)}"
                f" | Open issues: {meta.get('open_issues_count', 0)}",
                f"Homepage: {meta.get('homepage') or 'none'}",
                f"Created: {meta.get('created_at')} | Last push: {meta.get('pushed_at')}",
            ])
        )
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#repo",
            uri=meta.get("html_url", f"https://github.com/{self.slug}"),
            title=f"{self.slug} - repository overview",
            text=body,
            metadata={
                **self._base_meta("repo", head_sha),
                "ref": ref,
                "stars": meta.get("stargazers_count", 0),
                "language": meta.get("language"),
                "topics": topics,
                "license": (meta.get("license") or {}).get("spdx_id"),
                "pushed_at": meta.get("pushed_at"),
            },
        )

    def _readme_document(self, head_sha: str) -> RawDocument | None:
        try:
            readme = self.gh.get(f"/repos/{self.slug}/readme")
        except (HttpError, TransportError) as e:
            log.debug("no readme", repo=self.slug, err=str(e)[:100])
            return None
        try:
            text = base64.b64decode(readme.get("content", "")).decode("utf-8", "replace")
        except (ValueError, TypeError):
            return None
        path = readme.get("path", "README.md")
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#readme:{readme.get('sha','')}",
            uri=self._permalink(path, head_sha),
            title=f"{self.slug} - {path}",
            text=redact_secrets(text),
            metadata={**self._base_meta("readme", head_sha), "path": path, "language": "markdown"},
        )

    def _file_document(self, path: str, text: str, size: int, head_sha: str,
                       blob_sha: str, ref: str) -> RawDocument:
        ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#file:{path}",
            uri=self._permalink(path, head_sha),
            title=f"{self.slug}/{path}",
            text=redact_secrets(text),
            metadata={
                **self._base_meta("file", head_sha),
                "path": path,
                "dir": path.rsplit("/", 1)[0] if "/" in path else "",
                "filename": path.rsplit("/", 1)[-1],
                "ext": ext,
                "language": LANGUAGE_BY_EXT.get(ext, "text"),
                "size": size,
                "blob_sha": blob_sha,
                "ref": ref,
                "is_doc": ext in {".md", ".markdown", ".rst", ".txt", ".adoc", ".mdx"},
                "is_test": bool(re.search(r"(^|/)(tests?|spec)/|_test\.|test_|\.spec\.", path, re.I)),
            },
        )

    def _issue_document(self, issue: dict[str, Any]) -> RawDocument:
        is_pr = "pull_request" in issue
        number = issue.get("number")
        labels = [lbl.get("name", "") for lbl in issue.get("labels", []) if isinstance(lbl, dict)]
        parts = [
            f"# {'PR' if is_pr else 'Issue'} #{number}: {issue.get('title','')}",
            f"State: {issue.get('state')} | Author: {(issue.get('user') or {}).get('login')}"
            f" | Comments: {issue.get('comments', 0)}",
            f"Labels: {', '.join(labels) if labels else 'none'}",
            f"Opened: {issue.get('created_at')} | Updated: {issue.get('updated_at')}",
            "",
            issue.get("body") or "(no description)",
        ]
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#{'pr' if is_pr else 'issue'}:{number}",
            uri=issue.get("html_url", ""),
            title=f"{self.slug} {'PR' if is_pr else 'issue'} #{number}: {issue.get('title','')}",
            text=redact_secrets("\n".join(parts)),
            metadata={
                **self._base_meta("pull_request" if is_pr else "issue"),
                "number": number,
                "state": issue.get("state"),
                "labels": labels,
                "author": (issue.get("user") or {}).get("login"),
                "created_at": issue.get("created_at"),
                "updated_at": issue.get("updated_at"),
                "comment_count": issue.get("comments", 0),
            },
        )

    def _commit_document(self, commit: dict[str, Any]) -> RawDocument:
        info = commit.get("commit", {})
        sha = commit.get("sha", "")
        message = info.get("message", "")
        author = (info.get("author") or {})
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#commit:{sha}",
            uri=commit.get("html_url", ""),
            title=f"{self.slug} commit {sha[:8]}: {message.splitlines()[0][:80] if message else ''}",
            text=redact_secrets(f"# Commit {sha[:8]}\n\nAuthor: {author.get('name')}"
                                f"\nDate: {author.get('date')}\n\n{message}"),
            metadata={
                **self._base_meta("commit"),
                "sha": sha,
                "author": author.get("name"),
                "date": author.get("date"),
            },
        )

    def _release_document(self, release: dict[str, Any]) -> RawDocument | None:
        body = release.get("body") or ""
        if not body.strip():
            return None
        tag = release.get("tag_name", "")
        return RawDocument(
            source_system="github",
            external_id=f"{self.slug}#release:{tag}",
            uri=release.get("html_url", ""),
            title=f"{self.slug} release {tag}: {release.get('name') or ''}".strip(),
            text=redact_secrets(f"# Release {tag}\n\nPublished: {release.get('published_at')}\n\n{body}"),
            metadata={
                **self._base_meta("release"),
                "tag": tag,
                "prerelease": release.get("prerelease", False),
                "published_at": release.get("published_at"),
            },
        )
