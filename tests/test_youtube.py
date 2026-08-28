"""YouTube access has three failure modes that look alike and are not alike.

These tests pin the discriminator: no key, bad key and spent quota arrive with
different HTTP statuses and different JSON, and only one of the three is worth
retrying.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.ingest.youtube import (  # noqa: E402
    QUOTA_COST,
    ManifestEntry,
    TranscriptStore,
    YouTubeClient,
    YouTubeConnector,
    YouTubeUnavailable,
    classify_api_error,
    extract_video_id,
    load_manifest,
    parse_caption_file,
    resolve_manifest_location,
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


MANIFEST = """{
  "_about": "documentation for a human reader, ignored by the loader",
  "videos": [
    {"video_id": "T-D1OfcDW1M", "title": "What is RAG?", "channel": "IBM Technology",
     "presenter": "Marina Danilevsky", "verification": "search_confirmed",
     "topics": ["rag", "grounding"],
     "related": ["https://www.ibm.com/think/videos/rag"]},
    {"video_id": "https://www.youtube.com/watch?v=LpKGm1jJXv4", "title": "Setting up RAG",
     "channel": "IBM Technology", "verification": "search_listed"},
    {"video_id": "not-an-id", "title": "malformed"},
    {"title": "no id at all"}
  ]
}"""


class TestManifest(unittest.TestCase):
    """A manifest is how a video corpus survives an environment with no egress."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.path = self.dir / "manifest.json"
        self.path.write_text(MANIFEST, "utf-8")
        # Defeat any ambient key so the offline path is what is exercised.
        self._saved = os.environ.pop("YOUTUBE_API_KEY", None)
        if self._saved is not None:
            self.addCleanup(lambda: os.environ.__setitem__("YOUTUBE_API_KEY", self._saved))

    def test_valid_entries_load_and_malformed_ones_are_reported(self) -> None:
        # A corpus that quietly shrank is worse than one that failed loudly:
        # every downstream number improves either way.
        entries, errors = load_manifest(self.path)
        self.assertEqual(len(entries), 2)
        self.assertEqual(len(errors), 2)

    def test_a_watch_url_is_accepted_as_an_id(self) -> None:
        entries, _ = load_manifest(self.path)
        self.assertIn("LpKGm1jJXv4", [e.video_id for e in entries])

    def test_underscore_keys_are_documentation_not_data(self) -> None:
        entries, errors = load_manifest(self.path)
        self.assertEqual(len(entries), 2)
        self.assertFalse(any("_about" in e for e in errors))

    def test_a_missing_manifest_is_an_error_not_an_empty_success(self) -> None:
        entries, errors = load_manifest(self.dir / "absent.json")
        self.assertEqual(entries, [])
        self.assertTrue(errors)

    def test_malformed_json_is_reported(self) -> None:
        bad = self.dir / "bad.json"
        bad.write_text("{not json", "utf-8")
        entries, errors = load_manifest(bad)
        self.assertEqual(entries, [])
        self.assertTrue(errors)

    def test_the_connector_produces_documents_with_no_key_and_no_network(self) -> None:
        class ExplodingClient:
            def get(self, *a: object, **k: object) -> object:
                raise AssertionError("a request was made on the manifest path")

        connector = YouTubeConnector(
            manifest=self.path,
            client=YouTubeClient(api_key="", client=ExplodingClient()),  # type: ignore[arg-type]
        )
        connector.api.api_key = ""
        docs = list(connector.fetch({}))
        self.assertEqual(len(docs), 2)

    def test_a_video_with_no_captions_is_labelled_metadata_only(self) -> None:
        # The distinction that stops a description being cited as speech.
        connector = YouTubeConnector(manifest=self.path)
        connector.api.api_key = ""
        docs = list(connector.fetch({}))
        for doc in docs:
            self.assertEqual(doc.metadata["transcript_source"], "metadata_only")
            self.assertFalse(doc.metadata["transcript_available"])

    def test_a_caption_file_beside_the_manifest_upgrades_the_source(self) -> None:
        (self.dir / "T-D1OfcDW1M.en.vtt").write_text(VTT, "utf-8")
        connector = YouTubeConnector(manifest=self.path)
        connector.api.api_key = ""
        docs = {d.external_id: d for d in connector.fetch({})}
        self.assertEqual(docs["T-D1OfcDW1M"].metadata["transcript_source"], "captions")
        self.assertEqual(docs["LpKGm1jJXv4"].metadata["transcript_source"], "metadata_only")

    def test_the_verification_grade_is_carried_through(self) -> None:
        # search_listed is weaker evidence than search_confirmed, and a reader
        # should be able to tell which they are looking at.
        connector = YouTubeConnector(manifest=self.path)
        connector.api.api_key = ""
        grades = {d.external_id: d.metadata["verification"] for d in connector.fetch({})}
        self.assertEqual(grades["T-D1OfcDW1M"], "search_confirmed")
        self.assertEqual(grades["LpKGm1jJXv4"], "search_listed")

    def test_no_prose_is_attributed_to_a_video_without_captions(self) -> None:
        # The failure this guards: a summary stored next to a video reads
        # exactly like a transcript once chunked, and a citation pointing at it
        # would look verbatim while being someone's paraphrase.
        connector = YouTubeConnector(manifest=self.path)
        connector.api.api_key = ""
        for doc in connector.fetch({}):
            self.assertNotIn("## Transcript", doc.text)

    def test_manifest_entry_rejects_an_unusable_id(self) -> None:
        self.assertIsNone(ManifestEntry.from_dict({"video_id": "nope"}))
        self.assertIsNone(ManifestEntry.from_dict({}))


