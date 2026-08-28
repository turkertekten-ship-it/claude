---
date: 2025-11-03T13:01:24+0000
source: https://pypi.org/project/lz4/
---
## Status

 [image: Build Status] [image: Documentation] [image: CodeCov]

## Introduction

This package provides python bindings for the LZ4 compression library.

The production ready bindings provided in this package cover the frame format, and the
block format
specifications. The frame format bindings are the recommended ones to use, as
this guarantees interoperability with other implementations and language
bindings.

Experimental bindings for the the streaming format
specification are also included, but further work on those is required.

The API provided by the frame format bindings follows that of the LZMA, zlib,
gzip and bzip2 compression libraries which are provided with the Python standard
library. As such, these LZ4 bindings should provide a drop-in alternative to the
compression libraries shipped with Python. The package provides context managers
and file handler support.

The bindings drop the GIL when calling in to the underlying LZ4 library, and is
thread safe. An extensive test suite is included.

## Documentation

 [image: Documentation]

Full documentation is included with the project. The documentation is
generated using Sphinx. Documentation is also hosted on readthedocs.

master:

http://python-lz4.readthedocs.io/en/stable/

development:

http://python-lz4.readthedocs.io/en/latest/

## Homepage

The project homepage is hosted
on Github. Please report any issues you find using the issue tracker.

## Licensing

Code specific to this project is covered by the BSD 3-Clause License
