---
date: 2023-01-29T15:52:12+0000
source: https://pypi.org/project/argparse-addons/
---
## About

Additional Python argparse types and actions.

Project homepage: https://github.com/eerimoq/argparse_addons

## Installation

```
$ pip install argparse_addons
```

## Examples

Integer type

The script. See examples/integer.py for the complete script.

```
parser.add_argument('--min-max',
                    type=argparse_addons.Integer(0, 255))
parser.add_argument('--min',
                    type=argparse_addons.Integer(0, None))
parser.add_argument('--max',
                    type=argparse_addons.Integer(None, 255))
parser.add_argument('--any',
                    type=argparse_addons.Integer())
```

Error message for the --min-max argument.

```
$ python3 examples/integer.py --min-max -1
usage: integer.py [-h] [--min-max MIN_MAX] [--min MIN] [--max MAX] [--any ANY]
integer.py: error: argument --min-max: -1 is not in the range 0..255
```

Error message for the --min argument.

```
$ python3 examples/integer.py --min -1
usage: integer.py [-h] [--min-max MIN_MAX] [--min MIN] [--max MAX] [--any ANY]
integer.py: error: argument --min: -1 is not in the range 0..inf
```

Error message for the --max argument.

```
$ python3 examples/integer.py --max 1000
usage: integer.py [-h] [--min-max MIN_MAX] [--min MIN] [--max MAX] [--any ANY]
integer.py: error: argument --max: 1000 is not in the range -inf..255
```

Error message for the --any argument.

```
$ python3 examples/integer.py --any a
usage: integer.py [-h] [--min-max MIN_MAX] [--min MIN] [--max MAX] [--any ANY]
integer.py: error: argument --any: invalid integer value: 'a'
```

All values within allowed ranges.

```
$ python3 examples/integer.py --min-max 47 --min 1000 --max -5 --any 1
--min-max: 47
--min:     1000
--max:     -5
--any:     1
```

## Contributing

1. Fork the repository.
1. Install prerequisites.

```
pip install -r requirements.txt
``` 
1. Implement the new feature or bug fix.
1. Implement test case(s) to ensure that future changes do not break
legacy.
1. Run the tests.

```
make test
``` 
1. Create a pull request.
