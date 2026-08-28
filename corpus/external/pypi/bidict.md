---
date: 2026-08-25T23:45:51+0000
source: https://pypi.org/project/bidict/
---
The bidirectional mapping library for Python.

## Status

 [image: Latest release] [image: Documentation] [image: GitHub Actions CI status] [image: License] [image: PyPI Downloads] [image: Sponsor]

## Features

- Mature: Depended on by
Google, Venmo, CERN, Baidu, Tencent,
and teams across the world since 2009
- Familiar, Pythonic APIs
that are carefully designed for
safety, simplicity, flexibility, and ergonomics
- Lightweight, with no runtime dependencies
outside Python’s standard library
- Implemented in
concise, well-factored, fully type-hinted Python code
that is optimized for running efficiently
as well as for long-term maintenance and stability
(as well as joy)
- Extensively documented
- 100% test coverage
running continuously across all supported Python versions
(including property-based tests and benchmarks)

## Installation

pip install bidict

## Quick Start

```
>>> from bidict import bidict
>>> element_by_symbol = bidict({'H': 'hydrogen'})
>>> element_by_symbol['H']
'hydrogen'
>>> element_by_symbol.inverse['hydrogen']
'H'
```

For more usage documentation,
head to the intro [1]
and proceed from there.

## Enterprise Support

Enterprise-level support for bidict can be obtained via the
Tidelift subscription
or by contacting me directly.

I have a US-based LLC set up for invoicing,
and I have over 20 years of professional experience
delivering software and support to companies successfully.

You can also sponsor my work through several platforms, including GitHub Sponsors.
See the Sponsoring section below for details,
including rationale and examples of companies
supporting the open source projects they depend on.

## Voluntary Community Support

Please search through already-asked questions and answers
in GitHub Discussions
and the issue tracker
in case your question has already been addressed.

Otherwise, please feel free to
start a new discussion
or create a new issue on GitHub
for voluntary community support.

## Notice of Usage

If you use bidict,
and especially if your usage or your organization is significant in some way,
please let me know in any of the following ways:

- star bidict on GitHub
- post in GitHub Discussions
- email me

## Changelog

For bidict release notes, see the changelog. [2]

## Release Notifications

Watch bidict releases on GitHub
to be notified when new versions of bidict are published.
Click the “Watch” dropdown, choose “Custom”, and then choose “Releases”.

## Learning from bidict

One of the best things about bidict
is that it touches a surprising number of
interesting Python corners,
especially given its small size and scope.

Check out learning-from-bidict [3]
if you’re interested in learning more.

## Contributing

I have been bidict’s sole maintainer
and active contributor
since I started the project ~15 years ago.

Your help would be most welcome!
See the contributors-guide [4]
for more information.

## Sponsoring

 [image: Sponsor through GitHub]

Bidict is the product of thousands of hours of my unpaid work
over the 15+ years that I’ve been the sole maintainer.

If bidict has helped you or your company accomplish your work,
please sponsor my work through one of the following,
and/or ask your company to do the same:

- GitHub
- PayPal
- Tidelift
- thanks.dev
- Gumroad
- a support engagement with my LLC

If you’re not sure which to use, GitHub is an easy option,
especially if you already have a GitHub account.
Just choose a monthly or one-time amount, and GitHub handles everything else.
Your bidict sponsorship on GitHub will automatically go
on the same regular bill as any other GitHub charges you pay for.
PayPal is another easy option for one-time contributions.

See the following for rationale and examples of companies
supporting the open source projects they depend on
in this manner:

- https://engineering.atspotify.com/2022/04/announcing-the-spotify-foss-fund/
- https://blog.sentry.io/2021/10/21/we-just-gave-154-999-dollars-and-89-cents-to-open-source-maintainers
- https://engineering.indeedblog.com/blog/2019/07/foss-fund-six-months-in/

## Finding Documentation

If you’re viewing this on https://bidict.readthedocs.io,
note that multiple versions of the documentation are available,
and you can choose a different version using the popup menu at the bottom-right.
Please make sure you’re viewing the version of the documentation
that corresponds to the version of bidict you’d like to use.

If you’re viewing this on GitHub, PyPI, or some other place
that can’t render and link this documentation properly
and are seeing broken links,
try these alternate links instead:
