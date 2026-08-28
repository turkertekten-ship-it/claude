# Flask

Flask is a lightweight WSGI web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around Werkzeug
and Jinja, and has become one of the most popular Python web
application frameworks.

Flask offers suggestions, but doesn't enforce any dependencies or
project layout. It is up to the developer to choose the tools and
libraries they want to use. There are many extensions provided by the
community that make adding new functionality easy.

## A Simple Example

```
# save this as app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"
```

```
$ flask run
  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## Donate

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, please
donate today.

## Contributing

See our detailed contributing documentation for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

flask-3.1.3.tar.gz
 (759.0 kB
 view details)

Uploaded
 Feb 19, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

flask-3.1.3-py3-none-any.whl
 (103.4 kB
 view details)

Uploaded
 Feb 19, 2026
 Python 3

## File details

Details for the file flask-3.1.3.tar.gz.

### File metadata

- Download URL: flask-3.1.3.tar.gz
- Upload date:
 Feb 19, 2026
- Size: 759.0 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for flask-3.1.3.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 0ef0e52b8a9cd932855379197dd8f94047b359ca0a78695144304cb45f87c9eb | |
| MD5 | 4dd9abd8b17b66338a02ac45fafa710b | |
| BLAKE2b-256 | 260035d85dcce6c57fdc871f3867d465d780f302a175ea360f62533f12b27e2b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for flask-3.1.3.tar.gz:

Publisher: publish.yaml on pallets/flask

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: flask-3.1.3.tar.gz
 - Subject digest: 0ef0e52b8a9cd932855379197dd8f94047b359ca0a78695144304cb45f87c9eb
 - Sigstore transparency entry: 967560838
 - Sigstore integration time:
 Feb 19, 2026
 Source repository:

 - Permalink: pallets/flask@22d924701a6ae2e4cd01e9a15bbaf3946094af65
 - Branch / Tag: refs/tags/3.1.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@22d924701a6ae2e4cd01e9a15bbaf3946094af65
 - Trigger Event: push

## File details

Details for the file flask-3.1.3-py3-none-any.whl.

### File metadata

- Download URL: flask-3.1.3-py3-none-any.whl
- Upload date:
 Feb 19, 2026
- Size: 103.4 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for flask-3.1.3-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | f4bcbefc124291925f1a26446da31a5178f9483862233b23c0c96a20701f670c | |
| MD5 | 3da2e5b81647a4453e6d007668532627 | |
| BLAKE2b-256 | 7f9c34f6962f9b9e9c71f6e5ed806e0d0ff03c9d1b0b2340088a0cf4bce09b18 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for flask-3.1.3-py3-none-any.whl:

Publisher: publish.yaml on pallets/flask

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: flask-3.1.3-py3-none-any.whl
 - Subject digest: f4bcbefc124291925f1a26446da31a5178f9483862233b23c0c96a20701f670c
 - Sigstore transparency entry: 967560891
 - Sigstore integration time:
 Feb 19, 2026
 Source repository:

 - Permalink: pallets/flask@22d924701a6ae2e4cd01e9a15bbaf3946094af65
 - Branch / Tag: refs/tags/3.1.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@22d924701a6ae2e4cd01e9a15bbaf3946094af65
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

3.1.3 This release

Feb 19, 2026
 2 files

3.1.2

Aug 19, 2025
 2 files

3.1.1

May 13, 2025
 2 files

3.1.0

Nov 13, 2024
 2 files

3.0.3

Apr 7, 2024
 2 files

3.0.2

Feb 3, 2024
 2 files

3.0.1

Jan 18, 2024
 2 files

3.0.0

Sep 30, 2023
 2 files

2.3.3

Aug 21, 2023
 2 files

2.3.2

May 1, 2023
 2 files

2.3.1

Apr 25, 2023
 2 files

2.3.0

Apr 25, 2023
 2 files

2.2.5

May 2, 2023
 2 files

2.2.4

Apr 25, 2023
 2 files

2.2.3

Feb 15, 2023
 2 files

2.2.2

Aug 8, 2022
 2 files

2.2.1

Aug 3, 2022
 2 files

2.2.0

Aug 2, 2022
 2 files

2.1.3

Jul 13, 2022
 2 files

2.1.2

Apr 28, 2022
 2 files

2.1.1

Mar 30, 2022
 2 files

2.1.0

Mar 28, 2022
 2 files

2.0.3

Feb 14, 2022
 2 files

2.0.2

Oct 4, 2021
 2 files

2.0.1

May 21, 2021
 2 files

2.0.0

May 11, 2021
 2 files

Pre-release

2.0.0rc2

May 3, 2021
 2 files

Pre-release

2.0.0rc1

Apr 16, 2021
 2 files

1.1.4

May 14, 2021
 2 files

1.1.3

May 13, 2021
 2 files

1.1.2

Apr 3, 2020
 2 files

1.1.1

Jul 8, 2019
 2 files

1.1.0

Jul 4, 2019
 2 files

1.0.4

Jul 4, 2019
 2 files

1.0.3

May 17, 2019
 2 files

1.0.2

May 2, 2018
 2 files

1.0.1

Apr 30, 2018
 2 files

1.0

Apr 26, 2018
 2 files

0.12.5

Feb 10, 2020
 2 files

0.12.4

Apr 30, 2018
 2 files

0.12.3

Apr 26, 2018
 2 files

0.12.2

May 16, 2017
 2 files

0.12.1

Mar 31, 2017
 2 files

0.12

Dec 21, 2016
 2 files

0.11.1

Jun 7, 2016
 2 files

0.11

May 29, 2016
 2 files

0.10.1

Jun 14, 2013
 1 file

0.10

Jun 13, 2013
 1 file

0.9

Jul 1, 2012
 1 file

0.8.1

Jul 1, 2012
 1 file

0.8

Sep 29, 2011
 1 file

0.7.2

Jul 6, 2011
 1 file

0.7.1

Jun 29, 2011
 1 file

0.7

Jun 28, 2011
 1 file

0.6.1

Dec 31, 2010
 1 file

0.6

Jul 27, 2010
 1 file

0.5.2

Jul 15, 2010
 1 file

0.5.1

Jul 6, 2010
 1 file

0.5

Jul 6, 2010
 1 file

0.4

Jun 18, 2010
 1 file

0.3.1

May 28, 2010
 1 file

0.3

May 27, 2010
 1 file

0.2

May 11, 2010
 1 file

0.1

Apr 16, 2010
 1 file