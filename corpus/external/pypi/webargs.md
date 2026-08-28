---
date: 2025-10-29T16:07:47+0000
source: https://pypi.org/project/webargs/
---
[image: PyPI package] [image: Build status] [image: Documentation] [image: marshmallow 3|4 compatible]

Homepage: https://webargs.readthedocs.io/

webargs is a Python library for parsing and validating HTTP request objects, with built-in support for popular web frameworks, including Flask, Django, Bottle, Tornado, Pyramid, Falcon, and aiohttp.

```
from flask import Flask
from webargs import fields
from webargs.flaskparser import use_args

app = Flask(__name__)

@app.route("/")
@use_args({"name": fields.Str(required=True)}, location="query")
def index(args):
    return "Hello " + args["name"]

if __name__ == "__main__":
    app.run()

# curl http://localhost:5000/\?name\='World'
# Hello World
```

## Install

```
pip install -U webargs
```

## Documentation

Full documentation is available at https://webargs.readthedocs.io/.

## Support webargs

webargs is maintained by a group of
volunteers.
If you’d like to support the future of the project, please consider
contributing to our Open Collective:

 [image: Donate to our collective]

## Professional Support

Professionally-supported webargs is available through the
Tidelift Subscription.

Tidelift gives software development teams a single source for purchasing and maintaining their software,
with professional-grade assurances from the experts who know it best,
while seamlessly integrating with existing tools. [Get professional support]

 [image: Get supported marshmallow with Tidelift]

## Security Contact Information

To report a security vulnerability, please use the
Tidelift security contact.
Tidelift will coordinate the fix and disclosure.

## Project Links

- Docs: https://webargs.readthedocs.io/
- Changelog: https://webargs.readthedocs.io/en/latest/changelog.html
- Contributing Guidelines: https://webargs.readthedocs.io/en/latest/contributing.html
- PyPI: https://pypi.python.org/pypi/webargs
- Issues: https://github.com/marshmallow-code/webargs/issues
- Ecosystem / related packages: https://github.com/marshmallow-code/webargs/wiki/Ecosystem

## License

MIT licensed. See the LICENSE file for more details.
