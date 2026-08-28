## dateutil - powerful extensions to datetime

[image: pypi version] [image: supported Python version] [image: licence]

[image: Join the chat at https://gitter.im/dateutil/dateutil] [image: Read the documentation at https://dateutil.readthedocs.io/en/latest/]

[image: travis build status] [image: appveyor build status] [image: azure pipelines build status] [image: Code coverage]

The dateutil module provides powerful extensions to
the standard datetime module, available in Python.

## Installation

dateutil can be installed from PyPI using pip (note that the package name is
different from the importable name):

```
pip install python-dateutil
```

## Download

dateutil is available on PyPI
https://pypi.org/project/python-dateutil/

The documentation is hosted at:
https://dateutil.readthedocs.io/en/stable/

## Code

The code and issue tracker are hosted on GitHub:
https://github.com/dateutil/dateutil/

## Features

- Computing of relative deltas (next month, next year,
next Monday, last week of month, etc);
- Computing of relative deltas between two given
date and/or datetime objects;
- Computing of dates based on very flexible recurrence rules,
using a superset of the iCalendar
specification. Parsing of RFC strings is supported as well.
- Generic parsing of dates in almost any string format;
- Timezone (tzinfo) implementations for tzfile(5) format
files (/etc/localtime, /usr/share/zoneinfo, etc), TZ
environment string (in all known formats), iCalendar
format files, given ranges (with help from relative deltas),
local machine timezone, fixed offset timezone, UTC timezone,
and Windows registry-based time zones.
- Internal up-to-date world timezone information based on
Olson’s database.
- Computing of Easter Sunday dates for any given year,
using Western, Orthodox or Julian algorithms;
- A comprehensive test suite.

## Quick example

Here’s a snapshot, just to give an idea about the power of the
package. For more examples, look at the documentation.

Suppose you want to know how much time is left, in
years/months/days/etc, before the next easter happening on a
year with a Friday 13th in August, and you want to get today’s
date out of the “date” unix system command. Here is the code:

```
>>> from dateutil.relativedelta import *
>>> from dateutil.easter import *
>>> from dateutil.rrule import *
>>> from dateutil.parser import *
>>> from datetime import *
>>> now = parse("Sat Oct 11 17:13:46 UTC 2003")
>>> today = now.date()
>>> year = rrule(YEARLY,dtstart=now,bymonth=8,bymonthday=13,byweekday=FR)[0].year
>>> rdelta = relativedelta(easter(year), today)
>>> print("Today is: %s" % today)
Today is: 2003-10-11
>>> print("Year with next Aug 13th on a Friday is: %s" % year)
Year with next Aug 13th on a Friday is: 2004
>>> print("How far is the Easter of that year: %s" % rdelta)
How far is the Easter of that year: relativedelta(months=+6)
>>> print("And the Easter of that year is: %s" % (today+rdelta))
And the Easter of that year is: 2004-04-11
```

Being exactly 6 months ahead was really a coincidence :)

## Contributing

We welcome many types of contributions - bug reports, pull requests (code, infrastructure or documentation fixes). For more information about how to contribute to the project, see the CONTRIBUTING.md file in the repository.

## Author

The dateutil module was written by Gustavo Niemeyer <gustavo@niemeyer.net>
in 2003.

It is maintained by:

- Gustavo Niemeyer <gustavo@niemeyer.net> 2003-2011
- Tomi Pieviläinen <tomi.pievilainen@iki.fi> 2012-2014
- Yaron de Leeuw <me@jarondl.net> 2014-2016
- Paul Ganssle <paul@ganssle.io> 2015-

Starting with version 2.4.1 and running until 2.8.2, all source and binary
distributions will be signed by a PGP key that has, at the very least, been
signed by the key which made the previous release. A table of release signing
keys can be found below:

| Releases | Signing key fingerprint |
| 2.4.1-2.8.2 | 6B49 ACBA DCF6 BD1C A206 67AB CD54 FCE3 D964 BEFB |

