---
date: 2026-07-20T02:04:21+0000
source: https://pypi.org/project/yarl/
---
## yarl

The module provides handy URL class for URL parsing and changing.

 [image: https://github.com/aio-libs/yarl/workflows/CI/badge.svg] [image: Codecov coverage for the pytest-driven measurements] [image: https://img.shields.io/endpoint?url=https://codspeed.io/badge.json] [image: https://badge.fury.io/py/yarl.svg] [image: https://readthedocs.org/projects/yarl/badge/?version=latest] [image: https://img.shields.io/pypi/pyversions/yarl.svg] [image: Matrix Room — #aio-libs:matrix.org] [image: Matrix Space — #aio-libs-space:matrix.org]

### Introduction

Url is constructed from str:

```
>>> from yarl import URL
>>> url = URL('https://www.python.org/~guido?arg=1#frag')
>>> url
URL('https://www.python.org/~guido?arg=1#frag')
```

All url parts: scheme, user, password, host, port, path,
query and fragment are accessible by properties:

```
>>> url.scheme
'https'
>>> url.host
'www.python.org'
>>> url.path
'/~guido'
>>> url.query_string
'arg=1'
>>> url.query
<MultiDictProxy('arg': '1')>
>>> url.fragment
'frag'
```

All url manipulations produce a new url object:

```
>>> url = URL('https://www.python.org')
>>> url / 'foo' / 'bar'
URL('https://www.python.org/foo/bar')
>>> url / 'foo' % {'bar': 'baz'}
URL('https://www.python.org/foo?bar=baz')
```

Strings passed to constructor and modification methods are
automatically encoded giving canonical representation as result:

```
>>> url = URL('https://www.python.org/шлях')
>>> url
URL('https://www.python.org/%D1%88%D0%BB%D1%8F%D1%85')
```

Regular properties are percent-decoded, use raw_ versions for
getting encoded strings:

```
>>> url.path
'/шлях'

>>> url.raw_path
'/%D1%88%D0%BB%D1%8F%D1%85'
```

Human readable representation of URL is available as .human_repr():

```
>>> url.human_repr()
'https://www.python.org/шлях'
```

For full documentation please read https://yarl.aio-libs.org.

### Installation

```
$ pip install yarl
```

The library is Python 3 only!

PyPI contains binary wheels for Linux, Windows and MacOS. If you want to install
yarl on another operating system where wheels are not provided,
the tarball will be used to compile the library from
the source code. It requires a C compiler and and Python headers installed.

To skip the compilation you must explicitly opt-in by using a PEP 517
configuration setting pure-python, or setting the YARL_NO_EXTENSIONS
environment variable to a non-empty value, e.g.:

```
$ pip install yarl --config-settings=pure-python=false
```

Please note that the pure-Python (uncompiled) version is much slower. However,
PyPy always uses a pure-Python implementation, and, as such, it is unaffected
by this variable.

### Dependencies

YARL requires multidict and propcache libraries.

### API documentation

The documentation is located at https://yarl.aio-libs.org.

### Why isn’t boolean supported by the URL query API?

There is no standard for boolean representation of boolean values.

Some systems prefer true/false, others like yes/no, on/off,
Y/N, 1/0, etc.

yarl cannot make an unambiguous decision on how to serialize bool values because
it is specific to how the end-user’s application is built and would be different for
different apps. The library doesn’t accept booleans in the API; a user should convert
bools into strings using own preferred translation protocol.

### Comparison with other URL libraries

- furl (https://pypi.python.org/pypi/furl)

The library has rich functionality but the furl object is mutable.

I’m afraid to pass this object into foreign code: who knows if the
code will modify my url in a terrible way while I just want to send URL
with handy helpers for accessing URL properties.

furl has other non-obvious tricky things but the main objection
is mutability.
- URLObject (https://pypi.python.org/pypi/URLObject)

URLObject is immutable, that’s pretty good.

Every URL change generates a new URL object.

But the library doesn’t do any decode/encode transformations leaving the
end user to cope with these gory details.

### Source code

The project is hosted on GitHub

Please file an issue on the bug tracker if you have found a bug
or have some suggestion in order to improve the library.

### Discussion list

aio-libs google group: https://groups.google.com/forum/#!forum/aio-libs

Feel free to post your questions and ideas here.

### Authors and License

The yarl package is written by Andrew Svetlov.

It’s Apache 2 licensed and freely available.

#### Changelog

## v1.24.5

(2026-07-19)

### Contributor-facing changes

- Restricted the exhaustive IDNA default-ignorable sweep test to a native
Linux x86_64 runner. It iterates roughly 140,000 code points and its result
does not depend on the architecture, so running it under emulated wheel
builds only added minutes and intermittently crashed the test workers
– by @bdraco.

Related issues and pull requests on GitHub: #1806.

---

## v1.24.4

(2026-07-19)

### Packaging updates and notes for downstreams

- Stopped installing hypothesis in the wheel-build test environment. The
property-based quoting tests that need it are skipped there already, and
building it from source on architectures without a prebuilt wheel (such as
armv7l musllinux, where the build pulls in a Rust toolchain) was failing
the wheel jobs – by @bdraco.

Related issues and pull requests on GitHub: #1804.

---

## v1.24.3

(2026-07-19)

### Bug fixes

- Fixed the ~yarl.URL.host property incorrectly returning the
percent-encoded zone ID separator %25 instead of decoding it to %
for IPv6 Zone ID URLs (e.g. http://[fe80::1%251]/ now correctly exposes
.host as fe80::1%1 per 6874)
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1653.
- Fixed _check_netloc() missing % from its NFKC normalization character
check, which allowed Unicode characters U+FF05 (FULLWIDTH PERCENT SIGN) and
U+FE6A (SMALL PERCENT SIGN) to produce a literal % in url.host via
the standard library IDNA fallback
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1655.
- Fixed yarl.URL.build() failing to validate characters in the zone ID
portion of IPv6 addresses when validate_host=True, allowing control
characters such as CR, LF, and NUL to pass through into url.host.
Zone IDs now reject ASCII control characters and the empty string (a bare
trailing %) per
RFC 9844 §6.3
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1655.
- Fixed the Cython quoting backend retaining a lone surrogate code
point when it was the only character forcing a rewrite; the
pure-Python backend already dropped lone surrogates, so both now
drop them and produce identical output
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1751.
- Fixed the Cython quoting backend percent-encoding the % of a
%XX escape when a lone surrogate fell within it, instead of
dropping the surrogate and keeping the escape; it now matches the
pure-Python backend and produces identical output
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1752.
- Fixed the Cython quoter preserving lone surrogate characters
(U+D800..``U+DFFF``) instead of dropping them; it now matches the
pure-Python quoter, which strips them, so both backends produce the
same output for the same input – by @bdraco.

Related issues and pull requests on GitHub: #1799.
- Fixed URL.build()() and
yarl.URL.with_host() accepting hosts that expand to a URL
delimiter (/, ? or #) under IDNA normalization; such hosts
are now rejected, so the builder APIs agree with the parser
– by @bdraco.

Related issues and pull requests on GitHub: #1800.
- Fixed host encoding accepting Unicode default-ignorable and format code
points (such as soft hyphen, zero-width space, and word joiner) that IDNA
normalization silently drops or otherwise folds into a different host,
so the parsed host could differ from the input string; such hosts are now
rejected on both the ~yarl.URL constructor and the builder APIs
(URL.build()() and yarl.URL.with_host())
– by @bdraco.

Related issues and pull requests on GitHub: #1801.
- Fixed yarl.URL.build(), yarl.URL.joinpath() (and the /
operator), yarl.URL.with_name(), and yarl.URL.with_suffix()
building a URL with no host and no scheme whose serialized string could be
parsed back as an absolute or executable-scheme URL; a scheme-shaped leading
colon in a relative path is now percent-encoded, matching the parser and
yarl.URL.human_repr() – by @bdraco.

Related issues and pull requests on GitHub: #1802.

### Improved documentation

- Documented how ~yarl.URL.host and ~yarl.URL.raw_host
expose 6874 IPv6 zone identifiers and that the host subcomponent
properties include the zone identifier verbatim
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #998.
- Fixed the stale with_name() example output in the API reference; the
apostrophe is a character that 3986 allows unencoded in path
segments – by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1784.

### Packaging updates and notes for downstreams

- The setuptools build dependency lower bound has been restored to be
>= 47 after an incorrect automated increase in PR #1657
– by @bbhtt.

Related issues and pull requests on GitHub: #1764.
- Fixed the in-tree PEP 517 build backend to import Cython at the point
of use instead of module load time. The build front-ends that serve all
the build hooks from a single long-running backend process, the way
pyproject-api under tox does, import the backend before the
dynamically declared Cython build dependency is provisioned, so the
accelerated build used to fail with a NameError
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1784.

### Contributor-facing changes

- Added UV_CONSTRAINT and UV_BUILD_CONSTRAINT alongside
PIP_CONSTRAINT and PIP_BUILD_CONSTRAINT in the
cibuildwheel environment so the requirements/cython.txt
pin is honored under the build[uv] frontend; uv pip
ignores the PIP_ variables and reads only the UV_ ones,
while the PIP_ variants are kept for the pip fallback path
– by @bdraco.

Related issues and pull requests on GitHub: #1729.
- Dependabot has been restricted to the requirements subdirectory to
avoid unintended updates outside dependency requirement files
– by @bbhtt.

Related issues and pull requests on GitHub: #1764.
- Started running the Sphinx doctest builder in CI through the
doctest-docs tox environment, which existed but was never wired
into the lint matrix and never installed the package whose examples it
runs. Also added spelling word list entries so the spell check passes
with dictionary backends other than the one CI uses
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1784.

### Miscellaneous internal changes

- Added regression tests ensuring that lone surrogates produced by
decoding invalid UTF-8 with surrogateescape are preserved when
building a URL with encoded=True and are dropped consistently by
the C and pure-Python quoting backends when parsing
– by @pajod.

Related issues and pull requests on GitHub: #991.
- Expanded the test suite to pin IPv6 zone identifier handling per the
6874 compatibility research: the %25 and legacy bare %
separator forms, empty zone and reserved character corner cases,
encoded=True round-trips, and zone survival through URL mutation
APIs – by @rodrigobnogueira.

Related issues and pull requests on GitHub: #998.

---

## v1.24.2

(2026-05-19)

### Contributor-facing changes

- Switched the aarch64 and armv7l wheel builds to GitHub’s native ARM
runners. The aarch64 wheels now build without QEMU emulation, and
armv7l runs on aarch64 hosts so its 32-bit ARM execution is far
cheaper than the previous aarch64-on-x86_64 path
– by @bdraco.

Related issues and pull requests on GitHub: #1724.
- Restored per-runner native arches in the Windows wheel matrix on tag
releases. The previous CIBW_ARCHS_WINDOWS=AMD64 ARM64 setting made
both windows-latest and windows-11-arm cross-compile the other
arch, producing two artifacts with identically-named wheels whose
bytes differed; the deploy job’s download-artifact ... merge-multiple
step tore those writes together, yielding a wheel that PyPI rejected
with 400 Invalid distribution file. ZIP archive not accepted: Mis-matched data size during the 1.24.0 and 1.24.1 releases
– by @bdraco.

Related issues and pull requests on GitHub: #1725.

---

## v1.24.1

(2026-05-19)

### Contributor-facing changes

- Allowed re-running the deploy job after a partial release failure: the
Make Release step now skips when the GitHub Release already exists,
and the PyPI publish step uses skip-existing so dists that were
already uploaded on a prior attempt do not break the retry
– by @bdraco.

Related issues and pull requests on GitHub: #1721.

---

## v1.24.0

(2026-05-19)

### Bug fixes

- Delayed importing pydantic until it’s needed to avoid increased import time – by @Dreamsorcerer.

Related issues and pull requests on GitHub: #1607, #1702.
- Fixed pickling of ~yarl.URL on Python 3.15, where SplitResult
gained a __getstate__ that requires attributes set by __init__.
__getstate__ now returns the raw 5-tuple instead of a SplitResult
built via tuple.__new__, so pickling no longer touches SplitResult
serialization at all. Pickles produced by older yarl releases (which embed
a SplitResult) continue to load unchanged
– by @befeleme.

Related issues and pull requests on GitHub: #1632, #1642, #1687.
- Fixed a parsing issue where URLs containing text before an opening bracket
in the host component (e.g. http://127.0.0.1[aa::ff]) were silently accepted
instead of being rejected as strictly invalid per RFC 3986
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1654.
- Raise ValueError when a URL’s authority component contains a
backslash, which is not a valid character per 3986
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1659.
- Fixed a host-confusion parsing bug where URLs containing multiple bracket
characters in the host component (e.g. http://[:localhost[]].google:80)
were silently parsed as an unintended host. Both split_url() and
split_netloc() now raise ValueError when more than one [ or
] is found in the authority, or when [ does not appear at the start of
the host subcomponent, in compliance with 3986 – by
@rodrigobnogueira.

Related issues and pull requests on GitHub: #1661.
- Fixed a parser/serializer inconsistency where percent-encoded characters in
the scheme portion of a URL (e.g. ht%74p://...) were decoded by the
requoter, causing str() and yarl.URL.human_repr() to emit an
absolute URL with a scheme and host while the parsed properties
(~yarl.URL.scheme, ~yarl.URL.host, ~yarl.URL.absolute)
reported a relative, hostless URL. The fix preserves the percent-encoding of
the colon (%3A) in relative paths whenever decoding it would materialize a
URL scheme – by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1669.
- Fixed a parsing issue where URLs containing text after the closing bracket
of an IP-literal host (e.g. http://[::1]allowed.example:1/) were silently
accepted and normalized to the bracketed IP address (http://[::1]:1/),
dropping the trailing suffix and changing the effective host identity.
Per RFC 3986, after the closing ] only : followed by a port number or
end-of-authority is valid
– by @rodrigobnogueira.

Related issues and pull requests on GitHub: #1672.

### Features

- Start building and shipping riscv64 wheels
– by @justeph.

Related issues and pull requests on GitHub: #1626.

### Removals and backward incompatible breaking changes

- Dropped support for the experimental free-threaded build of Python 3.13 – by @ngoldbaum.

Related issues and pull requests on GitHub: #1667.

### Improved documentation

- Added a note in the yarl.URL.with_query() documentation explaining
that types implementing __int__ (e.g. ~uuid.UUID) are
converted to integers, and advising users to cast to str when the
human-readable representation is needed – by @r266-tech.

Related issues and pull requests on GitHub: #1638, #1645.

### Contributor-facing changes

- Resolved a ruff ISC004 violation in the PEP 517 build backend so the
pre-commit ruff-check hook passes again
– by @bdraco.

Related issues and pull requests on GitHub: #1674.
- Renamed the actions/checkout depth input to fetch-depth in the
reusable codspeed workflow so the actionlint pre-commit hook passes and the
intended shallow clone actually takes effect
– by @bdraco.

Related issues and pull requests on GitHub: #1676.
- Bumped the pinned pyupgrade pre-commit hook to v3.21.2 so it stops
crashing on Python 3.14, which made tokenize.cookie_re bytes-only
– by @bdraco.

Related issues and pull requests on GitHub: #1677.
- The type preciseness coverage report generated by MyPy is now uploaded to Coveralls and
will not be included in the Codecov views going forward
– by @webknjaz.

Related issues and pull requests on GitHub: #1680.
- Raised the per-matrix-cell timeout of the CI Test job from
5 to 10 minutes to prevent false failures on slower runners
– by @aiolibsbot.

Related issues and pull requests on GitHub: #1683.
- Added an AGENTS.md orientation file at the repository root,
covering the pull request template, CHANGES/ news fragment
conventions, draft-PR workflow, and the Cython quoter layout, so
LLM contributors land changes that match project style
– by @bdraco.

Related issues and pull requests on GitHub: #1685.
- Documented in AGENTS.md that the coverage gate also
applies to test code, so unreachable defensive raise guards
and one-sided cleanup branches in tests will fail CI
– by @bdraco.

Related issues and pull requests on GitHub: #1689.
- Shrunk the CI wheel-build matrix on pull requests and non-tag pushes by
restricting CIBW_ARCHS_MACOS to arm64, CIBW_ARCHS_WINDOWS to
AMD64, and skipping the windows-11-arm runner – the test matrix only
exercises those architectures, so the previously-built x86_64 macOS and
ARM64 Windows wheels were never installed. Tag releases still build the
full architecture set
– by @aiolibsbot.

Related issues and pull requests on GitHub: #1692.
- Documented the docs spell check (make doc-spelling) in
AGENTS.md as a pre-push gate, mirroring
aio-libs/multidict#1345. The
spell checker reads every CHANGES/*.rst fragment as part
of the docs build, so an unknown technical word in a news
fragment fails CI before a human sees the PR
– by @bdraco.

Related issues and pull requests on GitHub: #1693.
- Added a CLAUDE.md at the repository root that imports
AGENTS.md via Claude Code’s @-syntax, so the
project’s LLM contributor rules load automatically when
working in Claude Code
– by @bdraco.

Related issues and pull requests on GitHub: #1696.
- Enforced top-level imports across yarl and tests via the ruff
PLC0415 rule, wired through a new ruff-check pre-commit hook.
Function-scoped imports must now opt in with # noqa: PLC0415 plus
a comment explaining the import-time reason. Dropped the yesqa
hook, which could not recognize ruff-only codes and stripped the new
noqa comments as stale; a wider migration off flake8 onto ruff
will follow separately
– by @bdraco.

Related issues and pull requests on GitHub: #1697.
- Migrated the main tree from standalone black and isort
pre-commit hooks to ruff format and the ruff I lint rule,
sharing the existing [tool.ruff] config in pyproject.toml.
ruff-check now runs with --fix so import-order fixes apply
on commit, and the orphan [isort] block in setup.cfg was
removed. The packaging/pep517_backend/ subtree keeps its own
.ruff.toml and is unaffected
– by @bdraco.

Related issues and pull requests on GitHub: #1698.
- Switched the cibuildwheel build frontend to build[uv] so
that uv provisions every build and test virtual environment
in the wheel matrix. Test-dependency installation in particular
drops from a multi-second pip install per ABI to a roughly
sub-second uv resolve
– by @bdraco.

Related issues and pull requests on GitHub: #1699.
- Restructured the root CLAUDE.md to import contributor
context from a shared aio-libs layer
(~/.claude/aio-libs/context.md), a project-specific layer
(~/.claude/aio-libs/yarl/context.md), the in-tree
AGENTS.md, and an optional per-checkout
CLAUDE.local.md override (added to .gitignore),
so shared aio-libs guidance can live outside the repository
while project rules continue to load automatically in Claude
Code – by @aiolibsbot.

Related issues and pull requests on GitHub: #1700, #1701.
- Switched CI/CD to tox-dev/workflow’s reusable-tox.yml
driven by an in-tree tox.ini. The build,
metadata-validation and lint (pre-commit,
spellcheck-docs, build-docs) jobs all run through the
reusable workflow; MyPy coverage uploads to Coveralls from a
post-tox-job hook
– by @bdraco.

Related issues and pull requests on GitHub: #1711.
- Switched the CI test job from actions/setup-python to
astral-sh/setup-uv with uv pip install. Pre-release
interpreters skip the wheel cache so each run resolves freshly
against the current snapshot
– by @bdraco.

Related issues and pull requests on GitHub: #1715.
- Switched the Aiohttp workflow that runs the aiohttp test
suite against the in-tree yarl checkout from
actions/setup-python to astral-sh/setup-uv with uv pip install
– by @bdraco.

Related issues and pull requests on GitHub: #1716.
- Switched the Aiohttp workflow’s make .develop step to
install aiohttp’s dev env through uv pip by passing
PIP="uv pip"
– by @bdraco.

Related issues and pull requests on GitHub: #1717.

---

## 1.23.0

(2025-12-16)

### Features

- Added support for pydantic, the ~yarl.URL could be used as a
field type in pydantic models seamlessly.

Related issues and pull requests on GitHub: #1607.

### Packaging updates and notes for downstreams

- The CI has been set up to notify Codecov about upload completion
– by @webknjaz.

With this, Codecov no longer needs to guess whether it received all
the intended coverage reports or not.

Related issues and pull requests on GitHub: #1577.
- The in-tree build backend allows the end-users appending
CFLAGS and LDFLAGS by setting respective environment
variables externally.

It additionally sets up default compiler flags to perform
building with maximum optimization in release mode. This
makes the resulting artifacts shipped to PyPI smaller.

When line tracing is requested, the compiler and linker
flags are configured to include as much information as
possible for debugging and coverage tracking. The
development builds are therefore smaller.

– by @webknjaz

Related issues and pull requests on GitHub: #1586.
- The PEP 517 build backend now supports a new config
setting for controlling whether to build the project in-tree
or in a temporary directory. It only affects wheels and is
set up to build in a temporary directory by default. It does
not affect editable wheel builds — they will keep being
built in-tree regardless.

– by @webknjaz

Here’s an example of using this setting:

```
$ python -m build \
    --config-setting=build-inplace=true
```

Related issues and pull requests on GitHub: #1590.
- Starting this version, when building the wheels is happening
in an automatically created temporary directory, the build
backend makes an effort to normalize the respective file
system path to a deterministic source checkout directory.

– by @webknjaz

It does so by injecting the -ffile-prefix-map compiler
option into the CFLAGS environment variable as suggested
by known reproducible build practices.

The effect is that downstreams will get more reproducible
build results.

Related issues and pull requests on GitHub: #1591.
- Dropped Python 3.9 support; Python 3.10 is the minimal supported Python version
– by @bdraco.

Related issues and pull requests on GitHub: #1609.

### Contributor-facing changes

- The deprecated license classifier was removed from setup.cfg
– by @yegorich.

Related issues and pull requests on GitHub: #1550.
- The in-tree build backend allows the end-users appending
CFLAGS and LDFLAGS by setting respective environment
variables externally.

It additionally sets up default compiler flags to perform
building with maximum optimization in release mode. This
makes the resulting artifacts shipped to PyPI smaller.

When line tracing is requested, the compiler and linker
flags are configured to include as much information as
possible for debugging and coverage tracking. The
development builds are therefore smaller.

– by @webknjaz

Related issues and pull requests on GitHub: #1586.
- The CI has been updated to consistently benchmark optimized
release builds – by @webknjaz.

When the release workflow is triggered, the pre-built wheels
ready to hit PyPI are being tested. Otherwise, the job
builds the project from source, while the rest of the
workflow uses debug builds for line tracing and coverage
collection.

Related issues and pull requests on GitHub: #1587.

---

## 1.22.0

(2025-10-05)

### Features

- Added arm64 Windows wheel builds
– by @finnagin.

Related issues and pull requests on GitHub: #1516.

---

## 1.21.0

(2025-10-05)

### Contributor-facing changes

- The reusable-cibuildwheel.yml workflow has been refactored to
be more generic and ci-cd.yml now holds all the configuration
toggles – by @webknjaz.

Related issues and pull requests on GitHub: #1535.
- When building wheels, the source distribution is now passed directly
to the cibuildwheel invocation – by @webknjaz.

Related issues and pull requests on GitHub: #1536.
- Added CI for Python 3.14 – by @kumaraditya303.

Related issues and pull requests on GitHub: #1560.

---

## 1.20.1

(2025-06-09)

### Bug fixes

- Started raising a ValueError exception raised for corrupted
IPv6 URL values.

These fixes the issue where exception IndexError was
leaking from the internal code because of not being handled and
transformed into a user-facing error. The problem was happening
under the following conditions: empty IPv6 URL, brackets in
reverse order.

– by @MaelPic.

Related issues and pull requests on GitHub: #1512.

### Packaging updates and notes for downstreams

- Updated to use Cython 3.1 universally across the build path – by @lysnikolaou.

Related issues and pull requests on GitHub: #1514.
- Made Cython line tracing opt-in via the with-cython-tracing build config setting – by @bdraco.

Previously, line tracing was enabled by default in pyproject.toml, which caused build issues for some users and made wheels nearly twice as slow.
Now line tracing is only enabled when explicitly requested via pip install . --config-setting=with-cython-tracing=true or by setting the YARL_CYTHON_TRACING environment variable.

Related issues and pull requests on GitHub: #1521.

---

## 1.20.0

(2025-04-16)

### Features

- Implemented support for the free-threaded build of CPython 3.13 – by @lysnikolaou.

Related issues and pull requests on GitHub: #1456.

### Packaging updates and notes for downstreams

- Started building wheels for the free-threaded build of CPython 3.13 – by @lysnikolaou.

Related issues and pull requests on GitHub: #1456.

---

## 1.19.0

(2025-04-05)

### Bug fixes

- Fixed entire name being re-encoded when using yarl.URL.with_suffix() – by @NTFSvolume.

Related issues and pull requests on GitHub: #1468.

### Features

- Started building armv7l wheels for manylinux – by @bdraco.

Related issues and pull requests on GitHub: #1495.

### Contributor-facing changes

- GitHub Actions CI/CD is now configured to manage caching pip-ecosystem
dependencies using re-actors/cache-python-deps – an action by
@webknjaz that takes into account ABI stability and the exact
version of Python runtime.

Related issues and pull requests on GitHub: #1471.
- Increased minimum propcache version to 0.2.1 to fix failing tests – by @bdraco.

Related issues and pull requests on GitHub: #1479.
- Added all hidden folders to pytest’s norecursedirs to prevent it
from trying to collect tests there – by @lysnikolaou.

Related issues and pull requests on GitHub: #1480.

### Miscellaneous internal changes

- Improved accuracy of type annotations – by @Dreamsorcerer.

Related issues and pull requests on GitHub: #1484.
- Improved performance of parsing query strings – by @bdraco.

Related issues and pull requests on GitHub: #1493, #1497.
- Improved performance of the C unquoter – by @bdraco.

Related issues and pull requests on GitHub: #1496, #1498.

---

## 1.18.3

(2024-12-01)

### Bug fixes

- Fixed uppercase ASCII hosts being rejected by URL.build()() and yarl.URL.with_host() – by @bdraco.

Related issues and pull requests on GitHub: #954, #1442.

### Miscellaneous internal changes

- Improved performances of multiple path properties on cache miss – by @bdraco.

Related issues and pull requests on GitHub: #1443.

---

## 1.18.2

(2024-11-29)

No significant changes.

---

## 1.18.1

(2024-11-29)

### Miscellaneous internal changes

- Improved cache performance when ~yarl.URL objects are constructed from yarl.URL.build() with encoded=True – by @bdraco.

Related issues and pull requests on GitHub: #1432.
- Improved cache performance for operations that produce a new ~yarl.URL object – by @bdraco.

Related issues and pull requests on GitHub: #1434, #1436.

---

## 1.18.0

(2024-11-21)

### Features

- Added keep_query and keep_fragment flags in the yarl.URL.with_path(), yarl.URL.with_name() and yarl.URL.with_suffix() methods, allowing users to optionally retain the query string and fragment in the resulting URL when replacing the path – by @paul-nameless.

Related issues and pull requests on GitHub: #111, #1421.

### Contributor-facing changes

- Started running downstream aiohttp tests in CI – by @Cycloctane.

Related issues and pull requests on GitHub: #1415.

### Miscellaneous internal changes

- Improved performance of converting ~yarl.URL to a string – by @bdraco.

Related issues and pull requests on GitHub: #1422.

---

## 1.17.2

(2024-11-17)

### Bug fixes

- Stopped implicitly allowing the use of Cython pre-release versions when
building the distribution package – by @ajsanchezsanz and
@markgreene74.

Related issues and pull requests on GitHub: #1411, #1412.
- Fixed a bug causing ~yarl.URL.port to return the default port when the given port was zero
– by @gmacon.

Related issues and pull requests on GitHub: #1413.

### Features

- Make error messages include details of incorrect type when port is not int in yarl.URL.build().
– by @Cycloctane.

Related issues and pull requests on GitHub: #1414.

### Packaging updates and notes for downstreams

- Stopped implicitly allowing the use of Cython pre-release versions when
building the distribution package – by @ajsanchezsanz and
@markgreene74.

Related issues and pull requests on GitHub: #1411, #1412.

### Miscellaneous internal changes

- Improved performance of the yarl.URL.joinpath() method – by @bdraco.

Related issues and pull requests on GitHub: #1418.

---

## 1.17.1

(2024-10-30)

### Miscellaneous internal changes

- Improved performance of many ~yarl.URL methods – by @bdraco.

Related issues and pull requests on GitHub: #1396, #1397, #1398.
- Improved performance of passing a dict or str to yarl.URL.extend_query() – by @bdraco.

Related issues and pull requests on GitHub: #1401.

---

## 1.17.0

(2024-10-28)

### Features

- Added ~yarl.URL.host_port_subcomponent which returns the 3986#section-3.2.2 host and 3986#section-3.2.3 port subcomponent – by @bdraco.

Related issues and pull requests on GitHub: #1375.

---

## 1.16.0

(2024-10-21)

### Bug fixes

- Fixed blocking I/O to load Python code when creating a new ~yarl.URL with non-ascii characters in the network location part – by @bdraco.

Related issues and pull requests on GitHub: #1342.

### Removals and backward incompatible breaking changes

- Migrated to using a single cache for encoding hosts – by @bdraco.

Passing ip_address_size and host_validate_size to yarl.cache_configure() is deprecated in favor of the new encode_host_size parameter and will be removed in a future release. For backwards compatibility, the old parameters affect the encode_host cache size.

Related issues and pull requests on GitHub: #1348, #1357, #1363.

### Miscellaneous internal changes

- Improved performance of constructing ~yarl.URL – by @bdraco.

Related issues and pull requests on GitHub: #1336.
- Improved performance of calling yarl.URL.build() and constructing unencoded ~yarl.URL – by @bdraco.

Related issues and pull requests on GitHub: #1345.
- Reworked the internal encoding cache to improve performance on cache hit – by @bdraco.

Related issues and pull requests on GitHub: #1369.

---

## 1.15.5

(2024-10-18)

### Miscellaneous internal changes

- Improved performance of the yarl.URL.joinpath() method – by @bdraco.

Related issues and pull requests on GitHub: #1304.
- Improved performance of the yarl.URL.extend_query() method – by @bdraco.

Related issues and pull requests on GitHub: #1305.
- Improved performance of the yarl.URL.origin() method – by @bdraco.

Related issues and pull requests on GitHub: #1306.
- Improved performance of the yarl.URL.with_path() method – by @bdraco.

Related issues and pull requests on GitHub: #1307.
- Improved performance of the yarl.URL.with_query() method – by @bdraco.

Related issues and pull requests on GitHub: #1308, #1328.
- Improved performance of the yarl.URL.update_query() method – by @bdraco.

Related issues and pull requests on GitHub: #1309, #1327.
- Improved performance of the yarl.URL.join() method – by @bdraco.

Related issues and pull requests on GitHub: #1313.
- Improved performance of ~yarl.URL equality checks – by @bdraco.

Related issues and pull requests on GitHub: #1315.
- Improved performance of ~yarl.URL methods that modify the network location – by @bdraco.

Related issues and pull requests on GitHub: #1316.
- Improved performance of the yarl.URL.with_fragment() method – by @bdraco.

Related issues and pull requests on GitHub: #1317.
- Improved performance of calculating the hash of ~yarl.URL objects – by @bdraco.

Related issues and pull requests on GitHub: #1318.
- Improved performance of the yarl.URL.relative() method – by @bdraco.

Related issues and pull requests on GitHub: #1319.
- Improved performance of the yarl.URL.with_name() method – by @bdraco.

Related issues and pull requests on GitHub: #1320.
- Improved performance of ~yarl.URL.parent – by @bdraco.

Related issues and pull requests on GitHub: #1321.
- Improved performance of the yarl.URL.with_scheme() method – by @bdraco.

Related issues and pull requests on GitHub: #1322.

---

## 1.15.4

(2024-10-16)

### Miscellaneous internal changes

- Improved performance of the quoter when all characters are safe – by @bdraco.

Related issues and pull requests on GitHub: #1288.
- Improved performance of unquoting strings – by @bdraco.

Related issues and pull requests on GitHub: #1292, #1293.
- Improved performance of calling yarl.URL.build() – by @bdraco.

Related issues and pull requests on GitHub: #1297.

---

## 1.15.3

(2024-10-15)

### Bug fixes

- Fixed yarl.URL.build() failing to validate paths must start with a / when passing authority – by @bdraco.

The validation only worked correctly when passing host.

Related issues and pull requests on GitHub: #1265.

### Removals and backward incompatible breaking changes

- Removed support for Python 3.8 as it has reached end of life – by @bdraco.

Related issues and pull requests on GitHub: #1203.

### Miscellaneous internal changes

- Improved performance of constructing ~yarl.URL when the net location is only the host – by @bdraco.

Related issues and pull requests on GitHub: #1271.

---

## 1.15.2

(2024-10-13)

### Miscellaneous internal changes

- Improved performance of converting ~yarl.URL to a string – by @bdraco.

Related issues and pull requests on GitHub: #1234.
- Improved performance of yarl.URL.joinpath() – by @bdraco.

Related issues and pull requests on GitHub: #1248, #1250.
- Improved performance of constructing query strings from ~multidict.MultiDict – by @bdraco.

Related issues and pull requests on GitHub: #1256.
- Improved performance of constructing query strings with int values – by @bdraco.

Related issues and pull requests on GitHub: #1259.

---

## 1.15.1

(2024-10-12)

### Miscellaneous internal changes

- Improved performance of calling yarl.URL.build() – by @bdraco.

Related issues and pull requests on GitHub: #1222.
- Improved performance of all ~yarl.URL methods that create new ~yarl.URL objects – by @bdraco.

Related issues and pull requests on GitHub: #1226.
- Improved performance of ~yarl.URL methods that modify the network location – by @bdraco.

Related issues and pull requests on GitHub: #1229.

---

## 1.15.0

(2024-10-11)

### Bug fixes

- Fixed validation with yarl.URL.with_scheme() when passed scheme is not lowercase – by @bdraco.

Related issues and pull requests on GitHub: #1189.

### Features

- Started building armv7l wheels – by @bdraco.

Related issues and pull requests on GitHub: #1204.

### Miscellaneous internal changes

- Improved performance of constructing unencoded ~yarl.URL objects – by @bdraco.

Related issues and pull requests on GitHub: #1188.
- Added a cache for parsing hosts to reduce overhead of encoding ~yarl.URL – by @bdraco.

Related issues and pull requests on GitHub: #1190.
- Improved performance of constructing query strings from ~collections.abc.Mapping – by @bdraco.

Related issues and pull requests on GitHub: #1193.
- Improved performance of converting ~yarl.URL objects to strings – by @bdraco.

Related issues and pull requests on GitHub: #1198.

---

## 1.14.0

(2024-10-08)

### Packaging updates and notes for downstreams

- Switched to using the propcache package for property caching
– by @bdraco.

The propcache package is derived from the property caching
code in yarl and has been broken out to avoid maintaining it for multiple
projects.

Related issues and pull requests on GitHub: #1169.

### Contributor-facing changes

- Started testing with Hypothesis – by @webknjaz and @bdraco.

Special thanks to @Zac-HD for helping us get started with this framework.

Related issues and pull requests on GitHub: #860.

### Miscellaneous internal changes

- Improved performance of yarl.URL.is_default_port() when no explicit port is set – by @bdraco.

Related issues and pull requests on GitHub: #1168.
- Improved performance of converting ~yarl.URL to a string when no explicit port is set – by @bdraco.

Related issues and pull requests on GitHub: #1170.
- Improved performance of the yarl.URL.origin() method – by @bdraco.

Related issues and pull requests on GitHub: #1175.
- Improved performance of encoding hosts – by @bdraco.

Related issues and pull requests on GitHub: #1176.

---

## 1.13.1

(2024-09-27)

### Miscellaneous internal changes

- Improved performance of calling yarl.URL.build() with authority – by @bdraco.

Related issues and pull requests on GitHub: #1163.

---

## 1.13.0

(2024-09-26)

### Bug fixes

- Started rejecting ASCII hostnames with invalid characters. For host strings that
look like authority strings, the exception message includes advice on what to do
instead – by @mjpieters.

Related issues and pull requests on GitHub: #880, #954.
- Fixed IPv6 addresses missing brackets when the ~yarl.URL was converted to a string – by @bdraco.

Related issues and pull requests on GitHub: #1157, #1158.

### Features

- Added ~yarl.URL.host_subcomponent which returns the 3986#section-3.2.2 host subcomponent – by @bdraco.

The only current practical difference between ~yarl.URL.raw_host and ~yarl.URL.host_subcomponent is that IPv6 addresses are returned bracketed.

Related issues and pull requests on GitHub: #1159.

---

## 1.12.1

(2024-09-23)

No significant changes.

---

## 1.12.0

(2024-09-23)

### Features

- Added ~yarl.URL.path_safe to be able to fetch the path without %2F and %25 decoded – by @bdraco.

Related issues and pull requests on GitHub: #1150.

### Removals and backward incompatible breaking changes

- Restore decoding %2F (/) in URL.path – by @bdraco.

This change restored the behavior before #1057.

Related issues and pull requests on GitHub: #1151.

### Miscellaneous internal changes

- Improved performance of processing paths – by @bdraco.

Related issues and pull requests on GitHub: #1143.

---

## 1.11.1

(2024-09-09)

### Bug fixes

- Allowed scheme replacement for relative URLs if the scheme does not require a host – by @bdraco.

Related issues and pull requests on GitHub: #280, #1138.
- Allowed empty host for URL schemes other than the special schemes listed in the WHATWG URL spec – by @bdraco.

Related issues and pull requests on GitHub: #1136.

### Features

- Loosened restriction on integers as query string values to allow classes that implement __int__ – by @bdraco.

Related issues and pull requests on GitHub: #1139.

### Miscellaneous internal changes

- Improved performance of normalizing paths – by @bdraco.

Related issues and pull requests on GitHub: #1137.

---

## 1.11.0

(2024-09-08)

### Features

- Added URL.extend_query()() method, which can be used to extend parameters without replacing same named keys – by @bdraco.

This method was primarily added to replace the inefficient hand rolled method currently used in aiohttp.

Related issues and pull requests on GitHub: #1128.

### Miscellaneous internal changes

- Improved performance of the Cython cached_property implementation – by @bdraco.

Related issues and pull requests on GitHub: #1122.
- Simplified computing ports by removing unnecessary code – by @bdraco.

Related issues and pull requests on GitHub: #1123.
- Improved performance of encoding non IPv6 hosts – by @bdraco.

Related issues and pull requests on GitHub: #1125.
- Improved performance of URL.build()() when the path, query string, or fragment is an empty string – by @bdraco.

Related issues and pull requests on GitHub: #1126.
- Improved performance of the URL.update_query()() method – by @bdraco.

Related issues and pull requests on GitHub: #1130.
- Improved performance of processing query string changes when arguments are str – by @bdraco.

Related issues and pull requests on GitHub: #1131.

---

## 1.10.0

(2024-09-06)

### Bug fixes

- Fixed joining a path when the existing path was empty – by @bdraco.

A regression in URL.join()() was introduced in #1082.

Related issues and pull requests on GitHub: #1118.

### Features

- Added URL.without_query_params()() method, to drop some parameters from query string – by @hongquan.

Related issues and pull requests on GitHub: #774, #898, #1010.
- The previously protected types _SimpleQuery, _QueryVariable, and _Query are now available for use externally as SimpleQuery, QueryVariable, and Query – by @bdraco.

Related issues and pull requests on GitHub: #1050, #1113.

### Contributor-facing changes

- Replaced all ~typing.Optional with ~typing.Union – by @bdraco.

Related issues and pull requests on GitHub: #1095.

### Miscellaneous internal changes

- Significantly improved performance of parsing the network location – by @bdraco.

Related issues and pull requests on GitHub: #1112.
- Added internal types to the cache to prevent future refactoring errors – by @bdraco.

Related issues and pull requests on GitHub: #1117.

---

## 1.9.11

(2024-09-04)

### Bug fixes

- Fixed a TypeError with MultiDictProxy and Python 3.8 – by @bdraco.

Related issues and pull requests on GitHub: #1084, #1105, #1107.

### Miscellaneous internal changes

- Improved performance of encoding hosts – by @bdraco.

Previously, the library would unconditionally try to parse a host as an IP Address. The library now avoids trying to parse a host as an IP Address if the string is not in one of the formats described in 3986#section-3.2.2.

Related issues and pull requests on GitHub: #1104.

---

## 1.9.10

(2024-09-04)

### Bug fixes

- URL.join()() has been changed to match
3986 and align with
/ operation() and URL.joinpath()()
when joining URLs with empty segments.
Previously urllib.parse.urljoin was used,
which has known issues with empty segments
(python/cpython#84774).

Due to the semantics of URL.join()(), joining an
URL with scheme requires making it relative, prefixing with ./.

```
>>> URL("https://web.archive.org/web/").join(URL("./https://github.com/aio-libs/yarl"))
URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')
```

Empty segments are honored in the base as well as the joined part.

```
>>> URL("https://web.archive.org/web/https://").join(URL("github.com/aio-libs/yarl"))
URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')
```

– by @commonism

This change initially appeared in 1.9.5 but was reverted in 1.9.6 to resolve a problem with query string handling.

Related issues and pull requests on GitHub: #1039, #1082.

### Features

- Added ~yarl.URL.absolute which is now preferred over URL.is_absolute() – by @bdraco.

Related issues and pull requests on GitHub: #1100.

---

## 1.9.9

(2024-09-04)

### Bug fixes

- Added missing type on ~yarl.URL.port – by @bdraco.

Related issues and pull requests on GitHub: #1097.

---

## 1.9.8

(2024-09-03)

### Features

- Covered the ~yarl.URL object with types – by @bdraco.

Related issues and pull requests on GitHub: #1084.
- Cache parsing of IP Addresses when encoding hosts – by @bdraco.

Related issues and pull requests on GitHub: #1086.

### Contributor-facing changes

- Covered the ~yarl.URL object with types – by @bdraco.

Related issues and pull requests on GitHub: #1084.

### Miscellaneous internal changes

- Improved performance of handling ports – by @bdraco.

Related issues and pull requests on GitHub: #1081.

---

## 1.9.7

(2024-09-01)

### Removals and backward incompatible breaking changes

- Removed support 3986#section-3.2.3 port normalization when the scheme is not one of http, https, wss, or ws – by @bdraco.

Support for port normalization was recently added in #1033 and contained code that would do blocking I/O if the scheme was not one of the four listed above. The code has been removed because this library is intended to be safe for usage with asyncio.

Related issues and pull requests on GitHub: #1076.

### Miscellaneous internal changes

- Improved performance of property caching – by @bdraco.

The reify implementation from aiohttp was adapted to replace the internal cached_property implementation.

Related issues and pull requests on GitHub: #1070.

---

## 1.9.6

(2024-08-30)

### Bug fixes

- Reverted 3986 compatible URL.join()() honoring empty segments which was introduced in #1039.

This change introduced a regression handling query string parameters with joined URLs. The change was reverted to maintain compatibility with the previous behavior.

Related issues and pull requests on GitHub: #1067.

---

## 1.9.5

(2024-08-30)

### Bug fixes

- Joining URLs with empty segments has been changed
to match 3986.

Previously empty segments would be removed from path,
breaking use-cases such as

```
URL("https://web.archive.org/web/") / "https://github.com/"
```

Now / operation() and URL.joinpath()()
keep empty segments, but do not introduce new empty segments.
e.g.

```
URL("https://example.org/") / ""
```

does not introduce an empty segment.

– by @commonism and @youtux

Related issues and pull requests on GitHub: #1026.
- The default protocol ports of well-known URI schemes are now taken into account
during the normalization of the URL string representation in accordance with
3986#section-3.2.3.

Specified ports are removed from the str representation of a ~yarl.URL
if the port matches the scheme’s default port – by @commonism.

Related issues and pull requests on GitHub: #1033.
- URL.join()() has been changed to match
3986 and align with
/ operation() and URL.joinpath()()
when joining URLs with empty segments.
Previously urllib.parse.urljoin was used,
which has known issues with empty segments
(python/cpython#84774).

Due to the semantics of URL.join()(), joining an
URL with scheme requires making it relative, prefixing with ./.

```
>>> URL("https://web.archive.org/web/").join(URL("./https://github.com/aio-libs/yarl"))
URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')
```

Empty segments are honored in the base as well as the joined part.

```
>>> URL("https://web.archive.org/web/https://").join(URL("github.com/aio-libs/yarl"))
URL('https://web.archive.org/web/https://github.com/aio-libs/yarl')
```

– by @commonism

Related issues and pull requests on GitHub: #1039.

### Removals and backward incompatible breaking changes

- Stopped decoding %2F (/) in URL.path, as this could lead to code incorrectly treating it as a path separator
– by @Dreamsorcerer.

Related issues and pull requests on GitHub: #1057.
- Dropped support for Python 3.7 – by @Dreamsorcerer.

Related issues and pull requests on GitHub: #1016.

### Improved documentation

- On the Contributing docs page,
a link to the Towncrier philosophy has been fixed.

Related issues and pull requests on GitHub: #981.
- The pre-existing / magic method()
has been documented in the API reference – by @commonism.

Related issues and pull requests on GitHub: #1026.

### Packaging updates and notes for downstreams

- A flaw in the logic for copying the project directory into a
temporary folder that led to infinite recursion when TMPDIR
was set to a project subdirectory path. This was happening in Fedora
and its downstream due to the use of pyproject-rpm-macros. It was
only reproducible with pip wheel and was not affecting the
pyproject-build users.

– by @hroncok and @webknjaz

Related issues and pull requests on GitHub: #992, #1014.
- Support Python 3.13 and publish non-free-threaded wheels

Related issues and pull requests on GitHub: #1054.

### Contributor-facing changes

- The CI/CD setup has been updated to test arm64 wheels
under macOS 14, except for Python 3.7 that is unsupported
in that environment – by @webknjaz.

Related issues and pull requests on GitHub: #1015.
- Removed unused type ignores and casts – by @hauntsaninja.

Related issues and pull requests on GitHub: #1031.

### Miscellaneous internal changes

- port, scheme, and raw_host are now cached_property – by @bdraco.

aiohttp accesses these properties quite often, which cause urllib to build the _hostinfo property every time. port, scheme, and raw_host are now cached properties, which will improve performance.

Related issues and pull requests on GitHub: #1044, #1058.

---

## 1.9.4 (2023-12-06)

### Bug fixes

- Started raising TypeError when a string value is passed into
yarl.URL.build() as the port argument – by @commonism.

Previously the empty string as port would create malformed URLs when rendered as string representations. (#883)

### Packaging updates and notes for downstreams

- The leading -- has been dropped from the PEP 517 in-tree build
backend config setting names. --pure-python is now just pure-python
– by @webknjaz.

The usage now looks as follows:

```
$ python -m build \
    --config-setting=pure-python=true \
    --config-setting=with-cython-tracing=true
```

(#963)

### Contributor-facing changes

- A step-by-step Release Guide guide has
been added, describing how to release yarl – by @webknjaz.

This is primarily targeting maintainers. (#960)
- Coverage collection has been implemented for the Cython modules
– by @webknjaz.

It will also be reported to Codecov from any non-release CI jobs.

To measure coverage in a development environment, yarl can be
installed in editable mode:

```
$ python -Im pip install -e .
```

Editable install produces C-files required for the Cython coverage
plugin to map the measurements back to the PYX-files.

#961
- It is now possible to request line tracing in Cython builds using the
with-cython-tracing PEP 517 config setting
– @webknjaz.

This can be used in CI and development environment to measure coverage
on Cython modules, but is not normally useful to the end-users or
downstream packagers.

Here’s a usage example:

```
$ python -Im pip install . --config-settings=with-cython-tracing=true
```

For editable installs, this setting is on by default. Otherwise, it’s
off unless requested explicitly.

The following produces C-files required for the Cython coverage
plugin to map the measurements back to the PYX-files:

```
$ python -Im pip install -e .
```

Alternatively, the YARL_CYTHON_TRACING=1 environment variable
can be set to do the same as the PEP 517 config setting.

#962

## 1.9.3 (2023-11-20)

### Bug fixes

- Stopped dropping trailing slashes in yarl.URL.joinpath() – by @gmacon. (#862, #866)
- Started accepting string subclasses in yarl.URL.__truediv__() operations (URL / segment) – by @mjpieters. (#871, #884)
- Fixed the human representation of URLs with square brackets in usernames and passwords – by @mjpieters. (#876, #882)
- Updated type hints to include URL.missing_port(), URL.__bytes__()
and the encoding argument to yarl.URL.joinpath()
– by @mjpieters. (#891)

### Packaging updates and notes for downstreams

- Integrated Cython 3 to enable building yarl under Python 3.12 – by @mjpieters. (#829, #881)
- Declared modern setuptools.build_meta as the PEP 517 build
backend in pyproject.toml explicitly – by @webknjaz. (#886)
- Converted most of the packaging setup into a declarative setup.cfg
config – by @webknjaz. (#890)
- The packaging is replaced from an old-fashioned setup.py to an
in-tree PEP 517 build backend – by @webknjaz.

Whenever the end-users or downstream packagers need to build yarl from
source (a Git checkout or an sdist), they may pass a config_settings
flag --pure-python. If this flag is not set, a C-extension will be built
and included into the distribution.

Here is how this can be done with pip:

```
$ python -m pip install . --config-settings=--pure-python=false
```

This will also work with -e | --editable.

The same can be achieved via pypa/build:

```
$ python -m build --config-setting=--pure-python=false
```

Adding -w | --wheel can force pypa/build produce a wheel from source
directly, as opposed to building an sdist and then building from it. (#893)
- Declared Python 3.12 supported officially in the distribution package metadata
– by @edgarrmondragon. (#942)

### Contributor-facing changes

- A regression test for no-host URLs was added per #821
and 3986 – by @kenballus. (#821, #822)
- Started testing yarl against Python 3.12 in CI – by @mjpieters. (#881)
- All Python 3.12 jobs are now marked as required to pass in CI
– by @edgarrmondragon. (#942)
- MyST is now integrated in Sphinx – by @webknjaz.

This allows the contributors to author new documents in Markdown
when they have difficulties with going straight RST. (#953)

## 1.9.2 (2023-04-25)

Bugfixes

- Fix regression with yarl.URL.__truediv__() and absolute URLs with empty paths causing the raw path to lack the leading /.
(#854)

## 1.9.1 (2023-04-21)

Bugfixes

- Marked tests that fail on older Python patch releases (< 3.7.10, < 3.8.8 and < 3.9.2) as expected to fail due to missing a security fix for CVE-2021-23336. (#850)

## 1.9.0 (2023-04-19)

This release was never published to PyPI, due to issues with the build process.

### Features

- Added URL.joinpath(*elements), to create a new URL appending multiple path elements. (#704)
- Made URL.__truediv__()() return NotImplemented if called with an
unsupported type — by @michaeljpeters.
(#832)

### Bugfixes

- Path normalization for absolute URLs no longer raises a ValueError exception
when .. segments would otherwise go beyond the URL path root.
(#536)
- Fixed an issue with update_query() not getting rid of the query when argument is None. (#792)
- Added some input restrictions on with_port() function to prevent invalid boolean inputs or out of valid port inputs; handled incorrect 0 port representation. (#793)
- Made yarl.URL.build() raise a TypeError if the host argument is None — by @paulpapacz. (#808)
- Fixed an issue with update_query() getting rid of the query when the argument
is empty but not None. (#845)

### Misc

- #220

## 1.8.2 (2022-12-03)

This is the first release that started shipping wheels for Python 3.11.

## 1.8.1 (2022-08-01)

Misc

- #694, #699, #700, #701, #702, #703, #739

## 1.8.0 (2022-08-01)

### Features

- Added URL.raw_suffix, URL.suffix, URL.raw_suffixes, URL.suffixes, URL.with_suffix. (#613)

### Improved Documentation

- Fixed broken internal references to yarl.URL.human_repr().
(#665)
- Fixed broken external references to multidict:index docs. (#665)

### Deprecations and Removals

- Dropped Python 3.6 support. (#672)

### Misc

- #646, #699, #701

## 1.7.2 (2021-11-01)

Bugfixes

- Changed call in with_port() to stop reencoding parts of the URL that were already encoded. (#623)

## 1.7.1 (2021-10-07)

Bugfixes

- Fix 1.7.0 build error

## 1.7.0 (2021-10-06)

Features

- Add __bytes__() magic method so that bytes(url) will work and use optimal ASCII encoding.
(#582)
- Started shipping platform-specific arm64 wheels for Apple Silicon. (#622)
- Started shipping platform-specific wheels with the musl tag targeting typical Alpine Linux runtimes. (#622)
- Added support for Python 3.10. (#622)

## 1.6.3 (2020-11-14)

Bugfixes

- No longer loose characters when decoding incorrect percent-sequences (like %e2%82%f8). All non-decodable percent-sequences are now preserved.
#517
- Provide x86 Windows wheels.
#535

---

## 1.6.2 (2020-10-12)

Bugfixes

- Provide generated .c files in TarBall distribution.
#530

## 1.6.1 (2020-10-12)

### Features

- Provide wheels for aarch64, i686, ppc64le, s390x architectures on
Linux as well as x86_64.
#507
- Provide wheels for Python 3.9.
#526

### Bugfixes

- human_repr() now always produces valid representation equivalent to the original URL (if the original URL is valid).
#511
- Fixed requoting a single percent followed by a percent-encoded character in the Cython implementation.
#514
- Fix ValueError when decoding % which is not followed by two hexadecimal digits.
#516
- Fix decoding % followed by a space and hexadecimal digit.
#520
- Fix annotation of with_query()/update_query() methods for key=[val1, val2] case.
#528

### Removal

- Drop Python 3.5 support; Python 3.6 is the minimal supported Python version.

---

## 1.6.0 (2020-09-23)

### Features

- Allow for int and float subclasses in query, while still denying bool.
#492

### Bugfixes

- Do not requote arguments in URL.build(), with_xxx() and in / operator.
#502
- Keep IPv6 brackets in origin().
#504

---

## 1.5.1 (2020-08-01)

### Bugfixes

- Fix including relocated internal yarl._quoting_c C-extension into published PyPI dists.
#485

### Misc

- #484

---

## 1.5.0 (2020-07-26)

### Features

- Convert host to lowercase on URL building.
#386
- Allow using mod operator (%) for updating query string (an alias for update_query() method).
#435
- Allow use of sequences such as list and tuple in the values
of a mapping such as dict to represent that a key has many values:

```
url = URL("http://example.com")
assert url.with_query({"a": [1, 2]}) == URL("http://example.com/?a=1&a=2")
```

#443
- Support URL.build() with scheme and path (creates a relative URL).
#464
- Cache slow IDNA encode/decode calls.
#476
- Add @final / Final type hints
#477
- Support URL authority/raw_authority properties and authority argument of URL.build() method.
#478
- Hide the library implementation details, make the exposed public list very clean.
#483

### Bugfixes

- Fix tests with newer Python (3.7.6, 3.8.1 and 3.9.0+).
#409
- Fix a bug where query component, passed in a form of mapping or sequence, is unquoted in unexpected way.
#426
- Hide Query and QueryVariable type aliases in __init__.pyi, now they are prefixed with underscore.
#431
- Keep IPv6 brackets after updating port/user/password.
#451

---

## 1.4.2 (2019-12-05)

Features

- Workaround for missing str.isascii() in Python 3.6
#389

---

## 1.4.1 (2019-11-29)

- Fix regression, make the library work on Python 3.5 and 3.6 again.

## 1.4.0 (2019-11-29)

- Distinguish an empty password in URL from a password not provided at all (#262)
- Fixed annotations for optional parameters of URL.build (#309)
- Use None as default value of user parameter of URL.build (#309)
- Enforce building C Accelerated modules when installing from source tarball, use
YARL_NO_EXTENSIONS environment variable for falling back to (slower) Pure Python
implementation (#329)
- Drop Python 3.5 support
- Fix quoting of plus in path by pure python version (#339)
- Don’t create a new URL if fragment is unchanged (#292)
- Included in error message the path that produces starting slash forbidden error (#376)
- Skip slow IDNA encoding for ASCII-only strings (#387)

## 1.3.0 (2018-12-11)

- Fix annotations for query parameter (#207)
- An incoming query sequence can have int variables (the same as for
Mapping type) (#208)
- Add URL.explicit_port property (#218)
- Give a friendlier error when port can’t be converted to int (#168)
- bool(URL()) now returns False (#272)

## 1.2.6 (2018-06-14)

- Drop Python 3.4 trove classifier (#205)

## 1.2.5 (2018-05-23)

- Fix annotations for build (#199)

## 1.2.4 (2018-05-08)

- Fix annotations for cached_property (#195)

## 1.2.3 (2018-05-03)

- Accept str subclasses in URL constructor (#190)

## 1.2.2 (2018-05-01)

- Fix build

## 1.2.1 (2018-04-30)

- Pin minimal required Python to 3.5.3 (#189)

## 1.2.0 (2018-04-30)

- Forbid inheritance, replace __init__ with __new__ (#171)
- Support PEP-561 (provide type hinting marker) (#182)

## 1.1.1 (2018-02-17)

- Fix performance regression: don’t encode empty netloc (#170)

## 1.1.0 (2018-01-21)

- Make pure Python quoter consistent with Cython version (#162)

## 1.0.0 (2018-01-15)

- Use fast path if quoted string does not need requoting (#154)
- Speed up quoting/unquoting by _Quoter and _Unquoter classes (#155)
- Drop yarl.quote and yarl.unquote public functions (#155)
- Add custom string writer, reuse static buffer if available (#157)
Code is 50-80 times faster than Pure Python version (was 4-5 times faster)
- Don’t recode IP zone (#144)
- Support encoded=True in yarl.URL.build() (#158)
- Fix updating query with multiple keys (#160)

## 0.18.0 (2018-01-10)

- Fallback to IDNA 2003 if domain name is not IDNA 2008 compatible (#152)

## 0.17.0 (2017-12-30)

- Use IDNA 2008 for domain name processing (#149)

## 0.16.0 (2017-12-07)

- Fix raising TypeError by url.query_string() after
url.with_query({}) (empty mapping) (#141)

## 0.15.0 (2017-11-23)

- Add raw_path_qs attribute (#137)

## 0.14.2 (2017-11-14)

- Restore strict parameter as no-op in quote / unquote

## 0.14.1 (2017-11-13)

- Restore strict parameter as no-op for sake of compatibility with
aiohttp 2.2

## 0.14.0 (2017-11-11)

- Drop strict mode (#123)
- Fix "ValueError: Unallowed PCT %" when there’s a "%" in the URL (#124)

## 0.13.0 (2017-10-01)

- Document encoded parameter (#102)
- Support relative URLs like '?key=value' (#100)
- Unsafe encoding for QS fixed. Encode ; character in value parameter (#104)
- Process passwords without user names (#95)

## 0.12.0 (2017-06-26)

- Properly support paths without leading slash in URL.with_path() (#90)
- Enable type annotation checks

## 0.11.0 (2017-06-26)

- Normalize path (#86)
- Clear query and fragment parts in .with_path() (#85)

## 0.10.3 (2017-06-13)

- Prevent double URL arguments unquoting (#83)

## 0.10.2 (2017-05-05)

- Unexpected hash behavior (#75)

## 0.10.1 (2017-05-03)

- Unexpected compare behavior (#73)
- Do not quote or unquote + if not a query string. (#74)

## 0.10.0 (2017-03-14)

- Added URL.build class method (#58)
- Added path_qs attribute (#42)

## 0.9.8 (2017-02-16)

- Do not quote : in path

## 0.9.7 (2017-02-16)

- Load from pickle without _cache (#56)
- Percent-encoded pluses in path variables become spaces (#59)

## 0.9.6 (2017-02-15)

- Revert backward incompatible change (BaseURL)

## 0.9.5 (2017-02-14)

- Fix BaseURL rich comparison support

## 0.9.4 (2017-02-14)

- Use BaseURL

## 0.9.3 (2017-02-14)

- Added BaseURL

## 0.9.2 (2017-02-08)

- Remove debug print

## 0.9.1 (2017-02-07)

- Do not lose tail chars (#45)

## 0.9.0 (2017-02-07)

- Allow to quote % in non strict mode (#21)
- Incorrect parsing of query parameters with %3B (;) inside (#34)
- Fix core dumps (#41)
- tmpbuf - compiling error (#43)
- Added URL.update_path() method
- Added URL.update_query() method (#47)

## 0.8.1 (2016-12-03)

- Fix broken aiohttp: revert back quote / unquote.

## 0.8.0 (2016-12-03)

- Support more verbose error messages in .with_query() (#24)
- Don’t percent-encode @ and : in path (#32)
- Don’t expose yarl.quote and yarl.unquote, these functions are
part of private API

## 0.7.1 (2016-11-18)

- Accept not only str but all classes inherited from str also (#25)

## 0.7.0 (2016-11-07)

- Accept int as value for .with_query()

## 0.6.0 (2016-11-07)

- Explicitly use UTF8 encoding in setup.py (#20)
- Properly unquote non-UTF8 strings (#19)

## 0.5.3 (2016-11-02)

- Don’t use typing.NamedTuple fields but indexes on URL construction

## 0.5.2 (2016-11-02)

- Inline _encode class method

## 0.5.1 (2016-11-02)

- Make URL construction faster by removing extra classmethod calls

## 0.5.0 (2016-11-02)

- Add Cython optimization for quoting/unquoting
- Provide binary wheels

## 0.4.3 (2016-09-29)

- Fix typing stubs

## 0.4.2 (2016-09-29)

- Expose quote() and unquote() as public API

## 0.4.1 (2016-09-28)

- Support empty values in query ('/path?arg')

## 0.4.0 (2016-09-27)

- Introduce relative() (#16)

## 0.3.2 (2016-09-27)

- Typo fixes #15

## 0.3.1 (2016-09-26)

- Support sequence of pairs as with_query() parameter

## 0.3.0 (2016-09-26)

- Introduce is_default_port()

## 0.2.1 (2016-09-26)

- Raise ValueError for URLs like ‘http://:8080/’

## 0.2.0 (2016-09-18)

- Avoid doubling slashes when joining paths (#13)
- Appending path starting from slash is forbidden (#12)

## 0.1.4 (2016-09-09)

- Add kwargs support for with_query() (#10)

## 0.1.3 (2016-09-07)

- Document with_query(), with_fragment() and origin()
- Allow None for with_query() and with_fragment()

## 0.1.2 (2016-09-07)

- Fix links, tune docs theme.

## 0.1.1 (2016-09-06)

- Update README, old version used obsolete API

## 0.1.0 (2016-09-06)

- The library was deeply refactored, bytes are gone away but all
accepted strings are encoded if needed.

## 0.0.1 (2016-08-30)

- The first release.
