---
date: 2026-07-09T14:53:45+0000
source: https://pypi.org/project/docker/
---
# Docker SDK for Python

[image: Build Status]

A Python library for the Docker Engine API. It lets you do anything the docker command does, but from within Python apps – run containers, manage containers, manage Swarms, etc.

## Installation

The latest stable version is available on PyPI. Install with pip:

```
pip install docker
```

> Older versions (< 6.0) required installing docker[tls] for SSL/TLS support.
> This is no longer necessary and is a no-op, but is supported for backwards compatibility.

## Usage

Connect to Docker using the default socket or the configuration in your environment:

```
import docker
client = docker.from_env()
```

You can run containers:

```
>>> client.containers.run("ubuntu:latest", "echo hello world")
'hello world\n'
```

You can run containers in the background:

```
>>> client.containers.run("bfirsh/reticulate-splines", detach=True)
<Container '45e6d2de7c54'>
```

You can manage containers:

```
>>> client.containers.list()
[<Container '45e6d2de7c54'>, <Container 'db18e4f20eaa'>, ...]

>>> container = client.containers.get('45e6d2de7c54')

>>> container.attrs['Config']['Image']
"bfirsh/reticulate-splines"

>>> container.logs()
"Reticulating spline 1...\n"

>>> container.stop()
```

You can stream logs:

```
>>> for line in container.logs(stream=True):
...   print(line.strip())
Reticulating spline 2...
Reticulating spline 3...
...
```

You can manage images:

```
>>> client.images.pull('nginx')
<Image 'nginx'>

>>> client.images.list()
[<Image 'ubuntu'>, <Image 'nginx'>, ...]
```

Read the full documentation to see everything you can do.
