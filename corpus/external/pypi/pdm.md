---
date: 2026-08-18T02:18:44+0000
source: https://pypi.org/project/pdm/
---
# PDM

[image: Support Frost's Python packaging ecosystem]

A modern Python package and dependency manager supporting the latest PEP standards.
中文版本说明

[image: PDM logo]

[image: Docs] [image: Twitter Follow] [image: Discord]

[image: Github Actions] [image: PyPI] [image: codecov] [image: Packaging status] [image: Downloads] [image: pdm-managed] [image: trackgit-views]

[image: asciicast]

## What is PDM?

PDM is meant to be a next-generation package manager.
It was originally built for personal use. If you feel you are going well
with Pipenv or Poetry and don't want to introduce another package manager,
just stick to it. But if you are missing something that is not present in those tools,
you can probably find some goodness in pdm.

## Highlights of features

- Simple and fast dependency resolver, mainly for large binary distributions.
- A PEP 517 build backend.
- PEP 621 project metadata.
- Flexible and powerful plug-in system.
- Versatile user scripts.
- Install Pythons using astral-sh's python-build-standalone.
- Opt-in, centralized installation cache like pnpm.

## Comparisons to other alternatives

### Pipenv

Pipenv is a dependency manager that combines pip and venv, as the name implies.
It can install packages from a non-standard Pipfile.lock or Pipfile.
However, Pipenv does not handle any packages related to packaging your code,
so it’s useful only for developing non-installable applications (Django sites, for example).
If you’re a library developer, you need setuptools anyway.

### Poetry

Poetry manages environments and dependencies in a similar way to Pipenv,
but it can also build .whl files with your code, and it can upload wheels and source distributions to PyPI.
It has a pretty user interface and users can customize it via a plugin. Poetry uses the pyproject.toml standard.

### Hatch

Hatch can also manage environments, allowing multiple environments per project. By default it has a central location for all environments but it can be configured to put a project's environment(s) in the project root directory. It can manage packages but without lockfile support. It can also be used to package a project (with PEP 621 compliant pyproject.toml files) and upload it to PyPI.

### This project

PDM can manage virtual environments (venvs) in both project and centralized locations, similar to Pipenv. It reads project metadata from a standardized pyproject.toml file and supports lockfiles. Users can add additional functionality through plugins, which can be shared by uploading them as distributions.

Unlike Poetry and Hatch, PDM is not limited to a specific build backend; users have the freedom to choose any build backend they prefer.

## Installation

 [image: Packaging status]

PDM requires python version 3.10 or higher. Alternatively, you can download the standalone binary from the release assets.

### Install Binary via Script (recommended)

Install the standalone binary directly with the installer scripts:

For Linux/Mac

```
curl -sSL https://pdm-project.org/install.sh | bash
```

For Windows

```
powershell -ExecutionPolicy ByPass -c "irm https://pdm-project.org/install.ps1 | iex"
```

For alternative installation methods (Python script, package managers, etc.), see the installation section in documentation.

## Quickstart

Create a new PDM project

```
pdm new my-project
```

Answer the prompts, and a PDM project with a pyproject.toml file will be ready to use., and a PDM project with a pyproject.toml file will be ready to use.

Install dependencies

```
pdm add requests flask
```

You can add multiple dependencies in the same command. After a while, check the pdm.lock file to see what is locked for each package.

## Badges

Tell people you are using PDM in your project by including the markdown code in README.md:

```
[![pdm-managed](https://img.shields.io/endpoint?url=https%3A%2F%2Fcdn.jsdelivr.net%2Fgh%2Fpdm-project%2F.github%2Fbadge.json)](https://pdm-project.org)
```

[image: pdm-managed]

## PDM Eco-system

Awesome PDM is a curated list of awesome PDM plugins and resources.

## Experimental

Enable PEP 582 for a project:

```
pdm config python.use_venv False
```

This makes PDM install packages into a local project folder instead of a venv (similar to how npm installs into node_modules).

Enable uv integration:

```
pdm config use_uv true
```

uv is a very fast Python package installer written in Rust.

Note: uv does not work with PEP 582.

## Sponsors

## Credits

This project is strongly inspired by pyflow and poetry.

## License

This project is open sourced under MIT license, see the LICENSE file for more details.
