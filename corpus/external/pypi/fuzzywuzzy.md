---
date: 2020-02-13T21:06:25+0000
source: https://pypi.org/project/fuzzywuzzy/
---
[image: https://travis-ci.org/seatgeek/fuzzywuzzy.svg?branch=master]

## FuzzyWuzzy

Fuzzy string matching like a boss. It uses Levenshtein Distance to calculate the differences between sequences in a simple-to-use package.

## Requirements

- Python 2.7 or higher
- difflib
- python-Levenshtein (optional, provides a 4-10x speedup in String
Matching, though may result in differing results for certain cases)

### For testing

- pycodestyle
- hypothesis
- pytest

## Installation

Using PIP via PyPI

```
pip install fuzzywuzzy
```

or the following to install python-Levenshtein too

```
pip install fuzzywuzzy[speedup]
```

Using PIP via Github

```
pip install git+git://github.com/seatgeek/fuzzywuzzy.git@0.18.0#egg=fuzzywuzzy
```

Adding to your requirements.txt file (run pip install -r requirements.txt afterwards)

```
git+ssh://git@github.com/seatgeek/fuzzywuzzy.git@0.18.0#egg=fuzzywuzzy
```

Manually via GIT

```
git clone git://github.com/seatgeek/fuzzywuzzy.git fuzzywuzzy
cd fuzzywuzzy
python setup.py install
```

## Usage

```
>>> from fuzzywuzzy import fuzz
>>> from fuzzywuzzy import process
```

### Simple Ratio

```
>>> fuzz.ratio("this is a test", "this is a test!")
    97
```

### Partial Ratio

```
>>> fuzz.partial_ratio("this is a test", "this is a test!")
    100
```

### Token Sort Ratio

```
>>> fuzz.ratio("fuzzy wuzzy was a bear", "wuzzy fuzzy was a bear")
    91
>>> fuzz.token_sort_ratio("fuzzy wuzzy was a bear", "wuzzy fuzzy was a bear")
    100
```

### Token Set Ratio

```
>>> fuzz.token_sort_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear")
    84
>>> fuzz.token_set_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear")
    100
```

### Process

```
>>> choices = ["Atlanta Falcons", "New York Jets", "New York Giants", "Dallas Cowboys"]
>>> process.extract("new york jets", choices, limit=2)
    [('New York Jets', 100), ('New York Giants', 78)]
>>> process.extractOne("cowboys", choices)
    ("Dallas Cowboys", 90)
```

You can also pass additional parameters to extractOne method to make it use a specific scorer. A typical use case is to match file paths:

```
>>> process.extractOne("System of a down - Hypnotize - Heroin", songs)
    ('/music/library/good/System of a Down/2005 - Hypnotize/01 - Attack.mp3', 86)
>>> process.extractOne("System of a down - Hypnotize - Heroin", songs, scorer=fuzz.token_sort_ratio)
    ("/music/library/good/System of a Down/2005 - Hypnotize/10 - She's Like Heroin.mp3", 61)
```

## Known Ports

FuzzyWuzzy is being ported to other languages too! Here are a few ports we know about:

- Java: xpresso’s fuzzywuzzy implementation
- Java: fuzzywuzzy (java port)
- Rust: fuzzyrusty (Rust port)
- JavaScript: fuzzball.js (JavaScript port)
- C++: Tmplt/fuzzywuzzy
- C#: fuzzysharp (.Net port)
- Go: go-fuzzywuzz (Go port)
- Free Pascal: FuzzyWuzzy.pas (Free Pascal port)
- Kotlin multiplatform: FuzzyWuzzy-Kotlin
- R: fuzzywuzzyR (R port)
