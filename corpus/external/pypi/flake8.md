---
date: 2025-06-20T19:31:34+0000
source: https://pypi.org/project/flake8/
---
[image: build status] [image: pre-commit.ci status] [image: Discord]

## Flake8

Flake8 is a wrapper around these tools:

- PyFlakes
- pycodestyle
- Ned Batchelder’s McCabe script

Flake8 runs all the tools by launching the single flake8 command.
It displays the warnings in a per-file, merged output.

It also adds a few features:

- files that contain this line are skipped:

```
# flake8: noqa
``` 
- lines that contain a # noqa comment at the end will not issue warnings.
- you can ignore specific errors on a line with # noqa: <error>, e.g.,
# noqa: E234. Multiple codes can be given, separated by comma. The noqa token is case insensitive, the colon before the list of codes is required otherwise the part after noqa is ignored
- Git and Mercurial hooks
- extendable through flake8.extension and flake8.formatting entry
points

### Quickstart

See our quickstart documentation for how to install
and get started with Flake8.

### Frequently Asked Questions

Flake8 maintains an FAQ in its
documentation.

### Questions or Feedback

If you have questions you’d like to ask the developers, or feedback you’d like
to provide, feel free to use the mailing list: code-quality@python.org

We would love to hear from you. Additionally, if you have a feature you’d like
to suggest, the mailing list would be the best place for it.

### Links

- Flake8 Documentation
- GitHub Project
- All (Open and Closed) Issues
- Code-Quality Archives
- Code of Conduct
- Getting Started Contributing

### Maintenance

Flake8 was created by Tarek Ziadé and is currently maintained by anthony sottile and Ian Cordasco
