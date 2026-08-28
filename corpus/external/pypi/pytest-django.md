---
date: 2026-08-10T14:13:06+0000
source: https://pypi.org/project/pytest-django/
---
[image: PyPI Version] [image: Supported Python versions] [image: Build Status] [image: Supported Django versions] [image: Coverage]

## Welcome to pytest-django!

pytest-django allows you to test your Django project/applications with the
pytest testing tool.

- Quick start / tutorial
- Changelog
- Full documentation: https://pytest-django.readthedocs.io/en/latest/
- Contribution docs
- Version compatibility:

 - Django: 5.2, 6.0 and latest main branch (compatible at the time
of each release)
 - Python: CPython>=3.10 or PyPy 3
 - pytest: >=7.0

For compatibility with older versions, use previous pytest-django releases.
- Licence: BSD
- All contributors
- GitHub repository: https://github.com/pytest-dev/pytest-django
- Issue tracker
- Python Package Index (PyPI)

### Install pytest-django

```
pip install pytest-django
```

### Why would I use this instead of Django’s manage.py test command?

Running your test suite with pytest-django allows you to tap into the features
that are already present in pytest. Here are some advantages:

- Manage test dependencies with pytest fixtures.
- Less boilerplate tests: no need to import unittest, create a subclass with methods. Write tests as regular functions.
- Database re-use: no need to re-create the test database for every test run.
- Run tests in multiple processes for increased speed (with the pytest-xdist plugin).
- Make use of other pytest plugins.
- Works with both worlds: Existing unittest-style TestCase’s still work without any modifications.

See the pytest documentation for more information on pytest itself.
