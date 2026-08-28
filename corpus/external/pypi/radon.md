[image: Codacy badge] [image: Travis-CI badge] [image: Coveralls badge] [image: PyPI latest version badge] [image: Radon license]

---

Radon is a Python tool that computes various metrics from the source code.
Radon can compute:

- McCabe’s complexity, i.e. cyclomatic complexity
- raw metrics (these include SLOC, comment lines, blank lines, &c.)
- Halstead metrics (all of them)
- Maintainability Index (the one used in Visual Studio)

## Requirements

Radon will run from Python 2.7 to Python 3.8 (except Python versions
from 3.0 to 3.3) with a single code base and without the need of tools like
2to3 or six. It can also run on PyPy without any problems (currently PyPy
3.5 v7.3.1 is used in tests).

Radon depends on as few packages as possible. Currently only mando is
strictly required (for the CLI interface). colorama is also listed as a
dependency but if Radon cannot import it, the output simply will not be
colored.

Note:
Python 2.6 was supported until version 1.5.0. Starting from version 2.0, it
is not supported anymore.

## Installation

With Pip:

```
$ pip install radon
```

If you want to configure Radon from pyproject.toml and you run Python <3.11,
you’ll need the extra toml dependency:

```
$ pip install radon[toml]
```

Or download the source and run the setup file:

```
$ python setup.py install
```

## Usage

Radon can be used either from the command line or programmatically.
Documentation is at https://radon.readthedocs.org/.

## Cyclomatic Complexity Example

Quick example:

```
$ radon cc sympy/solvers/solvers.py -a -nc
sympy/solvers/solvers.py
    F 346:0 solve - F
    F 1093:0 _solve - F
    F 1434:0 _solve_system - F
    F 2647:0 unrad - F
    F 110:0 checksol - F
    F 2238:0 _tsolve - F
    F 2482:0 _invert - F
    F 1862:0 solve_linear_system - E
    F 1781:0 minsolve_linear_system - D
    F 1636:0 solve_linear - D
    F 2382:0 nsolve - C

11 blocks (classes, functions, methods) analyzed.
Average complexity: F (61.0)
```

Explanation:

- cc is the radon command to compute Cyclomatic Complexity
- -a tells radon to calculate the average complexity at the end. Note that
the average is computed among the shown blocks. If you want the total
average, among all the blocks, regardless of what is being shown, you should
use --total-average.
- -nc tells radon to print only results with a complexity rank of C or
worse. Other examples: -na (from A to F), or -nd (from D to F).
- The letter in front of the line numbers represents the type of the block
(F means function, M method and C class).

Actually it’s even better: it’s got colors!

 [image: A screen of Radon's cc command]

Note about file encoding

On some systems, such as Windows, the default encoding is not UTF-8. If you are
using Unicode characters in your Python file and want to analyze it with Radon,
you’ll have to set the RADONFILESENCODING environment variable to UTF-8.

## On a Continuous Integration server

If you are looking to use radon on a CI server you may be better off with
xenon. Although still experimental, it will
fail (that means exiting with a non-zero exit code) when various thresholds are
surpassed. radon is more of a reporting tool, while xenon is a monitoring
one.

If you are looking for more complete solutions, read the following sections.

### Codacy

Codacy uses Radon by default to calculate metrics from the source code.

### Code Climate

Radon is available as a Code Climate Engine.
To understand how to add Radon’s checks to your Code Climate Platform, head
over to their documentation:
https://docs.codeclimate.com/v1.0/docs/radon

### coala Analyzer

Radon is also supported in coala. To add Radon’s
checks to coala, simply add the RadonBear to one of the sections in
your .coafile.

### CodeFactor

CodeFactor uses Radon out-of-the-box to calculate Cyclomatic Complexity.

## Usage with Jupyter Notebooks

Radon can be used with .ipynb files to inspect code metrics for Python cells. Any % macros will be ignored in the metrics.

To enable scanning of Jupyter notebooks, add the --include-ipynb flag.

To enable reporting of individual cells, add the --ipynb-cells flag.

Quick example:

```
$ radon raw --include-ipynb --ipynb-cells .
example.ipynb
    LOC: 63
    LLOC: 37
    SLOC: 37
    Comments: 3
    Single comments: 2
    Multi: 10
    Blank: 14
    - Comment Stats
        (C % L): 5%
        (C % S): 8%
        (C + M % L): 21%
example.ipynb:[0]
    LOC: 0
    LLOC: 0
    SLOC: 0
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
example.ipynb:[1]
    LOC: 2
    LLOC: 2
    SLOC: 2
    Comments: 0
    Single comments: 0
    Multi: 0
    Blank: 0
    - Comment Stats
        (C % L): 0%
        (C % S): 0%
        (C + M % L): 0%
```

## Links

- Documentation: https://radon.readthedocs.org
- PyPI: http://pypi.python.org/pypi/radon
- Issue Tracker: https://github.com/rubik/radon/issues
