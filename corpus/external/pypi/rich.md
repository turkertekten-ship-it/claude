[image: Supported Python Versions] [image: PyPI version]

[image: Downloads] [image: codecov] [image: Rich blog] [image: Twitter Follow]

[image: Logo]

English readme
• 简体中文 readme
• 正體中文 readme
• Lengua española readme
• Deutsche readme
• Läs på svenska
• 日本語 readme
• 한국어 readme
• Français readme
• Schwizerdütsch readme
• हिन्दी readme
• Português brasileiro readme
• Italian readme
• Русский readme
• Indonesian readme
• فارسی readme
• Türkçe readme
• Polskie readme

Rich is a Python library for rich text and beautiful formatting in the terminal.

The Rich API makes it easy to add color and style to terminal output. Rich can also render pretty tables, progress bars, markdown, syntax highlighted source code, tracebacks, and more — out of the box.

[image: Features]

For a video introduction to Rich see calmcode.io by @fishnets88.

See what people are saying about Rich.

## Compatibility

Rich works with Linux, macOS and Windows. True color / emoji works with new Windows Terminal, classic terminal is limited to 16 colors. Rich requires Python 3.8 or later.

Rich works with Jupyter notebooks with no additional configuration required.

## Installing

Install with pip or your favorite PyPI package manager.

```
python -m pip install rich
```

Run the following to test Rich output on your terminal:

```
python -m rich
```

## Rich Print

To effortlessly add rich output to your application, you can import the rich print method, which has the same signature as the builtin Python function. Try this:

```
from rich import print

print("Hello, [bold magenta]World[/bold magenta]!", ":vampire:", locals())
```

[image: Hello World]

## Rich REPL

Rich can be installed in the Python REPL, so that any data structures will be pretty printed and highlighted.

```
>>> from rich import pretty
>>> pretty.install()
```

[image: REPL]

## Using the Console

For more control over rich terminal content, import and construct a Console object.

```
from rich.console import Console

console = Console()
```

The Console object has a print method which has an intentionally similar interface to the builtin print function. Here's an example of use:

```
console.print("Hello", "World!")
```

As you might expect, this will print "Hello World!" to the terminal. Note that unlike the builtin print function, Rich will word-wrap your text to fit within the terminal width.

There are a few ways of adding color and style to your output. You can set a style for the entire output by adding a style keyword argument. Here's an example:

```
console.print("Hello", "World!", style="bold red")
```

The output will be something like the following:

[image: Hello World]

That's fine for styling a line of text at a time. For more finely grained styling, Rich renders a special markup which is similar in syntax to bbcode. Here's an example:

```
console.print("Where there is a [bold cyan]Will[/bold cyan] there [u]is[/u] a [i]way[/i].")
```

[image: Console Markup]

You can use a Console object to generate sophisticated output with minimal effort. See the Console API docs for details.

## Rich Inspect

Rich has an inspect function which can produce a report on any Python object, such as class, instance, or builtin.

```
>>> my_list = ["foo", "bar"]
>>> from rich import inspect
>>> inspect(my_list, methods=True)
```

[image: Log]

See the inspect docs for details.

# Rich Library

Rich contains a number of builtin renderables you can use to create elegant output in your CLI and help you debug your code.

Click the following headings for details:

Log

The Console object has a log() method which has a similar interface to print(), but also renders a column for the current time and the file and line which made the call. By default Rich will do syntax highlighting for Python structures and for repr strings. If you log a collection (i.e. a dict or a list) Rich will pretty print it so that it fits in the available space. Here's an example of some of these features.

```
from rich.console import Console
console = Console()

test_data = [
    {"jsonrpc": "2.0", "method": "sum", "params": [None, 1, 2, 4, False, True], "id": "1",},
    {"jsonrpc": "2.0", "method": "notify_hello", "params": [7]},
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
]

def test_log():
    enabled = False
    context = {
        "foo": "bar",
    }
    movies = ["Deadpool", "Rise of the Skywalker"]
    console.log("Hello from", console, "!")
    console.log(test_data, log_locals=True)

test_log()
```

The above produces the following output:

[image: Log]

Note the log_locals argument, which outputs a table containing the local variables where the log method was called.

The log method could be used for logging to the terminal for long running applications such as servers, but is also a very nice debugging aid.

Logging Handler

You can also use the builtin Handler class to format and colorize output from Python's logging module. Here's an example of the output:

[image: Logging]

Emoji

To insert an emoji in to console output place the name between two colons. Here's an example:

