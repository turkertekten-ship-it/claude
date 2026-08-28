---
date: 2024-11-01T14:06:24+0000
source: https://pypi.org/project/watchdog/
---
[image: PyPI Version] [image: PyPI Status] [image: PyPI Python Versions] [image: Github Build Status] [image: GitHub License]

Python API and shell utilities to monitor file system events.

Works on 3.9+.

## Example API Usage

A simple program that uses watchdog to monitor directories specified
as command-line arguments and logs events generated:

```
import time

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

class MyEventHandler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent) -> None:
        print(event)

event_handler = MyEventHandler()
observer = Observer()
observer.schedule(event_handler, ".", recursive=True)
observer.start()
try:
    while True:
        time.sleep(1)
finally:
    observer.stop()
    observer.join()
```

## Shell Utilities

Watchdog comes with an optional utility script called watchmedo.
Please type watchmedo --help at the shell prompt to
know more about this tool.

Here is how you can log the current directory recursively
for events related only to *.py and *.txt files while
ignoring all directory events:

```
watchmedo log \
    --patterns='*.py;*.txt' \
    --ignore-directories \
    --recursive \
    --verbose \
    .
```

You can use the shell-command subcommand to execute shell commands in
response to events:

```
watchmedo shell-command \
    --patterns='*.py;*.txt' \
    --recursive \
    --command='echo "${watch_src_path}"' \
    .
```

Please see the help information for these commands by typing:

```
watchmedo [command] --help
```

### About watchmedo Tricks

watchmedo can read tricks.yaml files and execute tricks within them in
response to file system events. Tricks are actually event handlers that
subclass watchdog.tricks.Trick and are written by plugin authors. Trick
classes are augmented with a few additional features that regular event handlers
don’t need.

An example tricks.yaml file:

```
tricks:
- watchdog.tricks.LoggerTrick:
    patterns: ["*.py", "*.js"]
- watchmedo_webtricks.GoogleClosureTrick:
    patterns: ['*.js']
    hash_names: true
    mappings_format: json                  # json|yaml|python
    mappings_module: app/javascript_mappings
    suffix: .min.js
    compilation_level: advanced            # simple|advanced
    source_directory: app/static/js/
    destination_directory: app/public/js/
    files:
      index-page:
      - app/static/js/vendor/jquery*.js
      - app/static/js/base.js
      - app/static/js/index-page.js
      about-page:
      - app/static/js/vendor/jquery*.js
      - app/static/js/base.js
      - app/static/js/about-page/**/*.js
```

The directory containing the tricks.yaml file will be monitored. Each trick
class is initialized with its corresponding keys in the tricks.yaml file as
arguments and events are fed to an instance of this class as they arrive.

## Installation

Install from PyPI using pip:

```
$ python -m pip install -U watchdog

# or to install the watchmedo utility:
$ python -m pip install -U 'watchdog[watchmedo]'
```

Install from source:

```
$ python -m pip install -e .

# or to install the watchmedo utility:
$ python -m pip install -e '.[watchmedo]'
```

## Documentation

You can browse the latest release documentation online.

## Contribute

Fork the repository on GitHub and send a pull request, or file an issue
ticket at the issue tracker. For general help and questions use
stackoverflow with tag python-watchdog.

Create and activate your virtual environment, then:

```
python -m pip install tox
python -m tox [-q] [-e ENV]
```

If you are making a substantial change, add an entry to the “Unreleased” section
of the changelog.

## Supported Platforms

- Linux 2.6 (inotify)
- macOS (FSEvents, kqueue)
- FreeBSD/BSD (kqueue)
- Windows (ReadDirectoryChangesW with I/O completion ports;
ReadDirectoryChangesW worker threads)
- OS-independent (polling the disk for directory snapshots and comparing them
periodically; slow and not recommended)

Note that when using watchdog with kqueue, you need the
number of file descriptors allowed to be opened by programs
running on your system to be increased to more than the
number of files that you will be monitoring. The easiest way
to do that is to edit your ~/.profile file and add
a line similar to:

