---
date: 2026-08-06T04:53:20+0000
source: https://pypi.org/project/argcomplete/
---
Tab complete all the things!

Argcomplete provides easy, extensible command line tab completion of arguments for your Python application.

It makes two assumptions:

- You’re using bash or zsh as your shell (limited support exists for other shells - see below)
- You’re using argparse to manage your command line arguments/options

Argcomplete is particularly useful if your program has lots of options or subparsers, and if your program can
dynamically suggest completions for your argument/option values (for example, if the user is browsing resources over
the network).

## Installation

```
pip install argcomplete
activate-global-python-argcomplete
```

See Activating global completion below for details about the second step.

Refresh your shell environment (start a new shell).

## Synopsis

Add the PYTHON_ARGCOMPLETE_OK marker and a call to argcomplete.autocomplete() to your Python application as
follows:

```
#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argcomplete, argparse
parser = argparse.ArgumentParser()
...
argcomplete.autocomplete(parser)
args = parser.parse_args()
...
```

If using pyproject.toml [project.scripts] entry points, the PYTHON_ARGCOMPLETE_OK marker should appear
at the beginning of the file that contains the entry point.

Register your Python application with your shell’s completion framework by running register-python-argcomplete:

```
eval "$(register-python-argcomplete my-python-app)"
```

Quotes are significant; the registration will fail without them. See Global completion below for a way to enable
argcomplete generally without registering each application individually.

### argcomplete.autocomplete(parser)

This method is the entry point to the module. It must be called after ArgumentParser construction is complete, but
before the ArgumentParser.parse_args() method is called. The method looks for an environment variable that the
completion hook shellcode sets, and if it’s there, collects completions, prints them to the output stream (fd 8 by
default), and exits. Otherwise, it returns to the caller immediately.

## Specifying completers

You can specify custom completion functions for your options and arguments. Two styles are supported: callable and
readline-style. Callable completers are simpler. They are called with the following keyword arguments:

- prefix: The prefix text of the last word before the cursor on the command line.
For dynamic completers, this can be used to reduce the work required to generate possible completions.
- action: The argparse.Action instance that this completer was called for.
- parser: The argparse.ArgumentParser instance that the action was taken by.
- parsed_args: The result of argument parsing so far (the argparse.Namespace args object normally returned by
ArgumentParser.parse_args()).

Completers can return their completions as an iterable of strings or a mapping (dict) of strings to their
descriptions (zsh will display the descriptions as context help alongside completions). An example completer for names
of environment variables might look like this:

```
def EnvironCompleter(**kwargs):
    return os.environ
```

To specify a completer for an argument or option, set the completer attribute of its associated action. An easy
way to do this at definition time is:

```
from argcomplete.completers import EnvironCompleter

parser = argparse.ArgumentParser()
parser.add_argument("--env-var1").completer = EnvironCompleter
parser.add_argument("--env-var2").completer = EnvironCompleter
argcomplete.autocomplete(parser)
```

If you specify the choices keyword for an argparse option or argument (and don’t specify a completer), it will be
used for completions.

A completer that is initialized with a set of all possible choices of values for its action might look like this:

```
class ChoicesCompleter(object):
    def __init__(self, choices):
        self.choices = choices

    def __call__(self, **kwargs):
        return self.choices
```

The following two ways to specify a static set of choices are equivalent for completion purposes:

```
from argcomplete.completers import ChoicesCompleter

parser.add_argument("--protocol", choices=('http', 'https', 'ssh', 'rsync', 'wss'))
parser.add_argument("--proto").completer=ChoicesCompleter(('http', 'https', 'ssh', 'rsync', 'wss'))
```

Note that if you use the choices=<completions> option, argparse will show
all these choices in the --help output by default. To prevent this, set
metavar (like parser.add_argument("--protocol", metavar="PROTOCOL", choices=('http', 'https', 'ssh', 'rsync', 'wss'))).

The following script uses
parsed_args and Requests to query GitHub for publicly known members of an
organization and complete their names, then prints the member description:

```
#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import argcomplete, argparse, requests, pprint

def github_org_members(prefix, parsed_args, **kwargs):
    resource = "https://api.github.com/orgs/{org}/members".format(org=parsed_args.organization)
    return (member['login'] for member in requests.get(resource).json() if member['login'].startswith(prefix))

parser = argparse.ArgumentParser()
parser.add_argument("--organization", help="GitHub organization")
parser.add_argument("--member", help="GitHub member").completer = github_org_members

argcomplete.autocomplete(parser)
args = parser.parse_args()

pprint.pprint(requests.get("https://api.github.com/users/{m}".format(m=args.member)).json())
```

