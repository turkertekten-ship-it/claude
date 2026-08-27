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

The connector therefore degrades in three named steps — metadata + transcript,
metadata only, nothing-with-a-reason — and never fabricates the level above the
one it actually reached.
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
    """Parse WebVTT or SubRip into timed cues.

    Both formats are handled by the same pass because they differ only in the
    header and the cue-number line, and a parser that accepts both means an
    operator does not have to care which one their export tool produced.
    Consecutive duplicate lines are collapsed: YouTube's rolling captions
    repeat each line as it scrolls, which would otherwise triple the tokens.
    """
    video_id = path.stem.split(".")[0]
    raw = path.read_text("utf-8", errors="replace")
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
    return Transcript(video_id=video_id, cues=cues, source_path=str(path))


class TranscriptStore:
    """Caption files on disk, keyed by video id.

    This is the egress-free half of the connector. An owner who can reach
    YouTube from their own machine exports captions once and drops them here;
    the pipeline then indexes real transcripts without ever needing the site.
    """

    SUFFIXES = (".vtt", ".srt")

    def __init__(self, directory: str | Path | None) -> None:
        self.directory = Path(directory) if directory else None
        self._index: dict[str, Path] = {}
        if self.directory and self.directory.is_dir():
            for p in sorted(self.directory.iterdir()):
                if p.suffix.lower() in self.SUFFIXES:
                    vid = extract_video_id(p.stem.split(".")[0]) or p.stem.split(".")[0]
                    self._index.setdefault(vid, p)

    def __len__(self) -> int:
        return len(self._index)

    @property
    def available(self) -> bool:
        return bool(self._index)

    def get(self, video_id: str) -> Transcript | None:
        path = self._index.get(video_id)
        if path is None:
            return None
        try:
            return parse_caption_file(path)
        except OSError as e:
            log.warn("caption file unreadable", path=str(path), err=str(e))
            return None


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
        api_key: str = "",
        transcript_dir: str | Path | None = None,
        client: YouTubeClient | None = None,
        include_timestamps: bool = True,
        key: str = "",
    ) -> None:
        self.video_ids = [v for v in (extract_video_id(x) or "" for x in (video_ids or [])) if v]
        self.playlist_ids = list(playlist_ids or [])
        self.api = client or YouTubeClient(api_key=api_key)
        self.transcripts = TranscriptStore(transcript_dir)
        self.include_timestamps = include_timestamps
        self.key = key or f"youtube:{','.join(self.video_ids[:3]) or 'playlists'}"

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        ids = list(self.video_ids)
        for pl in self.playlist_ids:
            ids.extend(self.api.playlist_video_ids(pl))
        seen: set[str] = set()
        ids = [i for i in ids if not (i in seen or seen.add(i))]
        if not ids:
            return

        for item in self.api.videos(ids):
            doc = self._video_document(item)
            if doc is not None:
                yield doc

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
                "transcript_available": transcript is not None,
                "transcript_cues": len(transcript.cues) if transcript else 0,
                "transcript_source": transcript.source_path if transcript else "",
                "quota_spent": self.api.quota_spent,
            },
        )
