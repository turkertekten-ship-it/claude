---
date: 2026-03-11T01:23:56+0000
source: https://pypi.org/project/pyramid/
---
[image: 2.1-branch CI Status] [image: main Documentation Status] [image: Discord Server] [image: IRC Libera.Chat]

Pyramid is a small, fast, down-to-earth, open source Python web framework.
It makes real-world web application development
and deployment more fun, more predictable, and more productive.
Try Pyramid, browse its add-ons and documentation, and get an overview.

```
from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response

def hello_world(request):
    return Response('Hello World!')

if __name__ == '__main__':
    with Configurator() as config:
        config.add_route('hello', '/')
        config.add_view(hello_world, route_name='hello')
        app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 6543, app)
    server.serve_forever()
```

Pyramid is a project of the Pylons Project.

## Support and Documentation

See Pyramid Support and Development
for documentation, reporting bugs, and getting support.

## Developing and Contributing

See HACKING.txt and
contributing.md
for guidelines on running tests, adding features, coding style, and updating
documentation when developing in or contributing to Pyramid.

## License

Pyramid is offered under the BSD-derived Repoze Public License.

## Authors

Pyramid is made available by Agendaless Consulting
and a team of contributors.
