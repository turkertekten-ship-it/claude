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

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

cryptography-50.0.1.tar.gz
 (880.4 kB
 view details)

Uploaded
 Aug 25, 2026
 Source

### Built Distributions

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

cryptography-50.0.1-pp311-pypy311_pp73-win_amd64.whl
 (3.8 MB
 view details)

Uploaded
 Aug 25, 2026
 PyPyWindows x86-64

cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 PyPymanylinux: glibc 2.34+ x86-64

cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 PyPymanylinux: glibc 2.34+ ARM64

cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 PyPymanylinux: glibc 2.28+ x86-64

cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 PyPymanylinux: glibc 2.28+ ARM64

cryptography-50.0.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl
 (4.0 MB
 view details)

Uploaded
 Aug 25, 2026
 PyPymacOS 11.0+ ARM64

cryptography-50.0.1-cp314-cp314t-win_amd64.whl
 (3.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tWindows x86-64

cryptography-50.0.1-cp314-cp314t-musllinux_1_2_x86_64.whl
 (5.0 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmusllinux: musl 1.2+ x86-64

cryptography-50.0.1-cp314-cp314t-musllinux_1_2_aarch64.whl
 (4.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmusllinux: musl 1.2+ ARM64

cryptography-50.0.1-cp314-cp314t-manylinux_2_34_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.34+ x86-64

cryptography-50.0.1-cp314-cp314t-manylinux_2_34_ppc64le.whl
 (5.3 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.34+ ppc64le

cryptography-50.0.1-cp314-cp314t-manylinux_2_34_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.34+ ARM64

cryptography-50.0.1-cp314-cp314t-manylinux_2_31_armv7l.whl
 (4.3 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.31+ ARMv7l

cryptography-50.0.1-cp314-cp314t-manylinux_2_28_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.28+ x86-64

cryptography-50.0.1-cp314-cp314t-manylinux_2_28_ppc64le.whl
 (5.3 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.28+ ppc64le

cryptography-50.0.1-cp314-cp314t-manylinux_2_28_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.28+ ARM64

cryptography-50.0.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.17+ x86-64

cryptography-50.0.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmanylinux: glibc 2.17+ ARM64

cryptography-50.0.1-cp314-cp314t-macosx_11_0_arm64.whl
 (4.0 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.14tmacOS 11.0+ ARM64

cryptography-50.0.1-cp311-abi3-win_amd64.whl
 (3.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+Windows x86-64

cryptography-50.0.1-cp311-abi3-musllinux_1_2_x86_64.whl
 (5.0 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+musllinux: musl 1.2+ x86-64

cryptography-50.0.1-cp311-abi3-musllinux_1_2_aarch64.whl
 (4.9 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+musllinux: musl 1.2+ ARM64

cryptography-50.0.1-cp311-abi3-manylinux_2_34_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.34+ x86-64

cryptography-50.0.1-cp311-abi3-manylinux_2_34_ppc64le.whl
 (5.3 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.34+ ppc64le

cryptography-50.0.1-cp311-abi3-manylinux_2_34_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.34+ ARM64

cryptography-50.0.1-cp311-abi3-manylinux_2_31_armv7l.whl
 (4.4 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.31+ ARMv7l

cryptography-50.0.1-cp311-abi3-manylinux_2_28_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.28+ x86-64

cryptography-50.0.1-cp311-abi3-manylinux_2_28_ppc64le.whl
 (5.4 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.28+ ppc64le

cryptography-50.0.1-cp311-abi3-manylinux_2_28_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.28+ ARM64

cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.17+ x86-64

cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+manylinux: glibc 2.17+ ARM64

cryptography-50.0.1-cp311-abi3-macosx_11_0_arm64.whl
 (4.0 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.11+macOS 11.0+ ARM64

cryptography-50.0.1-cp39-abi3-win_amd64.whl
 (3.9 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+Windows x86-64

cryptography-50.0.1-cp39-abi3-musllinux_1_2_x86_64.whl
 (5.0 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+musllinux: musl 1.2+ x86-64

cryptography-50.0.1-cp39-abi3-musllinux_1_2_aarch64.whl
 (4.9 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+musllinux: musl 1.2+ ARM64

cryptography-50.0.1-cp39-abi3-manylinux_2_34_x86_64.whl
 (4.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.34+ x86-64

cryptography-50.0.1-cp39-abi3-manylinux_2_34_ppc64le.whl
 (5.3 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.34+ ppc64le

cryptography-50.0.1-cp39-abi3-manylinux_2_34_aarch64.whl
 (4.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.34+ ARM64

cryptography-50.0.1-cp39-abi3-manylinux_2_31_armv7l.whl
 (4.4 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.31+ ARMv7l

cryptography-50.0.1-cp39-abi3-manylinux_2_28_x86_64.whl
 (4.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.28+ x86-64

cryptography-50.0.1-cp39-abi3-manylinux_2_28_ppc64le.whl
 (5.4 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.28+ ppc64le

cryptography-50.0.1-cp39-abi3-manylinux_2_28_aarch64.whl
 (4.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.28+ ARM64

cryptography-50.0.1-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
 (4.7 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.17+ x86-64

cryptography-50.0.1-cp39-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
 (4.8 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+manylinux: glibc 2.17+ ARM64

cryptography-50.0.1-cp39-abi3-macosx_11_0_arm64.whl
 (4.0 MB
 view details)

Uploaded
 Aug 25, 2026
 CPython 3.9+macOS 11.0+ ARM64

## File details

Details for the file cryptography-50.0.1.tar.gz.

### File metadata

- Download URL: cryptography-50.0.1.tar.gz
- Upload date:
 Aug 25, 2026
- Size: 880.4 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 5dd9bda1c12b4162f6ff568eeb5e0ff956c28d14406e875cfe8a63a2d414ff20 | |
| MD5 | 8b86292ecad42d61a097d7f31ecb774e | |
| BLAKE2b-256 | bbad5d6702db60b1e40b41ef513b6967ff5848f307d50f8449baf1634f5908f1 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1.tar.gz:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1.tar.gz
 - Subject digest: 5dd9bda1c12b4162f6ff568eeb5e0ff956c28d14406e875cfe8a63a2d414ff20
 - Sigstore transparency entry: 2588249963
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-pp311-pypy311_pp73-win_amd64.whl.

### File metadata

- Download URL: cryptography-50.0.1-pp311-pypy311_pp73-win_amd64.whl
- Upload date:
 Aug 25, 2026
- Size: 3.8 MB
- Tags: PyPy, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-pp311-pypy311_pp73-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 693c99b49bd37d0d096e4334c10232c77248c415b98d35236094cdf96d57258b | |
| MD5 | 7b035970199fa3c0863d84c65f3bd9a7 | |
| BLAKE2b-256 | 7144711e61f7d014be825ef79b285b047292d1bf893732ac1bc030a351fb517f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-pp311-pypy311_pp73-win_amd64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-pp311-pypy311_pp73-win_amd64.whl
 - Subject digest: 693c99b49bd37d0d096e4334c10232c77248c415b98d35236094cdf96d57258b
 - Sigstore transparency entry: 2588251043
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: PyPy, manylinux: glibc 2.34+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 804728ce710890870f3aaa344b2e161172d258d768ac139d02cfd9092d0d94e6 | |
| MD5 | f54df8242c068562ac1fa86ae527140c | |
| BLAKE2b-256 | 51cf5b3f53a0b74d122f023476ede40ba5d3e70d5cf475f73b899740d26a4fb2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_x86_64.whl
 - Subject digest: 804728ce710890870f3aaa344b2e161172d258d768ac139d02cfd9092d0d94e6
 - Sigstore transparency entry: 2588248512
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: PyPy, manylinux: glibc 2.34+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | d63ae8f6481fec907ac0f588eee8a90aefde112c633131fe540e5711ddbb5a4e | |
| MD5 | 4f9c49f67798cb849c1157e88be85488 | |
| BLAKE2b-256 | 1de0e786934472e3ac4ecdecc7b129a0ca1a2a40dffdafcf2c3ea9d4397f8def | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_34_aarch64.whl
 - Subject digest: d63ae8f6481fec907ac0f588eee8a90aefde112c633131fe540e5711ddbb5a4e
 - Sigstore transparency entry: 2588250408
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: PyPy, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | fb4b9672d389c738b175c4166e78310f8a70358886aacd9173ee03a85ffdc671 | |
| MD5 | 03847517689359e9f0963a87ecc719b0 | |
| BLAKE2b-256 | 73355c3717edf9e68a0550ce04e28eab493fe545eccd81742af03f6a75fe260b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_x86_64.whl
 - Subject digest: fb4b9672d389c738b175c4166e78310f8a70358886aacd9173ee03a85ffdc671
 - Sigstore transparency entry: 2588250167
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: PyPy, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 5fe939deeb161024a6be98229c953b6591fef1f41214497a78fe793a244c017f | |
| MD5 | 55ac66c23f610a243dca233a02c582fc | |
| BLAKE2b-256 | 149a6d3a4d7852e22d657438b7bf51f66102c7d71c0e1fafeec652281d0403e5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-pp311-pypy311_pp73-manylinux_2_28_aarch64.whl
 - Subject digest: 5fe939deeb161024a6be98229c953b6591fef1f41214497a78fe793a244c017f
 - Sigstore transparency entry: 2588237428
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl.

### File metadata

- Download URL: cryptography-50.0.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.0 MB
- Tags: PyPy, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 9cb3cb952cf5a8abd50c782a98a89d71699715e802fe349704b47f2425b42a94 | |
| MD5 | 722c7ccc5162ff24c65a65352f1e2684 | |
| BLAKE2b-256 | c7278d207af749c453ee17ea087340b3f2b4adef75aadd1d277b1b129bdda84e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl
 - Subject digest: 9cb3cb952cf5a8abd50c782a98a89d71699715e802fe349704b47f2425b42a94
 - Sigstore transparency entry: 2588251198
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-win_amd64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-win_amd64.whl
- Upload date:
 Aug 25, 2026
- Size: 3.8 MB
- Tags: CPython 3.14t, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | f74455bb086a85d5e81246412602aaa97ed095e504cd40dd261ef50be42205bf | |
| MD5 | ffeaa29d60b56b889f04d9b778a585cc | |
| BLAKE2b-256 | 4d56bc4f2b209e766c93372cfcd59b781a0b2b59700f62a969580415b699c2b2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-win_amd64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-win_amd64.whl
 - Subject digest: f74455bb086a85d5e81246412602aaa97ed095e504cd40dd261ef50be42205bf
 - Sigstore transparency entry: 2588224334
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 5.0 MB
- Tags: CPython 3.14t, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 42be3bb70596b3abe4ac097b75be223e8b3ab614a0e5de068e3dcc54d71d6149 | |
| MD5 | 0019730a588c76ed9f46177afc6fa7b0 | |
| BLAKE2b-256 | 2dfd60d0ddf4defa12e482c9d5e0f554384d6e8ab25341fd15f060028fd92e6a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-musllinux_1_2_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-musllinux_1_2_x86_64.whl
 - Subject digest: 42be3bb70596b3abe4ac097b75be223e8b3ab614a0e5de068e3dcc54d71d6149
 - Sigstore transparency entry: 2588246919
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.8 MB
- Tags: CPython 3.14t, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 330fbb252391c596f1ae42c5754449dc924e6ad012dca8efe0d703f9f2d12ec6 | |
| MD5 | 31408918f84c4a8c2a48dee50d983738 | |
| BLAKE2b-256 | 9eb9e7425ebfb599241a0c1d7000f1b466c3062da66c19d9525031315dff7213 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-musllinux_1_2_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-musllinux_1_2_aarch64.whl
 - Subject digest: 330fbb252391c596f1ae42c5754449dc924e6ad012dca8efe0d703f9f2d12ec6
 - Sigstore transparency entry: 2588248289
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux_2_34_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux_2_34_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.14t, manylinux: glibc 2.34+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux_2_34_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 79bf008d1f9af6071c797ad133e39915dfee7614f18f18f4db9072eb715064a3 | |
| MD5 | edbb73318c49cd2890858ae48372ae4e | |
| BLAKE2b-256 | 1a010127d11a762b31a9ee0221894f540318761783f3fdc4bc5d057698caebd5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux_2_34_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux_2_34_x86_64.whl
 - Subject digest: 79bf008d1f9af6071c797ad133e39915dfee7614f18f18f4db9072eb715064a3
 - Sigstore transparency entry: 2588217649
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux_2_34_ppc64le.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux_2_34_ppc64le.whl
- Upload date:
 Aug 25, 2026
- Size: 5.3 MB
- Tags: CPython 3.14t, manylinux: glibc 2.34+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux_2_34_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 16c5ecd954b3330ebfb6605eca4fd952da8bef376551d5cc264534e3770a9ee6 | |
| MD5 | 89c28a9248f44ec238dfe9fce1aef09e | |
| BLAKE2b-256 | b11bec3ebd31741d0e963612c4fe43caa39341b9b1e031e469820e42e4c83918 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux_2_34_ppc64le.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux_2_34_ppc64le.whl
 - Subject digest: 16c5ecd954b3330ebfb6605eca4fd952da8bef376551d5cc264534e3770a9ee6
 - Sigstore transparency entry: 2588243739
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux_2_34_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux_2_34_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.14t, manylinux: glibc 2.34+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux_2_34_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | cbf74a81765ee67413503ca6e26dcc4f6f5a519822436cc0a1b97aab6c1b8a17 | |
| MD5 | 12ba8b8e4e2156d2aad1c7efd502a499 | |
| BLAKE2b-256 | 88ddb215616f9bab3fc18510c78a4e5c9f362d77838503c363dc747c7d4f5c6f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux_2_34_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux_2_34_aarch64.whl
 - Subject digest: cbf74a81765ee67413503ca6e26dcc4f6f5a519822436cc0a1b97aab6c1b8a17
 - Sigstore transparency entry: 2588220904
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux_2_31_armv7l.whl
- Upload date:
 Aug 25, 2026
- Size: 4.3 MB
- Tags: CPython 3.14t, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | ac02b07824d4d1001bd4367599f839c19cb171924c796e52c23508ac14c2c0cc | |
| MD5 | 92601eefb41f437abf64d7ff6bae2fda | |
| BLAKE2b-256 | 390da1e7633e2c744d0f2983320a27e924ef2264c79c56e1a58d5fb0a1cfd413 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux_2_31_armv7l.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux_2_31_armv7l.whl
 - Subject digest: ac02b07824d4d1001bd4367599f839c19cb171924c796e52c23508ac14c2c0cc
 - Sigstore transparency entry: 2588218145
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux_2_28_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.14t, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 8df2de9102026855887e4587084f6eabd80ed0f345b8ad8a7ac27ab9bf4723e0 | |
| MD5 | cc47fbc9daff1ed45d4331ff7cb919a7 | |
| BLAKE2b-256 | 4792b4317e8c32c4f47b062f5398bd79106b220a124546f42be83bf32b761e2a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux_2_28_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux_2_28_x86_64.whl
 - Subject digest: 8df2de9102026855887e4587084f6eabd80ed0f345b8ad8a7ac27ab9bf4723e0
 - Sigstore transparency entry: 2588231889
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 25, 2026
- Size: 5.3 MB
- Tags: CPython 3.14t, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | a255449073358275b64b67d3f595f268bbef70e72b6edb65e0c70c735bf739c9 | |
| MD5 | 955dfaa90ff1f200143a36ccb865240e | |
| BLAKE2b-256 | f66e1cf405c5c8e8df7545378048e954792f00b7f2367af8863ce8b8f3e10607 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux_2_28_ppc64le.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux_2_28_ppc64le.whl
 - Subject digest: a255449073358275b64b67d3f595f268bbef70e72b6edb65e0c70c735bf739c9
 - Sigstore transparency entry: 2588226976
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux_2_28_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.14t, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | a8f40ea47330e71b594a7e246898f93177c259490c63183dbaf9e571d71ed9a5 | |
| MD5 | db2f1aa5945aba58ca3d9f8765c9c674 | |
| BLAKE2b-256 | 08bded5396be499ffcf8807a585bfe38b71a1fbdd1c342b4f9b6d0ef5162a946 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux_2_28_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux_2_28_aarch64.whl
 - Subject digest: a8f40ea47330e71b594a7e246898f93177c259490c63183dbaf9e571d71ed9a5
 - Sigstore transparency entry: 2588250661
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 8921d58f426793c5f1b47f0b59575780de9a095214958d0eb37d909593db8367 | |
| MD5 | 05b69069fe3a8080e1417639b9a73929 | |
| BLAKE2b-256 | b4f2bb1f56e10815b789df0b409a69fa4992ff3d3fef9c72747f4a6b26fed38e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
 - Subject digest: 8921d58f426793c5f1b47f0b59575780de9a095214958d0eb37d909593db8367
 - Sigstore transparency entry: 2588241194
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | a0b1a59e3a089064a0ec309e9428c8e3ae4e161419d20ac33600767e83fc658a | |
| MD5 | 8d696225982ec0da15671b6a10bd7a78 | |
| BLAKE2b-256 | 4d723a2711d967977ab5fc80b782837c7e8d1ac7445e764c20c381a265c57ef3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
 - Subject digest: a0b1a59e3a089064a0ec309e9428c8e3ae4e161419d20ac33600767e83fc658a
 - Sigstore transparency entry: 2588248858
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp314-cp314t-macosx_11_0_arm64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp314-cp314t-macosx_11_0_arm64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.0 MB
- Tags: CPython 3.14t, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp314-cp314t-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 30a125032e5642a21ff816e021152bd4e7e94f03eff3f4b7fca41cd22bc3110f | |
| MD5 | 43e1f79917e3ce5e55ca00e60873c5d3 | |
| BLAKE2b-256 | 5bf0424cb557d99aa86ac55da5e2add02e2882e44047b6264f93ade1b975a993 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp314-cp314t-macosx_11_0_arm64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp314-cp314t-macosx_11_0_arm64.whl
 - Subject digest: 30a125032e5642a21ff816e021152bd4e7e94f03eff3f4b7fca41cd22bc3110f
 - Sigstore transparency entry: 2588218814
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-win_amd64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-win_amd64.whl
- Upload date:
 Aug 25, 2026
- Size: 3.8 MB
- Tags: CPython 3.11+, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | aed8db4f6d71c51efb89530e12d9464e7bf2923d46c3205dc794a2a93f8c0648 | |
| MD5 | e98d9c3ab027067090f3a0fb7af91a3c | |
| BLAKE2b-256 | 428bcb12b1b60c91b074ca6bf0fdd59aa8f10d8bc5f73af8faece86ef0421b37 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-win_amd64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-win_amd64.whl
 - Subject digest: aed8db4f6d71c51efb89530e12d9464e7bf2923d46c3205dc794a2a93f8c0648
 - Sigstore transparency entry: 2588247238
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 5.0 MB
- Tags: CPython 3.11+, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 9ebcdd5519be9b652a46f507817a74591774fc3d6923ac364e4dfa64e36b291b | |
| MD5 | 247cf1f0a5132f96faf53cc54384c911 | |
| BLAKE2b-256 | 7e22c3654cccc856e9d682817b04ac3ee79731cb09ca6f95996a95c904de2883 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-musllinux_1_2_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-musllinux_1_2_x86_64.whl
 - Subject digest: 9ebcdd5519be9b652a46f507817a74591774fc3d6923ac364e4dfa64e36b291b
 - Sigstore transparency entry: 2588250925
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.9 MB
- Tags: CPython 3.11+, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | be224a65493ec5b74a158ff22a5522ce4a5ca1e543c647a3a4730d4a09e5f959 | |
| MD5 | 8299b3ed56e9275dd30a187ceb158cfe | |
| BLAKE2b-256 | 130eb1f92e013228111413f2e6743948b80bc24dfd3c1b87ba98ceea16f5df89 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-musllinux_1_2_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-musllinux_1_2_aarch64.whl
 - Subject digest: be224a65493ec5b74a158ff22a5522ce4a5ca1e543c647a3a4730d4a09e5f959
 - Sigstore transparency entry: 2588238892
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux_2_34_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux_2_34_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.11+, manylinux: glibc 2.34+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux_2_34_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 51afcfceb15597cf2635068e4ac9a56b2abde622edde17f37d85fd7b5306497a | |
| MD5 | 91fe20c2bf06e167eacec9e3b25281e1 | |
| BLAKE2b-256 | 85666ccca4722987ddedaa7fc9c3f4708af7431f5535666c174350830888c6b7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux_2_34_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux_2_34_x86_64.whl
 - Subject digest: 51afcfceb15597cf2635068e4ac9a56b2abde622edde17f37d85fd7b5306497a
 - Sigstore transparency entry: 2588243178
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux_2_34_ppc64le.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux_2_34_ppc64le.whl
- Upload date:
 Aug 25, 2026
- Size: 5.3 MB
- Tags: CPython 3.11+, manylinux: glibc 2.34+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux_2_34_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 76de83fbd91ac49c0feaaa983d0748fd7a53176afac5fb3bf7478d244f0eb527 | |
| MD5 | 4b5baccf2ef89511d3518ec1a1c2e217 | |
| BLAKE2b-256 | e33845abd72ef63f2e7d0754a6cacf97bd8b69512ace7f6130d24c39ece65da2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux_2_34_ppc64le.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux_2_34_ppc64le.whl
 - Subject digest: 76de83fbd91ac49c0feaaa983d0748fd7a53176afac5fb3bf7478d244f0eb527
 - Sigstore transparency entry: 2588249327
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux_2_34_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux_2_34_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.11+, manylinux: glibc 2.34+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux_2_34_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | e2ca8fd1b6b4b82a1c4cb02841d0837e3c12336c2e24b520ab8ab3b969733d8f | |
| MD5 | 3884f29854fc68e6eb8494bba07016b9 | |
| BLAKE2b-256 | 393be96c1ef71edef71057c7e3c3d982ce8fda554e0c52d0cc19c18845cde3eb | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux_2_34_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux_2_34_aarch64.whl
 - Subject digest: e2ca8fd1b6b4b82a1c4cb02841d0837e3c12336c2e24b520ab8ab3b969733d8f
 - Sigstore transparency entry: 2588236870
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux_2_31_armv7l.whl
- Upload date:
 Aug 25, 2026
- Size: 4.4 MB
- Tags: CPython 3.11+, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 359e62deae718bce96170e223fdcb6357e4fbd3bb7a3a75f4430763532560e49 | |
| MD5 | 99b1d057a2a2496f83f758be239e41de | |
| BLAKE2b-256 | 29ba042ca458b8c64348c768284b5d23e69b92ed53d057ab779fee628564676d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux_2_31_armv7l.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux_2_31_armv7l.whl
 - Subject digest: 359e62deae718bce96170e223fdcb6357e4fbd3bb7a3a75f4430763532560e49
 - Sigstore transparency entry: 2588239075
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux_2_28_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.11+, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 51593d180cf6d179bde5c5d065bed81386b1f381656ae7d042b7ffc87a9895ad | |
| MD5 | d0a7216304899e8e16b7f1197f93d1f3 | |
| BLAKE2b-256 | e11b82f0f0d8858d4432be1af790477edf62aef90324041aa07c57e57bef1af7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux_2_28_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux_2_28_x86_64.whl
 - Subject digest: 51593d180cf6d179bde5c5d065bed81386b1f381656ae7d042b7ffc87a9895ad
 - Sigstore transparency entry: 2588231425
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 25, 2026
- Size: 5.4 MB
- Tags: CPython 3.11+, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 5fe002589592ed749ce77fe0695fcbd3500dd61d7d6db5858a7544c612fa8e45 | |
| MD5 | 3b86ac144234b823f9d3eeb149c75f75 | |
| BLAKE2b-256 | 553238c0d344b98c06d34b5df8946565a9c0d6dbf32c8e0730a7f05f0a3c6cab | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux_2_28_ppc64le.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux_2_28_ppc64le.whl
 - Subject digest: 5fe002589592ed749ce77fe0695fcbd3500dd61d7d6db5858a7544c612fa8e45
 - Sigstore transparency entry: 2588250756
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux_2_28_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.11+, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | e74591e283fe6eb956416c929eb58262a719fe0311fd9054c62c3350ed8760d8 | |
| MD5 | 1808fcb300081052b1cc043a06c42921 | |
| BLAKE2b-256 | e6ded3cdc2815697aae84126cbd6a030ca7b6b452e28a88b501b836bd3aa7a86 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux_2_28_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux_2_28_aarch64.whl
 - Subject digest: e74591e283fe6eb956416c929eb58262a719fe0311fd9054c62c3350ed8760d8
 - Sigstore transparency entry: 2588223520
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.11+, manylinux: glibc 2.17+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | ff838d62ec1bfce4f9ba7fa16f4a7b554cd8d0c299e6be37502161a660c84eef | |
| MD5 | e20b405396d6246d101d577f26dc265b | |
| BLAKE2b-256 | 5726e6d4fc8512a51a5f9ee7bfdbfb853bce1197087df40c9ad993ad370b846f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
 - Subject digest: ff838d62ec1bfce4f9ba7fa16f4a7b554cd8d0c299e6be37502161a660c84eef
 - Sigstore transparency entry: 2588233852
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.11+, manylinux: glibc 2.17+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 53e279950892dc102c6b4e52af03ae5ea92fac572a1ddab78ca73a997f62b69f | |
| MD5 | 228753715588afb10b49701e04050735 | |
| BLAKE2b-256 | 90349ce9a62ed9dc82ca9fd6a34445b6904af56e5f38b3eae2ed32e49c36053d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
 - Subject digest: 53e279950892dc102c6b4e52af03ae5ea92fac572a1ddab78ca73a997f62b69f
 - Sigstore transparency entry: 2588235727
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp311-abi3-macosx_11_0_arm64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp311-abi3-macosx_11_0_arm64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.0 MB
- Tags: CPython 3.11+, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp311-abi3-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | b8f852c65863251b9e3a1b8c150ce21e59b522dbb6a7d4bc80e680d38388e986 | |
| MD5 | 890a4b4173df1d41d4137c2e3249fe69 | |
| BLAKE2b-256 | ba19797e2aaac9df6a66f1550f49979dc1b1e39ecd2077501c30efa81e8d5d67 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp311-abi3-macosx_11_0_arm64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp311-abi3-macosx_11_0_arm64.whl
 - Subject digest: b8f852c65863251b9e3a1b8c150ce21e59b522dbb6a7d4bc80e680d38388e986
 - Sigstore transparency entry: 2588250525
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-win_amd64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-win_amd64.whl
- Upload date:
 Aug 25, 2026
- Size: 3.9 MB
- Tags: CPython 3.9+, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 55d16b1ef3ee0958d893a977b19777887e546c9954ea81b200c3301a864013f2 | |
| MD5 | 8b26ff600d373c82f986d0a4e38a9056 | |
| BLAKE2b-256 | 998987ef49ffe383ef4e147d27b7bf2088fb0b54ea409dd87b5a89442e5828a5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-win_amd64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-win_amd64.whl
 - Subject digest: 55d16b1ef3ee0958d893a977b19777887e546c9954ea81b200c3301a864013f2
 - Sigstore transparency entry: 2588238431
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 5.0 MB
- Tags: CPython 3.9+, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 2a93d05e34d5f67fba6f891fe85d929999baa7195e853923ea6d7576c9e68c5e | |
| MD5 | 8948947020c40b53bb43b72919d48e85 | |
| BLAKE2b-256 | 1fab89e2b798d2c3925f82e2bb72d5979f3d2f6da2dd22ef4a8cd8b70d920039 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-musllinux_1_2_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-musllinux_1_2_x86_64.whl
 - Subject digest: 2a93d05e34d5f67fba6f891fe85d929999baa7195e853923ea6d7576c9e68c5e
 - Sigstore transparency entry: 2588229904
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.9 MB
- Tags: CPython 3.9+, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | fd3718b960d0b5dd213cdf03f3bcb7000e69dda0de8b956061947ff6bcff5558 | |
| MD5 | 708fbb3f2cf34dd8a193e62551dd98c9 | |
| BLAKE2b-256 | 638ef1f955e0921dd2b6d22eae7e8d24a4c4b638d10735ffbf6a71f99eb0fcb8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-musllinux_1_2_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-musllinux_1_2_aarch64.whl
 - Subject digest: fd3718b960d0b5dd213cdf03f3bcb7000e69dda0de8b956061947ff6bcff5558
 - Sigstore transparency entry: 2588229076
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux_2_34_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux_2_34_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.8 MB
- Tags: CPython 3.9+, manylinux: glibc 2.34+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux_2_34_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 9dde0a357190eb3b1da1bb9ab750e9c85cba82ca5977aa0836cbb94e92611239 | |
| MD5 | dddbe321dcf264f0479b3b0d0cc40fd2 | |
| BLAKE2b-256 | 8ceb5d7124083e8d8cda8f5b348f544b71ad6f707ad63193758ef4d8e569da02 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux_2_34_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux_2_34_x86_64.whl
 - Subject digest: 9dde0a357190eb3b1da1bb9ab750e9c85cba82ca5977aa0836cbb94e92611239
 - Sigstore transparency entry: 2588224730
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux_2_34_ppc64le.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux_2_34_ppc64le.whl
- Upload date:
 Aug 25, 2026
- Size: 5.3 MB
- Tags: CPython 3.9+, manylinux: glibc 2.34+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux_2_34_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | fc3ed7ebd2a8c96f5b166de0ab9b624996bef3b07bbeb19364dfb78222c22c80 | |
| MD5 | c00503118020438e833848088e287df4 | |
| BLAKE2b-256 | dd04557fc5ead96a829e0bc812a3b9dc4a52a2f27e4f7f5950da7ff27653a805 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux_2_34_ppc64le.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux_2_34_ppc64le.whl
 - Subject digest: fc3ed7ebd2a8c96f5b166de0ab9b624996bef3b07bbeb19364dfb78222c22c80
 - Sigstore transparency entry: 2588250264
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux_2_34_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux_2_34_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.8 MB
- Tags: CPython 3.9+, manylinux: glibc 2.34+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux_2_34_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 01f41478cf33fc605a6a089cd56d28b45c6c0b45a1928b61797f2621a04bac71 | |
| MD5 | ae97b0b1437e5e5e367ef0525bdb9948 | |
| BLAKE2b-256 | 84d57d1fe1cb93f91c428093ff234e128c89ba8ea61a6f26aab406081f9b996e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux_2_34_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux_2_34_aarch64.whl
 - Subject digest: 01f41478cf33fc605a6a089cd56d28b45c6c0b45a1928b61797f2621a04bac71
 - Sigstore transparency entry: 2588240342
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux_2_31_armv7l.whl
- Upload date:
 Aug 25, 2026
- Size: 4.4 MB
- Tags: CPython 3.9+, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 2b34d76a652ea2b6faf777c35df230c5637842cd904e04f16230c3f9f03e4361 | |
| MD5 | 8c64406d0e46f5464148e87eed36cb5f | |
| BLAKE2b-256 | 0d5c13ea642e08e2544d0f5396122055f4820cfacb3203562197b5967125ea97 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux_2_31_armv7l.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux_2_31_armv7l.whl
 - Subject digest: 2b34d76a652ea2b6faf777c35df230c5637842cd904e04f16230c3f9f03e4361
 - Sigstore transparency entry: 2588244986
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux_2_28_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.8 MB
- Tags: CPython 3.9+, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 407fe2b6db00939c05c0e945e9914238f2f0a430974839429dafc82b1ee6bee5 | |
| MD5 | a97c6090cfacf099a4393a56a4c09b80 | |
| BLAKE2b-256 | d6513f9701867a46b6c1740c9b52fc4d3bed6cbdcfedcc9b6e64305c07f39cff | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux_2_28_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux_2_28_x86_64.whl
 - Subject digest: 407fe2b6db00939c05c0e945e9914238f2f0a430974839429dafc82b1ee6bee5
 - Sigstore transparency entry: 2588249626
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 25, 2026
- Size: 5.4 MB
- Tags: CPython 3.9+, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 2ebbfb0f1fed745e91796e3e1080a1440423fdae8ece1b995a1d80883a409054 | |
| MD5 | 07d49a2ca61ac14f0d494fc28bd208a4 | |
| BLAKE2b-256 | 6e2b214cf0cf93db9628c3c20c896b229f327f6fb1b20e4b3743d8ad3f00af8b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux_2_28_ppc64le.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux_2_28_ppc64le.whl
 - Subject digest: 2ebbfb0f1fed745e91796e3e1080a1440423fdae8ece1b995a1d80883a409054
 - Sigstore transparency entry: 2588227188
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux_2_28_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.8 MB
- Tags: CPython 3.9+, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 4c4188f7c0cf655be5c06342b817ed0f9595b69ffa2b12026e5353eed29dea88 | |
| MD5 | d04f8bb9353a4af7024b2840c6ad2644 | |
| BLAKE2b-256 | 273a3c5f80daa4dcd47323c7af8a2fcb90de27a33564d4fcac69846c0972691a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux_2_28_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux_2_28_aarch64.whl
 - Subject digest: 4c4188f7c0cf655be5c06342b817ed0f9595b69ffa2b12026e5353eed29dea88
 - Sigstore transparency entry: 2588227483
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.7 MB
- Tags: CPython 3.9+, manylinux: glibc 2.17+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | e22dfed744bd4002e909464cb23d2f0b05c6f3113a79ef2e9864a53db737c733 | |
| MD5 | 12937413f1b22da97ca8b733223863ed | |
| BLAKE2b-256 | 7e3c0e77bd5ffcf078e9dd27d3074aad6c030d9b10d0bf69329d573c927a188c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux2014_x86_64.manylinux_2_17_x86_64.whl
 - Subject digest: e22dfed744bd4002e909464cb23d2f0b05c6f3113a79ef2e9864a53db737c733
 - Sigstore transparency entry: 2588251131
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.8 MB
- Tags: CPython 3.9+, manylinux: glibc 2.17+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 05ba322c4da95b262a212c345af888ef2c37c88c0509756ea00a0e6d68850f23 | |
| MD5 | d861dbb5941744ffffe58bf4bf735fb6 | |
| BLAKE2b-256 | 5ea59ec7e81e8526c0d7a387d73386b2daed3f39e10d81a85930bd1b6bfba65c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.whl
 - Subject digest: 05ba322c4da95b262a212c345af888ef2c37c88c0509756ea00a0e6d68850f23
 - Sigstore transparency entry: 2588232397
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## File details

Details for the file cryptography-50.0.1-cp39-abi3-macosx_11_0_arm64.whl.

### File metadata

- Download URL: cryptography-50.0.1-cp39-abi3-macosx_11_0_arm64.whl
- Upload date:
 Aug 25, 2026
- Size: 4.0 MB
- Tags: CPython 3.9+, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: uv/0.12.5 {"installer":{"name":"uv","version":"0.12.5","subcommand":["publish"]},"python":null,"implementation":{"name":null,"version":null},"distro":{"name":"Ubuntu","version":"24.04","id":"noble","libc":null},"system":{"name":null,"release":null},"cpu":null,"openssl_version":null,"setuptools_version":null,"rustc_version":null,"ci":true}

### File hashes

Hashes for cryptography-50.0.1-cp39-abi3-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | ca83d00d9e69cd5eb63f2e69c3a5a59e0cecae5ae14c6ae0b35830fe3b37bad0 | |
| MD5 | e064ce95764cf9908d6f64936ad952a8 | |
| BLAKE2b-256 | 84a9ee16a903f13755e914d1eecc482fe64d1f10761c3960e5d8fa6837377aff | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for cryptography-50.0.1-cp39-abi3-macosx_11_0_arm64.whl:

Publisher: pypi-publish.yml on pyca/cryptography

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: cryptography-50.0.1-cp39-abi3-macosx_11_0_arm64.whl
 - Subject digest: ca83d00d9e69cd5eb63f2e69c3a5a59e0cecae5ae14c6ae0b35830fe3b37bad0
 - Sigstore transparency entry: 2588222002
 - Sigstore integration time:
 Aug 25, 2026
 Source repository:

 - Permalink: pyca/cryptography@dc1125347f52b36b7070332910c680e68db0f478
 - Branch / Tag: refs/heads/main
 - Owner: https://github.com/pyca
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 pypi-publish.yml@dc1125347f52b36b7070332910c680e68db0f478
 - Trigger Event: workflow_run

## Release history Release notifications |
 RSS feed

This release

50.0.1 This release

Aug 25, 2026
 46 files

50.0.0

Jul 31, 2026
 46 files

49.0.0

Jun 12, 2026
 46 files

48.0.1

Jun 9, 2026
 49 files

48.0.0

May 4, 2026
 49 files

47.0.0

Apr 24, 2026
 49 files

46.0.7

Apr 8, 2026
 49 files

46.0.6

Mar 25, 2026
 49 files

46.0.5

Feb 10, 2026
 49 files

46.0.4

Jan 28, 2026
 49 files

46.0.3

Oct 15, 2025
 54 files

46.0.2

Oct 1, 2025
 54 files

46.0.1

Sep 17, 2025
 54 files

46.0.0

Sep 16, 2025
 54 files

45.0.7

Sep 1, 2025
 37 files

45.0.6

Aug 5, 2025
 37 files

45.0.5

Jul 2, 2025
 37 files

45.0.4

Jun 10, 2025
 37 files

45.0.3

May 25, 2025
 37 files

45.0.2

May 18, 2025
 37 files

45.0.1

May 17, 2025
 37 files

Yanked

45.0.0

May 17, 2025
 37 files

44.0.3

May 2, 2025
 37 files

44.0.2

Mar 2, 2025
 35 files

44.0.1

Feb 11, 2025
 31 files

44.0.0

Nov 27, 2024
 27 files

43.0.3

Oct 18, 2024
 27 files

43.0.1

Sep 3, 2024
 27 files

43.0.0

Jul 20, 2024
 27 files

42.0.8

Jun 4, 2024
 32 files

42.0.7

May 6, 2024
 32 files

42.0.6

May 4, 2024
 32 files

42.0.5

Feb 24, 2024
 32 files

42.0.4

Feb 21, 2024
 32 files

42.0.3

Feb 16, 2024
 32 files

42.0.2

Jan 30, 2024
 32 files

42.0.1

Jan 25, 2024
 32 files

42.0.0

Jan 23, 2024
 32 files

41.0.7

Nov 28, 2023
 23 files

41.0.6

Nov 27, 2023
 23 files

41.0.5

Oct 24, 2023
 23 files

41.0.4

Sep 19, 2023
 23 files

41.0.3

Aug 1, 2023
 23 files

41.0.2

Jul 11, 2023
 23 files

41.0.1

Jun 1, 2023
 19 files

41.0.0

May 30, 2023
 19 files

40.0.2

Apr 14, 2023
 19 files

40.0.1

Mar 25, 2023
 19 files

40.0.0

Mar 24, 2023
 19 files

39.0.2

Mar 2, 2023
 23 files

39.0.1

Feb 7, 2023
 23 files

39.0.0

Jan 2, 2023
 23 files

38.0.4

Nov 27, 2022
 26 files

38.0.3

Nov 1, 2022
 26 files

Yanked

38.0.2

Oct 11, 2022
 26 files

38.0.1

Sep 7, 2022
 26 files

38.0.0

Sep 7, 2022
 26 files

37.0.4

Jul 5, 2022
 22 files

Yanked

37.0.3

Jun 21, 2022
 22 files

37.0.2

May 4, 2022
 22 files

37.0.1

Apr 27, 2022
 22 files

37.0.0

Apr 26, 2022
 22 files

36.0.2

Mar 15, 2022
 20 files

36.0.1

Dec 14, 2021
 20 files

36.0.0

Nov 21, 2021
 21 files

35.0.0

Sep 30, 2021
 20 files

3.4.8

Aug 24, 2021
 19 files

3.4.7

Mar 25, 2021
 14 files

3.4.6

Feb 16, 2021
 12 files

3.4.5

Feb 13, 2021
 7 files

3.4.4

Feb 9, 2021
 7 files

3.4.3

Feb 9, 2021
 7 files

3.4.2

Feb 8, 2021
 7 files

3.4.1

Feb 7, 2021
 7 files

3.4

Feb 7, 2021
 8 files

3.3.2

Feb 7, 2021
 14 files

3.3.1

Dec 10, 2020
 14 files

3.3

Dec 9, 2020
 14 files

3.2.1

Oct 28, 2020
 22 files

3.2

Oct 26, 2020
 22 files

3.1.1

Sep 22, 2020
 22 files

3.1

Aug 27, 2020
 22 files

3.0

Jul 20, 2020
 19 files

2.9.2

Apr 22, 2020
 19 files

2.9.1

Apr 21, 2020
 19 files

2.9

Apr 2, 2020
 19 files

2.8

Oct 17, 2019
 21 files

2.7

May 30, 2019
 16 files

2.6.1

Feb 27, 2019
 19 files

2.6

Feb 27, 2019
 19 files

2.5

Jan 22, 2019
 19 files

2.4.2

Nov 21, 2018
 19 files

2.4.1

Nov 12, 2018
 19 files

2.4

Nov 12, 2018
 13 files

2.3.1

Aug 14, 2018
 19 files

2.3

Jul 18, 2018
 19 files

2.2.2

Mar 27, 2018
 19 files

2.2.1

Mar 20, 2018
 17 files

2.2

Mar 19, 2018
 17 files

2.1.4

Nov 30, 2017
 23 files

2.1.3

Nov 2, 2017
 23 files

2.1.2

Oct 24, 2017
 23 files

2.1.1

Oct 12, 2017
 27 files

2.1

Oct 11, 2017
 27 files

2.0.3

Aug 3, 2017
 30 files

2.0.2

Jul 27, 2017
 30 files

2.0.1

Jul 26, 2017
 30 files

2.0

Jul 17, 2017
 32 files

1.9

May 30, 2017
 18 files

1.8.2

May 26, 2017
 26 files

1.8.1

Mar 10, 2017
 26 files

1.8

Mar 10, 2017
 26 files

1.7.2

Jan 27, 2017
 19 files

1.7.1

Dec 13, 2016
 26 files

1.7

Dec 12, 2016
 22 files

1.6

Nov 22, 2016
 22 files

1.5.3

Nov 6, 2016
 22 files

1.5.2

Sep 26, 2016
 22 files

1.5.1

Sep 22, 2016
 22 files

1.5

Aug 26, 2016
 22 files

1.4

Jun 4, 2016
 22 files

1.3.4

Jun 3, 2016
 22 files

1.3.3

Jun 2, 2016
 17 files

1.3.2

May 4, 2016
 17 files

1.3.1

Mar 21, 2016
 24 files

1.3

Mar 18, 2016
 21 files

1.2.3

Mar 2, 2016
 21 files

1.2.2

Jan 29, 2016
 21 files

1.2.1

Jan 8, 2016
 21 files

1.2

Jan 8, 2016
 21 files

1.1.2

Dec 10, 2015
 21 files

1.1.1

Nov 19, 2015
 21 files

1.1

Oct 28, 2015
 17 files

1.0.2

Sep 27, 2015
 17 files

1.0.1

Sep 6, 2015
 16 files

1.0

Aug 12, 2015
 9 files

0.9.3

Jul 9, 2015
 9 files

0.9.2

Jul 3, 2015
 9 files

0.9.1

Jun 6, 2015
 9 files

0.9

May 14, 2015
 9 files

0.8.2

Apr 11, 2015
 11 files

0.8.1

Mar 20, 2015
 11 files

0.8

Mar 9, 2015
 11 files

0.7.2

Jan 16, 2015
 11 files

0.7.1

Dec 29, 2014
 11 files

0.7

Dec 18, 2014
 11 files

0.6.1

Oct 16, 2014
 11 files

0.6

Sep 30, 2014
 11 files

0.5.4

Aug 21, 2014
 11 files

0.5.3

Aug 7, 2014
 11 files

0.5.2

Jul 10, 2014
 11 files

0.5.1

Jul 8, 2014
 11 files

0.5

Jul 7, 2014
 11 files

0.4

May 3, 2014
 11 files

0.3

Mar 27, 2014
 6 files

0.2.2

Mar 4, 2014
 5 files

0.2.1

Feb 22, 2014
 5 files

0.2

Feb 20, 2014
 5 files

0.1

Jan 8, 2014
 1 file