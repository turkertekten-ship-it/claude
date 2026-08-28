# Blinker

Blinker provides a fast dispatching system that allows any number of
interested parties to subscribe to events, or "signals".

## Pallets Community Ecosystem

> [!IMPORTANT]
> This project is part of the Pallets Community Ecosystem. Pallets is the open
> source organization that maintains Flask; Pallets-Eco enables community
> maintenance of related projects. If you are interested in helping maintain
> this project, please reach out on the Pallets Discord server.

## Example

Signal receivers can subscribe to specific senders or receive signals
sent by any sender.

```
>>> from blinker import signal
>>> started = signal('round-started')
>>> def each(round):
...     print(f"Round {round}")
...
>>> started.connect(each)

>>> def round_two(round):
...     print("This is round two.")
...
>>> started.connect(round_two, sender=2)

>>> for round in range(1, 4):
...     started.send(round)
...
Round 1!
Round 2!
This is round two.
Round 3!
```

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

blinker-1.9.0.tar.gz
 (22.5 kB
 view details)

Uploaded
 Nov 8, 2024
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

blinker-1.9.0-py3-none-any.whl
 (8.5 kB
 view details)

Uploaded
 Nov 8, 2024
 Python 3

## File details

Details for the file blinker-1.9.0.tar.gz.

### File metadata

- Download URL: blinker-1.9.0.tar.gz
- Upload date:
 Nov 8, 2024
- Size: 22.5 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/5.1.1 CPython/3.12.7

### File hashes

Hashes for blinker-1.9.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | b4ce2265a7abece45e7cc896e98dbebe6cead56bcf805a3d23136d145f5445bf | |
| MD5 | 1ffce54aca3d568ab18ee921d479274f | |
| BLAKE2b-256 | 21289b3f50ce0e048515135495f198351908d99540d69bfdc8c1d15b73dc55ce | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for blinker-1.9.0.tar.gz:

Publisher: publish.yaml on pallets-eco/blinker

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: blinker-1.9.0.tar.gz
 - Subject digest: b4ce2265a7abece45e7cc896e98dbebe6cead56bcf805a3d23136d145f5445bf
 - Sigstore transparency entry: 147619386
 - Sigstore integration time:
 Nov 8, 2024
 Source repository:

 - Permalink: pallets-eco/blinker@669f3a027828d19786e708b511277fabcd6b9532
 - Branch / Tag: refs/tags/1.9.0
 - Owner: https://github.com/pallets-eco
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@669f3a027828d19786e708b511277fabcd6b9532
 - Trigger Event: push

## File details

Details for the file blinker-1.9.0-py3-none-any.whl.

### File metadata

- Download URL: blinker-1.9.0-py3-none-any.whl
- Upload date:
 Nov 8, 2024
- Size: 8.5 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/5.1.1 CPython/3.12.7

### File hashes

Hashes for blinker-1.9.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | ba0efaa9080b619ff2f3459d1d500c57bddea4a6b424b60a91141db6fd2f08bc | |
| MD5 | 26605819b98a22f8bc46ee0eb2e0d4d2 | |
| BLAKE2b-256 | 10cbf2ad4230dc2eb1a74edf38f1a38b9b52277f75bef262d8908e60d957e13c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for blinker-1.9.0-py3-none-any.whl:

Publisher: publish.yaml on pallets-eco/blinker

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: blinker-1.9.0-py3-none-any.whl
 - Subject digest: ba0efaa9080b619ff2f3459d1d500c57bddea4a6b424b60a91141db6fd2f08bc
 - Sigstore transparency entry: 147619387
 - Sigstore integration time:
 Nov 8, 2024
 Source repository:

 - Permalink: pallets-eco/blinker@669f3a027828d19786e708b511277fabcd6b9532
 - Branch / Tag: refs/tags/1.9.0
 - Owner: https://github.com/pallets-eco
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@669f3a027828d19786e708b511277fabcd6b9532
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

1.9.0 This release

Nov 8, 2024
 2 files

1.8.2

May 6, 2024
 2 files

1.8.1

Apr 28, 2024
 2 files

1.8.0

Apr 27, 2024
 2 files

1.7.0

Nov 1, 2023
 2 files

1.6.3

Oct 7, 2023
 2 files

1.6.2

Apr 12, 2023
 2 files

1.6.1

Apr 9, 2023
 2 files

1.6

Apr 2, 2023
 2 files

1.5

Jul 17, 2022
 2 files

1.4

Jul 23, 2015
 1 file

1.3

Jul 3, 2013
 1 file

1.2

Oct 27, 2011
 1 file

1.1

Jul 21, 2010
 1 file

1.0

Mar 28, 2010
 1 file

0.9

Feb 27, 2010
 1 file

0.8

Feb 14, 2010
 1 file