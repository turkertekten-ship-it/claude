---
date: 2026-08-01T20:40:24+0000
source: https://pypi.org/project/cbor2/
---
[image: Testing Status] [image: Publish Status] [image: Code Coverage] [image: Documentation Status] [image: Tidelift]

## About

This library provides encoding and decoding for the Concise Binary Object Representation (CBOR)
(RFC 8949) serialization format. The specification is fully compatible with the original RFC
7049. Read the docs to learn more.

It is implemented in Rust.

### Features

- Simple API like the json or pickle modules
- Support many CBOR tags with stdlib objects
- Generic tag decoding
- Shared value references including cyclic references
- String references compact encoding with repeated strings replaced with indices
- Extensible tagged value handling using tag_hook and object_hook on decode and
default on encode.
- Command-line diagnostic tool, converting CBOR file or stream to JSON python -m cbor2.tool
(This is a lossy conversion, for diagnostics only)
- Thorough test suite (Tested on big- and little-endian architectures)

## Installation

The simplest way to install the library is with pip:

```
pip install cbor2
```

If this fails, see the next section.

### Build requirements

If you wish to compile the code yourself, or are installing on a yet unsupported Python version
or platform where there are no wheels available, you need the following pre-requisites:

- Python >= 3.10 (or PyPy3 3.11+)
- Rust toolchain (tested with v1.93.0)

## Usage

Basic Usage

## Command-line Usage

The provided command line tool (cbor2) converts CBOR data in raw binary or base64
encoding into a representation that allows printing as JSON. This is a lossy
transformation as each datatype is converted into something that can be represented as a
JSON value.

The tool can alternatively be invoked with python -m cbor2.tool.

Usage:

```
# Pass hexadecimal through xxd.
$ echo a16568656c6c6f65776f726c64 | xxd -r -ps | cbor2 --pretty
{
    "hello": "world"
}
# Decode Base64 directly
$ echo ggEC | python -m cbor2.tool --decode
[1, 2]
# Read from a file encoded in Base64
$ python -m cbor2.tool -d tests/examples.cbor.b64
{...}
```

It can be used in a pipeline with json processing tools like jq to allow syntax
coloring, field extraction and more.

CBOR data items concatenated into a sequence can be decoded also:

```
$ echo ggECggMEggUG | cbor2 -d --sequence
[1, 2]
[3, 4]
[5, 6]
```

Multiple files can also be sent to a single output file:

```
$ cbor2 -o all_files.json file1.cbor file2.cbor ... fileN.cbor
```

## Security

This library has not been tested against malicious input. In theory it should be
as safe as JSON, since unlike pickle the decoder does not execute any code.
