---
date: 2025-10-09T20:51:03+0000
source: https://pypi.org/project/aiofiles/
---
# aiofiles: file support for asyncio

[image: PyPI] [image: Build] [image: Coverage] [image: Supported Python versions] [image: Ruff]

aiofiles is an Apache2 licensed library, written in Python, for handling local
disk files in asyncio applications.

Ordinary local file IO is blocking, and cannot easily and portably be made
asynchronous. This means doing file IO may interfere with asyncio applications,
which shouldn't block the executing thread. aiofiles helps with this by
introducing asynchronous versions of files that support delegating operations to
a separate thread pool.

```
async with aiofiles.open('filename', mode='r') as f:
    contents = await f.read()
print(contents)
'My file contents'
```

Asynchronous iteration is also supported.

```
async with aiofiles.open('filename') as f:
    async for line in f:
        ...
```

Asynchronous interface to tempfile module.

```
async with aiofiles.tempfile.TemporaryFile('wb') as f:
    await f.write(b'Hello, World!')
```

## Features

- a file API very similar to Python's standard, blocking API
- support for buffered and unbuffered binary files, and buffered text files
- support for async/await (PEP 492) constructs
- async interface to tempfile module

## Installation

To install aiofiles, simply:

```
pip install aiofiles
```

## Usage

Files are opened using the aiofiles.open() coroutine, which in addition to
mirroring the builtin open accepts optional loop and executor
arguments. If loop is absent, the default loop will be used, as per the
set asyncio policy. If executor is not specified, the default event loop
executor will be used.

In case of success, an asynchronous file object is returned with an
API identical to an ordinary file, except the following methods are coroutines
and delegate to an executor:

- close
- flush
- isatty
- read
- readall
- read1
- readinto
- readline
- readlines
- seek
- seekable
- tell
- truncate
- writable
- write
- writelines

In case of failure, one of the usual exceptions will be raised.

aiofiles.stdin, aiofiles.stdout, aiofiles.stderr,
aiofiles.stdin_bytes, aiofiles.stdout_bytes, and
aiofiles.stderr_bytes provide async access to sys.stdin,
sys.stdout, sys.stderr, and their corresponding .buffer properties.

The aiofiles.os module contains executor-enabled coroutine versions of
several useful os functions that deal with files:

- stat
- statvfs
- sendfile
- rename
- renames
- replace
- remove
- unlink
- mkdir
- makedirs
- rmdir
- removedirs
- link
- symlink
- readlink
- listdir
- scandir
- access
- getcwd
- path.abspath
- path.exists
- path.isfile
- path.isdir
- path.islink
- path.ismount
- path.getsize
- path.getatime
- path.getctime
- path.samefile
- path.sameopenfile

### Tempfile

aiofiles.tempfile implements the following interfaces:

- TemporaryFile
- NamedTemporaryFile
- SpooledTemporaryFile
- TemporaryDirectory

Results return wrapped with a context manager allowing use with async with and async for.

```
async with aiofiles.tempfile.NamedTemporaryFile('wb+') as f:
    await f.write(b'Line1\n Line2')
    await f.seek(0)
    async for line in f:
        print(line)

async with aiofiles.tempfile.TemporaryDirectory() as d:
    filename = os.path.join(d, "file.ext")
```

### Writing tests for aiofiles

Real file IO can be mocked by patching aiofiles.threadpool.sync_open
as desired. The return type also needs to be registered with the
aiofiles.threadpool.wrap dispatcher:

```
aiofiles.threadpool.wrap.register(mock.MagicMock)(
    lambda *args, **kwargs: aiofiles.threadpool.AsyncBufferedIOBase(*args, **kwargs)
)

async def test_stuff():
    write_data = 'data'
    read_file_chunks = [
        b'file chunks 1',
        b'file chunks 2',
        b'file chunks 3',
        b'',
    ]
    file_chunks_iter = iter(read_file_chunks)

    mock_file_stream = mock.MagicMock(
        read=lambda *args, **kwargs: next(file_chunks_iter)
    )

    with mock.patch('aiofiles.threadpool.sync_open', return_value=mock_file_stream) as mock_open:
        async with aiofiles.open('filename', 'w') as f:
            await f.write(write_data)
            assert await f.read() == b'file chunks 1'

        mock_file_stream.write.assert_called_once_with(write_data)
```

### Contributing

Contributions are very welcome. Tests can be run with tox, please ensure
the coverage at least stays the same before you submit a pull request.
