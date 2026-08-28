---
date: 2026-03-10T15:19:16+0000
source: https://pypi.org/project/mongoengine/
---
Info:

MongoEngine is an ORM-like layer on top of PyMongo.

Repository:

https://github.com/MongoEngine/mongoengine

Author:

Harry Marr (http://github.com/hmarr)

Maintainer:

Bastien Gerard (http://github.com/bagerard)

 [image: https://travis-ci.org/MongoEngine/mongoengine.svg?branch=master] [image: https://coveralls.io/repos/github/MongoEngine/mongoengine/badge.svg?branch=master] [image: https://img.shields.io/badge/code%20style-black-000000.svg] [image: https://pepy.tech/badge/mongoengine/month] [image: https://img.shields.io/pypi/v/mongoengine.svg] [image: https://readthedocs.org/projects/mongoengine-odm/badge/?version=latest]

## About

MongoEngine is a Python Object-Document Mapper for working with MongoDB.
Documentation is available at https://mongoengine-odm.readthedocs.io - there
is currently a tutorial,
a user guide, and
an API reference.

## Supported MongoDB Versions

MongoEngine is currently tested against MongoDB v4.4, v5.0, v6.0 and
v7.0. Future versions should be supported as well, but aren’t actively tested
at the moment. Make sure to open an issue or submit a pull request if you
experience any problems with a more recent MongoDB versions.

## Installation

We recommend the use of virtualenv and of
pip. You can then use python -m pip install -U mongoengine.
You may also have setuptools
and thus you can use easy_install -U mongoengine. Another option is
pipenv. You can then use pipenv install mongoengine
to both create the virtual environment and install the package. Otherwise, you can
download the source from GitHub and
run python setup.py install.

The support for Python2 was dropped with MongoEngine 0.20.0

## Dependencies

All of the dependencies can easily be installed via python -m pip.
At the very least, you’ll need these two packages to use MongoEngine:

- pymongo>=3.4

If you utilize a DateTimeField, you might also use a more flexible date parser:

- dateutil>=2.1.0

If you need to use an ImageField or ImageGridFsProxy:

- Pillow>=7.0.0

If you need to use signals:

- blinker>=1.3

## Examples

Some simple examples of what MongoEngine code looks like:

```
from mongoengine import *
connect('mydb')

class BlogPost(Document):
    title = StringField(required=True, max_length=200)
    posted = DateTimeField(default=datetime.datetime.utcnow)
    tags = ListField(StringField(max_length=50))
    meta = {'allow_inheritance': True}

class TextPost(BlogPost):
    content = StringField(required=True)

class LinkPost(BlogPost):
    url = StringField(required=True)

# Create a text-based post
>>> post1 = TextPost(title='Using MongoEngine', content='See the tutorial')
>>> post1.tags = ['mongodb', 'mongoengine']
>>> post1.save()

# Create a link-based post
>>> post2 = LinkPost(title='MongoEngine Docs', url='hmarr.com/mongoengine')
>>> post2.tags = ['mongoengine', 'documentation']
>>> post2.save()

# Iterate over all posts using the BlogPost superclass
>>> for post in BlogPost.objects:
...     print('===', post.title, '===')
...     if isinstance(post, TextPost):
...         print(post.content)
...     elif isinstance(post, LinkPost):
...         print('Link:', post.url)
...

# Count all blog posts and its subtypes
>>> BlogPost.objects.count()
2
>>> TextPost.objects.count()
1
>>> LinkPost.objects.count()
1

# Count tagged posts
>>> BlogPost.objects(tags='mongoengine').count()
2
>>> BlogPost.objects(tags='mongodb').count()
1
```

## Tests

To run the test suite, ensure you are running a local instance of MongoDB on
the standard port and have pytest installed. Then, run pytest tests/.

To run the test suite on every supported Python and PyMongo version, you can
use tox. You’ll need to make sure you have each supported Python version
installed in your environment and then:

```
# Install tox
$ python -m pip install tox
# Run the test suites
$ tox
```

## Community

- MongoEngine Users mailing list
- MongoEngine Developers mailing list

## Contributing

We welcome contributions! See the Contribution guidelines
