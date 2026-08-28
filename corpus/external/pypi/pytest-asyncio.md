---
date: 2026-05-26T09:56:02+0000
source: https://pypi.org/project/pytest-asyncio/
---
[image: https://img.shields.io/pypi/v/pytest-asyncio.svg] [image: https://github.com/pytest-dev/pytest-asyncio/workflows/CI/badge.svg] [image: https://codecov.io/gh/pytest-dev/pytest-asyncio/branch/main/graph/badge.svg] [image: Supported Python versions] [image: Matrix chat room: #pytest-asyncio]

pytest-asyncio is a pytest plugin. It facilitates testing of code that uses the asyncio library.

Specifically, pytest-asyncio provides support for coroutines as test functions. This allows users to await code inside their tests. For example, the following code is executed as a test item by pytest:

```
@pytest.mark.asyncio
async def test_some_asyncio_code():
    res = await library.do_something()
    assert b"expected result" == res
```

More details can be found in the documentation.

Note that test classes subclassing the standard unittest library are not supported. Users
are advised to use unittest.IsolatedAsyncioTestCase
or an async framework such as asynctest.

pytest-asyncio is available under the Apache License 2.0.

## Installation

To install pytest-asyncio, simply:

```
$ pip install pytest-asyncio
```

This is enough for pytest to pick up pytest-asyncio.

## Contributing

Contributions are very welcome. Tests can be run with tox, please ensure
the coverage at least stays the same before you submit a pull request.
