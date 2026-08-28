---
date: 2024-10-10T00:53:56+0000
source: https://pypi.org/project/immutables/
---
[image: https://github.com/MagicStack/immutables/workflows/Tests/badge.svg?branch=master] [image: https://img.shields.io/pypi/v/immutables.svg]

An immutable mapping type for Python.

The underlying datastructure is a Hash Array Mapped Trie (HAMT)
used in Clojure, Scala, Haskell, and other functional languages.
This implementation is used in CPython 3.7 in the contextvars
module (see PEP 550 and
PEP 567 for more details).

Immutable mappings based on HAMT have O(log N) performance for both
set() and get() operations, which is essentially O(1) for
relatively small mappings.

Below is a visualization of a simple get/set benchmark comparing
HAMT to an immutable mapping implemented with a Python dict
copy-on-write approach (the benchmark code is available
here):

 [image: bench.png]

## Installation

immutables requires Python 3.6+ and is available on PyPI:

```
$ pip install immutables
```

## API

immutables.Map is an unordered immutable mapping. Map objects
are hashable, comparable, and pickleable.

The Map object implements the collections.abc.Mapping ABC
so working with it is very similar to working with Python dicts:

```
import immutables

map = immutables.Map(a=1, b=2)

print(map['a'])
# will print '1'

print(map.get('z', 100))
# will print '100'

print('z' in map)
# will print 'False'
```

Since Maps are immutable, there is a special API for mutations that
allow apply changes to the Map object and create new (derived) Maps:

```
map2 = map.set('a', 10)
print(map, map2)
# will print:
#   <immutables.Map({'a': 1, 'b': 2})>
#   <immutables.Map({'a': 10, 'b': 2})>

map3 = map2.delete('b')
print(map, map2, map3)
# will print:
#   <immutables.Map({'a': 1, 'b': 2})>
#   <immutables.Map({'a': 10, 'b': 2})>
#   <immutables.Map({'a': 10})>
```

Maps also implement APIs for bulk updates: MapMutation objects:

```
map_mutation = map.mutate()
map_mutation['a'] = 100
del map_mutation['b']
map_mutation.set('y', 'y')

map2 = map_mutation.finish()

print(map, map2)
# will print:
#   <immutables.Map({'a': 1, 'b': 2})>
#   <immutables.Map({'a': 100, 'y': 'y'})>
```

MapMutation objects are context managers. Here’s the above example
rewritten in a more idiomatic way:

```
with map.mutate() as mm:
    mm['a'] = 100
    del mm['b']
    mm.set('y', 'y')
    map2 = mm.finish()

print(map, map2)
# will print:
#   <immutables.Map({'a': 1, 'b': 2})>
#   <immutables.Map({'a': 100, 'y': 'y'})>
```

## Further development

- An immutable version of Python set type with efficient
add() and discard() operations.

## License

Apache 2.0