```
ulimit -n 1024
```

This is an inherent problem with kqueue because it uses
file descriptors to monitor files. That plus the enormous
amount of bookkeeping that watchdog needs to do in order
to monitor file descriptors just makes this a painful way
to monitor files and directories. In essence, kqueue is
not a very scalable way to monitor a deeply nested
directory of files and directories with a large number of
files.

## About using watchdog with editors like Vim

Vim does not modify files unless directed to do so.
It creates backup files and then swaps them in to replace
the files you are editing on the disk. This means that
if you use Vim to edit your files, the on-modified events
for those files will not be triggered by watchdog.
You may need to configure Vim appropriately to disable
this feature.

## About using watchdog with CIFS

When you want to watch changes in CIFS, you need to explicitly tell watchdog to
use PollingObserver, that is, instead of letting watchdog decide an
appropriate observer like in the example above, do:

```
from watchdog.observers.polling import PollingObserver as Observer
```

## Dependencies

1. Python 3.9 or above.
1. XCode (only on macOS when installing from sources)
1. PyYAML (only for watchmedo)

## Licensing

Watchdog is licensed under the terms of the Apache License, version 2.0.

- Copyright 2018-2024 Mickaël Schoentgen & contributors
- Copyright 2014-2018 Thomas Amland & contributors
- Copyright 2012-2014 Google, Inc.
- Copyright 2011-2012 Yesudeep Mangalapilly

Project source code is available at Github. Please report bugs and file
enhancement requests at the issue tracker.

## Why Watchdog?

Too many people tried to do the same thing and none did what I needed Python
to do:

- pnotify
- unison fsmonitor
- fsmonitor
- guard
- pyinotify
- inotify-tools
- jnotify
- treewatcher
- file.monitor
- pyfilesystem

## Changelog

### 6.0.0

2024-11-01 • full history

