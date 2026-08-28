---
date: 2026-03-21T20:11:14+0000
source: https://pypi.org/project/pytest-cov/
---
| docs | [image: Documentation Status] |
| tests | [image: GitHub Actions Status] |
| package | [image: PyPI Package latest release] [image: conda-forge] [image: PyPI Wheel] [image: Supported versions] [image: Supported implementations] [image: Commits since latest release] |

This plugin provides coverage functionality as a pytest plugin. Compared to just using coverage run this plugin does some extras:

- Automatic erasing and combination of .coverage files and default reporting.
- Support for detailed coverage contexts (add --cov-context=test to have the full test name including parametrization as the context).
- Xdist support: you can use all of pytest-xdist’s features including remote interpreters and still get coverage.
- Consistent pytest behavior. If you run coverage run -m pytest you will have slightly different sys.path (CWD will be
in it, unlike when running pytest).

All features offered by the coverage package should work, either through pytest-cov’s command line options or
through coverage’s config file.

- Free software: MIT license

## Installation

Install with pip:

```
pip install pytest-cov
```

For distributed testing support install pytest-xdist:

```
pip install pytest-xdist
```

### Upgrading from pytest-cov 6.3

pytest-cov 6.3 and older were using a .pth file to enable coverage measurements in subprocesses. This was removed in pytest-cov 7 - use coverage’s patch options to enable subprocess measurements.

### Uninstalling

Uninstall with pip:

```
pip uninstall pytest-cov
```

Under certain scenarios a stray .pth file may be left around in site-packages.

- pytest-cov 2.0 may leave a pytest-cov.pth if you installed without wheels
(easy_install, setup.py install etc).
- pytest-cov 1.8 or older will leave a init_cov_core.pth.

## Usage

```
pytest --cov=myproj tests/
```

Would produce a report like:

```
-------------------- coverage: ... ---------------------
Name                 Stmts   Miss  Cover
----------------------------------------
myproj/__init__          2      0   100%
myproj/myproj          257     13    94%
myproj/feature4286      94      7    92%
----------------------------------------
TOTAL                  353     20    94%
```

## Documentation

https://pytest-cov.readthedocs.io/en/latest/

## Coverage Data File

The data file is erased at the beginning of testing to ensure clean data for each test run. If you
need to combine the coverage of several test runs you can use the --cov-append option to append
this coverage data to coverage data from previous test runs.

The data file is left at the end of testing so that it is possible to use normal coverage tools to
examine it.

## Limitations

For distributed testing the workers must have the pytest-cov package installed. This is needed since
the plugin must be registered through setuptools for pytest to start the plugin on the
worker.

## Security

To report a security vulnerability please use the Tidelift security contact.
Tidelift will coordinate the fix and disclosure.

## Acknowledgements

Whilst this plugin has been built fresh from the ground up it has been influenced by the work done
on pytest-coverage (Ross Lawley, James Mills, Holger Krekel) and nose-cover (Jason Pellerin) which are
other coverage plugins.

Ned Batchelder for coverage and its ability to combine the coverage results of parallel runs.

Holger Krekel for pytest with its distributed testing support.

Jason Pellerin for nose.

Michael Foord for unittest2.

No doubt others have contributed to these tools as well.

## Changelog

### 7.1.0 (2026-03-21)

- Fixed total coverage computation to always be consistent, regardless of reporting settings.
Previously some reports could produce different total counts, and consequently can make –cov-fail-under behave different depending on
reporting options.
See #641.
- Improve handling of ResourceWarning from sqlite3.

The plugin adds warning filter for sqlite3 ResourceWarning unclosed database (since 6.2.0).
It checks if there is already existing plugin for this message by comparing filter regular expression.
When filter is specified on command line the message is escaped and does not match an expected message.
A check for an escaped regular expression is added to handle this case.

With this fix one can suppress ResourceWarning from sqlite3 from command line:

