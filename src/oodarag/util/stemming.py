"""The Porter stemming algorithm (Porter, 1980).

Implemented here rather than approximated with suffix-stripping heuristics for
one reason: **SQLite's FTS5 `porter` tokenizer runs this exact algorithm**, and
index-time and query-time analysis have to agree.

They disagreed, and it was expensive. The FTS index stemmed, so a query for
"abstain" correctly matched a passage saying "abstained" and BM25 ranked it
first. The reranker then matched raw tokens, computed the passage's coverage of
"abstain" as zero, and pushed the best lexical hit out of the results entirely.
Both halves were individually reasonable, and the combination made retrieval
measurably worse than no stemming at all - the eval caught it as a regression
with no failing component to point at.

The rule this encodes: any two stages that compare the same text must analyse it
the same way. Approximate agreement is not agreement.
"""

from __future__ import annotations

VOWELS = frozenset("aeiou")


def _is_consonant(word: str, index: int) -> bool:
    char = word[index]
    if char in VOWELS:
        return False
    if char == "y":
        # 'y' is a consonant unless preceded by one (toy -> consonant, by -> vowel)
        return index == 0 or not _is_consonant(word, index - 1)
    return True


def _measure(stem: str) -> int:
    """Porter's `m`: the number of vowel-consonant sequences in the stem."""
    count = 0
    previous_vowel = False
    for index in range(len(stem)):
        vowel = not _is_consonant(stem, index)
        if previous_vowel and not vowel:
            count += 1
        previous_vowel = vowel
    return count


def _contains_vowel(stem: str) -> bool:
    return any(not _is_consonant(stem, i) for i in range(len(stem)))


def _ends_double_consonant(word: str) -> bool:
    return (len(word) >= 2 and word[-1] == word[-2]
            and _is_consonant(word, len(word) - 1))


def _cvc(word: str) -> bool:
    """consonant-vowel-consonant where the final consonant is not w, x or y."""
    if len(word) < 3:
        return False
    if not (_is_consonant(word, len(word) - 3)
            and not _is_consonant(word, len(word) - 2)
            and _is_consonant(word, len(word) - 1)):
        return False
    return word[-1] not in "wxy"


def _replace(word: str, suffix: str, replacement: str, min_measure: int = -1) -> str | None:
    if not word.endswith(suffix):
        return None
    stem = word[: len(word) - len(suffix)] if suffix else word
    if min_measure >= 0 and _measure(stem) <= min_measure:
        return None
    return stem + replacement


_STEP2 = [
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"), ("anci", "ance"),
    ("izer", "ize"), ("abli", "able"), ("alli", "al"), ("entli", "ent"),
    ("eli", "e"), ("ousli", "ous"), ("ization", "ize"), ("ation", "ate"),
    ("ator", "ate"), ("alism", "al"), ("iveness", "ive"), ("fulness", "ful"),
    ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"),
]
_STEP3 = [
    ("icate", "ic"), ("ative", ""), ("alize", "al"), ("iciti", "ic"),
    ("ical", "ic"), ("ful", ""), ("ness", ""),
]
_STEP4 = [
    "al", "ance", "ence", "er", "ic", "able", "ible", "ant", "ement", "ment",
    "ent", "ou", "ism", "ate", "iti", "ous", "ive", "ize",
]


def stem(word: str) -> str:
    """Reduce an English word to its Porter stem. Short words are returned as-is."""
    word = word.lower()
    if len(word) <= 2 or not word.isalpha():
        return word

    # Step 1a - plurals
    for suffix, replacement in (("sses", "ss"), ("ies", "i"), ("ss", "ss"), ("s", "")):
        if word.endswith(suffix):
            word = word[: len(word) - len(suffix)] + replacement
            break

    # Step 1b - past tense and gerunds
    if word.endswith("eed"):
        if _measure(word[:-3]) > 0:
            word = word[:-1]
    else:
        changed = False
        for suffix in ("ed", "ing"):
            if word.endswith(suffix) and _contains_vowel(word[: -len(suffix)]):
                word = word[: -len(suffix)]
                changed = True
                break
        if changed:
            if word.endswith(("at", "bl", "iz")):
                word += "e"
            elif _ends_double_consonant(word) and not word.endswith(("l", "s", "z")):
                word = word[:-1]
            elif _measure(word) == 1 and _cvc(word):
                word += "e"

    # Step 1c - terminal y
    if word.endswith("y") and _contains_vowel(word[:-1]):
        word = word[:-1] + "i"

    # Steps 2 and 3 - derivational suffixes
    for suffix, replacement in _STEP2:
        if (result := _replace(word, suffix, replacement, 0)) is not None:
            word = result
            break
    for suffix, replacement in _STEP3:
        if (result := _replace(word, suffix, replacement, 0)) is not None:
            word = result
            break

    # Step 4 - remove the suffix entirely when the stem is substantial
    for suffix in _STEP4:
        if word.endswith(suffix):
            stem_candidate = word[: -len(suffix)]
            if _measure(stem_candidate) > 1:
                if suffix in ("ion",) and not stem_candidate.endswith(("s", "t")):
                    continue
                word = stem_candidate
            break
    if word.endswith("ion") and _measure(word[:-3]) > 1 and word[-4:-3] in ("s", "t"):
        word = word[:-3]

    # Step 5 - tidy up
    if word.endswith("e"):
        measure = _measure(word[:-1])
        if measure > 1 or (measure == 1 and not _cvc(word[:-1])):
            word = word[:-1]
    if word.endswith("ll") and _measure(word) > 1:
        word = word[:-1]
    return word


def stem_all(tokens: list[str]) -> list[str]:
    return [stem(t) for t in tokens]
