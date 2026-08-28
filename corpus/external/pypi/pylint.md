[image: https://github.com/pylint-dev/pylint/actions/workflows/tests.yaml/badge.svg?branch=main] [image: https://codecov.io/gh/pylint-dev/pylint/branch/main/graph/badge.svg?token=ZETEzayrfk] [image: PyPI Package version] [image: Documentation Status] [image: https://img.shields.io/badge/code%20style-black-000000.svg] [image: https://img.shields.io/badge/linting-pylint-yellowgreen] [image: pre-commit.ci status] [image: CII Best Practices] [image: OpenSSF Scorecard] [image: Discord]

## What is Pylint?

Pylint is a static code analyser for Python 2 or 3. The latest version supports Python
3.10.0 and above.

Pylint analyses your code without actually running it. It checks for errors, enforces a
coding standard, looks for code smells, and can make suggestions about how the code
could be refactored.

## Install

For command line use, pylint is installed with:

```
pip install pylint
```

Or if you want to also check spelling with enchant (you might need to
install the enchant C library):

```
pip install pylint[spelling]
```

It can also be integrated in most editors or IDEs. More information can be found
in the documentation.

## What differentiates Pylint?

Pylint is not trusting your typing and is inferring the actual values of nodes (for a
start because there was no typing when pylint started off) using its internal code
representation (astroid). If your code is import logging as argparse, Pylint
can check and know that argparse.error(...) is in fact a logging call and not an
argparse call. This makes pylint slower, but it also lets pylint find more issues if
your code is not fully typed.

> [inference] is the killer feature that keeps us using [pylint] in our project despite how painfully slow it is.
> - Realist pylint user, 2022

pylint, not afraid of being a little slower than it already is, is also a lot more thorough than other linters.
There are more checks, including some opinionated ones that are deactivated by default
but can be enabled using configuration.

## How to use pylint

Pylint isn’t smarter than you: it may warn you about things that you have
conscientiously done or check for some things that you don’t care about.
During adoption, especially in a legacy project where pylint was never enforced,
it’s best to start with the --errors-only flag, then disable
convention and refactor messages with --disable=C,R and progressively
re-evaluate and re-enable messages as your priorities evolve.

Pylint is highly configurable and permits to write plugins in order to add your
own checks (for example, for internal libraries or an internal rule). Pylint also has an
ecosystem of existing plugins for popular frameworks and third-party libraries.

## Advised linters alongside pylint

Projects that you might want to use alongside pylint include ruff (really fast,
with builtin auto-fix and a large number of checks taken from popular linters, but
implemented in rust) or flake8 (a framework to implement your own checks in python using ast directly),
mypy, pyright / pylance or pyre (typing checks), bandit (security oriented checks), black and
isort (auto-formatting), autoflake (automated removal of unused imports or variables), pyupgrade
(automated upgrade to newer python syntax) and pydocstringformatter (automated pep257).

## Additional tools included in pylint

Pylint ships with two additional tools:

- pyreverse (standalone tool that generates package and class diagrams.)
- symilar (duplicate code finder that is also integrated in pylint)

## Contributing

We welcome all forms of contributions such as updates for documentation, new code, checking issues for duplicates or telling us
that we can close them, confirming that issues still exist, creating issues because
you found a bug or want a feature, etc. Everything is much appreciated!

Please follow the code of conduct and check the Contributor Guides if you want to
make a code contribution.

## Show your usage

You can place this badge in your README to let others know your project uses pylint.

> [image: https://img.shields.io/badge/linting-pylint-yellowgreen]

Learn how to add a badge to your documentation in the badge documentation.

## License

pylint is, with a few exceptions listed below, GPLv2.

The icon files are licensed under the CC BY-SA 4.0 license:

- doc/logo.png
- doc/logo.svg

## Support

Please check the contact information.

| [image: Tidelift] | Professional support for pylint is available as part of the Tidelift
Subscription. Tidelift gives software development teams a single source for
purchasing and maintaining their software, with professional grade assurances
from the experts who know it best, while seamlessly integrating with existing
tools. |
