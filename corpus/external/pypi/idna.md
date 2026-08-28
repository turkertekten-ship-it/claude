# Internationalized Domain Names in Applications (IDNA)

Support for Internationalized Domain Names in Applications
(IDNA) and Unicode IDNA
Compatibility Processing. It
supersedes the standard library's encodings.idna, which only
implements the 2003 specification, offering broader script coverage and
limiting domains with known security vulnerabilities.

## Usage

Package may be installed from PyPI via
the typical methods (e.g. python3 -m pip install idna)

For typical usage, the encode and decode functions will take a
domain name argument and perform a conversion to ASCII-compatible encoding
(known as A-labels), or to Unicode strings (known as U-labels)
respectively.

```
>>> import idna
>>> idna.encode('ドメイン.テスト')
b'xn--eckwd4c7c.xn--zckzah'
>>> print(idna.decode('xn--eckwd4c7c.xn--zckzah'))
ドメイン.テスト
```

Conversions can be applied at a per-label basis using the ulabel or
alabel functions for specialized use cases.

### Compatibility Mapping (UTS #46)

This library provides support for Unicode IDNA Compatibility
Processing which normalizes input from
different potential ways a user may input a domain prior to performing the IDNA
conversion operations. This functionality, known as a
mapping, is considered by the
specification to be a local user-interface issue distinct from IDNA
conversion functionality.

For example, "Königsgäßchen" is not a permissible label as capital letters
are not allowed. UTS #46 will convert this into lower case prior to applying
the IDNA conversion.

```
>>> import idna
>>> idna.encode('Königsgäßchen')
...
idna.core.InvalidCodepoint: Codepoint U+004B at position 1 of 'Königsgäßchen' not allowed
>>> idna.encode('Königsgäßchen', uts46=True)
b'xn--knigsgchen-b4a3dun'
>>> idna.decode('xn--knigsgchen-b4a3dun')
'königsgäßchen'
```

When performing a decode operation for display purposes, decode()
accepts a display=True argument that leaves any xn-- label that
fails to decode unchanged. This is useful for user interface display
where a domain is in use, the A-label form can be presented when it
is not a valid IDN.

## Exceptions

All errors raised during conversion derive from the idna.IDNAError
base class. The more specific exceptions are:

- idna.IDNABidiError — raised when a label contains an illegal
combination of left-to-right and right-to-left characters.
- idna.InvalidCodepoint — raised when a label contains a codepoint
that is INVALID for IDNA.
- idna.InvalidCodepointContext — raised when a CONTEXTO or CONTEXTJ
codepoint appears in a position whose contextual requirements are
not satisfied.

Exceptions carry machine-readable attributes so that applications
do not need to parse the message: code is a short, stable identifier
for the rule that failed (listed below); and, when the failure can be
attributed to a particular character, text (the label, or domain for
UTS #46 processing, being validated), codepoint (the offending
codepoint as an integer) and position (its 1-based index within
text, as quoted in the message) are set. Each is None when it does
not apply. Message wording is not part of the API and may change.

```
>>> try:
...     idna.encode('Königsgäßchen')
... except idna.IDNAError as err:
...     print(err.code, err.codepoint, err.position, err.text)
disallowed_codepoint 75 1 Königsgäßchen
```

| code | Meaning |
| input_too_long | Input exceeds the library's defensive length limit and was not processed |
| label_too_long | A label exceeds 63 octets |
| domain_too_long | The domain exceeds 253 octets |
| empty_label | A label is empty (e.g. consecutive dots) |
| empty_domain | The domain is empty |
| not_nfc | The label is not in Unicode Normalization Form C |
| hyphen_3_4 | The label has hyphens in the 3rd and 4th positions |
| hyphen_start_end | The label starts or ends with a hyphen |
| leading_combiner | The label starts with a combining mark |
| disallowed_codepoint | A codepoint is DISALLOWED or UNASSIGNED under IDNA 2008 |
| contextj | A CONTEXTJ codepoint (joiner) appears in an invalid context |
| contexto | A CONTEXTO codepoint appears in an invalid context |
| unknown_codepoint | A codepoint next to a joiner is unknown to this Python's Unicode database |
| bidi_rule_1 ... bidi_rule_6 | The corresponding rule of RFC 5893 (the Bidi Rule) is violated |
| bidi_unknown_direction | A codepoint's directionality is unknown to this Python's Unicode database |
| invalid_alabel | An xn-- label is malformed or is not valid Punycode |
| non_canonical_alabel | An xn-- label is not the canonical Punycode encoding of its U-label (a "fake A-label") |
| invalid_ascii | Byte input is not ASCII |
| invalid_utf8 | Byte input is not UTF-8 |
| uts46_disallowed | A codepoint is disallowed by the UTS #46 mapping table |
| uts46_std3 | An ASCII character is rejected by the UTS #46 STD3 rules |
| unsupported_errors | The codec was given an errors handler other than strict |

## Command-line tool

The package supports command-line usage to convert domain names
between their Unicode and ASCII-compatible forms. It can be run either
as a module (python3 -m idna) or, once installed (such as with uv tool or pipx), via the idna script:

```
$ uv tool install idna
$ idna xn--e1afmkfd.xn--p1ai
пример.рф
$ idna пример.рф
xn--e1afmkfd.xn--p1ai
```

Mode can be specified with -e/--encode or -d/--decode, otherwise
it will be chosen automatically based on the first input. Multiple
domains can be supplied either as arguments or through standard input.
UTS #46 mapping is applied by default, which lets the tool accept
inputs that aren't strictly valid IDNA 2008 by normalising them first,
pass --strict to disable UTS #46.

