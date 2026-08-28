"""Are the two unfixable retrieval failures a bug, or the documented cost of ADR 0001?

Five external cases fail. Three are the abstention gate (L77: no threshold
separates them). The other two are documents that never enter the candidate set
at all - freezegun at lexical rank 107 and dense 331 - and L80 established that
query expansion cannot reach them, because it re-ranks the candidate set rather
than extending it.

`embedding/hashing.py` says of itself: "It is not a learned model and it will
not match a good neural embedder on paraphrase." The hypothesis was that these
two questions share fewer literal terms with their answer than the ones that
pass, making the failures the price of the zero-dependency core (ADR 0001)
rather than a defect.

**Measured, that is false**, which is why this script now reports two things
instead of one. Raw overlap:

    cases that pass    min 0.200  p25 0.571  median 0.714  max 1.000
    the two that fail  0.500 and 0.667

Both failures sit above the passing p25, and six passing cases have *lower*
overlap than either - bcrypt passes on 0.200. So how much of the question the
answer contains does not decide anything.

What the missing terms suggest instead is *which* terms are left. freezegun is
missing `clock` and `control`, responses `fake`, `network`, `repli`. What
remains in both is high-frequency vocabulary for a corpus of Python packages -
test, time, return, library - so the answer document is no better matched than
a hundred others. The second table measures that: the idf mass of the shared
terms, and how many documents share them.

    PYTHONPATH=src python3 scripts/paraphrase_gap.py
"""
import json
import pathlib
import statistics

from oodarag.util.text import tokenize

CORPUS = pathlib.Path("corpus/external/pypi")
GOLDENS = pathlib.Path("evals/goldens-external.jsonl")
FAILING = {"freezegun", "responses"}


def content_terms(text: str) -> set[str]:
    return set(tokenize(text, stem_words=True))


def main() -> None:
    docs = {p.stem: content_terms(p.read_text("utf-8", errors="replace"))
            for p in CORPUS.glob("*.md")}
    passing, failing = [], []
    for line in GOLDENS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        case = json.loads(line)
        expected = [s for s in case.get("expect_sources", [])]
        if not expected:
            continue
        query = content_terms(case["question"])
        if not query:
            continue
        # Share of the question's terms the expected document actually contains.
        # This is what a term-matching retriever has to work with; a learned
        # embedder would not be limited to it.
        for name in expected:
            stem = pathlib.Path(name).stem
            if stem not in docs:
                continue
            overlap = len(query & docs[stem]) / len(query)
            (failing if stem in FAILING else passing).append(
                (overlap, case["question"], stem))

    for label, rows in (("cases that pass", passing), ("the two that fail", failing)):
        scores = sorted(r[0] for r in rows)
        print(f"\n{label}: {len(scores)} cases  min {scores[0]:.3f}  "
              f"p25 {scores[len(scores)//4]:.3f}  median {statistics.median(scores):.3f}  "
              f"max {scores[-1]:.3f}")

    print("\nlowest-overlap cases overall:")
    for overlap, question, stem in sorted(passing + failing)[:6]:
        mark = "  <-- fails" if stem in FAILING else ""
        print(f"  {overlap:.3f}  [{stem}] {question}{mark}")

    # The discriminativeness of what *is* shared, which is the hypothesis the
    # raw-overlap table above forces us to. A term in 1 document of 153 picks
    # the answer out; a term in 120 of them cannot.
    df: dict[str, int] = {}
    for terms in docs.values():
        for term in terms:
            df[term] = df.get(term, 0) + 1
    total = len(docs)
    rows = []
    for line in GOLDENS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        case = json.loads(line)
        query = content_terms(case["question"])
        for name in case.get("expect_sources", []):
            stem = pathlib.Path(name).stem
            if stem not in docs or not query:
                continue
            shared = query & docs[stem]
            if not shared:
                continue
            # Document frequency of the *rarest* shared term: the best hook the
            # retriever has for picking this document out of the corpus.
            rarest = min(df[t] for t in shared)
            rows.append((rarest, stem, case["question"]))
    passing_r = sorted(r[0] for r in rows if r[1] not in FAILING)
    failing_r = sorted(r[0] for r in rows if r[1] in FAILING)
    print(f"\ndocument frequency of the rarest shared term (of {total} documents):")
    print(f"  cases that pass    min {passing_r[0]}  p25 {passing_r[len(passing_r)//4]}  "
          f"median {statistics.median(passing_r):.0f}  max {passing_r[-1]}")
    print(f"  the two that fail  {failing_r}")

    print("\nterms the question uses that its answer document does not contain:")
    for line in GOLDENS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        case = json.loads(line)
        for name in case.get("expect_sources", []):
            stem = pathlib.Path(name).stem
            if stem in FAILING and stem in docs:
                missing = sorted(content_terms(case["question"]) - docs[stem])
                print(f"  [{stem}] {case['question']}")
                print(f"      missing: {', '.join(missing) or '(none)'}")


if __name__ == "__main__":
    main()
