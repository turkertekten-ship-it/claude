---
date: 2026-07-31T06:41:20+0000
source: https://pypi.org/project/dotenv-linter/
---
# dotenv-linter

[image: wemake.services] [image: test] [image: codecov] [image: Github Action] [image: Python Version] [image: Documentation Status]

---

Simple linter for .env files.

[image: dotenv-logo]

While .env files are very simple it is required to keep them consistent.
This tool offers a wide range of consistency rules and best practices.

And it integrates perfectly to any existing workflow.

Read the announcing post.

## Installation and usage

```
pip install dotenv-linter
```

And then run it:

```
dotenv-linter .env .env.template
```

See Usage
section for more information.

## Examples

There are many things that can go wrong in your .env files:

```
# Next line has leading space which will be removed:
 SPACED=

# Equal signs should not be spaced:
KEY = VALUE

# Quotes won't be preserved after parsing, do not use them:
SECRET="my value"

# Beware of duplicate keys!
SECRET=Already defined ;(

# Respect the convention, use `UPPER_CASE`:
kebab-case-name=1
snake_case_name=2
```

And much more! You can find the full list of violations in our docs.

## Pre-commit hooks

dotenv-linter can also be used as a pre-commit hook.
To do so, add the following to the .pre-commit-config.yaml file at the root of your project:

```
repos:
  - repo: https://github.com/wemake-services/dotenv-linter
    rev: 0.8.0  # Use the ref you want to point at
    hooks:
      - id: dotenv-linter
```

For the more detailed instructions on the pre-commit tool itself,
please refer to its website.

## Gratis

Special thanks goes to Ignacio Toledo
for creating an awesome logo for the project.
