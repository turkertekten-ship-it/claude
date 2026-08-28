[image: PyPI version] [image: https://img.shields.io/conda/vn/conda-forge/pytest-xdist.svg] [image: Python versions] [image: https://github.com/pytest-dev/pytest-xdist/workflows/test/badge.svg] [image: https://img.shields.io/badge/code%20style-black-000000.svg]

The pytest-xdist plugin extends pytest with new test execution modes, the most used being distributing
tests across multiple CPUs to speed up test execution:

```
pytest -n auto
```

With this call, pytest will spawn a number of workers processes equal to the number of available CPUs, and distribute
the tests randomly across them.

## Documentation

Documentation is available at Read The Docs.
