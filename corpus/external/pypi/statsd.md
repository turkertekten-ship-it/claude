---
date: 2022-11-06T14:17:34+0000
source: https://pypi.org/project/statsd/
---
statsd is a friendly front-end to Graphite. This is a Python client
for the statsd daemon.

 [image: Latest CI status] [image: Latest release] [image: Supported Python versions] [image: Wheel Status]

Code:

https://github.com/jsocol/pystatsd

License:

MIT; see LICENSE file

Issues:

https://github.com/jsocol/pystatsd/issues

Documentation:

https://statsd.readthedocs.io/

Quickly, to use:

```
>>> import statsd
>>> c = statsd.StatsClient('localhost', 8125)
>>> c.incr('foo')  # Increment the 'foo' counter.
>>> c.timing('stats.timed', 320)  # Record a 320ms 'stats.timed'.
```

You can also add a prefix to all your stats:

```
>>> import statsd
>>> c = statsd.StatsClient('localhost', 8125, prefix='foo')
>>> c.incr('bar')  # Will be 'foo.bar' in statsd/graphite.
```

## Installing

The easiest way to install statsd is with pip!

You can install from PyPI:

```
$ pip install statsd
```

Or GitHub:

```
$ pip install -e git+https://github.com/jsocol/pystatsd#egg=statsd
```

Or from source:

```
$ git clone https://github.com/jsocol/pystatsd
$ cd pystatsd
$ python setup.py install
```

## Docs

There are lots of docs in the docs/ directory and on ReadTheDocs.
