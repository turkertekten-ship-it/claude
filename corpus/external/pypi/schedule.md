---
date: 2024-05-25T18:41:59+0000
source: https://pypi.org/project/schedule/
---
[image: https://github.com/dbader/schedule/workflows/Tests/badge.svg] [image: https://coveralls.io/repos/dbader/schedule/badge.svg?branch=master] [image: https://img.shields.io/pypi/v/schedule.svg]

Python job scheduling for humans. Run Python functions (or any other callable) periodically using a friendly syntax.

- A simple to use API for scheduling jobs, made for humans.
- In-process scheduler for periodic jobs. No extra processes needed!
- Very lightweight and no external dependencies.
- Excellent test coverage.
- Tested on Python and 3.7, 3.8, 3.9, 3.10, 3.11, 3.12

## Usage

```
$ pip install schedule
```

```
import schedule
import time

def job():
    print("I'm working...")

schedule.every(10).seconds.do(job)
schedule.every(10).minutes.do(job)
schedule.every().hour.do(job)
schedule.every().day.at("10:30").do(job)
schedule.every(5).to(10).minutes.do(job)
schedule.every().monday.do(job)
schedule.every().wednesday.at("13:15").do(job)
schedule.every().day.at("12:42", "Europe/Amsterdam").do(job)
schedule.every().minute.at(":17").do(job)

def job_with_argument(name):
    print(f"I am {name}")

schedule.every(10).seconds.do(job_with_argument, name="Peter")

while True:
    schedule.run_pending()
    time.sleep(1)
```

## Documentation

Schedule’s documentation lives at schedule.readthedocs.io.

## Meta

Daniel Bader - @dbader_org - mail@dbader.org

Inspired by Adam Wiggins’ article “Rethinking Cron” and the clockwork Ruby module.

Distributed under the MIT license. See LICENSE.txt for more information.

https://github.com/dbader/schedule
