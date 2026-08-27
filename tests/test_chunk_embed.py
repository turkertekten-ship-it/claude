"""Chunking must preserve context; embeddings must be reproducible across runs."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.chunk import (  # noqa: E402
    KIND_POLICIES,
    ChunkConfig,
    chunk_document,
    policy_for,
)
from oodarag.embed import HashingEmbedder, cosine, pack, unpack  # noqa: E402
from oodarag.models import Document, RawDocument  # noqa: E402

MARKDOWN = """# Budgets

Every network stage has a budget.

## Pages

The crawler stops after the page budget is spent.

## Bytes

A response larger than the cap is refused before it is read into memory.
"""


def make_doc(text: str, title: str = "Design notes") -> Document:
    raw = RawDocument("file", "design.md", "file:///design.md", title, text)
    return Document.from_raw(raw, text, {})


class TestChunking(unittest.TestCase):
    def test_no_content_is_lost_across_section_boundaries(self) -> None:
        joined = " ".join(c.text for c in chunk_document(make_doc(MARKDOWN)))
        self.assertIn("page budget", joined)
        self.assertIn("larger than the cap", joined)

    def test_headings_become_boundaries_when_sections_are_large_enough(self) -> None:
        big = "\n".join(
            f"# Section {i}\n\n" + " ".join(
                f"Sentence {j} of section {i} with enough words to clear the runt floor."
                for j in range(12)
            )
            for i in range(3)
        )
        chunks = chunk_document(make_doc(big))
        self.assertGreaterEqual(len(chunks), 3)

    def test_a_merged_chunk_never_claims_a_heading_only_part_of_it_belongs_to(self) -> None:
        # The trap this guards: folding a runt from "Bytes" into a chunk from
        # "Pages" would label the whole thing "Pages", asserting a section over
        # text that is not in it.
        for chunk in chunk_document(make_doc(MARKDOWN)):
            for heading in chunk.metadata["headings"]:
                sections = [h for h in ("Pages", "Bytes") if h in chunk.text]
                if heading in ("Pages", "Bytes"):
                    self.assertEqual(
                        sections, [heading],
                        f"chunk headed {heading!r} also contains other sections",
                    )

    def test_every_chunk_carries_its_document_title(self) -> None:
        # This is what stops a retrieved passage being uninterpretable.
        for chunk in chunk_document(make_doc(MARKDOWN)):
            self.assertIn("Design notes", chunk.context_header)

    def test_the_heading_path_reaches_the_indexed_text(self) -> None:
        chunks = chunk_document(make_doc(MARKDOWN))
        byte_chunk = next(c for c in chunks if "cap" in c.text)
        self.assertIn("Bytes", byte_chunk.indexed_text)

    def test_ordinals_are_contiguous_from_zero(self) -> None:
        chunks = chunk_document(make_doc(MARKDOWN))
        self.assertEqual([c.ordinal for c in chunks], list(range(len(chunks))))

    def test_an_empty_document_produces_no_chunks(self) -> None:
        self.assertEqual(chunk_document(make_doc("   \n\n  ")), [])

    def test_a_document_with_no_headings_still_chunks(self) -> None:
        chunks = chunk_document(make_doc("Just one paragraph of prose, no headings at all."))
        self.assertEqual(len(chunks), 1)

    def test_a_long_section_is_split_with_overlap(self) -> None:
        body = "# Long\n\n" + " ".join(
            f"Sentence number {i} carries some distinct content about retrieval."
            for i in range(120)
        )
        cfg = ChunkConfig(target_tokens=60, max_tokens=90, overlap_sentences=1)
        chunks = chunk_document(make_doc(body), cfg)
        self.assertGreater(len(chunks), 3)
        # Overlap means consecutive chunks share a sentence, so a claim split
        # across a boundary is retrievable from either side.
        self.assertTrue(
            any(chunks[i].text.split(".")[-2:] and
                chunks[i].text[-40:].strip()[:20] in chunks[i + 1].text
                for i in range(len(chunks) - 1))
        )

    def test_chunk_ids_are_stable_for_identical_input(self) -> None:
        a = [c.chunk_id for c in chunk_document(make_doc(MARKDOWN))]
        b = [c.chunk_id for c in chunk_document(make_doc(MARKDOWN))]
        self.assertEqual(a, b)

    def test_tiny_trailing_fragments_are_folded_in(self) -> None:
        # A two-word chunk scores well on a two-word query and displaces the
        # passage that actually answers it.
        doc = make_doc("# A\n\nx\n\n# B\n\nThis section has real content worth retrieving.")
        for chunk in chunk_document(doc):
            self.assertGreater(len(chunk.text.strip()), 1)


def kinded_doc(text: str, kind: str, source: str = "github", title: str = "T") -> Document:
    raw = RawDocument(source, "x", "https://e.com/x", title, text, {"kind": kind})
    return Document.from_raw(raw, text, {"kind": kind})


class TestPerKindChunking(unittest.TestCase):
    COMMIT = ("Fix the retry loop so a 429 honours Retry-After\n\n"
              "The previous code backed off exponentially and ignored the header, "
              "which meant a rate-limited client waited either far too long or "
              "not long enough.")

    def test_a_commit_message_is_never_split(self) -> None:
        # One commit is one unit of meaning. Splitting it in half leaves two
        # halves that each describe nothing.
        chunks = chunk_document(kinded_doc(self.COMMIT, "commit"))
        self.assertEqual(len(chunks), 1)

    def test_two_short_commits_are_not_packed_together(self) -> None:
        # Merging would bury the shorter one behind the longer one's terms.
        a = chunk_document(kinded_doc("Bump the lockfile", "commit"))
        b = chunk_document(kinded_doc("Fix a typo in the README", "commit"))
        self.assertEqual(len(a), 1)
        self.assertEqual(len(b), 1)
        self.assertNotEqual(a[0].chunk_id, b[0].chunk_id)

    def test_an_unsplit_chunk_still_carries_a_context_header(self) -> None:
        # A whole-document chunk still has to say what document it is.
        chunk = chunk_document(kinded_doc(self.COMMIT, "commit", title="Repo"))[0]
        self.assertIn("Repo", chunk.context_header)

    def test_an_oversized_atomic_document_is_split_not_truncated(self) -> None:
        # Losing the tail of a long issue comment is worse than splitting it.
        long_comment = " ".join(
            f"Sentence {i} of a very long issue comment that runs well past the cap."
            for i in range(300)
        )
        chunks = chunk_document(kinded_doc(long_comment, "issue"))
        self.assertGreater(len(chunks), 1)
        rejoined = " ".join(c.text for c in chunks)
        self.assertIn("Sentence 299", rejoined)

    def test_atomic_kinds_take_no_overlap(self) -> None:
        for kind in ("commit", "issue", "pull_request", "release"):
            self.assertEqual(KIND_POLICIES[kind].overlap_sentences, 0, kind)
            self.assertTrue(KIND_POLICIES[kind].atomic, kind)

    def test_prose_kinds_keep_overlap(self) -> None:
        for kind in ("readme", "web", "skill"):
            self.assertGreater(KIND_POLICIES[kind].overlap_sentences, 0, kind)

    def test_markdown_still_splits_on_headings(self) -> None:
        # Sections must clear the runt floor, or folding them into one chunk is
        # the correct answer and the test is measuring nothing.
        big = "\n".join(
            f"# Section {i}\n\n" + " ".join(
                f"Sentence {j} of section {i}, long enough to stand on its own."
                for j in range(14)
            )
            for i in range(3)
        )
        chunks = chunk_document(kinded_doc(big, "readme", source="file"))
        self.assertGreater(len(chunks), 1)

    def test_policy_falls_back_to_the_source_system(self) -> None:
        raw = RawDocument("youtube", "v", "https://e.com/v", "V", "text", {})
        doc = Document.from_raw(raw, "text", {})
        self.assertEqual(policy_for(doc).label, "transcript")

    def test_an_unknown_kind_gets_the_default(self) -> None:
        raw = RawDocument("mystery", "x", "https://e.com/x", "X", "text", {})
        doc = Document.from_raw(raw, "text", {})
        self.assertEqual(policy_for(doc).label, "default")

    def test_per_kind_can_be_switched_off_for_an_ab_run(self) -> None:
        forced = ChunkConfig(target_tokens=20, max_tokens=30, per_kind=False)
        long_commit = " ".join(f"Sentence {i} of the commit body." for i in range(60))
        chunks = chunk_document(kinded_doc(long_commit, "commit"), forced)
        self.assertGreater(len(chunks), 1, "per_kind=False should force the caller's sizing")


PY_SOURCE = '''"""Module docstring."""

import os


class Widget:
    """A class with several members."""

    LIMIT = 10

    @property
    def size(self) -> int:
        """Return the size."""
        total = 0
        for item in range(self.LIMIT):
            total += item
        return total

    def render(self) -> str:
        """Render the widget."""
        parts = []
        for i in range(self.LIMIT):
            parts.append(str(i))
        return ",".join(parts)


def helper(value: int) -> int:
    """A top-level helper."""
    return value * 2
'''


class TestCodeAwareChunking(unittest.TestCase):
    def chunks(self, source: str = PY_SOURCE, **cfg: object) -> list:
        doc = kinded_doc(source, "file")
        return chunk_document(doc, ChunkConfig(**cfg) if cfg else None)  # type: ignore[arg-type]

    def test_no_chunk_begins_inside_a_statement_block(self) -> None:
        # The cut this strategy exists to prevent: a chunk starting at `return`
        # has behaviour with no signature, and the one before it a signature
        # with no behaviour.
        for chunk in self.chunks(target_tokens=30, max_tokens=60):
            first = chunk.text.splitlines()[0]
            self.assertFalse(
                re.match(r"^\s{4,}(return|for |if |while |total\b|parts\b)", first),
                f"chunk starts mid-statement: {first!r}",
            )

    def test_a_decorator_stays_with_the_member_it_decorates(self) -> None:
        # A chunk that is only `@property` describes nothing.
        for chunk in self.chunks(target_tokens=25, max_tokens=50):
            self.assertNotEqual(chunk.text.strip(), "@property")
            if chunk.text.lstrip().startswith("@property"):
                self.assertIn("def ", chunk.text)

    def test_the_module_preamble_is_its_own_unit(self) -> None:
        chunks = self.chunks(target_tokens=25, max_tokens=50)
        self.assertIn("Module docstring", chunks[0].text)

    def test_a_small_file_is_not_split_at_all(self) -> None:
        self.assertEqual(len(self.chunks("def f():\n    return 1\n")), 1)

    def test_a_file_with_no_definitions_falls_back_to_prose(self) -> None:
        config_text = "\n".join(f"setting_{i} = {i}" for i in range(200))
        self.assertGreaterEqual(len(self.chunks(config_text)), 1)

    def test_definitions_are_grouped_rather_than_one_chunk_each(self) -> None:
        # Twenty one-line helpers as twenty chunks is noise.
        tiny = "\n\n".join(f"def f{i}():\n    return {i}" for i in range(20))
        self.assertLess(len(self.chunks(tiny)), 20)


class TestEmbedding(unittest.TestCase):
    def setUp(self) -> None:
        self.embedder = HashingEmbedder()

    def test_vectors_are_unit_length(self) -> None:
        vec = self.embedder.embed("hybrid retrieval fuses lexical and dense arms")
        self.assertAlmostEqual(sum(v * v for v in vec) ** 0.5, 1.0, places=6)

    def test_related_text_scores_above_unrelated_text(self) -> None:
        a = self.embedder.embed("hybrid retrieval fuses BM25 with dense vectors")
        b = self.embedder.embed("dense vector retrieval combined with BM25 lexical search")
        c = self.embedder.embed("a recipe for sourdough bread with rye flour")
        self.assertGreater(cosine(a, b), cosine(a, c))

    def test_empty_text_gives_a_zero_vector_rather_than_raising(self) -> None:
        self.assertEqual(set(self.embedder.embed("   ")), {0.0})

    def test_dimension_is_a_power_of_two(self) -> None:
        # Bucketing is a modulo, so a non-power-of-two spreads tokens unevenly.
        dim = self.embedder.dim
        self.assertEqual(dim & (dim - 1), 0)

    def test_serialization_round_trips(self) -> None:
        vec = self.embedder.embed("round trip through float32 storage")
        restored = unpack(pack(vec))
        self.assertEqual(len(restored), len(vec))
        for original, back in zip(vec, restored, strict=True):
            self.assertAlmostEqual(original, back, places=6)

    def test_embeddings_are_identical_in_a_separate_process(self) -> None:
        # The reason `hash()` is never used: string hashing is salted per
        # process, so an index built in one run would not match a query vector
        # computed in the next.
        script = (
            "import sys; sys.path.insert(0, 'src');"
            "from oodarag.embed import HashingEmbedder;"
            "print(sum(HashingEmbedder().embed('stable across processes')))"
        )
        root = Path(__file__).resolve().parent.parent
        runs = {
            subprocess.run([sys.executable, "-c", script], capture_output=True,
                           text=True, cwd=root, check=True).stdout.strip()
            for _ in range(2)
        }
        self.assertEqual(len(runs), 1, f"embedding differed across processes: {runs}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
