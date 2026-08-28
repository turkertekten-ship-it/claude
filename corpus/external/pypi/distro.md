---
date: 2023-12-24T09:54:30+0000
source: https://pypi.org/project/distro/
---
# Distro - an OS platform information API

[image: CI Status] [image: PyPI version] [image: Supported Python Versions] [image: Code Coverage] [image: Is Wheel] [image: Latest Github Release]

distro provides information about the
OS distribution it runs on, such as a reliable machine-readable ID, or
version information.

It is the recommended replacement for Python's original
platform.linux_distribution
function (removed in Python 3.8). It also provides much more functionality
which isn't necessarily Python bound, like a command-line interface.

Distro currently supports Linux and BSD based systems but Windows and OS X support is also planned.

For Python 2.6 support, see https://github.com/python-distro/distro/tree/python2.6-support

## Installation

Installation of the latest released version from PyPI:

```
pip install distro
```

Installation of the latest development version:

```
pip install https://github.com/python-distro/distro/archive/master.tar.gz
```

To use as a standalone script, download distro.py directly:

```
curl -O https://raw.githubusercontent.com/python-distro/distro/master/src/distro/distro.py
python distro.py
```

distro is safe to vendor within projects that do not wish to add
dependencies.

```
cd myproject
curl -O https://raw.githubusercontent.com/python-distro/distro/master/src/distro/distro.py
```

## Usage

```
$ distro
Name: Antergos Linux
Version: 2015.10 (ISO-Rolling)
Codename: ISO-Rolling

$ distro -j
{
    "codename": "ISO-Rolling",
    "id": "antergos",
    "like": "arch",
    "version": "16.9",
    "version_parts": {
        "build_number": "",
        "major": "16",
        "minor": "9"
    }
}

$ python
>>> import distro
>>> distro.name(pretty=True)
'CentOS Linux 8'
>>> distro.id()
'centos'
>>> distro.version(best=True)
'8.4.2105'
```

## Documentation

On top of the aforementioned API, several more functions are available. For a complete description of the
API, see the latest API documentation.

## Background

An alternative implementation became necessary because Python 3.5 deprecated
this function, and Python 3.8 removed it altogether. Its predecessor function
platform.dist
was already deprecated since Python 2.6 and removed in Python 3.8. Still, there
are many cases in which access to that information is needed. See Python issue
1322 for more information.

The distro package implements a robust and inclusive way of retrieving the
information about a distribution based on new standards and old methods,
namely from these data sources (from high to low precedence):

- The os-release file /etc/os-release if present, with a fall-back on /usr/lib/os-release if needed.
- The output of the lsb_release command, if available.
- The distro release file (/etc/*(-|_)(release|version)), if present.
- The uname command for BSD based distrubtions.

## Python and Distribution Support

distro is supported and tested on Python 3.6+ and PyPy and on any
distribution that provides one or more of the data sources covered.

This package is tested with test data that mimics the exact behavior of the data sources of a number of Linux distributions.

## Testing

```
git clone git@github.com:python-distro/distro.git
cd distro
pip install tox
tox
```

## Contributions

Pull requests are always welcome to deal with specific distributions or just
for general merriment.

See CONTRIBUTIONS for contribution info.

Reference implementations for supporting additional distributions and file
formats can be found here:

- https://github.com/saltstack/salt/blob/develop/salt/grains/core.py#L1172
- https://github.com/chef/ohai/blob/master/lib/ohai/plugins/linux/platform.rb
- https://github.com/ansible/ansible/blob/devel/lib/ansible/module_utils/facts/system/distribution.py
- https://github.com/puppetlabs/facter/blob/master/lib/src/facts/linux/os_linux.cc

## Package manager distributions

- https://src.fedoraproject.org/rpms/python-distro
- https://www.archlinux.org/packages/community/any/python-distro/
- https://launchpad.net/ubuntu/+source/python-distro
- https://packages.debian.org/stable/python3-distro
- https://packages.gentoo.org/packages/dev-python/distro
- https://pkgs.org/download/python3-distro
- https://slackbuilds.org/repository/14.2/python/python-distro/
