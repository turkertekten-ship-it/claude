# Requests

[image: Version] [image: Supported Versions] [image: Downloads] [image: Contributors] [image: Documentation]

Requests is a simple, yet elegant, HTTP library.

```
>>> import requests
>>> r = requests.get('https://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
>>> r.status_code
200
>>> r.headers['content-type']
'application/json; charset=utf8'
>>> r.encoding
'utf-8'
>>> r.text
'{"authenticated": true, ...'
>>> r.json()
{'authenticated': True, ...}
```

Requests allows you to send HTTP/1.1 requests extremely easily. There’s no need to manually add query strings to your URLs, or to form-encode your PUT & POST data — but nowadays, just use the json method!

Requests is one of the most downloaded Python packages today, pulling in around 300M downloads / week — according to GitHub, Requests is currently depended upon by 4,000,000+ repositories.

## Installing Requests and Supported Versions

Requests is available on PyPI:

```
$ python -m pip install requests
```

Requests officially supports Python 3.10+.

## Supported Features & Best–Practices

Requests is ready for the demands of building robust and reliable HTTP–speaking applications, for the needs of today.

- Keep-Alive & Connection Pooling
- International Domains and URLs
- Sessions with Cookie Persistence
- Browser-style TLS/SSL Verification
- Basic & Digest Authentication
- Familiar dict–like Cookies
- Automatic Content Decompression and Decoding
- Multi-part File Uploads
- SOCKS Proxy Support
- Connection Timeouts
- Streaming Downloads
- Automatic honoring of .netrc
- Chunked HTTP Requests

## Cloning the repository

When cloning the Requests repository, you may need to add the -c fetch.fsck.badTimezone=ignore flag to avoid an error about a bad commit timestamp (see
this issue for more background):

```
git clone -c fetch.fsck.badTimezone=ignore https://github.com/psf/requests.git
```

You can also apply this setting to your global Git config:

```
git config --global fetch.fsck.badTimezone ignore
```

---

[image: Kenneth Reitz] [image: Python Software Foundation]

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

requests-2.34.2.tar.gz
 (142.9 kB
 view details)

Uploaded
 May 14, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

requests-2.34.2-py3-none-any.whl
 (73.1 kB
 view details)

Uploaded
 May 14, 2026
 Python 3

## File details

Details for the file requests-2.34.2.tar.gz.

### File metadata

- Download URL: requests-2.34.2.tar.gz
- Upload date:
 May 14, 2026
- Size: 142.9 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for requests-2.34.2.tar.gz
| Algorithm | Hash digest | |
| SHA256 | f288924cae4e29463698d6d60bc6a4da69c89185ad1e0bcc4104f584e960b9ed | |
| MD5 | 611e438d0803e962500225f9807a475e | |
| BLAKE2b-256 | acc3e2a2b89f2d3e2179abd6d00ebd70bff6273f37fb3e0cc209f48b39d00cbf | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for requests-2.34.2.tar.gz:

Publisher: publish.yml on psf/requests

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: requests-2.34.2.tar.gz
 - Subject digest: f288924cae4e29463698d6d60bc6a4da69c89185ad1e0bcc4104f584e960b9ed
 - Sigstore transparency entry: 1540243332
 - Sigstore integration time:
 May 14, 2026
 Source repository:

 - Permalink: psf/requests@6e83187b8feb273ed4c6cdab5efd8d54901dfab3
 - Branch / Tag: refs/tags/v2.34.2
 - Owner: https://github.com/psf
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yml@6e83187b8feb273ed4c6cdab5efd8d54901dfab3
 - Trigger Event: push

## File details

Details for the file requests-2.34.2-py3-none-any.whl.

### File metadata

- Download URL: requests-2.34.2-py3-none-any.whl
- Upload date:
 May 14, 2026
- Size: 73.1 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for requests-2.34.2-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0 | |
| MD5 | cc4287951c320ff794e5e183c7a91f85 | |
| BLAKE2b-256 | a0f4c67b0b3f1b9245e8d266f0f112c500d50e5b4e83cb6f3b71b6528104182a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for requests-2.34.2-py3-none-any.whl:

