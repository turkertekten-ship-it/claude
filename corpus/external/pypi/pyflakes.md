A simple program which checks Python source files for errors.

Pyflakes analyzes programs and detects various errors. It works by
parsing the source file, not importing it, so it is safe to use on
modules with side effects. It’s also much faster.

It is available on PyPI
and it supports all active versions of Python: 3.9+.

## Installation

It can be installed with:

```
$ pip install --upgrade pyflakes
```

Useful tips:

- Be sure to install it for a version of Python which is compatible
with your codebase: python#.# -m pip install pyflakes (for example,
python3.10 -m pip install pyflakes)
- You can also invoke Pyflakes with python#.# -m pyflakes . if you want
to run it for a specific python version.
- If you require more options and more flexibility, you could give a
look to Flake8 too.

## Design Principles

Pyflakes makes a simple promise: it will never complain about style,
and it will try very, very hard to never emit false positives.

Pyflakes is also faster than Pylint. This is
largely because Pyflakes only examines the syntax tree of each file
individually. As a consequence, Pyflakes is more limited in the
types of things it can check.

If you like Pyflakes but also want stylistic checks, you want
flake8, which combines
Pyflakes with style checks against
PEP 8 and adds
per-project configuration ability.

## Mailing-list

Share your feedback and ideas: subscribe to the mailing-list

## Contributing

Issues are tracked on GitHub.

Patches may be submitted via a GitHub pull request.
If you are comfortable doing so, please rebase your changes
so they may be applied to main with a fast-forward merge, and each commit is
a coherent unit of work with a well-written log message. If you are not
comfortable with this rebase workflow, the project maintainers will be happy to
rebase your commits for you.

All changes should include tests and pass flake8.

 [image: GitHub Actions build status]

## Changelog

Please see NEWS.rst.
