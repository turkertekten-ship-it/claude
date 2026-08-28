[image: Build Status] [image: codecov.io] [image: PyPI version]

# Tomli

> A lil' TOML parser

Table of Contents generated with mdformat-toc

- Intro
- Installation
- Usage

 - Parse a TOML string
 - Parse a TOML file
 - Handle invalid TOML
 - Construct decimal.Decimals from TOML floats
 - Building a tomli/tomllib compatibility layer
- FAQ

 - Why this parser?
 - Is comment preserving round-trip parsing supported?
 - Is there a dumps, write or encode function?
 - How do TOML types map into Python types?
- Performance

 - Mypyc generated wheel
 - Pure Python

## Intro

Tomli is a Python library for parsing TOML.
Version 2.4.0 and later are compatible with TOML v1.1.0.
Older versions are TOML v1.0.0 compatible.

A version of Tomli, the tomllib module,
was added to the standard library in Python 3.11
via PEP 680.
Tomli continues to provide a backport on PyPI for Python versions
where the standard library module is not available
and that have not yet reached their end-of-life.

Tomli uses mypyc
to generate binary wheels for most of the widely used platforms,
so Python 3.11+ users may prefer it over tomllib for improved performance.
Pure Python wheels are available on any platform and should perform the same as tomllib.

## Installation

```
pip install tomli
```

## Usage

### Parse a TOML string

```
import tomli

toml_str = """
[[players]]
name = "Lehtinen"
number = 26

[[players]]
name = "Numminen"
number = 27
"""

toml_dict = tomli.loads(toml_str)
assert toml_dict == {
    "players": [{"name": "Lehtinen", "number": 26}, {"name": "Numminen", "number": 27}]
}
```

### Parse a TOML file

```
import tomli

with open("path_to_file/conf.toml", "rb") as f:
    toml_dict = tomli.load(f)
```

The file must be opened in binary mode (with the "rb" flag).
Binary mode will enforce decoding the file as UTF-8 with universal newlines disabled,
both of which are required to correctly parse TOML.

### Handle invalid TOML

```
import tomli

try:
    toml_dict = tomli.loads("]] this is invalid TOML [[")
except tomli.TOMLDecodeError:
    print("Yep, definitely not valid.")
```

Note that error messages are considered informational only.
They should not be assumed to stay constant across Tomli versions.

### Construct decimal.Decimals from TOML floats

```
from decimal import Decimal
import tomli

toml_dict = tomli.loads("precision-matters = 0.982492", parse_float=Decimal)
assert isinstance(toml_dict["precision-matters"], Decimal)
assert toml_dict["precision-matters"] == Decimal("0.982492")
```

Note that decimal.Decimal can be replaced with another callable that converts a TOML float from string to a Python type.
The decimal.Decimal is, however, a practical choice for use cases where float inaccuracies can not be tolerated.

Illegal types are dict and list, and their subtypes.
A ValueError will be raised if parse_float produces illegal types.

### Building a tomli/tomllib compatibility layer

Python versions 3.11+ ship with a version of Tomli:
the tomllib standard library module.
To build code that uses the standard library if available,
but still works seamlessly with Python 3.6+,
do the following.

Instead of a hard Tomli dependency, use the following
dependency specifier
to only require Tomli when the standard library module is not available:

```
tomli >= 1.1.0 ; python_version < "3.11"
```

Then, in your code, import a TOML parser using the following fallback mechanism:

```
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

tomllib.loads("['This parses fine with Python 3.6+']")
```

## FAQ

### Why this parser?

- it's lil'
- pure Python with zero dependencies
- the fastest pure Python parser *:
14x as fast as tomlkit,
2.1x as fast as toml
- outputs basic data types only
- 100% spec compliant: passes all tests in
toml-lang/toml-test
test suite
- thoroughly tested: 100% branch coverage

### Is comment preserving round-trip parsing supported?

No.

The tomli.loads function returns a plain dict that is populated with builtin types and types from the standard library only.
Preserving comments requires a custom type to be returned so will not be supported,
at least not by the tomli.loads and tomli.load functions.

Look into TOML Kit if preservation of style is what you need.

### Is there a dumps, write or encode function?

Tomli-W is the write-only counterpart of Tomli, providing dump and dumps functions.

The core library does not include write capability, as most TOML use cases are read-only, and Tomli intends to be minimal.

### How do TOML types map into Python types?

| TOML type | Python type | Details |
| Document Root | dict | |
| Key | str | |
| String | str | |
| Integer | int | |
| Float | float | |
| Boolean | bool | |
| Offset Date-Time | datetime.datetime | tzinfo attribute set to an instance of datetime.timezone |
| Local Date-Time | datetime.datetime | tzinfo attribute set to None |
| Local Date | datetime.date | |
| Local Time | datetime.time | |
| Array | list | |
| Table | dict | |
| Inline Table | dict | |

## Performance

The benchmark/ folder in this repository contains a performance benchmark for comparing the various Python TOML parsers.

Below are the results for commit 064e492.

### Mypyc generated wheel

```
foo@bar:~/dev/tomli$ python --version
Python 3.14.2
foo@bar:~/dev/tomli$ pip freeze
pytomlpp==1.1.0
rtoml==0.13.0
toml==0.10.2
tomli @ file:///home/foo/dev/tomli
tomlkit==0.13.3
foo@bar:~/dev/tomli$ python benchmark/run.py
Parsing data.toml 5000 times:
------------------------------------------------------
    parser |  exec time | performance (more is better)
-----------+------------+-----------------------------
     rtoml |    0.328 s | baseline (100%)
  pytomlpp |    0.365 s | 89.75%
     tomli |    0.838 s | 39.12%
      toml |     3.01 s | 10.90%
   tomlkit |     20.7 s | 1.59%
```

### Pure Python

```
foo@bar:~/dev/tomli$ python benchmark/run.py
Parsing data.toml 5000 times:
------------------------------------------------------
    parser |  exec time | performance (more is better)
-----------+------------+-----------------------------
     rtoml |    0.323 s | baseline (100%)
  pytomlpp |    0.365 s | 88.40%
     tomli |     1.44 s | 22.36%
      toml |     3.03 s | 10.65%
   tomlkit |     20.6 s | 1.57%
```
