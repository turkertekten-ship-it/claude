---
date: 2026-08-28T10:26:53+0000
source: https://pypi.org/project/typer/
---
[image: Typer]

Typer, build great CLIs. Easy to code. Based on Python type hints.

[image: Test] [image: Coverage][image: Package version]

---

Documentation: https://typer.tiangolo.com

Source Code: https://github.com/fastapi/typer

---

Typer is a library for building CLI applications that users will love using and developers will love creating. Based on Python type hints.

It's also a command line tool to run scripts, automatically converting them to CLI applications.

The key features are:

- Intuitive to write: Great editor support. Completion everywhere. Less time debugging. Designed to be easy to use and learn. Less time reading docs.
- Easy to use: It's easy to use for the final users. Automatic help, and automatic completion for all shells.
- Short: Minimize code duplication. Multiple features from each parameter declaration. Fewer bugs.
- Start simple: The simplest example adds only 2 lines of code to your app: 1 import, 1 function call.
- Grow large: Grow in complexity as much as you want, create arbitrarily complex trees of commands and groups of subcommands, with options and arguments.
- Run scripts: Typer includes a typer command/program that you can use to run scripts, automatically converting them to CLIs, even if they don't use Typer internally.

## FastAPI of CLIs

Typer is FastAPI's little sibling, it's the FastAPI of CLIs.

## Installation

First, install uv, and then add Typer to your project:

```
$ uv add typer
---> 100%
```

This installs both the Typer library and the typer command in the project's virtual environment. To use typer directly with shell completion, activate the project environment and install completion.

If you prefer to use pip, install typer inside a virtual environment. See the installation guide for the alternative steps.

## Example

### The absolute minimum

- Create a file main.py with:

```
def main(name: str):
    print(f"Hello {name}")
```

This script doesn't even use Typer internally. But you can use the typer command to run it as a CLI application.

### Run it

Run your application with the typer command:

```
// Run your application
$ typer main.py run

// You get a nice error, you are missing 'name'
Usage: typer [PATH_OR_MODULE] run [OPTIONS] {name}
Try 'typer [PATH_OR_MODULE] run --help' for help.
╭─ Error ───────────────────────────────────────────╮
│ Missing argument 'name'.                          │
╰───────────────────────────────────────────────────╯

// You get a --help for free
$ typer main.py run --help

Usage: typer [PATH_OR_MODULE] run [OPTIONS] {name}

Run the provided Typer app.

╭─ Arguments ───────────────────────────────────────╮
│ *    name      <str>  [required]                  │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯

// Now pass the 'name' argument
$ typer main.py run Camila

Hello Camila

// It works! 🎉
```

This is the simplest use case, not even using Typer internally, but it can already be quite useful for simple scripts.

Note: auto-completion works when you create a Python package and run it with --install-completion or when you use the typer command.

## Use Typer in your code

Now let's start using Typer in your own code, update main.py with:

```
import typer

def main(name: str):
    print(f"Hello {name}")

if __name__ == "__main__":
    typer.run(main)
```

Now you could run it with Python directly:

```
// Run your application
$ uv run python main.py

// You get a nice error, you are missing 'name'
Usage: main.py [OPTIONS] {name}
Try 'main.py --help' for help.
╭─ Error ───────────────────────────────────────────╮
│ Missing argument 'name'.                          │
╰───────────────────────────────────────────────────╯

// You get a --help for free
$ uv run python main.py --help

Usage: main.py [OPTIONS] {name}

╭─ Arguments ───────────────────────────────────────╮
│ *    name      <str>  [required]                  │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯

// Now pass the 'name' argument
$ uv run python main.py Camila

Hello Camila

// It works! 🎉
```

Note: you can also call this same script with the typer command, but you don't need to.

## Example upgrade

This was the simplest example possible.

Now let's see one a bit more complex.

### An example with two subcommands

Modify the file main.py.

Create a typer.Typer() app, and create two subcommands with their parameters.

