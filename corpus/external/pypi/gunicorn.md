---
date: 2026-08-24T15:05:57+0000
source: https://pypi.org/project/gunicorn/
---
# Gunicorn

Gunicorn is maintained by volunteers. If it powers your production, please consider supporting us:
 [image: GitHub Sponsors] [image: Revolut]

[image: PyPI version] [image: Supported Python versions] [image: Build Status]

Gunicorn 'Green Unicorn' is a Python WSGI HTTP Server for UNIX. It's a pre-fork
worker model ported from Ruby's Unicorn project. The Gunicorn server is broadly
compatible with various web frameworks, simply implemented, light on server
resource usage, and fairly speedy.

New in v25: Per-app worker allocation for dirty arbiters, HTTP/2 support (beta)!

## Quick Start

```
pip install gunicorn
gunicorn myapp:app --workers 4
```

For ASGI applications (FastAPI, Starlette):

```
gunicorn myapp:app --worker-class asgi
```

## Features

- WSGI support for Django, Flask, Pyramid, and any WSGI framework
- ASGI support for FastAPI, Starlette, Quart
- HTTP/2 support (beta) with multiplexed streams
- Dirty Arbiters (beta) for heavy workloads (ML models, long-running tasks)
- uWSGI binary protocol for nginx integration
- Multiple worker types: sync, gthread, gevent, asgi
- Graceful worker process management
- Compatible with Python 3.10+

## Documentation

Full documentation at https://gunicorn.org

- Quickstart
- Configuration
- Deployment
- Settings Reference

## Community

- Report bugs on GitHub Issues
- Chat with us in your browser (#gunicorn on Libera.Chat, no account needed)
- See CONTRIBUTING.md for contribution guidelines

## Support

Powering Python apps since 2010. Support continued development.

[image: Become a Sponsor]

### Sponsors

[image: Enki Multimedia]

## License

Gunicorn is released under the MIT License. See the LICENSE file for details.
