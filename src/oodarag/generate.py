"""Turning retrieved chunks into an answer that cannot lie about where it came from.

The default generator is *extractive*: every sentence of the answer is copied
verbatim out of a retrieved chunk, and every citation carries the exact quote it
was copied from. That restriction is deliberate, and it is taken for two reasons.

The first is honesty. An honest abstention is a correct answer. A confident
fabrication carrying a real-looking URL is the single worst failure this pipeline
can produce: it reads exactly like a good answer, it survives a skim, and it
poisons whatever it gets pasted into. Extraction removes the *mechanism* - there
is no step in here capable of emitting a sentence the corpus does not contain -
and `verify_citations` then re-derives that guarantee from the strings
themselves, by containment, instead of trusting the code above it. The generator
runs its own output through that check before returning; distrusting this module
from inside this module is the point, because a provenance guarantee that only
holds while the generator is bug-free is not a guarantee.

The second is the zero-dependency promise. An install with no model, no API key
and no network still has to answer questions, or the whole retrieval stack is
unexercised until someone wires up a provider.

Alternatives rejected:

- **Abstractive stitching** (paraphrase or summarize the top chunks). There is
  no stdlib summarizer that does not invent, and the moment the answer text is
  synthesized, "is this quote really in the source" stops being decidable.
- **Ranking sentences by embedding similarity to the question.** The contract
  hands `generate()` no embedder, and a 512-dimension hashing embedder over a
  single sentence is mostly collision noise; idf over the retrieved set is
  computed from data already in hand and degrades sensibly on a short query.
- **Returning the top chunk verbatim.** A 320-token chunk is mostly not the
  answer, and burying one sentence of evidence in a wall of context is how
  citation checking becomes a ceremony nobody performs.

`build_prompt` is the seam for a hosted model. It is unused by the extractive
path and exists so that swapping in a generator later is a change to this module
only, not a rework of retrieval, chunking and citation plumbing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

from oodarag.models import Answer, Citation, ScoredChunk
from oodarag.util.logging import get_logger
from oodarag.util.text import (
    estimate_tokens,
    split_sentences,
    tokenize,
    tokenize_all,
    truncate_tokens,
)

log = get_logger("generate")

#: A sentence shorter than this is damped rather than dropped. Fragments
#: ("Yes.", "See below.") match query terms at a high *rate* and answer nothing,
#: so scoring by coverage alone would rank them first.
_MIN_SENTENCE_TOKENS = 6

#: How fast a sentence's prior decays with the rank of the chunk it came from.
#: Gentle on purpose: retrieval already ordered these, but rank 6 containing the
#: actual answer must still be able to beat rank 1 containing an aside.
_RANK_DECAY = 0.15

#: Independent documents needed for full breadth credit. Three sources agreeing
#: is corroboration; three chunks of one page agreeing is one source repeating
#: itself, which is why breadth counts `doc_id`s and not chunks.
_FULL_SUPPORT_DOCS = 3

#: Breadth can lift a well-evidenced answer by 1/_BREADTH_FLOOR, but never
#: manufactures confidence where the evidence term is zero.
_BREADTH_FLOOR = 0.6

#: Quotes are clipped at a word boundary and never elided with "...", because an
#: ellipsis would break the substring check that makes the citation verifiable.
_MAX_QUOTE_CHARS = 480

#: Below this, a truncated context block in a prompt is a title and no content.
_MIN_BLOCK_TOKENS = 40

_ABSTAIN_PREFIX = "Not enough evidence in the indexed corpus to answer that."


@dataclass(slots=True)
class GenerationConfig:
    max_context_tokens: int = 2000
    min_confidence: float = 0.12
    max_sentences: int = 6


@dataclass(slots=True)
class _Candidate:
    """One candidate sentence, carrying enough to cite it back to a byte range."""

    text: str
    start: int
    end: int
    rank: int
    chunk_id: str
    doc_id: str
    score: float


def _sentences_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Split into sentences and locate each one inside `text`.

    A sentence that cannot be located is dropped instead of being quoted from a
    guessed offset: an unquotable sentence costs one candidate, a wrong offset
    costs the provenance guarantee.
    """
    out: list[tuple[str, int, int]] = []
    cursor = 0
    for sentence in split_sentences(text):
        idx = text.find(sentence, cursor)
        if idx < 0:
            idx = text.find(sentence)
        if idx < 0:
            continue
        out.append((sentence, idx, idx + len(sentence)))
        cursor = idx + len(sentence)
    return out