```
pytest -W "ignore:unclosed database in <sqlite3.Connection object at:ResourceWarning" ...
``` 
- Various improvements to documentation.
Contributed by Art Pelling in #718 and
“vivodi” in #738.
Also closed #736.
- Fixed some assertions in tests.
Contributed by in Markéta Machová in #722.
- Removed unnecessary coverage configuration copying (meant as a backup because reporting commands had configuration side-effects before coverage 5.0).

### 7.0.0 (2025-09-09)

- Dropped support for subprocesses measurement.

It was a feature added long time ago when coverage lacked a nice way to measure subprocesses created in tests.
It relied on a .pth file, there was no way to opt-out and it created bad interations
with coverage’s new patch system added
in 7.10.

To migrate to this release you might need to enable the suprocess patch, example for .coveragerc:

```
[run]
patch = subprocess
```

This release also requires at least coverage 7.10.6.
- Switched packaging to have metadata completely in pyproject.toml and use hatchling for
building.
Contributed by Ofek Lev in #551
with some extras in #716.
- Removed some not really necessary testing deps like six.

### 6.3.0 (2025-09-06)

- Added support for markdown reports.
Contributed by Marcos Boger in #712
and #714.
- Fixed some formatting issues in docs.
Anonymous contribution in #706.

### 6.2.1 (2025-06-12)

- Added a version requirement for pytest’s pluggy dependency (1.2.0, released 2023-06-21) that has the required new-style hookwrapper API.
- Removed deprecated license classifier (packaging).
- Disabled coverage warnings in two more situations where they have no value:

 - “module-not-measured” in workers
 - “already-imported” in subprocesses

### 6.2.0 (2025-06-11)

- The plugin now adds 3 rules in the filter warnings configuration to prevent common coverage warnings being raised as obscure errors:

```
default:unclosed database in <sqlite3.Connection object at:ResourceWarning
once::PytestCovWarning
once::CoverageWarning
```

This fixes most of the bad interactions that are occurring on pytest 8.4 with filterwarnings=error.

The plugin will check if there already matching rules for the 3 categories
(ResourceWarning, PytestCovWarning, CoverageWarning) and message (unclosed database in <sqlite3.Connection object at) before adding the filters.

This means you can have this in your pytest configuration for complete oblivion (not recommended, if that is not clear):

```
filterwarnings = [
    "error",
    "ignore:unclosed database in <sqlite3.Connection object at:ResourceWarning",
    "ignore::PytestCovWarning",
    "ignore::CoverageWarning",
]
```

### 6.1.1 (2025-04-05)

- Fixed breakage that occurs when --cov-context and the no_cover marker are used together.

### 6.1.0 (2025-04-01)

- Change terminal output to use full width lines for the coverage header.
Contributed by Tsvika Shapira in #678.
- Removed unnecessary CovFailUnderWarning. Fixes #675.
- Fixed the term report not using the precision specified via --cov-precision.

### 6.0.0 (2024-10-29)

- Updated various documentation inaccuracies, especially on subprocess handling.
- Changed fail under checks to use the precision set in the coverage configuration.
Now it will perform the check just like coverage report would.
- Added a --cov-precision cli option that can override the value set in your coverage configuration.
- Dropped support for now EOL Python 3.8.

### 5.0.0 (2024-03-24)

- Removed support for xdist rsync (now deprecated).
Contributed by Matthias Reichenbach in #623.
- Switched docs theme to Furo.
- Various legacy Python cleanup and CI improvements.
Contributed by Christian Clauss and Hugo van Kemenade in
#630,
#631,
#632 and
#633.
- Added a pyproject.toml example in the docs.
Contributed by Dawn James in #626.
- Modernized project’s pre-commit hooks to use ruff. Initial POC contributed by
Christian Clauss in #584.
- Dropped support for Python 3.7.

### 4.1.0 (2023-05-24)

- Updated CI with new Pythons and dependencies.
- Removed rsyncdir support. This makes pytest-cov compatible with xdist 3.0.
Contributed by Sorin Sbarnea in #558.
- Optimized summary generation to not be performed if no reporting is active (for example,
when --cov-report='' is used without --cov-fail-under).
Contributed by Jonathan Stewmon in #589.
- Added support for JSON reporting.
Contributed by Matthew Gamble in #582.
- Refactored code to use f-strings.
Contributed by Mark Mayo in #572.
- Fixed a skip in the test suite for some old xdist.
Contributed by a bunch of people in #565.
- Dropped support for Python 3.6.

