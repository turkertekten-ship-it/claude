"""YouTube connector: video metadata and transcripts.

Video explainers are a genuinely useful RAG source - a good one states a concept
more plainly than the documentation does - and a genuinely awkward one, because
the text is captions: no punctuation you can trust, no paragraphs, and meaning
spread across cues. Two things make it work:

* **Timestamps travel with the chunk.** A citation into a video is only useful
  if it becomes a `?t=` deep link, so the chunker keeps the first timestamp of
  each window (see chunking._split_transcript).
* **Cues are re-joined before chunking.** Caption cues break mid-sentence by
  design; chunking on cue boundaries produces fragments that end mid-clause.

**On egress.** YouTube is blocked from many managed environments - it is blocked
from the one this was written in (`internal/ACCESS.md`). So the connector has
two paths, and neither is a stub:

1. **Live** - resolve metadata via oEmbed and captions via the timedtext
   endpoint, for environments that can reach youtube.com.
2. **Manifest** - read a committed manifest of videos with locally stored
   caption files or curated notes. This is the offline hand-off from
   `internal/CAPABILITY-PROTOCOL.md` rule 5: research happens on whatever path
   can reach the source, its result is committed, and ingestion consumes the
   committed artifact.

Provenance is explicit either way. Every document records `transcript_source` as
one of `captions` (the real thing) or `curated_note` (a human- or
model-authored summary). They are never presented as equivalent, because a
summary attributed to a video as if it were a quote is a fabricated citation.
"""

from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from oodarag.ingest.base import Connector
from oodarag.models import RawDocument
from oodarag.util.http import HttpClient, HttpError, TransportError
from oodarag.util.logging import get_logger
from oodarag.util.text import clean

log = get_logger("ingest.youtube")

OEMBED = "https://www.youtube.com/oembed"
TIMEDTEXT = "https://www.youtube.com/api/timedtext"
WATCH = "https://www.youtube.com/watch"

