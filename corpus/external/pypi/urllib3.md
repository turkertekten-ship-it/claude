# [image: urllib3]

[image: PyPI Version] [image: Python Versions] [image: Join our Discord] [image: Coverage Status] [image: Build Status on GitHub] [image: Documentation Status]
 [image: OpenSSF Scorecard] [image: SLSA 3] [image: CII Best Practices]

urllib3 is a powerful, user-friendly HTTP client for Python.
urllib3 brings many critical features that are missing from the Python
standard libraries:

- Thread safety.
- Connection pooling.
- Client-side SSL/TLS verification.
- File uploads with multipart encoding.
- Helpers for retrying requests and dealing with HTTP redirects.
- Support for gzip, deflate, brotli, and zstd encoding.
- Proxy support for HTTP and SOCKS.
- 100% test coverage.

... and many more features, but most importantly: Our maintainers have a 15+
year track record of maintaining urllib3 with the highest code standards and
attention to security and safety.

Much of the Python ecosystem already uses urllib3
and you should too.

## Installing

urllib3 can be installed with pip:

```
$ python -m pip install urllib3
```

Alternatively, you can grab the latest source code from GitHub:

```
$ git clone https://github.com/urllib3/urllib3.git
$ cd urllib3
$ pip install .
```

## Getting Started

urllib3 is easy to use:

```
>>> import urllib3
>>> resp = urllib3.request("GET", "http://httpbin.org/robots.txt")
>>> resp.status
200
>>> resp.data
b"User-agent: *\nDisallow: /deny\n"
```

urllib3 has usage and reference documentation at urllib3.readthedocs.io.

## Community

urllib3 has a community Discord channel for asking questions and
collaborating with other contributors. Drop by and say hello 👋

## Contributing

urllib3 happily accepts contributions. Please see our
contributing documentation
for some tips on getting started.

## Security Disclosures

To report a security vulnerability, please use the
Tidelift security contact.
Tidelift will coordinate the fix and disclosure with maintainers.

## Maintainers

Meet our maintainers since 2008:

- Current Lead: @illia-v (Illia Volochii)
- @sethmlarson (Seth M. Larson)
- @pquentin (Quentin Pradet)
- @theacodes (Thea Flowers)
- @haikuginger (Jess Shapiro)
- @lukasa (Cory Benfield)
- @sigmavirus24 (Ian Stapleton Cordasco)
- @shazow (Andrey Petrov)

👋

## Sponsorship

If your company benefits from this library, please consider sponsoring its
development.

## For Enterprise

Professional support for urllib3 is available as part of the Tidelift
Subscription. Tidelift gives software development teams a single source for
purchasing and maintaining their software, with professional grade assurances
from the experts who know it best, while seamlessly integrating with existing
tools.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

urllib3-2.7.0.tar.gz
 (433.6 kB
 view details)

Uploaded
 May 7, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

urllib3-2.7.0-py3-none-any.whl
 (131.1 kB
 view details)

Uploaded
 May 7, 2026
 Python 3

## File details

Details for the file urllib3-2.7.0.tar.gz.

### File metadata

- Download URL: urllib3-2.7.0.tar.gz
- Upload date:
 May 7, 2026
- Size: 433.6 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for urllib3-2.7.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 231e0ec3b63ceb14667c67be60f2f2c40a518cb38b03af60abc813da26505f4c | |
| MD5 | e79707b798a66c8165c9c441440f4e80 | |
| BLAKE2b-256 | 530c06f8b233b8fd13b9e5ee11424ef85419ba0d8ba0b3138bf360be2ff56953 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for urllib3-2.7.0.tar.gz:

Publisher: publish.yml on urllib3/urllib3

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: urllib3-2.7.0.tar.gz
 - Subject digest: 231e0ec3b63ceb14667c67be60f2f2c40a518cb38b03af60abc813da26505f4c
 - Sigstore transparency entry: 1462404383
 - Sigstore integration time:
 May 7, 2026
 Source repository:

 - Permalink: urllib3/urllib3@9a950b92d999f906b6020bb2d1076ee56cddd5d2
 - Branch / Tag: refs/tags/2.7.0
 - Owner: https://github.com/urllib3
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yml@9a950b92d999f906b6020bb2d1076ee56cddd5d2
 - Trigger Event: push

## File details

Details for the file urllib3-2.7.0-py3-none-any.whl.

### File metadata

- Download URL: urllib3-2.7.0-py3-none-any.whl
- Upload date:
 May 7, 2026
- Size: 131.1 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for urllib3-2.7.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 9fb4c81ebbb1ce9531cce37674bbc6f1360472bc18ca9a553ede278ef7276897 | |
| MD5 | 601cbc90e0f477aa45217521f6678eb7 | |
| BLAKE2b-256 | 7f3e5db95bcf282c52709639744ca2a8b149baccf648e39c8cc87553df9eae0c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for urllib3-2.7.0-py3-none-any.whl:

Publisher: publish.yml on urllib3/urllib3

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: urllib3-2.7.0-py3-none-any.whl
 - Subject digest: 9fb4c81ebbb1ce9531cce37674bbc6f1360472bc18ca9a553ede278ef7276897
 - Sigstore transparency entry: 1462404419
 - Sigstore integration time:
 May 7, 2026
 Source repository:

 - Permalink: urllib3/urllib3@9a950b92d999f906b6020bb2d1076ee56cddd5d2
 - Branch / Tag: refs/tags/2.7.0
 - Owner: https://github.com/urllib3
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yml@9a950b92d999f906b6020bb2d1076ee56cddd5d2
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

