---
date: 2026-08-11T00:33:40+0000
source: https://pypi.org/project/trio/
---
[image: Join chatroom] [image: Join forum] [image: Documentation] [image: Latest PyPi version] [image: Latest conda-forge version] [image: Test coverage]

## Trio – a friendly Python library for async concurrency and I/O

 [image: https://raw.githubusercontent.com/python-trio/trio/9b0bec646a31e0d0f67b8b6ecc6939726faf3e17/logo/logo-with-background.svg]

The Trio project aims to produce a production-quality,
permissively licensed,
async/await-native I/O library for Python. Like all async libraries,
its main purpose is to help you write programs that do multiple
things at the same time with parallelized I/O. A web spider that
wants to fetch lots of pages in parallel, a web server that needs to
juggle lots of downloads and websocket connections simultaneously, a
process supervisor monitoring multiple subprocesses… that sort of
thing. Compared to other libraries, Trio attempts to distinguish
itself with an obsessive focus on usability and
correctness. Concurrency is complicated; we try to make it easy
to get things right.

Trio was built from the ground up to take advantage of the latest
Python features, and
draws inspiration from many sources, in
particular Dave Beazley’s Curio.
The resulting design is radically simpler than older competitors like
asyncio and
Twisted, yet just as capable. Trio is
the Python I/O library I always wanted; I find it makes building
I/O-oriented programs easier, less error-prone, and just plain more
fun. Perhaps you’ll find the same.

Trio is a mature and well-tested project: the overall design is solid,
and the existing features are fully documented and widely used in
production. While we occasionally make minor interface adjustments,
breaking changes are rare. We encourage you to use Trio with confidence,
but if you rely on long-term API stability, consider subscribing to
issue #1 for advance
notice of any compatibility updates.

### Where to next?

I want to try it out! Awesome! We have a friendly tutorial to get you
started; no prior experience with async coding is required.

Ugh, I don’t want to read all that – show me some code! If you’re
impatient, then here’s a simple concurrency example,
an echo client,
and an echo server.

How does Trio make programs easier to read and reason about than
competing approaches? Trio is based on a new way of thinking that we
call “structured concurrency”. The best theoretical introduction is
the article Notes on structured concurrency, or: Go statement
considered harmful.
Or, check out this talk at PyCon 2018 to see a
demonstration of implementing the “Happy Eyeballs” algorithm in an
older library versus Trio.

Cool, but will it work on my system? Probably! As long as you have
some kind of Python 3.10-or-better (CPython or currently maintained versions of
PyPy3
are both fine), and are using Linux, macOS, Windows, or FreeBSD, then Trio
will work. Other environments might work too, but those
are the ones we test on. And all of our dependencies are pure Python,
except for CFFI on Windows, which has wheels available, so
installation should be easy (no C compiler needed).

I tried it, but it’s not working. Sorry to hear that! You can try
asking for help in our chat room or forum, filing a bug, or posting a
question on StackOverflow,
and we’ll do our best to help you out.

Trio is awesome, and I want to help make it more awesome! You’re
the best! There’s tons of work to do – filling in missing
functionality, building up an ecosystem of Trio-using libraries,
usability testing (e.g., maybe try teaching yourself or a friend to
use Trio and make a list of every error message you hit and place
where you got confused?), improving the docs, … check out our guide
for contributors!

I don’t have any immediate plans to use it, but I love geeking out
about I/O library design! That’s a little weird? But let’s be
honest, you’ll fit in great around here. We have a whole sub-forum
for discussing structured concurrency (developers
of other systems welcome!). Or check out our discussion of design
choices,
reading list, and
issues tagged design-discussion.

I want to make sure my company’s lawyers won’t get angry at me! No
worries, Trio is permissively licensed under your choice of MIT or
Apache 2. See LICENSE for details.

### Code of conduct

Contributors are requested to follow our code of conduct in all
project spaces.
