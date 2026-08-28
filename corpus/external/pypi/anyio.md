[image: Build Status] [image: Code Coverage] [image: Documentation] [image: Gitter chat] [image: Tidelift]

AnyIO is an asynchronous networking and concurrency library that works on top of either asyncio or
Trio. It implements Trio-like structured concurrency (SC) on top of asyncio and works in harmony
with the native SC of Trio itself.

Applications and libraries written against AnyIO’s API will run unmodified on either asyncio or
Trio. AnyIO can also be adopted into a library or application incrementally – bit by bit, no full
refactoring necessary. It will blend in with the native libraries of your chosen backend.

To find out why you might want to use AnyIO’s APIs instead of asyncio’s, you can read about it
here.

## Documentation

View full documentation at: https://anyio.readthedocs.io/

## Features

AnyIO offers the following functionality:

- Task groups (nurseries in trio terminology)
- High-level networking (TCP, UDP and UNIX sockets)

 - Happy eyeballs algorithm for TCP connections (more robust than that of asyncio on Python
3.8)
 - async/await style UDP sockets (unlike asyncio where you still have to use Transports and
Protocols)
- A versatile API for byte streams and object streams
- Inter-task synchronization and communication (locks, conditions, events, semaphores, object
streams)
- Worker threads
- Subprocesses
- Subinterpreter support for code parallelization (on Python 3.13 and later)
- Asynchronous file I/O (using worker threads)
- Signal handling
- Asynchronous versions of the functools and itertools modules

AnyIO also comes with its own pytest plugin which also supports asynchronous fixtures.
It even works with the popular Hypothesis library.

## Security contact information

To report a security vulnerability, please use the Tidelift security contact.
Tidelift will coordinate the fix and disclosure.
