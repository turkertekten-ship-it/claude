"""Does term co-occurrence separate answerable questions from unanswerable ones?

L50: "What is the capital of France?" is answered with confidence 0.758 because
`capit` appears in idna.md ("capital letters") and `franc` in chardet.md (a
French sample string). Each term exists; they never co-occur. For a genuinely
answerable question the discriminating terms sit in one document.

Measured before building anything: if the two classes do not separate, the
factor is not worth adding.

**They do not separate.** Across six rarity cutoffs the best single threshold
gives TPR-FPR of 0.159 at most, and both classes sit at median 1.00. The France
case is real and does not generalise: most unanswerable questions here are
ordinary English whose terms co-occur somewhere in dev prose anyway. Nothing was
built. See LEARNINGS L51.
"""
import json, math, pathlib
from oodarag.util.text import tokenize

docs = {p.stem: set(tokenize(p.read_text("utf-8", errors="replace"), stem_words=True))
        for p in pathlib.Path("corpus/external/pypi").glob("*.md")}
N = len(docs)
df = {}
for terms in docs.values():
    for t in terms:
        df[t] = df.get(t, 0) + 1

goldens = [json.loads(l) for l in open("evals/goldens-external.jsonl")
           if l.strip() and not l.lstrip().startswith("#")]


RARITY = 1 / 3


def best_cooccurrence(question: str) -> tuple[float, int]:
    """Largest share of the query's in-corpus content terms found in one document."""
    q = [t for t in dict.fromkeys(tokenize(question, stem_words=True)) if t in df]
    content = [t for t in q if df[t] <= N * RARITY]
    if not content:
        return 1.0, 0
    best = max((sum(t in d for t in content) for d in docs.values()), default=0)
    return best / len(content), len(content)


def evaluate():
    pos, neg = [], []
    for g in goldens:
        share, k = best_cooccurrence(g["question"])
        (neg if g.get("expect_abstain") else pos).append((share, k, g["question"]))
    best = max(((sum(s >= th for s, _, _ in pos) / len(pos)
                 - sum(s >= th for s, _, _ in neg) / len(neg), th)
                for th in [i / 20 for i in range(21)]))
    return pos, neg, best

print("| rarity cutoff (df <=) | best threshold | TPR-FPR | pos median | neg median |")
print("|---|---|---|---|---|")
for r in (1/3, 0.2, 0.1, 0.05, 0.03, 0.02):
    RARITY = r
    P, Ng, b = evaluate()
    pm = sorted(x[0] for x in P)[len(P)//2]
    nm = sorted(x[0] for x in Ng)[len(Ng)//2]
    print(f"| {r*100:.0f}% of corpus | {b[1]:.2f} | {b[0]:.3f} | {pm:.2f} | {nm:.2f} |")
RARITY = 1/3

pos, neg = [], []
for g in goldens:
    share, k = best_cooccurrence(g["question"])
    (neg if g.get("expect_abstain") else pos).append((share, k, g["question"]))

def summarise(rows, label):
    shares = sorted(r[0] for r in rows)
    mid = shares[len(shares) // 2]
    print(f"{label:22} n={len(rows):2}  min={shares[0]:.2f}  median={mid:.2f}  max={shares[-1]:.2f}")

summarise(pos, "answerable")
summarise(neg, "expect abstention")
print()
print("negatives with the HIGHEST co-occurrence (would still slip through):")
for share, k, q in sorted(neg, reverse=True)[:4]:
    print(f"  {share:.2f} ({k} content terms)  {q[:60]}")
print("answerable with the LOWEST co-occurrence (would be wrongly penalised):")
for share, k, q in sorted(pos)[:4]:
    print(f"  {share:.2f} ({k} content terms)  {q[:60]}")

# Separation: does any single threshold split them usefully?
best = max(((sum(s >= th for s, _, _ in pos) / len(pos)
             - sum(s >= th for s, _, _ in neg) / len(neg), th)
            for th in [i / 20 for i in range(21)]))
print(f"\nbest single threshold: {best[1]:.2f}  (TPR-FPR = {best[0]:.3f})")
