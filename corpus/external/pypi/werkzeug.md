# Werkzeug

werkzeug German noun: "tool". Etymology: werk ("work"), zeug ("stuff")

Werkzeug is a comprehensive WSGI web application library. It began as
a simple collection of various utilities for WSGI applications and has
become one of the most advanced WSGI utility libraries.

It includes:

- An interactive debugger that allows inspecting stack traces and
source code in the browser with an interactive interpreter for any
frame in the stack.
- A full-featured request object with objects to interact with
headers, query args, form data, files, and cookies.
- A response object that can wrap other WSGI applications and handle
streaming data.
- A routing system for matching URLs to endpoints and generating URLs
for endpoints, with an extensible system for capturing variables
from URLs.
- HTTP utilities to handle entity tags, cache control, dates, user
agents, cookies, files, and more.
- A threaded WSGI server for use while developing applications
locally.
- A test client for simulating HTTP requests during testing without
requiring running a server.

Werkzeug doesn't enforce any dependencies. It is up to the developer to
choose a template engine, database adapter, and even how to handle
requests. It can be used to build all sorts of end user applications
such as blogs, wikis, or bulletin boards.

Flask wraps Werkzeug, using it to handle the details of WSGI while
providing more structure and patterns for defining powerful
applications.

## A Simple Example

```
# save this as app.py
from werkzeug.wrappers import Request, Response

@Request.application
def application(request: Request) -> Response:
    return Response("Hello, World!")

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple("127.0.0.1", 5000, application)
```

