---
date: 2026-06-06T07:33:38+0000
source: https://pypi.org/project/structlog/
---
[image: structlog mascot]

structlog is the production-ready logging solution for Python:

- Simple: Everything is about functions that take and return dictionaries – all hidden behind familiar APIs.
- Powerful: Functions and dictionaries aren’t just simple but also powerful.
structlog leaves you in control.
- Fast: structlog is not hamstrung by designs of yore.
Its flexibility comes not at the price of performance.

Thanks to its flexible design, you choose whether you want structlog to take care of the output of your log entries or whether you prefer to forward them to an existing logging system like the standard library's logging module.

The output format is just as flexible and structlog comes with support for JSON, logfmt, as well as pretty console output out-of-the-box:

[image: Screenshot of colorful structlog output with ConsoleRenderer]

## Sponsors

structlog would not be possible without our amazing sponsors.
Especially those generously supporting us at the The Organization tier and higher:

Please consider joining them to help make structlog’s maintenance more sustainable!

## Introduction

structlog has been successfully used in production at every scale since 2013, while embracing cutting-edge technologies like asyncio, context variables, or type hints as they emerged.
Its paradigms proved influential enough to help design structured logging packages across ecosystems.

## Project Links

- Get Help (use the structlog tag on Stack Overflow)
- PyPI
- GitHub
- Documentation
- Changelog
- Third-party Extensions

## structlog for Enterprise

Available as part of the Tidelift Subscription.

The maintainers of structlog and thousands of other packages are working with Tidelift to deliver commercial support and maintenance for the open source packages you use to build your applications.
Save time, reduce risk, and improve code health, while paying the maintainers of the exact packages you use.

## Release Information

### Removed

- Python 3.8 and 3.9 support.

### Deprecated

- Support for better-exceptions is deprecated and will be removed within a year.
Use our Rich integration or copy-paste the one line of code you need.
#802

### Added

- Python 3.15 support.
#813
- structlog.dev.rich_monochrome_traceback for Rich-based monochrome exception rendering and add support for it throughout structlog.dev.ConsoleRenderer when the user asks for no colors.
#794
- structlog.BytesLogger now has a name attribute which allows you to use it with the structlog.stdlib.add_logger_name() processor without using the standard library integration.
#786
- structlog.processors.CallsiteParameterAdder now supports CallsiteParameter.QUAL_MODULE that adds the qualified import name of the module of the callsite, or __main__ if the module is the entry point.
This is only available for structlog-originated events since the standard library has no equivalent (except for the convention of setting the logger's name to __name__).
#812
- structlog.stdlib.BoundLogger now has is_enabled_for() and get_effective_level() methods that are snake_case aliases for its isEnabledFor() and getEffectiveLevel() methods.
This makes it more compatible with the native structlog.typing.FilteringBoundLogger, so you can swap configurations without changing your call sites.
#818

### Changed

- structlog.dev.ConsoleRenderer does not warn anymore when the exception key has a rendered value despite having a fancy formatter configured.
#790

### Fixed

- structlog.BytesLogger, structlog.PrintLogger, and structlog.WriteLogger now hold weak references to the files they use for output.
This prevents their leakage in long-running processes that open many logfiles, such as task executors that create a per-task BytesLogger or WriteLogger.
#807
- structlog.WriteLogger is usable after unpickling.
#787
- structlog.processors.CallsiteParameterAdder now reports the calling thread's id and name for async log methods, instead of the thread from the executor pool that runs the underlying sync logger.
#710 #805

---

Full Changelog →

## Credits

structlog is written and maintained by Hynek Schlawack.
The idea of bound loggers is inspired by previous work by Jean-Paul Calderone and David Reid.

The development is kindly supported by my employer Variomedia AG, structlog’s Tidelift subscribers, and all my amazing GitHub Sponsors.

The logs-loving beaver logo has been contributed by Lynn Root.
