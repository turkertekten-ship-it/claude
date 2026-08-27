"""Chunking must preserve context; embeddings must be reproducible across runs."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oodarag.chunk import ChunkConfig, chunk_document  # noqa: E402
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
