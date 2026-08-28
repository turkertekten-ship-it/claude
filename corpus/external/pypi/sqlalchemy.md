[image: PyPI] [image: PyPI - Python Version] [image: PyPI - Downloads]

The Python SQL Toolkit and Object Relational Mapper

## Introduction

SQLAlchemy is the Python SQL toolkit and Object Relational Mapper
that gives application developers the full power and
flexibility of SQL. SQLAlchemy provides a full suite
of well known enterprise-level persistence patterns,
designed for efficient and high-performing database
access, adapted into a simple and Pythonic domain
language.

Major SQLAlchemy features include:

- An industrial strength ORM, built
from the core on the identity map, unit of work,
and data mapper patterns. These patterns
allow transparent persistence of objects
using a declarative configuration system.
Domain models
can be constructed and manipulated naturally,
and changes are synchronized with the
current transaction automatically.
- A relationally-oriented query system, exposing
the full range of SQL’s capabilities
explicitly, including joins, subqueries,
correlation, and most everything else,
in terms of the object model.
Writing queries with the ORM uses the same
techniques of relational composition you use
when writing SQL. While you can drop into
literal SQL at any time, it’s virtually never
needed.
- A comprehensive and flexible system
of eager loading for related collections and objects.
Collections are cached within a session,
and can be loaded on individual access, all
at once using joins, or by query per collection
across the full result set.
- A Core SQL construction system and DBAPI
interaction layer. The SQLAlchemy Core is
separate from the ORM and is a full database
abstraction layer in its own right, and includes
an extensible Python-based SQL expression
language, schema metadata, connection pooling,
type coercion, and custom types.
- All primary and foreign key constraints are
assumed to be composite and natural. Surrogate
integer primary keys are of course still the
norm, but SQLAlchemy never assumes or hardcodes
to this model.
- Database introspection and generation. Database
schemas can be “reflected” in one step into
Python structures representing database metadata;
those same structures can then generate
CREATE statements right back out - all within
the Core, independent of the ORM.

SQLAlchemy’s philosophy:

- SQL databases behave less and less like object
collections the more size and performance start to
matter; object collections behave less and less like
tables and rows the more abstraction starts to matter.
SQLAlchemy aims to accommodate both of these
principles.
- An ORM doesn’t need to hide the “R”. A relational
database provides rich, set-based functionality
that should be fully exposed. SQLAlchemy’s
ORM provides an open-ended set of patterns
that allow a developer to construct a custom
mediation layer between a domain model and
a relational schema, turning the so-called
“object relational impedance” issue into
a distant memory.
- The developer, in all cases, makes all decisions
regarding the design, structure, and naming conventions
of both the object model as well as the relational
schema. SQLAlchemy only provides the means
to automate the execution of these decisions.
- With SQLAlchemy, there’s no such thing as
“the ORM generated a bad query” - you
retain full control over the structure of
queries, including how joins are organized,
how subqueries and correlation is used, what
columns are requested. Everything SQLAlchemy
does is ultimately the result of a developer-initiated
decision.
- Don’t use an ORM if the problem doesn’t need one.
SQLAlchemy consists of a Core and separate ORM
component. The Core offers a full SQL expression
language that allows Pythonic construction
of SQL constructs that render directly to SQL
strings for a target database, returning
result sets that are essentially enhanced DBAPI
cursors.
- Transactions should be the norm. With SQLAlchemy’s
ORM, nothing goes to permanent storage until
commit() is called. SQLAlchemy encourages applications
to create a consistent means of delineating
the start and end of a series of operations.
- Never render a literal value in a SQL statement.
Bound parameters are used to the greatest degree
possible, allowing query optimizers to cache
query plans effectively and making SQL injection
attacks a non-issue.

## Documentation

Latest documentation is at:

https://www.sqlalchemy.org/docs/

## Installation / Requirements

Full documentation for installation is at
Installation.

## Getting Help / Development / Bug reporting

Please refer to the SQLAlchemy Community Guide.

## Code of Conduct

Above all, SQLAlchemy places great emphasis on polite, thoughtful, and
constructive communication between users and developers.
Please see our current Code of Conduct at
Code of Conduct.

## License

SQLAlchemy is distributed under the MIT license.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

sqlalchemy-2.0.52.tar.gz
 (9.9 MB
 view details)

Uploaded
 Aug 11, 2026
 Source

### Built Distributions

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

sqlalchemy-2.0.52-py3-none-any.whl
 (2.0 MB
 view details)

Uploaded
 Aug 11, 2026
 Python 3

sqlalchemy-2.0.52-cp314-cp314t-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14tmacOS 11.0+ ARM64

sqlalchemy-2.0.52-cp314-cp314-win_amd64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14Windows x86-64

