# Click

Click is a Python package for creating beautiful command line interfaces
in a composable way with as little code as necessary. It's the "Command
Line Interface Creation Kit". It's highly configurable but comes with
sensible defaults out of the box.

It aims to make the process of writing command line tools quick and fun
while also preventing any frustration caused by the inability to
implement an intended CLI API.

Click in three points:

- Arbitrary nesting of commands
- Automatic help page generation
- Supports lazy loading of subcommands at runtime

## A Simple Example

```
import click

@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.option("--name", prompt="Your name", help="The person to greet.")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    hello()
```

```
$ python hello.py --count=3
Your name: Click
Hello, Click!
Hello, Click!
Hello, Click!
```

## Donate

The Pallets organization develops and supports Click and other popular
packages. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, please
donate today.

## Contributing

See our detailed contributing documentation for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

click-8.5.0.tar.gz
 (382.2 kB
 view details)

Uploaded
 Aug 26, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

click-8.5.0-py3-none-any.whl
 (125.3 kB
 view details)

Uploaded
 Aug 26, 2026
 Python 3

## File details

Details for the file click-8.5.0.tar.gz.

### File metadata

- Download URL: click-8.5.0.tar.gz
- Upload date:
 Aug 26, 2026
- Size: 382.2 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.14

### File hashes

Hashes for click-8.5.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | ba0d2089de75ea0310e2dde03160e6ca10009947fb95a182f9b54021bb272e34 | |
| MD5 | 39f57e4f423de0d075dd968c29b01539 | |
| BLAKE2b-256 | c70e7fa0ef50764b67090eca4114772a2abf8b6148198475e54c660b97caeee6 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for click-8.5.0.tar.gz:

Publisher: publish.yaml on pallets/click

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: click-8.5.0.tar.gz
 - Subject digest: ba0d2089de75ea0310e2dde03160e6ca10009947fb95a182f9b54021bb272e34
 - Sigstore transparency entry: 2603102647
 - Sigstore integration time:
 Aug 26, 2026
 Source repository:

 - Permalink: pallets/click@8b19813f2bfca99f1018a587a8cf54fc959f2e5d
 - Branch / Tag: refs/tags/8.5.0
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@8b19813f2bfca99f1018a587a8cf54fc959f2e5d
 - Trigger Event: push

## File details

Details for the file click-8.5.0-py3-none-any.whl.

### File metadata

- Download URL: click-8.5.0-py3-none-any.whl
- Upload date:
 Aug 26, 2026
- Size: 125.3 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.14

### File hashes

Hashes for click-8.5.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360 | |
| MD5 | 2f0b6de9bc2aa6bd8ff4200bc7d14bbe | |
| BLAKE2b-256 | 58506c0d534c5f134586a8e1ba4e330569e32f057e33372ae556463212fb4cd3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for click-8.5.0-py3-none-any.whl:

Publisher: publish.yaml on pallets/click

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: click-8.5.0-py3-none-any.whl
 - Subject digest: 255bc9599cf7748b4b1a446ccc735421bd08a2ae529a8b88597d3de5664ee360
 - Sigstore transparency entry: 2603102868
 - Sigstore integration time:
 Aug 26, 2026
 Source repository:

 - Permalink: pallets/click@8b19813f2bfca99f1018a587a8cf54fc959f2e5d
 - Branch / Tag: refs/tags/8.5.0
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@8b19813f2bfca99f1018a587a8cf54fc959f2e5d
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

8.5.0 This release

Aug 26, 2026
 2 files

8.4.2

Jun 24, 2026
 2 files

8.4.1

May 22, 2026
 2 files

8.4.0

May 17, 2026
 2 files

8.3.3

Apr 22, 2026
 2 files

8.3.2

Apr 3, 2026
 2 files

8.3.1

Nov 15, 2025
 2 files

8.3.0

Sep 18, 2025
 2 files

Yanked

8.2.2

Aug 2, 2025
 2 files

8.2.1

May 20, 2025
 2 files

8.2.0

May 10, 2025
 2 files

8.1.8

Dec 21, 2024
 2 files

8.1.7

Aug 17, 2023
 2 files

8.1.6

Jul 18, 2023
 2 files

8.1.5

Jul 13, 2023
 2 files

8.1.4

Jul 6, 2023
 2 files

8.1.3

Apr 28, 2022
 2 files

8.1.2

Mar 31, 2022
 2 files

8.1.1

Mar 30, 2022
 2 files

8.1.0

Mar 28, 2022
 2 files

8.0.4

Feb 18, 2022
 2 files

8.0.3

Oct 10, 2021
 2 files

8.0.2

Oct 8, 2021
 2 files

8.0.1

May 19, 2021
 2 files

8.0.0

May 11, 2021
 2 files

Pre-release

8.0.0rc1

Apr 16, 2021
 2 files

Pre-release

8.0.0a1

Nov 25, 2020
 2 files

7.1.2

Apr 27, 2020
 2 files

7.1.1

Mar 9, 2020
 2 files

7.1

Mar 9, 2020
 2 files

7.0

Sep 25, 2018
 2 files

6.7

Jan 6, 2017
 2 files

Pre-release

6.7.dev0

Jan 6, 2017
 1 file

6.6

Apr 4, 2016
 2 files

6.5

Apr 4, 2016
 1 file

6.4

Mar 23, 2016
 2 files

6.3

Feb 22, 2016
 2 files

6.2

Nov 27, 2015
 2 files

6.1

Nov 27, 2015
 2 files

6.0

Nov 24, 2015
 2 files

5.1

Aug 17, 2015
 2 files

5.0

Aug 16, 2015
 2 files

4.1

Jul 14, 2015
 2 files

4.0

Mar 31, 2015
 2 files

3.3

Sep 7, 2014
 2 files

3.2

Aug 22, 2014
 2 files

3.1

Aug 13, 2014
 2 files

3.0

Aug 12, 2014
 2 files

2.6

Aug 11, 2014
 2 files

2.5

Jul 27, 2014
 2 files

2.4

Jul 4, 2014
 2 files

2.3

Jul 3, 2014
 2 files

2.2

Jun 26, 2014
 2 files

2.1

Jun 14, 2014
 2 files

2.0

Jun 6, 2014
 2 files

1.1

May 23, 2014
 2 files

1.0

May 21, 2014
 2 files

0.7

May 11, 2014
 2 files

0.6

May 7, 2014
 2 files

0.5.1

May 6, 2014
 2 files

0.5

May 6, 2014
 2 files

0.4

May 6, 2014
 2 files

0.3

May 6, 2014
 2 files

0.2

May 5, 2014
 2 files

0.1

Apr 21, 2014
 2 files