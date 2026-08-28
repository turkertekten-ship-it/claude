[image: pypi] [image: conda-forge] [image: versions] [image: github-actions] [image: Join the chat at https://gitter.im/pytest-dev/pluggy] [image: black] [image: Code coverage Status]

This is the core framework used by the pytest, tox, and devpi projects.

Please read the docs to learn more!

## A definitive example

```
import pluggy

hookspec = pluggy.HookspecMarker("myproject")
hookimpl = pluggy.HookimplMarker("myproject")

class MySpec:
    """A hook specification namespace."""

    @hookspec
    def myhook(self, arg1, arg2):
        """My special little hook that you can customize."""

class Plugin_1:
    """A hook implementation namespace."""

    @hookimpl
    def myhook(self, arg1, arg2):
        print("inside Plugin_1.myhook()")
        return arg1 + arg2

class Plugin_2:
    """A 2nd hook implementation namespace."""

    @hookimpl
    def myhook(self, arg1, arg2):
        print("inside Plugin_2.myhook()")
        return arg1 - arg2

# create a manager and add the spec
pm = pluggy.PluginManager("myproject")
pm.add_hookspecs(MySpec)

# register plugins
pm.register(Plugin_1())
pm.register(Plugin_2())

# call our ``myhook`` hook
results = pm.hook.myhook(arg1=1, arg2=2)
print(results)
```

Running this directly gets us:

```
$ python docs/examples/toy-example.py
inside Plugin_2.myhook()
inside Plugin_1.myhook()
[-1, 3]
```

### Support pluggy

Open Collective is an online funding platform for open and transparent communities.
It provides tools to raise money and share your finances in full transparency.

It is the platform of choice for individuals and companies that want to make one-time or
monthly donations directly to the project.

pluggy is part of the pytest-dev project, see more details in the pytest collective.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

pluggy-1.6.0.tar.gz
 (69.4 kB
 view details)

Uploaded
 May 15, 2025
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

pluggy-1.6.0-py3-none-any.whl
 (20.5 kB
 view details)

Uploaded
 May 15, 2025
 Python 3

## File details

Details for the file pluggy-1.6.0.tar.gz.

### File metadata

- Download URL: pluggy-1.6.0.tar.gz
- Upload date:
 May 15, 2025
- Size: 69.4 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.12.8

### File hashes

Hashes for pluggy-1.6.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 7dcc130b76258d33b90f61b658791dede3486c3e6bfb003ee5c9bfb396dd22f3 | |
| MD5 | 54391218af778acb006c2d915085d469 | |
| BLAKE2b-256 | f9e23e91f31a7d2b083fe6ef3fa267035b518369d9511ffab804f839851d2779 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for pluggy-1.6.0.tar.gz:

Publisher: main.yml on pytest-dev/pluggy

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: pluggy-1.6.0.tar.gz
 - Subject digest: 7dcc130b76258d33b90f61b658791dede3486c3e6bfb003ee5c9bfb396dd22f3
 - Sigstore transparency entry: 213422855
 - Sigstore integration time:
 May 15, 2025
 Source repository:

 - Permalink: pytest-dev/pluggy@fd08ab5f811a9b2fa9124ae8cbbd393221151e2c
 - Branch / Tag: refs/tags/1.6.0
 - Owner: https://github.com/pytest-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 main.yml@fd08ab5f811a9b2fa9124ae8cbbd393221151e2c
 - Trigger Event: push

## File details

Details for the file pluggy-1.6.0-py3-none-any.whl.

### File metadata

- Download URL: pluggy-1.6.0-py3-none-any.whl
- Upload date:
 May 15, 2025
- Size: 20.5 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.12.8

### File hashes

Hashes for pluggy-1.6.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746 | |
| MD5 | e107bd9fd0c26746617d74bac26fa0c5 | |
| BLAKE2b-256 | 54204d324d65cc6d9205fabedc306948156824eb9f0ee1633355a8f7ec5c66bf | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for pluggy-1.6.0-py3-none-any.whl:

Publisher: main.yml on pytest-dev/pluggy

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: pluggy-1.6.0-py3-none-any.whl
 - Subject digest: e920276dd6813095e9377c0bc5566d94c932c33b27a3e3945d8389c374dd4746
 - Sigstore transparency entry: 213422857
 - Sigstore integration time:
 May 15, 2025
 Source repository:

 - Permalink: pytest-dev/pluggy@fd08ab5f811a9b2fa9124ae8cbbd393221151e2c
 - Branch / Tag: refs/tags/1.6.0
 - Owner: https://github.com/pytest-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 main.yml@fd08ab5f811a9b2fa9124ae8cbbd393221151e2c
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

1.6.0 This release

May 15, 2025
 2 files

1.5.0

Apr 20, 2024
 2 files

1.4.0

Jan 24, 2024
 2 files

1.3.0

Aug 26, 2023
 2 files

1.2.0

Jun 21, 2023
 2 files

Yanked

1.1.0

Jun 19, 2023
 2 files

1.0.0

Aug 25, 2021
 2 files

Pre-release

1.0.0.dev0

Jun 4, 2020
 2 files

0.13.1

Nov 21, 2019
 2 files

0.13.0

Sep 10, 2019
 2 files

0.12.0

May 27, 2019
 2 files

0.11.0

May 7, 2019
 2 files

0.10.0

May 7, 2019
 2 files

0.9.0

Feb 24, 2019
 2 files

0.8.1

Jan 9, 2019
 2 files

0.8.0

Oct 16, 2018
 2 files

0.7.1

Jul 28, 2018
 2 files

0.6.0

Nov 24, 2017
 3 files

0.5.2

Sep 6, 2017
 2 files

0.5.1

Aug 29, 2017
 2 files

0.5.0

Aug 29, 2017
 1 file

0.4.0

Sep 25, 2016
 2 files

0.3.1

Sep 17, 2015
 2 files

0.3.0

May 7, 2015
 2 files