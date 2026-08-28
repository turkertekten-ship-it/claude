---
date: 2024-01-25T13:21:49+0000
source: https://pypi.org/project/seaborn/
---
---

# seaborn: statistical data visualization

[image: PyPI Version] [image: License] [image: DOI] [image: Tests] [image: Code Coverage]

Seaborn is a Python visualization library based on matplotlib. It provides a high-level interface for drawing attractive statistical graphics.

## Documentation

Online documentation is available at seaborn.pydata.org.

The docs include a tutorial, example gallery, API reference, FAQ, and other useful information.

To build the documentation locally, please refer to doc/README.md.

## Dependencies

Seaborn supports Python 3.8+.

Installation requires numpy, pandas, and matplotlib. Some advanced statistical functionality requires scipy and/or statsmodels.

## Installation

The latest stable release (and required dependencies) can be installed from PyPI:

```
pip install seaborn
```

It is also possible to include optional statistical dependencies:

```
pip install seaborn[stats]
```

Seaborn can also be installed with conda:

```
conda install seaborn
```

Note that the main anaconda repository lags PyPI in adding new releases, but conda-forge (-c conda-forge) typically updates quickly.

## Citing

A paper describing seaborn has been published in the Journal of Open Source Software. The paper provides an introduction to the key features of the library, and it can be used as a citation if seaborn proves integral to a scientific publication.

## Testing

Testing seaborn requires installing additional dependencies; they can be installed with the dev extra (e.g., pip install .[dev]).

To test the code, run make test in the source directory. This will exercise the unit tests (using pytest) and generate a coverage report.

Code style is enforced with flake8 using the settings in the setup.cfg file. Run make lint to check. Alternately, you can use pre-commit to automatically run lint checks on any files you are committing: just run pre-commit install to set it up, and then commit as usual going forward.

## Development

Seaborn development takes place on Github: https://github.com/mwaskom/seaborn

Please submit bugs that you encounter to the issue tracker with a reproducible example demonstrating the problem. Questions about usage are more at home on StackOverflow, where there is a seaborn tag.
