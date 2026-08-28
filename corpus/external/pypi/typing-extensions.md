# Typing Extensions

[image: Chat at https://gitter.im/python/typing]

Documentation –
PyPI

## Overview

The typing_extensions module serves two related purposes:

- Enable use of new type system features on older Python versions. For example,
typing.TypeGuard is new in Python 3.10, but typing_extensions allows
users on previous Python versions to use it too.
- Enable experimentation with new type system PEPs before they are accepted and
added to the typing module.

typing_extensions is treated specially by static type checkers such as
mypy and pyright. Objects defined in typing_extensions are treated the same
way as equivalent forms in typing.

typing_extensions uses
Semantic Versioning. The
major version will be incremented only for backwards-incompatible changes.
Therefore, it's safe to depend
on typing_extensions like this: typing_extensions ~=x.y,
where x.y is the first version that includes all features you need.
This
is equivalent to typing_extensions >=x.y, <(x+1). Do not depend on ~= x.y.z
unless you really know what you're doing; that defeats the purpose of
semantic versioning.

## Included items

See the documentation for a
complete listing of module contents.

## Contributing

See CONTRIBUTING.md
for how to contribute to typing_extensions.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

typing_extensions-4.16.0.tar.gz
 (113.6 kB
 view details)

Uploaded
 Jul 2, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

typing_extensions-4.16.0-py3-none-any.whl
 (45.6 kB
 view details)

Uploaded
 Jul 2, 2026
 Python 3

## File details

Details for the file typing_extensions-4.16.0.tar.gz.

### File metadata

- Download URL: typing_extensions-4.16.0.tar.gz
- Upload date:
 Jul 2, 2026
- Size: 113.6 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for typing_extensions-4.16.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | dc983d19a509c94dba722ee6abd33940f7c05a89e243c47e907eb4db6f1a43e5 | |
| MD5 | 7758284b826ec6ca6b722e7891bbd10d | |
| BLAKE2b-256 | f6cc6253133b5bb138fc3306cebfbda2c520f545d36b5be2c7255cc528bb45d6 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for typing_extensions-4.16.0.tar.gz:

Publisher: publish.yml on python/typing_extensions

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: typing_extensions-4.16.0.tar.gz
 - Subject digest: dc983d19a509c94dba722ee6abd33940f7c05a89e243c47e907eb4db6f1a43e5
 - Sigstore transparency entry: 2045493586
 - Sigstore integration time:
 Jul 2, 2026
 Source repository:

 - Permalink: python/typing_extensions@f29cd28d8ed7642cafb1d18daf5aa41be6a5c0aa
 - Branch / Tag: refs/tags/4.16.0
 - Owner: https://github.com/python
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yml@f29cd28d8ed7642cafb1d18daf5aa41be6a5c0aa
 - Trigger Event: release

## File details

Details for the file typing_extensions-4.16.0-py3-none-any.whl.

### File metadata

- Download URL: typing_extensions-4.16.0-py3-none-any.whl
- Upload date:
 Jul 2, 2026
- Size: 45.6 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for typing_extensions-4.16.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8 | |
| MD5 | aaa249e7f620bbcecbcbf2b7b11fbd12 | |
| BLAKE2b-256 | 49d3b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for typing_extensions-4.16.0-py3-none-any.whl:

Publisher: publish.yml on python/typing_extensions

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: typing_extensions-4.16.0-py3-none-any.whl
 - Subject digest: 481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8
 - Sigstore transparency entry: 2045493716
 - Sigstore integration time:
 Jul 2, 2026
 Source repository:

 - Permalink: python/typing_extensions@f29cd28d8ed7642cafb1d18daf5aa41be6a5c0aa
 - Branch / Tag: refs/tags/4.16.0
 - Owner: https://github.com/python
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yml@f29cd28d8ed7642cafb1d18daf5aa41be6a5c0aa
 - Trigger Event: release

## Release history Release notifications |
 RSS feed

This release

4.16.0 This release

Jul 2, 2026
 2 files

Pre-release

4.16.0rc2

Jun 25, 2026
 2 files

Pre-release

4.16.0rc1

Jun 24, 2026
 2 files

4.15.0

Aug 25, 2025
 2 files

Pre-release

4.15.0rc1

Aug 18, 2025
 2 files

4.14.1

Jul 4, 2025
 2 files

4.14.0

Jun 2, 2025
 2 files

Pre-release

4.14.0rc1

May 24, 2025
 2 files

4.13.2

Apr 10, 2025
 2 files

4.13.1

Apr 3, 2025
 2 files

4.13.0

Mar 26, 2025
 2 files

Pre-release

4.13.0rc1

Mar 18, 2025
 2 files

4.12.2

Jun 7, 2024
 2 files

4.12.1

Jun 1, 2024
 2 files

4.12.0

May 24, 2024
 2 files

Pre-release

4.12.0rc1

May 16, 2024
 2 files

Pre-release

4.12.0a2

May 16, 2024
 2 files

4.11.0

Apr 5, 2024
 2 files

Pre-release

4.11.0rc1

Mar 24, 2024
 2 files

4.10.0

Feb 25, 2024
 2 files

Pre-release

4.10.0rc1

Feb 18, 2024
 2 files

4.9.0

Dec 10, 2023
 2 files

Pre-release

4.9.0rc1

Nov 29, 2023
 2 files

4.8.0

Sep 18, 2023
 2 files

Pre-release

4.8.0rc1

Sep 8, 2023
 2 files

4.7.1

Jul 2, 2023
 2 files

4.7.0

Jun 28, 2023
 2 files

Pre-release

4.7.0rc1

Jun 21, 2023
 2 files

4.6.3

Jun 1, 2023
 2 files

4.6.2

May 25, 2023
 2 files

4.6.1

May 24, 2023
 2 files

4.6.0

May 23, 2023
 2 files

4.5.0

Feb 15, 2023
 2 files

4.4.0

Oct 6, 2022
 2 files

4.3.0

Jul 1, 2022
 2 files

4.2.0

Apr 17, 2022
 2 files

4.1.1

Feb 14, 2022
 2 files

4.1.0

Feb 12, 2022
 2 files

4.0.1

Dec 1, 2021
 2 files

4.0.0

Nov 14, 2021
 2 files

3.10.0.2

Aug 30, 2021
 3 files

3.10.0.1

Aug 29, 2021
 3 files

3.10.0.0

May 1, 2021
 3 files

3.7.4.3

Aug 23, 2020
 3 files

3.7.4.2

Apr 2, 2020
 3 files

3.7.4.1

Oct 28, 2019
 3 files

3.7.4

Jun 19, 2019
 3 files

3.7.2

Jan 12, 2019
 3 files

3.6.6

Oct 6, 2018
 3 files

3.6.5

May 7, 2018
 3 files

3.6.2.1

Sep 30, 2017
 3 files

3.6.2

Sep 17, 2017
 3 files