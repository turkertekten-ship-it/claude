---
date: 2026-03-19T14:22:23+0000
source: https://pypi.org/project/attrs/
---
[image: attrs]

attrs is the Python package that will bring back the joy of writing classes by relieving you from the drudgery of implementing object protocols (aka dunder methods).
Trusted by NASA for Mars missions since 2020!

Its main goal is to help you to write concise and correct software without slowing down your code.

## Sponsors

attrs would not be possible without our amazing sponsors.
Especially those generously supporting us at the The Organization tier and higher:

Please consider joining them to help make attrs’s maintenance more sustainable!

## Example

attrs gives you a class decorator and a way to declaratively define the attributes on that class:

```
>>> from attrs import asdict, define, make_class, Factory

>>> @define
... class SomeClass:
...     a_number: int = 42
...     list_of_numbers: list[int] = Factory(list)
...
...     def hard_math(self, another_number):
...         return self.a_number + sum(self.list_of_numbers) * another_number

>>> sc = SomeClass(1, [1, 2, 3])
>>> sc
SomeClass(a_number=1, list_of_numbers=[1, 2, 3])

>>> sc.hard_math(3)
19
>>> sc == SomeClass(1, [1, 2, 3])
True
>>> sc != SomeClass(2, [3, 2, 1])
True

>>> asdict(sc)
{'a_number': 1, 'list_of_numbers': [1, 2, 3]}

>>> SomeClass()
SomeClass(a_number=42, list_of_numbers=[])

>>> C = make_class("C", ["a", "b"])
>>> C("foo", "bar")
C(a='foo', b='bar')
```

After declaring your attributes, attrs gives you:

- a concise and explicit overview of the class's attributes,
- a nice human-readable __repr__,
- equality-checking methods,
- an initializer,
- and much more,

without writing dull boilerplate code again and again and without runtime performance penalties.

---

This example uses attrs's modern APIs that have been introduced in version 20.1.0, and the attrs package import name that has been added in version 21.3.0.
The classic APIs (@attr.s, attr.ib, plus their serious-business aliases) and the attr package import name will remain indefinitely.

Check out On The Core API Names for an in-depth explanation!

### Hate Type Annotations!?

No problem!
Types are entirely optional with attrs.
Simply assign attrs.field() to the attributes instead of annotating them with types:

```
from attrs import define, field

@define
class SomeClass:
    a_number = field(default=42)
    list_of_numbers = field(factory=list)
```

## Data Classes

On the tin, attrs might remind you of dataclasses (and indeed, dataclasses are a descendant of attrs).
In practice it does a lot more and is more flexible.
For instance, it allows you to define special handling of NumPy arrays for equality checks, allows more ways to plug into the initialization process, has a replacement for __init_subclass__, and allows for stepping through the generated methods using a debugger.

For more details, please refer to our comparison page, but generally speaking, we are more likely to commit crimes against nature to make things work that one would expect to work, but that are quite complicated in practice.

## Project Information

- Changelog
- Documentation
- PyPI
- Source Code
- Contributing
- Third-party Extensions
- Get Help: use the python-attrs tag on Stack Overflow

### attrs for Enterprise

Available as part of the Tidelift Subscription.

The maintainers of attrs and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open source packages you use to build your applications.
Save time, reduce risk, and improve code health, while paying the maintainers of the exact packages you use.

## Release Information

### Backwards-incompatible Changes

- Field aliases are now resolved before calling field_transformer, so transformers receive fully populated Attribute objects with usable alias values instead of None.
The new Attribute.alias_is_default flag indicates whether the alias was auto-generated (True) or explicitly set by the user (False).
#1509

### Changes

- Fix type annotations for attrs.validators.optional(), so it no longer rejects tuples with more than one validator.
#1496
- The attrs.validators.disabled() contextmanager can now be nested.
#1513
- Frozen classes can set on_setattr=attrs.setters.NO_OP in addition to None.
#1515
- It's now possible to pass attrs instances in addition to attrs classes to attrs.fields().
#1529

---

Full changelog →
