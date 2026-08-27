"""YouTube access has three failure modes that look alike and are not alike.

These tests pin the discriminator: no key, bad key and spent quota arrive with
different HTTP statuses and different JSON, and only one of the three is worth
retrying.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.ingest.youtube import (  # noqa: E402
    QUOTA_COST,
    TranscriptStore,
    YouTubeClient,
    YouTubeUnavailable,
    classify_api_error,
    extract_video_id,
    parse_caption_file,
)
from oodarag.net.reachability import Barrier  # noqa: E402

NO_KEY = ('{"error":{"code":403,"message":"Method doesn\'t allow unregistered callers '
          '(callers without established identity).","errors":[{"reason":"forbidden",'
          '"domain":"global"}],"status":"PERMISSION_DENIED"}}')
BAD_KEY = ('{"error":{"code":400,"message":"API key not valid.","errors":[{"reason":'
           '"badRequest","domain":"global"}],"status":"INVALID_ARGUMENT","details":'
           '[{"reason":"API_KEY_INVALID","domain":"googleapis.com"}]}}')
QUOTA = ('{"error":{"code":403,"errors":[{"domain":"youtube.quota","reason":'
         '"quotaExceeded","message":"exceeded your quota"}]}}')
NO_KEY_AUTH = ('{"error":{"code":401,"message":"API keys are not supported by this API.",'
               '"status":"UNAUTHENTICATED"}}')


class TestErrorDiscrimination(unittest.TestCase):
    def test_missing_key_is_a_credential_problem(self) -> None:
        self.assertIs(classify_api_error(403, NO_KEY), Barrier.AUTH_REQUIRED)

    def test_invalid_key_arrives_as_400_and_must_not_fall_through(self) -> None:
        # The trap: an invalid key is a 400, not a 403. Without the
        # details[].reason check this is classified UNKNOWN and reported as an
        # unexplained failure when the real message is "your key is wrong".
        self.assertIs(classify_api_error(400, BAD_KEY), Barrier.AUTH_REQUIRED)

    def test_spent_quota_is_the_only_retryable_one(self) -> None:
        barrier = classify_api_error(403, QUOTA)
        self.assertIs(barrier, Barrier.RATE_LIMITED)
        self.assertTrue(barrier.retryable)
        self.assertFalse(classify_api_error(403, NO_KEY).retryable)
        self.assertFalse(classify_api_error(400, BAD_KEY).retryable)

    def test_captions_download_rejects_key_auth_outright(self) -> None:
        self.assertIs(classify_api_error(401, NO_KEY_AUTH), Barrier.AUTH_REQUIRED)

    def test_unparseable_body_does_not_raise(self) -> None:
        self.assertIs(classify_api_error(403, "<html>gateway</html>"), Barrier.FORBIDDEN)
        self.assertIs(classify_api_error(404, ""), Barrier.NOT_FOUND)


class TestQuotaTable(unittest.TestCase):
    def test_search_is_two_orders_of_magnitude_dearer_than_a_video_lookup(self) -> None:
        # The reason `search` is opt-in: 100 calls spend the whole daily
        # allowance, while 100 `videos` calls cover 5,000 videos.
        self.assertEqual(QUOTA_COST["videos"], 1)
        self.assertEqual(QUOTA_COST["search"], 100)
        self.assertGreater(QUOTA_COST["captions"], QUOTA_COST["videos"])


class TestNoKeyBehaviour(unittest.TestCase):
    def test_client_without_a_key_names_the_barrier_instead_of_crashing(self) -> None:
        client = YouTubeClient(api_key="")
        client.api_key = ""  # defeat any ambient YOUTUBE_API_KEY
        with self.assertRaises(YouTubeUnavailable) as ctx:
            client.call("videos", part="snippet", id="dQw4w9WgXcQ")
        self.assertIs(ctx.exception.barrier, Barrier.AUTH_REQUIRED)
        self.assertIn("YOUTUBE_API_KEY", str(ctx.exception))

    def test_no_network_call_is_attempted_without_a_key(self) -> None:
        class ExplodingClient:
            def get(self, *a: object, **k: object) -> object:
                raise AssertionError("a request was made without a key")

        client = YouTubeClient(api_key="", client=ExplodingClient())  # type: ignore[arg-type]
        client.api_key = ""
        with self.assertRaises(YouTubeUnavailable):
            client.call("videos", part="snippet")


class TestVideoIdExtraction(unittest.TestCase):
    def test_accepts_the_forms_a_person_actually_pastes(self) -> None:
        for value in [
            "dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/embed/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
        ]:
            self.assertEqual(extract_video_id(value), "dQw4w9WgXcQ", value)

    def test_rejects_something_that_is_not_an_id(self) -> None:
        self.assertIsNone(extract_video_id("https://example.com/"))
        self.assertIsNone(extract_video_id("short"))


VTT = """WEBVTT
Kind: captions
Language: en

00:00:01.000 --> 00:00:04.000
The index goes stale

00:00:04.000 --> 00:00:07.500
The index goes stale
and nobody notices

00:00:07.500 --> 00:00:09.000
<c>until someone profiles it</c>
"""

SRT = """1
00:00:01,000 --> 00:00:04,000
First subrip cue

2
00:00:05,000 --> 00:00:08,000
Second subrip cue
"""


class TestCaptionParsing(unittest.TestCase):
    def _write(self, name: str, body: str) -> Path:
        d = Path(self.tmp.name)
        p = d / name
        p.write_text(body, "utf-8")
        return p

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_webvtt_cues_carry_their_timestamps(self) -> None:
        t = parse_caption_file(self._write("dQw4w9WgXcQ.en.vtt", VTT))
        self.assertEqual(t.video_id, "dQw4w9WgXcQ")
        self.assertEqual(t.cues[0][0], 1.0)
        self.assertIn("[00:00:01]", t.with_timestamps())

    def test_rolling_duplicate_lines_are_collapsed(self) -> None:
        # YouTube repeats each line as the caption scrolls. Left alone this
        # triples the tokens for no additional content.
        t = parse_caption_file(self._write("dQw4w9WgXcQ.en.vtt", VTT))
        texts = [c[1] for c in t.cues]
        self.assertEqual(len(texts), len(set(texts)))

    def test_markup_inside_a_cue_is_stripped(self) -> None:
        t = parse_caption_file(self._write("dQw4w9WgXcQ.en.vtt", VTT))
        self.assertNotIn("<c>", t.text)
        self.assertIn("until someone profiles it", t.text)

    def test_subrip_parses_through_the_same_path(self) -> None:
        t = parse_caption_file(self._write("abcdefghijk.srt", SRT))
        self.assertEqual(len(t.cues), 2)
        self.assertEqual(t.cues[1][0], 5.0)

    def test_store_reports_absence_rather_than_inventing_a_transcript(self) -> None:
        store = TranscriptStore(self.tmp.name)
        self.assertIsNone(store.get("dQw4w9WgXcQ"))
        self.assertFalse(store.available)

    def test_store_indexes_by_video_id(self) -> None:
        self._write("dQw4w9WgXcQ.en.vtt", VTT)
        store = TranscriptStore(self.tmp.name)
        self.assertTrue(store.available)
        self.assertIsNotNone(store.get("dQw4w9WgXcQ"))

    def test_missing_directory_is_not_an_error(self) -> None:
        # An operator who has not exported anything yet should get an empty
        # store, not a crash on a path that does not exist.
        self.assertFalse(TranscriptStore("/nonexistent/path").available)
        self.assertFalse(TranscriptStore(None).available)


if __name__ == "__main__":
    unittest.main(verbosity=2)
