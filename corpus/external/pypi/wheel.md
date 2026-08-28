---
date: 2026-08-11T22:02:26+0000
source: https://pypi.org/project/wheel/
---
This is a command line tool for manipulating Python wheel files, as defined in
PEP 427. It contains the following functionality:

- Convert .egg archives into .whl
- Unpack wheel archives
- Repack wheel archives
- Add or remove tags in existing wheel archives

## Historical note

This project used to contain the implementation of the setuptools bdist_wheel
command, but as of setuptools v70.1, it no longer needs wheel installed for that to
work. Thus, you should install this only if you intend to use the wheel command
line tool!

## Documentation

The documentation can be found on Read The Docs.

## Code of Conduct

Everyone interacting in the wheel project’s codebases, issue trackers, chat
rooms, and mailing lists is expected to follow the PSF Code of Conduct.
