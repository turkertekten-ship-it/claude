---
date: 2026-06-17T11:18:33+0000
source: https://pypi.org/project/dramatiq/
---
# dramatiq

[image: Build Status] [image: PyPI version] [image: Documentation] [image: Discuss]

A fast and reliable distributed task processing library for Python 3.

---

Changelog: https://dramatiq.io/changelog.html
 Community: https://groups.io/g/dramatiq-users
 Documentation: https://dramatiq.io

---

### Sponsors

## Installation

If you want to use it with RabbitMQ

```
pip install 'dramatiq[rabbitmq, watch]'
```

or if you want to use it with Redis

```
pip install 'dramatiq[redis, watch]'
```

## Quickstart

Make sure you've got RabbitMQ running, then create a new file called
example.py:

```
import dramatiq
import requests
import sys

@dramatiq.actor
def count_words(url):
    response = requests.get(url)
    count = len(response.text.split(" "))
    print(f"There are {count} words at {url!r}.")

if __name__ == "__main__":
    count_words.send(sys.argv[1])
```

In one terminal, run your workers:

```
dramatiq example
```

In another, start enqueueing messages:

```
python example.py http://example.com
python example.py https://github.com
python example.py https://news.ycombinator.com
```

Check out the user guide to learn more!

## License

dramatiq is licensed under the LGPL. Please see COPYING and
COPYING.LESSER for licensing details.
