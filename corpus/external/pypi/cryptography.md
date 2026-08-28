[image: Latest Version] [image: Latest Docs] [image: https://github.com/pyca/cryptography/actions/workflows/ci.yml/badge.svg]

cryptography is a package which provides cryptographic recipes and
primitives to Python developers. Our goal is for it to be your “cryptographic
standard library”. It supports Python 3.9+ and PyPy3 7.3.11+.

cryptography includes both high level recipes and low level interfaces to
common cryptographic algorithms such as symmetric ciphers, message digests, and
key derivation functions. For example, to encrypt something with
cryptography’s high level symmetric encryption recipe:

```
>>> from cryptography.fernet import Fernet
>>> # Put this somewhere safe!
>>> key = Fernet.generate_key()
>>> f = Fernet(key)
>>> token = f.encrypt(b"A really secret message. Not for prying eyes.")
>>> token
b'...'
>>> f.decrypt(token)
b'A really secret message. Not for prying eyes.'
```

You can find more information in the documentation.

You can install cryptography with:

```
$ pip install cryptography
```

For full details see the installation documentation.

## Discussion

If you run into bugs, you can file them in our issue tracker.

We maintain a cryptography-dev mailing list for development discussion.

You can also join #pyca on irc.libera.chat to ask questions or get
involved.

## Security

Need to report a security issue? Please consult our security reporting
documentation.
