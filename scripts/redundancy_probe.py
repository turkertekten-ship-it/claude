"""Why is MMR worth a case on one corpus and a precision cost on the other?

ADR 0004 records the split and deliberately does not explain it, because the
`candidate_k` story that covered it was measured and turned out backwards for
MMR (L74). This measures the mechanism MMR's own docstring names instead of
inventing a second story:

    "a well-written document says the important thing in the introduction, the
     summary and the conclusion, and all three are excellent matches"

That is *within-document* redundancy, and it is directly observable. If it is
the mechanism, the primary corpus's candidate sets should be measurably more
redundant than the external corpus's - more chunks drawn from the same document,
and higher pairwise token overlap. If both corpora look equally diverse, the
docstring's account does not explain the split and something else does.

Measured on the pre-MMR ranking (use_mmr=False), over each corpus's own
goldens. This is the top 8 relevance alone returns - **not** MMR's choice set,
which is the full reranked candidate list of about 20. It is the list MMR would
be replacing, and so bounds what MMR can improve: if these 8 are already
diverse, any substitution gives up relevance for no diversity.

    PYTHONPATH=src python3 scripts/redundancy_probe.py
"""
import shutil, statistics, tempfile

from oodarag.eval.harness import load_goldens
from oodarag.ingest.filesystem import FilesystemConnector
from oodarag.pipeline import IndexPipeline
from oodarag.retrieve.hybrid import HybridRetriever, RetrievalConfig
from oodarag.retrieve.mmr import jaccard
from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.text import tokenize

CORPORA = [
    ("external", "corpus/external/pypi", ["**/*.md"], "evals/goldens-external.jsonl"),
    ("primary", ".", ["**/*.md", "src/**/*.py"], "evals/goldens.jsonl"),
]
TOP = 8


def main() -> None:
    for name, root, patterns, goldens in CORPORA:
        work = tempfile.mkdtemp(prefix=f"red-{name}-")
        try:
            store = SqliteStore(f"{work}/index.db")
            pipeline = IndexPipeline(store)
            pipeline.run([FilesystemConnector(root, patterns=patterns, key=f"fs:{name}")])
            retriever = HybridRetriever(store, pipeline.embedder,
                                        RetrievalConfig(use_mmr=False))
            overlaps, same_doc_shares, distinct_docs = [], [], []
            for case in load_goldens(goldens):
                results, _trace = retriever.retrieve(case.question, top_k=TOP)
                if len(results) < 2:
                    continue
                texts = [tokenize(r.chunk.indexed_text) for r in results]
                docs = [r.chunk.doc_id for r in results]
                pairs = [(i, j) for i in range(len(texts)) for j in range(i + 1, len(texts))]
                overlaps.append(statistics.mean(jaccard(texts[i], texts[j]) for i, j in pairs))
                same_doc_shares.append(
                    sum(1 for i, j in pairs if docs[i] == docs[j]) / len(pairs))
                distinct_docs.append(len(set(docs)) / len(docs))
            print(f"\n## {name}: {len(overlaps)} queries, top-{TOP} before MMR")
            print(f"  mean pairwise token overlap : {statistics.mean(overlaps):.4f}")
            print(f"  median                      : {statistics.median(overlaps):.4f}")
            print(f"  share of pairs same document: {statistics.mean(same_doc_shares):.4f}")
            print(f"  distinct documents / results: {statistics.mean(distinct_docs):.4f}")
            store.close()
        finally:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
