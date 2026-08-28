Certifi provides Mozilla’s carefully curated collection of Root Certificates for
validating the trustworthiness of SSL certificates while verifying the identity
of TLS hosts. It has been extracted from the Requests project.

## Installation

certifi is available on PyPI. Simply install it with pip:

```
$ pip install certifi
```

## Usage

To reference the installed certificate authority (CA) bundle, you can use the
built-in function:

```
>>> import certifi

>>> certifi.where()
'/usr/local/lib/python3.7/site-packages/certifi/cacert.pem'
```

Or from the command line:

```
$ python -m certifi
/usr/local/lib/python3.7/site-packages/certifi/cacert.pem
```

Enjoy!

## Addition/Removal of Certificates

Certifi does not support any addition/removal or other modification of the
CA trust store content. This project is intended to provide a reliable and
highly portable root of trust to python deployments. Look to upstream projects
for methods to use alternate trust.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

certifi-2026.7.22.tar.gz
 (138.1 kB
 view details)

Uploaded
 Jul 22, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

certifi-2026.7.22-py3-none-any.whl
 (137.0 kB
 view details)

Uploaded
 Jul 22, 2026
 Python 3

## File details

Details for the file certifi-2026.7.22.tar.gz.

### File metadata

- Download URL: certifi-2026.7.22.tar.gz
- Upload date:
 Jul 22, 2026
- Size: 138.1 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.14

### File hashes

Hashes for certifi-2026.7.22.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55 | |
| MD5 | 926857e560a3ae443ee35c2de270d75b | |
| BLAKE2b-256 | a3c224167ea9858356b47a87a50d39908bfdb72ceeefe0041586e704e5376b3a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for certifi-2026.7.22.tar.gz:

Publisher: release.yml on certifi/python-certifi

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: certifi-2026.7.22.tar.gz
 - Subject digest: 741e2c3b351ddf169a738da9f2c048608ff7f2c5cc02f1ebc6b118bb090d5d55
 - Sigstore transparency entry: 2215874464
 - Sigstore integration time:
 Jul 22, 2026
 Source repository:

 - Permalink: certifi/python-certifi@f4bc676bc101fe2235846e37044e8c693d6cbaf4
 - Branch / Tag: refs/tags/2026.07.22
 - Owner: https://github.com/certifi
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 release.yml@f4bc676bc101fe2235846e37044e8c693d6cbaf4
 - Trigger Event: push

## File details

Details for the file certifi-2026.7.22-py3-none-any.whl.

### File metadata

- Download URL: certifi-2026.7.22-py3-none-any.whl
- Upload date:
 Jul 22, 2026
- Size: 137.0 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.14

### File hashes

Hashes for certifi-2026.7.22-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775 | |
| MD5 | edeeb8218c0de1993d874d818064553c | |
| BLAKE2b-256 | 0ba771ac2cff56fec219ed242bb11b8efb69fcc4bec75db06fb7bfe35de520e6 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for certifi-2026.7.22-py3-none-any.whl:

Publisher: release.yml on certifi/python-certifi

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: certifi-2026.7.22-py3-none-any.whl
 - Subject digest: 62f22742b58a1a33014a2b6b706588a8d7e2a88ae7bd1a6ebe8c992928483775
 - Sigstore transparency entry: 2215874544
 - Sigstore integration time:
 Jul 22, 2026
 Source repository:

 - Permalink: certifi/python-certifi@f4bc676bc101fe2235846e37044e8c693d6cbaf4
 - Branch / Tag: refs/tags/2026.07.22
 - Owner: https://github.com/certifi
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 release.yml@f4bc676bc101fe2235846e37044e8c693d6cbaf4
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

2026.7.22 This release

Jul 22, 2026
 2 files

2026.6.17

Jun 17, 2026
 2 files

2026.5.20

May 20, 2026
 2 files

2026.4.22

Apr 22, 2026
 2 files

2026.2.25

Feb 25, 2026
 2 files

