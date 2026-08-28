## iniconfig: brain-dead simple parsing of ini files

iniconfig is a small and simple INI-file parser module
having a unique set of features:

- maintains order of sections and entries
- supports multi-line values with or without line-continuations
- supports “#” comments everywhere
- raises errors with proper line-numbers
- no bells and whistles like automatic substitutions
- iniconfig raises an Error if two sections have the same name.

If you encounter issues or have feature wishes please report them to:

> https://github.com/RonnyPfannschmidt/iniconfig/issues

## Basic Example

If you have an ini file like this:

```
# content of example.ini
[section1] # comment
name1=value1  # comment
name1b=value1,value2  # comment

[section2]
name2=
    line1
    line2
```

then you can do:

```
>>> import iniconfig
>>> ini = iniconfig.IniConfig("example.ini")
>>> ini['section1']['name1'] # raises KeyError if not exists
'value1'
>>> ini.get('section1', 'name1b', [], lambda x: x.split(","))
['value1', 'value2']
>>> ini.get('section1', 'notexist', [], lambda x: x.split(","))
[]
>>> [x.name for x in list(ini)]
['section1', 'section2']
>>> list(list(ini)[0].items())
[('name1', 'value1'), ('name1b', 'value1,value2')]
>>> 'section1' in ini
True
>>> 'inexistendsection' in ini
False
```

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

iniconfig-2.3.0.tar.gz
 (20.5 kB
 view details)

Uploaded
 Oct 18, 2025
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

iniconfig-2.3.0-py3-none-any.whl
 (7.5 kB
 view details)

Uploaded
 Oct 18, 2025
 Python 3

## File details

Details for the file iniconfig-2.3.0.tar.gz.

### File metadata

- Download URL: iniconfig-2.3.0.tar.gz
- Upload date:
 Oct 18, 2025
- Size: 20.5 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for iniconfig-2.3.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | c76315c77db068650d49c5b56314774a7804df16fee4402c1f19d6d15d8c4730 | |
| MD5 | 5c1d9c21275feb3da71400bf716edd72 | |
| BLAKE2b-256 | 723414ca021ce8e5dfedc35312d08ba8bf51fdd999c576889fc2c24cb97f4f10 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for iniconfig-2.3.0.tar.gz:

Publisher: test.yml on pytest-dev/iniconfig

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: iniconfig-2.3.0.tar.gz
 - Subject digest: c76315c77db068650d49c5b56314774a7804df16fee4402c1f19d6d15d8c4730
 - Sigstore transparency entry: 621686326
 - Sigstore integration time:
 Oct 18, 2025
 Source repository:

 - Permalink: pytest-dev/iniconfig@7faed13ae50bad7c5da3f5782f254a8a7736bb84
 - Branch / Tag: refs/tags/v2.3.0
 - Owner: https://github.com/pytest-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 test.yml@7faed13ae50bad7c5da3f5782f254a8a7736bb84
 - Trigger Event: push

## File details

Details for the file iniconfig-2.3.0-py3-none-any.whl.

### File metadata

- Download URL: iniconfig-2.3.0-py3-none-any.whl
- Upload date:
 Oct 18, 2025
- Size: 7.5 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for iniconfig-2.3.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12 | |
| MD5 | d3e156a9abd59ac8b5eb0c2e8b1c5dad | |
| BLAKE2b-256 | cbb13846dd7f199d53cb17f49cba7e651e9ce294d8497c8c150530ed11865bb8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for iniconfig-2.3.0-py3-none-any.whl:

Publisher: test.yml on pytest-dev/iniconfig

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: iniconfig-2.3.0-py3-none-any.whl
 - Subject digest: f631c04d2c48c52b84d0d0549c99ff3859c98df65b3101406327ecc7d53fbf12
 - Sigstore transparency entry: 621686328
 - Sigstore integration time:
 Oct 18, 2025
 Source repository:

 - Permalink: pytest-dev/iniconfig@7faed13ae50bad7c5da3f5782f254a8a7736bb84
 - Branch / Tag: refs/tags/v2.3.0
 - Owner: https://github.com/pytest-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 test.yml@7faed13ae50bad7c5da3f5782f254a8a7736bb84
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

2.3.0 This release

Oct 18, 2025
 2 files

2.2.0

Oct 18, 2025
 2 files

2.1.0

Mar 19, 2025
 2 files

2.0.0

Jan 7, 2023
 2 files

1.1.1

Oct 14, 2020
 2 files

1.1.0

Oct 14, 2020
 1 file

1.0.1

Jul 31, 2020
 2 files

1.0.0

Sep 23, 2016
 1 file

Pre-release

0.2.dev0

Oct 14, 2010
 1 file

0.1

Oct 12, 2010
 1 file

0.0

Sep 29, 2010