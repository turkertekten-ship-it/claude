---
date: 2026-05-18T04:30:05+0000
source: https://pypi.org/project/watchfiles/
---
# watchfiles

[image: CI] [image: Coverage] [image: pypi] [image: CondaForge] [image: license]

Simple, modern and high performance file watching and code reload in python.

---

Documentation: watchfiles.helpmanual.io

Source Code: github.com/samuelcolvin/watchfiles

---

Underlying file system notifications are handled by the Notify rust library.

This package was previously named "watchgod",
see the migration guide for more information.

## Installation

watchfiles requires Python 3.10 - 3.15.

```
pip install watchfiles
```

Binaries are available for most architectures on Linux, MacOS and Windows (learn more).

Otherwise, you can install from source which requires Rust stable to be installed.

## Usage

Here are some examples of what watchfiles can do:

### watch Usage

```
from watchfiles import watch

for changes in watch('./path/to/dir'):
    print(changes)
```

See watch docs for more details.

### awatch Usage

```
import asyncio
from watchfiles import awatch

async def main():
    async for changes in awatch('/path/to/dir'):
        print(changes)

asyncio.run(main())
```

See awatch docs for more details.

### run_process Usage

```
from watchfiles import run_process

def foobar(a, b, c):
    ...

if __name__ == '__main__':
    run_process('./path/to/dir', target=foobar, args=(1, 2, 3))
```

See run_process docs for more details.

### arun_process Usage

```
import asyncio
from watchfiles import arun_process

def foobar(a, b, c):
    ...

async def main():
    await arun_process('./path/to/dir', target=foobar, args=(1, 2, 3))

if __name__ == '__main__':
    asyncio.run(main())
```

See arun_process docs for more details.

## CLI

watchfiles also comes with a CLI for running and reloading code. To run some command when files in src change:

```
watchfiles "some command" src
```

For more information, see the CLI docs.

Or run

```
watchfiles --help
```
