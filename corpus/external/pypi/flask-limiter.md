---
date: 2025-12-06T17:38:59+0000
source: https://pypi.org/project/flask-limiter/
---
[image: docs] [image: ci] [image: codecov] [image: pypi] [image: license]

Flask-Limiter adds rate limiting to Flask applications.

You can configure rate limits at different levels such as:

- Application wide global limits per user
- Default limits per route
- By Blueprints
- By Class-based views
- By individual routes

Flask-Limiter can be configured to fit your application in many ways, including:

- Persistance to various commonly used storage backends
(such as Redis, Memcached & MongoDB)
via limits
- Any rate limiting strategy supported by limits

Follow the quickstart below to get started or read the documentation for more details.

## Quickstart

### Install

```
pip install Flask-Limiter
```

### Add the rate limiter to your flask app

```
# app.py

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["2 per minute", "1 per second"],
    storage_uri="memory://",
    # Redis
    # storage_uri="redis://localhost:6379",
    # Redis cluster
    # storage_uri="redis+cluster://localhost:7000,localhost:7001,localhost:70002",
    # Memcached
    # storage_uri="memcached://localhost:11211",
    # Memcached Cluster
    # storage_uri="memcached://localhost:11211,localhost:11212,localhost:11213",
    # MongoDB
    # storage_uri="mongodb://localhost:27017",
    strategy="fixed-window", # or "moving-window", or "sliding-window-counter"
)

@app.route("/slow")
@limiter.limit("1 per day")
def slow():
    return "24"

@app.route("/fast")
def fast():
    return "42"

@app.route("/ping")
@limiter.exempt
def ping():
    return 'PONG'
```

### Inspect the limits using the command line interface

```
pip install Flask-Limiter[cli]
```

```
$ FLASK_APP=app:app flask limiter limits

app
├── fast: /fast
│   ├── 2 per 1 minute
│   └── 1 per 1 second
├── ping: /ping
│   └── Exempt
└── slow: /slow
    └── 1 per 1 day
```

### Run the app

```
$ FLASK_APP=app:app flask run
```

### Test it out

The fast endpoint respects the default rate limit while the
slow endpoint uses the decorated one. ping has no rate limit associated
with it.

```
$ curl localhost:5000/fast
42
$ curl localhost:5000/fast
42
$ curl localhost:5000/fast
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>429 Too Many Requests</title>
<h1>Too Many Requests</h1>
<p>2 per 1 minute</p>
$ curl localhost:5000/slow
24
$ curl localhost:5000/slow
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>429 Too Many Requests</title>
<h1>Too Many Requests</h1>
<p>1 per 1 day</p>
$ curl localhost:5000/ping
PONG
$ curl localhost:5000/ping
PONG
$ curl localhost:5000/ping
PONG
$ curl localhost:5000/ping
PONG
```
