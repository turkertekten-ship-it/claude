"""Is the register mismatch an artifact of small N?

L48 measured that IDF ranks the discriminating query term first in only 28 of
40 goldens, because a function word like "cannot" appears in ~1 of 91 PyPI
pages and so scores as rare. If that is a small-corpus artifact, then at larger
N the function words should appear in proportionally more documents, their IDF
should fall, and discrimination should improve - with no code change at all.

Testable now, for free, by subsampling the corpus we have: measure the rate at
several sizes and look at the trend. Deterministic subsampling (sorted, strided)
so the answer does not depend on a seed.

If the rate is flat or falling in N, widening the corpus will not fix this and
the fetch is not worth making.
"""
import json, math, pathlib, sys

from oodarag.util.text import tokenize

CORPUS = pathlib.Path("corpus/external/pypi")
GOLDENS = pathlib.Path("evals/goldens-external.jsonl")

docs = sorted(CORPUS.glob("*.md"))
texts = {p.stem: p.read_text("utf-8", errors="replace") for p in docs}
terms = {name: set(tokenize(t, stem_words=True)) for name, t in texts.items()}

goldens = [json.loads(l) for l in GOLDENS.read_text("utf-8").splitlines()
           if l.strip() and not l.lstrip().startswith("#")]


def rate_at(names: list[str]) -> tuple[int, int]:
    n = len(names)
    present = {name: terms[name] for name in names}
    df: dict[str, int] = {}
    for ts in present.values():
        for t in ts:
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log(1 + n / c) for t, c in df.items()}

    hits = considered = 0
    for g in goldens:
        sources = g.get("expect_sources") or []
        target = next((k for k in present if any(s in k for s in sources)), None)
        if target is None:
            continue
        q = [t for t in dict.fromkeys(tokenize(g["question"], stem_words=True))
             if t in idf]
        if not q:
            continue
        disc = {t for t in q if t in present[target] and df.get(t, 0) <= 0.2 * n}
        if not disc:
            continue
        considered += 1
        hits += max(q, key=lambda t: (idf[t], t)) in disc
    return hits, considered


# Nested subsamples, so every size is a superset of the smallest. The question
# set is then held fixed at the goldens answerable in the *smallest* corpus -
# otherwise each row scores a different set of questions and the "trend" is an
# artifact of which targets survived subsampling, not of N.
SIZES = [20, 30, 45, 60, 75, len(docs)]
nested = []
for size in SIZES:
    stride = max(1, len(docs) // size)
    nested.append([p.stem for p in docs[::stride]][:size])
for i in range(1, len(nested)):
    nested[i] = sorted(set(nested[i]) | set(nested[i - 1]))

base_targets = set(nested[0])
fixed = []
for g in goldens:
    sources = g.get("expect_sources") or []
    if any(any(s in k for s in sources) for k in base_targets):
        fixed.append(g)
print(f"question set held fixed at {len(fixed)} goldens answerable in the "
      f"smallest ({len(nested[0])}-document) corpus\n")
goldens = fixed

print("| corpus size | discriminating-term-first | rate |")
print("|-------------|---------------------------|------|")
for names in nested:
    hits, considered = rate_at(names)
    if considered:
        print(f"| {len(names):<11} | {hits}/{considered:<24} | {hits/considered:.1%} |")
