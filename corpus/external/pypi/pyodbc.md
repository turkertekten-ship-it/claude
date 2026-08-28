---
date: 2025-10-17T18:02:58+0000
source: https://pypi.org/project/pyodbc/
---
# pyodbc

[image: Windows build] [image: Ubuntu build] [image: PyPI]

pyodbc is an open source Python module that makes accessing ODBC databases simple. It
implements the DB API 2.0 specification but is packed with even more Pythonic convenience.

The easiest way to install pyodbc is to use pip:

```
python -m pip install pyodbc
```

On Macs, you should probably install unixODBC first if you don't already have an ODBC
driver manager installed. For example, using the homebrew package manager:

```
brew install unixodbc
python -m pip install pyodbc
```

Similarly, on Unix you should make sure you have an ODBC driver manager installed before
installing pyodbc. See the docs
for more information about how to do this on different Unix flavors. (On Windows, the
ODBC driver manager is built-in.)

Precompiled binary wheels are provided for multiple Python versions on most Windows, macOS,
and Linux platforms. On other platforms pyodbc will be built from the source code. Note,
pyodbc contains C++ extensions so you will need a suitable C++ compiler when building from
source. See the docs for details.

Documentation

Release Notes