Publisher: publish.yml on psf/requests

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: requests-2.34.2-py3-none-any.whl
 - Subject digest: 2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0
 - Sigstore transparency entry: 1540243665
 - Sigstore integration time:
 May 14, 2026
 Source repository:

 - Permalink: psf/requests@6e83187b8feb273ed4c6cdab5efd8d54901dfab3
 - Branch / Tag: refs/tags/v2.34.2
 - Owner: https://github.com/psf
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yml@6e83187b8feb273ed4c6cdab5efd8d54901dfab3
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

2.34.2 This release

May 14, 2026
 2 files

2.34.1

May 13, 2026
 2 files

2.34.0

May 11, 2026
 2 files

Pre-release

2.34.0.dev1

May 3, 2026
 2 files

2.33.1

Mar 30, 2026
 2 files

2.33.0

Mar 25, 2026
 2 files

2.32.5

Aug 18, 2025
 2 files

2.32.4

Jun 9, 2025
 2 files

2.32.3

May 29, 2024
 2 files

2.32.2

May 21, 2024
 2 files

Yanked

2.32.1

May 20, 2024
 2 files

Yanked

2.32.0

May 20, 2024
 2 files

2.31.0

May 22, 2023
 2 files

2.30.0

May 3, 2023
 2 files

2.29.0

Apr 26, 2023
 2 files

2.28.2

Jan 12, 2023
 2 files

2.28.1

Jun 29, 2022
 2 files

2.28.0

Jun 9, 2022
 2 files

2.27.1

Jan 5, 2022
 2 files

2.27.0

Jan 3, 2022
 2 files

2.26.0

Jul 13, 2021
 2 files

2.25.1

Dec 16, 2020
 2 files

2.25.0

Nov 11, 2020
 2 files

2.24.0

Jun 17, 2020
 2 files

2.23.0

Feb 19, 2020
 3 files

2.22.0

May 16, 2019
 2 files

2.21.0

Dec 10, 2018
 2 files

2.20.1

Nov 8, 2018
 2 files

2.20.0

Oct 18, 2018
 2 files

2.19.1

Jun 14, 2018
 2 files

2.19.0

Jun 12, 2018
 2 files

2.18.4

Aug 15, 2017
 2 files

2.18.3

Aug 2, 2017
 2 files

2.18.2

Jul 25, 2017
 2 files

2.18.1

Jun 14, 2017
 2 files

2.18.0

Jun 14, 2017
 2 files

2.17.3

May 29, 2017
 2 files

2.17.2

May 29, 2017
 2 files

2.17.1

May 29, 2017
 2 files

2.17.0

May 29, 2017
 2 files

2.16.5

May 28, 2017
 2 files

2.16.4

May 27, 2017
 2 files

2.16.3

May 27, 2017
 2 files

2.16.2

May 27, 2017
 2 files

2.16.1

May 27, 2017
 2 files

2.16.0

May 27, 2017
 2 files

2.15.1

May 27, 2017
 2 files

2.15.0

May 27, 2017

2.14.2

May 10, 2017
 2 files

2.14.1

May 9, 2017
 2 files

2.14.0

May 9, 2017
 2 files

2.13.0

Jan 24, 2017
 2 files

2.12.5

Jan 18, 2017
 2 files

2.12.4

Dec 14, 2016
 2 files

2.12.3

Dec 1, 2016
 2 files

2.12.2

Nov 30, 2016
 2 files

2.12.1

Nov 16, 2016
 2 files

2.12.0

Nov 15, 2016
 2 files

2.11.1

Aug 17, 2016
 2 files

2.11.0

Aug 8, 2016
 2 files

2.10.0

Apr 29, 2016
 2 files

2.9.2

Apr 29, 2016
 2 files

2.9.1

Dec 21, 2015
 2 files

2.9.0

Dec 15, 2015
 2 files

2.8.1

Oct 13, 2015
 2 files

2.8.0

Oct 6, 2015
 2 files

2.7.0

May 3, 2015
 2 files

2.6.2

Apr 23, 2015
 2 files

2.6.1

Apr 23, 2015
 2 files

2.6.0

Mar 14, 2015
 2 files

2.5.3

Feb 24, 2015
 2 files

2.5.2

Feb 23, 2015
 2 files

2.5.1

Dec 23, 2014
 2 files

2.5.0

Dec 1, 2014
 2 files

2.4.3

Oct 6, 2014
 2 files

2.4.2

Oct 5, 2014
 2 files

2.4.1

Sep 9, 2014
 2 files

2.4.0

Aug 29, 2014
 2 files

2.3.0

May 16, 2014
 2 files