def _idf_weights(terms: list[str], docs: list[frozenset[str]]) -> dict[str, float]:
    """Inverse document frequency over the *retrieved set*, not the corpus.

    The retrieved set is the only frequency table available at this point, and it
    is the right one anyway: a term shared by every hit discriminates nothing
    between them. A query term matched by no chunk at all keeps the maximum
    weight, so it counts against every sentence's coverage - which is correct,
    the query asked about something retrieval never found.
    """
    n = len(docs)
    weights: dict[str, float] = {}
    for term in terms:
        df = sum(1 for d in docs if term in d)
        weights[term] = math.log(1.0 + n / (1.0 + df))
    return weights


def _clip_quote(text: str) -> str:
    if len(text) <= _MAX_QUOTE_CHARS:
        return text
    cut = text[:_MAX_QUOTE_CHARS]
    head, sep, _ = cut.rpartition(" ")
    return head if sep else cut


class ExtractiveGenerator:
    """Answers using only sentences that appear verbatim in retrieved chunks.

    Extractive by default so the zero-dependency install still answers questions
    and so every citation is verifiable by string containment rather than trust.

    Per-chunk failures are counted into `Answer.metrics` rather than raised: one
    pathological chunk in a retrieval set of eight must not turn a good answer
    into a traceback.
    """

    name: str = "extractive"

    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()

    def generate(self, question: str, scored: list[ScoredChunk]) -> Answer:
        cfg = self.config
        errors: list[str] = []
        by_id: dict[str, ScoredChunk] = {}
        metrics: dict[str, Any] = {"candidates": len(scored)}

        query_terms = list(dict.fromkeys(tokenize(question)))
        candidates = self._score_sentences(query_terms, scored, by_id, errors)
        metrics["sentences_considered"] = len(candidates)
        metrics["failed"] = len(errors)
        if errors:
            metrics["errors"] = errors[:5]

        picked = candidates[: max(cfg.max_sentences, 0)]
        evidence = picked[0].score if picked else 0.0
        doc_ids = {c.doc_id for c in picked}
        support = min(1.0, len(doc_ids) / _FULL_SUPPORT_DOCS) if doc_ids else 0.0

        # confidence = evidence * (0.6 + 0.4 * breadth), both factors in [0, 1]:
        #   evidence = share of the query's idf mass matched by the best sentence,
        #              damped for fragments and for the rank of its chunk
        #   breadth  = independent documents supporting the answer, capped at 3
        # Multiplicative, not additive, so corroboration can only amplify real
        # evidence and never substitute for it. The result stays in [0, 1].
        confidence = round(evidence * (_BREADTH_FLOOR + (1.0 - _BREADTH_FLOOR) * support), 6)
        metrics["evidence"] = round(evidence, 4)
        metrics["support"] = round(support, 4)

        # `min_confidence` is compared against this normalized number rather than
        # against the raw fused retrieval score. The scores arriving here are RRF
        # (rank-1 in one arm is ~0.016) or an MMR blend, so a 0.12 floor read
        # against them would abstain on literally every query; and the threshold
        # has to keep meaning the same thing if the upstream reranker changes.
        if not picked or confidence < cfg.min_confidence:
            if not candidates:
                metrics["reason"] = "no_candidates"
            elif not picked:
                metrics["reason"] = "no_sentence_budget"
            else:
                metrics["reason"] = "below_confidence_floor"
            return self._abstain(question, scored, confidence, metrics)

        text, cited = self._assemble(picked, by_id, metrics)
        verified = verify_citations(text, cited, scored)
        metrics["citations_dropped"] = len(cited) - len(verified)
        metrics["chunks_cited"] = len(verified)
        metrics["documents"] = len({c.doc_id for c in verified})

        if not verified:
            # An answer whose provenance did not survive verification is, from the
            # outside, indistinguishable from a fabrication. Abstain rather than
            # ship prose with the citations quietly stripped off.
            log.warn("all citations failed verification, abstaining", question=question[:80])
            metrics["reason"] = "unverifiable_citations"
            return self._abstain(question, scored, confidence, metrics)

        return Answer(
            question=question,
            text=text,
            citations=verified,
            confidence=confidence,
            abstained=False,
            generator=self.name,
            retrieved=list(scored),
            metrics=metrics,
        )

    def _score_sentences(
        self,
        query_terms: list[str],
        scored: list[ScoredChunk],
        by_id: dict[str, ScoredChunk],
        errors: list[str],
    ) -> list[_Candidate]:
        """Every quotable sentence in the retrieved set, best first."""
        bodies: list[str] = []
        for rank, hit in enumerate(scored):
            try:
                # Sentences are quoted from `chunk.text`, never `indexed_text`:
                # the context header is synthesized by the chunker, so quoting it
                # would attribute our own words to the source document.
                bodies.append(hit.chunk.text or "")
                by_id[hit.chunk.chunk_id] = hit
            except Exception as e:
                errors.append(f"rank {rank}: {type(e).__name__}: {e}")
                bodies.append("")

        term_sets = [frozenset(tokenize(b)) for b in bodies]
        idf = _idf_weights(query_terms, term_sets)
        total_idf = sum(idf.values())
        if total_idf <= 0.0:
            return []  # a query of nothing but stopwords has no evidence to find

        out: list[_Candidate] = []
        seen: set[str] = set()
        for rank, (hit, body) in enumerate(zip(scored, bodies)):
            if not body:
                continue
            prior = 1.0 / (1.0 + _RANK_DECAY * rank)
            try:
                chunk_id = hit.chunk.chunk_id
                doc_id = hit.chunk.doc_id
                for sentence, start, end in _sentences_with_offsets(body):
                    words = tokenize_all(sentence)
                    if not words:
                        continue
                    # Chunks overlap by design, so the same sentence can arrive
                    # from two chunks. Keep the first (best-ranked) copy only.
                    key = " ".join(words)
                    if key in seen:
                        continue
                    seen.add(key)
                    # Exact token match, no stemming. A hand-rolled suffix
                    # stripper is the obvious upgrade and is rejected: half this
                    # corpus is code, where `s3client` and `s3clients` are two
                    # identifiers and conflating them cites the wrong symbol. The
                    # cost is that "use" does not match "used", so an answer
                    # sentence can lose to a worse-worded one; the chunk is still
                    # retrieved and still cited either way.
                    present = frozenset(tokenize(sentence))
                    coverage = sum(w for t, w in idf.items() if t in present) / total_idf
                    if coverage <= 0.0:
                        continue
                    length_factor = min(1.0, len(words) / _MIN_SENTENCE_TOKENS)
                    out.append(
                        _Candidate(
                            text=sentence,
                            start=start,
                            end=end,
                            rank=rank,
                            chunk_id=chunk_id,
                            doc_id=doc_id,
                            score=coverage * length_factor * prior,
                        )
                    )
            except Exception as e:
                errors.append(f"rank {rank}: {type(e).__name__}: {e}")

        out.sort(key=lambda c: (-c.score, c.rank, c.start))
        return out

    def _assemble(
        self,
        picked: list[_Candidate],
        by_id: dict[str, ScoredChunk],
        metrics: dict[str, Any],
    ) -> tuple[str, list[Citation]]:
        """Render the chosen sentences in source order and cite each chunk once."""
        # Reading order follows retrieval rank, then position inside the chunk, so
        # the answer reads like the source rather than like a score table.
        ordered = sorted(picked, key=lambda c: (c.rank, c.start))

        markers: dict[str, int] = {}
        contributing: dict[str, list[_Candidate]] = {}
        pieces: list[str] = []
        used = 0
        dropped = 0
        for cand in ordered:
            marker = markers.get(cand.chunk_id) or len(markers) + 1
            piece = f"{cand.text} [{marker}]"
            if used and used + estimate_tokens(piece) > self.config.max_context_tokens:
                dropped += 1
                continue
            markers[cand.chunk_id] = marker
            contributing.setdefault(cand.chunk_id, []).append(cand)
            pieces.append(piece)
            used += estimate_tokens(piece)

        metrics["sentences_used"] = len(pieces)
        metrics["sentences_over_budget"] = dropped
        text = truncate_tokens(" ".join(pieces), self.config.max_context_tokens)

        citations: list[Citation] = []
        for chunk_id, marker in sorted(markers.items(), key=lambda kv: kv[1]):
            hit = by_id[chunk_id]
            cands = contributing[chunk_id]
            # One contiguous span from the chunk's own text, so the quote stays a
            # true substring even when a chunk contributed several sentences.
            span = hit.chunk.text[min(c.start for c in cands) : max(c.end for c in cands)]
            citations.append(
                Citation(
                    marker=marker,
                    chunk_id=chunk_id,
                    doc_id=hit.chunk.doc_id,
                    title=hit.citation_title,
                    uri=hit.citation_uri,
                    quote=_clip_quote(span),
                    score=round(float(hit.score), 6),
                )
            )
        return text, citations

    def _abstain(
        self,
        question: str,
        scored: list[ScoredChunk],
        confidence: float,
        metrics: dict[str, Any],
    ) -> Answer:
        """Say so, plainly, with no citations attached.

        An honest abstention is a correct answer. A confident fabrication with a
        real-looking URL is the single worst failure this pipeline can have: it
        is unfalsifiable at a glance and it travels. The abstention text names
        the number and the floor so a caller can tell "nothing was retrieved"
        from "the floor is set too high" without reading the metrics.
        """
        reason = metrics.get("reason", "")
        if reason == "no_candidates":
            detail = (
                f"Nothing in the {len(scored)} retrieved passage(s) mentions what the "
                f"question asks about."
            )
        elif reason == "no_sentence_budget":
            detail = (
                f"max_sentences is {self.config.max_sentences}, so no sentence could be quoted."
            )
        elif reason == "unverifiable_citations":
            detail = (
                "Sentences were found, but none of their citations could be traced back "
                "to a retrieved source, so the answer has no provenance to stand on."
            )
        else:
            detail = (
                f"The best supporting passage scored {confidence:.2f}, below the "
                f"{self.config.min_confidence:.2f} confidence floor."
            )
        text = (
            f"{_ABSTAIN_PREFIX} {detail} Answering anyway would mean inventing the part "
            f"the retrieved sources do not contain."
        )
        return Answer(
            question=question,
            text=text,
            citations=[],
            confidence=confidence,
            abstained=True,
            generator=self.name,
            retrieved=list(scored),
            metrics=metrics,
        )


