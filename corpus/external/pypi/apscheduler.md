[image: Build Status] [image: Code Coverage] [image: Documentation]

Advanced Python Scheduler (APScheduler) is a Python library that lets you schedule your Python code
to be executed later, either just once or periodically. You can add new jobs or remove old ones on
the fly as you please. If you store your jobs in a database, they will also survive scheduler
restarts and maintain their state. When the scheduler is restarted, it will then run all the jobs
it should have run while it was offline [1].

Among other things, APScheduler can be used as a cross-platform, application specific replacement
to platform specific schedulers, such as the cron daemon or the Windows task scheduler. Please
note, however, that APScheduler is not a daemon or service itself, nor does it come with any
command line tools. It is primarily meant to be run inside existing applications. That said,
APScheduler does provide some building blocks for you to build a scheduler service or to run a
dedicated scheduler process.

APScheduler has three built-in scheduling systems you can use:

- Cron-style scheduling (with optional start/end times)
- Interval-based execution (runs jobs on even intervals, with optional start/end times)
- One-off delayed execution (runs jobs once, on a set date/time)

You can mix and match scheduling systems and the backends where the jobs are stored any way you
like. Supported backends for storing jobs include:

- Memory
- SQLAlchemy (any RDBMS supported by SQLAlchemy works)
- MongoDB
- Redis
- RethinkDB
- ZooKeeper
- Etcd

APScheduler also integrates with several common Python frameworks, like:

- asyncio (PEP 3156)
- gevent
- Tornado
- Twisted
- Qt (using either
PyQt ,
PySide6 ,
PySide2 or
PySide)

There are third party solutions for integrating APScheduler with other frameworks:

- Django
- Flask

## Documentation

Documentation can be found here.

## Source

The source can be browsed at Github.

## Reporting bugs

A bug tracker is provided by Github.

## Getting help

If you have problems or other questions, you can either:

- Ask in the apscheduler room on Gitter
- Ask on the APScheduler GitHub discussion forum, or
- Ask on StackOverflow and tag your
question with the apscheduler tag