```
$ python -m app
  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## Donate

The Pallets organization develops and supports Werkzeug and other
popular packages. In order to grow the community of contributors and
users, and allow the maintainers to devote more time to the projects,
please donate today.

## Contributing

See our detailed contributing documentation for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

werkzeug-3.1.8.tar.gz
 (875.9 kB
 view details)

Uploaded
 Apr 2, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

werkzeug-3.1.8-py3-none-any.whl
 (226.5 kB
 view details)

Uploaded
 Apr 2, 2026
 Python 3

## File details

Details for the file werkzeug-3.1.8.tar.gz.

### File metadata

- Download URL: werkzeug-3.1.8.tar.gz
- Upload date:
 Apr 2, 2026
- Size: 875.9 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for werkzeug-3.1.8.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 9bad61a4268dac112f1c5cd4630a56ede601b6ed420300677a869083d70a4c44 | |
| MD5 | 5b3063a0bfc95d46cb35258b03b9f30e | |
| BLAKE2b-256 | ddb2381be8cfdee792dd117872481b6e378f85c957dd7c5bca38897b08f765fd | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for werkzeug-3.1.8.tar.gz:

Publisher: publish.yaml on pallets/werkzeug

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: werkzeug-3.1.8.tar.gz
 - Subject digest: 9bad61a4268dac112f1c5cd4630a56ede601b6ed420300677a869083d70a4c44
 - Sigstore transparency entry: 1219041094
 - Sigstore integration time:
 Apr 2, 2026
 Source repository:

 - Permalink: pallets/werkzeug@c1a26b45fb06d5e086b4d6be820c3302f588d815
 - Branch / Tag: refs/tags/3.1.8
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@c1a26b45fb06d5e086b4d6be820c3302f588d815
 - Trigger Event: push

## File details

Details for the file werkzeug-3.1.8-py3-none-any.whl.

### File metadata

- Download URL: werkzeug-3.1.8-py3-none-any.whl
- Upload date:
 Apr 2, 2026
- Size: 226.5 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for werkzeug-3.1.8-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 63a77fb8892bf28ebc3178683445222aa500e48ebad5ec77b0ad80f8726b1f50 | |
| MD5 | 32ebaee9805d9d7c6f77cdb0d39f2de4 | |
| BLAKE2b-256 | 938c2e650f2afeb7ee576912636c23ddb621c91ac6a98e66dc8d29c3c69446e1 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for werkzeug-3.1.8-py3-none-any.whl:

Publisher: publish.yaml on pallets/werkzeug

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: werkzeug-3.1.8-py3-none-any.whl
 - Subject digest: 63a77fb8892bf28ebc3178683445222aa500e48ebad5ec77b0ad80f8726b1f50
 - Sigstore transparency entry: 1219041150
 - Sigstore integration time:
 Apr 2, 2026
 Source repository:

 - Permalink: pallets/werkzeug@c1a26b45fb06d5e086b4d6be820c3302f588d815
 - Branch / Tag: refs/tags/3.1.8
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@c1a26b45fb06d5e086b4d6be820c3302f588d815
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

3.1.8 This release

Apr 2, 2026
 2 files

3.1.7

Mar 24, 2026
 2 files

3.1.6

Feb 19, 2026
 2 files

3.1.5

Jan 8, 2026
 2 files

3.1.4

Nov 29, 2025
 2 files

3.1.3

Nov 8, 2024
 2 files

3.1.2

Nov 4, 2024
 2 files

3.1.1

Nov 1, 2024
 2 files

3.1.0

Oct 31, 2024
 2 files

3.0.6

Oct 25, 2024
 2 files

3.0.5

Oct 25, 2024
 2 files

3.0.4

Aug 21, 2024
 2 files

3.0.3

May 5, 2024
 2 files

3.0.2

Apr 1, 2024
 2 files

3.0.1

Oct 24, 2023
 2 files

3.0.0

Sep 30, 2023
 2 files

2.3.8

Nov 8, 2023
 2 files

2.3.7

Aug 14, 2023
 2 files

2.3.6

Jun 8, 2023
 2 files

2.3.5

Jun 7, 2023
 2 files

2.3.4

May 8, 2023
 2 files

2.3.3

May 1, 2023
 2 files

2.3.2

Apr 28, 2023
 2 files

2.3.1

Apr 27, 2023
 2 files

2.3.0

Apr 25, 2023
 2 files

2.2.3

Feb 14, 2023
 2 files

2.2.2

Aug 8, 2022
 2 files

2.2.1

Jul 27, 2022
 2 files

2.2.0

Jul 23, 2022
 2 files

Pre-release

2.2.0a1

Jul 8, 2022
 2 files

2.1.2

Apr 28, 2022
 2 files

2.1.1

Apr 1, 2022
 2 files

2.1.0

Mar 28, 2022
 2 files

2.0.3

Feb 7, 2022
 2 files

2.0.2

Oct 6, 2021
 2 files

2.0.1

May 17, 2021
 2 files

2.0.0

May 11, 2021
 2 files

Pre-release

2.0.0rc5

May 3, 2021
 2 files

Pre-release

2.0.0rc4

Apr 16, 2021
 2 files

Pre-release

2.0.0rc3

Mar 17, 2021
 2 files

Pre-release

2.0.0rc2

Mar 3, 2021
 2 files

Pre-release

2.0.0rc1

Feb 8, 2021
 2 files

1.0.1

Mar 31, 2020
 2 files

1.0.0

Feb 6, 2020
 2 files

Pre-release

1.0.0rc1

Jan 31, 2020
 2 files

0.16.1

Jan 27, 2020
 2 files

0.16.0

Sep 19, 2019
 2 files

0.15.6

Sep 4, 2019
 2 files

0.15.5

Jul 17, 2019
 2 files

0.15.4

May 15, 2019
 2 files

0.15.3

May 14, 2019
 2 files

0.15.2

Apr 2, 2019
 2 files

0.15.1

Mar 21, 2019
 2 files

0.15.0

Mar 19, 2019
 2 files

0.14.1

Dec 31, 2017
 2 files

0.14

Dec 31, 2017
 2 files

0.13

Dec 7, 2017
 2 files

0.12.2

May 16, 2017
 2 files

0.12.1

Mar 15, 2017
 2 files

0.12

Mar 10, 2017
 2 files

0.11.15

Dec 30, 2016
 2 files

0.11.14

Dec 30, 2016
 2 files

0.11.13

Dec 26, 2016
 2 files

0.11.12

Dec 26, 2016
 2 files

0.11.11

Aug 31, 2016
 2 files

0.11.10

May 24, 2016
 2 files

0.11.9

Apr 24, 2016
 2 files

0.11.8

Apr 15, 2016
 2 files

0.11.7

Apr 14, 2016
 2 files

0.11.6

Apr 14, 2016
 2 files

0.11.5

Mar 22, 2016
 2 files

0.11.4

Feb 14, 2016
 2 files

0.11.3

Dec 19, 2015
 2 files

0.11.2

Nov 12, 2015
 2 files

0.11.1

Nov 10, 2015
 2 files

0.11

Nov 8, 2015
 2 files

0.10.4

Mar 26, 2015
 2 files

0.10.3

Mar 26, 2015

0.10.2

Mar 26, 2015
 2 files

0.10.1

Feb 3, 2015
 1 file

0.10

Jan 29, 2015
 1 file

0.9.6

Jun 7, 2014
 1 file

0.9.5

Jun 6, 2014
 1 file

0.9.4

Aug 25, 2013
 1 file

0.9.3

Jul 25, 2013
 1 file

0.9.2

Jul 18, 2013
 1 file

0.9.1

Jun 14, 2013
 1 file

0.9

Jun 13, 2013
 1 file

0.8.3

Feb 5, 2012
 1 file

0.8.2

Dec 16, 2011
 1 file

0.8.1

Sep 30, 2011
 1 file

0.8

Sep 29, 2011
 1 file

0.7.2

Sep 30, 2011
 1 file

0.7.1

Jul 26, 2011
 1 file

0.7

Jul 24, 2011
 1 file

0.6.2

Apr 23, 2010
 1 file

0.6.1

Apr 12, 2010
 1 file

0.6

Feb 18, 2010
 1 file

0.5.1

Jul 9, 2009
 1 file

0.5

Apr 24, 2009
 1 file

0.4.1

Jan 11, 2009
 1 file

0.4

Nov 23, 2008
 1 file

0.3.1

Jun 24, 2008
 4 files

0.3

Jun 14, 2008
 4 files

0.2

Feb 13, 2008
 3 files

0.1

Dec 9, 2007
 3 files