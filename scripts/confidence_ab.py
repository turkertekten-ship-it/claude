"""Does confidence separate right from wrong answers better if built from
relevance instead of the total score?

`_confidence` uses `results[0].score` - the total, which folds in authority,
recency and position. `rerank.py` says of exactly that number: "Fold them into
one number and the total stops being usable as an 'is this relevant at all'
signal ... the abstention gate uses `rerank_relevance` alone." The gate obeys
that; the confidence reported to the caller does not.

Scored by how well each formulation separates answers that cited the expected
source from ones that did not: AUC over all right/wrong pairs, plus the best
achievable TPR-FPR.

**Result: no.** The current form has the best AUC (0.665) and nothing is
distinguishable at 11 wrong answers. The reason is L43: authority is constant
across a single-source corpus and recency is saturated, so `top` is already
`relevance + phrase + a constant` here. The inconsistency is real and inert on
*this* corpus - it would bite on one with mixed authority or real age spread,
which is exactly what the priors were built for. Nothing changed; see L60.
"""
import json
from oodarag.config import Config
from oodarag.cli import _build, _generator

config = Config.load("oodarag-external.toml")
store, pipeline = _build(config)
gen = _generator(config, pipeline)
docs = {d.doc_id: d.uri for d in store.all_documents()}
goldens = [json.loads(l) for l in open("evals/goldens-external.jsonl")
           if l.strip() and not l.lstrip().startswith("#")]

samples = []   # (right?, top, margin, coverage, best_relevance)
for g in goldens:
    a = gen.answer(g["question"])
    if a.abstained or not a.retrieved:
        continue
    res = a.retrieved
    top = res[0].score
    margin = top - res[min(4, len(res) - 1)].score
    rel = max(r.components.get("rerank_relevance", 0.0) for r in res)
    cov = a.metrics.get("citation_coverage", a.metrics.get("coverage", 1.0)) or 1.0
    srcs = g.get("expect_sources") or []
    right = (not g.get("expect_abstain")) and (
        not srcs or any(any(s in docs.get(c.doc_id, "") for s in srcs) for c in a.citations))
    samples.append((right, top, margin, cov, rel))

def auc(scorer):
    pos = [scorer(s) for s in samples if s[0]]
    neg = [scorer(s) for s in samples if not s[0]]
    if not pos or not neg:
        return float("nan"), float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    a = wins / (len(pos) * len(neg))
    best = max((sum(p >= t for p in pos)/len(pos) - sum(n >= t for n in neg)/len(neg))
               for t in [i/200 for i in range(201)])
    return a, best

clip = lambda x, d: min(1.0, x / d)
FORMS = {
    "current: .5*top/.6 +.2*sep +.3*cov":
        lambda s: 0.5*clip(s[1],0.6) + 0.2*clip(s[2],0.25) + 0.3*s[3],
    "relevance only":
        lambda s: clip(s[4], 0.5),
    "swap top -> relevance":
        lambda s: 0.5*clip(s[4],0.5) + 0.2*clip(s[2],0.25) + 0.3*s[3],
    "current x relevance":
        lambda s: (0.5*clip(s[1],0.6)+0.2*clip(s[2],0.25)+0.3*s[3]) * clip(s[4],0.5),
    "half top, half relevance":
        lambda s: 0.25*clip(s[1],0.6) + 0.25*clip(s[4],0.5) + 0.2*clip(s[2],0.25) + 0.3*s[3],
}
print(f"{len([s for s in samples if s[0]])} right, "
      f"{len([s for s in samples if not s[0]])} wrong\n")
print(f"| formulation | AUC | best TPR-FPR |")
print(f"|---|---|---|")
for name, f in FORMS.items():
    a, b = auc(f)
    print(f"| {name:36} | {a:.3f} | {b:.3f} |")
