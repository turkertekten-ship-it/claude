---
date: 2026-07-18T17:42:28+0000
source: https://pypi.org/project/textblob/
---
[image: Latest version] [image: Build status]

Homepage: https://textblob.readthedocs.io/

TextBlob is a Python library for processing textual data. It provides a simple API for diving into common natural language processing (NLP) tasks such as part-of-speech tagging, noun phrase extraction, sentiment analysis, classification, and more.

```
from textblob import TextBlob

text = """
The titular threat of The Blob has always struck me as the ultimate movie
monster: an insatiably hungry, amoeba-like mass able to penetrate
virtually any safeguard, capable of--as a doomed doctor chillingly
describes it--"assimilating flesh on contact.
Snide comparisons to gelatin be damned, it's a concept with the most
devastating of potential consequences, not unlike the grey goo scenario
proposed by technological theorists fearful of
artificial intelligence run rampant.
"""

blob = TextBlob(text)
blob.tags  # [('The', 'DT'), ('titular', 'JJ'),
#  ('threat', 'NN'), ('of', 'IN'), ...]

blob.noun_phrases  # WordList(['titular threat', 'blob',
#            'ultimate movie monster',
#            'amoeba-like mass', ...])

for sentence in blob.sentences:
    print(sentence.sentiment.polarity)
# 0.060
# -0.341
```

TextBlob stands on the giant shoulders of NLTK and pattern, and plays nicely with both.

## Features

- Noun phrase extraction
- Part-of-speech tagging
- Sentiment analysis
- Classification (Naive Bayes, Decision Tree)
- Tokenization (splitting text into words and sentences)
- Word and phrase frequencies
- Parsing
- n-grams
- Word inflection (pluralization and singularization) and lemmatization
- Spelling correction
- Add new models or languages through extensions
- WordNet integration

## Get it now

```
$ pip install -U textblob
$ python -m textblob.download_corpora
```

## Examples

See more examples at the Quickstart guide.

## Documentation

Full documentation is available at https://textblob.readthedocs.io/.

## Project Links

- Docs: https://textblob.readthedocs.io/
- Changelog: https://textblob.readthedocs.io/en/latest/changelog.html
- PyPI: https://pypi.python.org/pypi/TextBlob
- Issues: https://github.com/sloria/TextBlob/issues

## License

MIT licensed. See the bundled LICENSE file for more details.
