Alembic is a database migrations tool written by the author
of SQLAlchemy. A migrations tool
offers the following functionality:

- Can emit ALTER statements to a database in order to change
the structure of tables and other constructs
- Provides a system whereby “migration scripts” may be constructed;
each script indicates a particular series of steps that can “upgrade” a
target database to a new version, and optionally a series of steps that can
“downgrade” similarly, doing the same steps in reverse.
- Allows the scripts to execute in some sequential manner.

The goals of Alembic are:

- Very open ended and transparent configuration and operation. A new
Alembic environment is generated from a set of templates which is selected
among a set of options when setup first occurs. The templates then deposit a
series of scripts that define fully how database connectivity is established
and how migration scripts are invoked; the migration scripts themselves are
generated from a template within that series of scripts. The scripts can
then be further customized to define exactly how databases will be
interacted with and what structure new migration files should take.
- Full support for transactional DDL. The default scripts ensure that all
migrations occur within a transaction - for those databases which support
this (Postgresql, Microsoft SQL Server), migrations can be tested with no
need to manually undo changes upon failure.
- Minimalist script construction. Basic operations like renaming
tables/columns, adding/removing columns, changing column attributes can be
performed through one line commands like alter_column(), rename_table(),
add_constraint(). There is no need to recreate full SQLAlchemy Table
structures for simple operations like these - the functions themselves
generate minimalist schema structures behind the scenes to achieve the given
DDL sequence.
- “auto generation” of migrations. While real world migrations are far more
complex than what can be automatically determined, Alembic can still
eliminate the initial grunt work in generating new migration directives
from an altered schema. The --autogenerate feature will inspect the
current status of a database using SQLAlchemy’s schema inspection
capabilities, compare it to the current state of the database model as
specified in Python, and generate a series of “candidate” migrations,
rendering them into a new migration script as Python directives. The
developer then edits the new file, adding additional directives and data
migrations as needed, to produce a finished migration. Table and column
level changes can be detected, with constraints and indexes to follow as
well.
- Full support for migrations generated as SQL scripts. Those of us who
work in corporate environments know that direct access to DDL commands on a
production database is a rare privilege, and DBAs want textual SQL scripts.
Alembic’s usage model and commands are oriented towards being able to run a
series of migrations into a textual output file as easily as it runs them
directly to a database. Care must be taken in this mode to not invoke other
operations that rely upon in-memory SELECTs of rows - Alembic tries to
provide helper constructs like bulk_insert() to help with data-oriented
operations that are compatible with script-based DDL.
- Non-linear, dependency-graph versioning. Scripts are given UUID
identifiers similarly to a DVCS, and the linkage of one script to the next
is achieved via human-editable markers within the scripts themselves.
The structure of a set of migration files is considered as a
directed-acyclic graph, meaning any migration file can be dependent
on any other arbitrary set of migration files, or none at
all. Through this open-ended system, migration files can be organized
into branches, multiple roots, and mergepoints, without restriction.
Commands are provided to produce new branches, roots, and merges of
branches automatically.
- Provide a library of ALTER constructs that can be used by any SQLAlchemy
application. The DDL constructs build upon SQLAlchemy’s own DDLElement base
and can be used standalone by any application or script.
- At long last, bring SQLite and its inability to ALTER things into the fold,
but in such a way that SQLite’s very special workflow needs are accommodated
in an explicit way that makes the most of a bad situation, through the
concept of a “batch” migration, where multiple changes to a table can
be batched together to form a series of instructions for a single, subsequent
“move-and-copy” workflow. You can even use “move-and-copy” workflow for
other databases, if you want to recreate a table in the background
on a busy system.

Documentation and status of Alembic is at https://alembic.sqlalchemy.org/

## The SQLAlchemy Project

Alembic is part of the SQLAlchemy Project and
adheres to the same standards and conventions as the core project.

### Development / Bug reporting / Pull requests

Please refer to the
SQLAlchemy Community Guide for
guidelines on coding and participating in this project.

### Code of Conduct

Above all, SQLAlchemy places great emphasis on polite, thoughtful, and
constructive communication between users and developers.
Please see our current Code of Conduct at
Code of Conduct.

## License

Alembic is distributed under the MIT license.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

alembic-1.19.1.tar.gz
 (2.1 MB
 view details)

Uploaded
 Aug 8, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

alembic-1.19.1-py3-none-any.whl
 (265.9 kB
 view details)

Uploaded
 Aug 8, 2026
 Python 3

## File details

Details for the file alembic-1.19.1.tar.gz.

### File metadata