New releases may have signed tags, but binary and source distributions
uploaded to PyPI will no longer have GPG signatures attached.

## Contact

Our mailing list is available at dateutil@python.org. As it is hosted by the PSF, it is subject to the PSF code of
conduct.

## License

All contributions after December 1, 2017 released under dual license - either Apache 2.0 License or the BSD 3-Clause License. Contributions before December 1, 2017 - except those those explicitly relicensed - are released only under the BSD 3-Clause License.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

python-dateutil-2.9.0.post0.tar.gz
 (342.4 kB
 view details)

Uploaded
 Mar 1, 2024
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

python_dateutil-2.9.0.post0-py2.py3-none-any.whl
 (229.9 kB
 view details)

Uploaded
 Mar 1, 2024
 Python 2Python 3

## File details

Details for the file python-dateutil-2.9.0.post0.tar.gz.

### File metadata

- Download URL: python-dateutil-2.9.0.post0.tar.gz
- Upload date:
 Mar 1, 2024
- Size: 342.4 kB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/5.0.0 CPython/3.9.18

### File hashes

Hashes for python-dateutil-2.9.0.post0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 37dd54208da7e1cd875388217d5e00ebd4179249f90fb72437e91a35459a0ad3 | |
| MD5 | 81cb6aad924ef40ebfd3d62eaebe47c6 | |
| BLAKE2b-256 | 66c00c8b6ad9f17a802ee498c46e004a0eb49bc148f2fd230864601a86dcf6db | |

See more details on using hashes here.

## File details

Details for the file python_dateutil-2.9.0.post0-py2.py3-none-any.whl.

### File metadata

- Download URL: python_dateutil-2.9.0.post0-py2.py3-none-any.whl
- Upload date:
 Mar 1, 2024
- Size: 229.9 kB
- Tags: Python 2, Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/5.0.0 CPython/3.9.18

### File hashes

Hashes for python_dateutil-2.9.0.post0-py2.py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | a8b2bc7bffae282281c8140a97d3aa9c14da0b136dfe83f850eea9a5f7470427 | |
| MD5 | 2178749b926fe0e2c25905cdfebe3361 | |
| BLAKE2b-256 | ec5756b9bcc3c9c6a792fcbaf139543cee77261f3651ca9da0c93f5c1221264b | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

This release

2.9.0.post0 This release

Mar 1, 2024
 2 files

2.9.0

Mar 1, 2024
 2 files

2.8.2

Jul 14, 2021
 2 files

2.8.1

Nov 3, 2019
 2 files

2.8.0

Feb 5, 2019
 2 files

2.7.5

Oct 27, 2018
 2 files

2.7.4

Oct 25, 2018
 2 files

2.7.3

May 10, 2018
 2 files

2.7.2

Mar 26, 2018
 2 files

2.7.1

Mar 24, 2018
 2 files

2.7.0

Mar 11, 2018
 2 files

2.6.1

Jul 10, 2017
 2 files

2.6.0

Nov 8, 2016
 3 files

2.5.3

Apr 21, 2016
 3 files

2.5.2

Mar 27, 2016
 3 files

2.5.1

Mar 17, 2016
 3 files

2.5.0

Feb 28, 2016
 3 files

2.4.2

Mar 31, 2015
 2 files

2.4.1

Mar 5, 2015
 4 files

2.4.0

Jan 5, 2015
 2 files

2.3

Dec 1, 2014
 2 files

2.2

Nov 1, 2013
 1 file

2.1

Mar 28, 2012
 1 file

2.0

Dec 1, 2011

1.5

Mar 29, 2010
 1 file

1.4.1

Aug 6, 2008
 1 file

1.4

Feb 28, 2008
 1 file

1.2

Jun 26, 2007

1.1

Dec 22, 2005

1.0

Jul 19, 2005

0.5

Jul 16, 2004

0.4

Mar 19, 2004

0.3

Oct 11, 2003

0.1

Oct 9, 2003