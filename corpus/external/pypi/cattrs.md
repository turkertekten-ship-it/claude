---
date: 2026-02-18T22:15:17+0000
source: https://pypi.org/project/cattrs/
---
# cattrs: Flexible Object Serialization and Validation

Because validation belongs to the edges.

[image: Documentation] [image: License: MIT] [image: PyPI] [image: Supported Python Versions] [image: Downloads] [image: Coverage]

---

cattrs is a Swiss Army knife for (un)structuring and validating data in Python.
In practice, that means it converts unstructured dictionaries into proper classes and back, while validating their contents.

## Example

cattrs works best with attrs classes, and dataclasses where simple (un-)structuring works out of the box, even for nested data, without polluting your data model with serialization details:

```
>>> from attrs import define
>>> from cattrs import structure, unstructure
>>> @define
... class C:
...     a: int
...     b: list[str]
>>> instance = structure({'a': 1, 'b': ['x', 'y']}, C)
>>> instance
C(a=1, b=['x', 'y'])
>>> unstructure(instance)
{'a': 1, 'b': ['x', 'y']}
```

Have a look at Why cattrs? for more examples!

## Features

### Recursive Unstructuring

- attrs classes and dataclasses are converted into dictionaries in a way similar to attrs.asdict(), or into tuples in a way similar to attrs.astuple().
- Enumeration instances are converted to their values.
- Other types are let through without conversion. This includes types such as integers, dictionaries, lists and instances of non-attrs classes.
- Custom converters for any type can be registered using register_unstructure_hook.

### Recursive Structuring

Converts unstructured data into structured data, recursively, according to your specification given as a type.
The following types are supported:

- typing.Optional[T] and its 3.10+ form, T | None.
- list[T], typing.List[T], typing.MutableSequence[T], typing.Sequence[T] convert to lists.
- tuple and typing.Tuple (both variants, tuple[T, ...] and tuple[X, Y, Z]).
- set[T], typing.MutableSet[T], and typing.Set[T] convert to sets.
- frozenset[T], and typing.FrozenSet[T] convert to frozensets.
- dict[K, V], typing.Dict[K, V], typing.MutableMapping[K, V], and typing.Mapping[K, V] convert to dictionaries.
- typing.TypedDict, both ordinary and generic.
- typing.NewType
- PEP 695 type aliases on 3.12+
- attrs classes with simple attributes and the usual __init__1.
- All attrs classes and dataclasses with the usual __init__, if their complex attributes have type metadata.
- Unions of supported attrs classes, given that all of the classes have a unique field.
- Unions of anything, if you provide a disambiguation function for it.
- Custom converters for any type can be registered using register_structure_hook.

### Batteries Included

cattrs comes with pre-configured converters for a number of serialization libraries, including JSON (standard library, orjson, UltraJSON), msgpack, cbor2, bson, PyYAML, tomlkit and msgspec (supports only JSON at this time).

For details, see the cattrs.preconf package.

## Design Decisions

cattrs is based on a few fundamental design decisions:

- Un/structuring rules are separate from the models.
This allows models to have a one-to-many relationship with un/structuring rules, and to create un/structuring rules for models which you do not own and you cannot change.
(cattrs can be configured to use un/structuring rules from models using the use_class_methods strategy.)
- Invent as little as possible; reuse existing ordinary Python instead.
For example, cattrs did not have a custom exception type to group exceptions until the sanctioned Python exceptiongroups.
A side-effect of this design decision is that, in a lot of cases, when you're solving cattrs problems you're actually learning Python instead of learning cattrs.
- Resist the temptation to guess.
If there are two ways of solving a problem, cattrs should refuse to guess and let the user configure it themselves.

A foolish consistency is the hobgoblin of little minds, so these decisions can and are sometimes broken, but they have proven to be a good foundation.

## Credits

Major credits to Hynek Schlawack for creating attrs and its predecessor, characteristic.

cattrs is tested with Hypothesis, by David R. MacIver.

cattrs is benchmarked using perf and pytest-benchmark.

This package was created with Cookiecutter and the audreyr/cookiecutter-pypackage project template.

1. Simple attributes are attributes that can be assigned unstructured data, like numbers, strings, and collections of unstructured data. ↩
