---
date: 2026-08-05T19:50:23+0000
source: https://pypi.org/project/dynaconf/
---
[image: dynaconf. new logo]

> dynaconf - Configuration Management for Python.

[image: MIT License] [image: PyPI] [image: PyPI] [image: PyPI - Downloads] [image: CI] [image: codecov] [image: Codacy Badge] [image: GitHub stars] [image: GitHub Release Date] [image: GitHub commits since latest release] [image: GitHub last commit] [image: Code Style Black]

[image: GitHub issues] [image: User Forum] [image: Join the chat at https://gitter.im/dynaconf/dev] [image: Matrix]

## Features

- Inspired by the 12-factor application guide
- Settings management (default values, validation, parsing, templating)
- Protection of sensitive information (passwords/tokens)
- Multiple file formats toml|yaml|json|ini|py and also customizable loaders.
- Full support for environment variables to override existing settings (dotenv support included).
- Optional layered system for multi environments [default, development, testing, production]
- Built-in support for Hashicorp Vault and Redis as settings and secrets storage.
- Built-in extensions for Django and Flask web frameworks.
- CLI for common operations such as init, list, write, validate, export.
- full docs on https://dynaconf.com

### Install

```
$ pip install dynaconf
```

#### Initialize Dynaconf on project root directory

```
$ cd path/to/your/project/

$ dynaconf init -f toml

⚙️  Configuring your Dynaconf environment
------------------------------------------
🐍 The file `config.py` was generated.

🎛️  settings.toml created to hold your settings.

🔑 .secrets.toml created to hold your secrets.

🙈 the .secrets.* is also included in `.gitignore`
  beware to not push your secrets to a public repo.

🎉 Dynaconf is configured! read more on https://dynaconf.com
```

> TIP: You can select toml|yaml|json|ini|py on dynaconf init -f <fileformat> toml is the default and also the most recommended format for configuration.

#### Dynaconf init creates the following files

```
.
├── config.py       # This is from where you import your settings object (required)
├── .secrets.toml   # This is to hold sensitive data like passwords and tokens (optional)
└── settings.toml   # This is to hold your application settings (optional)
```

On the file config.py Dynaconf init generates the following boilerplate

```
from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="DYNACONF",  # export envvars with `export DYNACONF_FOO=bar`.
    settings_files=['settings.yaml', '.secrets.yaml'],  # Load files in the given order.
)
```

> TIP: You can create the files yourself instead of using the init command as shown above and you can give any name you want instead of the default config.py (the file must be in your importable python path) - See more options that you can pass to Dynaconf class initializer on https://dynaconf.com

#### Using Dynaconf

Put your settings on settings.{toml|yaml|ini|json|py}

```
username = "admin"
port = 5555
database = {name='mydb', schema='main'}
```

Put sensitive information on .secrets.{toml|yaml|ini|json|py}

```
password = "secret123"
```

> IMPORTANT: dynaconf init command puts the .secrets.* in your .gitignore to avoid it to be exposed on public repos but it is your responsibility to keep it safe in your local environment, also the recommendation for production environments is to use the built-in support for Hashicorp Vault service for password and tokens.

Optionally you can now use environment variables to override values per execution or per environment.

```
# override `port` from settings.toml file and automatically casts as `int` value.
export DYNACONF_PORT=9900
```

On your code import the settings object

```
from path.to.project.config import settings

# Reading the settings

settings.username == "admin"  # dot notation with multi nesting support
settings.PORT == 9900  # case insensitive
settings['password'] == "secret123"  # dict like access
settings.get("nonexisting", "default value")  # Default values just like a dict
settings.databases.name == "mydb"  # Nested key traversing
settings['databases.schema'] == "main"  # Nested key traversing
```

## More

- Settings Schema Validation
- Custom Settings Loaders
- Vault Services
- Template substitutions
- etc...

There is a lot more you can do, read the docs: http://dynaconf.com

## Contribute

Main discussions happens on Discussions Tab learn more about how to get involved on CONTRIBUTING.md guide

## More

If you are looking for something similar to Dynaconf to use in your Rust projects: https://github.com/rubik/hydroconf

And a special thanks to Caneco for the logo.
