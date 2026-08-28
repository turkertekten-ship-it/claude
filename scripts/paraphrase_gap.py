#!/usr/bin/env python3
"""Could a corpus-derived model bridge the questions retrieval still misses?

Six of the external set's remaining failures are paraphrase gaps: the question
says "clock" and the page says "freeze time", the question says "fakes HTTP
replies" and the page says "mock out the requests library". The standing answer
is a hosted embedder, which is blocked on a key - so this asks whether the
corpus itself carries the link, because if it does, a co-occurrence model built
from 349 pages would be a zero-dependency route to the same place.

For each missing query term it reports the terms it co-occurs with most by PMI,
and whether any of them appear in the page the question should have found.

    PYTHONPATH=src python3 scripts/paraphrase_gap.py

Answer, measured: no, and not narrowly (L80). Not one partner of any probed term
appears in its target page, and several point at the wrong package - "replies"
co-occurs with `pytest_httpx`, "fakes" with the cheesecake and lollipop of
faker's example data. The knowledge that "clock" and "freeze time" are the same
idea is general language knowledge, and it is not in a corpus of package pages.
"""

from __future__ import annotations

import collections
import math
import pathlib
import sys

from oodarag.store.sqlite_store import SqliteStore
from oodarag.util.stemming import stem
from oodarag.util.text import tokenize

#: (page that should have been retrieved, terms the question used that it lacks)
PROBES = {
    "freezegun": ["clock", "control"],
    "bidict": ["value", "looked"],
    "langdetect": ["guesses", "natural"],
    "responses": ["fakes", "replies"],
    "pluggy": ["packages", "library"],
    "testcontainers": ["thrown", "afterwards"],
}
CORPUS = pathlib.Path("corpus/external/pypi")
MIN_DF = 5
MIN_CO = 3


def main() -> int:
    store = SqliteStore(".oodarag/external.db")
    try:
        sets = [set(stem(t) for t in tokenize(c.indexed_text.lower()))
                for c in store.all_chunks()]
    finally:
        store.close()
    total = len(sets)
    df: collections.Counter[str] = collections.Counter()
    for chunk in sets:
        df.update(chunk)
    print(f"{total} chunks, {len(df)} stems\n")

    for name, terms in PROBES.items():
        page = {stem(t) for t in
                tokenize(CORPUS.joinpath(f"{name}.md").read_text("utf-8").lower())}
        for term in terms:
            key = stem(term)
            if not df[key]:
                print(f"{name:15} {term!r}: absent from the corpus")
                continue
            co: collections.Counter[str] = collections.Counter()
            for chunk in sets:
                if key in chunk:
                    co.update(chunk)
            scored = [
                (other, math.log((n / total) / ((df[key] / total) * (df[other] / total))))
                for other, n in co.items()
                if other != key and df[other] >= MIN_DF and n >= MIN_CO
            ]
            scored.sort(key=lambda pair: -pair[1])
            partners = [p for p, _ in scored[:8]]
            bridged = [p for p in partners if p in page]
            print(f"{name:15} {term!r:12} df={df[key]:>4}  partners={partners[:5]}")
            print(f"{'':15} {'':12} in the target page: {bridged or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
