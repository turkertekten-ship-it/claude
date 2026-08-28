Sorted Containers is an Apache2 licensed sorted collections library,
written in pure-Python, and fast as C-extensions.

Python’s standard library is great until you need a sorted collections
type. Many will attest that you can get really far without one, but the moment
you really need a sorted list, sorted dict, or sorted set, you’re faced
with a dozen different implementations, most using C-extensions without great
documentation and benchmarking.

In Python, we can do better. And we can do it in pure-Python!

```
>>> from sortedcontainers import SortedList
>>> sl = SortedList(['e', 'a', 'c', 'd', 'b'])
>>> sl
SortedList(['a', 'b', 'c', 'd', 'e'])
>>> sl *= 10_000_000
>>> sl.count('c')
10000000
>>> sl[-3:]
['e', 'e', 'e']
>>> from sortedcontainers import SortedDict
>>> sd = SortedDict({'c': 3, 'a': 1, 'b': 2})
>>> sd
SortedDict({'a': 1, 'b': 2, 'c': 3})
>>> sd.popitem(index=-1)
('c', 3)
>>> from sortedcontainers import SortedSet
>>> ss = SortedSet('abracadabra')
>>> ss
SortedSet(['a', 'b', 'c', 'd', 'r'])
>>> ss.bisect_left('c')
2
```

All of the operations shown above run in faster than linear time. The above
demo also takes nearly a gigabyte of memory to run. When the sorted list is
multiplied by ten million, it stores ten million references to each of “a”
through “e”. Each reference requires eight bytes in the sorted
container. That’s pretty hard to beat as it’s the cost of a pointer to each
object. It’s also 66% less overhead than a typical binary tree implementation
(e.g. Red-Black Tree, AVL-Tree, AA-Tree, Splay-Tree, Treap, etc.) for which
every node must also store two pointers to children nodes.

Sorted Containers takes all of the work out of Python sorted collections -
making your deployment and use of Python easy. There’s no need to install a C
compiler or pre-build and distribute custom extensions. Performance is a
feature and testing has 100% coverage with unit tests and hours of stress.

## Testimonials

Alex Martelli, Fellow of the Python Software Foundation

“Good stuff! … I like the simple, effective implementation idea of
splitting the sorted containers into smaller “fragments” to avoid the O(N)
insertion costs.”

Jeff Knupp, author of Writing Idiomatic Python and Python Trainer

“That last part, “fast as C-extensions,” was difficult to believe. I would need
some sort of Performance Comparison to be convinced this is true. The author
includes this in the docs. It is.”

Kevin Samuel, Python and Django Trainer

I’m quite amazed, not just by the code quality (it’s incredibly readable and
has more comment than code, wow), but the actual amount of work you put at
stuff that is not code: documentation, benchmarking, implementation
explanations. Even the git log is clean and the unit tests run out of the box
on Python 2 and 3.

Mark Summerfield, a short plea for Python Sorted Collections

Python’s “batteries included” standard library seems to have a battery
missing. And the argument that “we never had it before” has worn thin. It is
time that Python offered a full range of collection classes out of the box,
including sorted ones.

Sorted Containers is used in popular open source projects such as:
Zipline, an algorithmic trading library from Quantopian; Angr, a binary
analysis platform from UC Santa Barbara; Trio, an async I/O library; and
Dask Distributed, a distributed computation library supported by Continuum
Analytics.

## Features

- Pure-Python
- Fully documented
- Benchmark comparison (alternatives, runtimes, load-factors)
- 100% test coverage
- Hours of stress testing
- Performance matters (often faster than C implementations)
- Compatible API (nearly identical to older blist and bintrees modules)
- Feature-rich (e.g. get the five largest keys in a sorted dict: d.keys()[-5:])
- Pragmatic design (e.g. SortedSet is a Python set with a SortedList index)
- Developed on Python 3.7
- Tested on CPython 2.7, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7 and PyPy, PyPy3
 [image: https://api.travis-ci.org/grantjenks/python-sortedcontainers.svg?branch=master] [image: https://ci.appveyor.com/api/projects/status/github/grantjenks/python-sortedcontainers?branch=master&svg=true]

## Quickstart

Installing Sorted Containers is simple with pip:

```
$ pip install sortedcontainers
```

You can access documentation in the interpreter with Python’s built-in help
function. The help works on modules, classes and methods in Sorted
Containers.

```
>>> import sortedcontainers
>>> help(sortedcontainers)
>>> from sortedcontainers import SortedDict
>>> help(SortedDict)
>>> help(SortedDict.popitem)
```

## Documentation

Complete documentation for Sorted Containers is available at
http://www.grantjenks.com/docs/sortedcontainers/

### User Guide

The user guide provides an introduction to Sorted Containers and extensive
performance comparisons and analysis.

- Introduction
- Performance Comparison
- Load Factor Performance Comparison
- Runtime Performance Comparison
- Simulated Workload Performance Comparison
- Performance at Scale

### Community Guide

The community guide provides information on the development of Sorted
Containers along with support, implementation, and history details.

- Development and Support
- Implementation Details
- Release History

### API Documentation

The API documentation provides information on specific functions, classes, and
modules in the Sorted Containers package.

- Sorted List
- Sorted Dict
- Sorted Set

## Talks

- Python Sorted Collections | PyCon 2016 Talk
- SF Python Holiday Party 2015 Lightning Talk
- DjangoCon 2015 Lightning Talk

## Resources

- Sorted Containers Documentation
- Sorted Containers at PyPI
- Sorted Containers at Github
- Sorted Containers Issue Tracker

## Sorted Containers License

Copyright 2014-2019 Grant Jenks

Licensed under the Apache License, Version 2.0 (the “License”);
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an “AS IS” BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