2026.1.4

Jan 4, 2026
 2 files

2025.11.12

Nov 12, 2025
 2 files

2025.10.5

Oct 5, 2025
 2 files

2025.8.3

Aug 3, 2025
 2 files

2025.7.14

Jul 14, 2025
 2 files

2025.7.9

Jul 9, 2025
 2 files

2025.6.15

Jun 15, 2025
 2 files

2025.4.26

Apr 26, 2025
 2 files

2025.1.31

Jan 31, 2025
 2 files

2024.12.14

Dec 14, 2024
 2 files

2024.8.30

Aug 30, 2024
 2 files

2024.7.4

Jul 4, 2024
 2 files

2024.6.2

Jun 2, 2024
 2 files

2024.2.2

Feb 2, 2024
 2 files

2023.11.17

Nov 18, 2023
 2 files

2023.7.22

Jul 22, 2023
 2 files

2023.5.7

May 7, 2023
 2 files

2022.12.7

Dec 7, 2022
 2 files

2022.9.24

Sep 24, 2022
 2 files

2022.9.14

Sep 14, 2022
 2 files

2022.6.15.2

Sep 13, 2022
 2 files

2022.6.15.1

Sep 9, 2022
 2 files

2022.6.15

Jun 15, 2022
 2 files

2022.5.18.1

May 19, 2022
 2 files

Yanked

2022.5.18

May 18, 2022
 2 files

2021.10.8

Oct 8, 2021
 2 files

2021.5.30

May 30, 2021
 2 files

2020.12.5

Dec 5, 2020
 2 files

2020.11.8

Nov 8, 2020
 2 files

2020.6.20

Jun 20, 2020
 2 files

2020.4.5.2

Jun 7, 2020
 2 files

2020.4.5.1

Apr 5, 2020
 2 files

2020.4.5

Apr 5, 2020
 2 files

2019.11.28

Nov 28, 2019
 2 files

2019.9.11

Sep 11, 2019
 2 files

2019.6.16

Jun 16, 2019
 2 files

2019.3.9

Mar 9, 2019
 2 files

2018.11.29

Nov 29, 2018
 2 files

2018.10.15

Oct 15, 2018
 2 files

2018.8.24

Aug 24, 2018
 2 files

2018.8.13

Aug 13, 2018
 2 files

2018.4.16

Apr 16, 2018
 2 files

2018.1.18

Jan 18, 2018
 2 files

2017.11.5

Nov 5, 2017
 2 files

2017.7.27.1

Jul 27, 2017
 2 files

2017.7.27

Jul 27, 2017
 2 files

2017.4.17

Apr 17, 2017
 2 files

2017.1.23

Jan 23, 2017
 2 files

2016.9.26

Sep 26, 2016
 2 files

2016.8.31

Aug 31, 2016
 2 files

2016.8.8

Aug 8, 2016
 2 files

2016.8.2

Aug 2, 2016
 2 files

2016.2.28

Feb 28, 2016
 2 files

2015.11.20.1

Nov 30, 2015
 2 files

2015.11.20

Nov 20, 2015
 2 files

2015.9.6.2

Sep 7, 2015
 2 files

2015.9.6.1

Sep 6, 2015
 2 files

2015.9.6

Sep 6, 2015
 2 files

2015.04.28

Apr 28, 2015
 2 files

14.05.14

May 18, 2014
 1 file

1.0.1

Mar 10, 2014
 2 files

1.0.0

Jan 17, 2014
 1 file

0.0.8

Jan 30, 2012
 1 file

0.0.7

Jan 23, 2012
 1 file

0.0.6

Dec 28, 2011
 1 file

0.0.5

Dec 28, 2011
 1 file

0.0.4

Dec 28, 2011
 1 file

0.0.3

Dec 28, 2011
 1 file

0.0.2

Dec 28, 2011
 1 file

0.0.1

Dec 28, 2011
 1 file

0

Dec 28, 2011