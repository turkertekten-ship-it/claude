---
date: 2026-08-01T21:20:38+0000
source: https://pypi.org/project/cachetools/
---
[image: Latest PyPI version] [image: CI build status] [image: Documentation build status] [image: Test coverage] [image: License]

This module provides various memoizing collections and decorators,
including variants of the Python Standard Library’s @lru_cache
function decorator.

```
from cachetools import cached, LRUCache, TTLCache

# speed up calculating Fibonacci numbers with dynamic programming
@cached(cache={})
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)

# cache least recently used Python Enhancement Proposals
@cached(cache=LRUCache(maxsize=32))
def get_pep(num):
    url = 'http://www.python.org/dev/peps/pep-%04d/' % num
    with urllib.request.urlopen(url) as s:
        return s.read()

# cache weather data for no longer than ten minutes
@cached(cache=TTLCache(maxsize=1024, ttl=600))
def get_weather(place):
    return owm.weather_at_place(place).get_weather()
```

For the purpose of this module, a cache is a mutable mapping of a
fixed maximum size. When the cache is full, i.e. by adding another
item the cache would exceed its maximum size, the cache must choose
which item(s) to discard based on a suitable cache algorithm.

This module provides multiple cache classes based on different cache
algorithms, as well as decorators for easily memoizing function and
method calls.

## Installation

cachetools is available from PyPI and can be installed by running:

```
pip install cachetools
```

## Project Resources

- Documentation
- Issue tracker
- Source code
- Change log

## Related Projects

- asyncache: Helpers to use cachetools with asyncio.
- cachetools-async: Helpers to use cachetools with asyncio.
- cacheing: Pure Python Cacheing Library.
- CacheToolsUtils: Stackable cache classes for sharing, encryption,
statistics and more on top of cachetools, redis and memcached.
- shelved-cache: Persistent cache implementation for Python
cachetools.

## License

Copyright (c) 2014-2026 Thomas Kemmer.

Licensed under the MIT License.