```
>>> console.print(":smiley: :vampire: :pile_of_poo: :thumbs_up: :raccoon:")
😃 🧛 💩 👍 🦝
```

Please use this feature wisely.

Tables

Rich can render flexible tables with unicode box characters. There is a large variety of formatting options for borders, styles, cell alignment etc.

[image: table movie]

The animation above was generated with table_movie.py in the examples directory.

Here's a simpler table example:

```
from rich.console import Console
from rich.table import Table

console = Console()

table = Table(show_header=True, header_style="bold magenta")
table.add_column("Date", style="dim", width=12)
table.add_column("Title")
table.add_column("Production Budget", justify="right")
table.add_column("Box Office", justify="right")
table.add_row(
    "Dec 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
)
table.add_row(
    "May 25, 2018",
    "[red]Solo[/red]: A Star Wars Story",
    "$275,000,000",
    "$393,151,347",
)
table.add_row(
    "Dec 15, 2017",
    "Star Wars Ep. VIII: The Last Jedi",
    "$262,000,000",
    "[bold]$1,332,539,889[/bold]",
)

console.print(table)
```

This produces the following output:

[image: table]

Note that console markup is rendered in the same way as print() and log(). In fact, anything that is renderable by Rich may be included in the headers / rows (even other tables).

The Table class is smart enough to resize columns to fit the available width of the terminal, wrapping text as required. Here's the same example, with the terminal made smaller than the table above:

[image: table2]

Progress Bars

Rich can render multiple flicker-free progress bars to track long-running tasks.

For basic usage, wrap any sequence in the track function and iterate over the result. Here's an example:

```
from rich.progress import track

for step in track(range(100)):
    do_step(step)
```

It's not much harder to add multiple progress bars. Here's an example taken from the docs:

[image: progress]

The columns may be configured to show any details you want. Built-in columns include percentage complete, file size, file speed, and time remaining. Here's another example showing a download in progress:

[image: progress]

To try this out yourself, see examples/downloader.py which can download multiple URLs simultaneously while displaying progress.

Status

For situations where it is hard to calculate progress, you can use the status method which will display a 'spinner' animation and message. The animation won't prevent you from using the console as normal. Here's an example:

```
from time import sleep
from rich.console import Console

console = Console()
tasks = [f"task {n}" for n in range(1, 11)]

with console.status("[bold green]Working on tasks...") as status:
    while tasks:
        task = tasks.pop(0)
        sleep(1)
        console.log(f"{task} complete")
```

This generates the following output in the terminal.

[image: status]

The spinner animations were borrowed from cli-spinners. You can select a spinner by specifying the spinner parameter. Run the following command to see the available values:

```
python -m rich.spinner
```

The above command generates the following output in the terminal:

[image: spinners]

Tree

Rich can render a tree with guide lines. A tree is ideal for displaying a file structure, or any other hierarchical data.

The labels of the tree can be simple text or anything else Rich can render. Run the following for a demonstration:

```
python -m rich.tree
```

This generates the following output:

[image: markdown]

See the tree.py example for a script that displays a tree view of any directory, similar to the linux tree command.

Columns

Rich can render content in neat columns with equal or optimal width. Here's a very basic clone of the (MacOS / Linux) ls command which displays a directory listing in columns:

```
import os
import sys

from rich import print
from rich.columns import Columns

directory = os.listdir(sys.argv[1])
print(Columns(directory))
```

The following screenshot is the output from the columns example which displays data pulled from an API in columns:

[image: columns]

Markdown

Rich can render markdown and does a reasonable job of translating the formatting to the terminal.

To render markdown import the Markdown class and construct it with a string containing markdown code. Then print it to the console. Here's an example:

```
from rich.console import Console
from rich.markdown import Markdown

console = Console()
with open("README.md") as readme:
    markdown = Markdown(readme.read())
console.print(markdown)
```

This will produce output something like the following:

[image: markdown]

Syntax Highlighting

Rich uses the pygments library to implement syntax highlighting. Usage is similar to rendering markdown; construct a Syntax object and print it to the console. Here's an example:

```
from rich.console import Console
from rich.syntax import Syntax

my_code = '''
def iter_first_last(values: Iterable[T]) -> Iterable[Tuple[bool, bool, T]]:
    """Iterate and generate a tuple with a flag for first and last value."""
    iter_values = iter(values)
    try:
        previous_value = next(iter_values)
    except StopIteration:
        return
    first = True
    for value in iter_values:
        yield first, False, previous_value
        first = False
        previous_value = value
    yield first, True, previous_value
'''
syntax = Syntax(my_code, "python", theme="monokai", line_numbers=True)
console = Console()
console.print(syntax)
```

