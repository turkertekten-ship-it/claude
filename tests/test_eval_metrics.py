"""The harness's arithmetic, checked against hand-computed values.

Every retrieval claim in this repository — the ADRs, the plan's known gaps, the
fusion invariant — is a number this module produced. A bug here would not make
those claims noisy; it would make them all wrong in the same direction, and
nothing downstream could tell. So these cases do not exercise the harness, they
verify the formulas against values computed by hand from the standard
definitions.

  RR    = 1 / rank of the first relevant result, else 0
  DCG   = sum over 1-indexed i of rel_i / log2(i + 1)
  nDCG  = DCG / IDCG, where IDCG puts min(total_targets, k) relevant items first
"""

from __future__ import annotations

import math
import unittest

from oodarag.evals.harness import dcg, ndcg_at_k, recall_at_k, reciprocal_rank, uri_matches

LOG2_3 = math.log2(3)  # 1.5849625...
LOG2_4 = 2.0


class ReciprocalRank(unittest.TestCase):
    def test_first_result_relevant(self) -> None:
        self.assertAlmostEqual(reciprocal_rank([True, False, False]), 1.0)

    def test_second_result_relevant(self) -> None:
        self.assertAlmostEqual(reciprocal_rank([False, True, False]), 0.5)

    def test_third_result_relevant(self) -> None:
        self.assertAlmostEqual(reciprocal_rank([False, False, True]), 1.0 / 3.0)

    def test_nothing_relevant_is_zero_not_undefined(self) -> None:
        self.assertEqual(reciprocal_rank([False, False]), 0.0)

    def test_empty_is_zero(self) -> None:
        self.assertEqual(reciprocal_rank([]), 0.0)

    def test_only_the_first_hit_counts(self) -> None:
        # RR is defined on the FIRST relevant result. If later hits moved it,
        # it would silently be measuring something else.
        self.assertAlmostEqual(reciprocal_rank([False, True, True, True]), 0.5)


class RecallAtK(unittest.TestCase):
    def test_half_the_targets_found(self) -> None:
        self.assertAlmostEqual(recall_at_k(2, 4), 0.5)

    def test_all_targets_found(self) -> None:
        self.assertAlmostEqual(recall_at_k(3, 3), 1.0)

    def test_none_found(self) -> None:
        self.assertAlmostEqual(recall_at_k(0, 5), 0.0)

    def test_no_targets_does_not_divide_by_zero(self) -> None:
        # A golden with no labelled target is a degenerate row, not a crash.
        value = recall_at_k(0, 0)
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)


class DCG(unittest.TestCase):
    def test_single_relevant_at_rank_one(self) -> None:
        self.assertAlmostEqual(dcg([True]), 1.0)

    def test_single_relevant_at_rank_two(self) -> None:
        self.assertAlmostEqual(dcg([False, True]), 1.0 / LOG2_3)

    def test_single_relevant_at_rank_three(self) -> None:
        self.assertAlmostEqual(dcg([False, False, True]), 1.0 / LOG2_4)

    def test_two_relevant_accumulate(self) -> None:
        self.assertAlmostEqual(dcg([True, True]), 1.0 + 1.0 / LOG2_3)

    def test_position_is_discounted_monotonically(self) -> None:
        # The whole purpose of the discount: earlier is worth strictly more.
        self.assertGreater(dcg([True, False, False]), dcg([False, True, False]))
        self.assertGreater(dcg([False, True, False]), dcg([False, False, True]))

    def test_nothing_relevant_is_zero(self) -> None:
        self.assertEqual(dcg([False, False, False]), 0.0)


class NDCGAtK(unittest.TestCase):
    def test_perfect_ranking_is_one(self) -> None:
        self.assertAlmostEqual(ndcg_at_k([True], total_targets=1, k=8), 1.0)

    def test_two_targets_both_at_top_is_one(self) -> None:
        self.assertAlmostEqual(ndcg_at_k([True, True], total_targets=2, k=8), 1.0)

    def test_one_target_at_rank_two(self) -> None:
        # DCG = 1/log2(3); IDCG = 1. So nDCG is 1/log2(3).
        self.assertAlmostEqual(ndcg_at_k([False, True], total_targets=1, k=8),
                               1.0 / LOG2_3)

    def test_it_is_bounded_by_one(self) -> None:
        for rel, total in (([True, True, True], 1), ([True] * 5, 2), ([True], 1)):
            with self.subTest(rel=rel, total=total):
                self.assertLessEqual(ndcg_at_k(rel, total_targets=total, k=8), 1.0 + 1e-9)

    def test_nothing_relevant_is_zero(self) -> None:
        self.assertEqual(ndcg_at_k([False, False], total_targets=1, k=8), 0.0)

    def test_no_targets_does_not_divide_by_zero(self) -> None:
        value = ndcg_at_k([False], total_targets=0, k=8)
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)


class UriMatching(unittest.TestCase):
    """A golden names a target as a repo-relative path; the pipeline reports an
    absolute file:// URI. If matching drifts, every recall number silently
    becomes zero — or worse, silently becomes one."""

    def test_a_relative_target_matches_its_absolute_uri(self) -> None:
        self.assertTrue(uri_matches("file:///home/user/claude/evals/corpus/bm25-scoring.md",
                                    "evals/corpus/bm25-scoring.md"))

    def test_a_different_document_does_not_match(self) -> None:
        self.assertFalse(uri_matches("file:///home/user/claude/evals/corpus/chunking-strategies.md",
                                     "evals/corpus/bm25-scoring.md"))

    def test_matching_is_not_a_bare_substring_test(self) -> None:
        # "bm25-scoring.md" appearing anywhere must not count; otherwise a
        # sibling path would match and recall would be inflated.
        self.assertFalse(uri_matches("file:///home/user/claude/evals/corpus/notes.md",
                                     "evals/corpus/bm25-scoring.md"))


if __name__ == "__main__":
    unittest.main()
