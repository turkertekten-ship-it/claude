Psycopg is the most popular PostgreSQL database adapter for the Python
programming language. Its main features are the complete implementation of
the Python DB API 2.0 specification and the thread safety (several threads can
share the same connection). It was designed for heavily multi-threaded
applications that create and destroy lots of cursors and make a large number
of concurrent “INSERT”s or “UPDATE”s.

Psycopg 2 is mostly implemented in C as a libpq wrapper, resulting in being
both efficient and secure. It features client-side and server-side cursors,
asynchronous communication and notifications, “COPY TO/COPY FROM” support.
Many Python types are supported out-of-the-box and adapted to matching
PostgreSQL data types; adaptation can be extended and customized thanks to a
flexible objects adaptation system.

Psycopg 2 is both Unicode and Python 3 friendly.

## Documentation

Documentation is included in the doc directory and is available online.

For any other resource (source code repository, bug tracker, mailing list)
please check the project homepage.

## Installation

Building Psycopg requires a few prerequisites (a C compiler, some development
packages): please check the install and the faq documents in the doc dir
or online for the details.

If prerequisites are met, you can install psycopg like any other Python
package, using pip to download it from PyPI:

```
$ pip install psycopg2
```

or using setup.py if you have downloaded the source package locally:

```
$ python setup.py build
$ sudo python setup.py install
```

You can also obtain a stand-alone package, not requiring a compiler or
external libraries, by installing the psycopg2-binary package from PyPI:

```
$ pip install psycopg2-binary
```

The binary package is a practical choice for development and testing but in
production it is advised to use the package built from sources.

Build status:

[image: Build status]