- Download URL: alembic-1.19.1.tar.gz
- Upload date:
 Aug 8, 2026
- Size: 2.1 MB
- Tags: Source
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.14.0

### File hashes

Hashes for alembic-1.19.1.tar.gz
| Algorithm | Hash digest | |
| SHA256 | e0fca0518118c78acc493e31bcb5402f190057aaf6df8b5b95ce94c4789cf648 | |
| MD5 | 8c5ef9ee10f7435d2609af37cb1057e4 | |
| BLAKE2b-256 | 162be4153978368de59918115c9e01d3ebf58a558a7285efa7e960c383c4b59a | |

See more details on using hashes here.

## File details

Details for the file alembic-1.19.1-py3-none-any.whl.

### File metadata

- Download URL: alembic-1.19.1-py3-none-any.whl
- Upload date:
 Aug 8, 2026
- Size: 265.9 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? No
- Uploaded via: twine/7.0.0 CPython/3.14.0

### File hashes

Hashes for alembic-1.19.1-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | b39018cb3d9413a19cbd54cf3c02ad33998641f0538eb77413a488a21c3e14be | |
| MD5 | f1ad383034463d0bd72c7a087590266d | |
| BLAKE2b-256 | 2089e62cc37b69ad357cc8ecd6e7367f5245f523d3cbb338a66197212bdf6749 | |

See more details on using hashes here.

## Release history Release notifications |
 RSS feed

This release

1.19.1 This release

Aug 8, 2026
 2 files

1.19.0

Aug 4, 2026
 2 files

1.18.5

Jun 25, 2026
 2 files

1.18.4

Feb 10, 2026
 2 files

1.18.3

Jan 29, 2026
 2 files

1.18.2

Jan 28, 2026
 2 files

1.18.1

Jan 14, 2026
 2 files

1.18.0

Jan 9, 2026
 2 files

1.17.2

Nov 14, 2025
 2 files

1.17.1

Oct 29, 2025
 2 files

1.17.0

Oct 11, 2025
 2 files

1.16.5

Aug 27, 2025
 2 files

1.16.4

Jul 10, 2025
 2 files

1.16.3

Jul 8, 2025
 2 files

1.16.2

Jun 16, 2025
 2 files

1.16.1

May 21, 2025
 2 files

1.16.0

May 21, 2025
 2 files

1.15.2

Mar 28, 2025
 2 files

1.15.1

Mar 4, 2025
 2 files

Yanked

1.15.0

Mar 4, 2025
 2 files

1.14.1

Jan 19, 2025
 2 files

1.14.0

Nov 4, 2024
 2 files

1.13.3

Sep 23, 2024
 2 files

1.13.2

Jun 26, 2024
 2 files

1.13.1

Dec 20, 2023
 2 files

1.13.0

Dec 1, 2023
 2 files

1.12.1

Oct 26, 2023
 2 files

1.12.0

Aug 31, 2023
 2 files

1.11.3

Aug 16, 2023
 2 files

1.11.2

Aug 4, 2023
 2 files

1.11.1

May 17, 2023
 2 files

1.11.0

May 15, 2023
 2 files

1.10.4

Apr 24, 2023
 2 files

1.10.3

Apr 5, 2023
 2 files

1.10.2

Mar 8, 2023
 2 files

1.10.1

Mar 7, 2023
 2 files

1.10.0

Mar 5, 2023
 2 files

1.9.4

Feb 16, 2023
 2 files

1.9.3

Feb 7, 2023
 2 files

1.9.2

Jan 14, 2023
 2 files

1.9.1

Dec 23, 2022
 2 files

1.9.0

Dec 15, 2022
 2 files

1.8.1

Jul 13, 2022
 2 files

1.8.0

May 31, 2022
 2 files

1.7.7

Mar 14, 2022
 2 files

1.7.6

Feb 1, 2022
 2 files

1.7.5

Nov 11, 2021
 2 files

1.7.4

Oct 6, 2021
 2 files

1.7.3

Sep 17, 2021
 2 files

1.7.2

Sep 17, 2021
 2 files

1.7.1

Aug 30, 2021
 2 files

1.7.0

Aug 30, 2021
 2 files

1.6.5

May 27, 2021
 2 files

1.6.4

May 24, 2021
 2 files

1.6.3

May 21, 2021
 2 files

1.6.2

May 7, 2021
 1 file

1.6.1

May 6, 2021
 2 files

1.6.0

May 3, 2021
 2 files

1.5.8

Mar 23, 2021
 2 files

1.5.7

Mar 11, 2021
 2 files

1.5.6

