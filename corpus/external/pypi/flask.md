---
date: 2026-02-19T05:00:56+0000
source: https://pypi.org/project/flask/
---
# Flask

Flask is a lightweight WSGI web application framework. It is designed
to make getting started quick and easy, with the ability to scale up to
complex applications. It began as a simple wrapper around Werkzeug
and Jinja, and has become one of the most popular Python web
application frameworks.

Flask offers suggestions, but doesn't enforce any dependencies or
project layout. It is up to the developer to choose the tools and
libraries they want to use. There are many extensions provided by the
community that make adding new functionality easy.

## A Simple Example

```
# save this as app.py
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello, World!"
```

```
$ flask run
  * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

## Donate

The Pallets organization develops and supports Flask and the libraries
it uses. In order to grow the community of contributors and users, and
allow the maintainers to devote more time to the projects, please
donate today.

## Contributing

See our detailed contributing documentation for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.
