[image: https://github.com/eliben/pycparser/workflows/pycparser-tests/badge.svg]

---

## 1Introduction

### 1.1What is pycparser?

pycparser is a parser for the C language, written in pure Python. It is a
module designed to be easily integrated into applications that need to parse
C source code.

### 1.2What is it good for?

Anything that needs C code to be parsed. The following are some uses for
pycparser, taken from real user reports:

- C code obfuscator
- Front-end for various specialized C compilers
- Static code checker
- Automatic unit-test discovery
- Adding specialized extensions to the C language

One of the most popular uses of pycparser is in the cffi library, which uses it to parse the
declarations of C functions and types in order to auto-generate FFIs.

pycparser is unique in the sense that it’s written in pure Python - a very
high level language that’s easy to experiment with and tweak. To people familiar
with Lex and Yacc, pycparser’s code will be simple to understand. It also
has no external dependencies (except for a Python interpreter), making it very
simple to install and deploy.

### 1.3Which version of C does pycparser support?

pycparser aims to support the full C99 language (according to the standard
ISO/IEC 9899). Some features from C11 are also supported, and patches to support
more are welcome.

pycparser supports very few GCC extensions, but it’s fairly easy to set
things up so that it parses code with a lot of GCC-isms successfully. See the
FAQ for more details.

### 1.4What grammar does pycparser follow?

pycparser very closely follows the C grammar provided in Annex A of the C99
standard (ISO/IEC 9899).

### 1.5How is pycparser licensed?

BSD license.

### 1.6Contact details

For reporting problems with pycparser or submitting feature requests, please
open an issue, or submit a
pull request.

## 2Installing

### 2.1Prerequisites

pycparser is being tested with modern versions of Python on
Linux, macOS and Windows. See the CI dashboard
for details.

pycparser has no external dependencies.

### 2.2Installation process

The recommended way to install pycparser is with pip:

```
> pip install pycparser
```

## 3Using

### 3.1Interaction with the C preprocessor

In order to be compilable, C code must be preprocessed by the C preprocessor -
cpp. A compatible cpp handles preprocessing directives like #include and
#define, removes comments, and performs other minor tasks that prepare the C
code for compilation.

For all but the most trivial snippets of C code pycparser, like a C
compiler, must receive preprocessed C code in order to function correctly. If
you import the top-level parse_file function from the pycparser package,
it will interact with cpp for you, as long as it’s in your PATH, or you
provide a path to it.

Note also that you can use gcc -E or clang -E instead of cpp. See
the using_gcc_E_libc.py example for more details. Windows users can download
and install a binary build of Clang for Windows from this website.

### 3.2What about the standard C library headers?

C code almost always #includes various header files from the standard C
library, like stdio.h. While (with some effort) pycparser can be made to
parse the standard headers from any C compiler, it’s much simpler to use the
provided “fake” standard includes for C11 in utils/fake_libc_include. These
are standard C header files that contain only the bare necessities to allow
valid parsing of the files that use them. As a bonus, since they’re minimal, it
can significantly improve the performance of parsing large C files.

The key point to understand here is that pycparser doesn’t really care about
the semantics of types. It only needs to know whether some token encountered in
the source is a previously defined type. This is essential in order to be able
to parse C correctly.

See this blog post
for more details.

Note that the fake headers are not included in the pip package nor installed
via the package build (#224).

### 3.3Basic usage

Take a look at the examples directory of the distribution for a few examples
of using pycparser. These should be enough to get you started. Please note
that most realistic C code samples would require running the C preprocessor
before passing the code to pycparser; see the previous sections for more
details.

### 3.4Advanced usage

The public interface of pycparser is well documented with comments in
pycparser/c_parser.py. For a detailed overview of the various AST nodes
created by the parser, see pycparser/_c_ast.cfg.

There’s also a FAQ available here.
In any case, you can always drop me an email for help.

## 4Modifying

There are a few points to keep in mind when modifying pycparser:

- The code for pycparser’s AST nodes is automatically generated from a
configuration file - _c_ast.cfg, by _ast_gen.py. If you modify the AST
configuration, make sure to re-generate the code. This can be done by running
the _ast_gen.py script (from the repository root or the
pycparser directory).
- Read the docstring in the constructor of the CParser class for details
on configuration and compatibility arguments.

## 5Package contents

Once you unzip the pycparser package, you’ll see the following files and
directories:

README.rst:

This README file.

LICENSE:

The pycparser license

setup.py:

Legacy installation script (build metadata lives in pyproject.toml).

pyproject.toml:

Package metadata and build configuration.

examples/:

A directory with some examples of using pycparser

pycparser/:

The pycparser module source code.

tests/:

Unit tests.

utils/fake_libc_include:

Minimal standard C library include files that should allow to parse any C code.
Note that these headers now include C11 code, so they may not work when the
preprocessor is configured to an earlier C standard (like -std=c99).

utils/internal/:

Internal utilities for my own use. You probably don’t need them.

## 6Contributors

Some people have contributed to pycparser by opening issues on bugs they’ve
found and/or submitting patches. The list of contributors is in the CONTRIBUTORS
file in the source distribution. After pycparser moved to Github I stopped
updating this list because Github does a much better job at tracking
contributions.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

pycparser-3.0.tar.gz
 (103.5 kB
 view details)

Uploaded
 Jan 21, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

pycparser-3.0-py3-none-any.whl
 (48.2 kB
 view details)

Uploaded
 Jan 21, 2026
 Python 3

## File details

Details for the file pycparser-3.0.tar.gz.

### File metadata

- Download URL: pycparser-3.0.tar.gz
- Upload date:
 Jan 21, 2026
- Size: 103.5 kB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: uv/0.5.13

### File hashes

Hashes for pycparser-3.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 600f49d217304a5902ac3c37e1281c9fe94e4d0489de643a9504c5cdfdfc6b29 | |
| MD5 | 56f3a0a82595b0cb04976cc0d3271a27 | |
| BLAKE2b-256 | 1b7d92392ff7815c21062bea51aa7b87d45576f649f16458d78b7cf94b9ab2e6 | |

See more details on using hashes here.

## File details

Details for the file pycparser-3.0-py3-none-any.whl.

### File metadata

- Download URL: pycparser-3.0-py3-none-any.whl
- Upload date:
 Jan 21, 2026
- Size: 48.2 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: uv/0.5.13

### File hashes

Hashes for pycparser-3.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | b727414169a36b7d524c1c3e31839a521725078d7b2ff038656844266160a992 | |
| MD5 | dfc689e63af0e21be54c80938cc8ac46 | |
| BLAKE2b-256 | 0cc344f3fbbfa403ea2a7c779186dc20772604442dde72947e7d01069cbe98e3 | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

This release

3.0 This release

Jan 21, 2026
 2 files

2.23

Sep 9, 2025
 2 files

2.22

Mar 30, 2024
 2 files

2.21

Nov 6, 2021
 2 files

2.20

Mar 4, 2020
 2 files

2.19

Sep 19, 2018
 1 file

2.18

Jul 4, 2017
 1 file

2.17

Oct 29, 2016
 1 file

2.16

Oct 18, 2016
 1 file

2.15

Oct 18, 2016
 1 file

2.14

Jun 10, 2015
 1 file

2.13

May 12, 2015
 1 file

2.12

Apr 22, 2015
 1 file

2.11

Apr 21, 2015
 1 file

2.10

Aug 3, 2013
 1 file

2.09.1

Dec 29, 2012
 1 file

2.09

Dec 27, 2012
 1 file

2.08

Aug 15, 2012
 1 file

2.07

Jun 16, 2012
 1 file

2.06

Feb 4, 2012
 1 file

2.05

Oct 16, 2011
 1 file

2.04

May 21, 2011
 1 file

2.03

Mar 7, 2011
 1 file

2.02

Feb 18, 2011
 1 file