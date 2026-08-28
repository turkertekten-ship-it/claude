---
date: 2025-08-28T19:00:19+0000
source: https://pypi.org/project/questionary/
---
# Questionary

[image: Version] [image: License] [image: Continuous Integration] [image: Coverage] [image: Supported Python Versions] [image: Documentation]

✨ Questionary is a Python library for effortlessly building pretty command line interfaces ✨

- Features
- Installation
- Usage
- Documentation
- Support

[image: Example]

```
import questionary

questionary.text("What's your first name").ask()
questionary.password("What's your secret?").ask()
questionary.confirm("Are you amazed?").ask()

questionary.select(
    "What do you want to do?",
    choices=["Order a pizza", "Make a reservation", "Ask for opening hours"],
).ask()

questionary.rawselect(
    "What do you want to do?",
    choices=["Order a pizza", "Make a reservation", "Ask for opening hours"],
).ask()

questionary.checkbox(
    "Select toppings", choices=["foo", "bar", "bazz"]
).ask()

questionary.path("Path to the projects version file").ask()
```

Used and supported by

## Features

Questionary supports the following input prompts:

- Text
- Password
- File Path
- Confirmation
- Select
- Raw select
- Checkbox
- Autocomplete

There is also a helper to print formatted text
for when you want to spice up your printed messages a bit.

## Installation

Use the package manager pip to install Questionary:

```
pip install questionary
```

✨🎂✨

## Usage

```
import questionary

questionary.select(
    "What do you want to do?",
    choices=[
        'Order a pizza',
        'Make a reservation',
        'Ask for opening hours'
    ]).ask()  # returns value of selection
```

That's all it takes to create a prompt! Have a look at the documentation
for some more examples.

## Documentation

Documentation for Questionary is available here.

## Support

Please open an issue
with enough information for us to reproduce your problem.
A minimal, reproducible example
would be very helpful.

## Contributing

Contributions are very much welcomed and appreciated. Head over to the documentation on how to contribute.

## Authors and Acknowledgment

Questionary is written and maintained by Tom Bocklisch and Kian Cross.

It is based on the great work by Oyetoke Toby
and Mark Fink.

## License

Licensed under the MIT License. Copyright 2021 Tom Bocklisch.
