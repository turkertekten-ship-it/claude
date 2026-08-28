---
date: 2023-03-10T12:50:17+0000
source: https://pypi.org/project/strictyaml/
---
# StrictYAML

StrictYAML is a type-safe YAML parser
that parses and validates a restricted subset of the YAML
specification.

Priorities:

- Beautiful API
- Refusing to parse the ugly, hard to read and insecure features of YAML like the Norway problem.
- Strict validation of markup and straightforward type casting.
- Clear, readable exceptions with code snippets and line numbers.
- Acting as a near-drop in replacement for pyyaml, ruamel.yaml or poyo.
- Ability to read in YAML, make changes and write it out again with comments preserved.
- Not speed, currently.

Simple example:

```
# All about the character
name: Ford Prefect
age: 42
possessions:
- Towel
```

```
from strictyaml import load, Map, Str, Int, Seq, YAMLError
```

Default parse result:

```
>>> load(yaml_snippet)
YAML({'name': 'Ford Prefect', 'age': '42', 'possessions': ['Towel']})
```

All data is string, list or OrderedDict:

```
>>> load(yaml_snippet).data
{'name': 'Ford Prefect', 'age': '42', 'possessions': ['Towel']}
```

Quickstart with schema:

```
from strictyaml import load, Map, Str, Int, Seq, YAMLError

schema = Map({"name": Str(), "age": Int(), "possessions": Seq(Str())})
```

42 is now parsed as an integer:

```
>>> person = load(yaml_snippet, schema)
>>> person.data
{'name': 'Ford Prefect', 'age': 42, 'possessions': ['Towel']}
```

A YAMLError will be raised if there are syntactic problems, violations of your schema or use of disallowed YAML features:

```
# All about the character
name: Ford Prefect
age: 42
```

For example, a schema violation:

```
try:
    person = load(yaml_snippet, schema)
except YAMLError as error:
    print(error)
```

```
while parsing a mapping
  in "<unicode string>", line 1, column 1:
    # All about the character
     ^ (line: 1)
required key(s) 'possessions' not found
  in "<unicode string>", line 3, column 1:
    age: '42'
    ^ (line: 3)
```

If parsed correctly:

```
from strictyaml import load, Map, Str, Int, Seq, YAMLError, as_document

schema = Map({"name": Str(), "age": Int(), "possessions": Seq(Str())})
```

You can modify values and write out the YAML with comments preserved:

```
person = load(yaml_snippet, schema)
person['age'] = 43
print(person.as_yaml())
```

```
# All about the character
name: Ford Prefect
age: 43
possessions:
- Towel
```

As well as look up line numbers:

```
>>> person = load(yaml_snippet, schema)
>>> person['possessions'][0].start_line
5
```

And construct YAML documents from dicts or lists:

```
print(as_document({"x": 1}).as_yaml())
```

```
x: 1
```

## Install

```
$ pip install strictyaml
```

## Why StrictYAML?

There are a number of formats and approaches that can achieve more or
less the same purpose as StrictYAML. I've tried to make it the best one.
Below is a series of documented justifications:

- Why avoid using environment variables as configuration?
- Why not use HJSON?
- Why not HOCON?
- Why not use INI files?
- Why not use JSON Schema for validation?
- Why not JSON for simple configuration files?
- Why not JSON5?
- Why not use the YAML 1.2 standard? - we don't need a new standard!
- Why not use kwalify with standard YAML to validate my YAML?
- Why not use Python's schema library (or similar) for validation?
- Why not use SDLang?
- What is wrong with TOML?
- Why shouldn't I just use Python code for configuration?
- Why not use XML for configuration or DSLs?

## Using StrictYAML

How to:

- Build a YAML document from scratch in code
- Either/or schema validation of different, equally valid different kinds of YAML
- Labeling exceptions
- Merge YAML documents
- Revalidate an already validated document
- Reading in YAML, editing it and writing it back out
- Get line numbers of YAML elements
- Parsing YAML without a schema

Compound validators:

- Fixed length sequences (FixedSeq)
- Mappings combining defined and undefined keys (MapCombined)
- Mappings with arbitrary key names (MapPattern)
- Mapping with defined keys and a custom key validator (Map)
- Using a YAML object of a parsed mapping
- Mappings with defined keys (Map)
- Optional keys with defaults (Map/Optional)
- Validating optional keys in mappings (Map)
- Sequences of unique items (UniqueSeq)
- Sequence/list validator (Seq)
- Updating document with a schema

Scalar validators:

- Boolean (Bool)
- Parsing comma separated items (CommaSeparated)
- Datetimes (Datetime)
- Decimal numbers (Decimal)
- Email and URL validators
- Empty key validation
- Enumerated scalars (Enum)
- Floating point numbers (Float)
- Hexadecimal Integers (HexInt)
- Integers (Int)
- Validating strings with regexes (Regex)
- Parsing strings (Str)

Restrictions:

- Disallowed YAML
- Duplicate keys
- Dirty load

## Design justifications

There are some design decisions in StrictYAML which are controversial
and/or not obvious. Those are documented here:

- What is wrong with duplicate keys?
- What is wrong with explicit tags?
- What is wrong with flow-style YAML?
- The Norway Problem - why StrictYAML refuses to do implicit typing and so should you
- What is wrong with node anchors and references?
- Why does StrictYAML not parse direct representations of Python objects?
- Why does StrictYAML only parse from strings and not files?
- Why is parsing speed not a high priority for StrictYAML?
- What is syntax typing?
- Why does StrictYAML make you define a schema in Python - a Turing-complete language?

## Star Contributors

- @wwoods
- @chrisburr
- @jnichols0

## Other Contributors

- @eulores
- @WaltWoods
- @ChristopherGS
- @gvx
- @AlexandreDecan
- @lots0logs
- @tobbez
- @jaredsampson
- @BoboTIG

StrictYAML also includes code from ruamel.yaml, Copyright Anthon van der Neut.

## Contributing

- Before writing any code, please read the tutorial on contributing to hitchdev libraries.
- Before writing any code, if you're proposing a new feature, please raise it on github. If it's an existing feature / bug, please comment and briefly describe how you're going to implement it.
- All code needs to come accompanied with a story that exercises it or a modification to an existing story. This is used both to test the code and build the documentation.