### 4.0.0 (2022-09-28)

Note that this release drops support for multiprocessing.

- –cov-fail-under no longer causes pytest –collect-only to fail
Contributed by Zac Hatfield-Dodds in #511.
- Dropped support for multiprocessing (mostly because issue 82408). This feature was
mostly working but very broken in certain scenarios and made the test suite very flaky and slow.

There is builtin multiprocessing support in coverage and you can migrate to that. All you need is this in your
.coveragerc:

```
[run]
concurrency = multiprocessing
parallel = true
sigterm = true
``` 
- Fixed deprecation in setup.py by trying to import setuptools before distutils.
Contributed by Ben Greiner in #545.
- Removed undesirable new lines that were displayed while reporting was disabled.
Contributed by Delgan in #540.
- Documentation fixes.
Contributed by Andre Brisco in #543
and Colin O’Dell in #525.
- Added support for LCOV output format via –cov-report=lcov. Only works with coverage 6.3+.
Contributed by Christian Fetzer in #536.
- Modernized pytest hook implementation.
Contributed by Bruno Oliveira in #549
and Ronny Pfannschmidt in #550.

### 3.0.0 (2021-10-04)

Note that this release drops support for Python 2.7 and Python 3.5.

- Added support for Python 3.10 and updated various test dependencies.
Contributed by Hugo van Kemenade in
#500.
- Switched from Travis CI to GitHub Actions. Contributed by Hugo van Kemenade in
#494 and
#495.
- Add a --cov-reset CLI option.
Contributed by Danilo Šegan in
#459.
- Improved validation of --cov-fail-under CLI option.
Contributed by … Ronny Pfannschmidt’s desire for skark in
#480.
- Dropped Python 2.7 support.
Contributed by Thomas Grainger in
#488.
- Updated trove classifiers. Contributed by Michał Bielawski in
#481.
- Reverted change for toml requirement.
Contributed by Thomas Grainger in
#477.

### 2.12.1 (2021-06-01)

