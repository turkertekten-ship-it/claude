---
date: 2026-04-07T11:13:37+0000
source: https://pypi.org/project/rapidfuzz/
---
# [image: RapidFuzz]

#### Rapid fuzzy string matching in Python and C++ using the Levenshtein Distance

[image: Continuous Integration] [image: PyPI package version] [image: Conda Version] [image: Python versions]
 [image: Documentation] [image: Code Coverage] [image: GitHub license]

Description •
 Installation •
 Usage •
 License

---

## Description

RapidFuzz is a fast string matching library for Python and C++, which is using the string similarity calculations from FuzzyWuzzy. However there are a couple of aspects that set RapidFuzz apart from FuzzyWuzzy:

1. It is MIT licensed so it can be used with whichever License you might want to choose for your project, while you're forced to adopt the GPL license when using FuzzyWuzzy
1. It provides many string_metrics like hamming or jaro_winkler, which are not included in FuzzyWuzzy
1. It is mostly written in C++ and on top of this comes with a lot of Algorithmic improvements to make string matching even faster, while still providing the same results. For detailed benchmarks check the documentation
1. Fixes multiple bugs in the partial_ratio implementation
1. It can be largely used as a drop in replacement for fuzzywuzzy. However there are a couple API differences described here

## Requirements

- Python 3.10 or later
- On Windows the Visual C++ 2019 redistributable is required

## Installation

There are several ways to install RapidFuzz, the recommended methods
are to either use pip(the Python package manager) or
conda (an open-source, cross-platform, package manager)

### with pip

RapidFuzz can be installed with pip the following way:

```
pip install rapidfuzz
```

There are pre-built binaries (wheels) of RapidFuzz for MacOS (10.9 and later), Linux x86_64 and Windows. Wheels for armv6l (Raspberry Pi Zero) and armv7l (Raspberry Pi) are available on piwheels.

> :heavy_multiplication_x: failure "ImportError: DLL load failed" If you run into this error on Windows the reason is most likely, that the Visual C++ 2019 redistributable is not installed, which is required to find C++ Libraries (The C++ 2019 version includes the 2015, 2017 and 2019 version).

### with conda

RapidFuzz can be installed with conda:

```
conda install -c conda-forge rapidfuzz
```

### from git

RapidFuzz can be installed directly from the source distribution by cloning the repository. This requires a C++17 capable compiler.

```
git clone --recursive https://github.com/rapidfuzz/rapidfuzz.git
cd rapidfuzz
pip install .
```

## Usage

Some simple functions are shown below. A complete documentation of all functions can be found here.

Note that from RapidFuzz 3.0.0, strings are not preprocessed(removing all non alphanumeric characters, trimming whitespaces, converting all characters to lower case) by default. Which means that when comparing two strings that have the same characters but different cases("this is a word", "THIS IS A WORD") their similarity score value might be different, so when comparing such strings you might see a difference in score value compared to previous versions. Some examples of string matching with preprocessing can be found here.

### Scorers

Scorers in RapidFuzz can be found in the modules fuzz and distance.

#### Simple Ratio

```
> from rapidfuzz import fuzz
> fuzz.ratio("this is a test", "this is a test!")
96.55172413793103
```

#### Partial Ratio

```
> from rapidfuzz import fuzz
> fuzz.partial_ratio("this is a test", "this is a test!")
100.0
```

#### Token Sort Ratio

```
> from rapidfuzz import fuzz
> fuzz.ratio("fuzzy wuzzy was a bear", "wuzzy fuzzy was a bear")
90.9090909090909
> fuzz.token_sort_ratio("fuzzy wuzzy was a bear", "wuzzy fuzzy was a bear")
100.0
```

#### Token Set Ratio

```
> from rapidfuzz import fuzz
> fuzz.token_sort_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear")
84.21052631578947
> fuzz.token_set_ratio("fuzzy was a bear", "fuzzy fuzzy was a bear")
100.0
# Returns 100.0 if one string is a subset of the other, regardless of extra content in the longer string
> fuzz.token_set_ratio("fuzzy was a bear but not a dog", "fuzzy was a bear")
100.0
# Score is reduced only when there is explicit disagreement in the two strings
> fuzz.token_set_ratio("fuzzy was a bear but not a dog", "fuzzy was a bear but not a cat")
92.3076923076923
```

#### Weighted Ratio

