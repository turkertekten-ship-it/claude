---
date: 2025-10-17T04:03:20+0000
source: https://pypi.org/project/toolz/
---
[image: Build Status] [image: Coverage Status] [image: Version Status]

A set of utility functions for iterators, functions, and dictionaries.

See the PyToolz documentation at https://toolz.readthedocs.io

## LICENSE

New BSD. See License File.

## Install

toolz is on the Python Package Index (PyPI):

```
pip install toolz
```

## Structure and Heritage

toolz is implemented in three parts:

itertoolz, for operations on iterables. Examples: groupby,
unique, interpose,

functoolz, for higher-order functions. Examples: memoize,
curry, compose,

dicttoolz, for operations on dictionaries. Examples: assoc,
update-in, merge.

These functions come from the legacy of functional languages for list
processing. They interoperate well to accomplish common complex tasks.

Read our API
Documentation for
more details.

## Example

This builds a standard wordcount function from pieces within toolz:

```
>>> def stem(word):
...     """ Stem word to primitive form """
...     return word.lower().rstrip(",.!:;'-\"").lstrip("'\"")

>>> from toolz import compose, frequencies
>>> from toolz.curried import map
>>> wordcount = compose(frequencies, map(stem), str.split)

>>> sentence = "This cat jumped over this other cat!"
>>> wordcount(sentence)
{'this': 2, 'cat': 2, 'jumped': 1, 'over': 1, 'other': 1}
```

## Dependencies

toolz supports Python 3.9+ with a common codebase.
It is pure Python and requires no dependencies beyond the standard
library.

It is, in short, a lightweight dependency.

## CyToolz

The toolz project has been reimplemented in Cython.
The cytoolz project is a drop-in replacement for the Pure Python
implementation.
See CyToolz GitHub Page for more
details.

## See Also

- Underscore.js: A similar library for
JavaScript
- Enumerable: A
similar library for Ruby
- Clojure: A functional language whose
standard library has several counterparts in toolz
- itertools: The
Python standard library for iterator tools
- functools: The
Python standard library for function tools

## Project Status

This project is alive but inactive.

The original maintainers have mostly moved on to other endeavors. We’re still
around for critical bug fixes, Python version bumps, and security issues and
will commit to keeping the project alive (it’s highly depended upon).
However, beyond that we don’t plan to spend much time reviewing contributions.
We view Toolz as mostly complete.

We encourage enthusiasts to innovate in new and wonderful places 🚀
