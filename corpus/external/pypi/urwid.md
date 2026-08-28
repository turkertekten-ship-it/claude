---
date: 2026-08-25T13:59:48+0000
source: https://pypi.org/project/urwid/
---
## Urwid

[image: current version on PyPi] [image: Documentation Status] [image: Gitter] [image: CI status] [image: pre-commit] [image: test coverage]

## About

Urwid is a console user interface library for Python on Linux, OSX, Cygwin or other unix-like OS
and partially supports Windows OS (see below).

It includes many features useful for text console application developers including:

- Applications resize quickly and smoothly
- Automatic, programmable text alignment and wrapping
- Simple markup for setting text attributes within blocks of text
- Powerful list box with programmable content for scrolling all widget types
- Your choice of event loops: Twisted, Glib, Tornado, asyncio, trio, ZeroMQ or select-based loop
- Pre-built widgets include edit boxes, buttons, check boxes and radio buttons
- Display modules include raw, curses, and experimental LCD and web displays
- Support for UTF-8, simple 8-bit and CJK encodings
- 24-bit (true color), 256 color, and 88 color mode support
- Compatible with Python 3.9+ and PyPy

Home Page:

http://urwid.org/

## Installation

To install using pip

```
pip install urwid
```

For advanced functionality extra requirements need to be installed.
Example for ZeroMQ event loop and LCD display:

```
pip install urwid[serial,zmq]
```

Alternatively if you are on Debian or Ubuntu

```
apt-get install python3-urwid
```

## Windows support notes

Windows support is limited to the Windows 10+ due to ANSI support requirement.

- Not supported:

1. Terminal widget and all related render API (TermCanvas, TermCharset, TermModes, TermScroller)
1. Any file descriptors except sockets (Windows OS limitation)
1. ZMQEventLoop.

- Special requirements:

1. Extra libraries required for curses display support:

```
pip install urwid[curses]
```

- CursesDisplay incorrectly handles mouse input in case of fast actions.
- Only UTF-8 mode is supported.

## Testing

To run tests locally, install & run tox. You must have
appropriate Python versions installed to run tox for
each of them.

To test code in all Python versions:

```
tox                     # Test all versions specified in tox.ini:
tox -e py39             # Test Python 3.9 only
tox -e py39,py10,pypy3  # Test Python 3.9, Python 3.10 & pypy3
```

## Supported Python versions

- 3.9
- 3.10
- 3.11
- 3.12
- 3.13
- 3.14
- pypy3

## Authors

### Creator

wardi

### Maintainers

and3rson,
tonycpsu,
ulidtko,
penguinolog

### Contributors

1in7billion,
abadger,
agrenott,
akorb,
alethiophile,
aleufroy,
alobbs,
amjltc295,
and-semakin,
andrewshadura,
andy-z,
anttin2020,
Apteryks,
Arfrever,
AutoAwesome,
belak,
berney,
bk2204,
BkPHcgQL3V,
bwesterb,
carlos-jenkins,
Certseeds,
Chipsterjulien,
chrisspen,
cltrudeau,
Codeberg-AsGithubAlternative-buhtz,
cortesi,
d0c-s4vage,
derdon,
dholth,
dimays,
dlo,
dnaeon,
doddo,
douglas-larocca,
drestebon,
dsotr,
dwf,
EdwardBetts,
elenril,
EnricoBilla,
extempore,
fabiand,
floppym,
flowblok,
fmoreau,
goncalopp,
Gordin,
GregIngelmo,
grzaks,
gurupras,
HarveyHunt,
Hoolean,
hukka,
hydratim,
ids1024,
imrek,
isovector,
itaisod,
ixxra,
jeblair,
johndeaton,
jonblack,
jspricke,
kedder,
Kelketek,
KennethNielsen,
kesipyc,
kkrolczyk,
Kwpolska,
Lahorde,
laike9m,
larsks,
lfam,
lgbaldoni,
lighth7015,
livibetter,
Lothiraldan,
Mad-ness,
madebr,
magniff,
marlox-ouda,
mattymo,
mdtrooper,
mgk,
mimi1vx,
mobyte0,
MonAaraj,
MonthlyPython,
mountainstorm,
mselee,
mwhudson,
naquad,
nchavez324,
neumond,
nolash,
ntamas,
nyov,
ocarneiro,
okayzed,
pquentin,
rbanffy,
ReddyKilowatt,
regebro,
renegarcia,
rianhunter,
roburban,
RRMoelker,
rwarren,
scopatz,
seanhussey,
seonon,
shadedKE,
sithglan,
Sjc1000,
sporkexec,
squrky,
ssbr,
techdragon,
thehunmonkgroup,
thisch,
thornycrackers,
TomasTomecek,
tompickering,
tony,
ttanner,
tu500,
uSpike,
vega0,
vit1251,
waveform80,
Wesmania,
xandfury,
xndcn,
zhongshangwu,
zrax
