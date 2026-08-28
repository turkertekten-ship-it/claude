#!/usr/bin/env python3
"""How does the abstention gate's signal scale with corpus size?

Written to test a mechanism that turned out to be wrong. L72 explained a floor
correction by claiming the two arms overlap less as the corpus grows, so the
gate's `relevance x agreement` product falls with N. Measured over four
subsampled corpora, agreement does fall - and relevance rises by more, and the
product is flat (L73). There is no scaling law to normalise away.

Populations are split by whether a question's target document survived the
subsample, because shrinking a corpus removes the documents goldens point at
(L28): mixed together, these rows would measure which targets survived rather
than corpus size.

    PYTHONPATH=src python3 scripts/agreement_scaling.py

The row worth reading is the last column at N=90, where answerable and
unanswerable questions have identical agreement. This gate feature had no signal
at all on a corpus that size; it is worth 0.250 of separation at 349.
"""
import shutil, statistics, sys, tempfile, pathlib
sys.path.insert(0, "scripts")
from _corpora import EXTERNAL
from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.store.sqlite_store import SqliteStore

root, patterns, goldens_path = EXTERNAL
pages = sorted(pathlib.Path(root).glob("*.md"))
goldens = load_goldens(goldens_path)
K = 8
print(f"{'N':>5} {'population':<18} {'n':>3} {'agree':>10} {'relevance':>10} "
      f"{'product':>10} {'p10 prod':>10}")
for target in (90, 175, 260, len(pages)):
    step = len(pages) / target
    keep = [pages[int(i * step)] for i in range(target)]
    work = tempfile.mkdtemp()
    staging = pathlib.Path(work) / "corpus"; staging.mkdir()
    for p in keep:
        shutil.copy(p, staging / p.name)
    store = SqliteStore(f"{work}/i.db")
    pl = IndexPipeline(store)
    pl.run([FilesystemConnector(str(staging), patterns=patterns, key="fs:sub")])
    n = store.stats()["documents"]
    r = HybridRetriever(store, pl.embedder, RetrievalConfig())
    names = {p.name for p in keep}
    present, absent = [], []
    for g in goldens:
        hits, _ = r.retrieve(g.question, top_k=K)
        if not hits:
            continue
        agree = sum(1 for h in hits if "dense_rank" in h.components
                    and "lexical_rank" in h.components) / len(hits)
        has_target = bool(g.expect_sources) and any(
            any(e.lower() in nm.lower() for e in g.expect_sources) for nm in names)
        rel = max((h.components.get("rerank_relevance", 0.0) for h in hits), default=0.0)
        (present if has_target else absent).append((agree, rel, agree * rel))
    chance = K / n
    for label, vals in (("target present", present), ("no target / negative", absent)):
        if vals:
            ag = statistics.median(v[0] for v in vals)
            rel = statistics.median(v[1] for v in vals)
            prod = statistics.median(v[2] for v in vals)
            low = sorted(v[2] for v in vals)[max(0, len(vals) // 10)]
            print(f"{n:>5} {label:<18} {len(vals):>3} {ag:>10.3f} {rel:>10.3f} "
                  f"{prod:>10.3f} {low:>10.3f}")
    store.close(); shutil.rmtree(work, ignore_errors=True)