- Changed the toml requirement to be always be directly required (instead of being required through a coverage extra).
This fixes issues with pip-compile (pip-tools#1300).
Contributed by Sorin Sbarnea in #472.
- Documented show_contexts.
Contributed by Brian Rutledge in #473.

### 2.12.0 (2021-05-14)

- Added coverage’s toml extra to install requirements in setup.py.
Contributed by Christian Riedel in #410.
- Fixed pytest_cov.__version__ to have the right value (string with version instead of a string
including __version__ =).
- Fixed license classifier in setup.py.
Contributed by Chris Sreesangkom in #467.
- Fixed commits since badge.
Contributed by Terence Honles in #470.

### 2.11.1 (2021-01-20)

- Fixed support for newer setuptools (v42+).
Contributed by Michał Górny in #451.

### 2.11.0 (2021-01-18)

- Bumped minimum coverage requirement to 5.2.1. This prevents reporting issues.
Contributed by Mateus Berardo de Souza Terra in #433.
- Improved sample projects (from the examples
directory) to support running tox -e pyXY. Now the example configures a suffixed coverage data file,
and that makes the cleanup environment unnecessary.
Contributed by Ganden Schaffner in #435.
- Removed the empty console_scripts entrypoint that confused some Gentoo build script.
I didn’t ask why it was so broken cause I didn’t want to ruin my day.
Contributed by Michał Górny in #434.
- Fixed the missing coverage context
when using subprocesses.
Contributed by Bernát Gábor in #443.
- Updated the config section in the docs.
Contributed by Pamela McA’Nulty in #429.
- Migrated CI to travis-ci.com (from .org).

### 2.10.1 (2020-08-14)

- Support for pytest-xdist 2.0, which breaks compatibility with pytest-xdist before 1.22.3 (from 2017).
Contributed by Zac Hatfield-Dodds in #412.
- Fixed the LocalPath has no attribute startswith failure that occurred when using the pytester plugin
in inline mode.

### 2.10.0 (2020-06-12)

- Improved the --no-cov warning. Now it’s only shown if --no-cov is present before --cov.
- Removed legacy pytest support. Changed setup.py so that pytest>=4.6 is required.

### 2.9.0 (2020-05-22)

- Fixed RemovedInPytest4Warning when using Pytest 3.10.
Contributed by Michael Manganiello in #354.
- Made pytest startup faster when plugin not active by lazy-importing.
Contributed by Anders Hovmöller in #339.
- Various CI improvements.
Contributed by Daniel Hahler in #363 and
#364.
- Various Python support updates (drop EOL 3.4, test against 3.8 final).
Contributed by Hugo van Kemenade in
#336 and
#367.
- Changed --cov-append to always enable data_suffix (a coverage setting).
Contributed by Harm Geerts in
#387.
- Changed --cov-append to handle loading previous data better
(fixes various path aliasing issues).
- Various other testing improvements, github issue templates, example updates.
- Fixed internal failures that are caused by tests that change the current working directory by
ensuring a consistent working directory when coverage is called.
See #306 and
coveragepy#881

### 2.8.1 (2019-10-05)

- Fixed #348 -
regression when only certain reports (html or xml) are used then --cov-fail-under always fails.

### 2.8.0 (2019-10-04)

- Fixed RecursionError that can occur when using
cleanup_on_signal or
cleanup_on_sigterm.
See: #294.
The 2.7.x releases of pytest-cov should be considered broken regarding aforementioned cleanup API.
- Added compatibility with future xdist release that deprecates some internals
(match pytest-xdist master/worker terminology).
Contributed by Thomas Grainger in #321
- Fixed breakage that occurs when multiple reporting options are used.
Contributed by Thomas Grainger in #338.
- Changed internals to use a stub instead of os.devnull.
Contributed by Thomas Grainger in #332.
- Added support for Coverage 5.0.
Contributed by Ned Batchelder in #319.
- Added support for float values in --cov-fail-under.
Contributed by Martín Gaitán in #311.
- Various documentation fixes. Contributed by
Juanjo Bazán,
Andrew Murray and
Albert Tugushev in
#298,
#299 and
#307.
- Various testing improvements. Contributed by
Ned Batchelder,
Daniel Hahler,
Ionel Cristian Mărieș and
Hugo van Kemenade in
#313,
#314,
#315,
#316,
#325,
#326,
#334 and
#335.
- Added the --cov-context CLI options that enables coverage contexts. Only works with coverage 5.0+.
Contributed by Ned Batchelder in #345.

### 2.7.1 (2019-05-03)

- Fixed source distribution manifest so that garbage ain’t included in the tarball.

### 2.7.0 (2019-05-03)

- Fixed AttributeError: 'NoneType' object has no attribute 'configure_node' error when --no-cov is used.
Contributed by Alexander Shadchin in #263.
- Various testing and CI improvements. Contributed by Daniel Hahler in
#255,
#266,
#272,
#271 and
#269.
- Improved pytest_cov.embed.cleanup_on_sigterm to be reentrant (signal deliveries while signal handling is
running won’t break stuff).
- Added pytest_cov.embed.cleanup_on_signal for customized cleanup.
- Improved cleanup code and fixed various issues with leftover data files. All contributed in
#265 or
#262.
- Improved examples. Now there are two examples for the common project layouts, complete with working coverage
configuration. The examples have CI testing. Contributed in
#267.
- Improved help text for CLI options.

### 2.6.1 (2019-01-07)

- Added support for Pytest 4.1. Contributed by Daniel Hahler and Семён Марьясин in
#253 and
#230.
- Various test and docs fixes. Contributed by Daniel Hahler in
#224 and
#223.
- Fixed the “Module already imported” issue (#211).
Contributed by Daniel Hahler in #228.

### 2.6.0 (2018-09-03)

- Dropped support for Python 3 < 3.4, Pytest < 3.5 and Coverage < 4.4.
- Fixed some documentation formatting. Contributed by Jean Jordaan and Julian.
- Added an example with addopts in documentation. Contributed by Samuel Giffard in
#195.
- Fixed TypeError: 'NoneType' object is not iterable in certain xdist configurations. Contributed by Jeremy Bowman in
#213.
- Added a no_cover marker and fixture. Fixes
#78.
- Fixed broken no_cover check when running doctests. Contributed by Terence Honles in
#200.
- Fixed various issues with path normalization in reports (when combining coverage data from parallel mode). Fixes
#130.
Contributed by Ryan Hiebert & Ionel Cristian Mărieș in
#178.
- Report generation failures don’t raise exceptions anymore. A warning will be logged instead. Fixes
#161.
- Fixed multiprocessing issue on Windows (empty env vars are not passed). Fixes
#165.

### 2.5.1 (2017-05-11)

- Fixed xdist breakage (regression in 2.5.0).
Fixes #157.
- Allow setting custom data_file name in .coveragerc.
Fixes #145.
Contributed by Jannis Leidel & Ionel Cristian Mărieș in
#156.

### 2.5.0 (2017-05-09)

- Always show a summary when --cov-fail-under is used. Contributed by Francis Niu in PR#141.
- Added --cov-branch option. Fixes #85.
- Improve exception handling in subprocess setup. Fixes #144.
- Fixed handling when --cov is used multiple times. Fixes #151.

### 2.4.0 (2016-10-10)

- Added a “disarm” option: --no-cov. It will disable coverage measurements. Contributed by Zoltan Kozma in
PR#135.

WARNING: Do not put this in your configuration files, it’s meant to be an one-off for situations where you want to
disable coverage from command line.
- Fixed broken exception handling on .pth file. See #136.

### 2.3.1 (2016-08-07)

- Fixed regression causing spurious errors when xdist was used. See #124.
- Fixed DeprecationWarning about incorrect addoption use. Contributed by Florian Bruhin in PR#127.
- Fixed deprecated use of funcarg fixture API. Contributed by Daniel Hahler in PR#125.

### 2.3.0 (2016-07-05)

- Add support for specifying output location for html, xml, and annotate report.
Contributed by Patrick Lannigan in PR#113.
- Fix bug hiding test failure when cov-fail-under failed.
- For coverage >= 4.0, match the default behaviour of coverage report and
error if coverage fails to find the source instead of just printing a warning.
Contributed by David Szotten in PR#116.
- Fixed bug occurred when bare --cov parameter was used with xdist.
Contributed by Michael Elovskikh in PR#120.
- Add support for skip_covered and added --cov-report=term-skip-covered command
line options. Contributed by Saurabh Kumar in PR#115.

### 2.2.1 (2016-01-30)

- Fixed incorrect merging of coverage data when xdist was used and coverage was >= 4.0.

### 2.2.0 (2015-10-04)

- Added support for changing working directory in tests. Previously changing working
directory would disable coverage measurements in suprocesses.
- Fixed broken handling for --cov-report=annotate.

### 2.1.0 (2015-08-23)

- Added support for coverage 4.0b2.
- Added the --cov-append command line options. Contributed by Christian Ledermann
in PR#80.

### 2.0.0 (2015-07-28)

- Added --cov-fail-under, akin to the new fail_under option in coverage-4.0
(automatically activated if there’s a [report] fail_under = ... in .coveragerc).
- Changed --cov-report=term to automatically upgrade to --cov-report=term-missing
if there’s [run] show_missing = True in .coveragerc.
- Changed --cov so it can be used with no path argument (in which case the source
settings from .coveragerc will be used instead).
- Fixed .pth installation to work in all cases (install, easy_install, wheels, develop etc).
- Fixed .pth uninstallation to work for wheel installs.
- Support for coverage 4.0.
- Data file suffixing changed to use coverage’s data_suffix=True option (instead of the
custom suffixing).
- Avoid warning about missing coverage data (just like coverage.control.process_startup).
- Fixed a race condition when running with xdist (all the workers tried to combine the files).
It’s possible that this issue is not present in pytest-cov 1.8.X.

### 1.8.2 (2014-11-06)

- N/A
