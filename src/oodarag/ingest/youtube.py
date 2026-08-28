"""YouTube ingestion over the Data API, with an offline path for captions.

Reaching YouTube from a filtered network is not one problem but three, and they
have different answers:

  1. `www.youtube.com`, `youtu.be`, `i.ytimg.com` and every third-party mirror
     (Invidious, Piped, reader-proxies, transcript scrapers) are refused at the
     proxy's CONNECT when egress is an allowlist. Nothing in this file tries to
     scrape them; a blocked host stays blocked however it is dressed up.
  2. `youtube.googleapis.com` is a different host with a different policy, and
     is commonly reachable where the consumer site is not. It answers
     unauthenticated calls with HTTP 403 `PERMISSION_DENIED`, which
     `oodarag.net.reachability` reports as AUTH_REQUIRED rather than as a
     block — the remedy is a key, not a firewall change.
  3. Caption *text* for a video you do not own is not available from the Data
     API at all, at any quota, with any API key: `captions.download` authorises
     against the video owner. So transcripts arrive from a local export
     directory instead, and the connector says which videos lack one rather
     than quietly indexing title-and-description as though it were a transcript.

A manifest may live in a **GitHub repository** rather than on disk, which is
the practical answer here: `raw.githubusercontent.com` serves any public
repository and is on this container's allowlist, while `www.youtube.com` is
refused at CONNECT. A repository holding transcripts is therefore reachable
where the source site is not — the material is fetched from a host that answers
instead of scraped from one that does not.

There are therefore three ways in, and every document records which one it came
from in `transcript_source`:

  - `captions`      — a real caption file was read; the text is the speech.
  - `metadata_only` — title, description and channel; no transcript exists here.
  - `api`           — metadata fetched live from the Data API.

The connector never fabricates the level above the one it reached, and it will
not promote a curated summary to `captions`. A paragraph *about* a video, stored
next to it, reads exactly like a transcript once it has been chunked — and a
citation pointing at it would look verbatim while being someone's paraphrase.
That is the failure the citation contract exists to prevent, so the distinction
is a stored field rather than a convention.

The vocabulary above is deliberately the same as the one used by the sibling
branch `claude/rag-system-data-pipeline-rdkde9`, which built a manifest format
for the same problem. Two implementations of one pipeline are already one too
many; they should at least agree on what their documents claim.
"""

from __future__ import annotations

import html
import json
import os
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.net.reachability import Barrier, classify_exception
from oodarag.util.http import HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger
from oodarag.util.text import clean, redact_secrets

log = get_logger("ingest.youtube")

API_ROOT = "https://youtube.googleapis.com/youtube/v3"

#: Quota cost in units per call. The default project allowance is 10,000 units
#: a day, resetting at midnight Pacific. The costs differ by two orders of
#: magnitude, which is why `search` is opt-in: 100 search calls spend the entire
#: daily allowance, while the same 100 calls to `videos` — each carrying up to
#: 50 ids — spend 100 units and cover 5,000 videos.
QUOTA_COST = {
    "videos": 1,
    "playlistItems": 1,
    "channels": 1,
    "captions": 50,
    "captions/download": 200,
    "search": 100,
}

#: The API's default daily allowance, for budget arithmetic before a run.
DAILY_QUOTA_UNITS = 10_000

#: Ids per `videos.list` call. The call costs one unit whether it carries one
#: id or fifty, so batching is a 50x quota saving for free.
VIDEOS_PER_CALL = 50

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URL_ID_RE = re.compile(r"(?:v=|/vi?/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})")


class YouTubeUnavailable(Exception):
    """The API could not be used, with the barrier that stopped it attached."""

    def __init__(self, barrier: Barrier, detail: str) -> None:
        super().__init__(f"{barrier.value}: {detail} — remedy: {barrier.remedy}")
        self.barrier = barrier
        self.detail = detail


