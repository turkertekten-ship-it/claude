---
date: 2026-07-21T08:08:03+0000
source: https://pypi.org/project/setuptools-scm/
---
# setuptools-scm

[image: github ci] [image: Documentation Status] [image: tidelift]

## about

setuptools-scm extracts Python package versions from git or hg metadata
instead of declaring them as the version argument
or in a Source Code Managed (SCM) managed file.

Additionally setuptools-scm provides setuptools with a list of
files that are managed by the SCM

(i.e. it automatically adds all the SCM-managed files to the sdist).

Unwanted files must be excluded via MANIFEST.in
or configuring Git archive.

> ⚠️ Important: Installing setuptools-scm automatically enables a file finder that includes all SCM-tracked files in your source distributions. This can be surprising if you have development files tracked in Git/Mercurial that you don't want in your package. Use MANIFEST.in to exclude unwanted files. See the documentation for details.

## pyproject.toml usage

The preferred way to configure setuptools-scm is to author
settings in a tool.setuptools_scm section of pyproject.toml.

This feature requires setuptools 61 or later (recommended: >=80 for best compatibility).
First, ensure that setuptools-scm is present during the project's
build step by specifying it as one of the build requirements.

```
[build-system]
requires = ["setuptools>=80", "setuptools-scm>=8"]
build-backend = "setuptools.build_meta"
```

That will be sufficient to require setuptools-scm for projects
that support PEP 518 like pip and build.

To enable version inference, you need to set the version
dynamically in the project section of pyproject.toml:

```
[project]
# version = "0.0.1"  # Remove any existing version parameter.
dynamic = ["version"]

[tool.setuptools_scm]
```

!!! note "Simplified Configuration"

```
Starting with setuptools-scm 8.1+, if `setuptools_scm` (or `setuptools-scm`) is
present in your `build-system.requires`, the `[tool.setuptools_scm]` section
becomes optional! (In 9.2+, this requires the `simple` extra.) You can now
enable setuptools-scm with just:

```toml title="pyproject.toml"
[build-system]
requires = ["setuptools>=80", "setuptools-scm[simple]>=9.2"]
build-backend = "setuptools.build_meta"

[project]
dynamic = ["version"]
```

The `[tool.setuptools_scm]` section is only needed if you want to customize
configuration options.
```

Additionally, a version file can be written by specifying:

```
[tool.setuptools_scm]
version_file = "pkg/_version.py"
```

Where pkg is the name of your package.

If you need to confirm which version string is being generated or debug the configuration,
you can install setuptools-scm directly in your working environment and run:

```
$ python -m setuptools_scm
# To explore other options, try:
$ python -m setuptools_scm --help
```

For further configuration see the documentation.

## Interaction with Enterprise Distributions

Some enterprise distributions like RHEL7
ship rather old setuptools versions.

In those cases its typically possible to build by using an sdist against setuptools-scm<2.0.
As those old setuptools versions lack sensible types for versions,
modern setuptools-scm is unable to support them sensibly.

It's strongly recommended to build a wheel artifact using modern Python and setuptools,
then installing the artifact instead of trying to run against old setuptools versions.

!!! note "Legacy Setuptools Support"
While setuptools-scm recommends setuptools >=80, it maintains compatibility with setuptools 61+
to support legacy deployments that cannot easily upgrade. Support for setuptools <80 is deprecated
and will be removed in a future release. This allows enterprise environments and older CI/CD systems
to continue using setuptools-scm while still encouraging adoption of newer versions.

## Code of Conduct

Everyone interacting in the setuptools-scm project's codebases, issue
trackers, chat rooms, and mailing lists is expected to follow the
PSF Code of Conduct.

## Security Contact

To report a security vulnerability, please use the
Tidelift security contact.
Tidelift will coordinate the fix and disclosure.