Mar 5, 2021
 2 files

1.5.5

Feb 20, 2021
 2 files

1.5.4

Feb 3, 2021
 2 files

1.5.3

Jan 29, 2021
 2 files

1.5.2

Jan 20, 2021
 2 files

1.5.1

Jan 19, 2021
 2 files

Yanked

1.5.0

Jan 18, 2021
 1 file

1.4.3

Sep 11, 2020
 2 files

1.4.2

Mar 19, 2020
 1 file

1.4.1

Mar 1, 2020
 1 file

1.4.0

Feb 4, 2020
 1 file

1.3.3

Jan 22, 2020
 1 file

1.3.2

Dec 16, 2019
 1 file

1.3.1

Nov 13, 2019
 1 file

1.3.0

Oct 31, 2019
 1 file

1.2.1

Sep 24, 2019
 1 file

1.2.0

Sep 20, 2019
 1 file

1.1.0

Aug 27, 2019
 1 file

1.0.11

Jun 25, 2019
 1 file

1.0.10

Apr 28, 2019
 1 file

1.0.9

Apr 15, 2019
 1 file

1.0.8

Mar 4, 2019
 1 file

1.0.7

Jan 26, 2019
 1 file

1.0.6

Jan 13, 2019
 1 file

1.0.5

Nov 28, 2018
 1 file

1.0.4

Nov 28, 2018
 1 file

1.0.3

Nov 14, 2018
 1 file

1.0.2

Oct 31, 2018
 1 file

1.0.1

Oct 17, 2018
 1 file

1.0.0

Jul 13, 2018
 2 files

0.9.10

Jun 29, 2018
 1 file

0.9.9

Mar 22, 2018
 1 file

0.9.8

Feb 16, 2018
 1 file

0.9.7

Jan 16, 2018
 1 file

0.9.6

Oct 13, 2017
 1 file

0.9.5

Aug 9, 2017
 1 file

0.9.4

Aug 1, 2017
 1 file

0.9.3

Jul 6, 2017
 1 file

0.9.2

May 18, 2017
 1 file

0.9.1

Mar 1, 2017
 1 file

0.9.0

Feb 28, 2017
 1 file

0.8.10

Jan 17, 2017
 1 file

0.8.9

Nov 28, 2016
 1 file

0.8.8

Sep 12, 2016
 1 file

0.8.7

Jul 26, 2016
 1 file

0.8.6

Apr 14, 2016
 1 file

0.8.5

Mar 9, 2016
 1 file

0.8.4

Dec 16, 2015
 1 file

0.8.3

Oct 16, 2015
 1 file

0.8.2

Aug 25, 2015
 1 file

0.8.1

Aug 22, 2015
 1 file

0.8.0

Aug 12, 2015
 1 file

0.7.7

Jul 22, 2015
 1 file

0.7.6

May 5, 2015
 1 file

0.7.5.post2

Mar 20, 2015
 1 file

0.7.5.post1

Mar 19, 2015
 1 file

0.7.4

Jan 12, 2015
 1 file

0.7.3

Dec 30, 2014
 1 file

0.7.2

Dec 18, 2014
 1 file

0.7.1

Dec 3, 2014
 1 file

0.7.0

Nov 24, 2014
 1 file

0.6.7

Sep 9, 2014
 1 file

0.6.6

Aug 7, 2014
 1 file

0.6.5

May 3, 2014
 1 file

0.6.4

Mar 28, 2014
 1 file

0.6.3

Feb 3, 2014
 1 file

0.6.2

Dec 27, 2013
 1 file

0.6.1

Nov 27, 2013
 1 file

0.6.0

Jul 19, 2013
 1 file

0.5.0

Apr 4, 2013
 1 file

0.4.2

Jan 11, 2013
 1 file

0.4.1

Dec 9, 2012
 1 file

0.4.0

Oct 2, 2012
 1 file

0.3.6

Aug 15, 2012
 1 file

0.3.5

Jul 8, 2012
 1 file

0.3.4

Jun 3, 2012
 1 file

0.3.2

Apr 30, 2012
 1 file

0.3.1

Apr 7, 2012
 1 file

0.3.0

Apr 5, 2012
 1 file

0.2.2

Apr 4, 2012
 1 file

0.2.1

Jan 31, 2012
 1 file

0.2.0

Jan 30, 2012
 1 file

0.1.1

Jan 5, 2012
 1 file

0.1.0

Nov 30, 2011
 1 file

Pre-release

0.1alphadev

Oct 3, 2011

Pre-release

0.1.0dev

Nov 29, 2011