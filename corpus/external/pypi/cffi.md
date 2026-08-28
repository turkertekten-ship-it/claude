---
date: 2026-08-03T21:19:15+0000
source: https://pypi.org/project/cffi/
---
[image: GitHub Actions Status] [image: PyPI version] [image: Read the Docs]

# CFFI

Foreign Function Interface for Python calling C code.

Please see the Documentation or uncompiled in the doc/ subdirectory.

## Download

Download page

## Source Code

Source code is publicly available on
GitHub.

## Contact

Mailing list

## Testing/development tips

After git clone or wget && tar, we will get a directory called cffi or cffi-x.x.x. We call it repo-directory. To run tests under CPython, run the following in the repo-directory:

```
pip install pytest
pip install -e .  # editable install of CFFI for local development
pytest src/c/ testing/
```
