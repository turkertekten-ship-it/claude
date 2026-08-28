---
date: 2025-06-03T06:55:30+0000
source: https://pypi.org/project/argon2-cffi/
---
# argon2-cffi: Argon2 for Python

Argon2 won the Password Hashing Competition and argon2-cffi is the simplest way to use it in Python:

```
>>> from argon2 import PasswordHasher
>>> ph = PasswordHasher()
>>> hash = ph.hash("correct horse battery staple")
>>> hash  # doctest: +SKIP
'$argon2id$v=19$m=65536,t=3,p=4$MIIRqgvgQbgj220jfp0MPA$YfwJSVjtjSU0zzV/P3S9nnQ/USre2wvJMjfCIjrTQbg'
>>> ph.verify(hash, "correct horse battery staple")
True
>>> ph.check_needs_rehash(hash)
False
>>> ph.verify(hash, "Tr0ub4dor&3")
Traceback (most recent call last):
  ...
argon2.exceptions.VerifyMismatchError: The password does not match the supplied hash
```

## Project Links

- PyPI
- GitHub
- Documentation
- Changelog
- Funding
- The low-level Argon2 CFFI bindings are maintained in the separate argon2-cffi-bindings project.

## Release Information

### Added

- Official support for Python 3.13 and 3.14.
No code changes were necessary.

### Removed

- Python 3.7 is not supported anymore.
#186

### Changed

- argon2.PasswordHasher.check_needs_rehash() now also accepts bytes like the rest of the API.
#174
- Improved parameter compatibility handling for Pyodide / WebAssembly environments.
#190

---

Full Changelog →

## Credits

argon2-cffi is maintained by Hynek Schlawack.

The development is kindly supported by my employer Variomedia AG, argon2-cffi Tidelift subscribers, and my amazing GitHub Sponsors.

## argon2-cffi for Enterprise

Available as part of the Tidelift Subscription.

The maintainers of argon2-cffi and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open-source packages you use to build your applications.
Save time, reduce risk, and improve code health, while paying the maintainers of the exact packages you use.