class TestRepositoryHostedManifest(unittest.TestCase):
    """A corpus in a git repository is reachable where youtube.com is not.

    This is the whole point of the remote path: `raw.githubusercontent.com`
    answers for any public repository and is on this container's allowlist,
    while `www.youtube.com` is refused at CONNECT. None of these tests touch
    the network — they cover the resolution and the failure reporting.
    """

    def test_a_bare_owner_repo_resolves_to_raw_github(self) -> None:
        self.assertEqual(
            resolve_manifest_location("someowner/somerepo"),
            "https://raw.githubusercontent.com/someowner/somerepo/main/corpus/manifest.json",
        )

    def test_a_ref_can_be_pinned(self) -> None:
        self.assertIn("/v2.1/", resolve_manifest_location("someowner/somerepo@v2.1"))

    def test_a_path_inside_the_repository_can_be_named(self) -> None:
        self.assertTrue(
            resolve_manifest_location("o/r@main:data/videos.json").endswith(
                "/o/r/main/data/videos.json"
            )
        )

    def test_a_url_passes_through_unchanged(self) -> None:
        url = "https://example.invalid/manifest.json"
        self.assertEqual(resolve_manifest_location(url), url)

    def test_an_existing_local_path_is_preferred_over_repo_expansion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "manifest.json"
            p.write_text('{"videos": []}', "utf-8")
            self.assertEqual(resolve_manifest_location(str(p)), str(p))

    def test_an_unreachable_manifest_names_its_barrier(self) -> None:
        # A repository that is private and one that does not exist read
        # identically; only one is fixable by the operator, so the report has
        # to carry the barrier and its remedy rather than a stack trace.
        class Refusing:
            def get(self, url: str, **kw: object) -> object:
                from oodarag.util.http import TransportError
                raise TransportError("Tunnel connection failed: 403 Forbidden")

        entries, errors = load_manifest("someowner/somerepo", client=Refusing())  # type: ignore[arg-type]
        self.assertEqual(entries, [])
        self.assertEqual(len(errors), 1)
        self.assertIn("egress_blocked", errors[0])
        self.assertIn("allowlist", errors[0])

    def test_a_404_is_reported_as_a_path_problem_not_a_block(self) -> None:
        class NotFound:
            def get(self, url: str, **kw: object) -> object:
                from oodarag.util.http import HttpError
                raise HttpError(404, url, "404: Not Found")

        _entries, errors = load_manifest("someowner/somerepo", client=NotFound())  # type: ignore[arg-type]
        self.assertIn("not_found", errors[0])

    def test_the_committed_manifest_loads_and_grades_every_entry(self) -> None:
        # The corpus actually committed to this repository.
        repo_manifest = Path(__file__).resolve().parent.parent / "corpus/ibm-technology/manifest.json"
        if not repo_manifest.exists():
            self.skipTest("no committed manifest in this checkout")
        entries, errors = load_manifest(repo_manifest)
        self.assertEqual(errors, [])
        self.assertTrue(entries)
        for entry in entries:
            self.assertIn(entry.verification, ("search_confirmed", "search_listed"))
            self.assertTrue(entry.title)

    def test_the_committed_manifest_claims_no_transcripts_it_does_not_have(self) -> None:
        repo_manifest = Path(__file__).resolve().parent.parent / "corpus/ibm-technology/manifest.json"
        if not repo_manifest.exists():
            self.skipTest("no committed manifest in this checkout")
        connector = YouTubeConnector(manifest=repo_manifest)
        connector.api.api_key = ""
        for doc in connector.fetch({}):
            self.assertEqual(doc.metadata["transcript_source"], "metadata_only")
            self.assertNotIn("## Transcript", doc.text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
