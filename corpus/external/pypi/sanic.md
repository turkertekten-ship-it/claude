---
date: 2026-05-31T19:45:45+0000
source: https://pypi.org/project/sanic/
---
[image: Sanic | Build fast. Run fast.]

## Sanic | Build fast. Run fast.

| Build | [image: Tests] |
| Docs | [image: UserGuide] [image: Documentation] |
| Package | [image: PyPI] [image: PyPI version] [image: PyPI Wheel] [image: Supported implementations] [image: Code style ruff] |
| Support | [image: Forums] [image: Discord] [image: Awesome Sanic List] |
| Stats | [image: Downloads] [image: Downloads] [image: Downloads] |

Sanic is a Python 3.10+ web server and web framework that’s written to go fast. It allows the usage of the async/await syntax added in Python 3.5, which makes your code non-blocking and speedy.

Sanic is also ASGI compliant, so you can deploy it with an alternative ASGI webserver.

Source code on GitHub | Help and discussion board | User Guide | Chat on Discord

The project is maintained by the community, for the community. Contributions are welcome!

The goal of the project is to provide a simple way to get up and running a highly performant HTTP server that is easy to build, to expand, and ultimately to scale.

### Sponsor

Check out open collective to learn more about helping to fund Sanic.

### Installation

pip install sanic

> Sanic makes use of uvloop and ujson to help with performance. If you do not want to use those packages, simply add an environmental variable SANIC_NO_UVLOOP=true or SANIC_NO_UJSON=true at install time. $exportSANIC_NO_UVLOOP=true$exportSANIC_NO_UJSON=true$pipinstall--no-binary:all:sanic

### Hello World Example

```
from sanic import Sanic
from sanic.response import json

app = Sanic("my-hello-world-app")

@app.route('/')
async def test(request):
    return json({'hello': 'world'})
```

Sanic can now be easily run from CLI using sanic hello.app.

```
[2018-12-30 11:37:41 +0200] [13564] [INFO] Goin' Fast @ http://127.0.0.1:8000
[2018-12-30 11:37:41 +0200] [13564] [INFO] Starting worker [13564]
```

And, we can verify it is working: curl localhost:8000 -i

```
HTTP/1.1 200 OK
Connection: keep-alive
Keep-Alive: 5
Content-Length: 17
Content-Type: application/json

{"hello":"world"}
```

Now, let’s go build something fast!

Minimum Python version is 3.10.

### Documentation

User Guide, Changelog, and API Documentation can be found at sanic.dev.

### Questions and Discussion

Ask a question or join the conversation.

### Contribution

We are always happy to have new contributions. We have marked issues good for anyone looking to get started, and welcome questions on the forums. Please take a look at our Contribution guidelines.
