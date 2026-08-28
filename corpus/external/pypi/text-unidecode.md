---
date: 2019-08-30T21:36:45+0000
source: https://pypi.org/project/text-unidecode/
---
[image: Build Status]

text-unidecode is the most basic port of the
Text::Unidecode
Perl library.

There are other Python ports of Text::Unidecode (unidecode
and isounidecode). unidecode is GPL; isounidecode uses too much memory,
and it didn’t support Python 3 when this package was created.

You can redistribute it and/or modify this port under the terms of either:

- Artistic License, or
- GPL or GPLv2+

If you’re OK with GPL-only, use unidecode (it has better memory usage and
better transliteration quality).

text-unidecode supports Python 2.7 and 3.4+.

## Installation

```
pip install text-unidecode
```

## Usage

```
>>> from text_unidecode import unidecode
>>> unidecode(u'какой-то текст')
'kakoi-to tekst'
```