```
> from rapidfuzz import fuzz
> fuzz.WRatio("this is a test", "this is a new test!!!")
85.5

> from rapidfuzz import fuzz, utils
> # Removing non alpha numeric characters("!") from the string
> fuzz.WRatio("this is a test", "this is a new test!!!", processor=utils.default_process) # here "this is a new test!!!" is converted to "this is a new test"
95.0
> fuzz.WRatio("this is a test", "this is a new test")
95.0

> # Converting string to lower case
> fuzz.WRatio("this is a word", "THIS IS A WORD")
21.42857142857143
> fuzz.WRatio("this is a word", "THIS IS A WORD", processor=utils.default_process) # here "THIS IS A WORD" is converted to "this is a word"
100.0
```

#### Quick Ratio

```
> from rapidfuzz import fuzz
> fuzz.QRatio("this is a test", "this is a new test!!!")
80.0

> from rapidfuzz import fuzz, utils
> # Removing non alpha numeric characters("!") from the string
> fuzz.QRatio("this is a test", "this is a new test!!!", processor=utils.default_process)
87.5
> fuzz.QRatio("this is a test", "this is a new test")
87.5

> # Converting string to lower case
> fuzz.QRatio("this is a word", "THIS IS A WORD")
21.42857142857143
> fuzz.QRatio("this is a word", "THIS IS A WORD", processor=utils.default_process)
100.0
```

### Process

The process module makes it compare strings to lists of strings. This is generally more
performant than using the scorers directly from Python.
Here are some examples on the usage of processors in RapidFuzz:

```
> from rapidfuzz import process, fuzz
> choices = ["Atlanta Falcons", "New York Jets", "New York Giants", "Dallas Cowboys"]
> process.extract("new york jets", choices, scorer=fuzz.WRatio, limit=2)
[('New York Jets', 76.92307692307692, 1), ('New York Giants', 64.28571428571428, 2)]
> process.extractOne("cowboys", choices, scorer=fuzz.WRatio)
('Dallas Cowboys', 83.07692307692308, 3)

> # With preprocessing
> from rapidfuzz import process, fuzz, utils
> process.extract("new york jets", choices, scorer=fuzz.WRatio, limit=2, processor=utils.default_process)
[('New York Jets', 100.0, 1), ('New York Giants', 78.57142857142857, 2)]
> process.extractOne("cowboys", choices, scorer=fuzz.WRatio, processor=utils.default_process)
('Dallas Cowboys', 90.0, 3)
```

The full documentation of processors can be found here

## Benchmark

The following benchmark gives a quick performance comparison between RapidFuzz and FuzzyWuzzy.
More detailed benchmarks for the string metrics can be found in the documentation. For this simple comparison I generated a list of 10.000 strings with length 10, that is compared to a sample of 100 elements from this list:

```
words = [
    "".join(random.choice(string.ascii_letters + string.digits) for _ in range(10))
    for _ in range(10_000)
]
samples = words[:: len(words) // 100]
```

The first benchmark compares the performance of the scorers in FuzzyWuzzy and RapidFuzz when they are used directly
from Python in the following way:

```
for sample in samples:
    for word in words:
        scorer(sample, word)
```

The following graph shows how many elements are processed per second with each of the scorers. There are big performance differences between the different scorers. However each of the scorers is faster in RapidFuzz

 [image: Benchmark Scorer]

The second benchmark compares the performance when the scorers are used in combination with cdist in the following
way:

```
cdist(samples, words, scorer=scorer)
```

The following graph shows how many elements are processed per second with each of the scorers. In RapidFuzz the usage of scorers through processors like cdist is a lot faster than directly using it. That's why they should be used whenever possible.

 [image: Benchmark cdist]

## Support the project

If you are using RapidFuzz for your work and feel like giving a bit of your own benefit back to support the project, consider sending us money through GitHub Sponsors or PayPal that we can use to buy us free time for the maintenance of this great library, to fix bugs in the software, review and integrate code contributions, to improve its features and documentation, or to just take a deep breath and have a cup of tea every once in a while. Thank you for your support.

Support the project through GitHub Sponsors or via PayPal:

.

## License

RapidFuzz is licensed under the MIT license since I believe that everyone should be able to use it without being forced to adopt the GPL license. That's why the library is based on an older version of fuzzywuzzy that was MIT licensed as well.
This old version of fuzzywuzzy can be found here.
