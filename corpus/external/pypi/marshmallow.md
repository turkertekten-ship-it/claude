[image: Latest version] [image: Build status] [image: pre-commit.ci status] [image: Documentation]

marshmallow is an ORM/ODM/framework-agnostic library for converting complex datatypes, such as objects, to and from native Python datatypes.

```
from datetime import date
from pprint import pprint

from marshmallow import Schema, fields

class ArtistSchema(Schema):
    name = fields.Str()

class AlbumSchema(Schema):
    title = fields.Str()
    release_date = fields.Date()
    artist = fields.Nested(ArtistSchema())

bowie = dict(name="David Bowie")
album = dict(artist=bowie, title="Hunky Dory", release_date=date(1971, 12, 17))

schema = AlbumSchema()
result = schema.dump(album)
pprint(result, indent=2)
# { 'artist': {'name': 'David Bowie'},
#   'release_date': '1971-12-17',
#   'title': 'Hunky Dory'}
```

In short, marshmallow schemas can be used to:

- Validate input data.
- Deserialize input data to app-level objects.
- Serialize app-level objects to primitive Python types. The serialized objects can then be rendered to standard formats such as JSON for use in an HTTP API.

## Get it now

```
$ pip install -U marshmallow
```

## Documentation

Full documentation is available at https://marshmallow.readthedocs.io/ .

## Ecosystem

A list of marshmallow-related libraries can be found at the GitHub wiki here:

https://github.com/marshmallow-code/marshmallow/wiki/Ecosystem

## Credits

### Contributors

This project exists thanks to all the people who contribute.

You’re highly encouraged to participate in marshmallow’s development.
Check out the Contributing Guidelines to see how you can help.

Thank you to all who have already contributed to marshmallow!

 [image: Contributors]

### Backers

If you find marshmallow useful, please consider supporting the team with
a donation. Your donation helps move marshmallow forward.

Thank you to all our backers! [Become a backer]

 [image: Backers]

### Sponsors

marshmallow is sponsored by Route4Me.

 [image: Routing Planner]

Support this project by becoming a sponsor (or ask your company to support this project by becoming a sponsor).
Your logo will be displayed here with a link to your website. [Become a sponsor]

## Professional Support

Professionally-supported marshmallow is now available through the
Tidelift Subscription.

Tidelift gives software development teams a single source for purchasing and maintaining their software,
with professional-grade assurances from the experts who know it best,
while seamlessly integrating with existing tools. [Get professional support]

 [image: Get supported marshmallow with Tidelift]

## Project Links

- Docs: https://marshmallow.readthedocs.io/
- Changelog: https://marshmallow.readthedocs.io/en/latest/changelog.html
- Contributing Guidelines: https://github.com/marshmallow-code/.github/blob/main/CONTRIBUTING.md
- PyPI: https://pypi.org/project/marshmallow/
- Issues: https://github.com/marshmallow-code/marshmallow/issues
- Donate: https://opencollective.com/marshmallow

## License

MIT licensed. See the bundled LICENSE file for more details.
