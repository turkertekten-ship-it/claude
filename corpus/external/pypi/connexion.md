---
date: 2025-10-13T12:41:48+0000
source: https://pypi.org/project/connexion/
---
[image: coveralls] [image: PyPI version] [image: PyPI] [image: License] [image: GitHub Workflow Status] [image: Coveralls] [image: Gurubase]

 Explore the docs »

---

Connexion is a modern Python web framework that makes spec-first and api-first development easy.
You describe your API in an OpenAPI (or Swagger) specification with as much
detail as you want and Connexion will guarantee that it works as you specified.

It works either standalone, or in combination with any ASGI or WSGI-compatible framework!

📢 Connexion 3 was recently released! Read about the changes here »

## ✨ Features

Connexion provides the following functionality based on your specification:

- 🚏 Automatic route registration, no @route decorators needed
- 🔒 Authentication, split from your application logic
- 🔎 Request and response validation of headers, parameters, and body
- 📬 Parameter parsing and injection, no request object needed
- 📨 Response serialization, you can return regular Python objects
- 📺 A Swagger UI console with live documentation and ‘try it out’ feature
- 🧩 Pluggability, in all dimensions

Connexion also helps you write your OpenAPI specification and develop against it by providing a command line interface which lets you test and mock your specification.

```
   connexion run openapi.yaml
```

(back to top)

## 🫶 Sponsors

Sponsors help us dedicate time to maintain Connexion. Want to help?

Explore the options »

(back to top)

## 🪤 Why Connexion

With Connexion, you write the spec first. Connexion then calls your Python
code, handling the mapping from the specification to the code. This
incentivizes you to write the specification so that all of your
developers can understand what your API does, even before you write a
single line of code.

If multiple teams depend on your APIs, you can use Connexion to easily
send them the documentation of your API. This guarantees that your API will
follow the specification that you wrote. This is a different process from
the one offered by most frameworks, which generate a specification
after you've written the code.
Some disadvantages of generating specifications based on code is that
they often end up lacking details or mix your documentation with the implementation
logic of your application.

(back to top)

## ⚒️ How to Use

### Installation

You can install connexion using pip:

```
    $ pip install connexion
```

Connexion provides 'extras' with optional dependencies to unlock additional features:

- swagger-ui: Enables a Swagger UI console for your application.
- uvicorn: Enables to run the your application using app.run() for
development instead of using an external ASGI server.
- flask: Enables the FlaskApp to build applications compatible with the Flask
ecosystem.

You can install them as follows:

```
    $ pip install connexion[swagger-ui]
    $ pip install connexion[swagger-ui,uvicorn]
```

(back to top)

### Creating your application

Connexion can be used either as a standalone application or as a middleware wrapping an existing
ASGI (or WSGI) application written using a different framework. The standalone application can be
built using either the AsyncApp or FlaskApp.

- The AsyncApp is a lightweight application with native asynchronous support. Use it if you
are starting a new project and have no specific reason to use one of the other options.

```
    from connexion import AsyncApp
    app = AsyncApp(__name__)
``` 
- The FlaskApp leverages the Flask framework, which is useful if you're migrating from
connexion 2.X or you want to leverage the Flask ecosystem.

```
    from connexion import FlaskApp
    app = FlaskApp(__name__)
``` 
- The ConnexionMiddleware can be wrapped around any existing ASGI or WSGI application.
Use it if you already have an application written in a different framework and want to add
functionality provided by connexion

```
    from asgi_framework import App
    from connexion import ConnexionMiddleware
    app = App(__name__)
    app = ConnexionMiddleware(app)
``` 

(back to top)

### Registering an API

While you can register individual routes on your application, Connexion really shines when you
register an API defined by an OpenAPI (or Swagger) specification.
The operation described in your specification is automatically linked to your Python view function via the operationId

run.py

```
   def post_greeting(name: str, greeting: str):  # Paramaeters are automatically unpacked
       return f"{greeting} {name}", 200          # Responses are automatically serialized

   app.add_api("openapi.yaml")
```

openapi.yaml

```
   ...
   paths:
     /greeting/{name}:
       post:
         operationId: run.post_greeting
         responses:
           '200':
             content:
               text/plain:
                 schema:
                   type: string
         parameters:
           - name: name
             in: path
             required: true
             schema:
               type: string
           - name: greeting
             in: query
             required: true
             schema:
               type: string
```

(back to top)

### Running your application

If you installed connexion using connexion[uvicorn], you can run it using the
run method. This is only recommended for development:

```
    app.run()
```

In production, run your application using an ASGI server such as uvicorn. If you defined your
app in a python module called run.py, you can run it as follows:

```
    $ uvicorn run:app
```

Or with gunicorn:

```
    $ gunicorn -k uvicorn.workers.UvicornWorker run:app
```

---

Now you're able to run and use Connexion!

See the examples folder for more examples.

(back to top)

## 📜 Changes

A full changelog is maintained on the GitHub releases page.

(back to top)

## 🤲 Contributing

We welcome your ideas, issues, and pull requests. Just follow the
usual/standard GitHub practices.

For easy development, install connexion using poetry with all extras, and
install the pre-commit hooks to automatically run black formatting and static analysis checks.

```
    pip install poetry
    poetry install --all-extras
    pre-commit install
```

You can find out more about how Connexion works and where to apply your changes by having a look
at our architecture.

Unless you explicitly state otherwise in advance, any non trivial
contribution intentionally submitted for inclusion in this project by you
to the steward of this repository shall be under the
terms and conditions of Apache License 2.0 written below, without any
additional copyright information, terms or conditions.

(back to top)

## 🙏 Thanks

We'd like to thank all of Connexion's contributors for working on this
project, Swagger/OpenAPI for their support, and Zalando for originally developing and releasing Connexion.

## 📚 Recommended Resources

About the advantages of working spec-first:

- Blog Atlassian
- API guidelines Zalando
- Blog ML6
- Blog Zalando

Tools to help you work spec-first:

- Online swagger editor
- VS Code plugin
- Pycharm plugin
