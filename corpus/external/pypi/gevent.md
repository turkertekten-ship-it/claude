## gevent

 [image: https://coveralls.io/repos/gevent/gevent/badge.svg?branch=master&service=github]

gevent is a coroutine -based Python networking library that uses
greenlet to provide a high-level synchronous API on top of the libev
or libuv event loop.

Features include:

- Fast event loop based on libev or libuv.
- Lightweight execution units based on greenlets.
- API that re-uses concepts from the Python standard library (for
examples there are events and
queues).
- Cooperative sockets with SSL support
- Cooperative DNS queries performed through a threadpool,
dnspython, or c-ares.
- Monkey patching utility to get 3rd party modules to become cooperative
- TCP/UDP/HTTP servers
- Subprocess support (through gevent.subprocess)
- Thread pools

gevent is inspired by eventlet but features a more consistent API,
simpler implementation and better performance. Read why others use
gevent and check out the list of the open source projects based on
gevent.

gevent was written by Denis Bilenko.

Since version 1.1, gevent is maintained by Jason Madden for
NextThought (through gevent 21) and
Institutional Shareholder Services
with help from the contributors and is
licensed under the MIT license.

See what’s new in the latest major release.

Check out the detailed changelog for this version.

Read the documentation online at http://www.gevent.org.

Post issues on the bug tracker, discuss and ask open ended
questions on the mailing list, and find announcements and
information on the blog and twitter (@gevent).

## Installation and Requirements

### Supported Platforms

This version of gevent runs on Python 3.9 and up (for exact details
of tested versions, see the classifiers on the PyPI page or in
setup.py). gevent requires the greenlet library and will install the
cffi library by default on Windows. The cffi library will become
the default on all platforms in a future release of gevent.

This version of gevent is also tested on PyPy 3.10 (7.3.12); it
should run on PyPy 3.9 and above. On PyPy, there are no external
dependencies.

gevent is tested on Windows, macOS, and Linux, and should run on most
other Unix-like operating systems (e.g., FreeBSD, Solaris, etc.)

#### Older Versions of Python

Users of older versions of Python 2 or Python 3 may install an older
version of gevent. Note that these versions are generally not
supported.

| Python
Version | Gevent
Version |
| 2.5 | 1.0.x |
| 2.6 | 1.1.x |
| <=
2.7.8 | 1.2.x |
| 3.3 | 1.2.x |
| 3.4.0 -
3.4.2 | 1.3.x |
| 3.4.3 | 1.4.x |
| 3.5.x | 20.9.0 |
| 2.7.9 -
2.7.18,
3.6,
3.7 | 22.10 |
| 3.8 | 24.2.1 |

### Installation

gevent and greenlet can both be installed with pip, e.g., pip install gevent. Installation using buildout is also supported.

On Windows, macOS, and Linux, both gevent and greenlet are
distributed as binary wheels.

#### Installing From Source

If you are unable to use the binary wheels (for platforms where no
pre-built wheels are available or if wheel installation is disabled),
you can build gevent from source. A normal pip install will
fall back to doing this if no binary wheel is available. See
Installing From Source for more, including common installation issues.

### Extra Dependencies

There are a number
of additional libraries that extend gevent’s functionality and will be
used if they are available. All of these may be installed using
setuptools extras,
as named below, e.g., pip install gevent[events].

events

In versions of gevent up to and including 20.5.0, this provided configurable
event support using zope.event and was highly
recommended.

In versions after that, this extra is empty and does nothing. It
will be removed in gevent 21.0.

dnspython

Enables a pure-Python resolver, backed by dnspython. On Python 2, this also
includes idna. They can be
installed with the dnspython extra.

monitor

Enhancements to gevent’s self-monitoring capabilities. This
includes the psutil library,
which is needed to monitor memory usage. (Note that this may not
build on all platforms.)

recommended

A shortcut for installing suggested extras together. This includes
the non-test extras defined here, plus additions that improve
gevent’s operation on certain platforms (for example, in the past,
it has included backports of newer APIs).

test

Everything needed to run the complete gevent test suite.
