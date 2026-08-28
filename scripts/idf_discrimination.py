"""Is IDF ranking this corpus's query terms informatively, or noisily?

The coverage factor weights a query term by IDF, on the stated theory that
"matching a term that appears everywhere is not evidence, matching a rare one
is". That theory needs the corpus to *have* terms that appear everywhere. On 91
short PyPI pages every term in one failing query appears in ~1 document, so IDF
is ~flat and ranks the function word "cannot" above the content word "password".

This measures the thing directly: for each golden with an expected source, does
IDF put the query term that actually identifies the answer at the top?

A term is called *discriminating* here if it appears in the expected document
and in at most 20% of the corpus - derived from the corpus, not asserted.
"""
import json
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.text import tokenize

store = SqliteStore(".oodarag/external.db")
idf = store.idf_table()
docs = store.all_documents()
by_name = {d.uri.rsplit("/", 1)[-1]: d for d in docs}
n = len(docs)

# Document frequency of each stem, computed here rather than trusted.
df = {}
for d in docs:
    for t in set(tokenize(d.text, stem_words=True)):
        df[t] = df.get(t, 0) + 1

goldens = [json.loads(line) for line in open("evals/goldens-external.jsonl")
           if line.strip() and not line.lstrip().startswith("#")]
top_is_discriminating = 0
considered = 0
rows = []
for g in goldens:
    sources = g.get("expect_sources") or []
    if not sources:
        continue
    target = next((by_name[k] for k in by_name
                   if any(s in k for s in sources)), None)
    if target is None:
        continue
    target_terms = set(tokenize(target.text, stem_words=True))
    q_terms = [t for t in dict.fromkeys(tokenize(g["question"], stem_words=True))
               if t in idf]
    if not q_terms:
        continue
    discriminating = {t for t in q_terms
                      if t in target_terms and df.get(t, 0) <= 0.2 * n}
    if not discriminating:
        continue
    considered += 1
    ranked = sorted(q_terms, key=lambda t: -idf[t])
    hit = ranked[0] in discriminating
    top_is_discriminating += hit
    rows.append((hit, g["question"][:52], ranked[0], round(idf[ranked[0]], 2),
                 sorted(discriminating)[:3]))

print(f"corpus: {n} documents")
print(f"goldens with an expected source and >=1 discriminating query term: {considered}")
print(f"IDF's top-ranked query term IS discriminating: "
      f"{top_is_discriminating}/{considered} = {top_is_discriminating/considered:.1%}")
print(f"a coin flip over the query's terms would get roughly: "
      f"{sum(len(r[4]) for r in rows)/sum(1 for _ in rows):.2f} of ~5 terms")
print()
print("cases where IDF's top term is NOT the discriminating one:")
for hit, q, top, v, disc in rows:
    if not hit:
        print(f"  {q:54} top={top!r} ({v})  should favour {disc}")
