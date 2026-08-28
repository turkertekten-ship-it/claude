[image: Documentation Status] [image: PyPI Release] [image: Changelog] [image: MIT Licensed]

aiosqlite provides a friendly, async interface to sqlite databases.

It replicates the standard sqlite3 module, but with async versions
of all the standard connection and cursor methods, plus context managers for
automatically closing connections and cursors:

```
async with aiosqlite.connect(...) as db:
    await db.execute("INSERT INTO some_table ...")
    await db.commit()

    async with db.execute("SELECT * FROM some_table") as cursor:
        async for row in cursor:
            ...
```

It can also be used in the traditional, procedural manner:

```
db = await aiosqlite.connect(...)
cursor = await db.execute('SELECT * FROM some_table')
row = await cursor.fetchone()
rows = await cursor.fetchall()
await cursor.close()
await db.close()
```

aiosqlite also replicates most of the advanced features of sqlite3:

```
async with aiosqlite.connect(...) as db:
    db.row_factory = aiosqlite.Row
    async with db.execute('SELECT * FROM some_table') as cursor:
        async for row in cursor:
            value = row['column']

    await db.execute('INSERT INTO foo some_table')
    assert db.total_changes > 0
```

## Install

aiosqlite is compatible with Python 3.8 and newer.
You can install it from PyPI:

```
$ pip install aiosqlite
```

## Details

aiosqlite allows interaction with SQLite databases on the main AsyncIO event
loop without blocking execution of other coroutines while waiting for queries
or data fetches. It does this by using a single, shared thread per connection.
This thread executes all actions within a shared request queue to prevent
overlapping actions.

Connection objects are proxies to the real connections, contain the shared
execution thread, and provide context managers to handle automatically closing
connections. Cursors are similarly proxies to the real cursors, and provide
async iterators to query results.

## License

aiosqlite is copyright Amethyst Reese, and licensed under the
MIT license. I am providing code in this repository to you under an open source
license. This is my personal repository; the license you receive to my code
is from me and not from my employer. See the LICENSE file for details.
