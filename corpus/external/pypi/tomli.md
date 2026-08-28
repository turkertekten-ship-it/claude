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

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

tomli-2.4.1.tar.gz
 (17.5 kB
 view details)

Uploaded
 Mar 25, 2026
 Source

### Built Distributions

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

tomli-2.4.1-py3-none-any.whl
 (14.6 kB
 view details)

Uploaded
 Mar 25, 2026
 Python 3

tomli-2.4.1-cp314-cp314t-win_arm64.whl
 (100.4 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tWindows ARM64

tomli-2.4.1-cp314-cp314t-win_amd64.whl
 (121.2 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tWindows x86-64

tomli-2.4.1-cp314-cp314t-win32.whl
 (108.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tWindows x86

tomli-2.4.1-cp314-cp314t-musllinux_1_2_x86_64.whl
 (283.1 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tmusllinux: musl 1.2+ x86-64

tomli-2.4.1-cp314-cp314t-musllinux_1_2_aarch64.whl
 (274.9 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tmusllinux: musl 1.2+ ARM64

tomli-2.4.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (278.5 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tmanylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

tomli-2.4.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (270.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tmanylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

tomli-2.4.1-cp314-cp314t-macosx_11_0_arm64.whl
 (160.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tmacOS 11.0+ ARM64

tomli-2.4.1-cp314-cp314t-macosx_10_15_x86_64.whl
 (164.3 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14tmacOS 10.15+ x86-64

tomli-2.4.1-cp314-cp314-win_arm64.whl
 (96.5 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14Windows ARM64

tomli-2.4.1-cp314-cp314-win_amd64.whl
 (109.1 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14Windows x86-64

tomli-2.4.1-cp314-cp314-win32.whl
 (99.0 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14Windows x86

tomli-2.4.1-cp314-cp314-musllinux_1_2_x86_64.whl
 (256.2 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14musllinux: musl 1.2+ x86-64

tomli-2.4.1-cp314-cp314-musllinux_1_2_aarch64.whl
 (248.0 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14musllinux: musl 1.2+ ARM64

tomli-2.4.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (252.1 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

tomli-2.4.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (244.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

tomli-2.4.1-cp314-cp314-macosx_11_0_arm64.whl
 (149.9 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14macOS 11.0+ ARM64

tomli-2.4.1-cp314-cp314-macosx_10_15_x86_64.whl
 (155.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.14macOS 10.15+ x86-64

tomli-2.4.1-cp313-cp313-win_arm64.whl
 (95.3 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13Windows ARM64

tomli-2.4.1-cp313-cp313-win_amd64.whl
 (108.8 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13Windows x86-64

tomli-2.4.1-cp313-cp313-win32.whl
 (98.0 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13Windows x86

tomli-2.4.1-cp313-cp313-musllinux_1_2_x86_64.whl
 (251.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13musllinux: musl 1.2+ x86-64

tomli-2.4.1-cp313-cp313-musllinux_1_2_aarch64.whl
 (247.2 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13musllinux: musl 1.2+ ARM64

tomli-2.4.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (251.6 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

tomli-2.4.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (243.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

tomli-2.4.1-cp313-cp313-macosx_11_0_arm64.whl
 (149.9 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13macOS 11.0+ ARM64

tomli-2.4.1-cp313-cp313-macosx_10_13_x86_64.whl
 (155.9 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.13macOS 10.13+ x86-64

tomli-2.4.1-cp312-cp312-win_arm64.whl
 (95.1 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12Windows ARM64

tomli-2.4.1-cp312-cp312-win_amd64.whl
 (108.8 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12Windows x86-64

tomli-2.4.1-cp312-cp312-win32.whl
 (98.1 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12Windows x86

tomli-2.4.1-cp312-cp312-musllinux_1_2_x86_64.whl
 (253.3 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12musllinux: musl 1.2+ x86-64

tomli-2.4.1-cp312-cp312-musllinux_1_2_aarch64.whl
 (248.2 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12musllinux: musl 1.2+ ARM64

tomli-2.4.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (253.3 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

tomli-2.4.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (244.9 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

tomli-2.4.1-cp312-cp312-macosx_11_0_arm64.whl
 (150.0 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12macOS 11.0+ ARM64

tomli-2.4.1-cp312-cp312-macosx_10_13_x86_64.whl
 (155.9 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.12macOS 10.13+ x86-64

tomli-2.4.1-cp311-cp311-win_arm64.whl
 (95.3 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11Windows ARM64

tomli-2.4.1-cp311-cp311-win_amd64.whl
 (108.1 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11Windows x86-64

tomli-2.4.1-cp311-cp311-win32.whl
 (97.2 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11Windows x86

tomli-2.4.1-cp311-cp311-musllinux_1_2_x86_64.whl
 (247.9 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11musllinux: musl 1.2+ x86-64

tomli-2.4.1-cp311-cp311-musllinux_1_2_aarch64.whl
 (242.2 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11musllinux: musl 1.2+ ARM64

tomli-2.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (243.8 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

tomli-2.4.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (237.6 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

tomli-2.4.1-cp311-cp311-macosx_11_0_arm64.whl
 (149.5 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11macOS 11.0+ ARM64

tomli-2.4.1-cp311-cp311-macosx_10_9_x86_64.whl
 (154.7 kB
 view details)

Uploaded
 Mar 25, 2026
 CPython 3.11macOS 10.9+ x86-64

## File details

Details for the file tomli-2.4.1.tar.gz.

### File metadata

- Download URL: tomli-2.4.1.tar.gz
- Upload date:
 Mar 25, 2026
- Size: 17.5 kB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 7c7e1a961a0b2f2472c1ac5b69affa0ae1132c39adcb67aba98568702b9cc23f | |
| MD5 | 74df8e3714ffa480b8076c98247ae1d1 | |
| BLAKE2b-256 | 22de48c59722572767841493b26183a0d1cc411d54fd759c5607c4590b6563a6 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-py3-none-any.whl.

### File metadata

- Download URL: tomli-2.4.1-py3-none-any.whl
- Upload date:
 Mar 25, 2026
- Size: 14.6 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 0d85819802132122da43cb86656f8d1f8c6587d54ae7dcaf30e90533028b49fe | |
| MD5 | ebb39e1673d8b752468c3462e88f185f | |
| BLAKE2b-256 | 7b61cceae43728b7de99d9b847560c262873a1f6c98202171fd5ed62640b494b | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-win_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-win_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 100.4 kB
- Tags: CPython 3.14t, Windows ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | eab21f45c7f66c13f2a9e0e1535309cee140182a9cdae1e041d02e47291e8396 | |
| MD5 | 77d9359bc9633574cc8dfd50abdbbde4 | |
| BLAKE2b-256 | 5acde80b62269fc78fc36c9af5a6b89c835baa8af28ff5ad28c7028d60860320 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-win_amd64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-win_amd64.whl
- Upload date:
 Mar 25, 2026
- Size: 121.2 kB
- Tags: CPython 3.14t, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 2c1c351919aca02858f740c6d33adea0c5deea37f9ecca1cc1ef9e884a619d26 | |
| MD5 | 9f846af1f6ba62663b366cbe6efa2b24 | |
| BLAKE2b-256 | 1264da524626d3b9cc40c168a13da8335fe1c51be12c0a63685cc6db7308daae | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-win32.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-win32.whl
- Upload date:
 Mar 25, 2026
- Size: 108.7 kB
- Tags: CPython 3.14t, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-win32.whl
| Algorithm | Hash digest | |
| SHA256 | b1d22e6e9387bf4739fbe23bfa80e93f6b0373a7f1b96c6227c32bef95a4d7a8 | |
| MD5 | cbf58f79921f2de7fe51797c41a141f7 | |
| BLAKE2b-256 | efbe605a6261cac79fba2ec0c9827e986e00323a1945700969b8ee0b30d85453 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-musllinux_1_2_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 283.1 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 504aa796fe0569bb43171066009ead363de03675276d2d121ac1a4572397870f | |
| MD5 | ec60ff8763f097eec525dd81932e1171 | |
| BLAKE2b-256 | 77a3ec9dd4fd2c38e98de34223b995a3b34813e6bdadf86c75314c928350ed14 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-musllinux_1_2_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 274.9 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 8a650c2dbafa08d42e51ba0b62740dae4ecb9338eefa093aa5c78ceb546fcd5c | |
| MD5 | 1f71dbed665f8ddd13b96957f9c806bb | |
| BLAKE2b-256 | 053830f541baf6a3f6df77b3df16b01ba319221389e2da59427e221ef417ac0c | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 278.5 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 734e20b57ba95624ecf1841e72b53f6e186355e216e5412de414e3c51e5e3c41 | |
| MD5 | db2769ce4e6aea65487eaa77c43e3740 | |
| BLAKE2b-256 | 7ab41613716072e544d1a7891f548d8f9ec6ce2faf42ca65acae01d76ea06bb0 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 270.7 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 1d8591993e228b0c930c4bb0db464bdad97b3289fb981255d6c9a41aedc84b2d | |
| MD5 | 3cdbcbb65b8aefe75e7e05516763bf88 | |
| BLAKE2b-256 | 02e03630057d8eb170310785723ed5adcdfb7d50cb7e6455f85ba8a3deed642b | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-macosx_11_0_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-macosx_11_0_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 160.7 kB
- Tags: CPython 3.14t, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 7008df2e7655c495dd12d2a4ad038ff878d4ca4b81fccaf82b714e07eae4402c | |
| MD5 | 2d57042d1009860d8ff325cc59399b03 | |
| BLAKE2b-256 | 24796ab420d37a270b89f7195dec5448f79400d9e9c1826df982f3f8e97b24fd | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314t-macosx_10_15_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314t-macosx_10_15_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 164.3 kB
- Tags: CPython 3.14t, macOS 10.15+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314t-macosx_10_15_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | d4d8fe59808a54658fcc0160ecfb1b30f9089906c50b23bcb4c69eddc19ec2b4 | |
| MD5 | 081bf166dff99394ae2a5c041a59a12f | |
| BLAKE2b-256 | 454bb877b05c8ba62927d9865dd980e34a755de541eb65fffba52b4cc495d4d2 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-win_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-win_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 96.5 kB
- Tags: CPython 3.14, Windows ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | b8c198f8c1805dc42708689ed6864951fd2494f924149d3e4bce7710f8eb5232 | |
| MD5 | f8cef18980bb272cf1dbfa0f1f738107 | |
| BLAKE2b-256 | d52f702d5e05b227401c1068f0d386d79a589bb12bf64c3d2c72ce0631e3bc49 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-win_amd64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-win_amd64.whl
- Upload date:
 Mar 25, 2026
- Size: 109.1 kB
- Tags: CPython 3.14, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 88dceee75c2c63af144e456745e10101eb67361050196b0b6af5d717254dddf7 | |
| MD5 | a03b1cb1df9ddefbe74de0a2261dfb77 | |
| BLAKE2b-256 | 1458640ac93bf230cd27d002462c9af0d837779f8773bc03dee06b5835208214 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-win32.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-win32.whl
- Upload date:
 Mar 25, 2026
- Size: 99.0 kB
- Tags: CPython 3.14, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 3d48a93ee1c9b79c04bb38772ee1b64dcf18ff43085896ea460ca8dec96f35f6 | |
| MD5 | d3ca0c8eb54d8abbaf89f3838d952c94 | |
| BLAKE2b-256 | 8c9ab4173689a9203472e5467217e0154b00e260621caa227b6fa01feab16998 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-musllinux_1_2_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 256.2 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | ede3e6487c5ef5d28634ba3f31f989030ad6af71edfb0055cbbd14189ff240ba | |
| MD5 | 622e6dfae818b12bcd8b09980066d9fa | |
| BLAKE2b-256 | 6750361e986652847fec4bd5e4a0208752fbe64689c603c7ae5ea7cb16b1c0ca | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-musllinux_1_2_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 248.0 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 7f94b27a62cfad8496c8d2513e1a222dd446f095fca8987fceef261225538a15 | |
| MD5 | 1b111303b2db37a30fec8878afe4a369 | |
| BLAKE2b-256 | 00713a69e86f3eafe8c7a59d008d245888051005bd657760e96d5fbfb0b740c2 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 252.1 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 01f520d4f53ef97964a240a035ec2a869fe1a37dde002b57ebc4417a27ccd853 | |
| MD5 | c87d84e0be1723273769073a650012cd | |
| BLAKE2b-256 | df6dc5fad00d82b3c7a3ab6189bd4b10e60466f22cfe8a08a9394185c8a8111c | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 244.7 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 559db847dc486944896521f68d8190be1c9e719fced785720d2216fe7022b662 | |
| MD5 | 03bcd4d59cd26a59165213df89159b10 | |
| BLAKE2b-256 | ce4866341bdb858ad9bd0ceab5a86f90eddab127cf8b046418009f2125630ecb | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-macosx_11_0_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-macosx_11_0_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 149.9 kB
- Tags: CPython 3.14, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | a120733b01c45e9a0c34aeef92bf0cf1d56cfe81ed9d47d562f9ed591a9828ac | |
| MD5 | 92d6c89412514223c21c65522344aad6 | |
| BLAKE2b-256 | 6205d2f816630cc771ad836af54f5001f47a6f611d2d39535364f148b6a92d6b | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp314-cp314-macosx_10_15_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp314-cp314-macosx_10_15_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 155.7 kB
- Tags: CPython 3.14, macOS 10.15+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp314-cp314-macosx_10_15_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | fd0409a3653af6c147209d267a0e4243f0ae46b011aa978b1080359fddc9b6cf | |
| MD5 | 9f2358fa5a5ca4327f23cefef3de8e23 | |
| BLAKE2b-256 | 3cfb9a5c8d27dbab540869f7c1f8eb0abb3244189ce780ba9cd73f3770662072 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-win_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-win_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 95.3 kB
- Tags: CPython 3.13, Windows ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 4b605484e43cdc43f0954ddae319fb75f04cc10dd80d830540060ee7cd0243cd | |
| MD5 | baa0354c85defe13e1f9b18a95aa8694 | |
| BLAKE2b-256 | 837ad34f422a021d62420b78f5c538e5b102f62bea616d1d75a13f0a88acb04a | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-win_amd64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-win_amd64.whl
- Upload date:
 Mar 25, 2026
- Size: 108.8 kB
- Tags: CPython 3.13, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 8d65a2fbf9d2f8352685bc1364177ee3923d6baf5e7f43ea4959d7d8bc326a36 | |
| MD5 | 1ac2ae9ab013f9460fb92e7ab37d50b8 | |
| BLAKE2b-256 | 6a1e71dfd96bcc1c775420cb8befe7a9d35f2e5b1309798f009dca17b7708c1e | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-win32.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-win32.whl
- Upload date:
 Mar 25, 2026
- Size: 98.0 kB
- Tags: CPython 3.13, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 2190f2e9dd7508d2a90ded5ed369255980a1bcdd58e52f7fe24b8162bf9fedbd | |
| MD5 | 7fb4b75051161d0813166cee5dfd4516 | |
| BLAKE2b-256 | 16f9229fa3434c590ddf6c0aa9af64d3af4b752540686cace29e6281e3458469 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-musllinux_1_2_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 251.7 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 51529d40e3ca50046d7606fa99ce3956a617f9b36380da3b7f0dd3dd28e68cb5 | |
| MD5 | 62bec3d1465ec7fc28cdad67fb334bff | |
| BLAKE2b-256 | d37416336ffd19ed4da28a70959f92f506233bd7cfc2332b20bdb01591e8b1d1 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-musllinux_1_2_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 247.2 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | d312ef37c91508b0ab2cee7da26ec0b3ed2f03ce12bd87a588d771ae15dcf82d | |
| MD5 | 1ebad934e46e86ce7d9f5ee50895de6f | |
| BLAKE2b-256 | e3f1dbeeb9116715abee2485bf0a12d07a8f31af94d71608c171c45f64c0469d | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 251.6 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | f3c6818a1a86dd6dca7ddcaaf76947d5ba31aecc28cb1b67009a5877c9a64f3f | |
| MD5 | b7a0dd2df126145fd162c500b6f484b6 | |
| BLAKE2b-256 | 108fd3ddb16c5a4befdf31a23307f72828686ab2096f068eaf56631e136c1fdd | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 243.7 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | c7f2c7f2b9ca6bdeef8f0fa897f8e05085923eb091721675170254cbc5b02897 | |
| MD5 | e8748302cd3dc334ede4f46ca3904bfc | |
| BLAKE2b-256 | 5ce090637574e5e7212c09099c67ad349b04ec4d6020324539297b634a0192b0 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-macosx_11_0_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-macosx_11_0_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 149.9 kB
- Tags: CPython 3.13, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | eb0dc4e38e6a1fd579e5d50369aa2e10acfc9cace504579b2faabb478e76941a | |
| MD5 | a1c4cd874d50a559ada39bf364d805a2 | |
| BLAKE2b-256 | 146f12645cf7f08e1a20c7eb8c297c6f11d31c1b50f316a7e7e1e1de6e2e7b7e | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp313-cp313-macosx_10_13_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp313-cp313-macosx_10_13_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 155.9 kB
- Tags: CPython 3.13, macOS 10.13+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp313-cp313-macosx_10_13_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 36d2bd2ad5fb9eaddba5226aa02c8ec3fa4f192631e347b3ed28186d43be6b54 | |
| MD5 | 3fddb416c052db5ac89930af9925a5a7 | |
| BLAKE2b-256 | 0706b823a7e818c756d9a7123ba2cda7d07bc2dd32835648d1a7b7b7a05d848d | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-win_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-win_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 95.1 kB
- Tags: CPython 3.12, Windows ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | f758f1b9299d059cc3f6546ae2af89670cb1c4d48ea29c3cacc4fe7de3058257 | |
| MD5 | 7d2f8ea5ffae58af999346dc788619ac | |
| BLAKE2b-256 | 68fd70e768887666ddd9e9f5d85129e84910f2db2796f9096aa02b721a53098d | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-win_amd64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-win_amd64.whl
- Upload date:
 Mar 25, 2026
- Size: 108.8 kB
- Tags: CPython 3.12, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 52c8ef851d9a240f11a88c003eacb03c31fc1c9c4ec64a99a0f922b93874fda9 | |
| MD5 | ee6f099da176f70fd440c3fd003fe3cc | |
| BLAKE2b-256 | 24224daacd05391b92c55759d55eaee21e1dfaea86ce5c571f10083360adf534 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-win32.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-win32.whl
- Upload date:
 Mar 25, 2026
- Size: 98.1 kB
- Tags: CPython 3.12, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-win32.whl
| Algorithm | Hash digest | |
| SHA256 | da25dc3563bff5965356133435b757a795a17b17d01dbc0f42fb32447ddfd917 | |
| MD5 | 7db2f906acfb6ae5cc19f12eb5adc5cb | |
| BLAKE2b-256 | d62f4a3c322f22c5c66c4b836ec58211641a4067364f5dcdd7b974b4c5da300c | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-musllinux_1_2_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 253.3 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 5cb41aa38891e073ee49d55fbc7839cfdb2bc0e600add13874d048c94aadddd1 | |
| MD5 | 1463043b5a06e590fd52bf63e7c3885f | |
| BLAKE2b-256 | 99e7c6f69c3120de34bbd882c6fba7975f3d7a746e9218e56ab46a1bc4b42552 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-musllinux_1_2_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 248.2 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 5e262d41726bc187e69af7825504c933b6794dc3fbd5945e41a79bb14c31f585 | |
| MD5 | e3e9ff4ab1658ca5fe82fc458dfdd841 | |
| BLAKE2b-256 | 1a7ecaf6496d60152ad4ed09282c1885cca4eea150bfd007da84aea07bcc0a3e | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 253.3 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 136443dbd7e1dee43c68ac2694fde36b2849865fa258d39bf822c10e8068eac5 | |
| MD5 | 5b4773812639196f447cf67fd74ad201 | |
| BLAKE2b-256 | 1090d62ce007a1c80d0b2c93e02cab211224756240884751b94ca72df8a875ca | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 244.9 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | ff18e6a727ee0ab0388507b89d1bc6a22b138d1e2fa56d1ad494586d61d2eae9 | |
| MD5 | 325c4bde49cdac8fb4e0504ebdd060fd | |
| BLAKE2b-256 | 5c0579d13d7c15f13bdef410bdd49a6485b1c37d28968314eabee452c22a7fda | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-macosx_11_0_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-macosx_11_0_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 150.0 kB
- Tags: CPython 3.12, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 7f86fd587c4ed9dd76f318225e7d9b29cfc5a9d43de44e5754db8d1128487085 | |
| MD5 | 9c5c6927dcfe725cc36ca0f4da617bab | |
| BLAKE2b-256 | dcc762d7a17c26487ade21c5422b646110f2162f1fcc95980ef7f63e73c68f14 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp312-cp312-macosx_10_13_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp312-cp312-macosx_10_13_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 155.9 kB
- Tags: CPython 3.12, macOS 10.13+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp312-cp312-macosx_10_13_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | c742f741d58a28940ce01d58f0ab2ea3ced8b12402f162f4d534dfe18ba1cd6a | |
| MD5 | 0b7b3760560dca4568810f33bd799550 | |
| BLAKE2b-256 | c1ba42f134a3fe2b370f555f44b1d72feebb94debcab01676bf918d0cb70e9aa | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-win_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-win_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 95.3 kB
- Tags: CPython 3.11, Windows ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | c2541745709bad0264b7d4705ad453b76ccd191e64aa6f0fc66b69a293a45ece | |
| MD5 | 97d426540d29a2be25fd9ad8acaf71d0 | |
| BLAKE2b-256 | b883dceca96142499c069475b790e7913b1044c1a4337e700751f48ed723f883 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-win_amd64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-win_amd64.whl
- Upload date:
 Mar 25, 2026
- Size: 108.1 kB
- Tags: CPython 3.11, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 5ee18d9ebdb417e384b58fe414e8d6af9f4e7a0ae761519fb50f721de398dd4e | |
| MD5 | 9c7f1129f9d2a19f6f72d1e6b5e72568 | |
| BLAKE2b-256 | 425971461df1a885647e10b6bb7802d0b8e66480c61f3f43079e0dcd315b3954 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-win32.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-win32.whl
- Upload date:
 Mar 25, 2026
- Size: 97.2 kB
- Tags: CPython 3.11, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-win32.whl
| Algorithm | Hash digest | |
| SHA256 | ff2983983d34813c1aeb0fa89091e76c3a22889ee83ab27c5eeb45100560c049 | |
| MD5 | 9ec77c16fad73b6e99482e1aecbf2338 | |
| BLAKE2b-256 | 83bd6c1a630eaca337e1e78c5903104f831bda934c426f9231429396ce3c3467 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-musllinux_1_2_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 247.9 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | ec9bfaf3ad2df51ace80688143a6a4ebc09a248f6ff781a9945e51937008fcbc | |
| MD5 | d1327a3dd843e03b85aa491e869514e7 | |
| BLAKE2b-256 | 6b492b2a0ef529aa6eec245d25f0c703e020a73955ad7edf73e7f54ddc608aa5 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-musllinux_1_2_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 242.2 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 47149d5bd38761ac8be13a84864bf0b7b70bc051806bc3669ab1cbc56216b23c | |
| MD5 | 77ae1c8a92e073828e6e2d034d49fdbc | |
| BLAKE2b-256 | 22e45a816ecdd1f8ca51fb756ef684b90f2780afc52fc67f987e3c61d800a46d | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 243.8 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 5a881ab208c0baf688221f8cecc5401bd291d67e38a1ac884d6736cbcd8247e9 | |
| MD5 | 42df515becdcc5775ccf0b7a81004455 | |
| BLAKE2b-256 | 48c1f41d9cb618acccca7df82aaf682f9b49013c9397212cb9f53219e3abac37 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Mar 25, 2026
- Size: 237.6 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 96481a5786729fd470164b47cdb3e0e58062a496f455ee41b4403be77cb5a076 | |
| MD5 | 9eb91b9fa0997ffb8ea54b6713f3db3a | |
| BLAKE2b-256 | 617181c50943cf953efa35bce7646caab3cf457a7d8c030b27cfb40d7235f9ee | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-macosx_11_0_arm64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-macosx_11_0_arm64.whl
- Upload date:
 Mar 25, 2026
- Size: 149.5 kB
- Tags: CPython 3.11, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 4ab97e64ccda8756376892c53a72bd1f964e519c77236368527f758fbc36a53a | |
| MD5 | 595ee8e30e8540bcc03dafc3e9a0e4ea | |
| BLAKE2b-256 | 6df7675db52c7e46064a9aa928885a9b20f4124ecb9bc2e1ce74c9106648d202 | |

See more details on using hashes here.

## File details

Details for the file tomli-2.4.1-cp311-cp311-macosx_10_9_x86_64.whl.

### File metadata

- Download URL: tomli-2.4.1-cp311-cp311-macosx_10_9_x86_64.whl
- Upload date:
 Mar 25, 2026
- Size: 154.7 kB
- Tags: CPython 3.11, macOS 10.9+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/6.2.0 CPython/3.14.3

### File hashes

Hashes for tomli-2.4.1-cp311-cp311-macosx_10_9_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | f8f0fc26ec2cc2b965b7a3b87cd19c5c6b8c5e5f436b984e85f486d652285c30 | |
| MD5 | 62fa38b769d403c9966dd2801710d27a | |
| BLAKE2b-256 | f411db3d5885d8528263d8adc260bb2d28ebf1270b96e98f0e0268d32b8d9900 | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

This release

2.4.1 This release

Mar 25, 2026
 47 files

2.4.0

Jan 11, 2026
 47 files

2.3.1

Mar 25, 2026
 47 files

2.3.0

Oct 8, 2025
 42 files

2.2.1

Nov 27, 2024
 32 files

2.1.0

Nov 11, 2024
 2 files

2.0.2

Oct 2, 2024
 2 files

2.0.1

Feb 8, 2022
 2 files

2.0.0

Dec 13, 2021
 2 files

1.2.3

Dec 13, 2021
 2 files

1.2.2

Oct 25, 2021
 2 files

1.2.1

Aug 5, 2021
 2 files

1.2.0

Jul 30, 2021
 2 files

1.1.0

Jul 23, 2021
 2 files

1.0.4

Jul 4, 2021
 2 files

1.0.3

Jun 27, 2021
 2 files

1.0.2

Jun 18, 2021
 2 files

1.0.1

Jun 15, 2021
 2 files

1.0.0

Jun 8, 2021
 2 files

0.2.10

Jun 6, 2021
 2 files

0.2.9

Jun 4, 2021
 2 files

0.2.8

Jun 4, 2021
 2 files

0.2.7

Jun 2, 2021
 2 files

0.2.6

May 31, 2021
 2 files

0.2.5

May 31, 2021
 2 files

0.2.4

May 30, 2021
 2 files

0.2.3

May 29, 2021
 2 files

0.2.2

May 28, 2021
 2 files

0.2.1

May 28, 2021
 2 files

0.2.0

May 27, 2021
 2 files