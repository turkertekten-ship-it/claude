[image: pytest]

---

 [image: https://img.shields.io/pypi/v/pytest.svg] [image: https://img.shields.io/conda/vn/conda-forge/pytest.svg] [image: https://img.shields.io/pypi/pyversions/pytest.svg] [image: Code coverage Status] [image: https://github.com/pytest-dev/pytest/actions/workflows/test.yml/badge.svg] [image: pre-commit.ci status] [image: https://www.codetriage.com/pytest-dev/pytest/badges/users.svg] [image: Documentation Status] [image: Discord] [image: Libera chat]

The pytest framework makes it easy to write small tests, yet
scales to support complex functional testing for applications and libraries.

An example of a simple test:

```
# content of test_sample.py
def inc(x):
    return x + 1

def test_answer():
    assert inc(3) == 5
```

To execute it:

```
$ pytest
============================= test session starts =============================
collected 1 items

test_sample.py F

================================== FAILURES ===================================
_________________________________ test_answer _________________________________

    def test_answer():
>       assert inc(3) == 5
E       assert 4 == 5
E        +  where 4 = inc(3)

test_sample.py:5: AssertionError
========================== 1 failed in 0.04 seconds ===========================
```

Thanks to pytest’s detailed assertion introspection, you can simply use plain assert statements. See getting-started for more examples.

## Features

- Detailed info on failing assert statements (no need to remember self.assert* names)
- Auto-discovery
of test modules and functions
- Modular fixtures for
managing small or parametrized long-lived test resources
- Can run unittest (or trial)
test suites out of the box
- Python 3.10+ or PyPy3
- Rich plugin architecture, with over 1300+ external plugins and thriving community

## Documentation

For full documentation, including installation, tutorials and PDF documents, please see https://docs.pytest.org/en/stable/.

## Bugs/Requests

Please use the GitHub issue tracker to submit bugs or request features.

## Changelog

Consult the Changelog page for fixes and enhancements of each version.

## Support pytest

Open Collective is an online funding platform for open and transparent communities.
It provides tools to raise money and share your finances in full transparency.

It is the platform of choice for individuals and companies that want to make one-time or
monthly donations directly to the project.

See more details in the pytest collective.

## pytest for enterprise

Available as part of the Tidelift Subscription.

The maintainers of pytest and thousands of other packages are working with Tidelift to deliver commercial support and
maintenance for the open source dependencies you use to build your applications.
Save time, reduce risk, and improve code health, while paying the maintainers of the exact dependencies you use.

Learn more.

### Security

If you have found an issue that you believe is a security vulnerability, please do not create an issue – instead, report it via a new security advisory.

## License

Copyright Holger Krekel and others, 2004.

Distributed under the terms of the MIT license, pytest is free and open source software.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

pytest-9.1.1.tar.gz
 (1.6 MB
 view details)

Uploaded
 Jun 19, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

pytest-9.1.1-py3-none-any.whl
 (386.5 kB
 view details)

Uploaded
 Jun 19, 2026
 Python 3

## File details

Details for the file pytest-9.1.1.tar.gz.

### File metadata

- Download URL: pytest-9.1.1.tar.gz
- Upload date:
 Jun 19, 2026
- Size: 1.6 MB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for pytest-9.1.1.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 1088fbde8f2b49d95a549a195707afa7a76a3ce9bcadc26b6d71f0ffda5fe313 | |
| MD5 | 31f635913c0b1bce9438be52d44398a8 | |
| BLAKE2b-256 | e447b9efed96c114afcfa3c9d3fe98a76a1d14c74a9e266d397cf6eb64be5e01 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for pytest-9.1.1.tar.gz:

Publisher: deploy.yml on pytest-dev/pytest

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: pytest-9.1.1.tar.gz
 - Subject digest: 1088fbde8f2b49d95a549a195707afa7a76a3ce9bcadc26b6d71f0ffda5fe313
 - Sigstore transparency entry: 1870068935
 - Sigstore integration time:
 Jun 19, 2026
 Source repository:

 - Permalink: pytest-dev/pytest@cf470ec0bf7eb89cd97dd56df4859eae5db46447
 - Branch / Tag: refs/heads/release-9.1.1
 - Owner: https://github.com/pytest-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 deploy.yml@cf470ec0bf7eb89cd97dd56df4859eae5db46447
 - Trigger Event: workflow_dispatch

## File details

Details for the file pytest-9.1.1-py3-none-any.whl.

### File metadata

- Download URL: pytest-9.1.1-py3-none-any.whl
- Upload date:
 Jun 19, 2026
- Size: 386.5 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for pytest-9.1.1-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c | |
| MD5 | fd1dd7f62af8bb92733c0d20bcff497e | |
| BLAKE2b-256 | 24251de2678b631f5a49215c6c96fff41ba892b0a34df68d6d80292b1b48aa7f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for pytest-9.1.1-py3-none-any.whl:

Publisher: deploy.yml on pytest-dev/pytest

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: pytest-9.1.1-py3-none-any.whl
 - Subject digest: 37a86b45efb9a47a61a36449063e8e18d0cab3161329fc099eb21783169c4f0c
 - Sigstore transparency entry: 1870068948
 - Sigstore integration time:
 Jun 19, 2026
 Source repository:

 - Permalink: pytest-dev/pytest@cf470ec0bf7eb89cd97dd56df4859eae5db46447
 - Branch / Tag: refs/heads/release-9.1.1
 - Owner: https://github.com/pytest-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 deploy.yml@cf470ec0bf7eb89cd97dd56df4859eae5db46447
 - Trigger Event: workflow_dispatch

## Release history Release notifications |
 RSS feed

This release

9.1.1 This release

Jun 19, 2026
 2 files

9.1.0

Jun 13, 2026
 2 files

9.0.3

Apr 7, 2026
 2 files

9.0.2

Dec 6, 2025
 2 files

9.0.1

Nov 12, 2025
 2 files

9.0.0

Nov 8, 2025
 2 files

8.4.2

Sep 4, 2025
 2 files

8.4.1

Jun 18, 2025
 2 files

8.4.0

Jun 2, 2025
 2 files

8.3.5

Mar 2, 2025
 2 files

8.3.4

Dec 1, 2024
 2 files

8.3.3

Sep 10, 2024
 2 files

8.3.2

Jul 25, 2024
 2 files

8.3.1

Jul 20, 2024
 2 files

8.3.0

Jul 20, 2024
 2 files

8.2.2

Jun 4, 2024
 2 files

8.2.1

May 19, 2024
 2 files

8.2.0

Apr 27, 2024
 2 files

8.1.2

Apr 26, 2024
 2 files

8.1.1

Mar 9, 2024
 2 files

Yanked

8.1.0

Mar 3, 2024
 2 files

8.0.2

Feb 24, 2024
 2 files

8.0.1

Feb 16, 2024
 2 files

8.0.0

Jan 27, 2024
 2 files

Pre-release

8.0.0rc2

Jan 17, 2024
 2 files

Pre-release

8.0.0rc1

Jan 2, 2024
 2 files

7.4.4

Dec 31, 2023
 2 files

7.4.3

Oct 24, 2023
 2 files

7.4.2

Sep 7, 2023
 2 files

7.4.1

Sep 2, 2023
 2 files

7.4.0

Jun 23, 2023
 2 files

7.3.2

Jun 10, 2023
 2 files

7.3.1

Apr 14, 2023
 2 files

7.3.0

Apr 8, 2023
 2 files

7.2.2

Mar 3, 2023
 2 files

7.2.1

Jan 14, 2023
 2 files

7.2.0

Oct 25, 2022
 2 files

7.1.3

Sep 2, 2022
 2 files

7.1.2

Apr 23, 2022
 2 files

7.1.1

Mar 17, 2022
 2 files

7.1.0

Mar 13, 2022
 2 files

7.0.1

Feb 11, 2022
 2 files

7.0.0

Feb 4, 2022
 2 files

Pre-release

7.0.0rc1

Dec 7, 2021
 2 files

6.2.5

Aug 30, 2021
 2 files

6.2.4

May 4, 2021
 2 files

6.2.3

Apr 3, 2021
 2 files

6.2.2

Jan 25, 2021
 2 files

6.2.1

Dec 15, 2020
 2 files

6.2.0

Dec 12, 2020
 2 files

6.1.2

Oct 28, 2020
 2 files

6.1.1

Oct 3, 2020
 2 files

6.1.0

Sep 26, 2020
 2 files

6.0.2

Sep 11, 2020
 2 files

6.0.1

Jul 30, 2020
 2 files

6.0.0

Jul 28, 2020
 2 files

Pre-release

6.0.0rc1

Jul 10, 2020
 2 files

5.4.3

Jun 2, 2020
 2 files

5.4.2

May 8, 2020
 2 files

5.4.1

Mar 13, 2020
 2 files

5.4.0

Mar 12, 2020
 2 files

5.3.5

Jan 29, 2020
 2 files

5.3.4

Jan 20, 2020
 2 files

5.3.3

Jan 17, 2020
 2 files

5.3.2

Dec 14, 2019
 2 files

5.3.1

Nov 26, 2019
 2 files

5.3.0

Nov 19, 2019
 2 files

5.2.4

Nov 15, 2019
 2 files

5.2.3

Nov 14, 2019
 2 files

5.2.2

Oct 25, 2019
 2 files

5.2.1

Oct 6, 2019
 2 files

5.2.0

Sep 29, 2019
 2 files

5.1.3

Sep 21, 2019
 2 files

5.1.2

Aug 30, 2019
 2 files

5.1.1

Aug 20, 2019
 2 files

5.1.0

Aug 16, 2019
 2 files

5.0.1

Jul 5, 2019
 2 files

5.0.0

Jun 29, 2019
 2 files

4.6.11

Jun 5, 2020
 2 files

4.6.10

May 8, 2020
 2 files

4.6.9

Jan 4, 2020
 2 files

4.6.8

Dec 19, 2019
 2 files

4.6.7

Dec 6, 2019
 2 files

4.6.6

Oct 13, 2019
 2 files

4.6.5

Aug 5, 2019
 2 files

4.6.4

Jun 29, 2019
 2 files

4.6.3

Jun 11, 2019
 2 files

4.6.2

Jun 3, 2019
 2 files

4.6.1

Jun 2, 2019
 2 files

4.6.0

Jun 1, 2019
 2 files

4.5.0

May 11, 2019
 2 files

4.4.2

May 8, 2019
 2 files

4.4.1

Apr 15, 2019
 2 files

4.4.0

Mar 31, 2019
 2 files

4.3.1

Mar 12, 2019
 2 files

4.3.0

Feb 18, 2019
 2 files

4.2.1

Feb 13, 2019
 2 files

4.2.0

Jan 30, 2019
 2 files

4.1.1

Jan 12, 2019
 2 files

4.1.0

Jan 6, 2019
 2 files

4.0.2

Dec 14, 2018
 2 files

4.0.1

Nov 24, 2018
 2 files

4.0.0

Nov 14, 2018
 2 files

3.10.1

Nov 11, 2018
 2 files

3.10.0

Nov 4, 2018
 2 files

3.9.3

Oct 27, 2018
 2 files

3.9.2

Oct 23, 2018
 2 files

3.9.1

Oct 16, 2018
 2 files

3.8.2

Oct 2, 2018
 2 files

3.8.1

Sep 22, 2018
 2 files

3.8.0

Sep 6, 2018
 2 files

3.7.4

Aug 29, 2018
 2 files

3.7.3

Aug 26, 2018
 2 files

3.7.2

Aug 18, 2018
 2 files

3.7.1

Aug 2, 2018
 2 files

3.7.0

Jul 30, 2018
 2 files

3.6.4

Jul 28, 2018
 2 files

3.6.3

Jul 4, 2018
 2 files

3.6.2

Jun 20, 2018
 2 files

3.6.1

Jun 5, 2018
 2 files

3.6.0

May 23, 2018
 2 files

3.5.1

Apr 24, 2018
 2 files

3.5.0

Mar 22, 2018
 2 files

3.4.2

Mar 5, 2018
 2 files

3.4.1

Feb 20, 2018
 2 files

3.4.0

Jan 30, 2018
 2 files

3.3.2

Jan 4, 2018
 2 files

3.3.1

Dec 6, 2017
 2 files

3.3.0

Nov 27, 2017
 2 files

3.2.5

Nov 15, 2017
 2 files

3.2.4

Nov 14, 2017
 2 files

3.2.3

Oct 4, 2017
 2 files

3.2.2

Sep 7, 2017
 2 files

3.2.1

Aug 9, 2017
 2 files

3.2.0

Aug 1, 2017
 2 files

3.1.3

Jul 4, 2017
 2 files

3.1.2

Jun 9, 2017
 2 files

3.1.1

May 31, 2017
 2 files

3.1.0

May 22, 2017
 2 files

3.0.7

Mar 14, 2017
 2 files

3.0.6

Jan 22, 2017
 2 files

3.0.5

Dec 5, 2016
 2 files

3.0.4

Nov 11, 2016
 2 files

3.0.3

Sep 29, 2016
 2 files

3.0.2

Sep 2, 2016
 2 files

3.0.1

Aug 24, 2016
 2 files

3.0.0

Aug 19, 2016
 2 files

2.9.2

May 31, 2016
 2 files

2.9.1

Mar 18, 2016
 2 files

2.9.0

Mar 1, 2016
 2 files

2.8.7

Jan 24, 2016
 2 files

2.8.6

Jan 22, 2016
 2 files

2.8.5

Dec 12, 2015
 2 files

2.8.4

Dec 6, 2015
 2 files

2.8.3

Nov 19, 2015
 2 files

2.8.2

Oct 7, 2015
 2 files

2.8.1

Sep 29, 2015
 2 files

2.8.0

Sep 18, 2015
 2 files

2.7.3

Sep 15, 2015
 2 files

2.7.2

Jun 23, 2015
 2 files

2.7.1

May 19, 2015
 2 files

2.7.0

Mar 26, 2015
 1 file

2.6.4

Oct 24, 2014
 1 file

2.6.3

Sep 24, 2014
 1 file

2.6.2

Sep 5, 2014
 1 file

2.6.1

Aug 7, 2014
 1 file

2.6.0

Jul 20, 2014
 1 file

2.5.2

Jan 29, 2014
 1 file

2.5.1

Dec 17, 2013
 1 file

2.5.0

Dec 12, 2013
 1 file

2.4.2

Oct 4, 2013
 1 file

2.4.1

Oct 2, 2013
 1 file

2.4.0

Oct 1, 2013
 1 file

2.3.5

Apr 30, 2013
 1 file

2.3.4

Nov 20, 2012
 1 file

2.3.3

Nov 6, 2012
 1 file

2.3.2

Oct 25, 2012
 1 file

2.3.1

Oct 20, 2012
 1 file

2.3.0

Oct 19, 2012
 1 file

2.2.4

May 22, 2012
 1 file

2.2.3

Feb 6, 2012
 1 file

2.2.2

Feb 5, 2012
 1 file

2.2.1

Dec 16, 2011
 1 file

2.2.0

Nov 18, 2011
 1 file

2.1.3

Oct 18, 2011
 1 file

2.1.2

Sep 24, 2011
 1 file

2.1.1

Aug 20, 2011
 1 file

2.1.0

Jul 9, 2011
 1 file

2.0.3

Apr 17, 2011
 1 file

2.0.2

Mar 9, 2011
 1 file

2.0.1

Feb 7, 2011
 1 file

2.0.0

Nov 25, 2010
 1 file