_VIDEO_ID_RE = re.compile(r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})")
_TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[.,](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[.,](\d{3})")


def video_id(url_or_id: str) -> str | None:
    """Accept a URL or a bare id."""
    candidate = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        return candidate
    match = _VIDEO_ID_RE.search(candidate)
    return match.group(1) if match else None


def watch_url(vid: str) -> str:
    return f"{WATCH}?v={vid}"


def parse_vtt(text: str) -> list[tuple[str, str]]:
    """Parse WebVTT or SRT into (timestamp, text) cues.

    Written to handle both because caption exports arrive as either, and the
    only structural difference that matters here is the millisecond separator.
    """
    cues: list[tuple[str, str]] = []
    current_stamp: str | None = None
    buffer: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if current_stamp and buffer:
                cues.append((current_stamp, " ".join(buffer)))
            current_stamp, buffer = None, []
            continue
        if match := _TIMESTAMP_RE.search(line):
            if current_stamp and buffer:
                cues.append((current_stamp, " ".join(buffer)))
                buffer = []
            hours, minutes, seconds = match.group(1), match.group(2), match.group(3)
            current_stamp = (f"{int(hours)}:{minutes}:{seconds}" if int(hours)
                             else f"{minutes}:{seconds}")
            continue
        if line.upper().startswith(("WEBVTT", "NOTE ", "KIND:", "LANGUAGE:")) or line.isdigit():
            continue
        # Caption files carry inline styling tags that are noise in a corpus.
        buffer.append(clean(re.sub(r"<[^>]+>", "", line)))

    if current_stamp and buffer:
        cues.append((current_stamp, " ".join(buffer)))
    return cues


def cues_to_transcript(cues: list[tuple[str, str]], window_seconds: int = 30) -> str:
    """Join cues into timestamped paragraphs.

    Caption cues break every few seconds, mid-clause. Emitting one line per cue
    produces chunks that start and end mid-sentence; grouping into windows gives
    the chunker whole thoughts to split on, while keeping one timestamp per
    window for deep linking.
    """
    if not cues:
        return ""
    lines: list[str] = []
    window_start = _seconds(cues[0][0])
    buffer: list[str] = []
    stamp = cues[0][0]

    for timestamp, text in cues:
        position = _seconds(timestamp)
        if position - window_start >= window_seconds and buffer:
            lines.append(f"[{stamp}] {' '.join(buffer)}")
            buffer, window_start, stamp = [], position, timestamp
        # Auto-generated captions repeat the tail of the previous cue as the
        # head of the next; dropping the duplicate keeps the text readable.
        if buffer and text and buffer[-1].endswith(text):
            continue
        buffer.append(text)
    if buffer:
        lines.append(f"[{stamp}] {' '.join(buffer)}")
    return "\n".join(lines)


def _seconds(timestamp: str) -> int:
    parts = [int(p) for p in timestamp.split(":")]
    total = 0
    for part in parts:
        total = total * 60 + part
    return total


class YouTubeConnector(Connector):
    """Ingest videos listed in a manifest, live or from committed captions.

    The manifest is a JSON list of entries:

        {
          "video_id": "T-D1OfcDW1M",
          "title": "What is Retrieval-Augmented Generation (RAG)?",
          "channel": "IBM Technology",
          "captions_file": "corpus/ibm/rag.vtt",   # optional
          "notes_file": "corpus/ibm/rag.md",       # optional fallback
          "verification": "search_confirmed"
        }
    """

    def __init__(self, manifest: str | Path | None = None,
                 videos: list[str] | None = None, *,
                 client: HttpClient | None = None,
                 allow_network: bool = True,
                 languages: tuple[str, ...] = ("en",),
                 authority: float = 0.85,
                 key: str | None = None) -> None:
        self.manifest_path = Path(manifest) if manifest else None
        self.videos = videos or []
        self.client = client or HttpClient(rate_per_sec=2.0)
        self.allow_network = allow_network
        self.languages = languages
        self.authority = authority
        self.key = key or f"youtube:{self.manifest_path or ','.join(self.videos[:2]) or 'empty'}"
        self.stats: dict[str, Any] = {}

    # ---------------------------------------------------------------- manifest

    def _entries(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        if self.manifest_path and self.manifest_path.exists():
            data = json.loads(self.manifest_path.read_text("utf-8"))
            entries.extend(data.get("videos", data) if isinstance(data, dict) else data)
        for item in self.videos:
            if vid := video_id(item):
                entries.append({"video_id": vid})
        return entries

    def fetch(self, cursor: dict[str, Any]) -> Iterator[RawDocument]:
        counts = {"captions": 0, "curated_note": 0, "metadata_only": 0, "failed": 0}
        base = self.manifest_path.parent if self.manifest_path else Path(".")

        for entry in self._entries():
            vid = entry.get("video_id") or video_id(entry.get("url", ""))
            if not vid:
                counts["failed"] += 1
                continue
            metadata = dict(entry)
            if self.allow_network:
                metadata.update(self._live_metadata(vid))

            text, source = self._transcript(vid, entry, base)
            if not text:
                # Metadata alone is still worth indexing: a title and channel
                # let a query find the video even with no transcript, and the
                # document says plainly that the transcript is missing.
                text = (f"# {metadata.get('title', vid)}\n\n"
                        f"Channel: {metadata.get('channel', 'unknown')}\n\n"
                        f"No transcript available in this environment. "
                        f"{metadata.get('summary', '')}").strip()
                source = "metadata_only"
            counts[source] = counts.get(source, 0) + 1

            yield RawDocument(
                source_system="youtube",
                external_id=f"video:{vid}",
                uri=watch_url(vid),
                title=metadata.get("title") or f"YouTube video {vid}",
                text=text,
                metadata={
                    "kind": "transcript",
                    "video_id": vid,
                    "channel": metadata.get("channel", ""),
                    "published": metadata.get("published", ""),
                    # The single most important field on this source: whether
                    # the text is what was said, or what someone wrote about it.
                    "transcript_source": source,
                    "verification": metadata.get("verification", "unverified"),
                    "authority": self.authority if source == "captions"
                    else self.authority * 0.8,
                    "topics": metadata.get("topics", []),
                },
            )
        self.stats = counts
        log.info("youtube fetch complete", **counts)

    # -------------------------------------------------------------- transcript

    def _transcript(self, vid: str, entry: dict[str, Any], base: Path) -> tuple[str, str]:
        if captions_file := entry.get("captions_file"):
            path = self._resolve(captions_file, base)
            if path.exists():
                cues = parse_vtt(path.read_text("utf-8", errors="replace"))
                if cues:
                    return cues_to_transcript(cues), "captions"

        if self.allow_network:
            if live := self._live_captions(vid):
                return live, "captions"

        if notes_file := entry.get("notes_file"):
            path = self._resolve(notes_file, base)
            if path.exists():
                body = path.read_text("utf-8", errors="replace")
                # Marked in the body as well as the metadata: whoever reads a
                # retrieved passage must be able to tell a summary from a quote
                # without inspecting its metadata.
                return (f"[Curated note - not a verbatim transcript]\n\n{body}",
                        "curated_note")

        if summary := entry.get("summary"):
            return f"[Curated note - not a verbatim transcript]\n\n{summary}", "curated_note"
        return "", "metadata_only"

    @staticmethod
    def _resolve(candidate: str, base: Path) -> Path:
        path = Path(candidate)
        return path if path.is_absolute() or path.exists() else base / candidate

    def _live_metadata(self, vid: str) -> dict[str, Any]:
        params = urllib.parse.urlencode({"url": watch_url(vid), "format": "json"})
        try:
            payload = self.client.get_json(f"{OEMBED}?{params}")
        except (HttpError, TransportError) as e:
            log.debug("oembed unavailable", video=vid, err=str(e)[:120])
            return {}
        return {"title": payload.get("title"), "channel": payload.get("author_name")}

    def _live_captions(self, vid: str) -> str:
        for language in self.languages:
            params = urllib.parse.urlencode({"v": vid, "lang": language, "fmt": "json3"})
            try:
                response = self.client.get(f"{TIMEDTEXT}?{params}", allow_status=(404, 403))
            except (HttpError, TransportError) as e:
                log.debug("timedtext unreachable", video=vid, err=str(e)[:120])
                return ""
            if response.status != 200 or not response.body.strip():
                continue
            try:
                payload = response.json()
            except (ValueError, json.JSONDecodeError):
                continue
            cues: list[tuple[str, str]] = []
            for event in payload.get("events", []):
                segments = event.get("segs") or []
                text = clean("".join(seg.get("utf8", "") for seg in segments))
                if not text:
                    continue
                start_ms = int(event.get("tStartMs", 0))
                minutes, seconds = divmod(start_ms // 1000, 60)
                hours, minutes = divmod(minutes, 60)
                stamp = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"
                cues.append((stamp, text))
            if cues:
                return cues_to_transcript(cues)
        return ""

    def next_cursor(self, cursor: dict[str, Any]) -> dict[str, Any]:
        cursor["stats"] = self.stats
        return cursor
