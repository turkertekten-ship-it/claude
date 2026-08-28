---
date: 2025-10-20T16:17:36+0000
source: https://pypi.org/project/patsy/
---
# Patsy

Notice: patsy is no longer under active development. As of August 2021,
Matthew Wardrop (@matthewwardrop) and Tomás Capretto (@tomicapretto) have taken
on responsibility from Nathaniel Smith (@njsmith) for keeping the lights on, but
no new feature development is planned. The spiritual successor of this project
is Formulaic, and we
recommend that users migrate
when possible. For the time being, until major software packages have successfully
transitioned, we will attempt to keep patsy working in its current state with
current releases in the Python ecosystem.

---

Patsy is a Python library for describing statistical models
(especially linear models, or models that have a linear component) and
building design matrices. Patsy brings the convenience of R "formulas" to Python.

[image: PyPI - Version] [image: PyPI - Python Version] [image: https://patsy.readthedocs.io/] [image: PyPI - Status] [image: https://coveralls.io/r/pydata/patsy?branch=master] [image: https://doi.org/10.5281/zenodo.592075]

- Documentation: https://patsy.readthedocs.io/
- Downloads: http://pypi.python.org/pypi/patsy/
- Code and issues: https://github.com/pydata/patsy
- Mailing list: pydata@googlegroups.com (http://groups.google.com/group/pydata)

## Dependencies

- Python (3.6+)
- numpy
- Optional:

 - pytest/pytest-cov: needed to run tests
 - scipy: needed for spline-related functions like bs

## Installation

pip install patsy (or, for traditionalists: python setup.py install)

## License

2-clause BSD, see LICENSE.txt for details.
