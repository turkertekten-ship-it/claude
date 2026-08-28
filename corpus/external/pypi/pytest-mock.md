---
date: 2025-09-16T16:37:25+0000
source: https://pypi.org/project/pytest-mock/
---
This plugin provides a mocker fixture which is a thin-wrapper around the patching API
provided by the mock package:

```
import os

class UnixFS:

    @staticmethod
    def rm(filename):
        os.remove(filename)

def test_unix_fs(mocker):
    mocker.patch('os.remove')
    UnixFS.rm('file')
    os.remove.assert_called_once_with('file')
```

Besides undoing the mocking automatically after the end of the test, it also provides other
nice utilities such as spy and stub, and uses pytest introspection when
comparing calls.

[image: python] [image: version] [image: anaconda] [image: docs] [image: ci] [image: coverage] [image: black] [image: pre-commit]

Professionally supported pytest-mock is available.

## Documentation

For full documentation, please see https://pytest-mock.readthedocs.io/en/latest.

## License

Distributed under the terms of the MIT license.
