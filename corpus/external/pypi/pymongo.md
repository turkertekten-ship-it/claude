---
date: 2026-04-20T16:37:20+0000
source: https://pypi.org/project/pymongo/
---
# PyMongo

[image: PyPI Version] [image: Python Versions] [image: Monthly Downloads] [image: API Documentation Status] [image: codecov]

## About

The PyMongo distribution contains tools for interacting with MongoDB
database from Python. The bson package is an implementation of the
BSON format for Python. The pymongo package is
a native Python driver for MongoDB, offering both synchronous and asynchronous APIs. The gridfs package is a
gridfs
implementation on top of pymongo.

PyMongo supports MongoDB 4.0, 4.2, 4.4, 5.0, 6.0, 7.0, and 8.0. PyMongo follows semantic versioning for its releases.

## Documentation

Documentation is available at
mongodb.com.

API documentation and the full changelog for each release is available at readthedocs.io.

## Support / Feedback

For issues with, questions about, or feedback for PyMongo, please look
into our support channels. Please
do not email any of the PyMongo developers directly with issues or
questions - you're more likely to get an answer on
StackOverflow
(using a "mongodb" tag).

## Bugs / Feature Requests

Think you've found a bug? Want to see a new feature in PyMongo? Please
open a case in our issue management tool, JIRA:

- Create an account and login.
- Navigate to the PYTHON
project.
- Click Create Issue - Please provide as much information as
possible about the issue type and how to reproduce it.

Bug reports in JIRA for all driver projects (i.e. PYTHON, CSHARP, JAVA)
and the Core Server (i.e. SERVER) project are public.

### How To Ask For Help

Please include all of the following information when opening an issue:

- Detailed steps to reproduce the problem, including full traceback,
if possible.
- The exact python version used, with patch level:

```
python -c "import sys; print(sys.version)"
```

- The exact version of PyMongo used, with patch level:

```
python -c "import pymongo; print(pymongo.version); print(pymongo.has_c())"
```

- The operating system and version (e.g. Windows 7, OSX 10.8, ...)
- Web framework or asynchronous network library used, if any, with
version (e.g. Django 1.7, mod_wsgi 4.3.0, gevent 1.0.1, Tornado
4.0.2, ...)

### Security Vulnerabilities

If you've identified a security vulnerability in a driver or any other
MongoDB project, please report it according to the instructions
here.

## Installation

PyMongo can be installed with pip:

```
python -m pip install pymongo
```

You can also download the project source and do:

```
pip install .
```

Do not install the "bson" package from pypi. PyMongo comes with
its own bson package; running "pip install bson" installs a third-party
package that is incompatible with PyMongo.

## Dependencies

PyMongo supports CPython 3.9+ and PyPy3.9+.

Required dependencies:

Support for mongodb+srv:// URIs requires dnspython

Optional dependencies:

GSSAPI authentication requires
pykerberos on Unix or
WinKerberos on Windows. The
correct dependency can be installed automatically along with PyMongo:

```
python -m pip install "pymongo[gssapi]"
```

MONGODB-AWS authentication requires
pymongo-auth-aws:

```
python -m pip install "pymongo[aws]"
```

OCSP (Online Certificate Status Protocol) requires
PyOpenSSL,
requests,
service_identity and may
require certifi:

```
python -m pip install "pymongo[ocsp]"
```

Wire protocol compression with snappy requires
python-snappy:

```
python -m pip install "pymongo[snappy]"
```

Wire protocol compression with zstandard requires
backports.zstd
when used with Python versions before 3.14:

```
python -m pip install "pymongo[zstd]"
```

Client-Side Field Level Encryption requires
pymongocrypt and
pymongo-auth-aws:

```
python -m pip install "pymongo[encryption]"
```

You can install all dependencies automatically with the following
command:

```
python -m pip install "pymongo[gssapi,aws,ocsp,snappy,zstd,encryption]"
```

## Examples

Here's a basic example (for more see the examples section of the
docs):

```
>>> import pymongo
>>> client = pymongo.MongoClient("localhost", 27017)
>>> db = client.test
>>> db.name
'test'
>>> db.my_collection
Collection(Database(MongoClient('localhost', 27017), 'test'), 'my_collection')
>>> db.my_collection.insert_one({"x": 10}).inserted_id
ObjectId('4aba15ebe23f6b53b0000000')
>>> db.my_collection.insert_one({"x": 8}).inserted_id
ObjectId('4aba160ee23f6b543e000000')
>>> db.my_collection.insert_one({"x": 11}).inserted_id
ObjectId('4aba160ee23f6b543e000002')
>>> db.my_collection.find_one()
{'x': 10, '_id': ObjectId('4aba15ebe23f6b53b0000000')}
>>> for item in db.my_collection.find():
...     print(item["x"])
...
10
8
11
>>> db.my_collection.create_index("x")
'x_1'
>>> for item in db.my_collection.find().sort("x", pymongo.ASCENDING):
...     print(item["x"])
...
8
10
11
>>> [item["x"] for item in db.my_collection.find().limit(2).skip(1)]
[8, 11]
```

## Learning Resources

- MongoDB Learn - Python
courses.
- Python Articles on Developer
Center.

## Testing

The easiest way to run the tests is to run the following from the repository root.

```
pip install -e ".[test]"
pytest
```

For more advanced testing scenarios, see the contributing guide.
