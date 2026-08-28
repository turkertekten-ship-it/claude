---
date: 2023-09-03T16:56:59+0000
source: https://pypi.org/project/devtools/
---
# python devtools

[image: CI] [image: Coverage] [image: pypi] [image: versions] [image: license]

Python's missing debug print command and other development tools.

For more information, see documentation.

## Install

Just

```
pip install devtools
```

If you've got python 3.7+ and pip installed, you're good to go.

## Usage

```
from devtools import debug

whatever = [1, 2, 3]
debug(whatever)
```

Outputs:

```
test.py:4 <module>:
    whatever: [1, 2, 3] (list)
```

That's only the tip of the iceberg, for example:

```
import numpy as np

data = {
    'foo': np.array(range(20)),
    'bar': {'apple', 'banana', 'carrot', 'grapefruit'},
    'spam': [{'a': i, 'b': (i for i in range(3))} for i in range(3)],
    'sentence': 'this is just a boring sentence.\n' * 4
}

debug(data)
```

outputs:

[image: python-devtools demo]

## Usage without Import

devtools can be used without from devtools import debug if you add debug into __builtins__
in sitecustomize.py.

For instructions on adding debug to __builtins__,
see the installation docs.
