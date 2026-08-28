---
date: 2025-12-29T12:55:20+0000
source: https://pypi.org/project/termcolor/
---
# termcolor

[image: PyPI version] [image: Supported Python versions] [image: PyPI downloads] [image: GitHub Actions status] [image: Codecov] [image: Licence] [image: Code style: Black] [image: Tidelift]

## Installation

### From PyPI

```
python3 -m pip install --upgrade termcolor
```

### From source

```
git clone https://github.com/termcolor/termcolor
cd termcolor
python3 -m pip install .
```

### Demo

To see demo output, run:

```
python3 -m termcolor
```

## Example

```
import sys

from termcolor import colored, cprint

text = colored("Hello, World!", "red", attrs=["reverse", "blink"])
print(text)
cprint("Hello, World!", "green", "on_red")

print_red_on_cyan = lambda x: cprint(x, "red", "on_cyan")
print_red_on_cyan("Hello, World!")
print_red_on_cyan("Hello, Universe!")

for i in range(10):
    cprint(i, "magenta", end=" ")

cprint("Attention!", "red", attrs=["bold"], file=sys.stderr)

# You can also specify 0-255 RGB ints via a tuple
cprint("Both foreground and background can use tuples", (100, 150, 250), (50, 60, 70))
```

## Text properties

| Text colors | Text highlights | Attributes |
| black | on_black | bold |
| red | on_red | dark |
| green | on_green | italic |
| yellow | on_yellow | underline |
| blue | on_blue | blink |
| magenta | on_magenta | reverse |
| cyan | on_cyan | concealed |
| white | on_white | strike |
| light_grey | on_light_grey | |
| dark_grey | on_dark_grey | |
| light_red | on_light_red | |
| light_green | on_light_green | |
| light_yellow | on_light_yellow | |
| light_blue | on_light_blue | |
| light_magenta | on_light_magenta | |
| light_cyan | on_light_cyan | |

You can also use any arbitrary RGB color specified as a tuple of 0-255 integers, for
example, (100, 150, 250).

## Terminal properties

| Terminal | bold | dark | italic | underline | blink | reverse | concealed |
| xterm | yes | no | yes | yes | bold | yes | yes |
| linux | yes | yes | color | bold | yes | yes | no |
| rxvt | yes | no | yes | yes | bold/black | yes | no |
| dtterm | yes | yes | ? | yes | reverse | yes | yes |
| teraterm | reverse | no | ? | yes | rev/red | yes | no |
| aixterm | normal | no | ? | yes | no | yes | yes |
| PuTTY | color | no | no | yes | no | yes | no |
| Windows | no | no | no | no | no | yes | no |
| Cygwin SSH | yes | no | ? | color | color | color | yes |
| Mac Terminal | yes | no | yes | yes | yes | yes | yes |

## Overrides

Terminal colour detection can be disabled or enabled in several ways.

In order of precedence:

1. Calling colored or cprint with a truthy no_color disables colour.
1. Calling colored or cprint with a truthy force_color forces colour.
1. Setting the ANSI_COLORS_DISABLED environment variable to any non-empty value
disables colour.
1. Setting the NO_COLOR environment variable to any non-empty
value disables colour.
1. Setting the FORCE_COLOR environment variable to any
non-empty value forces colour.
1. Setting the TERM environment variable to dumb, or using such a
dumb terminal,
disables colour.
1. Finally, termcolor will attempt to detect whether the terminal supports colour.
