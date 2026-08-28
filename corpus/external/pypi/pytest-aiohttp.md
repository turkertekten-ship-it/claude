---
date: 2026-06-07T23:56:33+0000
source: https://pypi.org/project/pytest-aiohttp/
---
pytest plugin for aiohttp support

The library provides useful fixtures for creation test aiohttp server and client.

## Installation

```
$ pip install pytest-aiohttp
```

Add asyncio_mode = auto line to pytest configuration (see pytest-asyncio modes for details). The plugin works
with strict mode also.

## Usage

Write tests in pytest-asyncio style
using provided fixtures for aiohttp test server and client creation. The plugin provides
resources cleanup out-of-the-box.

The simple usage example:

```
from aiohttp import web

async def hello(request):
    return web.Response(body=b"Hello, world")

def create_app():
    app = web.Application()
    app.router.add_route("GET", "/", hello)
    return app

async def test_hello(aiohttp_client):
    client = await aiohttp_client(create_app())
    resp = await client.get("/")
    assert resp.status == 200
    text = await resp.text()
    assert "Hello, world" in text
```

See aiohttp documentation <https://docs.aiohttp.org/en/stable/testing.html#pytest> for
more details about fixtures usage.
