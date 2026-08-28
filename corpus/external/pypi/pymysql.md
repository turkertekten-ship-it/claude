---
date: 2026-05-19T08:26:20+0000
source: https://pypi.org/project/pymysql/
---
[image: Documentation Status] [image: codecov] [image: Ask DeepWiki]

# PyMySQL

This package contains a pure-Python MySQL and MariaDB client library, based on
PEP 249.

## Requirements

- Python -- one of the following:

 - CPython : 3.9 and newer
 - PyPy : Latest 3.x version
- MySQL Server -- one of the following:

 - MySQL LTS versions
 - MariaDB LTS versions

## Installation

Package is uploaded on PyPI.

You can install it with pip:

```
$ python3 -m pip install PyMySQL
```

To use "sha256_password" or "caching_sha2_password" for authenticate,
you need to install additional dependency:

```
$ python3 -m pip install PyMySQL[rsa]
```

To use MariaDB's "ed25519" authentication method, you need to install
additional dependency:

```
$ python3 -m pip install PyMySQL[ed25519]
```

## Documentation

Documentation is available online: https://pymysql.readthedocs.io/

For support, please refer to the
StackOverflow.

## Example

The following examples make use of a simple table

```
CREATE TABLE `users` (
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `email` varchar(255) COLLATE utf8_bin NOT NULL,
    `password` varchar(255) COLLATE utf8_bin NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin
AUTO_INCREMENT=1 ;
```

```
import pymysql.cursors

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='user',
                             password='passwd',
                             database='db',
                             cursorclass=pymysql.cursors.DictCursor)

with connection:
    with connection.cursor() as cursor:
        # Create a new record
        sql = "INSERT INTO `users` (`email`, `password`) VALUES (%s, %s)"
        cursor.execute(sql, ('webmaster@python.org', 'very-secret'))

    # connection is not autocommit by default. So you must commit to save
    # your changes.
    connection.commit()

    with connection.cursor() as cursor:
        # Read a single record
        sql = "SELECT `id`, `password` FROM `users` WHERE `email`=%s"
        cursor.execute(sql, ('webmaster@python.org',))
        result = cursor.fetchone()
        print(result)
```

This example will print:

```
{'password': 'very-secret', 'id': 1}
```

## Resources

- DB-API 2.0: https://www.python.org/dev/peps/pep-0249/
- MySQL Reference Manuals: https://dev.mysql.com/doc/
- Getting Help With MariaDB https://mariadb.com/kb/en/getting-help-with-mariadb/
- MySQL client/server protocol:
https://dev.mysql.com/doc/internals/en/client-server-protocol.html
- "Connector" channel in MySQL Community Slack:
https://lefred.be/mysql-community-on-slack/
- PyMySQL mailing list:
https://groups.google.com/forum/#!forum/pymysql-users

## License

PyMySQL is released under the MIT License. See LICENSE for more
information.
