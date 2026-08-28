# Boltons

boltons should be builtins.

Boltons is a set of over 230 BSD-licensed, pure-Python utilities
in the same spirit as — and yet conspicuously missing from —
the standard library, including:

- Atomic file saving, bolted on with fileutils
- A highly-optimized OrderedMultiDict, in dictutils
- Two types of PriorityQueue, in queueutils
- Chunked and windowed iteration, in iterutils
- Recursive data structure iteration and merging, with iterutils.remap
- Exponential backoff functionality, including jitter, through iterutils.backoff
- A full-featured TracebackInfo type, for representing stack traces,
in tbutils

Full and extensive docs are available on Read The Docs. See
what's new by checking the CHANGELOG.

Boltons is tested against Python 3.7-3.14, as well as PyPy3.

## Installation

Boltons can be added to a project in a few ways. There's the obvious one:

```
pip install boltons
```

On macOS, it can also be installed via MacPorts:

```
sudo port install py-boltons
```

Then, thanks to PyPI, dozens of boltons are just an import away:

```
from boltons.cacheutils import LRU
my_cache = LRU()
```

However, due to the nature of utilities, application developers might
want to consider other options, including vendorization of individual
modules into a project. Boltons is pure-Python and has no
dependencies. If the whole project is too big, each module is
independent, and can be copied directly into a project. See the
Integration section of the docs for more details.

## Third-party packages

The majority of boltons strive to be "good enough" for a wide range of
basic uses, leaving advanced use cases to Python's myriad specialized
3rd-party libraries. In many cases the respective boltons module
will describe 3rd-party alternatives worth investigating when use
cases outgrow boltons. If you've found a natural "next-step"
library worth mentioning, see the next section!

## Gaps

Found something missing in the standard library that should be in
boltons? Found something missing in boltons? First, take a
moment to read the very brief architecture statement
to make sure the functionality would be a good fit. It covers the
design philosophy, what belongs in boltons, and how modules are
organized.

Then, if you are very motivated, submit a Pull Request. Otherwise,
submit a short feature request on the Issues page, and we will
figure something out.

## Development

Install uv, then set up a dev environment:

```
uv venv && uv pip install -e .
```

Run the test suite (includes doctests):

```
uvx --with tox-uv tox -e py314
```

Run all environments in parallel:

```
uvx --with tox-uv tox -p auto
```
