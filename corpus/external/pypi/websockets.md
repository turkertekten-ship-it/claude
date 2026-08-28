[image: websockets]

[image: licence] [image: version] [image: pyversions]

## What is websockets?

websockets is a library for building WebSocket servers and clients in Python
with a focus on correctness, simplicity, robustness, and performance.

Built on top of asyncio, Python’s standard asynchronous I/O framework, the
default implementation provides an elegant coroutine-based API.

Implementations on top of threading and trio are also provided, as well
as a Sans-I/O layer for integration in third-party projects.

Documentation is available on Read the Docs.

Here’s an echo server with the asyncio API:

```
#!/usr/bin/env python

import asyncio
from websockets.asyncio.server import serve

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def main():
    server = await serve(echo, "localhost", 8765)
    await server.serve_forever()

asyncio.run(main())
```

Here’s how a client sends and receives messages with the threading API:

```
#!/usr/bin/env python

from websockets.sync.client import connect

def hello():
    with connect("ws://localhost:8765") as websocket:
        websocket.send("Hello world!")
        message = websocket.recv()
        print(f"Received: {message}")

hello()
```

Does that look good?

Get started with the tutorial!

## Why should I use websockets?

The development of websockets is shaped by four principles:

1. Correctness: websockets is heavily tested for compliance with
RFC 6455. Continuous integration fails under 100% branch coverage.
1. Simplicity: all you need to understand is msg = await ws.recv() and
await ws.send(msg). websockets takes care of managing connections
so you can focus on your application.
1. Robustness: websockets is built for production. For example, it was
the only library to handle backpressure correctly before the issue
became widely known in the Python community.
1. Performance: memory usage is optimized and configurable. A C extension
accelerates expensive operations. It’s pre-compiled for Linux, macOS and
Windows and packaged in the wheel format for each system and Python version.

Documentation is a first class concern in the project. Head over to Read the
Docs and see for yourself.

## Why shouldn’t I use websockets?

- If you prefer callbacks over coroutines: websockets was created to
provide the best coroutine-based API to manage WebSocket connections in
Python. Pick another library for a callback-based API.
- If you’re looking for a mixed HTTP / WebSocket library: websockets aims
at being an excellent implementation of RFC 6455: The WebSocket Protocol
and RFC 7692: Compression Extensions for WebSocket. Its support for HTTP
is minimal — just enough for an HTTP health check.

If you want to do both in the same server, look at HTTP + WebSocket servers
that build on top of websockets to support WebSocket connections, like
uvicorn or Sanic.

## What else?

Bug reports, patches and suggestions are welcome!

To report a security vulnerability, please use the Tidelift security
contact. Tidelift will coordinate the fix and disclosure.

For anything else, please open an issue or send a pull request.

Participants must uphold the Contributor Covenant code of conduct.

websockets is released under the BSD license.