sqlalchemy-2.0.52-cp314-cp314-win32.whl
 (2.1 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14Windows x86

sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14musllinux: musl 1.2+ x86-64

sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14musllinux: musl 1.2+ ARM64

sqlalchemy-2.0.52-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

sqlalchemy-2.0.52-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

sqlalchemy-2.0.52-cp314-cp314-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.14macOS 11.0+ ARM64

sqlalchemy-2.0.52-cp313-cp313-win_amd64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.13Windows x86-64

sqlalchemy-2.0.52-cp313-cp313-win32.whl
 (2.1 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.13Windows x86

sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.13musllinux: musl 1.2+ x86-64

sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.13musllinux: musl 1.2+ ARM64

sqlalchemy-2.0.52-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.13manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

sqlalchemy-2.0.52-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.13manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

sqlalchemy-2.0.52-cp313-cp313-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.13macOS 11.0+ ARM64

sqlalchemy-2.0.52-cp312-cp312-win_amd64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.12Windows x86-64

sqlalchemy-2.0.52-cp312-cp312-win32.whl
 (2.1 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.12Windows x86

sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_x86_64.whl
 (3.4 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.12musllinux: musl 1.2+ x86-64

sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.12musllinux: musl 1.2+ ARM64

sqlalchemy-2.0.52-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (3.4 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.12manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

sqlalchemy-2.0.52-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (3.4 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.12manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

sqlalchemy-2.0.52-cp312-cp312-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.12macOS 11.0+ ARM64

sqlalchemy-2.0.52-cp311-cp311-win_amd64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.11Windows x86-64

sqlalchemy-2.0.52-cp311-cp311-win32.whl
 (2.1 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.11Windows x86

sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.11musllinux: musl 1.2+ x86-64

sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.11musllinux: musl 1.2+ ARM64

sqlalchemy-2.0.52-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (3.4 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.11manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

sqlalchemy-2.0.52-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (3.4 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.11manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

sqlalchemy-2.0.52-cp311-cp311-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.11macOS 11.0+ ARM64

sqlalchemy-2.0.52-cp310-cp310-win_amd64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.10Windows x86-64

sqlalchemy-2.0.52-cp310-cp310-win32.whl
 (2.1 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.10Windows x86

sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.10musllinux: musl 1.2+ x86-64

sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_aarch64.whl
 (3.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.10musllinux: musl 1.2+ ARM64

sqlalchemy-2.0.52-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.10manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

sqlalchemy-2.0.52-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.10manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

sqlalchemy-2.0.52-cp310-cp310-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.10macOS 11.0+ ARM64

sqlalchemy-2.0.52-cp39-cp39-win_amd64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.9Windows x86-64

sqlalchemy-2.0.52-cp39-cp39-win32.whl
 (2.1 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.9Windows x86

sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_x86_64.whl
 (3.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.9musllinux: musl 1.2+ x86-64

sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_aarch64.whl
 (3.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.9musllinux: musl 1.2+ ARM64

sqlalchemy-2.0.52-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.9manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

sqlalchemy-2.0.52-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.9manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

sqlalchemy-2.0.52-cp39-cp39-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.9macOS 11.0+ ARM64

sqlalchemy-2.0.52-cp38-cp38-win_amd64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.8Windows x86-64

sqlalchemy-2.0.52-cp38-cp38-win32.whl
 (2.1 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.8Windows x86

sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.8musllinux: musl 1.2+ x86-64

sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_aarch64.whl
 (3.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.8musllinux: musl 1.2+ ARM64

sqlalchemy-2.0.52-cp38-cp38-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.8manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

sqlalchemy-2.0.52-cp38-cp38-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (3.3 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.8manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

sqlalchemy-2.0.52-cp38-cp38-macosx_11_0_arm64.whl
 (2.2 MB
 view details)

Uploaded
 Aug 11, 2026
 CPython 3.8macOS 11.0+ ARM64

## File details

Details for the file sqlalchemy-2.0.52.tar.gz.

### File metadata

- Download URL: sqlalchemy-2.0.52.tar.gz
- Upload date:
 Aug 11, 2026
- Size: 9.9 MB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.14.0

### File hashes

Hashes for sqlalchemy-2.0.52.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 5e2d46356ac2ccb7d268ab6c2319ac6a2b42f1b8d5fd8bd3d46855cd82abee97 | |
| MD5 | 86199caf75358c41c8834dd305b2ef1e | |
| BLAKE2b-256 | 3b2177b4c147963073040dc3c3a5cb7a8c3001a1893c0209432cb77f9df836aa | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-py3-none-any.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-py3-none-any.whl
- Upload date:
 Aug 11, 2026
- Size: 2.0 MB
- Tags: Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 3b81b8363a919ce53453591cdb93702e6bd54ade6c4fa2f468fc053baee5ed89 | |
| MD5 | 5f59a5f18eddc7258b7a3f07f59ce1f8 | |
| BLAKE2b-256 | b33f3582293d1e185e71d19d7c731c3e2ee20ba21981c4a1115c0806c1f62120 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314t-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314t-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.14t, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314t-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | c1e61d08bdf4ee2f41024569e3400de7d6734ba498144766b11260936ccfa582 | |
| MD5 | 5385b890e46a6d2e63cfeffc03087cb1 | |
| BLAKE2b-256 | dc4be01a737eef378e734cc6394a82248a6ce13b167dfa36c731075ce9fc9c64 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314-win_amd64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314-win_amd64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.14, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | a593db51b3bae75db17a5738ad5f992244b3a03863f83c28117ee482c6a3f76d | |
| MD5 | c46c96cb9d431ded3bd86c86420b4ea7 | |
| BLAKE2b-256 | 96d78ac6ffa1e36169e762ef65bd835046abb2251b1bc17f8f6708e14ed8d31f | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314-win32.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314-win32.whl
- Upload date:
 Aug 11, 2026
- Size: 2.1 MB
- Tags: CPython 3.14, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314-win32.whl
| Algorithm | Hash digest | |
| SHA256 | ab9da41e61b9979b910499d633b241df20c51ee5037e5405b11c2faac3cbe1a2 | |
| MD5 | ae5eb01418da2c110f745c47d43d7705 | |
| BLAKE2b-256 | 456705cf86541c1e1716fca1e4a996954a439cd74501707cda607fb7cb02ef50 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.14, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 49565daf5af554f538e23aef1fc81a95a4e49658f152285e45c02f5fc44f04cd | |
| MD5 | eb84f6f3a3b6904694ec6e24424d524b | |
| BLAKE2b-256 | 35f3ea8933fc9f7d1353e9c2ff9965eae687c4cef181120574591ed2fa0633e1 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.14, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 50bff43b632a56fbf5ed9afdd76307e1512b62051bcd5afb341ae67205bbb6c8 | |
| MD5 | 29db530c6a980ef5597525a226d6242f | |
| BLAKE2b-256 | 13f52cc160590ca49173359557880b92a0572293ccb899e8f6cedf150c5a3ddf | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.14, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 812bae5138bfc0aa46fb0686da0fc7f581f68e2bbb05bc24c3713bebaedd1437 | |
| MD5 | 96572c5d8b8cea10f0c8ff2d899869d2 | |
| BLAKE2b-256 | ae5c290c84c7c2566ecd3b65baaae0fddec9bc33b033b398a06123bb86fbfc6e | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.14, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | dfe9ce533dbe4d0a2ae1486546619bd30b76bcd670539a44d910361376175f5e | |
| MD5 | 4f094bee9e3fc867ea58c199b92bfb92 | |
| BLAKE2b-256 | 4c93d07ebd645d1b07b6b5ed63450a70f063a346a7e0f2c8810daf2e532400cb | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp314-cp314-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp314-cp314-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.14, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp314-cp314-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 410d52be41d17f1a236d19520fbe776257dc16516ed06bd16d433311842aefd9 | |
| MD5 | fe6afd81aa59926c67e65b90e082f571 | |
| BLAKE2b-256 | d5f571cb30af58c9b80a4e1fac0b73bb48f86d497a774a6a2eb6d2f1e657bb73 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp313-cp313-win_amd64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp313-cp313-win_amd64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.13, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp313-cp313-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 9876b09b9f1ce7398b0ffece585c0a911244c53191187341f6bcae640e133751 | |
| MD5 | 485fbfb8cd8c9f8de6dd130297c54a59 | |
| BLAKE2b-256 | 964e226eda27654318ce525d043025221f689abef883da2c7126f9065121618c | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp313-cp313-win32.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp313-cp313-win32.whl
- Upload date:
 Aug 11, 2026
- Size: 2.1 MB
- Tags: CPython 3.13, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp313-cp313-win32.whl
| Algorithm | Hash digest | |
| SHA256 | c63bda077685c85ca513286547a531ba57e7a68cf0a7ed3bafcc2bbd18896f4d | |
| MD5 | 6b75eac557a27f915507de661ebb0455 | |
| BLAKE2b-256 | 6607557c0d04716705599227945ac14e0a17ad0338e899f37d8c2ddff4dcc663 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.13, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | ab66fa9618269390d4dfa222f2f2f88f7bc4bf5da13905131b818217db7e8057 | |
| MD5 | ccda18040bd27f9bcabb4dc5a66d44a2 | |
| BLAKE2b-256 | 51e6074ade0c07b9e4c8e8bca46820320ed94df9702afdb6f2af06623068d2e6 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.13, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp313-cp313-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | b08cddb8989775e3c88799d86704bdfc3ee6e9846118201aa5997f16f27e3a15 | |
| MD5 | 6607b737724abc898b498d1c706fdc8a | |
| BLAKE2b-256 | 8bf7752cc8ee453da222829b3f5c4613614bf750d97429363b70414fa10478e4 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.13, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 651d6d8782e80679e6151707c7b490834d46ada526328895abf567f25e63d29c | |
| MD5 | 4bc1292ab115ec7d1672018cdb3b60f8 | |
| BLAKE2b-256 | cfb88490916e893f3f8d74dc9cc54c078619364999dee37047a188e73abbc852 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.13, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 923bb183c1dc64fdf7b717965e3d59938ec4f8b8710b419a21ce403e5da9a9e1 | |
| MD5 | 50340aded7f836c2952d349a90d8886d | |
| BLAKE2b-256 | d0562e17d161a4f7ecc1c2ffb93e607b4e1898bb551b451b283235acb8f6ce47 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp313-cp313-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp313-cp313-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.13, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp313-cp313-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 2eb3c6a64b1bfe6704777cfd504e7b8ad093a5f3e03ce67663a5e6742f294e43 | |
| MD5 | e216ffdc135a51df710158a7fc9dafb5 | |
| BLAKE2b-256 | 7f18e30c6fe1eca1bf34a39fbdd6066121cc9974c850faf6f349eac563697a26 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp312-cp312-win_amd64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp312-cp312-win_amd64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.12, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp312-cp312-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 2d5e53e36e37129fe0be8b9d08b6e4052c10a963ee6cda56c8c10dcc194b99ca | |
| MD5 | 56035f007551c938f7865a6a87e51902 | |
| BLAKE2b-256 | ed06543dab8ef62d4e9fb96fb31a30c2b8b14a8763bccf48d428294d6b3041c0 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp312-cp312-win32.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp312-cp312-win32.whl
- Upload date:
 Aug 11, 2026
- Size: 2.1 MB
- Tags: CPython 3.12, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp312-cp312-win32.whl
| Algorithm | Hash digest | |
| SHA256 | afda3ec521d0517d0de783fc70030775841900896d832de5bbd066549290470e | |
| MD5 | 2f488e679165b181b41d859298c69a33 | |
| BLAKE2b-256 | 22205c2b4583904af4173076dda1c9e53c9e2ffc7a702d2efde0216bbacbf7cb | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.4 MB
- Tags: CPython 3.12, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | e49f51a5d59857a7a0dcaf9469febf7197d9394bd88f00d69c2c4e848112cdbf | |
| MD5 | 55827f4fb11da062bbeed8be6dc2f30c | |
| BLAKE2b-256 | 020f466bdf9e1feeeef5587f868c187d8687e21ff8c85b1775e9041130181132 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.12, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp312-cp312-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 37a4d548327b6cab9c7d8cdb4e0e82feabee0110c4d150059068e2d1cfbd99ee | |
| MD5 | 51c2f7852e5c439ec11b9e5cec94ce6a | |
| BLAKE2b-256 | 15c32887cf9dd111d1fbf05d22165b404c221ef43e029f7a2695e7302f27a7cc | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.4 MB
- Tags: CPython 3.12, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 8738008376d22f30f411ea3efecf39b51110b6996d80bb73786f30bcfdd5fd3b | |
| MD5 | 89e27a8b06738113aeb303c07789b2ca | |
| BLAKE2b-256 | be572eadf93a552568c57e8680b7e58bb5e9770d80942a1bdbaf4f2f63f0d7c8 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.4 MB
- Tags: CPython 3.12, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 1b2d9e507a458832adcfbd8af6e2036ddf069b7710b799448542ebccae2dceee | |
| MD5 | b83da4cf8765581c8af4cae0a42d1b91 | |
| BLAKE2b-256 | 54bdf444444adb37b5d53753fb1730ee7a421628e2e3b756c4da461af7e6394a | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp312-cp312-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp312-cp312-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.12, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp312-cp312-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | be8c49131665dfe2cc74c498aa1240ffb548d0fd901325dd11c2c7a18956f727 | |
| MD5 | 382f1893151275aae4e015da33b86581 | |
| BLAKE2b-256 | e0d51b77a026d161f98a08f11af1a5f6c47b98ee7c7e2648af525a1004826c78 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp311-cp311-win_amd64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp311-cp311-win_amd64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.11, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp311-cp311-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | f1c850792a3b25a3ad74dade3f05e4f402cdebfea27438bcadafaa1617f77bcc | |
| MD5 | 5bd2dc99a46b44ff20c228d9df8c4240 | |
| BLAKE2b-256 | 7af004d2ac5ad66f3d31278f37064ed5f5ef3fe653f7bdaa67036663f223d186 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp311-cp311-win32.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp311-cp311-win32.whl
- Upload date:
 Aug 11, 2026
- Size: 2.1 MB
- Tags: CPython 3.11, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp311-cp311-win32.whl
| Algorithm | Hash digest | |
| SHA256 | cef328349452ae152637df4d11ce5a0919ecdf0a363e16c830c3518ee33bde72 | |
| MD5 | 74213ded4f93cdb4288c4ef21266df08 | |
| BLAKE2b-256 | c2f10f1b1d4800e51218e736a06ed55a3b2a59c257600bbaca7673bf13d2dbec | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.11, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 4699dbb8d396d199e7e78fd4d525e3ad3d6008a9c8c0160b87e74c606c2c3736 | |
| MD5 | 95e27c96f2f50b4e07dd77ac84680b82 | |
| BLAKE2b-256 | b2ba25ffd5c24681ea4b46e62c80ceca8200ce204de1773366321306cf3f608a | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.11, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.15

### File hashes

Hashes for sqlalchemy-2.0.52-cp311-cp311-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 5f8438a98d49424acf69d0d53c0a522951dfe49a6f2d86417fbb37ad3066ab43 | |
| MD5 | 952c22369b3b44bfba796efdc607bcf0 | |
| BLAKE2b-256 | 1225410fbc6c2f1fa8310f4ef1b6847d47d0ac1c042c7b4e81eaaca063d030a9 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.4 MB
- Tags: CPython 3.11, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 938325a5373267afc53bfbe72983b20fbd64ca47842aac62433c3da1137ecff1 | |
| MD5 | e27a72ab5e54f7dd744a340c87dcb764 | |
| BLAKE2b-256 | a873e75597b5841043e3c74055d00d4feb53d9a49a5c89ba2450d2d9aab53597 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.4 MB
- Tags: CPython 3.11, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.15

### File hashes

Hashes for sqlalchemy-2.0.52-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 7a0d48c4b80717c61385b4e966e087c839a66cfd7b780641dcb428f4dba65608 | |
| MD5 | 9397f09afc38aa274b33be85f265a019 | |
| BLAKE2b-256 | eddc9a2abad8bfc8fdcd38c64adc056aeefab7aaa96ecd32f5e8c140e6375f17 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp311-cp311-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp311-cp311-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.11, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp311-cp311-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | e0c3ce43907374889f3352bdcc6195c970148a2cb71574cd0237a5071a37fb6c | |
| MD5 | bf8cba7c694efa426670976b1c91f829 | |
| BLAKE2b-256 | 6b08cc5f7627b92f1456bc0b5fb7e98af4600248abe422a44da0d17a3fe6a448 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp310-cp310-win_amd64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp310-cp310-win_amd64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.10, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp310-cp310-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 11560064cc4696e772298b6221ede59e646386d9f2a85d549365473b972f7850 | |
| MD5 | 457ead29a9b6accdeca1b5b4ef0cb4d2 | |
| BLAKE2b-256 | b3a1934bb6cf543a398c72784d1fc777eb530559c16ebe1549fa7611e5989ce9 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp310-cp310-win32.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp310-cp310-win32.whl
- Upload date:
 Aug 11, 2026
- Size: 2.1 MB
- Tags: CPython 3.10, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp310-cp310-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 2e15b1d1116a64fc399b8c2694a83f3e792fdc58df28514a81e1dc4f8cf22729 | |
| MD5 | 94bea4557b77f4e1780c3e62a96f84e5 | |
| BLAKE2b-256 | 41f23c9b54b61bec4f493c0007dc9e2700c963c5b32667e21a506f1aca7a8115 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.10, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 9255ceb65a80c1b001129060b63ee776a2e9c288be3b662be36dfbb888fffdcd | |
| MD5 | 612ff1cdca6bbb37c4eccfe346218a0a | |
| BLAKE2b-256 | 7219ab0cb9ccdafa2419c796ae62f8740aedb903f1e93bb326064b1a0147e458 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.2 MB
- Tags: CPython 3.10, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.15

### File hashes

Hashes for sqlalchemy-2.0.52-cp310-cp310-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 2f9eccf8793c8c3f8dd2dfd11b9e400cb27d1d19370ef732b66017e212107822 | |
| MD5 | f92ff4434e9ebd41319262b9669ff812 | |
| BLAKE2b-256 | 5069ce6776724511d1b5dd40477b08d6a5f0953a45375e092dfa852b1857732c | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.10, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 309cc8ba50fc5d2174189dfcd49cdf7aa711f8346afcff19f2642ae4fc449c14 | |
| MD5 | f1934b4733562c846fe33fb1d969ce4e | |
| BLAKE2b-256 | 20055b96afc1407c314347ad006b72bb251fb68ef84d05505ebf8a39bc47fcde | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.10, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.15

### File hashes

Hashes for sqlalchemy-2.0.52-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 6c1b7ed45bf87b214e0a9def9c2313949067efe6269db5ef18d542ee13250af7 | |
| MD5 | ba3ef89405b68248ed442bef1d939915 | |
| BLAKE2b-256 | 5b6498eef682e6946eb1b4195a9a2393db4662ebfcc89f823ae78b938765c3c0 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp310-cp310-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp310-cp310-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.10, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp310-cp310-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | a7438774e1091192fc50a2bd8ceff5c596912d00ecd46587e88effdea7826101 | |
| MD5 | 76c259cbc3f41273357adb40afc5bed2 | |
| BLAKE2b-256 | a6d7e0354e7334d33ea2795db3ecbe2977026c05a1ecf8ba4b5953c329872453 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp39-cp39-win_amd64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp39-cp39-win_amd64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.9, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp39-cp39-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 3c95c3044edddb65e4a2f7194ec52ca5a9736f72d33ca3a6fa4196aedcc689fd | |
| MD5 | f35d6d231946000f7cad7e1a8135b6dd | |
| BLAKE2b-256 | be5c88a50b3ff879c251d8718b83f16a5ee5f246b189d4ad5aaac047e75f97d0 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp39-cp39-win32.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp39-cp39-win32.whl
- Upload date:
 Aug 11, 2026
- Size: 2.1 MB
- Tags: CPython 3.9, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp39-cp39-win32.whl
| Algorithm | Hash digest | |
| SHA256 | de89de5b5798cafdd7ef7b7b804acec246d6152922128fd9d156cd1701271aff | |
| MD5 | df8e466e9d8bec8b98912e093244e77f | |
| BLAKE2b-256 | 6115d255948b182217d3d4e3d14fa15225a6353b07b147f1c1f0c48faae1f63b | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.2 MB
- Tags: CPython 3.9, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | f4d4f7afc682961dc567db70e00a7b5bd81ccd3743c46199b0257f0744902dde | |
| MD5 | 799e836f02b280f986b4cda58a36625d | |
| BLAKE2b-256 | 338e1eb0099caefe62faf416df7288d984ccb3d77335c1ae2a82fa3cc4ed9780 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.2 MB
- Tags: CPython 3.9, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp39-cp39-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 2f5fa2b2aca75d2c7f36db3a8dd04717b6fbfd1a964fb32bdeae16698e475ab3 | |
| MD5 | 851be89328b94de392f71caddf54e140 | |
| BLAKE2b-256 | ef074bd32de2f405e80eaf180ee91a2a932980c9d958e55e4c3513635adb6ca7 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.9, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | cce4922535db73f9dbb91e3db2b3e851ac629467fd1ebd8e354a60e369521c63 | |
| MD5 | d73d7b2567305e83a41c27f6bda84c63 | |
| BLAKE2b-256 | f3c7eb6125b5ec2dceb1625171c2c93e0a591583ce4dc357eba8345252bd2f93 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.9, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 8cf993f065bc04caa5000b339e8d9d6f3d9d00251511f850147c516c9e07115f | |
| MD5 | 1027ebb247db3346e0766b2d653b7952 | |
| BLAKE2b-256 | 67239d53f5155d093e8c95951078e7a8b4301787207ac10e61c1582a50c0e282 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp39-cp39-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp39-cp39-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.9, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp39-cp39-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 4b89e93bb89eabdbea9d5d3fa2d6cc6544e733c33064339f91e5292480cf130e | |
| MD5 | 1b06d975d5d248be13d407da32a04931 | |
| BLAKE2b-256 | 484bc5c0fe0b2d606b34618933f7448ebf93e1aeb60d896149a8061b7ac5bfd9 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp38-cp38-win_amd64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp38-cp38-win_amd64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.8, Windows x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp38-cp38-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 765f439da5bc8696973bc0c8a31fae0912ac3ff1cb9d66246a6b2728ee4fbbc8 | |
| MD5 | 3ab68df9e342776bd468d45cb35757b5 | |
| BLAKE2b-256 | 246325d38c447a521224bb6e497f9f804a8e47d67c62ca28009ff3d4d1ef5cad | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp38-cp38-win32.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp38-cp38-win32.whl
- Upload date:
 Aug 11, 2026
- Size: 2.1 MB
- Tags: CPython 3.8, Windows x86
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp38-cp38-win32.whl
| Algorithm | Hash digest | |
| SHA256 | f2b09029ef6f260409eefa5dc2b8276f6c3d7b892bfb50d50e8f852257d4a6b4 | |
| MD5 | f9766d3d43f9c41ae6f6a17ea2bc703f | |
| BLAKE2b-256 | f71c4cad64319467b8486de78aba6050c1355561d82ca6af5093280a0bcbcac4 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.8, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | df8f213ceb485d8227b74935eb87ba0d80169a8401eba7835da6e30d6727dac4 | |
| MD5 | 92af2714dc1d74cef7a2d0e1d00e7910 | |
| BLAKE2b-256 | daad72fdbbc3aed10dbe7c69199db877ac89cf24bdc79239f54776dc6ff30b75 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.2 MB
- Tags: CPython 3.8, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp38-cp38-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 46f0c46f0d360d727b84660b26c62b295d82306ec2c82b701e97747d2c6dcbe1 | |
| MD5 | 0b376a6e01a72631f0099d0c5296378a | |
| BLAKE2b-256 | 3f6668f71c1d0ac3824f0346da1f82a56d83585b027feca3e7154b36278c9017 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp38-cp38-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp38-cp38-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.8, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp38-cp38-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | cd9206024b8602e7518bbaf44016c29e0045722f09328d8e654941023920d0b3 | |
| MD5 | 4ea16a9ebdf62b265829a687c39eb5e7 | |
| BLAKE2b-256 | ebb71b18e61b7ea4e31f18bd3322f4229cc2a56428fe4aa7fd06dda9a837b775 | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp38-cp38-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp38-cp38-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 11, 2026
- Size: 3.3 MB
- Tags: CPython 3.8, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp38-cp38-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 77a247d3fd179f6583171e7e0e98f40dc6642ed4f655557515a5a7e25923e9a4 | |
| MD5 | f3356e9910b8ee481bb1826c7b01b7cc | |
| BLAKE2b-256 | e99ee6209c158f81275366e6749e2b71e4d82af8b60bc64ba9d123972e86f0cf | |

See more details on using hashes here.

## File details

Details for the file sqlalchemy-2.0.52-cp38-cp38-macosx_11_0_arm64.whl.

### File metadata

- Download URL: sqlalchemy-2.0.52-cp38-cp38-macosx_11_0_arm64.whl
- Upload date:
 Aug 11, 2026
- Size: 2.2 MB
- Tags: CPython 3.8, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for sqlalchemy-2.0.52-cp38-cp38-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 1b92a1e23ed40022081217b40d2d1feba4f77064e69ef4f39f68bcbbd148452a | |
| MD5 | 8119a7d26db7f5282c304921b913147a | |
| BLAKE2b-256 | 6a8380181b4acdacbe5103062dcadf80ac3175fcff32e674c8da5eac5316d839 | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

Pre-release

2.1.0b3

Jun 27, 2026
 62 files

Pre-release

2.1.0b2

Apr 16, 2026
 70 files

Pre-release

2.1.0b1

Jan 21, 2026
 42 files

This release

2.0.52 This release

Aug 11, 2026
 52 files

2.0.51

Jun 15, 2026
 58 files

2.0.50

May 24, 2026
 58 files

2.0.49

Apr 3, 2026
 63 files

2.0.48

Mar 2, 2026
 63 files

2.0.47

Feb 24, 2026
 63 files

2.0.46

Jan 21, 2026
 59 files

2.0.45

Dec 9, 2025
 52 files

2.0.44

Oct 10, 2025
 57 files

2.0.43

Aug 11, 2025
 57 files

2.0.42

Jul 29, 2025
 57 files

2.0.41

May 14, 2025
 57 files

2.0.40

Mar 27, 2025
 57 files

2.0.39

Mar 11, 2025
 57 files

2.0.38

Feb 6, 2025
 57 files

2.0.37

Jan 9, 2025
 57 files

2.0.36

Oct 15, 2024
 57 files

2.0.35

Sep 16, 2024
 49 files

2.0.34

Sep 4, 2024
 49 files

2.0.33

Sep 3, 2024
 49 files

2.0.32

Aug 5, 2024
 49 files

2.0.31

Jun 18, 2024
 49 files

2.0.30

May 5, 2024
 49 files

2.0.29

Mar 23, 2024
 49 files

2.0.28

Mar 4, 2024
 49 files

2.0.27

Feb 13, 2024
 49 files

2.0.26

Feb 11, 2024
 49 files

2.0.25

Jan 3, 2024
 49 files

2.0.24

Dec 28, 2023
 49 files

2.0.23

Nov 2, 2023
 49 files

2.0.22

Oct 12, 2023
 49 files

2.0.21

Sep 18, 2023
 49 files

2.0.20

Aug 15, 2023
 41 files

2.0.19

Jul 15, 2023
 41 files

2.0.18

Jul 5, 2023
 41 files

2.0.17

Jun 23, 2023
 41 files

2.0.16

Jun 10, 2023
 41 files

2.0.15

May 20, 2023
 41 files

2.0.14

May 18, 2023
 41 files

2.0.13

May 10, 2023
 41 files

2.0.12

Apr 30, 2023
 41 files

2.0.11

Apr 27, 2023
 41 files

2.0.10

Apr 21, 2023
 41 files

2.0.9

Apr 5, 2023
 41 files

2.0.8

Mar 31, 2023
 41 files

2.0.7

Mar 18, 2023
 41 files

2.0.6

Mar 13, 2023
 41 files

2.0.5.post1

Mar 6, 2023
 41 files

Yanked

2.0.5

Mar 6, 2023
 2 files

2.0.4

Feb 17, 2023
 41 files

2.0.3

Feb 10, 2023
 41 files

2.0.2

Feb 7, 2023
 41 files

2.0.1

Feb 1, 2023
 41 files

2.0.0

Jan 26, 2023
 41 files

Pre-release

2.0.0rc3

Jan 19, 2023
 41 files

Pre-release

2.0.0rc2

Jan 9, 2023
 41 files

Pre-release

2.0.0rc1

Dec 28, 2022
 41 files

Pre-release

2.0.0b4

Dec 5, 2022
 41 files

Pre-release

2.0.0b3

Nov 4, 2022
 41 files

Pre-release

2.0.0b2

Oct 20, 2022
 31 files

Pre-release

2.0.0b1

Oct 13, 2022
 41 files

1.4.54

Sep 5, 2024
 44 files

1.4.53

Jul 29, 2024
 44 files

1.4.52

Mar 4, 2024
 46 files

1.4.51

Jan 3, 2024
 46 files

1.4.50

Oct 29, 2023
 46 files

1.4.49

Jul 5, 2023
 48 files

1.4.48

Apr 30, 2023
 41 files

1.4.47

Mar 18, 2023
 41 files

1.4.46

Jan 3, 2023
 41 files

1.4.45

Dec 10, 2022
 41 files

1.4.44

Nov 12, 2022
 41 files

1.4.43

Nov 4, 2022
 41 files

1.4.42

Oct 16, 2022
 41 files

1.4.41

Sep 7, 2022
 41 files

1.4.40

Aug 8, 2022
 36 files

1.4.39

Jun 24, 2022
 36 files

1.4.38

Jun 23, 2022
 35 files

1.4.37

May 31, 2022
 36 files

1.4.36

Apr 26, 2022
 36 files

1.4.35

Apr 6, 2022
 36 files

Yanked

1.4.34

Mar 31, 2022
 36 files

Yanked

1.4.33

Mar 31, 2022
 36 files

1.4.32

Mar 6, 2022
 35 files

1.4.31

Jan 21, 2022
 36 files

1.4.30

Jan 19, 2022
 36 files

1.4.29

Dec 23, 2021
 36 files

1.4.28

Dec 9, 2021
 35 files

1.4.27

Nov 11, 2021
 36 files

1.4.26

Oct 19, 2021
 36 files

1.4.25

Sep 23, 2021
 30 files

1.4.24

Sep 22, 2021
 30 files

1.4.23

Aug 18, 2021
 30 files

1.4.22

Jul 22, 2021
 30 files

1.4.21

Jul 14, 2021
 30 files

1.4.20

Jun 28, 2021
 30 files

1.4.19

Jun 23, 2021
 30 files

1.4.18

Jun 10, 2021
 30 files

1.4.17

May 29, 2021
 30 files

1.4.16

May 28, 2021
 30 files

1.4.15

May 11, 2021
 30 files

1.4.14

May 6, 2021
 30 files

1.4.13

May 3, 2021
 34 files

1.4.12

Apr 29, 2021
 34 files

1.4.11

Apr 22, 2021
 34 files

1.4.10

Apr 21, 2021
 34 files

1.4.9

Apr 17, 2021
 34 files

1.4.8

Apr 15, 2021
 34 files

1.4.7

Apr 9, 2021
 34 files

1.4.6

Apr 6, 2021
 34 files

1.4.5

Apr 2, 2021
 34 files

1.4.4

Mar 31, 2021
 34 files

1.4.3

Mar 25, 2021
 34 files

1.4.2

Mar 19, 2021
 34 files

1.4.1

Mar 17, 2021
 34 files

1.4.0

Mar 15, 2021
 34 files

Pre-release

1.4.0b3

Feb 15, 2021
 28 files

Pre-release

1.4.0b2

Feb 3, 2021
 32 files

Pre-release

1.4.0b1

Nov 2, 2020
 32 files

1.3.24

Mar 30, 2021
 34 files

1.3.23

Feb 1, 2021
 38 files

1.3.22

Dec 18, 2020
 38 files

1.3.21

Dec 17, 2020
 38 files

1.3.20

Oct 12, 2020
 38 files

1.3.19

Aug 17, 2020
 32 files

1.3.18

Jun 25, 2020
 28 files

1.3.17

May 13, 2020
 28 files

1.3.16

Apr 8, 2020
 19 files

1.3.15

Mar 11, 2020
 1 file

1.3.14

Mar 10, 2020
 1 file

1.3.13

Jan 22, 2020
 1 file

1.3.12

Dec 16, 2019
 1 file

1.3.11

Nov 11, 2019
 1 file

1.3.10

Oct 10, 2019
 1 file

1.3.9

Oct 4, 2019
 1 file

1.3.8

Aug 27, 2019
 1 file

1.3.7

Aug 14, 2019
 1 file

1.3.6

Jul 21, 2019
 1 file

1.3.5

Jun 17, 2019
 1 file

1.3.4

May 28, 2019
 1 file

1.3.3

Apr 15, 2019
 1 file

1.3.2

Apr 2, 2019
 1 file

1.3.1

Mar 9, 2019
 1 file

1.3.0

Mar 4, 2019
 1 file

Pre-release

1.3.0b3

Feb 8, 2019
 1 file

Pre-release

1.3.0b2

Jan 26, 2019
 1 file

Pre-release

1.3.0b1

Nov 17, 2018
 1 file

1.2.19

Apr 15, 2019
 1 file

1.2.18

Feb 15, 2019
 1 file

1.2.17

Jan 26, 2019
 1 file

1.2.16

Jan 11, 2019
 1 file

1.2.15

Dec 11, 2018
 1 file

1.2.14

Nov 10, 2018
 1 file

1.2.13

Oct 31, 2018
 1 file

1.2.12

Sep 19, 2018
 1 file

1.2.11

Aug 20, 2018
 1 file

1.2.10

Jul 13, 2018
 1 file

1.2.9

Jun 29, 2018
 1 file

1.2.8

May 28, 2018
 1 file

1.2.7

Apr 20, 2018
 1 file

1.2.6

Mar 30, 2018
 1 file

1.2.5

Mar 6, 2018
 1 file

1.2.4

Feb 22, 2018
 1 file

1.2.3

Feb 16, 2018
 1 file

1.2.2

Jan 25, 2018
 1 file

1.2.1

Jan 15, 2018
 1 file

1.2.0

Dec 27, 2017
 1 file

Pre-release

1.2.0b3

Oct 13, 2017
 1 file

Pre-release

1.2.0b2

Jul 24, 2017
 1 file

Pre-release

1.2.0b1

Jul 10, 2017
 1 file

1.1.18

Mar 6, 2018
 1 file

1.1.17

Feb 22, 2018
 1 file

1.1.16

Feb 16, 2018
 1 file

1.1.15

Nov 3, 2017
 1 file

1.1.14

Sep 5, 2017
 1 file

1.1.13

Aug 3, 2017
 1 file

1.1.12

Jul 24, 2017
 1 file

1.1.11

Jun 19, 2017
 1 file

1.1.10

May 19, 2017
 1 file

1.1.9

Apr 4, 2017
 1 file

1.1.8

Mar 31, 2017
 1 file

1.1.7

Mar 27, 2017
 1 file

1.1.6

Feb 28, 2017
 1 file

1.1.5

Jan 17, 2017
 1 file

1.1.4

Nov 15, 2016
 1 file

1.1.3

Oct 27, 2016
 1 file

1.1.2

Oct 17, 2016
 1 file

1.1.1

Oct 7, 2016
 1 file

1.1.0

Oct 5, 2016
 1 file

Pre-release

1.1.0b3

Jul 26, 2016
 1 file

Pre-release

1.1.0b2

Jul 1, 2016
 1 file

Pre-release

1.1.0b1

Jun 16, 2016
 1 file

1.0.19

Aug 3, 2017
 1 file

1.0.18

Jul 24, 2017
 1 file

1.0.17

Jan 17, 2017
 1 file

1.0.16

Nov 15, 2016
 1 file

1.0.15

Sep 1, 2016
 1 file

1.0.14

Jul 6, 2016
 1 file

1.0.13

May 16, 2016
 1 file

1.0.12

Feb 15, 2016
 1 file

1.0.11

Dec 23, 2015
 1 file

1.0.10

Dec 11, 2015
 1 file

1.0.9

Oct 20, 2015
 1 file

1.0.8

Jul 23, 2015
 1 file

1.0.7

Jul 20, 2015
 1 file

1.0.6

Jun 25, 2015
 1 file

1.0.5

Jun 7, 2015
 1 file

1.0.4

May 8, 2015
 1 file

1.0.3

May 1, 2015
 1 file

1.0.2

Apr 24, 2015
 1 file

1.0.1

Apr 23, 2015
 1 file

1.0.0

Apr 16, 2015
 1 file

Pre-release

1.0.0b5

Apr 3, 2015
 1 file

Pre-release

1.0.0b4

Mar 29, 2015
 1 file

Pre-release

1.0.0b3

Mar 20, 2015
 1 file

Pre-release

1.0.0b2

Mar 20, 2015
 1 file

Pre-release

1.0.0b1

Mar 13, 2015
 1 file

0.9.10

Jul 22, 2015
 1 file

0.9.9

Mar 10, 2015
 1 file

0.9.8

Oct 13, 2014
 1 file

0.9.7

Jul 22, 2014
 1 file

0.9.6

Jun 23, 2014
 1 file

0.9.5

Jun 23, 2014
 1 file

0.9.4

Mar 28, 2014
 1 file

0.9.3

Feb 20, 2014
 1 file

0.9.2

Feb 3, 2014
 1 file

0.9.1

Jan 6, 2014
 1 file

0.9.0

Dec 30, 2013
 1 file

0.8.7

Jul 22, 2014
 1 file

0.8.6

Mar 28, 2014
 1 file

0.8.5

Feb 20, 2014
 1 file

0.8.4

Dec 8, 2013
 1 file

0.8.3

Oct 26, 2013
 1 file

0.8.2

Jul 3, 2013
 1 file

0.8.1

Apr 27, 2013
 1 file

0.8.0

Mar 10, 2013
 1 file

Pre-release

0.8.0b2

Dec 14, 2012
 1 file

0.7.10

Feb 8, 2013
 1 file

0.7.9

Oct 2, 2012
 1 file

0.7.8

Jun 17, 2012
 1 file

0.7.7

May 5, 2012
 1 file

0.7.6

Mar 15, 2012
 1 file

0.7.5

Jan 28, 2012
 1 file

0.7.4

Dec 9, 2011
 1 file

0.7.3

Oct 16, 2011
 1 file

0.7.2

Jul 31, 2011
 1 file

0.7.1

Jun 5, 2011
 1 file

0.7.0

May 20, 2011
 1 file

0.6.9

May 5, 2012
 1 file

0.6.8

Jun 5, 2011
 1 file

0.6.7

Apr 14, 2011
 1 file

0.6.6

Jan 8, 2011
 1 file

0.6.5

Oct 24, 2010
 1 file

0.6.4

Sep 7, 2010
 1 file

0.6.3

Jul 15, 2010
 1 file

0.6.2

Jul 6, 2010
 1 file

0.6.1

May 31, 2010
 1 file

0.6.0

Apr 18, 2010
 1 file

Pre-release

0.6beta3

Mar 28, 2010
 1 file

Pre-release

0.6beta2

Mar 20, 2010
 1 file

Pre-release

0.6beta1

Feb 3, 2010
 1 file

0.5.8

Jan 16, 2010
 1 file

0.5.7

Dec 26, 2009
 1 file

0.5.6

Sep 13, 2009
 1 file

0.5.5

Jul 13, 2009
 1 file

0.5.4

May 17, 2009
 1 file

0.5.3

Mar 25, 2009
 1 file

0.5.2

Jan 24, 2009
 1 file

0.5.1

Jan 17, 2009
 1 file

0.5.0

Jan 6, 2009
 1 file

Pre-release

0.5.0rc4

Nov 14, 2008
 1 file

Pre-release

0.5.0rc3

Nov 7, 2008
 1 file

Pre-release

0.5.0rc2

Oct 12, 2008
 1 file

Pre-release

0.5.0rc1

Sep 11, 2008
 1 file

Pre-release

0.5.0beta3

Aug 4, 2008
 1 file

Pre-release

0.5.0beta2

Jul 14, 2008
 1 file

Pre-release

0.5.0beta1

Jun 12, 2008
 1 file

0.4.8

Oct 12, 2008
 1 file

0.4.7

Jul 26, 2008
 1 file

0.4.6

May 14, 2008
 1 file

0.4.5

Apr 4, 2008
 1 file

0.4.4

Mar 12, 2008
 2 files

0.4.3

Feb 14, 2008
 1 file

0.4.2

Jan 2, 2008
 1 file

Pre-release

0.4.2b

Jan 7, 2008
 1 file

Pre-release

0.4.2a

Jan 5, 2008
 1 file

0.4.1

Nov 18, 2007
 1 file

0.4.0

Oct 17, 2007
 1 file

Pre-release

0.4.0beta6

Sep 27, 2007
 1 file

Pre-release

0.4.0beta5

Sep 2, 2007
 1 file

Pre-release

0.4.0beta4

Aug 22, 2007
 1 file

Pre-release

0.4.0beta3

Aug 16, 2007
 1 file

Pre-release

0.4.0beta2

Aug 14, 2007
 1 file

Pre-release

0.4.0beta1

Aug 12, 2007
 1 file

0.3.11

Oct 14, 2007
 1 file

0.3.10

Jul 20, 2007
 1 file

0.3.9

Jul 15, 2007
 1 file

0.3.8

Jun 2, 2007
 1 file

0.3.7

Apr 30, 2007
 1 file

0.3.6

Mar 23, 2007
 1 file

0.3.5

Feb 22, 2007
 1 file

0.3.4

Jan 23, 2007
 1 file

0.3.3

Dec 15, 2006
 1 file

0.3.2

Dec 10, 2006
 1 file

0.3.1

Nov 12, 2006
 1 file

0.3.0

Oct 22, 2006
 1 file

0.2.8

Sep 5, 2006
 1 file

0.2.7

Aug 13, 2006
 1 file

0.2.6

Jul 20, 2006
 1 file

0.2.5

Jul 8, 2006
 1 file

0.2.4

Jun 28, 2006
 1 file

0.2.3

Jun 17, 2006
 1 file

0.2.2

Jun 5, 2006
 1 file

0.2.1

May 29, 2006
 1 file

0.2.0

May 27, 2006
 1 file

0.1.7

May 5, 2006
 1 file

0.1.6

Apr 12, 2006
 1 file

0.1.5

Mar 27, 2006
 1 file

0.1.4

Mar 13, 2006
 2 files

0.1.3

Mar 2, 2006
 2 files

0.1.2

Feb 24, 2006
 2 files

0.1.1

Feb 23, 2006
 2 files

0.1.0

Feb 14, 2006
 1 file