2.7.0 This release

May 7, 2026
 2 files

2.6.3

Jan 7, 2026
 2 files

2.6.2

Dec 11, 2025
 2 files

2.6.1

Dec 8, 2025
 2 files

2.6.0

Dec 5, 2025
 2 files

2.5.0

Jun 18, 2025
 2 files

2.4.0

Apr 10, 2025
 2 files

2.3.0

Dec 22, 2024
 2 files

2.2.3

Sep 12, 2024
 2 files

2.2.2

Jun 17, 2024
 2 files

2.2.1

Feb 18, 2024
 2 files

2.2.0

Jan 30, 2024
 2 files

2.1.0

Nov 13, 2023
 2 files

2.0.7

Oct 17, 2023
 2 files

2.0.6

Oct 2, 2023
 2 files

2.0.5

Sep 20, 2023
 2 files

2.0.4

Jul 19, 2023
 2 files

2.0.3

Jun 7, 2023
 2 files

2.0.2

May 3, 2023
 2 files

Yanked

2.0.1

Apr 30, 2023
 2 files

Yanked

2.0.0

Apr 26, 2023
 2 files

Pre-release

2.0.0a4

Apr 25, 2023
 2 files

Pre-release

2.0.0a3

Jan 11, 2023
 2 files

Pre-release

2.0.0a2

Nov 23, 2022
 2 files

Pre-release

2.0.0a1

Nov 15, 2022
 2 files

1.26.20

Aug 29, 2024
 2 files

1.26.19

Jun 17, 2024
 2 files

1.26.18

Oct 17, 2023
 2 files

1.26.17

Oct 2, 2023
 2 files

1.26.16

May 23, 2023
 2 files

1.26.15

Mar 11, 2023
 2 files

1.26.14

Jan 11, 2023
 2 files

1.26.13

Nov 23, 2022
 2 files

1.26.12

Aug 22, 2022
 2 files

1.26.11

Jul 25, 2022
 2 files

1.26.10

Jul 7, 2022
 2 files

1.26.9

Mar 16, 2022
 2 files

1.26.8

Jan 7, 2022
 2 files

1.26.7

Sep 22, 2021
 2 files

1.26.6

Jun 25, 2021
 2 files

1.26.5

May 26, 2021
 2 files

1.26.4

Mar 15, 2021
 2 files

1.26.3

Jan 26, 2021
 2 files

1.26.2

Nov 12, 2020
 2 files

1.26.1

Nov 11, 2020
 2 files

1.26.0

Nov 10, 2020
 2 files

1.25.11

Oct 19, 2020
 2 files

1.25.10

Jul 22, 2020
 2 files

1.25.9

Apr 16, 2020
 2 files

1.25.8

Jan 21, 2020
 2 files

1.25.7

Nov 11, 2019
 2 files

1.25.6

Sep 24, 2019
 2 files

1.25.5

Sep 20, 2019
 2 files

1.25.4

Sep 19, 2019
 2 files

1.25.3

May 23, 2019
 2 files

1.25.2

Apr 29, 2019
 2 files

Yanked

1.25.1

Apr 24, 2019
 2 files

Yanked

1.25

Apr 22, 2019
 2 files

1.24.3

May 2, 2019
 2 files

1.24.2

Apr 17, 2019
 2 files

1.24.1

Nov 2, 2018
 2 files

1.24

Oct 16, 2018
 2 files

1.23

Jun 5, 2018
 2 files

1.22

Jul 20, 2017
 2 files

1.21.1

May 2, 2017
 2 files

1.21

Apr 25, 2017
 2 files

1.20

Jan 19, 2017
 2 files

1.19.1

Nov 16, 2016
 2 files

1.19

Nov 3, 2016
 2 files

1.18.1

Oct 27, 2016
 2 files

1.18

Sep 26, 2016
 2 files

1.17

Sep 6, 2016
 2 files

1.16

Jun 11, 2016
 2 files

1.15.1

Apr 11, 2016
 2 files

1.15

Apr 6, 2016
 2 files

1.14

Dec 29, 2015
 2 files

1.13.1

Dec 18, 2015
 2 files

1.13

Dec 14, 2015
 2 files

1.12

Sep 6, 2015
 2 files

1.11

Jul 21, 2015
 2 files

1.10.4

May 3, 2015
 2 files

1.10.3

Apr 21, 2015
 2 files

1.10.2

Feb 25, 2015
 2 files

1.10.1

Feb 11, 2015
 2 files

1.10

Dec 14, 2014
 2 files

1.9.1

Sep 13, 2014
 2 files

1.9

Jul 7, 2014
 1 file

1.8.3

Jun 24, 2014
 1 file

1.8.2

Apr 18, 2014
 1 file

1.8

Mar 6, 2014
 1 file

1.7.1

Sep 25, 2013
 1 file

1.7

Aug 14, 2013
 1 file

1.6

Apr 25, 2013
 1 file

1.5

Aug 2, 2012
 1 file

1.4

Jun 16, 2012
 1 file

1.3

Mar 25, 2012
 1 file

1.2.2

Feb 6, 2012
 1 file

1.2.1

Feb 5, 2012
 1 file

1.2

Jan 29, 2012
 1 file

1.1

Jan 7, 2012
 1 file

1.0.2

Nov 4, 2011
 1 file

1.0.1

Oct 11, 2011
 1 file

1.0

Oct 9, 2011
 1 file

0.4.1

Jul 18, 2011

0.4.0

Mar 30, 2011

0.3.1

Jul 13, 2010

0.3

Dec 11, 2009

0.2

Nov 24, 2008
 1 file