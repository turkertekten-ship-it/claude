---
date: 2026-04-27T01:46:07+0000
source: https://pypi.org/project/pathspec/
---
## PathSpec

pathspec is a utility library for pattern matching of file paths. So far this
only includes Git’s gitignore pattern matching.

### Tutorial

Say you have a “Projects” directory and you want to back it up, but only
certain files, and ignore others depending on certain conditions:

```
>>> from pathspec import PathSpec
>>> # The gitignore-style patterns for files to select, but we're including
>>> # instead of ignoring.
>>> spec_text = """
...
... # This is a comment because the line begins with a hash: "#"
...
... # Include several project directories (and all descendants) relative to
... # the current directory. To reference only a directory you must end with a
... # slash: "/"
... /project-a/
... /project-b/
... /project-c/
...
... # Patterns can be negated by prefixing with exclamation mark: "!"
...
... # Ignore temporary files beginning or ending with "~" and ending with
... # ".swp".
... !~*
... !*~
... !*.swp
...
... # These are python projects so ignore compiled python files from
... # testing.
... !*.pyc
...
... # Ignore the build directories but only directly under the project
... # directories.
... !/*/build/
...
... """
```

The PathSpec class provides an abstraction around pattern implementations,
and we want to compile our patterns as “gitignore” patterns. You could call it a
wrapper for a list of compiled patterns:

```
>>> spec = PathSpec.from_lines('gitignore', spec_text.splitlines())
```

If we wanted to manually compile the patterns, we can use the GitIgnoreBasicPattern
class directly. It is used in the background for “gitignore” which internally
converts patterns to regular expressions:

```
>>> from pathspec.patterns.gitignore.basic import GitIgnoreBasicPattern
>>> patterns = map(GitIgnoreBasicPattern, spec_text.splitlines())
>>> spec = PathSpec(patterns)
```

PathSpec.from_lines() is a class method which simplifies that.

If you want to load the patterns from file, you can pass the file object
directly as well:

```
>>> with open('patterns.list', 'r') as fh:
>>>     spec = PathSpec.from_lines('gitignore', fh)
```

You can perform matching on a whole directory tree with:

```
>>> matches = set(spec.match_tree_files('path/to/directory'))
```

Or you can perform matching on a specific set of file paths with:

```
>>> matches = set(spec.match_files(file_paths))
```

Or check to see if an individual file matches:

```
>>> is_matched = spec.match_file(file_path)
```

There’s actually two implementations of “gitignore”. The basic implementation is
used by PathSpec and follows patterns as documented by gitignore.
However, Git’s behavior differs from the documented patterns. There’s some
edge-cases, and in particular, Git allows including files from excluded
directories which appears to contradict the documentation. GitIgnoreSpec
handles these cases to more closely replicate Git’s behavior:

```
>>> from pathspec import GitIgnoreSpec
>>> spec = GitIgnoreSpec.from_lines(spec_text.splitlines())
```

You do not specify the style of pattern for GitIgnoreSpec because it should
always use GitIgnoreSpecPattern internally.

### Performance

Running lots of regular expression matches against thousands of files in Python
is slow. Alternate regular expression backends can be used to improve
performance. PathSpec and GitIgnoreSpec both accept a backend
parameter to control the backend. The default is “best” to automatically choose
the best available backend. There are currently 3 backends.

The “simple” backend is the default and it simply uses Python’s re.Pattern
objects that are normally created. This can be the fastest when there’s only 1
or 2 patterns.

The “hyperscan” backend uses the hyperscan library. Hyperscan tends to be at
least 2 times faster than “simple”, and generally slower than “re2”. This can be
faster than “re2” under the right conditions with pattern counts of 1-25.

The “re2” backend uses the google-re2 library (not to be confused with the
re2 library on PyPI which is unrelated and abandoned). Google’s re2 tends to
be significantly faster than “simple”, and 3 times faster than “hyperscan” at
high pattern counts.

See benchmarks_backends.md for comparisons between native Python regular
expressions and the optional backends.

### FAQ

1. How do I ignore files like .gitignore?

GitIgnoreSpec (and PathSpec) positively match files by default. To find
the files to keep, and exclude files like .gitignore, you need to set
negate=True to flip the results:

```
>>> from pathspec import GitIgnoreSpec
>>> spec = GitIgnoreSpec.from_lines([...])
>>> keep_files = set(spec.match_tree_files('path/to/directory', negate=True))
>>> ignore_files = set(spec.match_tree_files('path/to/directory'))
```

### License

pathspec is licensed under the Mozilla Public License Version 2.0. See
LICENSE or the FAQ for more information.

In summary, you may use pathspec with any closed or open source project
without affecting the license of the larger work so long as you:

- give credit where credit is due,
- and release any custom changes made to pathspec.

### Source

The source code for pathspec is available from the GitHub repo
cpburnz/python-pathspec.

### Installation

pathspec is available for install through PyPI:

```
pip install pathspec
```

pathspec can also be built from source. The following packages will be
required:

- build (>=0.6.0)

pathspec can then be built and installed with:

