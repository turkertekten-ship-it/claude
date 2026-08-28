[image: pdoc]

 [image: pdoc documentation] [image: CI Status] [image: Code Coverage] [image: autofix.ci: yes] [image: PyPI Version] [image: Supported Python Versions]

API Documentation for Python Projects.

# Example

pdoc -o ./html pdoc generates this website: pdoc.dev/docs.

# Installation

```
pip install pdoc
```

pdoc is compatible with Python 3.10 and newer.

# Usage

```
pdoc your_python_module
# or
pdoc ./my_project.py
```

Run pdoc pdoc to see pdoc's own documentation,
run pdoc --help to view the command line flags,
or check our hosted copy of the documentation.

# Features

pdoc's main feature is a focus on simplicity: pdoc aims to do one thing and do it well.

- Documentation is plain Markdown.
- First-class support for type annotations and all other modern Python 3 features.
- Builtin web server with live reloading.
- Customizable HTML templates.
- Understands numpydoc and Google-style docstrings.
- Standalone HTML output without additional dependencies.

Under the hood...

- pdoc will automatically link identifiers in your docstrings to their corresponding documentation.
- pdoc respects your __all__ variable when present.
- pdoc will traverse the abstract syntax tree to extract type annotations and docstrings from constructors as well.
- pdoc will automatically try to resolve type annotation string literals as forward references.
- pdoc will use inheritance to resolve type annotations and docstrings for class members.

If you have substantially more complex documentation needs, we recommend using Sphinx!

## Contributing

As an open source project, pdoc welcomes contributions of all forms.

[image: Dev Guide]

## pdoc vs. pdoc3

This project is not associated with "pdoc3", which often falsely assumes our name.
Quoting @BurntSushi, the original author of pdoc:

> I'm pretty disgusted that someone has taken a project I built, relicensed it,
> attempted to erase its entry on the Python Wiki,
> released it under effectively the same name and, worst of all, associated it with Nazi symbols. Source: https://github.com/pdoc3/pdoc/issues/64

In contrast, the pdoc project strives to uphold a healthy community where everyone is treated with respect.
Everyone is welcome to contribute as long as they adhere to basic civility. We expressly distance ourselves from the use
of Nazi symbols and ideology.

---

The pdoc project was originally created by Andrew Gallant
and is currently maintained by Maximilian Hils.