This will produce the following output:

[image: syntax]

Tracebacks

Rich can render beautiful tracebacks which are easier to read and show more code than standard Python tracebacks. You can set Rich as the default traceback handler so all uncaught exceptions will be rendered by Rich.

Here's what it looks like on OSX (similar on Linux):

[image: traceback]

All Rich renderables make use of the Console Protocol, which you can also use to implement your own Rich content.

# Rich CLI

See also Rich CLI for a command line application powered by Rich. Syntax highlight code, render markdown, display CSVs in tables, and more, directly from the command prompt.

[image: Rich CLI]

# Textual

See also Rich's sister project, Textual, which you can use to build sophisticated User Interfaces in the terminal.

[image: textual-splash]

# Toad

Toad is a unified interface for agentic coding. Built with Rich and Textual.

[image: toad]

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

rich-15.0.0.tar.gz
 (230.7 kB
 view details)

Uploaded
 Apr 12, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

rich-15.0.0-py3-none-any.whl
 (310.7 kB
 view details)

Uploaded
 Apr 12, 2026
 Python 3

## File details

Details for the file rich-15.0.0.tar.gz.

### File metadata

- Download URL: rich-15.0.0.tar.gz
- Upload date:
 Apr 12, 2026
- Size: 230.7 kB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: poetry/2.3.2 CPython/3.12.11 Darwin/25.3.0

### File hashes

Hashes for rich-15.0.0.tar.gz
| Algorithm | Hash digest | |
| SHA256 | edd07a4824c6b40189fb7ac9bc4c52536e9780fbbfbddf6f1e2502c31b068c36 | |
| MD5 | 44f6e884d4af4150446b36469025e060 | |
| BLAKE2b-256 | c08f0722ca900cc807c13a6a0c696dacf35430f72e0ec571c4275d2371fca3e9 | |

See more details on using hashes here.

## File details

Details for the file rich-15.0.0-py3-none-any.whl.

### File metadata

- Download URL: rich-15.0.0-py3-none-any.whl
- Upload date:
 Apr 12, 2026
- Size: 310.7 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: poetry/2.3.2 CPython/3.12.11 Darwin/25.3.0

### File hashes

Hashes for rich-15.0.0-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 33bd4ef74232fb73fe9279a257718407f169c09b78a87ad3d296f548e27de0bb | |
| MD5 | ad15208ed2214a7350781ee40150ba42 | |
| BLAKE2b-256 | 823b64d4899d73f91ba49a8c18a8ff3f0ea8f1c1d75481760df8c68ef5235bf5 | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

This release

15.0.0 This release

Apr 12, 2026
 2 files

14.3.4

Apr 11, 2026
 2 files

14.3.3

Feb 19, 2026
 2 files

14.3.2

Feb 1, 2026
 2 files

14.3.1

Jan 24, 2026
 2 files

14.3.0

Jan 24, 2026
 2 files

14.2.0

Oct 9, 2025
 2 files

14.1.0

Jul 25, 2025
 2 files

14.0.0

Mar 30, 2025
 2 files

13.9.4

Nov 1, 2024
 2 files

13.9.3

Oct 22, 2024
 2 files

13.9.2

Oct 4, 2024
 2 files

13.9.1

Oct 1, 2024
 2 files

13.9.0

Oct 1, 2024
 2 files

13.8.1

Sep 10, 2024
 2 files

13.8.0

Aug 26, 2024
 2 files

13.7.1

Feb 28, 2024
 2 files

13.7.0

Nov 15, 2023
 2 files

13.6.0

Sep 30, 2023
 2 files

13.5.3

Sep 17, 2023
 2 files

13.5.2

Aug 1, 2023
 2 files

13.5.1

Jul 31, 2023
 2 files

13.5.0

Jul 29, 2023
 2 files

13.4.2

Jun 12, 2023
 2 files

13.4.1

May 31, 2023
 2 files

13.4.0

May 31, 2023
 2 files

13.3.5

Apr 27, 2023
 2 files

13.3.4

Apr 12, 2023
 2 files

13.3.3

Mar 27, 2023
 2 files

13.3.2

Mar 4, 2023
 2 files

13.3.1

Jan 28, 2023
 2 files

13.3.0

Jan 27, 2023
 2 files

13.2.0

Jan 19, 2023
 2 files

13.1.0

Jan 14, 2023
 2 files

13.0.1

Jan 6, 2023
 2 files

13.0.0

Dec 30, 2022
 2 files

Pre-release

13.0.0a1

