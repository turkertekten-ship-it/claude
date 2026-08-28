---
date: 2026-02-25T06:44:13+0000
source: https://pypi.org/project/bandit/
---
[image: Bandit]

---

 [image: Build Status] [image: Docs Status] [image: Latest Version] [image: Python Versions] [image: Format] [image: License] [image: Discord]

A security linter from PyCQA

- Free software: Apache license
- Documentation: https://bandit.readthedocs.io/en/latest/
- Source: https://github.com/PyCQA/bandit
- Bugs: https://github.com/PyCQA/bandit/issues
- Contributing: https://github.com/PyCQA/bandit/blob/main/CONTRIBUTING.md

## Overview

Bandit is a tool designed to find common security issues in Python code. To do
this Bandit processes each file, builds an AST from it, and runs appropriate
plugins against the AST nodes. Once Bandit has finished scanning all the files
it generates a report.

Bandit was originally developed within the OpenStack Security Project and
later rehomed to PyCQA.

 [image: Bandit Example Screen Shot]

## Show Your Style

 [image: Security Status]

Use our badge in your project’s README!

using Markdown:

```
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
```

using RST:

```
.. image:: https://img.shields.io/badge/security-bandit-yellow.svg
    :target: https://github.com/PyCQA/bandit
    :alt: Security Status
```

## References

Python AST module documentation: https://docs.python.org/3/library/ast.html

Green Tree Snakes - the missing Python AST docs:
https://greentreesnakes.readthedocs.org/en/latest/

Documentation of the various types of AST nodes that Bandit currently covers
or could be extended to cover:
https://greentreesnakes.readthedocs.org/en/latest/nodes.html

## Container Images

Bandit is available as a container image, built within the bandit repository
using GitHub Actions. The image is available on ghcr.io:

```
docker pull ghcr.io/pycqa/bandit/bandit
```

The image is built for the following architectures:

- amd64
- arm64
- armv7
- armv8

To pull a specific architecture, use the following format:

```
docker pull --platform=<architecture> ghcr.io/pycqa/bandit/bandit:latest
```

Every image is signed with sigstore cosign and it is possible to verify the
source of origin using the following cosign command:

```
cosign verify ghcr.io/pycqa/bandit/bandit:latest \
  --certificate-identity https://github.com/pycqa/bandit/.github/workflows/build-publish-image.yml@refs/tags/<version> \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

Where <version> is the release version of Bandit.

## Sponsors

The development of Bandit is made possible by the following sponsors:

| [image: Mercedes-Benz] | [image: Tidelift] | [image: Stacklok] |

If you also ❤️ Bandit, please consider sponsoring.