```
import typer

app = typer.Typer()

@app.command()
def hello(name: str):
    print(f"Hello {name}")

@app.command()
def goodbye(name: str, formal: bool = False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")

if __name__ == "__main__":
    app()
```

And that will:

- Explicitly create a typer.Typer app.

 - The previous typer.run actually creates one implicitly for you.
- Add two subcommands with @app.command().
- Execute the app() itself, as if it was a function (instead of typer.run).

### Run the upgraded example

Check the new help:

```
$ uv run python main.py --help

 Usage: main.py [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────╮
│ --install-completion          Install completion  │
│                               for the current     │
│                               shell.              │
│ --show-completion             Show completion for │
│                               the current shell,  │
│                               to copy it or       │
│                               customize the       │
│                               installation.       │
│ --help                        Show this message   │
│                               and exit.           │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ hello                                             │
│ goodbye                                           │
╰───────────────────────────────────────────────────╯

// When you create a package you get ✨ auto-completion ✨ for free, installed with --install-completion

// You have 2 subcommands (the 2 functions): hello and goodbye
```

Now check the help for the hello command:

```
$ uv run python main.py hello --help

 Usage: main.py hello [OPTIONS] {name}

╭─ Arguments ───────────────────────────────────────╮
│ *    name      <str>  [required]                  │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯
```

And now check the help for the goodbye command:

```
$ uv run python main.py goodbye --help

 Usage: main.py goodbye [OPTIONS] {name}

╭─ Arguments ───────────────────────────────────────╮
│ *    name      <str>  [required]                  │
╰───────────────────────────────────────────────────╯
╭─ Options ─────────────────────────────────────────╮
│ --formal    --no-formal      [default: no-formal] │
│ --help                       Show this message    │
│                              and exit.            │
╰───────────────────────────────────────────────────╯

// Automatic --formal and --no-formal for the bool option 🎉
```

Now you can try out the new command line application:

```
// Use it with the hello command

$ uv run python main.py hello Camila

Hello Camila

// And with the goodbye command

$ uv run python main.py goodbye Camila

Bye Camila!

// And with --formal

$ uv run python main.py goodbye --formal Camila

Goodbye Ms. Camila. Have a good day.
```

Note: If your app only has one command, by default the command name is omitted in usage: python main.py Camila. However, when there are multiple commands, you must explicitly include the command name: python main.py hello Camila. See One or Multiple Commands for more details.

### Recap

In summary, you declare once the types of parameters (CLI arguments and CLI options) as function parameters.

You do that with standard modern Python types.

You don't have to learn a new syntax, the methods or classes of a specific library, etc.

Just standard Python.

For example, for an int:

```
total: int
```

or for a bool flag:

```
force: bool
```

And similarly for files, paths, enums (choices), etc. And there are tools to create groups of subcommands, add metadata, extra validation, etc.

You get: great editor support, including completion and type checks everywhere.

Your users get: automatic --help, auto-completion in their terminal (Bash, Zsh, Fish, PowerShell) when they install your package or when using the typer command.

For a more complete example including more features, see the Tutorial - User Guide.

## Dependencies

Typer requires only a few dependencies (most are tiny):

- rich: to show nicely formatted errors automatically.
- shellingham: to automatically detect the current shell when installing completion.
- annotated-doc: to generate documentation from Python type annotations.
- colorama (only on Windows): for producing colored terminal text on Windows.

### Click code

Typer used to depend on Click as well, a popular tool for building CLIs in Python.

Since version 0.26.0, Typer has vendored Click (included Click's source code internally, instead of installing it as a third party package) and has unified the code interactions between Typer and the embedded Click source code for easier maintainability in the future.

Note that some Click functionality will not be available anymore in the future, as we continue to improve and extend Typer's codebase.

### typer-slim

There used to be a slimmed-down version of Typer called typer-slim, which didn't include the dependencies rich and shellingham, nor the typer command.

However, since version 0.22.0, we have stopped supporting this, and typer-slim now simply installs (all of) Typer.

If you want to disable Rich globally, you can set an environmental variable TYPER_USE_RICH to False or 0.

## License

This project is licensed under the terms of the MIT license.