- Pin test dependecies.
- [docs] Add typing info to quick start. (#1082)
- [inotify] Use of select.poll() instead of deprecated select.select(), if available. (#1078)
- [inotify] Fix reading inotify file descriptor after closing it. (#1081)
- [utils] The stop_signal keyword-argument type of the AutoRestartTrick class can now be either a signal.Signals or an int.
- [utils] Added the __repr__() method to the Trick class.
- [utils] Removed the unused echo_class() function from the echo module.
- [utils] Removed the unused echo_instancemethod() function from the echo module.
- [utils] Removed the unused echo_module() function from the echo module.
- [utils] Removed the unused is_class_private_name() function from the echo module.
- [utils] Removed the unused is_classmethod() function from the echo module.
- [utils] Removed the unused ic_method(met() function from the echo module.
- [utils] Removed the unused method_name() function from the echo module.
- [utils] Removed the unused name() function from the echo module.
- [watchmedo] Fixed Mypy issues.
- [watchmedo] Added the __repr__() method to the HelpFormatter class.
- [watchmedo] Removed the --trace CLI argument from the watchmedo log command, useless since events are logged by default at the LoggerTrick class level.
- [windows] Fixed Mypy issues.
- Thanks to our beloved contributors: @BoboTiG, @g-pichlern, @ethan-vanderheijden, @nhairs

### 5.0.3

2024-09-27 • full history

- [inotify] Improve cleaning up Inotify threads, and add eventlet test cases (#1070)
- Thanks to our beloved contributors: @BoboTiG, @ethan-vanderheijden

### 5.0.2

2024-09-03 • full history

- Enable OS specific Mypy checks (#1064)
- [watchmedo] Fix tricks argument type of schedule_tricks() (#1063)
- Thanks to our beloved contributors: @gnought, @BoboTiG

### 5.0.1

2024-09-02 • full history

- [kqueue] Fix TypeError: kqueue.control() only accepts positional parameters (#1062)
- Thanks to our beloved contributors: @apoirier, @BoboTiG

### 5.0.0

2024-08-26 • full history

Breaking Changes

- Drop support for Python 3.8 (#1055)
- [core] Enforced usage of proper keyword-arguments (#1057)
- [core] Renamed the BaseObserverSubclassCallable class to ObserverType (#1055)
- [inotify] Renamed the inotify_event_struct class to InotifyEventStruct (#1055)
- [inotify] Renamed the UnsupportedLibc exception to UnsupportedLibcError (#1057)
- [inotify] Removed the InotifyConstants.IN_CLOSE constant (#1046)
- [watchmedo] Renamed the LogLevelException exception to LogLevelError (#1057)
- [watchmedo] Renamed the WatchdogShutdown exception to WatchdogShutdownError (#1057)
- [windows] Renamed the FILE_NOTIFY_INFORMATION class to FileNotifyInformation (#1055)
- [windows] Removed the unused WATCHDOG_TRAVERSE_MOVED_DIR_DELAY constant (#1057)

Other Changes

- [core] Enable disallow_untyped_calls Mypy rule (#1055)
- [core] Enable disallow_untyped_defs Mypy rule (#1060)
- [core] Improve typing references for events (#1040)
- [inotify] Add support for IN_CLOSE_NOWRITE events. A FileClosedNoWriteEvent event will be fired, and its on_closed_no_write() dispatcher has been introduced (#1046)
- Thanks to our beloved contributors: @BoboTiG

### 4.0.2

2024-08-11 • full history

- Add support for Python 3.13 (#1052)
- [core] Run ruff, apply several fixes (#1033)
- [core] Remove execution rights from events.py
- [documentation] Update PatternMatchingEventHandler docstrings (#1048)
- [documentation] Simplify the quickstart example (#1047)
- [fsevents] Add missing event_filter keyword-argument to FSEventsObserver.schedule() (#1049)
- [utils] Fix a possible race condition in AutoRestartTrick (#1002)
- [watchmedo] Remove execution rights from watchmedo.py
- Thanks to our beloved contributors: @BoboTiG, @nbelakovski, @ivg

### 4.0.1

2024-05-23 • full history

- [inotify] Fix missing event_filter for the full emitter (#1032)
- Thanks to our beloved contributors: @mraspaud, @BoboTiG

### 4.0.0

2024-02-06 • full history

- Drop support for Python 3.7.
- Add support for Python 3.12.
- [snapshot] Add typing to dirsnapshot (#1012)
- [snapshot] Added DirectorySnapshotDiff.ContextManager (#1011)
- [events] FileSystemEvent, and subclasses, are now dataclass``es, and their ``repr() has changed
- [windows] WinAPINativeEvent is now a dataclass, and its repr() has changed
- [events] Log FileOpenedEvent, and FileClosedEvent, events in LoggingEventHandler
- [tests] Improve FileSystemEvent coverage
- [watchmedo] Log all events in LoggerTrick
- [windows] The observers.read_directory_changes.WATCHDOG_TRAVERSE_MOVED_DIR_DELAY hack was removed. The constant will be kept to prevent breaking other softwares.
- Thanks to our beloved contributors: @BoboTiG, @msabramo

### 3.0.0

2023-03-20 • full history

- Drop support for Python 3.6.
- watchdog is now PEP 561 compatible, and tested with mypy
- Fix missing > in FileSystemEvent.__repr__() (#980)
- [ci] Lots of improvements
- [inotify] Return from InotifyEmitter.queue_events() if not launched when thread is inactive (#963)
- [tests] Stability improvements
- [utils] Remove handling of threading.Event.isSet spelling (#962)
- [watchmedo] Fixed tricks YAML generation (#965)
- Thanks to our beloved contributors: @kurtmckee, @altendky, @agroszer, @BoboTiG

### 2.3.1

2023-02-28 • full history

- Run black on the entire source code
- Bundle the requirements-tests.txt file in the source distribution (#939)
- [watchmedo] Exclude FileOpenedEvent events from AutoRestartTrick, and ShellCommandTrick, to restore watchdog < 2.3.0 behavior. A better solution should be found in the future. (#949)
- [watchmedo] Log FileOpenedEvent, and FileClosedEvent, events in LoggerTrick
- Thanks to our beloved contributors: @BoboTiG

### 2.3.0

2023-02-23 • full history

- [inotify] Add support for IN_OPEN events: a FileOpenedEvent event will be fired (#941)
- [watchmedo] Add optional event debouncing for auto-restart, only restarting once if many events happen in quick succession (--debounce-interval) (#940)
- [watchmedo] Exit gracefully on KeyboardInterrupt exception (Ctrl+C) (#945)
- [watchmedo] Add option to not auto-restart the command after it exits (--no-restart-on-command-exit) (#946)
- Thanks to our beloved contributors: @BoboTiG, @dstaple, @taleinat, @cernekj

### 2.2.1

2023-01-01 • full history

- Enable mypy to discover type hints as specified in PEP 561 (#933)
- [ci] Set the expected Python version when building release files
- [ci] Update actions versions in use
- [watchmedo] [regression] Fix usage of missing signal.SIGHUP attribute on non-Unix OSes (#935)
- Thanks to our beloved contributors: @BoboTiG, @simon04, @piotrpdev

### 2.2.0

2022-12-05 • full history

- [build] Wheels are now available for Python 3.11 (#932)
- [documentation] HTML documentation builds are now tested for errors (#902)
- [documentation] Fix typos here, and there (#910)
- [fsevents2] The fsevents2 observer is now deprecated (#909)
- [tests] The error message returned by musl libc for error code -1 is now allowed (#923)
- [utils] Remove unnecessary code in dirsnapshot.py (#930)
- [watchmedo] Handle shutdown events from SIGHUP (#912)
- Thanks to our beloved contributors: @kurtmckee, @babymastodon, @QuantumEnergyE, @timgates42, @BoboTiG

### 2.1.9

2022-06-10 • full history

- [fsevents] Fix flakey test to assert that there are no errors when stopping the emitter.
- [inotify] Suppress occasional OSError: [Errno 9] Bad file descriptor at shutdown. (#805)
- [watchmedo] Make auto-restart restart the sub-process if it terminates. (#896)
- [watchmedo] Avoid zombie sub-processes when running shell-command without --wait. (#405)
- Thanks to our beloved contributors: @samschott, @taleinat, @altendky, @BoboTiG

### 2.1.8

2022-05-15 • full history

- Fix adding failed emitters on observer schedule. (#872)
- [inotify] Fix hang when unscheduling watch on a path in an unmounted filesystem. (#869)
- [watchmedo] Fix broken parsing of --kill-after argument for the auto-restart command. (#870)
- [watchmedo] Fix broken parsing of boolean arguments. (#887)
- [watchmedo] Fix broken parsing of commands from auto-restart, and shell-command. (#888)
- [watchmedo] Support setting verbosity level via -q/--quiet and -v/--verbose arguments. (#889)
- Thanks to our beloved contributors: @taleinat, @kianmeng, @palfrey, @IlayRosenberg, @BoboTiG

### 2.1.7

2022-03-25 • full history

- Eliminate timeout in waiting on event queue. (#861)
- [inotify] Fix not equality implementation for InotifyEvent. (#848)
- [watchmedo] Fix calling commands from within a Python script. (#879)
- [watchmedo] PyYAML is loaded only when strictly necessary. Simple usages of watchmedo are possible without the module being installed. (#847)
- Thanks to our beloved contributors: @sattlerc, @JanzenLiu, @BoboTiG

### 2.1.6

2021-10-01 • full history

- [bsd] Fixed returned paths in kqueue.py and restored the overall results of the test suite. (#842)
- [bsd] Updated FreeBSD CI support .(#841)
- [watchmedo] Removed the argh dependency in favor of the builtin argparse module. (#836)
- [watchmedo] Removed unexistant WindowsApiAsyncObserver references and --debug-force-winapi-async arguments.
- [watchmedo] Improved the help output.
- Thanks to our beloved contributors: @knobix, @AndreaRe9, @BoboTiG

### 2.1.5

2021-08-23 • full history

- Fix regression introduced in 2.1.4 (reverted “Allow overriding or adding custom event handlers to event dispatch map. (#814)”). (#830)
- Convert regexes of type str to list. (831)
- Thanks to our beloved contributors: @unique1o1, @BoboTiG

### 2.1.4

2021-08-19 • full history

- [watchmedo] Fix usage of os.setsid() and os.killpg() Unix-only functions. (#809)
- [mac] Fix missing FileModifiedEvent on permission or ownership changes of a file. (#815)
- [mac] Convert absolute watch path in FSEeventsEmitter with os.path.realpath(). (#822)
- Fix a possible AttributeError in SkipRepeatsQueue._put(). (#818)
- Allow overriding or adding custom event handlers to event dispatch map. (#814)
- Fix tests on big endian platforms. (#828)
- Thanks to our beloved contributors: @replabrobin, @BoboTiG, @SamSchott, @AndreiB97, @NiklasRosenstein, @ikokollari, @mgorny

### 2.1.3

2021-06-26 • full history

- Publish macOS arm64 and universal2 wheels. (#740)
- Thanks to our beloved contributors: @kainjow, @BoboTiG

### 2.1.2

2021-05-19 • full history

- [mac] Fix relative path handling for non-recursive watch. (#797)
- [windows] On PyPy, events happening right after start() were missed. Add a workaround for that. (#796)
- Thanks to our beloved contributors: @oprypin, @CCP-Aporia, @BoboTiG

### 2.1.1

2021-05-10 • full history

- [mac] Fix callback exceptions when the watcher is deleted but still receiving events (#786)
- Thanks to our beloved contributors: @rom1win, @BoboTiG, @CCP-Aporia

### 2.1.0

2021-05-04 • full history

- [inotify] Simplify libc loading (#776)
- [mac] Add support for non-recursive watches in FSEventsEmitter (#779)
- [watchmedo] Add support for --debug-force-* arguments to tricks (#781)
- Thanks to our beloved contributors: @CCP-Aporia, @aodj, @UnitedMarsupials, @BoboTiG

### 2.0.3

2021-04-22 • full history

- [mac] Use logger.debug() instead of logger.info() (#774)
- Updated documentation links (#777)
- Thanks to our beloved contributors: @globau, @imba-tjd, @BoboTiG

### 2.0.2

2021-02-22 • full history

- [mac] Add missing exception objects (#766)
- Thanks to our beloved contributors: @CCP-Aporia, @BoboTiG

### 2.0.1

2021-02-17 • full history

- [mac] Fix a segmentation fault when dealing with unicode paths (#763)
- Moved the CI from Travis-CI to GitHub Actions (#764)
- Thanks to our beloved contributors: @SamSchott, @BoboTiG

### 2.0.0

2021-02-11 • full history

- Avoid deprecated PyEval_InitThreads on Python 3.7+ (#746)
- [inotify] Add support for IN_CLOSE_WRITE events. A FileCloseEvent event will be fired. Note that IN_CLOSE_NOWRITE events are not handled to prevent much noise. (#184, #245, #280, #313, #690)
- [inotify] Allow to stop the emitter multiple times (#760)
- [mac] Support coalesced filesystem events (#734)
- [mac] Drop support for macOS 10.12 and earlier (#750)
- [mac] Fix an issue when renaming an item changes only the casing (#750)
- Thanks to our beloved contributors: @bstaletic, @lukassup, @ysard, @SamSchott, @CCP-Aporia, @BoboTiG

### 1.0.2

2020-12-18 • full history

- Wheels are published for GNU/Linux, macOS and Windows (#739)
- [mac] Fix missing event_id attribute in fsevents (#721)
- [mac] Return byte paths if a byte path was given in fsevents (#726)
- [mac] Add compatibility with old macOS versions (#733)
- Uniformize event for deletion of watched dir (#727)
- Thanks to our beloved contributors: @SamSchott, @CCP-Aporia, @di, @BoboTiG

### 1.0.1

2020-12-10 • Fix version with good metadatas.

### 1.0.0

2020-12-10 • full history

- Versioning is now following the semver
- Drop support for Python 2.7, 3.4 and 3.5
- [mac] Regression fixes for native fsevents (#717)
- [windows] winapi.BUFFER_SIZE now defaults to 64000 (instead of 2048) (#700)
- [windows] Introduced winapi.PATH_BUFFER_SIZE (defaults to 2048) to keep the old behavior with path-realted functions (#700)
- Use pathlib from the standard library, instead of pathtools (#556)
- Allow file paths on Unix that don’t follow the file system encoding (#703)
- Removed the long-time deprecated events.LoggingFileSystemEventHandler class, use LoggingEventHandler instead
- Thanks to our beloved contributors: @SamSchott, @bstaletic, @BoboTiG, @CCP-Aporia

### 0.10.4

2020-11-21 • full history

- Add logger parameter for the LoggingEventHandler (#676)
- Replace mutable default arguments with if None implementation (#677)
- Expand tests to Python 2.7 and 3.5-3.10 for GNU/Linux, macOS and Windows
- [mac] Performance improvements for the fsevents module (#680)
- [mac] Prevent compilation of watchdog_fsevents.c on non-macOS machines (#687)
- [watchmedo] Handle shutdown events from SIGTERM and SIGINT more reliably (#693)
- Thanks to our beloved contributors: @Sraw, @CCP-Aporia, @BoboTiG, @maybe-sybr

### 0.10.3

2020-06-25 • full history

- Ensure ObservedWatch.path is a string (#651)
- [inotify] Allow to monitor single file (#655)
- [inotify] Prevent raising an exception when a file in a monitored folder has no permissions (#669, #670)
- Thanks to our beloved contributors: @brant-ruan, @rec, @andfoy, @BoboTiG

### 0.10.2

2020-02-08 • full history

- Fixed the build_ext command on macOS Catalina (#628)
- Fixed the installation of macOS requirements on non-macOS OSes (#635)
- Refactored dispatch() method of FileSystemEventHandler,
PatternMatchingEventHandler and RegexMatchingEventHandler
- [bsd] Improved tests support on non Windows/Linux platforms (#633, #639)
- [bsd] Added FreeBSD CI support (#532)
- [bsd] Restored full support (#638, #641)
- Thanks to our beloved contributors: @BoboTiG, @evilham, @danilobellini

### 0.10.1

2020-01-30 • full history

- Fixed Python 2.7 to 3.6 installation when the OS locale is set to POSIX (#615)
- Fixed the build_ext command on macOS (#618, #620)
- Moved requirements to setup.cfg (#617)
- [mac] Removed old C code for Python 2.5 in the fsevents C implementation
- [snapshot] Added EmptyDirectorySnapshot (#613)
- Thanks to our beloved contributors: @Ajordat, @tehkirill, @BoboTiG

### 0.10.0

2020-01-26 • full history

Breaking Changes

- Dropped support for Python 2.6, 3.2 and 3.3
- Emitters that failed to start are now removed
- [snapshot] Removed the deprecated walker_callback argument,
use stat instead
- [watchmedo] The utility is no more installed by default but via the extra
watchdog[watchmedo]

Other Changes

- Fixed several Python 3 warnings
- Identify synthesized events with is_synthetic attribute (#369)
- Use os.scandir() to improve memory usage (#503)
- [bsd] Fixed flavors of FreeBSD detection (#529)
- [bsd] Skip unprocessable socket files (#509)
- [inotify] Fixed events containing non-ASCII characters (#516)
- [inotify] Fixed the way OSError are re-raised (#377)
- [inotify] Fixed wrong source path after renaming a top level folder (#515)
- [inotify] Removed delay from non-move events (#477)
- [mac] Fixed a bug when calling FSEventsEmitter.stop() twice (#466)
- [mac] Support for unscheduling deleted watch (#541)
- [mac] Fixed missing field initializers and unused parameters in
watchdog_fsevents.c
- [snapshot] Don’t walk directories without read permissions (#408)
- [snapshot] Fixed a race condition crash when a directory is swapped for a file (#513)
- [snasphot] Fixed an AttributeError about forgotten path_for_inode attr (#436)
- [snasphot] Added the ignore_device=False parameter to the ctor (597)
- [watchmedo] Fixed the path separator used (#478)
- [watchmedo] Fixed the use of yaml.load() for yaml.safe_load() (#453)
- [watchmedo] Handle all available signals (#549)
- [watchmedo] Added the --debug-force-polling argument (#404)
- [windows] Fixed issues when the observed directory is deleted (#570 and #601)
- [windows] WindowsApiEmitter made easier to subclass (#344)
- [windows] Use separate ctypes DLL instances
- [windows] Generate sub created events only if recursive=True (#454)
- Thanks to our beloved contributors: @BoboTiG, @LKleinNux, @rrzaripov,
@wildmichael, @TauPan, @segevfiner, @petrblahos, @QuantumEnergyE,
@jeffwidman, @kapsh, @nickoala, @petrblahos, @julianolf, @tonybaloney,
@mbakiev, @pR0Ps, javaguirre, @skurfer, @exarkun, @joshuaskelly,
@danilobellini, @Ajordat

### 0.9.0

2018-08-28 • full history

- Deleting the observed directory now emits a DirDeletedEvent event
- [bsd] Improved the platform detection (#378)
- [inotify] Fixed a crash when the root directory being watched by was deleted (#374)
- [inotify] Handle systems providing uClibc
- [linux] Fixed a possible DirDeletedEvent duplication when
deleting a directory
- [mac] Fixed unicode path handling fsevents2.py (#298)
- [watchmedo] Added the --debug-force-polling argument (#336)
- [windows] Fixed the FILE_LIST_DIRECTORY constant (#376)
- Thanks to our beloved contributors: @vulpeszerda, @hpk42, @tamland, @senden9,
@gorakhargosh, @nolsto, @mafrosis, @DonyorM, @anthrotype, @danilobellini,
@pierregr, @ShinNoNoir, @adrpar, @gforcada, @pR0Ps, @yegorich, @dhke

### 0.8.3

2015-02-11 • full history

- Fixed the use of the root logger (#274)
- [inotify] Refactored libc loading and improved error handling in
inotify_c.py
- [inotify] Fixed a possible unbound local error in inotify_c.py
- Thanks to our beloved contributors: @mmorearty, @tamland, @tony,
@gorakhargosh

### 0.8.2

2014-10-29 • full history

- Event emitters are no longer started on schedule if Observer is not
already running
- [mac] Fixed usued arguments to pass clang compilation (#265)
- [snapshot] Fixed a possible race condition crash on directory deletion (#281)
- [windows] Fixed an error when watching the same folder again (#270)
- Thanks to our beloved contributors: @tamland, @apetrone, @Falldog,
@theospears

### 0.8.1

2014-07-28 • full history

- Fixed anon_inode descriptors leakage (#249)
- [inotify] Fixed thread stop dead lock (#250)
- Thanks to our beloved contributors: @Witos, @adiroiban, @tamland

### 0.8.0

2014-07-02 • full history

- Fixed argh deprecation warnings (#242)
- [snapshot] Methods returning internal stats info were replaced by
mtime(), inode() and path() methods
- [snapshot] Deprecated the walker_callback argument
- [watchmedo] Fixed auto-restart to terminate all children processes (#225)
- [watchmedo] Added the --no-parallel argument (#227)
- [windows] Fixed the value of INVALID_HANDLE_VALUE (#123)
- [windows] Fixed octal usages to work with Python 3 as well (#223)
- Thanks to our beloved contributors: @tamland, @Ormod, @berdario, @cro,
@BernieSumption, @pypingou, @gotcha, @tommorris, @frewsxcv