Dec 30, 2022
 2 files

12.6.0

Oct 2, 2022
 2 files

Pre-release

12.6.0a2

Sep 23, 2022
 2 files

Pre-release

12.6.0a1

Sep 20, 2022
 2 files

12.5.1

Jul 11, 2022
 2 files

12.5.0

Jul 11, 2022
 2 files

12.4.4

May 24, 2022
 2 files

12.4.3

May 23, 2022
 2 files

12.4.2

May 23, 2022
 2 files

12.4.1

May 8, 2022
 2 files

12.4.0

May 7, 2022
 2 files

12.3.0

Apr 26, 2022
 2 files

12.2.0

Apr 5, 2022
 2 files

Yanked

12.1.0

Apr 3, 2022
 2 files

12.0.1

Mar 22, 2022
 2 files

12.0.0

Mar 10, 2022
 2 files

Pre-release

12.0.0a2

Mar 10, 2022
 2 files

Pre-release

12.0.0a1

Mar 9, 2022
 2 files

11.2.0

Feb 8, 2022
 2 files

11.1.0

Jan 28, 2022
 2 files

11.0.0

Jan 9, 2022
 2 files

10.16.2

Jan 2, 2022
 2 files

10.16.1

Dec 15, 2021
 2 files

Pre-release

10.16.1a1

Dec 14, 2021
 2 files

10.16.0

Dec 12, 2021
 2 files

Pre-release

10.15.3a2

Dec 11, 2021
 2 files

Pre-release

10.15.3a1

Dec 11, 2021
 2 files

10.15.2

Dec 2, 2021
 2 files

10.15.1

Nov 29, 2021
 2 files

10.15.0

Nov 28, 2021
 2 files

Pre-release

10.15.0a3

Nov 25, 2021
 2 files

Pre-release

10.15.0a2

Nov 24, 2021
 2 files

Pre-release

10.15.0a0

Nov 23, 2021
 2 files

10.14.0

Nov 16, 2021
 2 files

10.13.0

Nov 7, 2021
 2 files

10.12.0

Oct 6, 2021
 2 files

10.11.0

Sep 24, 2021
 2 files

10.10.0

Sep 18, 2021
 2 files

10.9.0

Aug 29, 2021
 2 files

10.8.0

Aug 28, 2021
 2 files

10.7.0

Aug 5, 2021
 2 files

10.6.0

Jul 12, 2021
 2 files

10.5.0

Jul 5, 2021
 2 files

10.4.0

Jun 18, 2021
 2 files

10.3.0

Jun 9, 2021
 2 files

10.2.2

May 19, 2021
 2 files

10.2.1

May 17, 2021
 2 files

10.2.0

May 12, 2021
 2 files

10.1.0

Apr 3, 2021
 2 files

10.0.1

Mar 30, 2021
 2 files

10.0.0

Mar 27, 2021
 2 files

9.13.0

Mar 6, 2021
 2 files

9.12.4

Mar 1, 2021
 2 files

9.12.3

Feb 28, 2021
 2 files

9.12.2

Feb 27, 2021
 2 files

9.12.1

Feb 27, 2021
 2 files

9.12.0

Feb 24, 2021
 2 files

9.11.1

Feb 20, 2021
 2 files

9.11.0

Feb 15, 2021
 2 files

9.10.0

Jan 27, 2021
 2 files

9.9.0

Jan 23, 2021
 2 files

9.8.2

Jan 15, 2021
 2 files

9.8.1

Jan 13, 2021
 2 files

9.8.0

Jan 11, 2021
 2 files

9.7.0

Jan 9, 2021
 2 files

9.6.2

Jan 7, 2021
 2 files

9.6.1

Dec 31, 2020
 2 files

9.6.0

Dec 30, 2020
 2 files

9.5.1

Dec 18, 2020
 2 files

9.5.0

Dec 18, 2020
 2 files

9.4.0

Dec 12, 2020
 2 files

9.3.0

Dec 1, 2020
 2 files

9.2.0

Nov 8, 2020
 2 files

9.1.0

Oct 23, 2020
 2 files

9.0.1

Oct 19, 2020
 2 files

9.0.0

Oct 18, 2020
 2 files

8.0.0

Oct 3, 2020
 2 files

7.1.0

Sep 26, 2020
 2 files

7.0.0

Sep 18, 2020
 2 files

6.2.0

Sep 14, 2020
 2 files

6.1.2

Sep 11, 2020
 2 files

6.1.1

Sep 7, 2020
 2 files

6.1.0

Sep 7, 2020
 2 files

6.0.0

