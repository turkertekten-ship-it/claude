---
date: 2026-04-12T21:43:45+0000
source: https://pypi.org/project/msgspec/
---
[image: CI] [image: Documentation] [image: License] [image: PyPI Version] [image: Conda Version] [image: Code Coverage]

msgspec is a fast serialization and validation library, with builtin
support for JSON, MessagePack,
YAML, and TOML. It features:

- 🚀 High performance encoders/decoders for common protocols. The JSON and
MessagePack implementations regularly
benchmark as the fastest
options for Python.
- 🎉 Support for a wide variety of Python types. Additional types may be
supported through
extensions.
- 🔍 Zero-cost schema validation using familiar Python type annotations. In
benchmarks msgspec
decodes and validates JSON faster than
orjson can decode it alone.
- ✨ A speedy Struct type for representing structured data. If you already
use dataclasses or
attrs,
structs should feel familiar.
However, they're
5-60x faster
for common operations.

All of this is included in a
lightweight library
with no required dependencies.

---

msgspec may be used for serialization alone, as a faster JSON or
MessagePack library. For the greatest benefit though, we recommend using
msgspec to handle the full serialization & validation workflow:

Define your message schemas using standard Python type annotations.

```
>>> import msgspec

>>> class User(msgspec.Struct):
...     """A new type describing a User"""
...     name: str
...     groups: set[str] = set()
...     email: str | None = None
```

Encode messages as JSON, or one of the many other supported protocols.

```
>>> alice = User("alice", groups={"admin", "engineering"})

>>> alice
User(name='alice', groups={"admin", "engineering"}, email=None)

>>> msg = msgspec.json.encode(alice)

>>> msg
b'{"name":"alice","groups":["admin","engineering"],"email":null}'
```

Decode messages back into Python objects, with optional schema validation.

```
>>> msgspec.json.decode(msg, type=User)
User(name='alice', groups={"admin", "engineering"}, email=None)

>>> msgspec.json.decode(b'{"name":"bob","groups":[123]}', type=User)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
msgspec.ValidationError: Expected `str`, got `int` - at `$.groups[0]`
```

msgspec is designed to be as performant as possible, while retaining some of
the nicities of validation libraries like
pydantic. For supported types,
encoding/decoding a message with msgspec can be
~10-80x faster than alternative libraries.

See the documentation for more information.

## LICENSE

New BSD. See the
License File.
