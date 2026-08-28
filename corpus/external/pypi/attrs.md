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

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

attrs-26.1.0.tar.gz
 (952.1 kB
 view details)

Uploaded
 Mar 19, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

attrs-26.1.0-py3-none-any.whl
 (67.5 kB
 view details)

Uploaded
 Mar 19, 2026
 Python 3

## File details

Details for the file attrs-26.1.0.tar.gz.

### File metadata

- Download URL: attrs-26.1.0.tar.gz
- Upload date:
 Mar 19, 2026
- Size: 952.1 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for attrs-26.1.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | d03ceb89cb322a8fd706d4fb91940737b6642aa36998fe130a9bc96c985eff32 | |
| MD5 | 633953d1aa39cfa76c733a20fdd9c196 | |
| BLAKE2b-256 | 9a8e82a0fe20a541c03148528be8cac2408564a6c9a0cc7e9171802bc1d26985 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for attrs-26.1.0.tar.gz:

Publisher: pypi-package.yml on python-attrs/attrs

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: attrs-26.1.0.tar.gz
 - Subject digest: d03ceb89cb322a8fd706d4fb91940737b6642aa36998fe130a9bc96c985eff32
 - Sigstore transparency entry: 1134709027
 - Sigstore integration time:
 Mar 19, 2026
 Source repository:

 - Permalink: python-attrs/attrs@7bfc49e9b22d5ba25b6e429524c3d49fee27cb36
 - Branch / Tag: refs/tags/26.1.0
 - Owner: https://github.com/python-attrs
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-package.yml@7bfc49e9b22d5ba25b6e429524c3d49fee27cb36
 - Trigger Event: release

## File details

Details for the file attrs-26.1.0-py3-none-any.whl.

### File metadata

- Download URL: attrs-26.1.0-py3-none-any.whl
- Upload date:
 Mar 19, 2026
- Size: 67.5 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for attrs-26.1.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309 | |
| MD5 | 643aa39724d0b47daf07adb1ba79027f | |
| BLAKE2b-256 | 64b417d4b0b2a2dc85a6df63d1157e028ed19f90d4cd97c36717afef2bc2f395 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for attrs-26.1.0-py3-none-any.whl:

Publisher: pypi-package.yml on python-attrs/attrs

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: attrs-26.1.0-py3-none-any.whl
 - Subject digest: c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309
 - Sigstore transparency entry: 1134709040
 - Sigstore integration time:
 Mar 19, 2026
 Source repository:

 - Permalink: python-attrs/attrs@7bfc49e9b22d5ba25b6e429524c3d49fee27cb36
 - Branch / Tag: refs/tags/26.1.0
 - Owner: https://github.com/python-attrs
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-package.yml@7bfc49e9b22d5ba25b6e429524c3d49fee27cb36
 - Trigger Event: release

## Release history Release notifications |
 RSS feed

This release

26.1.0 This release

Mar 19, 2026
 2 files

25.4.0

Oct 6, 2025
 2 files

25.3.0

Mar 13, 2025
 2 files

25.2.0

Mar 12, 2025
 2 files

25.1.0

Jan 25, 2025
 2 files

24.3.0

Dec 16, 2024
 2 files

24.2.0

Aug 6, 2024
 2 files

24.1.0

Aug 3, 2024
 2 files

23.2.0

Dec 31, 2023
 2 files

23.1.0

Apr 16, 2023
 2 files

22.2.0

Dec 21, 2022
 2 files

22.1.0

Jul 28, 2022
 2 files

21.4.0

Dec 29, 2021
 2 files

21.3.0

Dec 28, 2021
 2 files

21.2.0

May 7, 2021
 2 files

Yanked

21.1.0

May 6, 2021
 2 files

20.3.0

Nov 5, 2020
 2 files

20.2.0

Sep 5, 2020
 2 files

20.1.0

Aug 20, 2020
 2 files

19.3.0

Oct 15, 2019
 2 files

19.2.0

Oct 1, 2019
 2 files

19.1.0

Mar 3, 2019
 2 files

18.2.0

Sep 1, 2018
 2 files

18.1.0

May 3, 2018
 2 files

17.4.0

Dec 30, 2017
 2 files

17.3.0

Nov 8, 2017
 2 files

17.2.0

May 24, 2017
 2 files

17.1.0

May 16, 2017
 2 files

16.3.0

Nov 24, 2016
 2 files

16.2.0

Sep 17, 2016
 2 files

16.1.0

Aug 30, 2016
 2 files

16.0.0

May 23, 2016
 2 files

15.2.0

Dec 8, 2015
 2 files

15.1.0

Aug 20, 2015
 2 files

15.0.0

Apr 15, 2015
 2 files

Pre-release

15.0.0a1

Feb 21, 2015
 2 files