Aug 25, 2020
 2 files

5.2.1

Aug 20, 2020
 2 files

5.2.0

Aug 15, 2020
 2 files

5.1.2

Aug 10, 2020
 2 files

5.1.1

Aug 9, 2020
 2 files

5.1.0

Aug 8, 2020
 2 files

5.0.0

Aug 2, 2020
 2 files

4.2.2

Jul 30, 2020
 2 files

4.2.1

Jul 29, 2020
 2 files

4.2.0

Jul 27, 2020
 2 files

4.1.0

Jul 26, 2020
 2 files

4.0.0

Jul 23, 2020
 2 files

3.4.1

Jul 22, 2020
 2 files

3.4.0

Jul 22, 2020
 2 files

3.3.2

Jul 14, 2020
 2 files

3.3.1

Jul 13, 2020
 2 files

3.3.0

Jul 12, 2020
 2 files

3.2.0

Jul 10, 2020
 2 files

3.1.0

Jul 9, 2020
 2 files

3.0.5

Jul 7, 2020
 2 files

3.0.4

Jul 7, 2020
 2 files

3.0.3

Jul 3, 2020
 2 files

3.0.2

Jul 2, 2020
 2 files

3.0.1

Jun 30, 2020
 2 files

3.0.0

Jun 28, 2020
 2 files

2.3.1

Jun 26, 2020
 2 files

2.3.0

Jun 26, 2020
 2 files

2.2.6

Jun 24, 2020
 2 files

2.2.5

Jun 23, 2020
 2 files

2.2.4

Jun 21, 2020
 2 files

2.2.3

Jun 15, 2020
 2 files

2.2.2

Jun 14, 2020
 2 files

2.2.1

Jun 14, 2020
 2 files

2.2.0

Jun 14, 2020
 2 files

2.1.0

Jun 11, 2020
 2 files

2.0.1

Jun 10, 2020
 2 files

2.0.0

Jun 7, 2020
 2 files

1.3.1

Jun 1, 2020
 2 files

1.3.0

May 31, 2020
 2 files

1.2.3

May 24, 2020
 2 files

1.2.2

May 22, 2020
 2 files

1.2.1

May 22, 2020
 2 files

1.2.0

May 22, 2020
 2 files

1.1.9

May 20, 2020
 2 files

1.1.8

May 20, 2020
 2 files

1.1.7

May 19, 2020
 2 files

1.1.6

May 17, 2020
 2 files

1.1.5

May 15, 2020
 2 files

1.1.4

May 15, 2020
 2 files

1.1.3

May 14, 2020
 2 files

1.1.2

May 14, 2020
 2 files

1.1.1

May 12, 2020
 2 files

1.1.0

May 10, 2020
 2 files

1.0.3

May 8, 2020
 2 files

1.0.2

May 8, 2020
 2 files

1.0.1

May 8, 2020
 2 files

1.0.0

May 3, 2020
 2 files

0.8.13

Apr 28, 2020
 2 files

0.8.12

Apr 21, 2020
 2 files

0.8.11

Apr 14, 2020
 2 files

0.8.10

Apr 12, 2020
 2 files

0.8.9

Apr 12, 2020
 2 files

0.8.8

Mar 31, 2020
 2 files

0.8.7

Mar 31, 2020
 2 files

0.8.6

Mar 29, 2020
 2 files

0.8.5

Mar 29, 2020
 2 files

0.8.4

Mar 28, 2020
 2 files

0.8.3

Mar 27, 2020
 2 files

0.8.2

Mar 27, 2020
 2 files

0.8.1

Mar 22, 2020
 2 files

0.8.0

Mar 17, 2020
 2 files

Pre-release

0.8.0a1

Mar 16, 2020
 2 files

0.7.2

Mar 15, 2020
 2 files

0.7.1

Mar 13, 2020
 2 files

0.7.0

Mar 12, 2020
 2 files

0.6.0

Mar 3, 2020
 2 files

0.5.0

Feb 23, 2020
 2 files

0.4.1

Feb 22, 2020
 2 files

0.4.0

Feb 22, 2020
 2 files

0.3.3

Feb 4, 2020
 2 files

0.3.2

Jan 26, 2020
 2 files

0.3.1

Jan 22, 2020
 2 files

0.3.0

Jan 19, 2020
 2 files

0.2.3

Dec 29, 2019
 2 files

0.2.2

Dec 25, 2019
 2 files

0.2.1

Dec 25, 2019
 2 files

0.2.0

Dec 25, 2019
 2 files

0.1.0

Nov 10, 2019
 2 files