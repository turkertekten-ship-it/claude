---
date: 2016-07-03T20:05:40+0000
source: https://pypi.org/project/polyglot/
---
[image: Downloads] [image: Latest Version] [image: Build Status] [image: Documentation Status]

Polyglot is a natural language pipeline that supports massive
multilingual applications.

- Free software: GPLv3 license
- Documentation: http://polyglot.readthedocs.org.
- GitHub: https://github.com/aboSamoor/polyglot

## Features

- Tokenization (165 Languages)
- Language detection (196 Languages)
- Named Entity Recognition (40 Languages)
- Part of Speech Tagging (16 Languages)
- Sentiment Analysis (136 Languages)
- Word Embeddings (137 Languages)
- Morphological analysis (135 Languages)
- Transliteration (69 Languages)

## Developer

- Rami Al-Rfou @ rmyeid gmail com

### Quick Tutorial

```
import polyglot
from polyglot.text import Text, Word
```

## Language Detection

```
text = Text("Bonjour, Mesdames.")
print("Language Detected: Code={}, Name={}\n".format(text.language.code, text.language.name))
```

```
Language Detected: Code=fr, Name=French
```

## Tokenization

```
zen = Text("Beautiful is better than ugly. "
           "Explicit is better than implicit. "
           "Simple is better than complex.")
print(zen.words)
```

```
[u'Beautiful', u'is', u'better', u'than', u'ugly', u'.', u'Explicit', u'is', u'better', u'than', u'implicit', u'.', u'Simple', u'is', u'better', u'than', u'complex', u'.']
```

```
print(zen.sentences)
```

```
[Sentence("Beautiful is better than ugly."), Sentence("Explicit is better than implicit."), Sentence("Simple is better than complex.")]
```

## Part of Speech Tagging

```
text = Text(u"O primeiro uso de desobediência civil em massa ocorreu em setembro de 1906.")

print("{:<16}{}".format("Word", "POS Tag")+"\n"+"-"*30)
for word, tag in text.pos_tags:
    print(u"{:<16}{:>2}".format(word, tag))
```

```
Word            POS Tag
------------------------------
O               DET
primeiro        ADJ
uso             NOUN
de              ADP
desobediência   NOUN
civil           ADJ
em              ADP
massa           NOUN
ocorreu         ADJ
em              ADP
setembro        NOUN
de              ADP
1906            NUM
.               PUNCT
```

## Named Entity Recognition

```
text = Text(u"In Großbritannien war Gandhi mit dem westlichen Lebensstil vertraut geworden")
print(text.entities)
```

```
[I-LOC([u'Gro\xdfbritannien']), I-PER([u'Gandhi'])]
```

## Polarity

```
print("{:<16}{}".format("Word", "Polarity")+"\n"+"-"*30)
for w in zen.words[:6]:
    print("{:<16}{:>2}".format(w, w.polarity))
```

```
Word            Polarity
------------------------------
Beautiful        0
is               0
better           1
than             0
ugly            -1
.                0
```

## Embeddings

```
word = Word("Obama", language="en")
print("Neighbors (Synonms) of {}".format(word)+"\n"+"-"*30)
for w in word.neighbors:
    print("{:<16}".format(w))
print("\n\nThe first 10 dimensions out the {} dimensions\n".format(word.vector.shape[0]))
print(word.vector[:10])
```

```
Neighbors (Synonms) of Obama
------------------------------
Bush
Reagan
Clinton
Ahmadinejad
Nixon
Karzai
McCain
Biden
Huckabee
Lula

The first 10 dimensions out the 256 dimensions

[-2.57382345  1.52175975  0.51070285  1.08678675 -0.74386948 -1.18616164
  2.92784619 -0.25694436 -1.40958667 -2.39675403]
```

## Morphology

```
word = Text("Preprocessing is an essential step.").words[0]
print(word.morphemes)
```

```
[u'Pre', u'process', u'ing']
```

## Transliteration

```
from polyglot.transliteration import Transliterator
transliterator = Transliterator(source_lang="en", target_lang="ru")
print(transliterator.transliterate(u"preprocessing"))
```

```
препрокессинг
```

### History

### “14.11” (2014-01-11)

- First release on PyPI.

### “15.5.2” (2015-05-02)

- Polyglot is feature complete.

### “15.10.03” (2015-10-03)

- Change the polyglot models mirror to Stony Brook University DSL lab instead
of Google cloud storage.

### “16.07.04” (2016-07-03)

- New Features:
- Support Transfer POS Tagging.
- Support supplying hint_language_code for Text.
- Bug Fix:
- Improve sentence serialization (PR #34)
- Fix rare unicode encode error (PR #35)
- Fix transliteration from languages other than English (PR 46)
- Add link to Github in README (PR #49)
- Make handling of paths more coherent (RP #55)
- Fix normalizing embedding in place for NER corrupts the features of POS (issue #60, PR #62)
