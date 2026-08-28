---
date: 2026-07-24T23:08:00+0000
source: https://pypi.org/project/testcontainers/
---
[image: uv] [image: Ruff] [image: PyPI - Version] [image: PyPI - License] [image: PyPI - Python Version] [image: codecov] [image: Core Tests] [image: Community Tests] [image: Docs]

[image: Codespace]

# Testcontainers Python

testcontainers-python facilitates the use of Docker containers for functional and integration testing.

For more information, see the docs.

## Getting Started

```
>>> from testcontainers.postgres import PostgresContainer
>>> import sqlalchemy

>>> with PostgresContainer("postgres:16") as postgres:
...     engine = sqlalchemy.create_engine(postgres.get_connection_url())
...     with engine.begin() as connection:
...         result = connection.execute(sqlalchemy.text("select version()"))
...         version, = result.fetchone()
>>> version
'PostgreSQL 16...'
```

The snippet above will spin up a postgres database in a container. The get_connection_url() convenience method returns a sqlalchemy compatible url we use to connect to the database and retrieve the database version.

## Contributing / Development / Release

See CONTRIBUTING.md for more details.

## Configuration

You can set environment variables to configure the library behaviour:

| Env Variable | Example | Description |
| TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE | /var/run/docker.sock | Path to Docker's socket used by ryuk |
| TESTCONTAINERS_RYUK_PRIVILEGED | false | Run ryuk as a privileged container |
| TESTCONTAINERS_RYUK_DISABLED | false | Disable ryuk |
| RYUK_CONTAINER_IMAGE | testcontainers/ryuk:0.8.1 | Custom image for ryuk |
| RYUK_RECONNECTION_TIMEOUT | 10s | Reconnection timeout for Ryuk TCP socket before Ryuk reaps all dangling containers |

Alternatively you can set the configuration during runtime:

```
from testcontainers.core import testcontainers_config

testcontainers_config.ryuk_docker_socket = "/home/user/docker.sock"
```
