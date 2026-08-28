---
date: 2025-11-05T18:37:53+0000
source: https://pypi.org/project/brotli/
---
[image: GitHub Actions Build Status] [image: Fuzzing Status]

[image: Brotli]

### Introduction

Brotli is a generic-purpose lossless compression algorithm that compresses data
using a combination of a modern variant of the LZ77 algorithm, Huffman coding
and 2nd order context modeling, with a compression ratio comparable to the best
currently available general-purpose compression methods. It is similar in speed
with deflate but offers more dense compression.

The specification of the Brotli Compressed Data Format is defined in
RFC 7932.

Brotli is open-sourced under the MIT License, see the LICENSE file.

> Please note: brotli is a "stream" format; it does not contain
> meta-information, like checksums or uncompressed data length. It is possible
> to modify "raw" ranges of the compressed stream and the decoder will not
> notice that.

### Installation

In most Linux distributions, installing brotli is just a matter of using
the package management system. For example in Debian-based distributions:
apt install brotli will install brotli. On MacOS, you can use
Homebrew: brew install brotli.

[image: brotli packaging status]

Of course you can also build brotli from sources.

### Build instructions

#### Vcpkg

You can download and install brotli using the
vcpkg dependency manager:

```
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
./bootstrap-vcpkg.sh
./vcpkg integrate install
./vcpkg install brotli
```

The brotli port in vcpkg is kept up to date by Microsoft team members and
community contributors. If the version is out of date, please create an issue
or pull request on the vcpkg repository.

#### Bazel

See Bazel

#### CMake

The basic commands to build and install brotli are:

```
$ mkdir out && cd out
$ cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=./installed ..
$ cmake --build . --config Release --target install
```

You can use other CMake configuration.

#### Python

To install the latest release of the Python module, run the following:

```
$ pip install brotli
```

To install the tip-of-the-tree version, run:

```
$ pip install --upgrade git+https://github.com/google/brotli
```

See the Python readme for more details on installing
from source, development, and testing.

### Contributing

We glad to answer/library related questions in
brotli mailing list.

Regular issues / feature requests should be reported in
issue tracker.

For reporting vulnerability please read SECURITY.

For contributing changes please read CONTRIBUTING.

### Benchmarks

- Squash Compression Benchmark / Unstable Squash Compression Benchmark
- Large Text Compression Benchmark
- Lzturbo Benchmark

### Related projects

> Disclaimer: Brotli authors take no responsibility for the third party projects mentioned in this section.

Independent decoder implementation
by Mark Adler, based entirely on format specification.

JavaScript port of brotli decoder.
Could be used directly via npm install brotli

Hand ported decoder / encoder
in haxe by Dominik Homberger.
Output source code: JavaScript, PHP, Python, Java and C#

7Zip plugin

Dart compression framework with
fast FFI-based Brotli implementation
with ready-to-use prebuilt binaries for Win/Linux/Mac
