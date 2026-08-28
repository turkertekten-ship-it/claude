---
date: 2025-05-15T12:30:06+0000
source: https://pypi.org/project/pluggy/
---
[image: pypi] [image: conda-forge] [image: versions] [image: github-actions] [image: Join the chat at https://gitter.im/pytest-dev/pluggy] [image: black] [image: Code coverage Status]

This is the core framework used by the pytest, tox, and devpi projects.

Please read the docs to learn more!

## A definitive example

```
import pluggy

hookspec = pluggy.HookspecMarker("myproject")
hookimpl = pluggy.HookimplMarker("myproject")

class MySpec:
    """A hook specification namespace."""

    @hookspec
    def myhook(self, arg1, arg2):
        """My special little hook that you can customize."""

class Plugin_1:
    """A hook implementation namespace."""

    @hookimpl
    def myhook(self, arg1, arg2):
        print("inside Plugin_1.myhook()")
        return arg1 + arg2

class Plugin_2:
    """A 2nd hook implementation namespace."""

    @hookimpl
    def myhook(self, arg1, arg2):
        print("inside Plugin_2.myhook()")
        return arg1 - arg2

# create a manager and add the spec
pm = pluggy.PluginManager("myproject")
pm.add_hookspecs(MySpec)

# register plugins
pm.register(Plugin_1())
pm.register(Plugin_2())

# call our ``myhook`` hook
results = pm.hook.myhook(arg1=1, arg2=2)
print(results)
```

Running this directly gets us:

```
$ python docs/examples/toy-example.py
inside Plugin_2.myhook()
inside Plugin_1.myhook()
[-1, 3]
```

### Support pluggy

Open Collective is an online funding platform for open and transparent communities.
It provides tools to raise money and share your finances in full transparency.

It is the platform of choice for individuals and companies that want to make one-time or
monthly donations directly to the project.

pluggy is part of the pytest-dev project, see more details in the pytest collective.