def extract_video_id(value: str) -> str | None:
    """Accept a bare id, a watch URL, a short link, an embed or a Shorts URL."""
    value = value.strip()
    if _VIDEO_ID_RE.match(value):
        return value
    if m := _URL_ID_RE.search(value):
        return m.group(1)
    return None


# --------------------------------------------------------------------- captions


@dataclass(slots=True)
class Transcript:
    """A caption track read from disk, with its cues preserved.

    Cue timings are kept because they are the only stable anchor a video has:
    a chunk of a transcript can cite `?t=1234` and land the reader on the
    sentence it quoted, which is the video equivalent of a line number.
    """

    video_id: str
    cues: list[tuple[float, str]] = field(default_factory=list)
    source_path: str = ""

    @property
    def text(self) -> str:
        return "\n".join(t for _, t in self.cues)

    def with_timestamps(self) -> str:
        return "\n".join(f"[{_hhmmss(ts)}] {t}" for ts, t in self.cues)


def _hhmmss(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


_TS_RE = re.compile(r"(\d{1,2}):(\d{2}):(\d{2})[.,](\d{1,3})")
_TAG_RE = re.compile(r"<[^>]+>")


def parse_caption_file(path: Path) -> Transcript:
    """Parse a caption file from disk. See `parse_caption_text` for the format."""
    return parse_caption_text(
        path.read_text("utf-8", errors="replace"),
        path.stem.split(".")[0],
        str(path),
    )


def parse_caption_text(raw: str, video_id: str, source: str = "") -> Transcript:
    """Parse WebVTT or SubRip into timed cues.

    Both formats are handled by the same pass because they differ only in the
    header and the cue-number line, and a parser that accepts both means an
    operator does not have to care which one their export tool produced.
    Consecutive duplicate lines are collapsed: YouTube's rolling captions
    repeat each line as it scrolls, which would otherwise triple the tokens.
    """
    cues: list[tuple[float, str]] = []
    current: float | None = None
    buffer: list[str] = []

    def flush() -> None:
        if current is None:
            return
        text = clean(_TAG_RE.sub("", " ".join(buffer)))
        text = html.unescape(text).strip()
        if text and (not cues or cues[-1][1] != text):
            cues.append((current, text))

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            flush()
            current, buffer = None, []
            continue
        if "-->" in stripped:
            flush()
            buffer = []
            start = stripped.split("-->")[0].strip()
            if m := _TS_RE.search(start):
                h, mi, s, ms = m.groups()
                current = int(h) * 3600 + int(mi) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000
            else:
                current = 0.0
            continue
        if stripped.isdigit() and current is None:
            continue  # SubRip cue number
        if stripped.upper().startswith(("WEBVTT", "KIND:", "LANGUAGE:", "NOTE")):
            continue
        buffer.append(stripped)
    flush()
    return Transcript(video_id=video_id, cues=cues, source_path=source)


#: How the text of a video document was obtained. Ordered strongest first.
TRANSCRIPT_SOURCES = ("captions", "api", "metadata_only", "failed")


@dataclass(slots=True)
class ManifestEntry:
    """One video described in a committed manifest.

    A manifest is how a video corpus survives an environment that cannot reach
    YouTube: the ids and titles are gathered once, by whatever path works
    (search reaches metadata that fetch cannot), and committed. The connector
    then hydrates real captions wherever egress permits and degrades to
    metadata elsewhere, rather than being written for the blocked case and
    stuck there.
    """

    video_id: str
    title: str = ""
    channel: str = ""
    presenter: str = ""
    verification: str = ""
    topics: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ManifestEntry | None:
        raw_id = str(payload.get("video_id", "")).strip()
        video_id = extract_video_id(raw_id)
        if not video_id:
            return None
        return cls(
            video_id=video_id,
            title=str(payload.get("title", "")).strip(),
            channel=str(payload.get("channel", "")).strip(),
            presenter=str(payload.get("presenter", "")).strip(),
            verification=str(payload.get("verification", "")).strip(),
            topics=[str(t) for t in payload.get("topics", []) if str(t).strip()],
            related=[str(r) for r in payload.get("related", []) if str(r).strip()],
        )


#: Accepted forms for a repository-hosted manifest, most convenient first:
#:   owner/repo                      -> default branch, corpus/manifest.json
#:   owner/repo@ref                  -> that ref
#:   owner/repo@ref:path/to/file     -> that path
_REPO_SPEC = re.compile(r"^(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)"
                        r"(?:@(?P<ref>[\w./-]+))?"
                        r"(?::(?P<path>[\w./-]+))?$")

DEFAULT_MANIFEST_PATH = "corpus/manifest.json"
RAW_HOST = "https://raw.githubusercontent.com"


def resolve_manifest_location(spec: str) -> str:
    """Turn a manifest reference into something fetchable or readable.

    A URL and a filesystem path both pass through unchanged. A bare
    `owner/repo` is expanded to a raw.githubusercontent.com URL, because that
    is the form an operator actually wants to type and the host that actually
    answers.
    """
    spec = str(spec).strip()
    if spec.startswith(("http://", "https://")):
        return spec
    if Path(spec).exists():
        return spec
    m = _REPO_SPEC.match(spec)
    if not m:
        return spec  # a path that does not exist yet; the caller reports it
    ref = m.group("ref") or "main"
    path = m.group("path") or DEFAULT_MANIFEST_PATH
    return f"{RAW_HOST}/{m.group('owner')}/{m.group('repo')}/{ref}/{path}"


def _read_location(location: str, client: HttpClient | None = None) -> tuple[str, list[str]]:
    """Read a manifest's bytes from a URL or from disk, reporting the barrier."""
    if not location.startswith(("http://", "https://")):
        try:
            return Path(location).read_text("utf-8"), []
        except OSError as e:
            return "", [f"{location}: {type(e).__name__}: {e}"]

    http = client or HttpClient(rate_per_sec=5.0, burst=5)
    try:
        return http.get(location).text, []
    except (HttpError, TransportError, OSError) as exc:
        barrier, detail = classify_exception(exc)
        # Naming the barrier matters more here than anywhere: a repository that
        # is merely private reads identically to one that does not exist, and
        # only one of those is fixable by the operator.
        return "", [f"{location}: {barrier.value}: {detail[:160]} — {barrier.remedy}"]


def load_manifest(
    path: str | Path, client: HttpClient | None = None
) -> tuple[list[ManifestEntry], list[str]]:
    """Read a video manifest from a path, a URL, or an `owner/repo` reference.

    Keys beginning with an underscore are documentation for a human reader and
    are ignored. A malformed entry is reported rather than skipped silently: a
    corpus that quietly shrank is worse than one that failed loudly, because
    every downstream number improves either way.
    """
    location = resolve_manifest_location(str(path))
    errors: list[str] = []
    raw_text, read_errors = _read_location(location, client)
    if read_errors:
        return [], read_errors
    try:
        payload = json.loads(raw_text)
    except (ValueError, TypeError) as e:
        return [], [f"{location}: {type(e).__name__}: {e}"]
    p = location

    raw = payload.get("videos") if isinstance(payload, dict) else payload
    if not isinstance(raw, list):
        return [], [f"{p}: no 'videos' list found"]

    entries: list[ManifestEntry] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            errors.append(f"{p}[{i}]: entry is not an object")
            continue
        entry = ManifestEntry.from_dict(item)
        if entry is None:
            errors.append(f"{p}[{i}]: no usable video_id")
            continue
        entries.append(entry)
    return entries, errors


class TranscriptStore:
    """Caption files, keyed by video id, from a directory or a repository.

    This is the egress-free half of the connector — or rather, the half that
    does not need *YouTube*. Two ways to fill it:

    - A local directory. An owner who can reach YouTube from their own machine
      exports captions once and drops them here.
    - A base URL, typically inside a GitHub repository. A caption file
      committed to a repo is served by `raw.githubusercontent.com`, which
      answers, while `www.youtube.com` is refused at CONNECT — so the same
      bytes are reachable by a different route.

    A remote store cannot list its directory, so it fetches by convention:
    `<base>/<video_id><suffix>` for each suffix in turn. A miss is a normal
    outcome, not an error, and leaves the document at `metadata_only`.
    """

    SUFFIXES = (".vtt", ".srt", ".en.vtt", ".en.srt")

    def __init__(
        self,
        directory: str | Path | None,
        *,
        base_url: str = "",
        client: HttpClient | None = None,
    ) -> None:
        self.directory = Path(directory) if directory and not base_url else None
        self.base_url = base_url.rstrip("/")
        self.client = client
        self._index: dict[str, Path] = {}
        self._remote_cache: dict[str, Transcript | None] = {}
        if self.directory and self.directory.is_dir():
            for p in sorted(self.directory.iterdir()):
                if p.suffix.lower() in (".vtt", ".srt"):
                    vid = extract_video_id(p.stem.split(".")[0]) or p.stem.split(".")[0]
                    self._index.setdefault(vid, p)

    def __len__(self) -> int:
        return len(self._index)

    @property
    def available(self) -> bool:
        return bool(self._index) or bool(self.base_url)

    def get(self, video_id: str) -> Transcript | None:
        if self.base_url:
            return self._get_remote(video_id)
        path = self._index.get(video_id)
        if path is None:
            return None
        try:
            return parse_caption_file(path)
        except OSError as e:
            log.warn("caption file unreadable", path=str(path), err=str(e))
            return None

    def _get_remote(self, video_id: str) -> Transcript | None:
        """Fetch a caption file from the repository, by convention.

        Results are cached including misses, so a manifest of fifty videos with
        no captions costs one request each rather than one per suffix per run.
        """
        if video_id in self._remote_cache:
            return self._remote_cache[video_id]
        http = self.client or HttpClient(rate_per_sec=5.0, burst=5)
        found: Transcript | None = None
        for suffix in self.SUFFIXES:
            url = f"{self.base_url}/{video_id}{suffix}"
            try:
                resp = http.get(url, allow_status=(404,))
            except (HttpError, TransportError, OSError) as exc:
                barrier, _ = classify_exception(exc)
                log.debug("caption fetch failed", url=url, barrier=barrier.value)
                continue
            if resp.status == 404 or not resp.text.strip():
                continue
            found = parse_caption_text(resp.text, video_id, url)
            break
        self._remote_cache[video_id] = found
        return found


# ------------------------------------------------------------------------ client


@dataclass
class YouTubeClient:
    """Thin Data API client that reports barriers instead of raising blindly."""

    api_key: str = ""
    client: HttpClient | None = None
    quota_spent: int = 0

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("YOUTUBE_API_KEY", "")
        if self.client is None:
            # The Data API's own guidance is a low steady rate; the default
            # quota is spent by volume of calls, not by their speed.
            self.client = HttpClient(rate_per_sec=5.0, burst=5)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def call(self, resource: str, **params: Any) -> dict[str, Any]:
        """One Data API call. Raises YouTubeUnavailable with a named barrier."""
        if not self.api_key:
            raise YouTubeUnavailable(
                Barrier.AUTH_REQUIRED,
                "no API key: set YOUTUBE_API_KEY, or pass api_key=. The Data API "
                "host is reachable but rejects unregistered callers",
            )
        query = {k: v for k, v in params.items() if v not in (None, "", [])}
        query["key"] = self.api_key
        url = f"{API_ROOT}/{resource}?" + _urlencode(query)
        assert self.client is not None
        try:
            resp = self.client.get(url, headers={"Accept": "application/json"})
        except (HttpError, TransportError, OSError) as exc:
            barrier, detail = classify_exception(exc)
            if isinstance(exc, HttpError):
                barrier = classify_api_error(exc.status, exc.body)
            raise YouTubeUnavailable(barrier, _redact_key(detail, self.api_key)) from exc
        self.quota_spent += QUOTA_COST.get(resource.split("/")[0], 1)
        return resp.json()

    def videos(self, ids: list[str]) -> list[dict[str, Any]]:
        """Metadata for up to 50 ids per call, which is the API's page limit."""
        out: list[dict[str, Any]] = []
        for batch in _batched(ids, 50):
            payload = self.call(
                "videos",
                part="snippet,contentDetails,statistics,status",
                id=",".join(batch),
                maxResults=50,
            )
            out.extend(payload.get("items", []))
        return out

    def playlist_video_ids(self, playlist_id: str, *, max_items: int = 200) -> list[str]:
        ids: list[str] = []
        page: str | None = None
        while len(ids) < max_items:
            payload = self.call(
                "playlistItems",
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=min(50, max_items - len(ids)),
                pageToken=page,
            )
            for item in payload.get("items", []):
                vid = item.get("contentDetails", {}).get("videoId")
                if vid:
                    ids.append(vid)
            page = payload.get("nextPageToken")
            if not page:
                break
        return ids

    def caption_tracks(self, video_id: str) -> list[dict[str, Any]]:
        """List caption *track metadata* for a video. Never the caption text.

        Two cautions, both load-bearing:

        - This costs 50 quota units per call — fifty times a `videos.list` —
          so it is never called during a normal ingest run. It exists to answer
          "does a transcript exist for this video at all", which is worth
          knowing before an operator goes and exports one by hand.
        - `captions.list` publishes no read-only OAuth scope; it accepts only
          the write-grade scopes. Whether a plain API key succeeds against a
          video the caller does not own is **not established here** — it was
          never exercised with a valid key. Treat a failure as expected and
          read the barrier, rather than assuming the call is broken.

        Caption *text* is not obtainable this way at any quota or scope: see
        this module's docstring.
        """
        payload = self.call("captions", part="snippet", videoId=video_id)
        return payload.get("items", [])


def classify_api_error(status: int, body: str) -> Barrier:
    """Map a Data API error onto a barrier, discriminating on the JSON, not the prose.

    The three credential failures are genuinely different and the API separates
    them by *status* as well as by reason, so matching on the message text alone
    gets them wrong:

      - no key at all        -> HTTP 403, status `PERMISSION_DENIED`,
                                reason `forbidden`
      - key present, invalid -> HTTP 400, status `INVALID_ARGUMENT`, with
                                `details[].reason == "API_KEY_INVALID"`
      - quota spent          -> HTTP 403, with `errors[].domain == "youtube.quota"`
                                and reason `quotaExceeded`

    All three are AUTH_REQUIRED or RATE_LIMITED rather than FORBIDDEN, because
    all three are fixable by the operator. A 400 in particular would otherwise
    fall through to UNKNOWN and be reported as an unclassifiable failure when
    the real message is "your key is wrong".
    """
    reasons, domains, api_status = _error_reasons(body)

    if "quotaExceeded" in reasons or "youtube.quota" in domains:
        # Not retryable within the day: the allowance resets at midnight
        # Pacific, so a retry loop simply re-spends the failure.
        return Barrier.RATE_LIMITED
    if "API_KEY_INVALID" in reasons or api_status == "INVALID_ARGUMENT":
        return Barrier.AUTH_REQUIRED
    if status == 401 or api_status == "UNAUTHENTICATED":
        # `captions.download` answers here: it refuses API-key auth outright
        # and demands an OAuth principal.
        return Barrier.AUTH_REQUIRED
    if status == 403:
        lowered = (body or "").lower()
        if ("unregistered callers" in lowered or "without established identity" in lowered
                or api_status == "PERMISSION_DENIED"):
            return Barrier.AUTH_REQUIRED
        return Barrier.FORBIDDEN
    if status == 404:
        return Barrier.NOT_FOUND
    if 500 <= status < 600:
        return Barrier.SERVER_ERROR
    return Barrier.FORBIDDEN if status == 403 else Barrier.UNKNOWN


def _error_reasons(body: str) -> tuple[set[str], set[str], str]:
    """Pull reasons, domains and the canonical status out of an error payload."""
    reasons: set[str] = set()
    domains: set[str] = set()
    try:
        payload = json.loads(body or "{}")
    except (ValueError, TypeError):
        return reasons, domains, ""
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return reasons, domains, ""
    for entry in error.get("errors", []) or []:
        if isinstance(entry, dict):
            if r := entry.get("reason"):
                reasons.add(str(r))
            if d := entry.get("domain"):
                domains.add(str(d))
    for detail in error.get("details", []) or []:
        if isinstance(detail, dict) and (r := detail.get("reason")):
            reasons.add(str(r))
    return reasons, domains, str(error.get("status", ""))


def _redact_key(text: str, key: str) -> str:
    """A key must never reach a log line or a delta's error list."""
    return text.replace(key, "<redacted>") if key else text


def _urlencode(params: dict[str, Any]) -> str:
    from urllib.parse import urlencode

    return urlencode(params)


def _batched(items: list[str], size: int) -> Iterator[list[str]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


# --------------------------------------------------------------------- connector


class YouTubeConnector(Connector):
    """Turn videos, playlists and channels into documents.

    Every document records `transcript_available`, so a downstream reader can
    tell a real transcript from a description that merely reads like one. That
    flag is the whole point: without it, a corpus of descriptions is
    indistinguishable from a corpus of transcripts once it is chunked.
    """

    authority = 0.7  # a video description is weaker evidence than a doc page

    def __init__(
        self,
        *,
        video_ids: list[str] | None = None,
        playlist_ids: list[str] | None = None,
        manifest: str | Path | None = None,
        api_key: str = "",
        transcript_dir: str | Path | None = None,
        client: YouTubeClient | None = None,
        include_timestamps: bool = True,
        key: str = "",
    ) -> None:
        self.video_ids = [v for v in (extract_video_id(x) or "" for x in (video_ids or [])) if v]
        self.playlist_ids = list(playlist_ids or [])
        self.manifest_location = resolve_manifest_location(str(manifest)) if manifest else ""
        self.manifest_path = (
            Path(self.manifest_location)
            if self.manifest_location and not self.manifest_location.startswith("http")
            else None
        )
        self.manifest: dict[str, ManifestEntry] = {}
        self.manifest_errors: list[str] = []
        if self.manifest_location:
            entries, self.manifest_errors = load_manifest(self.manifest_location)
            self.manifest = {e.video_id: e for e in entries}
        self.api = client or YouTubeClient(api_key=api_key)
        # Captions live beside their manifest, whichever side of the network
        # the manifest is on.
        base_url = ""
        if self.manifest_location.startswith("http"):
            base_url = self.manifest_location.rsplit("/", 1)[0]
        elif transcript_dir is None and self.manifest_path:
            transcript_dir = self.manifest_path.parent
        self.transcripts = TranscriptStore(transcript_dir, base_url=base_url)
        self.include_timestamps = include_timestamps
        self.key = key or (
            f"youtube:{self.manifest_location}" if self.manifest_location
            else f"youtube:{','.join(self.video_ids[:3]) or 'playlists'}"
        )

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        for err in self.manifest_errors:
            log.warn("manifest entry skipped", err=err)

        ids = list(self.manifest) + list(self.video_ids)
        for pl in self.playlist_ids:
            ids.extend(self.api.playlist_video_ids(pl))
        seen: set[str] = set()
        ids = [i for i in ids if not (i in seen or seen.add(i))]
        if not ids:
            return

        # The API is used only when it can be: with no key, a manifest still
        # produces a corpus, which is the whole point of committing one.
        items: dict[str, dict[str, Any]] = {}
        if self.api.configured:
            try:
                items = {v["id"]: v for v in self.api.videos(ids) if isinstance(v.get("id"), str)}
            except YouTubeUnavailable as e:
                log.warn("Data API unavailable, falling back to the manifest",
                         barrier=e.barrier.value, detail=e.detail[:160])

        for video_id in ids:
            doc = (
                self._video_document(items[video_id])
                if video_id in items
                else self._manifest_document(video_id)
            )
            if doc is not None:
                yield doc

    def _manifest_document(self, video_id: str) -> RawDocument | None:
        """Build a document from the manifest alone, with no API call.

        Only the fields a human actually recorded are written. Nothing is
        invented to fill a gap, and no prose is attributed to the video unless
        a caption file was genuinely read.
        """
        entry = self.manifest.get(video_id)
        if entry is None:
            return None
        transcript = self.transcripts.get(video_id)

        body = [f"# {entry.title or video_id}"]
        if entry.channel:
            body.append(f"Channel: {entry.channel}")
        if entry.presenter:
            body.append(f"Presenter: {entry.presenter}")
        if entry.topics:
            body.append("Topics: " + ", ".join(entry.topics))
        if entry.related:
            body.append("\nRelated:\n" + "\n".join(f"- {r}" for r in entry.related))
        if transcript is not None:
            body.append("\n## Transcript\n")
            body.append(
                transcript.with_timestamps() if self.include_timestamps else transcript.text
            )

        source = "captions" if transcript is not None else "metadata_only"
        return RawDocument(
            source_system="youtube",
            external_id=video_id,
            uri=f"https://www.youtube.com/watch?v={video_id}",
            title=entry.title or video_id,
            text=redact_secrets("\n".join(body)),
            metadata={
                "kind": "video",
                "channel": entry.channel,
                "presenter": entry.presenter,
                "topics": entry.topics,
                "related": entry.related,
                # How strongly the manifest's own author vouched for the
                # channel attribution. Carried through rather than dropped,
                # because a search-listed attribution is weaker evidence than a
                # confirmed one and a reader should be able to tell.
                "verification": entry.verification,
                "transcript_source": source,
                "transcript_available": transcript is not None,
                "transcript_cues": len(transcript.cues) if transcript else 0,
                "transcript_source_path": transcript.source_path if transcript else "",
                "from_manifest": True,
            },
        )

    def _video_document(self, item: dict[str, Any]) -> RawDocument | None:
        video_id = item.get("id")
        if not isinstance(video_id, str):
            return None
        snippet = item.get("snippet", {})
        title = clean(snippet.get("title", "")) or video_id
        description = clean(snippet.get("description", ""))
        transcript = self.transcripts.get(video_id)

        body = [f"# {title}"]
        if channel := snippet.get("channelTitle"):
            body.append(f"Channel: {clean(channel)}")
        if published := snippet.get("publishedAt"):
            body.append(f"Published: {published}")
        if description:
            body.append("\n## Description\n\n" + description)
        if transcript is not None:
            body.append("\n## Transcript\n")
            body.append(
                transcript.with_timestamps() if self.include_timestamps else transcript.text
            )

        text = redact_secrets("\n".join(body))
        return RawDocument(
            source_system="youtube",
            external_id=video_id,
            uri=f"https://www.youtube.com/watch?v={video_id}",
            title=title,
            text=text,
            metadata={
                "kind": "video",
                "channel": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "published_at": snippet.get("publishedAt", ""),
                "duration": item.get("contentDetails", {}).get("duration", ""),
                "tags": snippet.get("tags", [])[:20],
                "view_count": item.get("statistics", {}).get("viewCount"),
                "transcript_source": "captions" if transcript is not None else "api",
                "transcript_available": transcript is not None,
                "transcript_cues": len(transcript.cues) if transcript else 0,
                "transcript_source_path": transcript.source_path if transcript else "",
                "verification": (
                    self.manifest[video_id].verification
                    if video_id in self.manifest else "api"
                ),
                "from_manifest": video_id in self.manifest,
                "quota_spent": self.api.quota_spent,
            },
        )
