---
date: 2025-10-22T00:15:15+0000
source: https://pypi.org/project/aiomysql/
---
[image: https://github.com/aio-libs/aiomysql/actions/workflows/ci-cd.yml/badge.svg?branch=main] [image: Code coverage] [image: Latest Version] [image: Documentation Status] [image: Chat on Gitter]

aiomysql is a “driver” for accessing a MySQL database
from the asyncio (PEP-3156/tulip) framework. It depends on and reuses most
parts of PyMySQL . aiomysql tries to be like awesome aiopg library and
preserve same api, look and feel.

Internally aiomysql is copy of PyMySQL, underlying io calls switched
to async, basically yield from and asyncio.coroutine added in
proper places)). sqlalchemy support ported from aiopg.

## Documentation

https://aiomysql.readthedocs.io/

## Basic Example

aiomysql based on PyMySQL , and provides same api, you just need
to use await conn.f() or yield from conn.f() instead of calling
conn.f() for every method.

Properties are unchanged, so conn.prop is correct as well as
conn.prop = val.

```
import asyncio
import aiomysql

async def test_example():
    async with aiomysql.create_pool(host='127.0.0.1', port=3306,
                                    user='root', password='',
                                    db='mysql') as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 42;")
                print(cur.description)
                (r,) = await cur.fetchone()
                assert r == 42

asyncio.run(test_example())
```

## Example of SQLAlchemy optional integration

Sqlalchemy support has been ported from aiopg so api should be very familiar
for aiopg user.:

```
import asyncio
import sqlalchemy as sa

from aiomysql.sa import create_engine

metadata = sa.MetaData()

tbl = sa.Table('tbl', metadata,
               sa.Column('id', sa.Integer, primary_key=True),
               sa.Column('val', sa.String(255)))

async def go():
    engine = await create_engine(user='root', db='test_pymysql',
                                 host='127.0.0.1', password='')
    async with engine.acquire() as conn:
        await conn.execute(tbl.insert().values(val='abc'))
        await conn.execute(tbl.insert().values(val='xyz'))

        async for row in conn.execute(tbl.select()):
            print(row.id, row.val)

    engine.close()
    await engine.wait_closed()

asyncio.run(go())
```

## Requirements

- Python 3.9+
- PyMySQL
