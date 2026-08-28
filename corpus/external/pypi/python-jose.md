---
date: 2025-05-28T17:31:52+0000
source: https://pypi.org/project/python-jose/
---
A JOSE implementation in Python

[image: PyPI] [image: Github Actions CI Status] [image: Coverage Status] [image: Docs] [image: Code style: black]

Docs are available on ReadTheDocs.

The JavaScript Object Signing and Encryption (JOSE) technologies - JSON
Web Signature (JWS), JSON Web Encryption (JWE), JSON Web Key (JWK), and
JSON Web Algorithms (JWA) - collectively can be used to encrypt and/or
sign content using a variety of algorithms. While the full set of
permutations is extremely large, and might be daunting to some, it is
expected that most applications will only use a small set of algorithms
to meet their needs.

## Installation

```
$ pip install python-jose[cryptography]
```

## Cryptographic Backends

As of 3.3.0, python-jose implements three different cryptographic backends.
The backend must be selected as an extra when installing python-jose.
If you do not select a backend, the native-python backend will be installed.

Unless otherwise noted, all backends support all operations.

Due to complexities with setuptools, the native-python backend is always installed,
even if you select a different backend on install.
We recommend that you remove unnecessary dependencies in production.

1. cryptography

 - This backend uses pyca/cryptography for all cryptographic operations.
This is the recommended backend and is selected over all other backends if any others are present.
 - Installation: pip install python-jose[cryptography]
 - Unused dependencies:

 - rsa
 - ecdsa
 - pyasn1
1. pycryptodome

 - This backend uses pycryptodome for all cryptographic operations.
 - Installation: pip install python-jose[pycryptodome]
 - Unused dependencies:

 - rsa
1. native-python

 - This backend uses python-rsa and python-ecdsa for all cryptographic operations.
This backend is always installed but any other backend will take precedence if one is installed.
 - Installation: pip install python-jose

## Usage

```
>>> from jose import jwt
>>> token = jwt.encode({'key': 'value'}, 'secret', algorithm='HS256')
u'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ2YWx1ZSJ9.FG-8UppwHaFp1LgRYQQeS6EDQF7_6-bMFegNucHjmWg'

>>> jwt.decode(token, 'secret', algorithms=['HS256'])
{u'key': u'value'}
```

## Thanks

This library was originally based heavily on the work of the folks over at PyJWT.
