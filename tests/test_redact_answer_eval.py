"""Tests for redaction, grounded answering, and the evaluation harness.

The redaction tests are weighted towards what must SURVIVE a pass. A redactor
that catches every identifier and also eats every lira amount has not protected
the document, it has destroyed it — silently, since the wreckage still reads as
plausible Turkish.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from oodarag.answer.extractive import ExtractiveAnswerer
from oodarag.answer.guards import (
    asks_for_a_figure,
    asks_for_redacted_class,
    missing_figure,
    topic_coverage,
)
from oodarag.answer.verify import coverage, quote_supported, verify_citations
from oodarag.eval import metrics
from oodarag.eval.harness import EvalHarness, EvalReport, Golden, compare
from oodarag.models import Answer, Chunk, Citation, Document, ScoredChunk
from oodarag.redact import Redactor, valid_iban, valid_luhn, valid_tckn, valid_vkn

# A TCKN and a VKN constructed to satisfy their own checksums.
GOOD_TCKN = "10100000046"
GOOD_VKN = "0010000009"
GOOD_IBAN = "TR33 0006 1005 1978 6457 8413 26"


def _chunk(cid: str, text: str, doc_id: str = "d1") -> Chunk:
    return Chunk(chunk_id=cid, doc_id=doc_id, ordinal=0, text=text)


def _scored(cid: str, text: str, score: float = 0.5,
            path: str = "docs/x.md") -> ScoredChunk:
    doc = Document(doc_id="d1", source_system="repo", external_id=path, uri=f"file://{path}",
                   title="x", text=text, content_hash="h", metadata={"path": path})
    return ScoredChunk(chunk=_chunk(cid, text), score=score, document=doc)


class TestChecksums(unittest.TestCase):
    def test_tckn(self) -> None:
        self.assertTrue(valid_tckn(GOOD_TCKN))
        self.assertFalse(valid_tckn("12345678901"))
        self.assertFalse(valid_tckn("01234567890"))   # may not start with zero
        self.assertFalse(valid_tckn("1234567890"))    # ten digits

    def test_vkn(self) -> None:
        self.assertTrue(valid_vkn(GOOD_VKN))
        # The VKN check digit accepts roughly one ten-digit string in ten, so a
        # rejected example has to be chosen rather than assumed: 1234567890 is
        # in fact a valid VKN, which is exactly why the pattern alone is not a
        # filter and the checksum has to carry the decision.
        self.assertTrue(valid_vkn("1234567890"))
        self.assertFalse(valid_vkn("1234567891"))
        self.assertFalse(valid_vkn("123456789"))

    def test_iban(self) -> None:
        self.assertTrue(valid_iban(GOOD_IBAN))
        self.assertFalse(valid_iban("TR33 0006 1005 1978 6457 8413 27"))
        self.assertFalse(valid_iban("TR12"))

    def test_luhn(self) -> None:
        self.assertTrue(valid_luhn("4539 1488 0343 6467"))
        self.assertFalse(valid_luhn("4539 1488 0343 6468"))


class TestRedactionDoesNotDestroyDocuments(unittest.TestCase):
    """The over-matching trap: everything below must come through untouched."""

    def setUp(self) -> None:
        self.r = Redactor(key=b"deterministic-test-key")

    def test_turkish_amounts_survive(self) -> None:
        for amount in ("1.234.567,89", "12.345.678.901,50", "30.000.000", "0,05"):
            out, _ = self.r.redact(f"Tutar {amount} TRY")
            self.assertIn(amount, out, amount)

    def test_dates_and_identifiers_survive(self) -> None:
        text = "31.07.2026 tarihli, ISIN TRSWAMP12345, tebliğ III-52.4, karar 45/1359"
        out, _ = self.r.redact(text)
        for token in ("31.07.2026", "TRSWAMP12345", "III-52.4", "45/1359"):
            self.assertIn(token, out, token)

    def test_a_bare_eleven_digit_number_that_is_not_a_tckn_survives(self) -> None:
        """The whole reason for the checksum. Without it every large figure goes."""
        out, findings = self.r.redact("referans 20260731000 ile")
        self.assertIn("20260731000", out)
        self.assertEqual(findings, [])

    def test_thirty_million_lira_is_not_a_vkn(self) -> None:
        out, _ = self.r.redact("Ödenmiş sermaye 30000000 TRY")
        self.assertIn("30000000", out)


class TestRedactionCatchesIdentifiers(unittest.TestCase):
    def setUp(self) -> None:
        self.r = Redactor(key=b"deterministic-test-key")

    def test_catches_each_kind(self) -> None:
        text = (f"TC {GOOD_TCKN}, VKN {GOOD_VKN}, IBAN {GOOD_IBAN}, "
                "e-posta a@b.com, tel +90 532 111 22 33.")
        out, findings = self.r.redact(text)
        kinds = {f.kind for f in findings}
        self.assertEqual(kinds, {"TCKN", "VKN", "IBAN", "EMAIL", "PHONE"})
        for raw in (GOOD_TCKN, GOOD_VKN, "a@b.com"):
            self.assertNotIn(raw, out, raw)

    def test_identifier_at_end_of_a_clause_is_still_caught(self) -> None:
        """Trailing punctuation must not shield an identifier."""
        out, _ = self.r.redact(f"Kimlik {GOOD_TCKN}, adres yok.")
        self.assertNotIn(GOOD_TCKN, out)

    def test_tokens_are_stable_and_typed(self) -> None:
        a, _ = self.r.redact(f"x {GOOD_TCKN} y")
        b, _ = self.r.redact(f"z {GOOD_TCKN} w")
        token = self.r.token("TCKN", GOOD_TCKN)
        self.assertIn(token, a)
        self.assertIn(token, b)
        self.assertIn("REDACTED:TCKN:", token)

    def test_different_keys_give_different_tokens(self) -> None:
        other = Redactor(key=b"another-key")
        self.assertNotEqual(self.r.token("TCKN", GOOD_TCKN),
                            other.token("TCKN", GOOD_TCKN))

    def test_empty_input(self) -> None:
        self.assertEqual(self.r.redact(""), ("", []))

    def test_callable_form_returns_text(self) -> None:
        self.assertIsInstance(self.r(f"TC {GOOD_TCKN}"), str)


class TestCitationVerification(unittest.TestCase):
    def test_a_fabricated_quote_is_dropped(self) -> None:
        """The control the whole design rests on."""
        retrieved = [_scored("c1", "The policy rate stands at 37 percent.")]
        answer = Answer(question="q", text="The policy rate stands at 99 percent. [1]",
                        citations=[Citation(1, "c1", "d1", "x", "u",
                                            "The policy rate stands at 99 percent.", 0.5)],
                        confidence=0.9)
        out = verify_citations(answer, retrieved)
        self.assertEqual(out.citations, [])
        self.assertTrue(out.abstained)
        self.assertEqual(out.metrics["citations_dropped"], 1)

    def test_citing_a_chunk_that_was_not_retrieved_is_dropped(self) -> None:
        retrieved = [_scored("c1", "real text here")]
        answer = Answer(question="q", text="real text here [1]",
                        citations=[Citation(1, "GHOST", "d1", "x", "u",
                                            "real text here", 0.5)], confidence=0.9)
        self.assertTrue(verify_citations(answer, retrieved).abstained)

    def test_a_true_quote_survives(self) -> None:
        retrieved = [_scored("c1", "The policy rate stands at 37 percent.")]
        answer = Answer(question="q", text="The policy rate stands at 37 percent. [1]",
                        citations=[Citation(1, "c1", "d1", "x", "u",
                                            "The policy rate stands at 37 percent.", 0.5)],
                        confidence=0.9)
        out = verify_citations(answer, retrieved)
        self.assertEqual(len(out.citations), 1)
        self.assertFalse(out.abstained)
        self.assertEqual(coverage(out), 1.0)

    def test_whitespace_is_normalised_but_content_is_not(self) -> None:
        self.assertTrue(quote_supported("a  b\nc", "a b c"))
        self.assertFalse(quote_supported("a b d", "a b c"))

    def test_a_digit_change_breaks_the_match(self) -> None:
        """Loose matching would defeat the entire control."""
        self.assertFalse(quote_supported("rate is 37", "rate is 38"))

    def test_partial_failure_costs_confidence_proportionally(self) -> None:
        retrieved = [_scored("c1", "true sentence one.")]
        answer = Answer(question="q", text="true sentence one. [1] invented. [2]",
                        citations=[
                            Citation(1, "c1", "d1", "x", "u", "true sentence one.", 0.5),
                            Citation(2, "c1", "d1", "x", "u", "invented.", 0.5)],
                        confidence=1.0)
        out = verify_citations(answer, retrieved)
        self.assertEqual(len(out.citations), 1)
        self.assertLess(out.confidence, 1.0)
        self.assertFalse(out.abstained)


class TestGuards(unittest.TestCase):
    def test_off_topic_question_scores_low_coverage(self) -> None:
        retrieved = [_scored("c1", "inflation accounting and fund valuation in Turkey")]
        self.assertLess(topic_coverage("football league champion trophy", retrieved), 0.6)

    def test_on_topic_question_scores_high(self) -> None:
        retrieved = [_scored("c1", "inflation accounting and fund valuation in Turkey")]
        self.assertGreater(topic_coverage("fund valuation inflation", retrieved), 0.9)

    def test_quantity_questions_are_recognised(self) -> None:
        for q in ("How many funds?", "what is the exact net asset value",
                  "ne kadar", "kaç tane"):
            self.assertTrue(asks_for_a_figure(q), q)
        self.assertFalse(asks_for_a_figure("Why is deal sourcing excluded?"))

    def test_a_year_does_not_count_as_the_figure(self) -> None:
        """Otherwise every passage mentioning 2026 answers every 'how much'."""
        self.assertIsNotNone(missing_figure("how many funds", ["Written in 2026. [1]"]))
        self.assertIsNone(missing_figure("how many funds", ["There are 4 funds."]))

    def test_redacted_classes_are_refused_by_construction(self) -> None:
        for q in ("What is his home address?", "give me the mobile number",
                  "what is the IBAN"):
            self.assertIsNotNone(asks_for_redacted_class(q), q)
        self.assertIsNone(asks_for_redacted_class("What are the fund codes?"))


class TestExtractiveAnswerer(unittest.TestCase):
    def setUp(self) -> None:
        self.a = ExtractiveAnswerer()

    def test_abstains_on_nothing_retrieved(self) -> None:
        out = self.a.answer("anything", [])
        self.assertTrue(out.abstained)
        self.assertIn("abstain_reason", out.metrics)

    def test_every_sentence_carries_a_marker(self) -> None:
        text = ("The management company applies inflation accounting under TMS 29. "
                "Investment funds are exempt from that requirement entirely.")
        out = self.a.answer("inflation accounting management company funds",
                            [_scored("c1", text)])
        self.assertFalse(out.abstained)
        self.assertIn("[1]", out.text)
        self.assertTrue(out.citations)

    def test_quotes_are_verbatim_so_verification_cannot_fail(self) -> None:
        text = ("The management company applies inflation accounting under TMS 29. "
                "Investment funds are exempt from that requirement entirely.")
        scored = [_scored("c1", text)]
        out = verify_citations(self.a.answer("inflation accounting funds exempt", scored),
                               scored)
        self.assertFalse(out.abstained)
        self.assertEqual(out.metrics["citations_dropped"], 0)


class TestMetrics(unittest.TestCase):
    def test_recall_and_precision(self) -> None:
        self.assertEqual(metrics.recall_at_k(["a", "b", "c"], ["a", "z"], 3), 0.5)
        self.assertAlmostEqual(metrics.precision_at_k(["a", "b"], ["a"], 2), 0.5)

    def test_mrr_rewards_the_first_hit(self) -> None:
        self.assertEqual(metrics.mrr(["x", "a"], ["a"]), 0.5)
        self.assertEqual(metrics.mrr(["a", "x"], ["a"]), 1.0)
        self.assertEqual(metrics.mrr(["x"], ["a"]), 0.0)

    def test_ndcg_prefers_earlier_hits(self) -> None:
        early = metrics.ndcg_at_k(["a", "x", "y"], ["a"], 3)
        late = metrics.ndcg_at_k(["x", "y", "a"], ["a"], 3)
        self.assertGreater(early, late)

    def test_empty_inputs_return_zero_rather_than_raising(self) -> None:
        """A metric that raises on an empty result set hides a regression."""
        self.assertEqual(metrics.recall_at_k([], [], 5), 0.0)
        self.assertEqual(metrics.mrr([], ["a"]), 0.0)
        self.assertEqual(metrics.abstention_rate([]), 0.0)

    def test_calibration_error_catches_overconfidence(self) -> None:
        bad = metrics.calibration_error([0.9, 0.9, 0.9, 0.9], [True, False, False, False])
        good = metrics.calibration_error([0.9, 0.9, 0.9, 0.9], [True, True, True, True])
        self.assertGreater(bad, good)


class TestEvalHarness(unittest.TestCase):
    def test_missing_golden_file_returns_empty_not_a_crash(self) -> None:
        self.assertEqual(EvalHarness.load("/nonexistent/goldens.jsonl"), [])

    def test_malformed_lines_are_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "g.jsonl"
            p.write_text('{"question":"ok"}\nnot json\n{"no_question":1}\n', encoding="utf-8")
            self.assertEqual(len(EvalHarness.load(p)), 1)

    def test_shipped_golden_set_contains_abstention_cases(self) -> None:
        """A golden set with no unanswerable questions cannot detect a bluffer."""
        goldens = EvalHarness.load("evals/goldens.jsonl")
        self.assertGreaterEqual(len(goldens), 12)
        self.assertGreaterEqual(sum(1 for g in goldens if g.should_abstain), 3)

    def test_answering_when_it_should_abstain_fails_the_case(self) -> None:
        class FakeRetriever:
            def retrieve(self, q: str, k: int = 5) -> list[ScoredChunk]:
                return [_scored("c1", "Fund valuation and inflation accounting in Turkey.")]

        report = EvalHarness(FakeRetriever()).run([
            Golden(question="Fund valuation inflation accounting", should_abstain=True)])
        self.assertEqual(report.passed, 0)
        self.assertIn("should have refused", report.cases[0].why)

    def test_compare_flags_a_material_drop_and_ignores_an_improvement(self) -> None:
        current = EvalReport(aggregate={"pass_rate": 0.5, "recall_at_5": 0.9,
                                        "abstention_rate": 0.1})
        baseline = {"aggregate": {"pass_rate": 0.9, "recall_at_5": 0.5,
                                  "abstention_rate": 0.1}}
        drops = compare(current, baseline)
        self.assertTrue(any("pass_rate" in d for d in drops))
        self.assertFalse(any("recall_at_5" in d for d in drops))

    def test_compare_treats_a_jump_in_abstention_as_a_regression(self) -> None:
        current = EvalReport(aggregate={"abstention_rate": 0.9})
        drops = compare(current, {"aggregate": {"abstention_rate": 0.1}})
        self.assertTrue(any("abstention_rate" in d for d in drops))

    def test_report_renders_both_ways(self) -> None:
        report = EvalReport(aggregate={"pass_rate": 1.0})
        self.assertIn("Retrieval evaluation", report.to_markdown())
        self.assertIn("aggregate", json.loads(report.to_json()))


if __name__ == "__main__":
    unittest.main()
