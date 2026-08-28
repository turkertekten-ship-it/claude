---
date: 2025-05-14T18:56:31+0000
source: https://pypi.org/project/motor/
---
# Motor

[image: PyPI Version] [image: Python Versions] [image: Monthly Downloads] [image: Documentation Status]

[image: image]

> [!WARNING]
> Motor will be deprecated on May 14th, 2026, one year after the production release of the PyMongo Async driver.
> Critical bug fixes will be made until May 14th, 2027.
> We strongly recommend that Motor users migrate to the PyMongo Async driver while Motor is still supported.
> To learn more, see the migration guide: https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/.

## About

Motor is a full-featured, non-blocking MongoDB
driver for Python asyncio and
Tornado applications. Motor presents a coroutine-based API
for non-blocking access to MongoDB.

> "We use Motor in high throughput environments, processing tens of
> thousands of requests per second. It allows us to take full advantage
> of modern hardware, ensuring we utilise the entire capacity of our
> purchased CPUs. This helps us be more efficient with computing power,
> compute spend and minimises the environmental impact of our
> infrastructure as a result." --David Mytton, Server Density "We develop easy-to-use sensors and sensor systems with open source
> software to ensure every innovator, from school child to laboratory
> researcher, has the same opportunity to create. We integrate Motor
> into our software to guarantee massively scalable sensor systems for
> everyone." --Ryan Smith, inXus Interactive

## Support / Feedback

For issues with, questions about, or feedback for PyMongo, please look
into our support channels. Please
do not email any of the Motor developers directly with issues or
questions - you're more likely to get an answer on the
StackOverflow
(using a "mongodb" tag).

## Bugs / Feature Requests

Think you've found a bug? Want to see a new feature in Motor? Please
open a case in our issue management tool, JIRA:

- Create an account and login.
- Navigate to the MOTOR
project.
- Click Create Issue - Please provide as much information as
possible about the issue type and how to reproduce it.

Bug reports in JIRA for all driver projects (i.e. MOTOR, CSHARP, JAVA)
and the Core Server (i.e. SERVER) project are public.

### How To Ask For Help

Please include all of the following information when opening an issue:

- Detailed steps to reproduce the problem, including full traceback, if
possible.
- The exact python version used, with patch level:

```
python -c "import sys; print(sys.version)"
```

- The exact version of Motor used, with patch level:

```
python -c "import motor; print(motor.version)"
```

- The exact version of PyMongo used, with patch level:

```
python -c "import pymongo; print(pymongo.version); print(pymongo.has_c())"
```

- The exact Tornado version, if you are using Tornado:

```
python -c "import tornado; print(tornado.version)"
```

- The operating system and version (e.g. RedHat Enterprise Linux 6.4,
OSX 10.9.5, ...)

### Security Vulnerabilities

If you've identified a security vulnerability in a driver or any other
MongoDB project, please report it according to the instructions
here.

## Installation

Motor can be installed with pip:

```
pip install motor
```

## Dependencies

Motor works in all the environments officially supported by Tornado or
by asyncio. It requires:

- Unix (including macOS) or Windows.
- PyMongo >=4.9,<5
- Python 3.9+

Optional dependencies:

Motor supports same optional dependencies as PyMongo. Required
dependencies can be installed along with Motor.

GSSAPI authentication requires gssapi extra dependency. The correct
dependency can be installed automatically along with Motor:

```
pip install "motor[gssapi]"
```

similarly,

MONGODB-AWS authentication requires aws extra dependency:

```
pip install "motor[aws]"
```

Support for mongodb+srv:// URIs requires srv extra dependency:

```
pip install "motor[srv]"
```

OCSP requires ocsp extra dependency:

```
pip install "motor[ocsp]"
```

Wire protocol compression with snappy requires snappy extra
dependency:

```
pip install "motor[snappy]"
```

Wire protocol compression with zstandard requires zstd extra
dependency:

```
pip install "motor[zstd]"
```

Client-Side Field Level Encryption requires encryption extra
dependency:

```
pip install "motor[encryption]"
```

You can install all dependencies automatically with the following
command:

```
pip install "motor[gssapi,aws,ocsp,snappy,srv,zstd,encryption]"
```

See
requirements
for details about compatibility.

## Examples

See the examples on
ReadTheDocs.

## Documentation

Motor's documentation is on
ReadTheDocs.

Build the documentation with Python 3.9+. Install
sphinx, Tornado,
and aiohttp, and do
cd doc; make html.

## Learning Resources

- MongoDB Learn - Python
courses.
- Python Articles on Developer
Center.

## Testing

Run python setup.py test. Tests are located in the test/ directory.
