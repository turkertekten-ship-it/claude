---
date: 2026-08-13T22:27:44+0000
source: https://pypi.org/project/pipx/
---
# pipx — Install and Run Python Applications in Isolated Environments

[image: image] [image: PyPI version]

Documentation: https://pipx.pypa.io

Source Code: https://github.com/pypa/pipx

For comparison to other tools including pipsi, see
Comparison to Other Tools.

## Overview: What is pipx?

pipx is a tool to help you install and run end-user applications written in Python. It's roughly similar to macOS's
brew, JavaScript's npx, and
Linux's apt.

It's closely related to pip. In fact, it uses pip, but is focused on installing and managing Python packages that can be
run from the command line directly as applications.

### Features

pipx enables you to

- expose CLI entrypoints of packages ("apps") installed to isolated environments with the install command,
guaranteeing no dependency conflicts and clean uninstalls;
- easily list, upgrade, and uninstall packages that were installed with pipx; and
- run the latest version of a Python application in a temporary environment with the run command.

Best of all, pipx runs with regular user permissions, never calling sudo pip install.

## Install pipx

### On macOS

```
brew install pipx
pipx ensurepath
```

### On Linux

Install pipx with your distribution's package manager. See the
Linux installation instructions for commands and alternatives.

```
pipx ensurepath
```

### On Windows

```
scoop install pipx
pipx ensurepath
```

For more detailed installation instructions, see the
full documentation.

## Quick Start

Install an application globally:

```
pipx install pycowsay
pycowsay mooo
```

Run an application without installing:

```
pipx run pycowsay moo
```

See the full documentation for more details.

## Contributing

Issues and Pull Requests are definitely welcome! Check out Contributing
to get started. Everyone who interacts with the pipx project via codebase, issue tracker, chat rooms, or otherwise is
expected to follow the PSF Code of Conduct.
