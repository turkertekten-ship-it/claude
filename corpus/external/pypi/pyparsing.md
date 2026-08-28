---
date: 2026-01-21T03:57:55+0000
source: https://pypi.org/project/pyparsing/
---
## PyParsing – A Python Parsing Module

[image: Version] [image: Build Status] [image: Coverage] [image: License] [image: Python versions] [image: pyparsing]

## Introduction

The pyparsing module is an alternative approach to creating and
executing simple grammars, vs. the traditional lex/yacc approach, or the
use of regular expressions. The pyparsing module provides a library of
classes that client code uses to construct the grammar directly in
Python code.

[Since first writing this description of pyparsing in late 2003, this
technique for developing parsers has become more widespread, under the
name Parsing Expression Grammars - PEGs. See more information on PEGs here .]

Here is a program to parse "Hello, World!" (or any greeting of the form
"salutation, addressee!"):

```
from pyparsing import Word, alphas
greet = Word(alphas) + "," + Word(alphas) + "!"
hello = "Hello, World!"
print(hello, "->", greet.parse_string(hello))
```

The program outputs the following:

```
Hello, World! -> ['Hello', ',', 'World', '!']
```

The Python representation of the grammar is quite readable, owing to the
self-explanatory class names, and the use of ‘+’, ‘|’ and ‘^’ operator
definitions.

The parsed results returned from parse_string() is a collection of type
ParseResults, which can be accessed as a
nested list, a dictionary, or an object with named attributes.

The pyparsing module handles some of the problems that are typically
vexing when writing text parsers:

- extra or missing whitespace (the above program will also handle "Hello,World!", "Hello , World !", etc.)
- quoted strings
- embedded comments

The examples directory includes a simple SQL parser, simple CORBA IDL
parser, a config file parser, a chemical formula parser, and a four-
function algebraic notation parser, among many others.

## Documentation

There are many examples in the online docstrings of the classes
and methods in pyparsing. You can find them compiled into online docs. Additional
documentation resources and project info are listed in the online
GitHub wiki. An
entire directory of examples can be found here.

## AI Instructions

There are also instructions for AI agents to use when helping you to create your parser. They can
be pulled from the GitHub project repository, at pyparsing/ai/best_practices.md. You can also tell
the AI to access them programmatically after installing pyparsing, either from the CLI with
python -m pyparsing.ai.show_best_practices or within python with
import pyparsing; pyparsing.show_best_practices().

## License

MIT License. See header of the pyparsing __init__.py file.

## History

See CHANGES file.

## Performance benchmarks

For usage instructions and details on the performance benchmark suite, see
tests/README.md in this repository.
