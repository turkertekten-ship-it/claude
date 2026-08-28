# ItsDangerous

... so better sign this

Various helpers to pass data to untrusted environments and to get it
back safe and sound. Data is cryptographically signed to ensure that a
token has not been tampered with.

It's possible to customize how data is serialized. Data is compressed as
needed. A timestamp can be added and verified automatically while
loading a token.

## A Simple Example

Here's how you could generate a token for transmitting a user's id and
name between web requests.

```
from itsdangerous import URLSafeSerializer
auth_s = URLSafeSerializer("secret key", "auth")
token = auth_s.dumps({"id": 5, "name": "itsdangerous"})

print(token)
# eyJpZCI6NSwibmFtZSI6Iml0c2Rhbmdlcm91cyJ9.6YP6T0BaO67XP--9UzTrmurXSmg

data = auth_s.loads(token)
print(data["name"])
# itsdangerous
```

## Donate

The Pallets organization develops and supports ItsDangerous and other
popular packages. In order to grow the community of contributors and
users, and allow the maintainers to devote more time to the projects,
please donate today.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

itsdangerous-2.2.0.tar.gz
 (54.4 kB
 view details)

Uploaded
 Apr 16, 2024
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

itsdangerous-2.2.0-py3-none-any.whl
 (16.2 kB
 view details)

Uploaded
 Apr 16, 2024
 Python 3

## File details

Details for the file itsdangerous-2.2.0.tar.gz.

### File metadata

- Download URL: itsdangerous-2.2.0.tar.gz
- Upload date:
 Apr 16, 2024
- Size: 54.4 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/5.0.0 CPython/3.12.3

### File hashes

Hashes for itsdangerous-2.2.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | e0050c0b7da1eea53ffaf149c0cfbb5c6e2e2b69c4bef22c81fa6eb73e5f6173 | |
| MD5 | a901babde35694c3577f7655010cd380 | |
| BLAKE2b-256 | 9ccb8ac0172223afbccb63986cc25049b154ecfb5e85932587206f42317be31d | |

See more details on using hashes here.

## File details

Details for the file itsdangerous-2.2.0-py3-none-any.whl.

### File metadata

- Download URL: itsdangerous-2.2.0-py3-none-any.whl
- Upload date:
 Apr 16, 2024
- Size: 16.2 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/5.0.0 CPython/3.12.3

### File hashes

Hashes for itsdangerous-2.2.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | c6242fc49e35958c8b15141343aa660db5fc54d4f13a1db01a3f5891b98700ef | |
| MD5 | 22e41bfb2008481e855f1693a9df4c54 | |
| BLAKE2b-256 | 049692447566d16df59b2a776c0fb82dbc4d9e07cd95062562af01e408583fc4 | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

This release

2.2.0 This release

Apr 16, 2024
 2 files

2.1.2

Mar 24, 2022
 2 files

2.1.1

Mar 9, 2022
 2 files

2.1.0

Feb 18, 2022
 2 files

2.0.1

May 18, 2021
 2 files

2.0.0

May 11, 2021
 2 files

Pre-release

2.0.0rc2

Apr 16, 2021
 2 files

Pre-release

2.0.0rc1

Feb 15, 2021
 2 files

Pre-release

2.0.0a1

May 28, 2020
 2 files

1.1.0

Oct 27, 2018
 2 files

0.24

Mar 28, 2014
 1 file

0.23

Aug 8, 2013
 1 file

0.22

Jul 3, 2013
 1 file

0.21

May 26, 2013
 1 file

0.20

May 23, 2013
 1 file

0.19

May 22, 2013
 1 file

0.18

May 15, 2013
 1 file

0.17

Aug 11, 2012
 1 file

0.16

Jul 11, 2012
 1 file

0.15

Jul 11, 2012
 1 file

0.14

Jun 29, 2012
 1 file

0.13

Jun 10, 2012
 1 file

0.12

Feb 22, 2012
 1 file

0.11

Jul 7, 2011
 1 file

0.10

Jun 29, 2011
 1 file

0.9.1

Jun 25, 2011
 1 file

0.9

Jun 24, 2011
 1 file