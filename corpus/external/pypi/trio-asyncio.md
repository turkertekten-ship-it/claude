---
date: 2026-05-15T21:27:41+0000
source: https://pypi.org/project/trio-asyncio/
---
trio-asyncio is a re-implementation of the asyncio mainloop on top of
Trio.

## Rationale

There are quite a few asyncio-compatible libraries.

On the other hand, Trio has native concepts of tasks and task cancellation.
Asyncio, on the other hand, is based on chaining Future objects, albeit
with nicer syntax.

Thus, being able to use asyncio libraries from Trio is useful.

## Principle of operation

The core of the “normal” asyncio main loop is the repeated execution of
synchronous code that’s submitted to call_soon or
add_reader/add_writer.

Everything else within asyncio, i.e. Futures and async/await,
is just syntactic sugar. There is no concept of a task; while a Future can
be cancelled, that in itself doesn’t affect the code responsible for
fulfilling it.

On the other hand, trio has genuine tasks with no separation between
returning a value asynchronously, and the code responsible for providing
that value.

trio_asyncio implements a task which runs (its own version of) the
asyncio main loop. It also contains shim code which translates between these
concepts as transparently and correctly as possible, and it supplants a few
of the standard loop’s key functions.

This works rather well: trio_asyncio consists of just ~700 lines of
code (asyncio: ~8000) but passes the complete Python 3.6 test suite with no
errors.

trio_asyncio requires Python 3.9 or later.

## Author

Matthias Urlichs <matthias@urlichs.de>