```
python -m build
pip install dist/pathspec-*-py3-none-any.whl
```

The following optional dependencies can be installed:

- google-re2: Enables optional “re2” backend.
- hyperscan: Enables optional “hyperscan” backend.
- typing-extensions: Improves some type hints.

### Documentation

Documentation for pathspec is available on Read the Docs.

The full change history can be found in CHANGES.rst and Change History.

An upgrade guide is available in UPGRADING.rst and Upgrade Guide.

### Other Languages

The related project pathspec-ruby (by highb) provides a similar library as
a Ruby gem.

## Change History

### 1.1.1 (2026-04-26)

Improvements:

- Improved type checking with mypy and pyright.

Bug fixes:

- Fixed typing on PathSpec[TPattern] to PathSpec[TPattern_co].
- Added missing variant type-hint type[Pattern] to PathSpec.from_lines() parameter pattern_factory.
- Fixed possible type error when using + and += operators on PathSpec.

### 1.1.0 (2026-04-22)

New features:

- Issue #108: Specialize pattern type for PathSpec as PathSpec[TPattern] for better debugging of PathSpec().patterns.

Bug fixes:

- Issue #93: Git discards invalid range notation. GitIgnoreSpecPattern now discards patterns with invalid range notation like Git.
- Pull #106: Fix escape() not escaping backslash characters.

Improvements:

- Pull #110: Nicer debug print outs (and str for regex pattern).

### 1.0.4 (2026-01-26)

Bug fixes:

- Issue #103: Using re2 fails if pyre2 is also installed.

### 1.0.3 (2026-01-09)

Bug fixes:

- Issue #101: pyright strict errors with pathspec >= 1.0.0.
- Issue #102: No module named ‘tomllib’.

### 1.0.2 (2026-01-07)

Bug fixes:

- Type hint collections.abc.Callable does not properly replace typing.Callable until Python 3.9.2.

### 1.0.1 (2026-01-06)

Bug fixes:

- Issue #100: ValueError(f”{patterns=!r} cannot be empty.”) when using black.

### 1.0.0 (2026-01-05)

Major changes:

- Issue #91: Dropped support of EoL Python 3.8.
- Added concept of backends to allow for faster regular expression matching. The backend can be controlled using the backend argument to PathSpec(), PathSpec.from_lines(), GitIgnoreSpec(), and GitIgnoreSpec.from_lines().
- Renamed “gitwildmatch” pattern back to “gitignore”. The “gitignore” pattern behaves slightly differently when used with PathSpec (gitignore as documented) than with GitIgnoreSpec (replicates Git’s edge cases).

API changes:

- Breaking: protected method pathspec.pathspec.PathSpec._match_file() (with a leading underscore) has been removed and replaced by backends. This does not affect normal usage of PathSpec or GitIgnoreSpec. Only custom subclasses will be affected. If this breaks your usage, let me know by opening an issue.
- Deprecated: “gitwildmatch” is now an alias for “gitignore”.
- Deprecated: pathspec.patterns.GitWildMatchPattern is now an alias for pathspec.patterns.gitignore.spec.GitIgnoreSpecPattern.
- Deprecated: pathspec.patterns.gitwildmatch module has been replaced by the pathspec.patterns.gitignore package.
- Deprecated: pathspec.patterns.gitwildmatch.GitWildMatchPattern is now an alias for pathspec.patterns.gitignore.spec.GitIgnoreSpecPattern.
- Deprecated: pathspec.patterns.gitwildmatch.GitWildMatchPatternError is now an alias for pathspec.patterns.gitignore.GitIgnorePatternError.
- Removed: pathspec.patterns.gitwildmatch.GitIgnorePattern has been deprecated since v0.4 (2016-07-15).
- Signature of method pathspec.pattern.RegexPattern.match_file() has been changed from def match_file(self, file: str) -> RegexMatchResult | None to def match_file(self, file: AnyStr) -> RegexMatchResult | None to reflect usage.
- Signature of class method pathspec.pattern.RegexPattern.pattern_to_regex() has been changed from def pattern_to_regex(cls, pattern: str) -> tuple[str, bool] to def pattern_to_regex(cls, pattern: AnyStr) -> tuple[AnyStr | None, bool | None] to reflect usage and documentation.

New features:

- Added optional “hyperscan” backend using hyperscan library. It will automatically be used when installed. This dependency can be installed with pip install 'pathspec[hyperscan]'.
- Added optional “re2” backend using the google-re2 library. It will automatically be used when installed. This dependency can be installed with pip install 'pathspec[re2]'.
- Added optional dependency on typing-extensions library to improve some type hints.

Bug fixes:

- Issue #93: Do not remove leading spaces.
- Issue #95: Matching for files inside folder does not seem to behave like .gitignore’s.
- Issue #98: UnboundLocalError in RegexPattern when initialized with pattern=None.
- Type hint on return value of pathspec.pattern.RegexPattern.match_file() to match documentation.

Improvements:

- Mark Python 3.13 and 3.14 as supported.
- No-op patterns are now filtered out when matching files, slightly improving performance.
- Fix performance regression in iter_tree_files() from v0.10.