def verify_citations(
    answer_text: str, citations: list[Citation], scored: list[ScoredChunk]
) -> list[Citation]:
    """Drop every citation that cannot be proved from the retrieved set.

    This is the safety net, and it is written to be adversarial towards whatever
    produced the citations - including `ExtractiveGenerator` itself, which runs
    its own output through here. A citation survives only if:

    1. it names a chunk that is actually in `scored` (no citing a chunk that was
       never retrieved, and no citing a chunk id that does not exist);
    2. its quote is a non-empty substring of that chunk's *body text*. Not
       `indexed_text`: the context header is written by the chunker, so a quote
       matched against it would attribute our own words to the source;
    3. its `doc_id` and `uri` agree with the chunk's own document. A plausible
       URL bolted onto a real quote is precisely the failure this pipeline must
       never emit, and it is the one a reader is least able to catch.

    Duplicate (chunk, quote) pairs collapse. Nothing is repaired: a citation that
    fails is removed, because a silently corrected citation is a claim that was
    never checked by anybody.
    """
    if not answer_text.strip():
        return []  # nothing was asserted, so there is nothing to support

    retrieved: dict[str, ScoredChunk] = {}
    for hit in scored:
        try:
            retrieved[hit.chunk.chunk_id] = hit
        except AttributeError:
            continue

    kept: list[Citation] = []
    seen: set[tuple[str, str]] = set()
    for cite in citations:
        hit = retrieved.get(cite.chunk_id)
        if hit is None:
            log.warn("citation dropped: chunk not retrieved", chunk_id=cite.chunk_id)
            continue
        if not cite.quote or cite.quote not in hit.chunk.text:
            log.warn("citation dropped: quote not in chunk", chunk_id=cite.chunk_id)
            continue
        if cite.doc_id and cite.doc_id != hit.chunk.doc_id:
            log.warn("citation dropped: doc_id mismatch", chunk_id=cite.chunk_id)
            continue
        if cite.uri and cite.uri != hit.citation_uri:
            log.warn("citation dropped: uri mismatch", chunk_id=cite.chunk_id, uri=cite.uri)
            continue
        key = (cite.chunk_id, cite.quote)
        if key in seen:
            continue
        seen.add(key)
        kept.append(cite)

    # Markers index into `answer_text`. If the answer uses them, renumbering the
    # survivors would silently repoint every remaining marker at another source,
    # so it only happens when the answer carries no markers at all.
    if kept and not any(f"[{c.marker}]" in answer_text for c in kept):
        kept = [replace(c, marker=i) for i, c in enumerate(kept, 1)]
    return kept