Try it like this:

```
./describe_github_user.py --organization heroku --member <TAB>
```

If you have a useful completer to add to the completer library, send a pull request!

### Readline-style completers

The readline module defines a completer protocol in rlcompleter. Readline-style completers are also supported by
argcomplete, so you can use the same completer object both in an interactive readline-powered shell and on the command
line. For example, you can use the readline-style completer provided by IPython to get introspective completions like
you would get in the IPython shell:

```
import IPython
parser.add_argument("--python-name").completer = IPython.core.completer.Completer()
```

argcomplete.CompletionFinder.rl_complete can also be used to plug in an argparse parser as a readline completer.

### Printing warnings in completers

Normal stdout/stderr output is suspended when argcomplete runs. Sometimes, though, when the user presses <TAB>, it’s
appropriate to print information about why completions generation failed. To do this, use warn:

```
from argcomplete import warn

def AwesomeWebServiceCompleter(prefix, **kwargs):
    if login_failed:
        warn("Please log in to Awesome Web Service to use autocompletion")
    return completions
```

### Using a custom completion validator

By default, argcomplete validates your completions by checking if they start with the prefix given to the completer. You
can override this validation check by supplying the validator keyword to argcomplete.autocomplete():

```
def my_validator(completion_candidate, current_input):
    """Complete non-prefix substring matches."""
    return current_input in completion_candidate

argcomplete.autocomplete(parser, validator=my_validator)
```

## Global completion

In global completion mode, you don’t have to register each argcomplete-capable executable separately. Instead, the shell
will look for the string PYTHON_ARGCOMPLETE_OK in the first 1024 bytes of any executable that it’s running
completion for, and if it’s found, follow the rest of the argcomplete protocol as described above.

Additionally, completion is activated for scripts run as python <script> and python -m <module>. If you’re using
multiple Python versions on the same system, the version being used to run the script must have argcomplete installed.

If you choose not to use global completion, or ship a completion module that depends on argcomplete, you must register
your script explicitly using eval "$(register-python-argcomplete my-python-app)". Standard completion module
registration rules apply: namely, the script name is passed directly to complete, meaning it is only tab completed
when invoked exactly as it was registered. In the above example, my-python-app must be on the path, and the user
must be attempting to complete it by that name. The above line alone would not allow you to complete
./my-python-app, or /path/to/my-python-app.

### Activating global completion

The script activate-global-python-argcomplete installs the global completion script
bash_completion.d/_python-argcomplete
into an appropriate location on your system for both bash and zsh. The specific location depends on your platform and
whether you installed argcomplete system-wide using sudo or locally (into your user’s home directory).

## Zsh Support

Argcomplete supports zsh. On top of plain completions like in bash, zsh allows you to see argparse help strings as
completion descriptions. All shellcode included with argcomplete is compatible with both bash and zsh, so the same
completer commands activate-global-python-argcomplete and eval "$(register-python-argcomplete my-python-app)"
work for zsh as well.

## Python Support

Argcomplete requires Python 3.10+.

## Support for other shells

Argcomplete maintainers provide support only for the bash and zsh shells on Linux and MacOS. For resources related to
other shells and platforms, including fish, tcsh, xonsh, powershell, and Windows, please see the
contrib directory.

## Common Problems

If global completion is not completing your script, bash may have registered a default completion function:

```
$ complete | grep my-python-app
complete -F _minimal my-python-app
```

You can fix this by restarting your shell, or by running complete -r my-python-app.

## Debugging

Set the _ARC_DEBUG variable in your shell to enable verbose debug output every time argcomplete runs. This will
disrupt the command line composition state of your terminal, but make it possible to see the internal state of the
completer if it encounters problems.

## Acknowledgments

Inspired and informed by the optcomplete module by Martin Blais.

## Links

- Project home page (GitHub)
- Documentation
- Package distribution (PyPI)
- Change log

### Bugs

Please report bugs, issues, feature requests, etc. on GitHub.

## License

Copyright 2012-2023, Andrey Kislyuk and argcomplete contributors. Licensed under the terms of the
Apache License, Version 2.0. Distribution of the LICENSE and NOTICE
files with source copies of this package and derivative works is REQUIRED as specified by the Apache License.

 [image: https://github.com/kislyuk/argcomplete/workflows/Python%20package/badge.svg] [image: https://codecov.io/github/kislyuk/argcomplete/coverage.svg?branch=master] [image: https://img.shields.io/pypi/v/argcomplete.svg] [image: https://img.shields.io/pypi/l/argcomplete.svg]