2.2.1

Jan 23, 2014
 2 files

2.2.0

Jan 9, 2014
 2 files

2.1.0

Dec 5, 2013
 2 files

2.0.1

Oct 24, 2013
 2 files

2.0.0

Sep 24, 2013
 2 files

1.2.3

May 25, 2013
 1 file

1.2.2

May 21, 2013
 1 file

1.2.1

May 20, 2013
 1 file

1.2.0

Mar 31, 2013
 1 file

1.1.0

Jan 10, 2013
 1 file

1.0.4

Dec 23, 2012
 1 file

1.0.3

Dec 18, 2012
 1 file

1.0.2

Dec 17, 2012
 1 file

1.0.1

Dec 17, 2012
 1 file

1.0.0

Dec 17, 2012
 1 file

0.14.2

Oct 27, 2012
 1 file

0.14.1

Oct 1, 2012
 1 file

0.14.0

Sep 2, 2012
 1 file

0.13.9

Aug 25, 2012
 1 file

0.13.8

Aug 20, 2012
 1 file

0.13.7

Aug 19, 2012
 1 file

0.13.6

Aug 6, 2012
 1 file

0.13.5

Jul 27, 2012
 1 file

0.13.4

Jul 27, 2012
 1 file

0.13.3

Jul 12, 2012
 1 file

0.13.2

Jun 29, 2012
 1 file

0.13.1

Jun 8, 2012
 1 file

0.13.0

May 30, 2012
 1 file

0.12.1

May 8, 2012
 1 file

0.12.01

May 8, 2012

0.12.0

May 2, 2012
 1 file

0.11.2

Apr 23, 2012
 1 file

0.11.1

Mar 31, 2012
 1 file

0.10.8

Mar 9, 2012
 1 file

0.10.7

Mar 8, 2012
 1 file

0.10.6

Feb 26, 2012
 1 file

0.10.4

Feb 20, 2012
 1 file

0.10.3

Feb 20, 2012
 1 file

0.10.2

Feb 15, 2012
 1 file

0.10.1

Jan 23, 2012
 1 file

0.10.0

Jan 22, 2012
 1 file

0.9.3

Jan 19, 2012
 1 file

0.9.2

Jan 19, 2012
 1 file

0.9.1

Jan 6, 2012
 1 file

0.9.0

Dec 28, 2011
 1 file

0.8.9

Dec 28, 2011
 1 file

0.8.8

Dec 28, 2011
 1 file

0.8.7

Dec 24, 2011
 1 file

0.8.6

Dec 19, 2011
 1 file

0.8.5

Dec 14, 2011
 1 file

0.8.4

Dec 11, 2011
 1 file

0.8.3

Nov 27, 2011
 1 file

0.8.2

Nov 19, 2011
 1 file

0.8.1

Nov 15, 2011
 1 file

0.8.0

Nov 13, 2011
 1 file

0.7.6

Nov 7, 2011
 1 file

0.7.5

Nov 5, 2011
 1 file

0.7.4

Oct 26, 2011
 1 file

0.7.3

Oct 23, 2011
 1 file

0.7.2

Oct 23, 2011
 1 file

0.7.1

Oct 23, 2011
 1 file

0.7.0

Oct 23, 2011
 1 file

0.6.6

Oct 19, 2011
 1 file

0.6.5

Oct 19, 2011
 1 file

0.6.4

Oct 14, 2011
 1 file

0.6.3

Oct 14, 2011
 1 file

0.6.2

Oct 9, 2011
 1 file

0.6.1

Aug 20, 2011
 1 file

0.6.0

Aug 17, 2011
 1 file

0.5.1

Jul 24, 2011
 1 file

0.5.0

Jun 22, 2011
 1 file

0.4.1

May 22, 2011
 1 file

0.4.0

May 15, 2011
 1 file

0.3.4

May 14, 2011
 1 file

0.3.3

May 12, 2011
 1 file

0.3.2

Apr 15, 2011
 1 file

0.3.1

Apr 1, 2011
 1 file

0.3.0

Feb 25, 2011
 1 file

0.2.4

Feb 19, 2011
 1 file

0.2.3

Feb 15, 2011
 1 file

0.2.2

Feb 14, 2011
 1 file

0.2.1

Feb 14, 2011
 1 file

0.2.0

Feb 14, 2011
 1 file

0.0.1

Feb 13, 2011