def build_prompt(question: str, scored: list[ScoredChunk], max_tokens: int = 2000) -> str:
    """Render retrieval as a numbered, cited context block for a hosted model.

    Unused by the extractive path. It lives here so that dropping in an API
    generator later touches this module and nothing else - the marker scheme is
    the same 1-based ordering `ExtractiveGenerator` uses, so `verify_citations`
    can police a hosted model's citations with no changes at all.

    The block loop spends a budget rather than assembling first and cutting
    after: the trailing question is what a model conditions on hardest, and a
    blind truncation at the end is exactly what would remove it. The closing
    `truncate_tokens` is the guarantee, not the mechanism.
    """
    header = (
        "Answer the question using only the numbered sources below.\n"
        "Cite every claim with its source marker, like [2]. Prefer the wording of\n"
        "the sources. If the sources do not contain the answer, reply exactly:\n"
        "not enough evidence.\n\nSources:\n"
    )
    footer = f"\nQuestion: {question}\nAnswer:"
    budget = max_tokens - estimate_tokens(header) - estimate_tokens(footer)

    blocks: list[str] = []
    skipped = 0
    for i, hit in enumerate(scored, 1):
        if budget < _MIN_BLOCK_TOKENS:
            break
        try:
            block = f"[{i}] {hit.citation_title} ({hit.citation_uri})\n{hit.chunk.indexed_text}\n"
        except Exception as e:
            skipped += 1
            log.warn("prompt block skipped", rank=i, err=f"{type(e).__name__}: {e}")
            continue
        cost = estimate_tokens(block)
        if cost > budget:
            # Clip rather than drop: the block's first line is its citation, so a
            # partial source is still attributable, while dropping it entirely
            # would leave a marker in the numbering with nothing behind it.
            blocks.append(truncate_tokens(block, budget))
            budget = 0
            break
        blocks.append(block)
        budget -= cost

    if skipped:
        log.warn("prompt built with skipped sources", skipped=skipped)
    body = "\n".join(blocks) if blocks else "(no sources retrieved)\n"
    return truncate_tokens(f"{header}{body}{footer}", max_tokens)
