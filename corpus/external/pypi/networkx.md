[image: https://github.com/networkx/networkx/actions/workflows/test.yml/badge.svg?branch=main] [image: https://img.shields.io/pypi/v/networkx.svg?] [image: https://img.shields.io/pypi/l/networkx.svg?] [image: https://img.shields.io/pypi/pyversions/networkx.svg?] [image: https://img.shields.io/github/labels/networkx/networkx/good%20first%20issue?color=green&label=contribute] [image: https://insights.linuxfoundation.org/api/badge/health-score?project=networkx]

NetworkX is a Python package for the creation, manipulation,
and study of the structure, dynamics, and functions
of complex networks.

- Website (including documentation): https://networkx.org
- Mailing list: https://groups.google.com/forum/#!forum/networkx-discuss
- Source: https://github.com/networkx/networkx
- Bug reports: https://github.com/networkx/networkx/issues
- Report a security vulnerability: https://tidelift.com/security
- Tutorial: https://networkx.org/documentation/latest/tutorial.html
- GitHub Discussions: https://github.com/networkx/networkx/discussions
- Discord (Scientific Python) invite link: https://discord.com/invite/vur45CbwMz
- NetworkX meetings calendar (open to all): https://scientific-python.org/calendars/networkx.ics

## Simple example

Find the shortest path between two nodes in an undirected graph:

```
>>> import networkx as nx
>>> G = nx.Graph()
>>> G.add_edge("A", "B", weight=4)
>>> G.add_edge("B", "D", weight=2)
>>> G.add_edge("A", "C", weight=3)
>>> G.add_edge("C", "D", weight=4)
>>> nx.shortest_path(G, "A", "D", weight="weight")
['A', 'B', 'D']
```

## Install

Install the latest released version of NetworkX:

```
$ pip install networkx
```

Install with all optional dependencies:

```
$ pip install networkx[default]
```

For additional details,
please see the installation guide.

## Bugs

Please report any bugs that you find here.
Or, even better, fork the repository on GitHub
and create a pull request (PR). We welcome all changes, big or small, and we
will help you make the PR if you are new to git (just ask on the issue and/or
see the contributor guide).

## License

Released under the 3-clause BSD license:

```
Copyright (c) 2004-2025, NetworkX Developers
Aric Hagberg <hagberg@lanl.gov>
Dan Schult <dschult@colgate.edu>
Pieter Swart <swart@lanl.gov>
```