Conversion failures are reported on stderr together with the
offending input; processing continues with the remaining domains and
the tool exits with a non-zero status if any conversion failed.

## Additional Notes

- Python version support. This library supports Python 3.9 and higher.
As this library serves as a low-level toolkit for a variety of
applications, we strive to support all versions of Python that are
not beyond end-of-life. Free-threaded Python is also supported,
as the library holds no mutable global state the functions can be
called concurrently from multiple threads.
- Unicode version. The IDNA and UTS #46 lookup tables are generated
from a specific Unicode release. Some Unicode data depends on the
running Python's unicodedata module, so on an older Python a
character new to Unicode may be rejected as unknown even if this
library knows about it.
- Emoji. It is an occasional request to support emoji domains in
this library. Encoding of symbols like emoji is expressly prohibited by
the IDNA technical standard, and emoji domains are broadly phased
out across the domain industry due to associated security risks.
- Regenerating lookup tables. The IDNA and UTS #46 functionality
relies upon pre-calculated lookup tables, generated using the
idna-data script in tools/.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

idna-3.19.tar.gz
 (215.2 kB
 view details)

Uploaded
 Aug 18, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

idna-3.19-py3-none-any.whl
 (68.5 kB
 view details)

Uploaded
 Aug 18, 2026
 Python 3

## File details

Details for the file idna-3.19.tar.gz.

### File metadata

- Download URL: idna-3.19.tar.gz
- Upload date:
 Aug 18, 2026
- Size: 215.2 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for idna-3.19.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 5e0811a4383b21dc5838069f801c4fb62113b7447663d2530d2bd6e77b49bf15 | |
| MD5 | c00c894c13c6267c2066c75521f77a76 | |
| BLAKE2b-256 | 5ff7abb373e5757eaec4b922b92f97ec8d6d7e057cf06778247604fbc4e7c3f3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for idna-3.19.tar.gz:

Publisher: deploy.yml on kjd/idna

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: idna-3.19.tar.gz
 - Subject digest: 5e0811a4383b21dc5838069f801c4fb62113b7447663d2530d2bd6e77b49bf15
 - Sigstore transparency entry: 2500406915
 - Sigstore integration time:
 Aug 18, 2026
 Source repository:

 - Permalink: kjd/idna@03a9a11dd8aecd4fea742cabe20f4d3d9ed82abb
 - Branch / Tag: refs/tags/v3.19
 - Owner: https://github.com/kjd
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 deploy.yml@03a9a11dd8aecd4fea742cabe20f4d3d9ed82abb
 - Trigger Event: push

## File details

Details for the file idna-3.19-py3-none-any.whl.

### File metadata

- Download URL: idna-3.19-py3-none-any.whl
- Upload date:
 Aug 18, 2026
- Size: 68.5 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for idna-3.19-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 815e7be7a7806d54abb586dc943addc79e8b2ee16915059658cbeff4b1b43bf4 | |
| MD5 | fd35a08db9d6bc5e4208c6258312e9cd | |
| BLAKE2b-256 | 57b00e52c878c53f245edd3a11020f20979b3f490f245af532c7cae3027754b5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for idna-3.19-py3-none-any.whl:

Publisher: deploy.yml on kjd/idna

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: idna-3.19-py3-none-any.whl
 - Subject digest: 815e7be7a7806d54abb586dc943addc79e8b2ee16915059658cbeff4b1b43bf4
 - Sigstore transparency entry: 2500406920
 - Sigstore integration time:
 Aug 18, 2026
 Source repository:

 - Permalink: kjd/idna@03a9a11dd8aecd4fea742cabe20f4d3d9ed82abb
 - Branch / Tag: refs/tags/v3.19
 - Owner: https://github.com/kjd
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 deploy.yml@03a9a11dd8aecd4fea742cabe20f4d3d9ed82abb
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

3.19 This release

Aug 18, 2026
 2 files

3.18

Jun 2, 2026
 2 files

3.17

May 28, 2026
 2 files

3.16

May 22, 2026
 2 files

3.15

May 12, 2026
 2 files

3.14

May 10, 2026
 2 files

3.13

Apr 22, 2026
 2 files

3.12

Apr 21, 2026
 2 files

3.11

Oct 12, 2025
 2 files

3.10

Sep 15, 2024
 2 files

3.9

Sep 14, 2024
 2 files

3.8

Aug 23, 2024
 2 files

3.7

Apr 11, 2024
 2 files

3.6

Nov 25, 2023
 2 files

3.5

Nov 24, 2023
 2 files

3.4

Sep 14, 2022
 2 files

3.3

Oct 12, 2021
 2 files

3.2

May 29, 2021
 2 files

3.1

Jan 4, 2021
 2 files

3.0

Jan 1, 2021
 2 files

2.10

Jun 27, 2020
 2 files

2.9

Feb 17, 2020
 2 files

2.8

Dec 4, 2018
 2 files

2.7

Jun 11, 2018
 2 files

2.6

Aug 8, 2017
 2 files

2.5

Mar 7, 2017
 2 files

2.4

Mar 1, 2017
 2 files

2.3

Feb 28, 2017
 2 files

2.2

Dec 21, 2016
 2 files

2.1

Mar 20, 2016
 3 files

2.0

May 19, 2015
 2 files

1.1

Jan 27, 2015
 1 file

1.0

Oct 12, 2014
 1 file

0.9

Jul 18, 2014
 1 file

0.8

Jul 10, 2014
 1 file

0.7

Jul 10, 2014
 1 file

0.6

Apr 29, 2014
 1 file

0.5

Feb 5, 2014
 1 file

0.4

Jan 7, 2014
 1 file

0.3

Jul 18, 2013
 1 file

0.2

Jul 16, 2013
 1 file

0.1

May 27, 2013