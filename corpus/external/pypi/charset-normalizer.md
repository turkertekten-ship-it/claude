# Charset Detection, for Everyone 👋

The Real First Universal Charset Detector
 [image: Download Count Total]

Featured Packages
 [image: Static Badge] [image: Static Badge]

In other language (unofficial port - by the community)
 [image: Static Badge]

> A library that helps you read text from an unknown charset encoding.
> Motivated by chardet,
> I'm trying to resolve the issue by taking a new approach.
> All IANA character set names for which the Python core library provides codecs are supported.
> You can also register your own set of codecs, and yes, it would work as-is.

This project offers you an alternative to Universal Charset Encoding Detector, also known as Chardet.

| Feature | Chardet | Charset Normalizer | cChardet |
| Fast | ✅ | ✅ | ✅ |
| Fast on large content (uncapped) | ❌ | ✅ | ❌ |
| Universal1 | ❌ | ✅ | ❌ |
| Reliable without distinguishable standards | ✅ | ✅ | ✅ |
| Reliable with distinguishable standards | ✅ | ✅ | ✅ |
| License | 0BSD2
disputed | MIT | MPL-1.1
restrictive |
| Native Python | ✅ | ✅ | ❌ |
| Detect spoken language | ✅ | ✅ | N/A |
| UnicodeDecodeError Safety | ❌ | ✅ | ❌ |
| Whl Size | ~1200 kB | ~250 kB | ~200 kB |
| Supported Encoding | 99 | 99 | 40 |
| Can register custom encoding | ❌ | ✅ | ❌ |

[image: Reading Normalized Text] [image: Cat Reading Text]

## ⚡ Performance

This package offer similar performances in general against Chardet. Expect 10X faster with large contents when you uncap Chardet max_bytes default assumption.

| Package | Accuracy | Mean per file (ms) |
| Chardet | 99 % | 0.4 ms3 0.6 ms4 |
| charset-normalizer | 98 % | 0.4 ms |
| cchardet5 | 94 % | 0.6 ms |

Well, sub-ms detectors made them extremely discrete in the overall runtime.
Competitors can still win individual measurements, especially capped Chardet on
small-file median latency. But when performance, accuracy, binary handling, validation
strength, portability, and maintainability are considered together, charset-normalizer
is the stronger package.

| Package | 99th percentile | 95th percentile | 50th percentile |
| Chardet | 2.5 ms3 4.2ms4 | 1 ms | 0.2 ms |
| charset-normalizer | 2.7 ms | 1.5 ms | 0.2 ms |
| cchardet | 2.7 ms | 2 ms | 0.3 ms |

updated as of August 2026 using CPython 3.12, Charset-Normalizer 3.5.1, and Chardet 7.5 inside a (libc Debian) container. The host CPU is a 13th gen Intel mobile CPU. We'll no longer update regularly those since the sub-ms changes aren't meaningful to anyone anymore.

> Stats are generated using 477 files using default parameters. More details on used files, see GHA workflows.
> And yes, these results might change at any time. The dataset can be updated to include more files.
> The actual delays heavily depends on your CPU capabilities. The factors should remain the same.
> Chardet claims on his documentation to have a greater accuracy than us based on the dataset they trained Chardet on(...)
> Whereas charset-normalizer don't train on anything, our solution is based on a completely different algorithm, still heuristic
> through, it does not need weights across every encoding tables.

## ✨ Installation

Using pip:

```
pip install charset-normalizer -U
```

## 🚀 Basic Usage

### CLI

This package comes with a CLI.

```
usage: normalizer [-h] [-v] [-a] [-n] [-m] [-r] [-f] [-t THRESHOLD]
                  file [file ...]

The Real First Universal Charset Detector. Discover originating encoding used
on text file. Normalize text to unicode.

positional arguments:
  files                 File(s) to be analysed

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Display complementary information about file if any.
                        Stdout will contain logs about the detection process.
  -a, --with-alternative
                        Output complementary possibilities if any. Top-level
                        JSON WILL be a list.
  -n, --normalize       Permit to normalize input file. If not set, program
                        does not write anything.
  -m, --minimal         Only output the charset detected to STDOUT. Disabling
                        JSON output.
  -r, --replace         Replace file when trying to normalize it instead of
                        creating a new one.
  -f, --force           Replace file without asking if you are sure, use this
                        flag with caution.
  -t THRESHOLD, --threshold THRESHOLD
                        Define a custom maximum amount of chaos allowed in
                        decoded content. 0. <= chaos <= 1.
  --version             Show version information and exit.
```

```
normalizer ./data/sample.1.fr.srt
```

or

```
python -m charset_normalizer ./data/sample.1.fr.srt
```

🎉 Since version 1.4.0 the CLI produce easily usable stdout result in JSON format.

```
{
    "path": "/home/default/projects/charset_normalizer/data/sample.1.fr.srt",
    "encoding": "cp1252",
    "encoding_aliases": [
        "1252",
        "windows_1252"
    ],
    "alternative_encodings": [
        "cp1254",
        "cp1256",
        "cp1258",
        "iso8859_14",
        "iso8859_15",
        "iso8859_16",
        "iso8859_3",
        "iso8859_9",
        "latin_1",
        "mbcs"
    ],
    "language": "French",
    "alphabets": [
        "Basic Latin",
        "Latin-1 Supplement"
    ],
    "has_sig_or_bom": false,
    "chaos": 0.149,
    "coherence": 97.152,
    "unicode_path": null,
    "is_preferred": true
}
```

### Python

Just print out normalized text

```
from charset_normalizer import from_path

results = from_path('./my_subtitle.srt')

print(str(results.best()))
```

Upgrade your code without effort

```
from charset_normalizer import detect
```

The above code will behave the same as chardet. We ensure that we offer the best (reasonable) BC result possible.

See the docs for advanced usage : readthedocs.io

## 😇 Why

When I started using Chardet, I noticed that it was not suited to my expectations, and I wanted to propose a
reliable alternative using a completely different method. Also! I never back down on a good challenge!

I don't care about the originating charset encoding, because two different tables can
produce two identical rendered string.
What I want is to get readable text, the best I can.

In a way, I'm brute forcing text decoding. How cool is that ? 😎

Don't confuse package ftfy with charset-normalizer or chardet. ftfy goal is to repair Unicode string whereas charset-normalizer to convert raw file in unknown encoding to unicode.

## 🍰 How

- Discard all charset encoding table that could not fit the binary content.
- Measure noise, or the mess once opened (by chunks) with a corresponding charset encoding.
- Extract matches with the lowest mess detected.
- Additionally, we measure coherence / probe for a language.

Wait a minute, what is noise/mess and coherence according to YOU ?

Noise : I opened hundred of text files, written by humans, with the wrong encoding table. I observed, then
I established some ground rules about what is obvious when it seems like a mess (aka. defining noise in rendered text).
I know that my interpretation of what is noise is probably incomplete, feel free to contribute in order to
improve or rewrite it.

Coherence : For each language there is on earth, we have computed ranked letter appearance occurrences (the best we can). So I thought
that intel is worth something here. So I use those records against decoded text to check if I can detect intelligent design.

## ⚡ Known limitations

- Language detection is unreliable when text contains two or more languages sharing identical letters. (eg. HTML (english tags) + Turkish content (Sharing Latin characters))
- Every charset detector heavily depends on sufficient content. In common cases, do not bother run detection on very tiny content.

## ⚠️ About Python EOLs

If you are running:

- Python >=2.7,<3.5: Unsupported
- Python 3.5: charset-normalizer < 2.1
- Python 3.6: charset-normalizer < 3.1

Upgrade your Python interpreter as soon as possible.

## 👤 Contributing

Contributions, issues and feature requests are very much welcome.

Feel free to check issues page if you want to contribute.

## 📝 License

Copyright © Ahmed TAHRI @Ousret.

This project is MIT licensed.

Characters frequencies used in this project © 2012 Denny Vrandečić

## 💼 For Enterprise

Professional support for charset-normalizer is available as part of the Tidelift
Subscription. Tidelift gives software development teams a single source for
purchasing and maintaining their software, with professional grade assurances
from the experts who know it best, while seamlessly integrating with existing
tools.

[image: OpenSSF Best Practices]

# Changelog

All notable changes to charset-normalizer will be documented in this file. This project adheres to Semantic Versioning.
The format is based on Keep a Changelog.

## 3.5.1 (2026-08-15)

### Changed

- Raised upper bound of setuptools to v84 (#794)
- Cache performance access optimization for our CharInfo struct (prebuilt only).

### Fixed

- No longer decoding large content when the noise detector output give a high entropy.
Only impacted large content input >1M bytes.

## 3.5.0 (2026-08-12)

### Added

- Explicit support for Python 3.15

### Fixed

- Comparing a CharsetMatch to a non-alias encoding strings (#773)
- Return 0.0 CharsetMatch.multi_byte_usage for empty payloads instead of crashing (#774)
- A file with both a charset declaration and BOM/SIG did not verify first the BOM/SIG charset.
- iso2022* cases misdetected due to a flaw in our multibyte chunking logic.

### Changed

- Replaced the optional mypyc build with Cython extensions while retaining the
pure Python fallback. The previous engine (mypyc) started to hit rough limit around
the optimization of our noise/coherence detector while Cython allows us to
steer the engine toward the right generated optimized sources.
This change SHOULD not impact bundler (e.g. Pyinstaller) as the module are
immediately discoverable (i.e. not hidden import like mypyc did).
Moreover, a long wished distribution is the abi3 wheels, this will allow us
to no longer rush each year when a new Python interpreter is released.
We still distribute the interpreter specific wheels for faster performance.
- Applied micro-optimization on several utils.
- CharsetMatches no longer sort on each match insertion.

### Misc

- Removed an old performance optimization attempt in apy.py (success_fast_tracked+payload_result_cache).

## 3.4.9 (2026-07-07)

### Fixed

- Regression in our fallback path leading to a decode error. (#771)
We've yanked 3.4.8 as a result of that bug.

## 3.4.8 (2026-07-06)

### Fixed

- Wall import time due to cascade codec imports for our multibyte first sort of iana supported codecs (#742)
- Unnecessary json import at runtime (#753)
- Inverse capitalization not seen by noise detector (#731)

### Changed

- No longer holding a global cache for our noise / coherence measurements. Relax RSS memory usage.
- Micro-optimizations in our noise / coherence measurements.
- No longer using regex search by default for our preemptive charset mark algorithm.
- Raised upperbound of setuptools to v83.
- Raised upperbound of mypy(c) to v2.1.

### Removed

- Redundant UTF7 BOM marker (#730)

## 3.4.7 (2026-04-02)

### Changed

- Pre-built optimized version using mypy[c] v1.20.
- Relax setuptools constraint to setuptools>=68,<82.1.

### Fixed

- Correctly remove SIG remnant in utf-7 decoded string. (#718) (#716)

## 3.4.6 (2026-03-15)

### Changed

- Flattened the logic in charset_normalizer.md for higher performance. Removed eligible(..) and feed(...)
in favor of feed_info(...).
- Raised upper bound for mypy[c] to 1.20, for our optimized version.
- Updated UNICODE_RANGES_COMBINED using Unicode blocks v17.

### Fixed

- Edge case where noise difference between two candidates can be almost insignificant. (#672)
- CLI --normalize writing to wrong path when passing multiple files in. (#702)

### Misc

- Freethreaded pre-built wheels now shipped in PyPI starting with 3.14t. (#616)

## 3.4.5 (2026-03-06)

### Changed

- Update setuptools constraint to setuptools>=68,<=82.
- Raised upper bound of mypyc for the optional pre-built extension to v1.19.1

### Fixed

- Add explicit link to lib math in our optimized build. (#692)
- Logger level not restored correctly for empty byte sequences. (#701)
- TypeError when passing bytearray to from_bytes. (#703)

### Misc

- Applied safe micro-optimizations in both our noise detector and language detector.
- Rewrote the query_yes_no function (inside CLI) to avoid using ambiguous licensed code.
- Added cd.py submodule into mypyc optional compilation to reduce further the performance impact.

## 3.4.4 (2025-10-13)

### Changed

- Bound setuptools to a specific constraint setuptools>=68,<=81.
- Raised upper bound of mypyc for the optional pre-built extension to v1.18.2

### Removed

- setuptools-scm as a build dependency.

### Misc

- Enforced hashes in dev-requirements.txt and created ci-requirements.txt for security purposes.
- Additional pre-built wheels for riscv64, s390x, and armv7l architectures.
- Restore multiple.intoto.jsonl in GitHub releases in addition to individual attestation file per wheel.

## 3.4.3 (2025-08-09)

### Changed

- mypy(c) is no longer a required dependency at build time if CHARSET_NORMALIZER_USE_MYPYC isn't set to 1. (#595) (#583)
- automatically lower confidence on small bytes samples that are not Unicode in detect output legacy function. (#391)

### Added

- Custom build backend to overcome inability to mark mypy as an optional dependency in the build phase.
- Support for Python 3.14

### Fixed

- sdist archive contained useless directories.
- automatically fallback on valid UTF-16 or UTF-32 even if the md says it's noisy. (#633)

### Misc

- SBOM are automatically published to the relevant GitHub release to comply with regulatory changes.
Each published wheel comes with its SBOM. We choose CycloneDX as the format.
- Prebuilt optimized wheel are no longer distributed by default for CPython 3.7 due to a change in cibuildwheel.

## 3.4.2 (2025-05-02)

### Fixed

- Addressed the DeprecationWarning in our CLI regarding argparse.FileType by backporting the target class into the package. (#591)
- Improved the overall reliability of the detector with CJK Ideographs. (#605) (#587)

### Changed

- Optional mypyc compilation upgraded to version 1.15 for Python >= 3.8

## 3.4.1 (2024-12-24)

### Changed

- Project metadata are now stored using pyproject.toml instead of setup.cfg using setuptools as the build backend.
- Enforce annotation delayed loading for a simpler and consistent types in the project.
- Optional mypyc compilation upgraded to version 1.14 for Python >= 3.8

### Added

- pre-commit configuration.
- noxfile.

### Removed

- build-requirements.txt as per using pyproject.toml native build configuration.
- bin/integration.py and bin/serve.py in favor of downstream integration test (see noxfile).
- setup.cfg in favor of pyproject.toml metadata configuration.
- Unused utils.range_scan function.

### Fixed

- Converting content to Unicode bytes may insert utf_8 instead of preferred utf-8. (#572)
- Deprecation warning "'count' is passed as positional argument" when converting to Unicode bytes on Python 3.13+

## 3.4.0 (2024-10-08)

### Added

- Argument --no-preemptive in the CLI to prevent the detector to search for hints.
- Support for Python 3.13 (#512)

### Fixed

- Relax the TypeError exception thrown when trying to compare a CharsetMatch with anything else than a CharsetMatch.
- Improved the general reliability of the detector based on user feedbacks. (#520) (#509) (#498) (#407) (#537)
- Declared charset in content (preemptive detection) not changed when converting to utf-8 bytes. (#381)

## 3.3.2 (2023-10-31)

### Fixed

- Unintentional memory usage regression when using large payload that match several encoding (#376)
- Regression on some detection case showcased in the documentation (#371)

### Added

- Noise (md) probe that identify malformed arabic representation due to the presence of letters in isolated form (credit to my wife)

## 3.3.1 (2023-10-22)

### Changed

- Optional mypyc compilation upgraded to version 1.6.1 for Python >= 3.8
- Improved the general detection reliability based on reports from the community

## 3.3.0 (2023-09-30)

### Added

- Allow to execute the CLI (e.g. normalizer) through python -m charset_normalizer.cli or python -m charset_normalizer
- Support for 9 forgotten encoding that are supported by Python but unlisted in encoding.aliases as they have no alias (#323)

### Removed

- (internal) Redundant utils.is_ascii function and unused function is_private_use_only
- (internal) charset_normalizer.assets is moved inside charset_normalizer.constant

### Changed

- (internal) Unicode code blocks in constants are updated using the latest v15.0.0 definition to improve detection
- Optional mypyc compilation upgraded to version 1.5.1 for Python >= 3.8

### Fixed

- Unable to properly sort CharsetMatch when both chaos/noise and coherence were close due to an unreachable condition in __lt__ (#350)

## 3.2.0 (2023-06-07)

### Changed

- Typehint for function from_path no longer enforce PathLike as its first argument
- Minor improvement over the global detection reliability

### Added

- Introduce function is_binary that relies on main capabilities, and optimized to detect binaries
- Propagate enable_fallback argument throughout from_bytes, from_path, and from_fp that allow a deeper control over the detection (default True)
- Explicit support for Python 3.12

### Fixed

- Edge case detection failure where a file would contain 'very-long' camel cased word (Issue #289)

## 3.1.0 (2023-03-06)

### Added

- Argument should_rename_legacy for legacy function detect and disregard any new arguments without errors (PR #262)

### Removed

- Support for Python 3.6 (PR #260)

### Changed

- Optional speedup provided by mypy/c 1.0.1

## 3.0.1 (2022-11-18)

### Fixed

- Multi-bytes cutter/chunk generator did not always cut correctly (PR #233)

### Changed

- Speedup provided by mypy/c 0.990 on Python >= 3.7

## 3.0.0 (2022-10-20)

### Added

- Extend the capability of explain=True when cp_isolation contains at most two entries (min one), will log in details of the Mess-detector results
- Support for alternative language frequency set in charset_normalizer.assets.FREQUENCIES
- Add parameter language_threshold in from_bytes, from_path and from_fp to adjust the minimum expected coherence ratio
- normalizer --version now specify if current version provide extra speedup (meaning mypyc compilation whl)

### Changed

- Build with static metadata using 'build' frontend
- Make the language detection stricter
- Optional: Module md.py can be compiled using Mypyc to provide an extra speedup up to 4x faster than v2.1

### Fixed

- CLI with opt --normalize fail when using full path for files
- TooManyAccentuatedPlugin induce false positive on the mess detection when too few alpha character have been fed to it
- Sphinx warnings when generating the documentation

### Removed

- Coherence detector no longer return 'Simple English' instead return 'English'
- Coherence detector no longer return 'Classical Chinese' instead return 'Chinese'
- Breaking: Method first() and best() from CharsetMatch
- UTF-7 will no longer appear as "detected" without a recognized SIG/mark (is unreliable/conflict with ASCII)
- Breaking: Class aliases CharsetDetector, CharsetDoctor, CharsetNormalizerMatch and CharsetNormalizerMatches
- Breaking: Top-level function normalize
- Breaking: Properties chaos_secondary_pass, coherence_non_latin and w_counter from CharsetMatch
- Support for the backport unicodedata2

## 3.0.0rc1 (2022-10-18)

### Added

- Extend the capability of explain=True when cp_isolation contains at most two entries (min one), will log in details of the Mess-detector results
- Support for alternative language frequency set in charset_normalizer.assets.FREQUENCIES
- Add parameter language_threshold in from_bytes, from_path and from_fp to adjust the minimum expected coherence ratio

### Changed

- Build with static metadata using 'build' frontend
- Make the language detection stricter

### Fixed

- CLI with opt --normalize fail when using full path for files
- TooManyAccentuatedPlugin induce false positive on the mess detection when too few alpha character have been fed to it

### Removed

- Coherence detector no longer return 'Simple English' instead return 'English'
- Coherence detector no longer return 'Classical Chinese' instead return 'Chinese'

## 3.0.0b2 (2022-08-21)

### Added

- normalizer --version now specify if current version provide extra speedup (meaning mypyc compilation whl)

### Removed

- Breaking: Method first() and best() from CharsetMatch
- UTF-7 will no longer appear as "detected" without a recognized SIG/mark (is unreliable/conflict with ASCII)

### Fixed

- Sphinx warnings when generating the documentation

## 3.0.0b1 (2022-08-15)

### Changed

- Optional: Module md.py can be compiled using Mypyc to provide an extra speedup up to 4x faster than v2.1

### Removed

- Breaking: Class aliases CharsetDetector, CharsetDoctor, CharsetNormalizerMatch and CharsetNormalizerMatches
- Breaking: Top-level function normalize
- Breaking: Properties chaos_secondary_pass, coherence_non_latin and w_counter from CharsetMatch
- Support for the backport unicodedata2

## 2.1.1 (2022-08-19)

### Deprecated

- Function normalize scheduled for removal in 3.0

### Changed

- Removed useless call to decode in fn is_unprintable (#206)

### Fixed

- Third-party library (i18n xgettext) crashing not recognizing utf_8 (PEP 263) with underscore from @aleksandernovikov (#204)

## 2.1.0 (2022-06-19)

### Added

- Output the Unicode table version when running the CLI with --version (PR #194)

### Changed

- Reuse decoded buffer for single byte character sets from @nijel (PR #175)
- Fixing some performance bottlenecks from @deedy5 (PR #183)

### Fixed

- Workaround potential bug in cpython with Zero Width No-Break Space located in Arabic Presentation Forms-B, Unicode 1.1 not acknowledged as space (PR #175)
- CLI default threshold aligned with the API threshold from @oleksandr-kuzmenko (PR #181)

### Removed

- Support for Python 3.5 (PR #192)

### Deprecated

- Use of backport unicodedata from unicodedata2 as Python is quickly catching up, scheduled for removal in 3.0 (PR #194)

## 2.0.12 (2022-02-12)

### Fixed

- ASCII miss-detection on rare cases (PR #170)

## 2.0.11 (2022-01-30)

### Added

- Explicit support for Python 3.11 (PR #164)

### Changed

- The logging behavior have been completely reviewed, now using only TRACE and DEBUG levels (PR #163 #165)

## 2.0.10 (2022-01-04)

### Fixed

- Fallback match entries might lead to UnicodeDecodeError for large bytes sequence (PR #154)

### Changed

- Skipping the language-detection (CD) on ASCII (PR #155)

## 2.0.9 (2021-12-03)

### Changed

- Moderating the logging impact (since 2.0.8) for specific environments (PR #147)

### Fixed

- Wrong logging level applied when setting kwarg explain to True (PR #146)

## 2.0.8 (2021-11-24)

### Changed

- Improvement over Vietnamese detection (PR #126)
- MD improvement on trailing data and long foreign (non-pure latin) data (PR #124)
- Efficiency improvements in cd/alphabet_languages from @adbar (PR #122)
- call sum() without an intermediary list following PEP 289 recommendations from @adbar (PR #129)
- Code style as refactored by Sourcery-AI (PR #131)
- Minor adjustment on the MD around european words (PR #133)
- Remove and replace SRTs from assets / tests (PR #139)
- Initialize the library logger with a NullHandler by default from @nmaynes (PR #135)
- Setting kwarg explain to True will add provisionally (bounded to function lifespan) a specific stream handler (PR #135)

### Fixed

- Fix large (misleading) sequence giving UnicodeDecodeError (PR #137)
- Avoid using too insignificant chunk (PR #137)

### Added

- Add and expose function set_logging_handler to configure a specific StreamHandler from @nmaynes (PR #135)
- Add CHANGELOG.md entries, format is based on Keep a Changelog (PR #141)

## 2.0.7 (2021-10-11)

### Added

- Add support for Kazakh (Cyrillic) language detection (PR #109)

### Changed

- Further, improve inferring the language from a given single-byte code page (PR #112)
- Vainly trying to leverage PEP263 when PEP3120 is not supported (PR #116)
- Refactoring for potential performance improvements in loops from @adbar (PR #113)
- Various detection improvement (MD+CD) (PR #117)

### Removed

- Remove redundant logging entry about detected language(s) (PR #115)

### Fixed

- Fix a minor inconsistency between Python 3.5 and other versions regarding language detection (PR #117 #102)

## 2.0.6 (2021-09-18)

### Fixed

- Unforeseen regression with the loss of the backward-compatibility with some older minor of Python 3.5.x (PR #100)
- Fix CLI crash when using --minimal output in certain cases (PR #103)

### Changed

- Minor improvement to the detection efficiency (less than 1%) (PR #106 #101)

## 2.0.5 (2021-09-14)

### Changed

- The project now comply with: flake8, mypy, isort and black to ensure a better overall quality (PR #81)
- The BC-support with v1.x was improved, the old staticmethods are restored (PR #82)
- The Unicode detection is slightly improved (PR #93)
- Add syntax sugar __bool__ for results CharsetMatches list-container (PR #91)

### Removed

- The project no longer raise warning on tiny content given for detection, will be simply logged as warning instead (PR #92)

### Fixed

- In some rare case, the chunks extractor could cut in the middle of a multi-byte character and could mislead the mess detection (PR #95)
- Some rare 'space' characters could trip up the UnprintablePlugin/Mess detection (PR #96)
- The MANIFEST.in was not exhaustive (PR #78)

## 2.0.4 (2021-07-30)

### Fixed

- The CLI no longer raise an unexpected exception when no encoding has been found (PR #70)
- Fix accessing the 'alphabets' property when the payload contains surrogate characters (PR #68)
- The logger could mislead (explain=True) on detected languages and the impact of one MBCS match (PR #72)
- Submatch factoring could be wrong in rare edge cases (PR #72)
- Multiple files given to the CLI were ignored when publishing results to STDOUT. (After the first path) (PR #72)
- Fix line endings from CRLF to LF for certain project files (PR #67)

### Changed

- Adjust the MD to lower the sensitivity, thus improving the global detection reliability (PR #69 #76)
- Allow fallback on specified encoding if any (PR #71)

## 2.0.3 (2021-07-16)

### Changed

- Part of the detection mechanism has been improved to be less sensitive, resulting in more accurate detection results. Especially ASCII. (PR #63)
- According to the community wishes, the detection will fall back on ASCII or UTF-8 in a last-resort case. (PR #64)

## 2.0.2 (2021-07-15)

### Fixed

- Empty/Too small JSON payload miss-detection fixed. Report from @tseaver (PR #59)

### Changed

- Don't inject unicodedata2 into sys.modules from @akx (PR #57)

## 2.0.1 (2021-07-13)

### Fixed

- Make it work where there isn't a filesystem available, dropping assets frequencies.json. Report from @sethmlarson. (PR #55)
- Using explain=False permanently disable the verbose output in the current runtime (PR #47)
- One log entry (language target preemptive) was not show in logs when using explain=True (PR #47)
- Fix undesired exception (ValueError) on getitem of instance CharsetMatches (PR #52)

### Changed

- Public function normalize default args values were not aligned with from_bytes (PR #53)

### Added

- You may now use charset aliases in cp_isolation and cp_exclusion arguments (PR #47)

## 2.0.0 (2021-07-02)

### Changed

- 4x to 5 times faster than the previous 1.4.0 release. At least 2x faster than Chardet.
- Accent has been made on UTF-8 detection, should perform rather instantaneous.
- The backward compatibility with Chardet has been greatly improved. The legacy detect function returns an identical charset name whenever possible.
- The detection mechanism has been slightly improved, now Turkish content is detected correctly (most of the time)
- The program has been rewritten to ease the readability and maintainability. (+Using static typing)+
- utf_7 detection has been reinstated.

### Removed

- This package no longer require anything when used with Python 3.5 (Dropped cached_property)
- Removed support for these languages: Catalan, Esperanto, Kazakh, Baque, Volapük, Azeri, Galician, Nynorsk, Macedonian, and Serbocroatian.
- The exception hook on UnicodeDecodeError has been removed.

### Deprecated

- Methods coherence_non_latin, w_counter, chaos_secondary_pass of the class CharsetMatch are now deprecated and scheduled for removal in v3.0

### Fixed

- The CLI output used the relative path of the file(s). Should be absolute.

## 1.4.1 (2021-05-28)

### Fixed

- Logger configuration/usage no longer conflict with others (PR #44)

## 1.4.0 (2021-05-21)

### Removed

- Using standard logging instead of using the package loguru.
- Dropping nose test framework in favor of the maintained pytest.
- Choose to not use dragonmapper package to help with gibberish Chinese/CJK text.
- Require cached_property only for Python 3.5 due to constraint. Dropping for every other interpreter version.
- Stop support for UTF-7 that does not contain a SIG.
- Dropping PrettyTable, replaced with pure JSON output in CLI.

### Fixed

- BOM marker in a CharsetNormalizerMatch instance could be False in rare cases even if obviously present. Due to the sub-match factoring process.
- Not searching properly for the BOM when trying utf32/16 parent codec.

### Changed

- Improving the package final size by compressing frequencies.json.
- Huge improvement over the larges payload.

### Added

- CLI now produces JSON consumable output.
- Return ASCII if given sequences fit. Given reasonable confidence.

## 1.3.9 (2021-05-13)

### Fixed

- In some very rare cases, you may end up getting encode/decode errors due to a bad bytes payload (PR #40)

## 1.3.8 (2021-05-12)

### Fixed

- Empty given payload for detection may cause an exception if trying to access the alphabets property. (PR #39)

## 1.3.7 (2021-05-12)

### Fixed

- The legacy detect function should return UTF-8-SIG if sig is present in the payload. (PR #38)

## 1.3.6 (2021-02-09)

### Changed

- Amend the previous release to allow prettytable 2.0 (PR #35)

## 1.3.5 (2021-02-08)

### Fixed

- Fix error while using the package with a python pre-release interpreter (PR #33)

### Changed

- Dependencies refactoring, constraints revised.

### Added

- Add python 3.9 and 3.10 to the supported interpreters

MIT License

Copyright (c) 2025 TAHRI Ahmed R.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

1. They are clearly using specific code for a specific encoding even if covering most of them. ↩
1. Chardet 7 replaced the historical LGPL-licensed implementation with an AI-assisted rewrite, initially distributed under MIT and later under 0BSD. The original author contests that the rewrite was sufficiently independent to permit relicensing, while Chardet's maintainer maintains that it is a new, non-derivative implementation. A separate discussion raises questions about copyright ownership and licensing of substantially AI-generated code. Neither unresolved question is presented here as settled law. The concern is broader than whether ideas, APIs, or observable behavior are copyrightable. Independent implementations are essential to open-source competition. The ethical question is whether a maintainer with extensive access to a reciprocal project's source, architecture, tests, behavior, community, and reputation can use an LLM to recreate the same product under the same package identity, then treat the generated implementation as a provenance reset that extinguishes the project's reciprocal licensing obligations and contributor expectations. Responsible AI use in open source requires more than producing text that differs from the historical source: it requires transparent provenance, respect for project lineage, meaningful attribution, accountable human review, and consideration for the social agreement under which earlier contributors participated. If automated rewriting becomes an accepted way to retain a project's name, users, and accumulated reputation while discarding its reciprocal license, it risks weakening the trust and incentives on which FOSS depends. Early Chardet 7.x development and evaluation also incorporated files originating from charset-normalizer's test corpus. Results measured on data that influenced implementation or model development are not independent validation. Charset-normalizer has been MIT-licensed since inception and originates from a continuous human-designed, encoding-agnostic project history. AI assistance may be used, but every proposed change remains subject to maintainer review, adjustment, testing, and accountability; AI is an engineering aid, not a mechanism for erasing provenance or project lineage. An attentive eye will see that some aspects lead by us are magically found in Chardet. ↩
1. Chardet does not feed the complete body but rather a limited part of it, because the algorithm doesn't scale properly with larger samples. Feeding the whole content slow things to 0.8 ms (from the 0.5ms avg). While we do not skip content in order for us to guarantee a usable result each and every time. We attempted to feed a 272 MiB UTF-8 (Reddit archive on comments/posts) file in Chardet uncapped and waited 3.4s while Charset-Normalizer took 0.3s, this is a 10-fold speedup. ↩ ↩2
1. Uncapped max_bytes (no truncating of content) ↩ ↩2
1. cchardet main repository/package was discontinued. we're relying on a known fork namely faust-cchardet. the idea remained the same: uchardet bindings. ↩

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

charset_normalizer-3.5.1.tar.gz
 (171.8 kB
 view details)

Uploaded
 Aug 15, 2026
 Source

### Built Distributions

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

charset_normalizer-3.5.1-py3-none-any.whl
 (68.7 kB
 view details)

Uploaded
 Aug 15, 2026
 Python 3

charset_normalizer-3.5.1-cp315-cp315t-win_arm64.whl
 (193.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tWindows ARM64

charset_normalizer-3.5.1-cp315-cp315t-win_amd64.whl
 (215.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tWindows x86-64

charset_normalizer-3.5.1-cp315-cp315t-win32.whl
 (191.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tWindows x86

charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_x86_64.whl
 (252.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmusllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_s390x.whl
 (258.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmusllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_riscv64.whl
 (250.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmusllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_ppc64le.whl
 (264.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmusllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_armv7l.whl
 (239.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmusllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_aarch64.whl
 (243.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmusllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp315-cp315t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (249.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmanylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (250.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmanylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (258.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmanylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (262.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmanylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (235.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmanylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (241.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmanylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp315-cp315t-macosx_10_15_universal2.whl
 (381.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15tmacOS 10.15+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp315-cp315-win_arm64.whl
 (184.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15Windows ARM64

charset_normalizer-3.5.1-cp315-cp315-win_amd64.whl
 (204.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15Windows x86-64

charset_normalizer-3.5.1-cp315-cp315-win32.whl
 (180.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15Windows x86

charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_x86_64.whl
 (253.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_s390x.whl
 (264.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_riscv64.whl
 (252.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_ppc64le.whl
 (267.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_armv7l.whl
 (241.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_aarch64.whl
 (245.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp315-cp315-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (252.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp315-cp315-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (252.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp315-cp315-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (263.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp315-cp315-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (266.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp315-cp315-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (237.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp315-cp315-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (243.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp315-cp315-macosx_10_15_universal2.whl
 (342.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.15macOS 10.15+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp314-cp314t-win_arm64.whl
 (194.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tWindows ARM64

charset_normalizer-3.5.1-cp314-cp314t-win_amd64.whl
 (216.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tWindows x86-64

charset_normalizer-3.5.1-cp314-cp314t-win32.whl
 (191.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tWindows x86

charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_x86_64.whl
 (250.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmusllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_s390x.whl
 (258.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmusllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_riscv64.whl
 (243.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmusllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_ppc64le.whl
 (263.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmusllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_armv7l.whl
 (230.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmusllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_aarch64.whl
 (242.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmusllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (243.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmanylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (249.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmanylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (259.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmanylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (260.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmanylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (227.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmanylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (240.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmanylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp314-cp314t-macosx_10_15_universal2.whl
 (381.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14tmacOS 10.15+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp314-cp314-win_arm64.whl
 (184.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14Windows ARM64

charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl
 (204.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14Windows x86-64

charset_normalizer-3.5.1-cp314-cp314-win32.whl
 (180.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14Windows x86

charset_normalizer-3.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl
 (140.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14PyEmscripten 2026.0 wasm32

charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_x86_64.whl
 (253.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_s390x.whl
 (264.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_riscv64.whl
 (245.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_ppc64le.whl
 (266.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_armv7l.whl
 (231.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_aarch64.whl
 (244.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (245.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (251.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (263.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (266.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp314-cp314-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (226.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (242.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp314-cp314-macosx_10_15_universal2.whl
 (341.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14macOS 10.15+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphonesimulator.whl
 (198.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14iOS 13.0+ ARM64 Simulator

charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphoneos.whl
 (194.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.14iOS 13.0+ ARM64 Device

charset_normalizer-3.5.1-cp314-cp314-android_24_x86_64.whl
 (224.9 kB
 view details)

Uploaded
 Aug 15, 2026
 Android API level 24+ x86-64CPython 3.14

charset_normalizer-3.5.1-cp314-cp314-android_24_arm64_v8a.whl
 (212.3 kB
 view details)

Uploaded
 Aug 15, 2026
 Android API level 24+ ARM64 v8aCPython 3.14

charset_normalizer-3.5.1-cp313-cp313-win_arm64.whl
 (179.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13Windows ARM64

charset_normalizer-3.5.1-cp313-cp313-win_amd64.whl
 (199.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13Windows x86-64

charset_normalizer-3.5.1-cp313-cp313-win32.whl
 (177.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13Windows x86

charset_normalizer-3.5.1-cp313-cp313-pyemscripten_2025_0_wasm32.whl
 (140.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13PyEmscripten 2025.0 wasm32

charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_x86_64.whl
 (252.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_s390x.whl
 (261.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_riscv64.whl
 (245.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_ppc64le.whl
 (264.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_armv7l.whl
 (233.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_aarch64.whl
 (242.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (244.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (250.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (260.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (263.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp313-cp313-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (228.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (240.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp313-cp313-macosx_10_13_universal2.whl
 (340.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13macOS 10.13+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphonesimulator.whl
 (197.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13iOS 13.0+ ARM64 Simulator

charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphoneos.whl
 (194.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.13iOS 13.0+ ARM64 Device

charset_normalizer-3.5.1-cp313-cp313-android_24_x86_64.whl
 (223.4 kB
 view details)

Uploaded
 Aug 15, 2026
 Android API level 24+ x86-64CPython 3.13

charset_normalizer-3.5.1-cp313-cp313-android_24_arm64_v8a.whl
 (211.6 kB
 view details)

Uploaded
 Aug 15, 2026
 Android API level 24+ ARM64 v8aCPython 3.13

charset_normalizer-3.5.1-cp312-cp312-win_arm64.whl
 (180.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12Windows ARM64

charset_normalizer-3.5.1-cp312-cp312-win_amd64.whl
 (200.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12Windows x86-64

charset_normalizer-3.5.1-cp312-cp312-win32.whl
 (178.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12Windows x86

charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_x86_64.whl
 (250.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_s390x.whl
 (260.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_riscv64.whl
 (243.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_ppc64le.whl
 (262.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_armv7l.whl
 (232.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_aarch64.whl
 (240.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (244.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (248.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (259.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (262.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp312-cp312-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (230.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (238.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp312-cp312-macosx_10_13_universal2.whl
 (344.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.12macOS 10.13+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp311-cp311-win_arm64.whl
 (185.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11Windows ARM64

charset_normalizer-3.5.1-cp311-cp311-win_amd64.whl
 (206.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11Windows x86-64

charset_normalizer-3.5.1-cp311-cp311-win32.whl
 (181.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11Windows x86

charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_x86_64.whl
 (263.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_s390x.whl
 (278.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_riscv64.whl
 (259.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_ppc64le.whl
 (280.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_armv7l.whl
 (240.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_aarch64.whl
 (252.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (261.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (262.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (276.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (280.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp311-cp311-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (239.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (251.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp311-cp311-macosx_10_9_universal2.whl
 (363.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.11macOS 10.9+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp310-cp310-win_arm64.whl
 (185.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10Windows ARM64

charset_normalizer-3.5.1-cp310-cp310-win_amd64.whl
 (206.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10Windows x86-64

charset_normalizer-3.5.1-cp310-cp310-win32.whl
 (182.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10Windows x86

charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_x86_64.whl
 (263.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_s390x.whl
 (277.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_riscv64.whl
 (258.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_ppc64le.whl
 (280.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_armv7l.whl
 (242.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_aarch64.whl
 (252.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (259.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (261.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (276.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (279.6 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp310-cp310-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (240.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (251.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp310-cp310-macosx_10_9_universal2.whl
 (369.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.10macOS 10.9+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp39-cp39-win_arm64.whl
 (185.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9Windows ARM64

charset_normalizer-3.5.1-cp39-cp39-win_amd64.whl
 (206.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9Windows x86-64

charset_normalizer-3.5.1-cp39-cp39-win32.whl
 (182.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9Windows x86

charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_x86_64.whl
 (264.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_s390x.whl
 (278.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_riscv64.whl
 (259.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_ppc64le.whl
 (282.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_armv7l.whl
 (242.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_aarch64.whl
 (253.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (260.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (262.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

charset_normalizer-3.5.1-cp39-cp39-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (278.4 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp39-cp39-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (281.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp39-cp39-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (241.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (251.7 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp39-cp39-macosx_10_9_universal2.whl
 (368.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.9macOS 10.9+ universal2 (ARM64, x86-64)

charset_normalizer-3.5.1-cp37-abi3-win_arm64.whl
 (287.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+Windows ARM64

charset_normalizer-3.5.1-cp37-abi3-win_amd64.whl
 (199.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+Windows x86-64

charset_normalizer-3.5.1-cp37-abi3-win32.whl
 (174.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+Windows x86

charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_x86_64.whl
 (254.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+musllinux: musl 1.2+ x86-64

charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_s390x.whl
 (256.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+musllinux: musl 1.2+ s390x

charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_riscv64.whl
 (247.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+musllinux: musl 1.2+ riscv64

charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_ppc64le.whl
 (260.3 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+musllinux: musl 1.2+ ppc64le

charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_armv7l.whl
 (232.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+musllinux: musl 1.2+ ARMv7l

charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_aarch64.whl
 (241.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+musllinux: musl 1.2+ ARM64

charset_normalizer-3.5.1-cp37-abi3-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (250.2 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

charset_normalizer-3.5.1-cp37-abi3-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 (255.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+manylinux: glibc 2.17+ s390xmanylinux: glibc 2.28+ s390x

charset_normalizer-3.5.1-cp37-abi3-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 (260.0 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+manylinux: glibc 2.17+ ppc64lemanylinux: glibc 2.28+ ppc64le

charset_normalizer-3.5.1-cp37-abi3-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 (230.8 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+manylinux: glibc 2.17+ ARMv7lmanylinux: glibc 2.31+ ARMv7l

charset_normalizer-3.5.1-cp37-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (240.9 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

charset_normalizer-3.5.1-cp37-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl
 (253.1 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+manylinux: glibc 2.28+ x86-64manylinux: glibc 2.5+ x86-64

charset_normalizer-3.5.1-cp37-abi3-macosx_10_9_universal2.whl
 (331.5 kB
 view details)

Uploaded
 Aug 15, 2026
 CPython 3.7+macOS 10.9+ universal2 (ARM64, x86-64)

## File details

Details for the file charset_normalizer-3.5.1.tar.gz.

### File metadata

- Download URL: charset_normalizer-3.5.1.tar.gz
- Upload date:
 Aug 15, 2026
- Size: 171.8 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 6117b84ea48435e5356dc737f5121485c30920ba43375fa7b434fd753df0eac3 | |
| MD5 | 45256d816357f60e3e1880c5aa54a8fd | |
| BLAKE2b-256 | e53f143b048436775b0f76ac3eec145c019e8173ccc2885c8f20319b996d5e83 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1.tar.gz:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1.tar.gz
 - Subject digest: 6117b84ea48435e5356dc737f5121485c30920ba43375fa7b434fd753df0eac3
 - Sigstore transparency entry: 2474047077
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-py3-none-any.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-py3-none-any.whl
- Upload date:
 Aug 15, 2026
- Size: 68.7 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 6df0ec430f9a831772c23ca5a224cba36517a58a84bb32c32bb59a9fa67c47f6 | |
| MD5 | 941e6cad75cc77b7d00e6a55f26785f1 | |
| BLAKE2b-256 | cc61d01fc49b8dea277640b55a9e15960dbca9fdc8c9fde18e572d39c59f4019 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-py3-none-any.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-py3-none-any.whl
 - Subject digest: 6df0ec430f9a831772c23ca5a224cba36517a58a84bb32c32bb59a9fa67c47f6
 - Sigstore transparency entry: 2474068337
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 193.9 kB
- Tags: CPython 3.15t, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | fb78f6e7fcd8ad785d28cd577168bc1aaee827b25bb8755638f694794ea98f0a | |
| MD5 | 8d950fe3202c4b642edacc87062750bf | |
| BLAKE2b-256 | a8769aad3e9c8865e5e0efa9a7f6f81c37a67635a985145ecd44528a81e088ee | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-win_arm64.whl
 - Subject digest: fb78f6e7fcd8ad785d28cd577168bc1aaee827b25bb8755638f694794ea98f0a
 - Sigstore transparency entry: 2474084736
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 215.9 kB
- Tags: CPython 3.15t, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 35aea775dc2bd5f54cd84a1cd2696cc3207c479cb9cf0bd346f0d343e4300ddb | |
| MD5 | c18696a82d3d093e1871dbbf95146b9d | |
| BLAKE2b-256 | 69d543c2b3e9d8267092b913eb8b0603f0f71993c395632886bd37a7223f96cf | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-win_amd64.whl
 - Subject digest: 35aea775dc2bd5f54cd84a1cd2696cc3207c479cb9cf0bd346f0d343e4300ddb
 - Sigstore transparency entry: 2474075068
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 191.2 kB
- Tags: CPython 3.15t, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-win32.whl
| Algorithm | Hash digest | |
| SHA256 | ac13b004224fb341e1e25a1ed5e19d32f57cdb2a403e01f003b46f051a550f6f | |
| MD5 | b8b5cac2253f8dab80dc48b8d26bef9a | |
| BLAKE2b-256 | 1e25ed3f9919c5aef8cc818be1f972f565f7610d7b2076b8ebb98839516ffc3c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-win32.whl
 - Subject digest: ac13b004224fb341e1e25a1ed5e19d32f57cdb2a403e01f003b46f051a550f6f
 - Sigstore transparency entry: 2474074501
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 252.0 kB
- Tags: CPython 3.15t, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 4d26f14f041e83dd8edfd61f4cd4fa7285d31798b5bf1f28e70c367ba6c41d61 | |
| MD5 | 5897aa1430f1570391beb0a22ca79acb | |
| BLAKE2b-256 | 34f7b13b1ccae2c8ec63980d13be1890eb73f8aeabbfce02a24aabc0908788f5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_x86_64.whl
 - Subject digest: 4d26f14f041e83dd8edfd61f4cd4fa7285d31798b5bf1f28e70c367ba6c41d61
 - Sigstore transparency entry: 2474058289
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 258.2 kB
- Tags: CPython 3.15t, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | a5cbd90ecf0fc62e64726917ad083b73001f0563657a87ec3c0b504e277dc90d | |
| MD5 | 94915578d7c93162d0f7ff24023f6af0 | |
| BLAKE2b-256 | 8158d325912115caec62d6bdd77bbab5e0b7da5d234a9f20affdffcbcb530d0b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_s390x.whl
 - Subject digest: a5cbd90ecf0fc62e64726917ad083b73001f0563657a87ec3c0b504e277dc90d
 - Sigstore transparency entry: 2474083066
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 250.3 kB
- Tags: CPython 3.15t, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 77efcff2b23071c349402ac1066667a3d011f62398d81408c9b88ad991747c9e | |
| MD5 | 0887a723078260ffb31cf2fea4fad7f8 | |
| BLAKE2b-256 | 104cdc48409274a1817ff349711d26c62aa0c597df865d4d69ef79160c859193 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_riscv64.whl
 - Subject digest: 77efcff2b23071c349402ac1066667a3d011f62398d81408c9b88ad991747c9e
 - Sigstore transparency entry: 2474073499
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 264.1 kB
- Tags: CPython 3.15t, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 6199d5606e2bbf2b096cf64d03f8b6790c91081d5ac866b8e7bb6422738cc60c | |
| MD5 | 359a97b19460173889c8f8b30bc0957d | |
| BLAKE2b-256 | d35856a48c296601274c4689b864a8e2dfb209b81dfcb39472753ce95eea662b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_ppc64le.whl
 - Subject digest: 6199d5606e2bbf2b096cf64d03f8b6790c91081d5ac866b8e7bb6422738cc60c
 - Sigstore transparency entry: 2474065222
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 239.8 kB
- Tags: CPython 3.15t, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 252d099029bcbea642f2a06c4ed5046bdf8b5a8150b64afa5e027e88b106e5ee | |
| MD5 | e3bd59ef5dfe72a5da39bd4a7db111dd | |
| BLAKE2b-256 | 7cc149a91fe7e97c8140094ca5c64161ab623a70d9f636bf834eace14048acb5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_armv7l.whl
 - Subject digest: 252d099029bcbea642f2a06c4ed5046bdf8b5a8150b64afa5e027e88b106e5ee
 - Sigstore transparency entry: 2474057012
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 243.6 kB
- Tags: CPython 3.15t, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 9b5db6052055d34d41230fb78d7c439c23dc536a9896f6cb039e8dd92cfc1263 | |
| MD5 | 6e964465320717dc902f3bcbd6875613 | |
| BLAKE2b-256 | adc3525f508cd1e58d0450ac55ed40ac75bc3a97482c59def5278456a5fbf03c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-musllinux_1_2_aarch64.whl
 - Subject digest: 9b5db6052055d34d41230fb78d7c439c23dc536a9896f6cb039e8dd92cfc1263
 - Sigstore transparency entry: 2474059257
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 249.9 kB
- Tags: CPython 3.15t, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 04368edf83514385ffc3e1cfd4546e595f4f1272dd23ba437a93a9cc3741d47b | |
| MD5 | cb6a82b38676cff22bd9ebfded97595d | |
| BLAKE2b-256 | 95b5a18d0dd1157ab655cc2cb14a545f4a4784bbad70ab3502412e36097502d9 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 04368edf83514385ffc3e1cfd4546e595f4f1272dd23ba437a93a9cc3741d47b
 - Sigstore transparency entry: 2474059531
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 250.2 kB
- Tags: CPython 3.15t, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | cc5d36d96478aa9c60654bd932525bf32964c62a7281eafdf16d85003a8d6004 | |
| MD5 | 00768f01fb18825bad5d0b4d933e2570 | |
| BLAKE2b-256 | ffc12adc2800903fb013210349313b710a5376856578d9e33e6b9a1d8b36714a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: cc5d36d96478aa9c60654bd932525bf32964c62a7281eafdf16d85003a8d6004
 - Sigstore transparency entry: 2474057916
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 258.9 kB
- Tags: CPython 3.15t, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 19a3dd5aa73cef1c99687c4fc57db016a9c17104ae1185da88ba566a5d3bebe4 | |
| MD5 | 08f1cc2f3cee47c382624270fb641a34 | |
| BLAKE2b-256 | 55663bb56a47f7dcba014055b1a1d33c6f08bbe9c1e74dba154cfa25f90ae885 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: 19a3dd5aa73cef1c99687c4fc57db016a9c17104ae1185da88ba566a5d3bebe4
 - Sigstore transparency entry: 2474089061
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 262.5 kB
- Tags: CPython 3.15t, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | ced3fdd71aaa83ce593746c2edb42b7a59cb4c19c8b5c407781c72e493aae55a | |
| MD5 | fdc7621f4c080b5456e4d3e44c57e93b | |
| BLAKE2b-256 | 7d07469f78af590f7d5cd48e20d8dbfa3d66deeff9ba37768c04d886b5afd45c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: ced3fdd71aaa83ce593746c2edb42b7a59cb4c19c8b5c407781c72e493aae55a
 - Sigstore transparency entry: 2474059809
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 235.3 kB
- Tags: CPython 3.15t, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | e4b018dc5a0eee4676e38fe84a47a427816c590b93b55d9025274ec4d6ffc2dc | |
| MD5 | da8b3ef71058cb8a3661f57557305c8f | |
| BLAKE2b-256 | 2853a2d249ebddf47b889a100c0bdcb61a2f9dbb8bc24ef325cc062e4f476877 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: e4b018dc5a0eee4676e38fe84a47a427816c590b93b55d9025274ec4d6ffc2dc
 - Sigstore transparency entry: 2474073828
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 241.7 kB
- Tags: CPython 3.15t, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 9dbdd9205662134957cf0c324f639bdc5031c0ca056e2369e238db75187c0f11 | |
| MD5 | 61921c2fa66ff7118e4b6b6c775eb8e0 | |
| BLAKE2b-256 | 9610e9aa7923d3ddac652c99a1c5f7be494e737e151566a44abe018daf757f2c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 9dbdd9205662134957cf0c324f639bdc5031c0ca056e2369e238db75187c0f11
 - Sigstore transparency entry: 2474093962
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315t-macosx_10_15_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315t-macosx_10_15_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 381.4 kB
- Tags: CPython 3.15t, macOS 10.15+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315t-macosx_10_15_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | 59171c6e45bf07d0d5cab3b0bf81d945035530f6873398b3b531c31184d46663 | |
| MD5 | 3d4343980c54dee5ba008c67bafce50a | |
| BLAKE2b-256 | 3b329b8929bf384061ee1fe5d9c27c6f9776d3d824039ad4e14c88ec00c7808e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315t-macosx_10_15_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315t-macosx_10_15_universal2.whl
 - Subject digest: 59171c6e45bf07d0d5cab3b0bf81d945035530f6873398b3b531c31184d46663
 - Sigstore transparency entry: 2474072685
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 184.1 kB
- Tags: CPython 3.15, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 5fc45d653ea8c9a20479167e11d4a0f8cb2fa3470737ab6f9c827532313187b7 | |
| MD5 | 7cf1b8656a9b02ac940f5f818a7df448 | |
| BLAKE2b-256 | a15d9ed554480eda8e447b673648628fdc29574d23dbad01fe11837adedd1cae | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-win_arm64.whl
 - Subject digest: 5fc45d653ea8c9a20479167e11d4a0f8cb2fa3470737ab6f9c827532313187b7
 - Sigstore transparency entry: 2474074003
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 204.2 kB
- Tags: CPython 3.15, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 92caef967d287a407085d61176fce4012b1dd62daed4eb6d5ceb26d3d2538712 | |
| MD5 | 03a4a4acfacbd51288e71c5e6ec815e5 | |
| BLAKE2b-256 | c9bcf46a132041b29e4a8779ed712d3df1bf112e94ca8de58b66d7ec2c0cf8b9 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-win_amd64.whl
 - Subject digest: 92caef967d287a407085d61176fce4012b1dd62daed4eb6d5ceb26d3d2538712
 - Sigstore transparency entry: 2474091440
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 180.3 kB
- Tags: CPython 3.15, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 706bfd38730a5ac7a365793269a00f4e988178cec121391f4248d84ad8c972e9 | |
| MD5 | 98d34676faa3051e100644d985566dc1 | |
| BLAKE2b-256 | afaf53afe99068b3c10b4cbae592a52ef72a7c92c0188440e83ee3a078fd8f75 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-win32.whl
 - Subject digest: 706bfd38730a5ac7a365793269a00f4e988178cec121391f4248d84ad8c972e9
 - Sigstore transparency entry: 2474075962
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 253.9 kB
- Tags: CPython 3.15, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 687c9ca3035544b113bea2055e180af96fb63c0c476e22a9180f51925186e7b7 | |
| MD5 | 171dc5a42dd6cfd47e45803d3a812349 | |
| BLAKE2b-256 | 3290fcc850bae791abd2e0c041847f13e270aa08692a79f3e00de6d2dce1cb50 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_x86_64.whl
 - Subject digest: 687c9ca3035544b113bea2055e180af96fb63c0c476e22a9180f51925186e7b7
 - Sigstore transparency entry: 2474073352
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 264.9 kB
- Tags: CPython 3.15, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | cc0329df4caaceb950d2f580b5ac716a377f7059624a0bafaeaf8a218c6ed774 | |
| MD5 | 269ef50dea25604db897c522db508e13 | |
| BLAKE2b-256 | 5efa40414471acf0aa0692ca77305aa00e434fcd8288f0941c93c30e9a5f8f2f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_s390x.whl
 - Subject digest: cc0329df4caaceb950d2f580b5ac716a377f7059624a0bafaeaf8a218c6ed774
 - Sigstore transparency entry: 2474070323
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 252.0 kB
- Tags: CPython 3.15, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 978eab16f55b4ab2c2a745be9a0a840bf8f09a7f227d9c76eb30214d078865a5 | |
| MD5 | 9984591627e2f640a91c1459e54d8b02 | |
| BLAKE2b-256 | b8d734d8e404e358d2adcc5a228c2134643af00104c8fb0bf525f3688d756f05 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_riscv64.whl
 - Subject digest: 978eab16f55b4ab2c2a745be9a0a840bf8f09a7f227d9c76eb30214d078865a5
 - Sigstore transparency entry: 2474071020
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 267.0 kB
- Tags: CPython 3.15, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 195ce897c6153c0700078142cf8efe3e6454ca4cf4357499e4078dfd83396626 | |
| MD5 | 2b78071887827e4ee8602bc9500e667e | |
| BLAKE2b-256 | 67c4217755fd1abc50d326c252922cd642002758095a81ff45010337b8b3ef65 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_ppc64le.whl
 - Subject digest: 195ce897c6153c0700078142cf8efe3e6454ca4cf4357499e4078dfd83396626
 - Sigstore transparency entry: 2474048378
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 241.5 kB
- Tags: CPython 3.15, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 838648accb3a7fd9803fd45c87bce8509648eb0c11bc34e216141300977244f2 | |
| MD5 | 80dbb9b638f9b92eeb81da089705e0cb | |
| BLAKE2b-256 | 26ded8e48c135ae480879539cdb179c8d3b50c7879497d75dd899b5763b69cee | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_armv7l.whl
 - Subject digest: 838648accb3a7fd9803fd45c87bce8509648eb0c11bc34e216141300977244f2
 - Sigstore transparency entry: 2474081460
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 245.2 kB
- Tags: CPython 3.15, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 21b82d8082f6f5e7f456ef0bd16323d08de1266efbfeb476e64b2a91d1471a4e | |
| MD5 | d158db7e651ded009baeba9685872246 | |
| BLAKE2b-256 | c8e3d119f86a01f9331e8186175f24873b1d74a7ee9e2e4b4d68f9947dae5afd | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-musllinux_1_2_aarch64.whl
 - Subject digest: 21b82d8082f6f5e7f456ef0bd16323d08de1266efbfeb476e64b2a91d1471a4e
 - Sigstore transparency entry: 2474068725
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 252.1 kB
- Tags: CPython 3.15, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 854066be00447fa8de2ccbbe893e2ffc4b123ef16d897af794c1e18bd4a714b0 | |
| MD5 | 69ad8dfbaec9642a41f0d5b99134ede2 | |
| BLAKE2b-256 | 2e57de221f1745a90d418199761967e2776bfe2c275a1194220985e8c1d37833 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 854066be00447fa8de2ccbbe893e2ffc4b123ef16d897af794c1e18bd4a714b0
 - Sigstore transparency entry: 2474061247
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 252.1 kB
- Tags: CPython 3.15, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 5c84bec0ab5ae0c64bfe73a7d2adcb5ce73b467523fc27fd6a28ab2aa6cbe35a | |
| MD5 | 97f47c6bc4616015ec3cdcf685d8fe84 | |
| BLAKE2b-256 | af3d391b193eb9f3e84b02f9314088c386debdc0debee843535aaea2e2c6715d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 5c84bec0ab5ae0c64bfe73a7d2adcb5ce73b467523fc27fd6a28ab2aa6cbe35a
 - Sigstore transparency entry: 2474073888
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 263.4 kB
- Tags: CPython 3.15, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 8fe532b3c966d1fb794e0698e4589d0444017ae77fc0b31edea13c0e35bcc449 | |
| MD5 | 20d351646d085b62bdf3e94a6473258b | |
| BLAKE2b-256 | 86d3e367787febe4e74769dec0f406f2c3c8d1b955fce5aee1fd0f94e8367a45 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: 8fe532b3c966d1fb794e0698e4589d0444017ae77fc0b31edea13c0e35bcc449
 - Sigstore transparency entry: 2474096900
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 266.2 kB
- Tags: CPython 3.15, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 8ac8c94b6539074e0f40899301273ac8402b9b3e01c7b7ba269ff30340aaaf20 | |
| MD5 | 58717738d332731332adebb3d41092df | |
| BLAKE2b-256 | 8cc2027335f0aa337a2a2e121bac1ad88c4f02ba6053ea0926802784f3db11af | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: 8ac8c94b6539074e0f40899301273ac8402b9b3e01c7b7ba269ff30340aaaf20
 - Sigstore transparency entry: 2474059386
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 237.0 kB
- Tags: CPython 3.15, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | baf3775a2635e5a11fbd5e4e64ee69c7e86875d224a5c72aca4c141064589a90 | |
| MD5 | 482e632d7e4426c3260e7c303c3b2c5d | |
| BLAKE2b-256 | 033b0cc9a26777334ab2f2e3089b948bbf4e4fe72ea70b897715ef6415043ec8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: baf3775a2635e5a11fbd5e4e64ee69c7e86875d224a5c72aca4c141064589a90
 - Sigstore transparency entry: 2474060600
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 243.0 kB
- Tags: CPython 3.15, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 2679de311c7946dde5d3b6f44941844133ff5c7cb86099c0061ab1e8901c20a8 | |
| MD5 | dfd43d8eb58863160921f7a8f6069bbe | |
| BLAKE2b-256 | 7fa6e3b46852424246065355644f4fb6dbccc0239a42a2eee27ecfc8957f0bcd | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 2679de311c7946dde5d3b6f44941844133ff5c7cb86099c0061ab1e8901c20a8
 - Sigstore transparency entry: 2474069657
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp315-cp315-macosx_10_15_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp315-cp315-macosx_10_15_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 342.0 kB
- Tags: CPython 3.15, macOS 10.15+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp315-cp315-macosx_10_15_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | 9085f87b0e38a2b92b8923059b4e8789fe40d9279712d15dcc670048d77079af | |
| MD5 | 580194b4ade1f380077f39523f9df991 | |
| BLAKE2b-256 | 4a4e8544831ef59d8f27ce92c80871380fdacc8076a8a56ed62f82e54f991333 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp315-cp315-macosx_10_15_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp315-cp315-macosx_10_15_universal2.whl
 - Subject digest: 9085f87b0e38a2b92b8923059b4e8789fe40d9279712d15dcc670048d77079af
 - Sigstore transparency entry: 2474059962
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 194.1 kB
- Tags: CPython 3.14t, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | fdb8a068947befafba9952162645dc2fecaeb400e64584829ed5e9b2fbe21a7f | |
| MD5 | f708e003f364b1d4c782519bee141cba | |
| BLAKE2b-256 | 27e961c01fb8b804692569c036b3fc50495814502dcf13a60649c6055390b02c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-win_arm64.whl
 - Subject digest: fdb8a068947befafba9952162645dc2fecaeb400e64584829ed5e9b2fbe21a7f
 - Sigstore transparency entry: 2474065402
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 216.5 kB
- Tags: CPython 3.14t, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | acaf604462bf330b0d07e7a07c1d6e4adac79e5fb13e9c5140590542cafacc00 | |
| MD5 | 32f7e42ded1c5a97ca5a578ebac3be68 | |
| BLAKE2b-256 | 4d81ae557d3c44d1a1d688696d60563413a0866a91b7ebc50f20df838be3d8c8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-win_amd64.whl
 - Subject digest: acaf604462bf330b0d07e7a07c1d6e4adac79e5fb13e9c5140590542cafacc00
 - Sigstore transparency entry: 2474047352
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 191.1 kB
- Tags: CPython 3.14t, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 58d3e12c88e0950bca850ae1f7c256055c097639c2edb9eb123af9807d8b15e4 | |
| MD5 | e34fbf5e10fc251635f25e6a6e276726 | |
| BLAKE2b-256 | ae103d8c777cf9024615295aa1b808324ad5b4a77855869c00824bad74ffaf8a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-win32.whl
 - Subject digest: 58d3e12c88e0950bca850ae1f7c256055c097639c2edb9eb123af9807d8b15e4
 - Sigstore transparency entry: 2474089461
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 250.8 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 85d5855daafc240cc045c026d7a15fd198a09b0fc8ff6f5ecbb5297b509cb11e | |
| MD5 | be99d2b1d8f76a5cc42e9aa9e31bc518 | |
| BLAKE2b-256 | 2e1d0fc91aeaeb3c83b748f532399ce67cf84604b48297405d740000f7a9e786 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_x86_64.whl
 - Subject digest: 85d5855daafc240cc045c026d7a15fd198a09b0fc8ff6f5ecbb5297b509cb11e
 - Sigstore transparency entry: 2474061060
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 258.8 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 496846868fea80e479324862fa877f02411f2fd0f83b79ccee2607aa68b2a032 | |
| MD5 | 6a723568d8fe2d5b59e6fd3f81145dc9 | |
| BLAKE2b-256 | ded8a50b79237f417af10f8c2a501ce8d1ca87829a22e69117891ca4ba20a69e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_s390x.whl
 - Subject digest: 496846868fea80e479324862fa877f02411f2fd0f83b79ccee2607aa68b2a032
 - Sigstore transparency entry: 2474076485
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 243.3 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 9eea3ab2597a5e65fe65296e2d6a84570845a6b55532d90333d740d48bbc850a | |
| MD5 | 324a135e3f87dd8eb04b858bf71d4821 | |
| BLAKE2b-256 | 98667c42677e739ba66746b297e2046918d793078094dc239e1e72768cffccc6 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_riscv64.whl
 - Subject digest: 9eea3ab2597a5e65fe65296e2d6a84570845a6b55532d90333d740d48bbc850a
 - Sigstore transparency entry: 2474096523
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 263.1 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 2bced4061f000f7187254a02ad3433ae17eaf991747ceea2f478422590a5bba9 | |
| MD5 | bc9551c0d7e6ad1e3347d5d17badfbf9 | |
| BLAKE2b-256 | 3ffcf6a85abebd42ce4da2f1db0aa56cc6a0df1995e318b3875d14401b8381d1 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_ppc64le.whl
 - Subject digest: 2bced4061f000f7187254a02ad3433ae17eaf991747ceea2f478422590a5bba9
 - Sigstore transparency entry: 2474047945
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 230.5 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 52ec005752a56ae79547a05c0139ca2501a0c866390b6115008456b9f0e7cde1 | |
| MD5 | 93659e96dde0513ce74e614ce5335cb7 | |
| BLAKE2b-256 | 3417672c251a888ed2aebcdd2fe830ad0104e25ff83c43f5c4f9c15e9fc6853c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_armv7l.whl
 - Subject digest: 52ec005752a56ae79547a05c0139ca2501a0c866390b6115008456b9f0e7cde1
 - Sigstore transparency entry: 2474057398
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 242.8 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | c010f5581d9c612804cc59fcf7b524b707fbcb72828551237ab545bb5c7034af | |
| MD5 | c39a9e7ac78644cf4f13a49c38de6cc4 | |
| BLAKE2b-256 | a5e9e925ca7569cf9fb9701fd82503fee73eea5268fdb856bdd64947092d3daa | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-musllinux_1_2_aarch64.whl
 - Subject digest: c010f5581d9c612804cc59fcf7b524b707fbcb72828551237ab545bb5c7034af
 - Sigstore transparency entry: 2474093125
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 243.1 kB
- Tags: CPython 3.14t, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 0c6dfb5ca6723eeed15aa8e564a014d69fcb8812f94eef11fe3631e0508199f5 | |
| MD5 | db4aa542ef18ad7b89f3b3f30c65673e | |
| BLAKE2b-256 | c425d5f4198819e6059735a84e8d0bfb72dc33976da67b97adcd3fb5a5e07ec6 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 0c6dfb5ca6723eeed15aa8e564a014d69fcb8812f94eef11fe3631e0508199f5
 - Sigstore transparency entry: 2474076165
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 249.3 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 58d4aa13a59c969dbfdf9e6a9560e242cbfd9e8a8f50c2747714df1a423adf65 | |
| MD5 | cfb1616bde3322b1c84c9ea260f835d1 | |
| BLAKE2b-256 | 1beee4e10a94d51cd1ee638aa7e00b65399e6b2a4e8376ab6d2eac9f95586671 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 58d4aa13a59c969dbfdf9e6a9560e242cbfd9e8a8f50c2747714df1a423adf65
 - Sigstore transparency entry: 2474085685
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 259.9 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 256dd4d85d9e4dc595e2bc983c980e73f62ddeb3165c58b4c3dfe78c5c8548c1 | |
| MD5 | 5b4c44147079f68c5354eb650ee48a33 | |
| BLAKE2b-256 | 3e11e6f5b9a3d0e55b0ef7505cd3765cdd48f22db89994c947b316f52f801fd8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: 256dd4d85d9e4dc595e2bc983c980e73f62ddeb3165c58b4c3dfe78c5c8548c1
 - Sigstore transparency entry: 2474086416
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 260.8 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | a3a370082ce34d0612f421e15fe011c53bb1feff21a26d06ad4fb244dab5a375 | |
| MD5 | 7ed80b0391ee28e51aa837b4d82e0d55 | |
| BLAKE2b-256 | e9a3887c1642f0da26000b0e0652d91071113c0e72cea33952e225cf589f49a9 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: a3a370082ce34d0612f421e15fe011c53bb1feff21a26d06ad4fb244dab5a375
 - Sigstore transparency entry: 2474084221
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 227.9 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 7ac76cf9afd34929d76eb7fcb63be476a4853d8a96f0dcf2d0db68a0cbdf9885 | |
| MD5 | d37860e65a25e65631248b6e166a1288 | |
| BLAKE2b-256 | 06ae7ae8807410dfa33f8e6f1715740adeaafa8a816cc4cb33508f54b1f7c896 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: 7ac76cf9afd34929d76eb7fcb63be476a4853d8a96f0dcf2d0db68a0cbdf9885
 - Sigstore transparency entry: 2474053589
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 240.8 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | e71c909f353863b2b89c83de2ebed71ea6d0df8a6ef65a128193c5e650766bef | |
| MD5 | d3204b291da4b5675a832406997ef8b4 | |
| BLAKE2b-256 | 30c763565f860921457feba93bae6c86fb7746deb4cffeed2f375cb845318146 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: e71c909f353863b2b89c83de2ebed71ea6d0df8a6ef65a128193c5e650766bef
 - Sigstore transparency entry: 2474080811
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314t-macosx_10_15_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314t-macosx_10_15_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 381.7 kB
- Tags: CPython 3.14t, macOS 10.15+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314t-macosx_10_15_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | fbc597639158fd7c14d55e808718848319540f51b0e6746e3eefa59723a4a348 | |
| MD5 | 88c2e1d5e8e9f2c09926cf5e4872c5c1 | |
| BLAKE2b-256 | 1c6cc73fa9d5a85f6ab05395de61c5f6984e0a9ff40bb5ff888d46dff02526c6 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314t-macosx_10_15_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314t-macosx_10_15_universal2.whl
 - Subject digest: fbc597639158fd7c14d55e808718848319540f51b0e6746e3eefa59723a4a348
 - Sigstore transparency entry: 2474077346
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 184.1 kB
- Tags: CPython 3.14, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 4bea7f8ebe90bbd7f0e4a2de42ca6924ba23e3e76418c408ff82f1d46fabd687 | |
| MD5 | 5f1c00e17ad7366c2daf90c2e2e4f866 | |
| BLAKE2b-256 | ac33eeb384dbd8dec570661354592f4f2e1b2fcc92585624d146a000caf53841 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-win_arm64.whl
 - Subject digest: 4bea7f8ebe90bbd7f0e4a2de42ca6924ba23e3e76418c408ff82f1d46fabd687
 - Sigstore transparency entry: 2474095609
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 204.2 kB
- Tags: CPython 3.14, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | c658c50ac0c98cd755a2dd50b7977d3bca7df401dcc47fbdfa87db53ef7d4e8b | |
| MD5 | 3218551938009322c595c32536dcff6c | |
| BLAKE2b-256 | 7a7c4938c329b6a9d446f6a59aa2092ff7118f274209b5ed0e26893d1d30a63c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl
 - Subject digest: c658c50ac0c98cd755a2dd50b7977d3bca7df401dcc47fbdfa87db53ef7d4e8b
 - Sigstore transparency entry: 2474064725
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 180.3 kB
- Tags: CPython 3.14, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 1f5883d77fd409a261abb5dc8ccbe335720d798b1de4abb3b1d47ccbbc76b53b | |
| MD5 | 79b19ed495170bc56ae43f8d23433e9f | |
| BLAKE2b-256 | f3461d362e1a00d035d66b9869e1281eee115907f7e390a16a07824ab5737360 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-win32.whl
 - Subject digest: 1f5883d77fd409a261abb5dc8ccbe335720d798b1de4abb3b1d47ccbbc76b53b
 - Sigstore transparency entry: 2474055791
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl
- Upload date:
 Aug 15, 2026
- Size: 140.6 kB
- Tags: CPython 3.14, PyEmscripten 2026.0 wasm32
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl
| Algorithm | Hash digest | |
| SHA256 | f03ac127268b43ef4fe9e6ab6794a6794b49485a0cc0c1db79876d2f33f75bc7 | |
| MD5 | 6fe532ee013cebcad8fbbce8c235b35c | |
| BLAKE2b-256 | a02a6a9034b7d3c60b17499afb482df5878bf9fa20b50cc3887d5ef017a833db | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-pyemscripten_2026_0_wasm32.whl
 - Subject digest: f03ac127268b43ef4fe9e6ab6794a6794b49485a0cc0c1db79876d2f33f75bc7
 - Sigstore transparency entry: 2474089956
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 253.1 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 9ac4444d8d4fd4c4bd08bf451ed3167aa9e7ec6cdb41b648794f1d1103652e36 | |
| MD5 | 84075c80ebdd0c70a7df149382c91728 | |
| BLAKE2b-256 | 4fab74a55fd803916a35ac461daf002708191aac19b546b80dc8cabfedc63d98 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_x86_64.whl
 - Subject digest: 9ac4444d8d4fd4c4bd08bf451ed3167aa9e7ec6cdb41b648794f1d1103652e36
 - Sigstore transparency entry: 2474050103
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 264.5 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 6c9cdde8becb25a7fde49924511aa2644d6f8081cc8df8e9452724303348d8e3 | |
| MD5 | 32815ed080ad3d3465a7e9f508e3ac30 | |
| BLAKE2b-256 | 7e3fffb64458527c7668031d5eb095d978de561958dc9f5b53f8e488a533e603 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_s390x.whl
 - Subject digest: 6c9cdde8becb25a7fde49924511aa2644d6f8081cc8df8e9452724303348d8e3
 - Sigstore transparency entry: 2474054442
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 245.8 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | fce8cbd4997efeb450bd298b54f755dcdff18d496f7a5ddbb4867c6d7c88fdc3 | |
| MD5 | 1b5cb73c46bd3ff9090f356000038b00 | |
| BLAKE2b-256 | 3dbb618749d70f792b44252a777bf89bfb86823b9bbc1ea13fe8ce759b07f38a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_riscv64.whl
 - Subject digest: fce8cbd4997efeb450bd298b54f755dcdff18d496f7a5ddbb4867c6d7c88fdc3
 - Sigstore transparency entry: 2474079675
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 266.7 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | bb57753e36e4855b8ca375069482250a6246372331a3e4f3407eaebb007443f5 | |
| MD5 | 869c9d693976592d0adf0791d372088c | |
| BLAKE2b-256 | 855446000450ada53bd9eac5429a2c8c54cd2d9b39c0c255f229aea9af0948a5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_ppc64le.whl
 - Subject digest: bb57753e36e4855b8ca375069482250a6246372331a3e4f3407eaebb007443f5
 - Sigstore transparency entry: 2474080249
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 231.4 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 329fc3ccb63ad22d867d84c2adea759a64079a37ba4a343433b02c7a2816871e | |
| MD5 | 898291f5ea7b41d05fd3fa99a91298b0 | |
| BLAKE2b-256 | c1ce9962938e179cf9f699d3f1e7b3114b5d7642dee6a893745229f9dd04f274 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_armv7l.whl
 - Subject digest: 329fc3ccb63ad22d867d84c2adea759a64079a37ba4a343433b02c7a2816871e
 - Sigstore transparency entry: 2474061944
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 244.6 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 01e93745f7f219b703b60ba7afead36cfc4242782be5af484673fc500df12da5 | |
| MD5 | ef65dd18d8e3bab7101696fab956423c | |
| BLAKE2b-256 | cca4689bb42e8e7cd492f3cb64907c6bc00ad247ec9a3628cd3f8eed126e8ae1 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-musllinux_1_2_aarch64.whl
 - Subject digest: 01e93745f7f219b703b60ba7afead36cfc4242782be5af484673fc500df12da5
 - Sigstore transparency entry: 2474051230
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 245.3 kB
- Tags: CPython 3.14, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 823f82903d189af463d7df250ef1f7f696f3cee08cc8d91deb565e8d425f6506 | |
| MD5 | 03ca9ac4bb89949a55d0f05fefcfc0eb | |
| BLAKE2b-256 | 1ca5cbe418bbc6ecdfc3e05a0116002897c4b403a5e838d697e64c78e9f0190d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 823f82903d189af463d7df250ef1f7f696f3cee08cc8d91deb565e8d425f6506
 - Sigstore transparency entry: 2474054032
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 251.2 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 15f024313246a4ed976c60f440bb8d257815513a681d212ff74fd46f7d715a90 | |
| MD5 | 3bdfef68a8f2e424abc15ae2dc57bf76 | |
| BLAKE2b-256 | e09139c3af510b0aa32bbda03374259200f28430febfd1bf5e511fe765282ce5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 15f024313246a4ed976c60f440bb8d257815513a681d212ff74fd46f7d715a90
 - Sigstore transparency entry: 2474072255
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 263.1 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | f6f7deae3feb4edfa2efaf7c574fe88cbf055038a6abdb40188e4fff66d5699f | |
| MD5 | f6dd8afd59b9f8c14a97f6e17fbef837 | |
| BLAKE2b-256 | 88be55127bfca72c0cff6c022488d140d7c5b04c771e3b72e9bdb4836d54979d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: f6f7deae3feb4edfa2efaf7c574fe88cbf055038a6abdb40188e4fff66d5699f
 - Sigstore transparency entry: 2474075481
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 266.1 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | ab743e9bc90c1f73552ec33e10e3331315acd2c397b36065b591b0181de533cc | |
| MD5 | 4ed00d23c9b88aa74371962dee1fe224 | |
| BLAKE2b-256 | 8a76c681192bbda3d55356db5dadd64381d5202b37c6b598fcda5282e88b5d3d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: ab743e9bc90c1f73552ec33e10e3331315acd2c397b36065b591b0181de533cc
 - Sigstore transparency entry: 2474090302
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 226.7 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 6b7430cf5728e68f6c462254009a6ef4086e1bea43cf2f57aa9c55fb4f50ff96 | |
| MD5 | f21a2ff829069c2a18246f2db685b546 | |
| BLAKE2b-256 | 2295b4618ce912e6db0b1aae89ba788e38e8a7eba0f3025cc66e8c0699f977b2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: 6b7430cf5728e68f6c462254009a6ef4086e1bea43cf2f57aa9c55fb4f50ff96
 - Sigstore transparency entry: 2474073119
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 242.5 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 2f06b7eae9dbe77fe1d644ca244dad508de8d302870a43f3c559b521270938a0 | |
| MD5 | 2fa8ce874e8de15db1e24d2e859d67d6 | |
| BLAKE2b-256 | f15a0e58b1c04a1596e0256f407274a92d5fb2ee21324409d1fab1da48a65b5b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 2f06b7eae9dbe77fe1d644ca244dad508de8d302870a43f3c559b521270938a0
 - Sigstore transparency entry: 2474049475
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-macosx_10_15_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-macosx_10_15_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 341.8 kB
- Tags: CPython 3.14, macOS 10.15+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-macosx_10_15_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | c428c6c31eb5f4277d7f8eccaf767fbd548ddd5ce3c8b4f4cbbfab3d96b5904c | |
| MD5 | 43aea3c2ddad002cff5fc4ec7257b955 | |
| BLAKE2b-256 | e940095ce62fa078483cccc1fa2b36e6bc9580b85422a20ee9f925341c50e44f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-macosx_10_15_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-macosx_10_15_universal2.whl
 - Subject digest: c428c6c31eb5f4277d7f8eccaf767fbd548ddd5ce3c8b4f4cbbfab3d96b5904c
 - Sigstore transparency entry: 2474075765
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphonesimulator.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphonesimulator.whl
- Upload date:
 Aug 15, 2026
- Size: 198.2 kB
- Tags: CPython 3.14, iOS 13.0+ ARM64 Simulator
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphonesimulator.whl
| Algorithm | Hash digest | |
| SHA256 | 4c9548dc78002099910abaebc0a72ac58b7d30931869e0351c09b507dff4ece3 | |
| MD5 | b742a484819dbb7498fc5c2cea0abf17 | |
| BLAKE2b-256 | 7476f2fc7380f056cc273a53af37f50d08ad54b2c59f61078f31432edcf1c2bd | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphonesimulator.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphonesimulator.whl
 - Subject digest: 4c9548dc78002099910abaebc0a72ac58b7d30931869e0351c09b507dff4ece3
 - Sigstore transparency entry: 2474076752
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphoneos.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphoneos.whl
- Upload date:
 Aug 15, 2026
- Size: 194.8 kB
- Tags: CPython 3.14, iOS 13.0+ ARM64 Device
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphoneos.whl
| Algorithm | Hash digest | |
| SHA256 | 09a7bba9f739468c8e78c36a75c33768e53cb1959fc638f510454c14683f00d5 | |
| MD5 | 8244e2ea077c5cf999756b3415786aa5 | |
| BLAKE2b-256 | c3d935ae3f64f29d0179c35c3baefe575904df2913dde519129c7f75995a2b1d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphoneos.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-ios_13_0_arm64_iphoneos.whl
 - Subject digest: 09a7bba9f739468c8e78c36a75c33768e53cb1959fc638f510454c14683f00d5
 - Sigstore transparency entry: 2474048957
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-android_24_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-android_24_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 224.9 kB
- Tags: Android API level 24+ x86-64, CPython 3.14
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-android_24_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 26422d45fd13551cf564c58932f7d72b4f58b93b0fcf18c35ba6be12b46bb102 | |
| MD5 | 8fec484afa0c4d8b3cc92ba97f67491c | |
| BLAKE2b-256 | 9e4aa6ee107430768a5334e6d63f31f148a04a1a491ef161a1ac9415a73f2fa8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-android_24_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-android_24_x86_64.whl
 - Subject digest: 26422d45fd13551cf564c58932f7d72b4f58b93b0fcf18c35ba6be12b46bb102
 - Sigstore transparency entry: 2474058056
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp314-cp314-android_24_arm64_v8a.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp314-cp314-android_24_arm64_v8a.whl
- Upload date:
 Aug 15, 2026
- Size: 212.3 kB
- Tags: Android API level 24+ ARM64 v8a, CPython 3.14
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp314-cp314-android_24_arm64_v8a.whl
| Algorithm | Hash digest | |
| SHA256 | 774d157f112367ff4abd29019f38f023c24e00e56edc7829c20e358a5a913ad8 | |
| MD5 | 88fa9e3fbc70323962bd796b6c6d5a7d | |
| BLAKE2b-256 | 29cd2b812ce5e888f1ce69a5350281e58aab07ae64a958ecae8912f30865718e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp314-cp314-android_24_arm64_v8a.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp314-cp314-android_24_arm64_v8a.whl
 - Subject digest: 774d157f112367ff4abd29019f38f023c24e00e56edc7829c20e358a5a913ad8
 - Sigstore transparency entry: 2474050277
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 179.9 kB
- Tags: CPython 3.13, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | fd0a274c0e5f9a21565cd9d3dd749b61f96b7aa1e20a93aa1ba4029518f2e5c0 | |
| MD5 | 39fff24db6eb2f221a34eb7c58e50535 | |
| BLAKE2b-256 | 5b755b20dd1e6573a01a08158fe104104fa2c8abf941745596954185726cd46c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-win_arm64.whl
 - Subject digest: fd0a274c0e5f9a21565cd9d3dd749b61f96b7aa1e20a93aa1ba4029518f2e5c0
 - Sigstore transparency entry: 2474085290
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 199.3 kB
- Tags: CPython 3.13, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | aea996a6aba25260827c9ea511d1addfde2da9eb686ac961838509086188b7e6 | |
| MD5 | 7b97124d4594b49bbed646d08cf8b651 | |
| BLAKE2b-256 | 8a3356d97ade41c8db611e727168c52ae46c9224c362ec28d4b65d7e9869e8da | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-win_amd64.whl
 - Subject digest: aea996a6aba25260827c9ea511d1addfde2da9eb686ac961838509086188b7e6
 - Sigstore transparency entry: 2474052921
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 177.8 kB
- Tags: CPython 3.13, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-win32.whl
| Algorithm | Hash digest | |
| SHA256 | d63600d620ad0064c3a748b950ac5ea38a80190e5498532efefa4b7b3f1da1f3 | |
| MD5 | 331586640ee1d4261a9554eb8e59c2a0 | |
| BLAKE2b-256 | b4d4703be739b26acce318bd29eb3b25b7209e1b1f527f9eae3d1f1f01fdde2b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-win32.whl
 - Subject digest: d63600d620ad0064c3a748b950ac5ea38a80190e5498532efefa4b7b3f1da1f3
 - Sigstore transparency entry: 2474069946
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-pyemscripten_2025_0_wasm32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-pyemscripten_2025_0_wasm32.whl
- Upload date:
 Aug 15, 2026
- Size: 140.4 kB
- Tags: CPython 3.13, PyEmscripten 2025.0 wasm32
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-pyemscripten_2025_0_wasm32.whl
| Algorithm | Hash digest | |
| SHA256 | 9d9a0dc7cbe9bec24c3f767c9122c41fe5a1bc43f47cd099d00d393e09769de4 | |
| MD5 | 634ac15793a418265a9b2c6a7e4ec402 | |
| BLAKE2b-256 | 764e362d4f9fdcdf5556fb2aa3ce7d4a58ebce03ed1ff03aa1d9aca8d02f13f3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-pyemscripten_2025_0_wasm32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-pyemscripten_2025_0_wasm32.whl
 - Subject digest: 9d9a0dc7cbe9bec24c3f767c9122c41fe5a1bc43f47cd099d00d393e09769de4
 - Sigstore transparency entry: 2474074807
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 252.6 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | fd0350afdc3aabd5576f60ea109228bd5538139713c7b094c5cd27c73a98bc6f | |
| MD5 | 0acf1ada68b23398195f197b24da92b7 | |
| BLAKE2b-256 | 90c6b09e05e6db7f64338e0dc067c79577b1138da86c1e38369096851d96be88 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_x86_64.whl
 - Subject digest: fd0350afdc3aabd5576f60ea109228bd5538139713c7b094c5cd27c73a98bc6f
 - Sigstore transparency entry: 2474083435
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 261.7 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 35fe081843b35aad20ffeccec3eeffbe637b15d14f3fb22cc1b59cd8ec17e93c | |
| MD5 | ec72aebdf0310d7b6568569c3e6aa8f0 | |
| BLAKE2b-256 | 372e651d910af6d0fba325eee1cda37ec5443462ed25360e666c144166eb6091 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_s390x.whl
 - Subject digest: 35fe081843b35aad20ffeccec3eeffbe637b15d14f3fb22cc1b59cd8ec17e93c
 - Sigstore transparency entry: 2474069331
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 245.2 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 90b7481fb62fbe172c558bc6fd1c4c98d82004a54a7551f20e11ac9bf0b8708c | |
| MD5 | d3414cfb2045a9c229da8c64fee2a147 | |
| BLAKE2b-256 | 5c6412b4c2a11ee8df4fcc518c78b0d93e3a92bd3d5253d1617ce74ff0e8c7ef | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_riscv64.whl
 - Subject digest: 90b7481fb62fbe172c558bc6fd1c4c98d82004a54a7551f20e11ac9bf0b8708c
 - Sigstore transparency entry: 2474091985
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 264.5 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 5c0ea61a470e070686aa30892fed79e297d2c8d0ab46b8bcdf027d38c51da591 | |
| MD5 | 97ec02b9fbacda50593c953c189e2756 | |
| BLAKE2b-256 | bd670f40eaf8d1b6e7cf15e82382a2965efaca787fc1c2794b7021d37aaf5036 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_ppc64le.whl
 - Subject digest: 5c0ea61a470e070686aa30892fed79e297d2c8d0ab46b8bcdf027d38c51da591
 - Sigstore transparency entry: 2474078044
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 233.7 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 485a0d363cafefcd2538a73c7c838daa2035f09b2c9f9b5e3133f80c6aeb84c2 | |
| MD5 | 0ae82e48acc48bde470c7c24d2679b08 | |
| BLAKE2b-256 | dbab55e683ba0fff2e43adafc10daa3001eac90fdaa419a97227d5a7067eedde | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_armv7l.whl
 - Subject digest: 485a0d363cafefcd2538a73c7c838daa2035f09b2c9f9b5e3133f80c6aeb84c2
 - Sigstore transparency entry: 2474066185
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 242.0 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | c71fb0d56c920c269cd3e2e3fe7c610e3f1fdb21a6ce60efa6430ff63676cea6 | |
| MD5 | 9efc0886d344ae3021f0f9dd74915fd3 | |
| BLAKE2b-256 | c024ef36367d38b9ddd4bccbf72888c342e8de1f5ae506fa0b2dcf970e2732a1 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-musllinux_1_2_aarch64.whl
 - Subject digest: c71fb0d56c920c269cd3e2e3fe7c610e3f1fdb21a6ce60efa6430ff63676cea6
 - Sigstore transparency entry: 2474077546
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 244.6 kB
- Tags: CPython 3.13, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | fa48b1b63d639f9483e0633e092f5851e2348c352f1f9bb6c8182f87884ef876 | |
| MD5 | f18ac18c440c52b2a0a54ba1df61ca10 | |
| BLAKE2b-256 | 4d6670dfad64f15be09c15ccfee81330a7e515895dbe296dd23114e9a231268a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: fa48b1b63d639f9483e0633e092f5851e2348c352f1f9bb6c8182f87884ef876
 - Sigstore transparency entry: 2474065658
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 250.6 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 62b55f6722735a6c472f88361cde6640608773d9443cebdbb51abf436a1fcdd3 | |
| MD5 | 17141d55e039a089f923a4daef827047 | |
| BLAKE2b-256 | fbaf63240b0c0248c075c2535a1f1bd992821d8251b9f173abc13329661d09e4 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 62b55f6722735a6c472f88361cde6640608773d9443cebdbb51abf436a1fcdd3
 - Sigstore transparency entry: 2474091780
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 260.4 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 394fea06235c8543390050ed5f529187074b029fb027213f6c46ac11ab5d950e | |
| MD5 | 61f1f344f52ba067bab7452d95beccc8 | |
| BLAKE2b-256 | 7ac2071575791dcc88316c0a9a65ce38897a82e4cfe4a325f0f7fe1b1ac47bcf | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: 394fea06235c8543390050ed5f529187074b029fb027213f6c46ac11ab5d950e
 - Sigstore transparency entry: 2474073723
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 263.7 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 0d929fc574b4d6fd9e7c0f5c2ede8716a41911923aa7fa5fce38e0818aa4a1ac | |
| MD5 | 283c620ba4c70f799035a646f529fde8 | |
| BLAKE2b-256 | ce485a97e84d63af1d55c07439cb80e56d99a8efb4295700eb4e18c0d1615d2c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: 0d929fc574b4d6fd9e7c0f5c2ede8716a41911923aa7fa5fce38e0818aa4a1ac
 - Sigstore transparency entry: 2474087657
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 228.2 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | d59b75732e9b6f27388e10c14b0259cc5f2e48c78627d185e6a177b58ad3cffe | |
| MD5 | 91f704593c8eb4726b6b71ca53b8c6fd | |
| BLAKE2b-256 | 095327923ce5cc6cbccb832037b27dca98882d9c53e9b69e866bbbef4aae7fc8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: d59b75732e9b6f27388e10c14b0259cc5f2e48c78627d185e6a177b58ad3cffe
 - Sigstore transparency entry: 2474066771
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 240.2 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 94d78ecec2605a8d0398b0f365d5f12a63248438516f5dac536a5eff7337df4a | |
| MD5 | 5d6d216742f55f99cb150a29685248a1 | |
| BLAKE2b-256 | 31e71d994be1b93d41e9502b8b0460eaa88a1dd8df335df415db87d6c3e91ab2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 94d78ecec2605a8d0398b0f365d5f12a63248438516f5dac536a5eff7337df4a
 - Sigstore transparency entry: 2474049837
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-macosx_10_13_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-macosx_10_13_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 340.5 kB
- Tags: CPython 3.13, macOS 10.13+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-macosx_10_13_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | e90251c0c7bdd54a100a0dce3c07b7e637278c93af29dbf78ebb89a58c4bac7d | |
| MD5 | 9dc36432e623673034222b137cc65077 | |
| BLAKE2b-256 | a4a0562247944386f7d4ef94467e84876600cc1e0f1b93239aaa9213d2bc3cbd | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-macosx_10_13_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-macosx_10_13_universal2.whl
 - Subject digest: e90251c0c7bdd54a100a0dce3c07b7e637278c93af29dbf78ebb89a58c4bac7d
 - Sigstore transparency entry: 2474064105
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphonesimulator.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphonesimulator.whl
- Upload date:
 Aug 15, 2026
- Size: 197.7 kB
- Tags: CPython 3.13, iOS 13.0+ ARM64 Simulator
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphonesimulator.whl
| Algorithm | Hash digest | |
| SHA256 | 977cdbd483a9cff38179bea4fd754289a6f2195c7abd414aba85410b3e66cc5e | |
| MD5 | f82be8ace744600292afbd4cbadf0b8c | |
| BLAKE2b-256 | de93d51ec556e01042fed6f993ea859311bc7917b466684182fbbceb6ca24762 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphonesimulator.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphonesimulator.whl
 - Subject digest: 977cdbd483a9cff38179bea4fd754289a6f2195c7abd414aba85410b3e66cc5e
 - Sigstore transparency entry: 2474091575
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphoneos.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphoneos.whl
- Upload date:
 Aug 15, 2026
- Size: 194.5 kB
- Tags: CPython 3.13, iOS 13.0+ ARM64 Device
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphoneos.whl
| Algorithm | Hash digest | |
| SHA256 | 9362dd90aa7dab48c0054a21187791ccf05473f7dba5d92b8033ae62164675e7 | |
| MD5 | 0293d2410ee0bf476ad27f2f646623b1 | |
| BLAKE2b-256 | 090ad3646670292ce8d8f8cc11ac067d44885e697a5591f57a9221128da5e7b3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphoneos.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-ios_13_0_arm64_iphoneos.whl
 - Subject digest: 9362dd90aa7dab48c0054a21187791ccf05473f7dba5d92b8033ae62164675e7
 - Sigstore transparency entry: 2474092500
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-android_24_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-android_24_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 223.4 kB
- Tags: Android API level 24+ x86-64, CPython 3.13
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-android_24_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 88ca277405c2d3b71c4e1c2ee0e7966e807bcba86a69d11e19ba199d18ae4491 | |
| MD5 | 586125af1be4f216504fd943f109402b | |
| BLAKE2b-256 | 1857a305c968be1ca13f3dd1b32f445877e97addf55d80b65c7cb35fac82b777 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-android_24_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-android_24_x86_64.whl
 - Subject digest: 88ca277405c2d3b71c4e1c2ee0e7966e807bcba86a69d11e19ba199d18ae4491
 - Sigstore transparency entry: 2474072543
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp313-cp313-android_24_arm64_v8a.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp313-cp313-android_24_arm64_v8a.whl
- Upload date:
 Aug 15, 2026
- Size: 211.6 kB
- Tags: Android API level 24+ ARM64 v8a, CPython 3.13
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp313-cp313-android_24_arm64_v8a.whl
| Algorithm | Hash digest | |
| SHA256 | 4f298bdadb8f0b9e5672877f647d1be9373ef5320c9e2f049795e26cad28b6a9 | |
| MD5 | 7d63c75e2e01f5825761e6e5e489f29e | |
| BLAKE2b-256 | bc612cb6ad133dbbb449fa2d37ccae973232f4827e799af258d15e589a3d1e9e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp313-cp313-android_24_arm64_v8a.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp313-cp313-android_24_arm64_v8a.whl
 - Subject digest: 4f298bdadb8f0b9e5672877f647d1be9373ef5320c9e2f049795e26cad28b6a9
 - Sigstore transparency entry: 2474062980
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 180.7 kB
- Tags: CPython 3.12, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 88e85ab89cb822c1e635f51d6d32e488f94e002e70e2f492bdb8b945543f345a | |
| MD5 | e15bfde1d705b091014656db0a0a8ee5 | |
| BLAKE2b-256 | cdd7eb95a042f0dd22e304b0b6472b154f3546a1a039a9ee89ccb2a7f61591fc | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-win_arm64.whl
 - Subject digest: 88e85ab89cb822c1e635f51d6d32e488f94e002e70e2f492bdb8b945543f345a
 - Sigstore transparency entry: 2474048803
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 200.6 kB
- Tags: CPython 3.12, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 3617ac3cfd8b9888f145ad89dd6e692285834b0201c6074a5eeaad3fd4d668c2 | |
| MD5 | 54121dc3ed00423eac0a1330bd33e774 | |
| BLAKE2b-256 | 9d7a4c6c298171e6b3e745633180ff59350fc0ca0db1ffd28df1e369e0579f71 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-win_amd64.whl
 - Subject digest: 3617ac3cfd8b9888f145ad89dd6e692285834b0201c6074a5eeaad3fd4d668c2
 - Sigstore transparency entry: 2474079255
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 178.5 kB
- Tags: CPython 3.12, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-win32.whl
| Algorithm | Hash digest | |
| SHA256 | cfa1c0cc3a8f9f53f1243a5a99ac36fd003880199383b37672e86ddda9cb07e2 | |
| MD5 | 1622551ee01be5aefe2b27276230e9c0 | |
| BLAKE2b-256 | 621646556278c2168d12df9da7fede5dc6fc70e60301b26a82bbeec238c9cfe3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-win32.whl
 - Subject digest: cfa1c0cc3a8f9f53f1243a5a99ac36fd003880199383b37672e86ddda9cb07e2
 - Sigstore transparency entry: 2474048152
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 250.6 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | ba501e667c17d8411f98e67a022d9604ef179aff0e459b7e292c796837c13573 | |
| MD5 | 398450e392ac9c7588ee678287e7c5f1 | |
| BLAKE2b-256 | b752643d11ffd60e9ac2fd1fb87e167a19285b9eefeff4a40e63c87cbfbeab36 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_x86_64.whl
 - Subject digest: ba501e667c17d8411f98e67a022d9604ef179aff0e459b7e292c796837c13573
 - Sigstore transparency entry: 2474051517
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 260.2 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 4abdc5f9ad448c1ecbfae2974b820535d6bc6e7eef63babbab3d81cf46968c71 | |
| MD5 | b9576c6a47f8ac37c6c1a474ae41cb1f | |
| BLAKE2b-256 | ca85f82f8a92e31c7519410e2e1afdc630f28ec47490ce2c09a11c1a43cbb459 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_s390x.whl
 - Subject digest: 4abdc5f9ad448c1ecbfae2974b820535d6bc6e7eef63babbab3d81cf46968c71
 - Sigstore transparency entry: 2474067274
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 243.0 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 7235dc28fc6dd9d832ac7c7bce95367dedb85929f17368a0c2bee1e080b9acbf | |
| MD5 | 5fbebcf348d8005f06958a8a62af58e6 | |
| BLAKE2b-256 | 355a337e4663a5eae6de99db940ee8066d4145caafb61327db62deda15313cce | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_riscv64.whl
 - Subject digest: 7235dc28fc6dd9d832ac7c7bce95367dedb85929f17368a0c2bee1e080b9acbf
 - Sigstore transparency entry: 2474058636
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 262.7 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | aae2ee51122d3ae968a3837d97dc24a0aeebb0dea23694422cd172bd30017cd6 | |
| MD5 | 8cb9b82bd66573f04301ada619ac8a09 | |
| BLAKE2b-256 | f9d2d2aad6fe0dbb44b194bf3becb60f5a0ac48446ade999a47fe7bb41eb09a7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_ppc64le.whl
 - Subject digest: aae2ee51122d3ae968a3837d97dc24a0aeebb0dea23694422cd172bd30017cd6
 - Sigstore transparency entry: 2474078459
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 232.8 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 5d8531a6569d025f68e2321e7638fb7978f23db58e5f69f56913837aae03816e | |
| MD5 | e23ec1db8053e97e2916859d31a6dbfd | |
| BLAKE2b-256 | 4622111e5be3b740d5c2a5bfcedb3d237b6591e5c2e82ae9d6ffcb121fe0909c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_armv7l.whl
 - Subject digest: 5d8531a6569d025f68e2321e7638fb7978f23db58e5f69f56913837aae03816e
 - Sigstore transparency entry: 2474084435
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 240.1 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 96fef3e886d6a9874b14f27fc193fbdc69d5d8035783d86aa4e1cea594e695f9 | |
| MD5 | 34cdc0e52d693e5878a9fd561900b1e2 | |
| BLAKE2b-256 | f60bc5292a2462d69b7378ea89793bbb5b2b6fcf6f7dd6d1667f9619094ad553 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-musllinux_1_2_aarch64.whl
 - Subject digest: 96fef3e886d6a9874b14f27fc193fbdc69d5d8035783d86aa4e1cea594e695f9
 - Sigstore transparency entry: 2474049579
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 244.1 kB
- Tags: CPython 3.12, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | f9f8405c2c758532c74fed975dbee57be1f31a6e865c031870c79a6ed3212ada | |
| MD5 | ddcdf9ec316149272d5bc74763b04e89 | |
| BLAKE2b-256 | b1baef83ae3aca816393decfa3530976f38a79812d707b80b580ac33b83f9877 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: f9f8405c2c758532c74fed975dbee57be1f31a6e865c031870c79a6ed3212ada
 - Sigstore transparency entry: 2474067115
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 248.8 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | b9af956078716df40d985fb0dfeb2c2120c5ca92ba4ff4b388acfd01cdc14d08 | |
| MD5 | 7388b44e08ae94885694fc80d8646898 | |
| BLAKE2b-256 | 6f89bb5108dc6c3651dca963f2b0a3ba19bbcb370c94e1b6d3e0e844a58e6dca | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: b9af956078716df40d985fb0dfeb2c2120c5ca92ba4ff4b388acfd01cdc14d08
 - Sigstore transparency entry: 2474081728
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 259.0 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 7c0c10730342b0c9b35dd1d619beb8214e520bd96a1f870f452680b238aab3e0 | |
| MD5 | d4a4e8857297e97d2c760a4a26ad07f4 | |
| BLAKE2b-256 | 38fe341861ac118dae06f3ec0eb487488af52128f2ef2faf0b11003944d22259 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: 7c0c10730342b0c9b35dd1d619beb8214e520bd96a1f870f452680b238aab3e0
 - Sigstore transparency entry: 2474094545
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 262.2 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | e6621fb2a4988d6e53eedc455e5903e2679f3967b8acb3d639f1b63c14a2e893 | |
| MD5 | fe64fb7d269ce53386e45bdd399e2117 | |
| BLAKE2b-256 | e7a047b18adeed31c8f16ba9700f32c1b18594cfa09f47eb672a488c273c22bf | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: e6621fb2a4988d6e53eedc455e5903e2679f3967b8acb3d639f1b63c14a2e893
 - Sigstore transparency entry: 2474080418
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 230.2 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 1d1c7a53a6c2103925cdd6d7229f8c567379f211c869793df679f2e9f738c369 | |
| MD5 | 292d4d472eaa10746c500dda5e1246cf | |
| BLAKE2b-256 | 76846f1290fa07ae6978d3960caa3eb1b8019bf9284ab7c2297b00c099ef4250 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: 1d1c7a53a6c2103925cdd6d7229f8c567379f211c869793df679f2e9f738c369
 - Sigstore transparency entry: 2474095320
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 238.5 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 4582c27e8c889d64811987b5967fbd3ae0c823fe1fd933b543d55ac20bb475fa | |
| MD5 | 6d0887e56af7bd65d991df598b14ae82 | |
| BLAKE2b-256 | 9a4cbe49ada26b1f0232d57aa89bbebf997a5cc2332a5616b6eca26ff680044d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 4582c27e8c889d64811987b5967fbd3ae0c823fe1fd933b543d55ac20bb475fa
 - Sigstore transparency entry: 2474095743
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp312-cp312-macosx_10_13_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp312-cp312-macosx_10_13_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 344.5 kB
- Tags: CPython 3.12, macOS 10.13+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp312-cp312-macosx_10_13_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | 5b6d1386bf0096d26d3a863dc0a487a5b4eb9aa93cf5ba69683d29dde6b9d60f | |
| MD5 | 097be59bba3ec9568db95ec1ae692575 | |
| BLAKE2b-256 | 302778873dc8b6a56357517b74b6bb9568b80450e7bb4f6ef7e3fa9d22aa0bd7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp312-cp312-macosx_10_13_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp312-cp312-macosx_10_13_universal2.whl
 - Subject digest: 5b6d1386bf0096d26d3a863dc0a487a5b4eb9aa93cf5ba69683d29dde6b9d60f
 - Sigstore transparency entry: 2474088490
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 185.6 kB
- Tags: CPython 3.11, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | ae31a1a1db2ee6cc2942fccaf695c934bc7f3db9f2133a3fef1f367cf1a4ab10 | |
| MD5 | f9a94008845f7039a1923ab4f0277cb1 | |
| BLAKE2b-256 | 17d4b65c433fc521e58b5f54293982a5e51c05cb5f2dd3f1c7a6acb65b75324e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-win_arm64.whl
 - Subject digest: ae31a1a1db2ee6cc2942fccaf695c934bc7f3db9f2133a3fef1f367cf1a4ab10
 - Sigstore transparency entry: 2474050674
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 206.7 kB
- Tags: CPython 3.11, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | f9b1e28d0e8dbfa858abdba91d6b547beaf2df1a59bec6da6faae7b96a4991a9 | |
| MD5 | c616374a1e104e9b5108df79c29cf868 | |
| BLAKE2b-256 | e35732f0ccea59e8612057c61d6fd22ef2cb63cca93c9fe594094919696ac170 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-win_amd64.whl
 - Subject digest: f9b1e28d0e8dbfa858abdba91d6b547beaf2df1a59bec6da6faae7b96a4991a9
 - Sigstore transparency entry: 2474082219
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 181.8 kB
- Tags: CPython 3.11, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-win32.whl
| Algorithm | Hash digest | |
| SHA256 | ac00177c4831ffa650f8609e4bdddd5fe09c03b1c0c47acece7e6ea20421598b | |
| MD5 | 130d7584dd83c9dee8f577f561914211 | |
| BLAKE2b-256 | 37ab4e4510e1e288478e2c8333131d1c1382382ba8cd2165053c79e39d1da961 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-win32.whl
 - Subject digest: ac00177c4831ffa650f8609e4bdddd5fe09c03b1c0c47acece7e6ea20421598b
 - Sigstore transparency entry: 2474062466
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 263.4 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 3d27167433c0d5f18dc850f07d0b3816221984fecdc405d6c157a6f0b8f8e9e6 | |
| MD5 | 1239170d2930c4c27dd2b700575538d8 | |
| BLAKE2b-256 | bfeb239c84503cc9e3ba6eb34686a24bc66e84f3924efdd7e38e751a19f6bc10 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_x86_64.whl
 - Subject digest: 3d27167433c0d5f18dc850f07d0b3816221984fecdc405d6c157a6f0b8f8e9e6
 - Sigstore transparency entry: 2474067956
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 278.2 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 6e2912d4babbc65196ac13c2f53468dc57fb8b9c25ef913e8c59ddf7c6dc0e1b | |
| MD5 | c09313e527a7409d60c79abb3eb18de4 | |
| BLAKE2b-256 | baed1dd7cfebb4e75812934c49ca3b79757d11948053f7937ab7070c151f3c55 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_s390x.whl
 - Subject digest: 6e2912d4babbc65196ac13c2f53468dc57fb8b9c25ef913e8c59ddf7c6dc0e1b
 - Sigstore transparency entry: 2474095948
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 259.6 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | f298e218441525d3794428b4c8b8fb8662c6d3ea79925d4807ee6b9a96a3bca5 | |
| MD5 | d6d24b1fd261a1c8eae407def778860f | |
| BLAKE2b-256 | fd4c9044135f42127630b6fa742feb51256353f6ab87a78f2fdd1de3de955a7f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_riscv64.whl
 - Subject digest: f298e218441525d3794428b4c8b8fb8662c6d3ea79925d4807ee6b9a96a3bca5
 - Sigstore transparency entry: 2474050903
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 280.8 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | bd6c173f04743d483881bffa1478d5a4624475b8cd1d2194956a75548e191c18 | |
| MD5 | f08a901d9f44eb044108886695b8e151 | |
| BLAKE2b-256 | 4285f9e22af69af67c54cce42be9455d9c81294f918b4ccc454db01f66efcac2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_ppc64le.whl
 - Subject digest: bd6c173f04743d483881bffa1478d5a4624475b8cd1d2194956a75548e191c18
 - Sigstore transparency entry: 2474074142
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 240.7 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | aa1099b956fb795e686d073568f6dc002a0bb89765ea6d5b055dd7d9bf1b116c | |
| MD5 | a35ed6442b31b1e43fc9aa7935d813a9 | |
| BLAKE2b-256 | f03e48f4cd187b1c33189d86039e9cbe4f92c05454175504b44ff81806d4d1bf | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_armv7l.whl
 - Subject digest: aa1099b956fb795e686d073568f6dc002a0bb89765ea6d5b055dd7d9bf1b116c
 - Sigstore transparency entry: 2474088722
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 252.8 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 0722590aabf9dc6a6c0343d523c05458fa2b5047dbe6302fd526bb570600753f | |
| MD5 | f140b97b102db32a052371bb34caf979 | |
| BLAKE2b-256 | 28f00c0ceec6d98b7daa62e361e418135d59685811d79ba11529aad5cdf15e84 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-musllinux_1_2_aarch64.whl
 - Subject digest: 0722590aabf9dc6a6c0343d523c05458fa2b5047dbe6302fd526bb570600753f
 - Sigstore transparency entry: 2474077022
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 261.1 kB
- Tags: CPython 3.11, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 6ba32c4d2abf1d2fe7cf27d280f4cca5664233b0f885549c7761719eb977f486 | |
| MD5 | 4996a5de6a7458c35793516ba6adf7da | |
| BLAKE2b-256 | f528c2028e7021fb89c6e56868ed0e387b8e9aa811abdd2ab3208d6578d2c930 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 6ba32c4d2abf1d2fe7cf27d280f4cca5664233b0f885549c7761719eb977f486
 - Sigstore transparency entry: 2474072859
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 262.3 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | c7b742bf31c88566b4bb6335a7f393bb322e580b6bb98df7bd0c25e6e3519ce8 | |
| MD5 | ed58fbefdb35fbc4af32da6af72e4022 | |
| BLAKE2b-256 | 0d35731ac04aa0a097fc1c97f0994c375bdb230c6c96619db794208fe664e9ce | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: c7b742bf31c88566b4bb6335a7f393bb322e580b6bb98df7bd0c25e6e3519ce8
 - Sigstore transparency entry: 2474060724
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 276.6 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | b54e7e13267d49ffbfe68e25b3cbd774dab38fa37238f71265e91b36146eb21c | |
| MD5 | b7d044df096434f5345c002cb1200905 | |
| BLAKE2b-256 | 8238083a24028304bc85bb9e376fed801178423dcbb67495f73b6ea0624e1894 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: b54e7e13267d49ffbfe68e25b3cbd774dab38fa37238f71265e91b36146eb21c
 - Sigstore transparency entry: 2474080587
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 280.1 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 6e5e4d73d588ca5ed09df1b7dcd1b203d1df3c542e3f50d126c947d432b10731 | |
| MD5 | 97cc1ac17f8448747c482f9d41d71473 | |
| BLAKE2b-256 | e780b9348b5d3041209f98b4cdad7655766369233f1d533f4f4f7558e9717bec | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: 6e5e4d73d588ca5ed09df1b7dcd1b203d1df3c542e3f50d126c947d432b10731
 - Sigstore transparency entry: 2474077692
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 239.7 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 0b2b1b3fa5670c127b246df1d0c059defd41f689a868a3b9d79df9b1cac42d22 | |
| MD5 | 1c71888471c09ac18da2df52d0fbb25c | |
| BLAKE2b-256 | a4c8ab42b07cfd82e919f427fcfaa7c41abae8242833ad1aad66d42bae40b669 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: 0b2b1b3fa5670c127b246df1d0c059defd41f689a868a3b9d79df9b1cac42d22
 - Sigstore transparency entry: 2474094806
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 251.2 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | aa2bb0b37202dca27175591f761108b5d34096ade1191ffe4808bdf6b1571488 | |
| MD5 | dcf7828a32beba2bfedbaeec67623556 | |
| BLAKE2b-256 | d5fa6a7e2a7c4b5451912b8c417732df79574354443592a88d616de03da66ae5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: aa2bb0b37202dca27175591f761108b5d34096ade1191ffe4808bdf6b1571488
 - Sigstore transparency entry: 2474090650
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp311-cp311-macosx_10_9_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp311-cp311-macosx_10_9_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 363.6 kB
- Tags: CPython 3.11, macOS 10.9+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp311-cp311-macosx_10_9_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | eda059b6bc8bc0812d626fd91a7ce01bf583df0a61296eff390fd94141a34e30 | |
| MD5 | b0ca635079adc58cf8f641ccb9dfbd3a | |
| BLAKE2b-256 | 6ab6034f6802e9c3f6418966cfabb7db8c9252cc2429c5098f41cc43af804149 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp311-cp311-macosx_10_9_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp311-cp311-macosx_10_9_universal2.whl
 - Subject digest: eda059b6bc8bc0812d626fd91a7ce01bf583df0a61296eff390fd94141a34e30
 - Sigstore transparency entry: 2474054689
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 185.1 kB
- Tags: CPython 3.10, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | a6d095662e73e74f0a49988e0593373e243e3a52e27bfeea0a859e88acf4a0f5 | |
| MD5 | c73fa2752c5d6888b5a7c6cf480f0261 | |
| BLAKE2b-256 | 862eb93135b5034b1157fb29554b0d06d4844ce62282f0e0a14036f93d7ee2e7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-win_arm64.whl
 - Subject digest: a6d095662e73e74f0a49988e0593373e243e3a52e27bfeea0a859e88acf4a0f5
 - Sigstore transparency entry: 2474074274
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 206.0 kB
- Tags: CPython 3.10, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | be47f99644b208bff7766314013f9acf57b056b04191d570d68ad14022cf5b1d | |
| MD5 | 0cff0394be71e5872d4645d23d23d74d | |
| BLAKE2b-256 | d22183fffb77864408b8bf0fe1ca603926401d6f8775a8e150b39aacc9958f8a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-win_amd64.whl
 - Subject digest: be47f99644b208bff7766314013f9acf57b056b04191d570d68ad14022cf5b1d
 - Sigstore transparency entry: 2474052550
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 182.0 kB
- Tags: CPython 3.10, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 94fbf1c0c6cc0d3d5e50f9a9313a8cdca90dd696d34b381cd1704f8c9e939f20 | |
| MD5 | caa5a59b24eea47de51ce62b5eec9647 | |
| BLAKE2b-256 | b723b38a20598d5a825f85d9d7636860e56ff0db1479f86497a6e485aa9326f7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-win32.whl
 - Subject digest: 94fbf1c0c6cc0d3d5e50f9a9313a8cdca90dd696d34b381cd1704f8c9e939f20
 - Sigstore transparency entry: 2474063401
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 263.8 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 494b70049a4d69aec6e8137c13af4cf8db8c9f9820a1392ac293b0dd2987a818 | |
| MD5 | 09ad6c09a941b8f291ad19d7863df1c6 | |
| BLAKE2b-256 | 58adb9aecf38d805cbcf84fa94f14c5d972a16561e20296a11dc799a5dcf3763 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_x86_64.whl
 - Subject digest: 494b70049a4d69aec6e8137c13af4cf8db8c9f9820a1392ac293b0dd2987a818
 - Sigstore transparency entry: 2474094297
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 277.2 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | a545775cfe815855ea32d7c27731d79da358ef2055b4a25830231b1622dd18aa | |
| MD5 | 8108e7901d1024a304f5e4224af07ee6 | |
| BLAKE2b-256 | b990082cc45599c392f28c036a497f49e0634041a785fc3849c80ccf396d096f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_s390x.whl
 - Subject digest: a545775cfe815855ea32d7c27731d79da358ef2055b4a25830231b1622dd18aa
 - Sigstore transparency entry: 2474056709
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 258.7 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | f5542f9b941279d82d41eb0aa9f98eba36fe4df5c7086c651df7944935b37182 | |
| MD5 | 6aa3d94c9ff94b097c1c57618da3b9e8 | |
| BLAKE2b-256 | ca7b311b3e02e8c4092400c449c850a760d8c45d900983c83a70cc07208c551d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_riscv64.whl
 - Subject digest: f5542f9b941279d82d41eb0aa9f98eba36fe4df5c7086c651df7944935b37182
 - Sigstore transparency entry: 2474055312
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 280.3 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 07ffd07412fc5d5e84cd8952acf9ff7e4ed7a708e69d1bada19d8ba91711353f | |
| MD5 | c34ac9aa6ead5677a1397e736e7e4b68 | |
| BLAKE2b-256 | 20c8c36f6e0b2dfec351bd38cbc05362697e58bcd073d7dbd95154290c9714ce | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_ppc64le.whl
 - Subject digest: 07ffd07412fc5d5e84cd8952acf9ff7e4ed7a708e69d1bada19d8ba91711353f
 - Sigstore transparency entry: 2474068980
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 242.2 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | c1dcc36dcb96abc02236e182d17e0f71430152a6c2c7447421da2d2dc144edea | |
| MD5 | ce6d034606303d1af571541d9b29189f | |
| BLAKE2b-256 | b92d918d0e98a0e679469ed05bb2d90c2088b4d315bb612969d8499f76fb5210 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_armv7l.whl
 - Subject digest: c1dcc36dcb96abc02236e182d17e0f71430152a6c2c7447421da2d2dc144edea
 - Sigstore transparency entry: 2474058408
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 252.5 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 950f23cb393f85543777b0433f082cddd25b51ab398eac7971146495679efe5f | |
| MD5 | 4903c12acc115f42f318560380e0a832 | |
| BLAKE2b-256 | 87bdfbc24d825c66f1c74f6ccdea3742c3d8354a4888e86d1315a197fee69061 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-musllinux_1_2_aarch64.whl
 - Subject digest: 950f23cb393f85543777b0433f082cddd25b51ab398eac7971146495679efe5f
 - Sigstore transparency entry: 2474067370
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 259.6 kB
- Tags: CPython 3.10, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 366ec70f5547c640d3ce1985722490f23faf4eb5216a7eeba78277490e78dacb | |
| MD5 | 9a7d18d69591a6e7b7ff00e3c2796d0a | |
| BLAKE2b-256 | f5e338b975422534a608f98c360e79c2f07c763d66dd4272300d45fb1fee54b0 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 366ec70f5547c640d3ce1985722490f23faf4eb5216a7eeba78277490e78dacb
 - Sigstore transparency entry: 2474061475
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 261.6 kB
- Tags: CPython 3.10, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 96eefc178f8636b9c760c5829345307fd81cfae9ab1e80997dbddeb0f54ee9a3 | |
| MD5 | de110d5b5b04db5fa987fd66ae31aa7f | |
| BLAKE2b-256 | 32cd4f564b8f132de25db594efc706897069f016790cea63a5669c9df2675f64 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 96eefc178f8636b9c760c5829345307fd81cfae9ab1e80997dbddeb0f54ee9a3
 - Sigstore transparency entry: 2474052100
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 276.5 kB
- Tags: CPython 3.10, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | ce854f5f478050ade5a238731c4ca985a7d3b3cb53ff600a9b5c3b689b5f0a7a | |
| MD5 | 2a74d22f3f016aa04b90748edbec4731 | |
| BLAKE2b-256 | 692bd8be3523ddf9f0b0f3e56d1359034aa10653a4d11564c697f802b4775766 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: ce854f5f478050ade5a238731c4ca985a7d3b3cb53ff600a9b5c3b689b5f0a7a
 - Sigstore transparency entry: 2474057673
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 279.6 kB
- Tags: CPython 3.10, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | ba2f37ee79e6338845261a3c5b1784e5d1acdff2c0785b284f1b633033d136ab | |
| MD5 | 74cedf6d5e39ff74421a5c1be2069dca | |
| BLAKE2b-256 | b22c45847198c16f4b38090cc7423b2b6a9008e438704d8ab413211832498d31 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: ba2f37ee79e6338845261a3c5b1784e5d1acdff2c0785b284f1b633033d136ab
 - Sigstore transparency entry: 2474048656
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 240.7 kB
- Tags: CPython 3.10, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 00668ebb0609751758682eb0b5857e7c35b9f00e84dfdef062e103244ec94d45 | |
| MD5 | 530bb297f4c4c285732542846316858d | |
| BLAKE2b-256 | 55537d819bd23a00ef45039146fa2cce1daa2f0771e758c5653ee1f6edac91ed | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: 00668ebb0609751758682eb0b5857e7c35b9f00e84dfdef062e103244ec94d45
 - Sigstore transparency entry: 2474071279
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 251.1 kB
- Tags: CPython 3.10, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | e9fbdce1e47394b09bc9f26ab117dfc8d6491977a11d86f592bb42c779db2fda | |
| MD5 | 04936e390a82ad1a73f497d9d0dac7ad | |
| BLAKE2b-256 | 036d439231dfc3ccfa6f8c06477b7da2219cbd41a2de3d49084df8ec7b5100f2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: e9fbdce1e47394b09bc9f26ab117dfc8d6491977a11d86f592bb42c779db2fda
 - Sigstore transparency entry: 2474086790
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp310-cp310-macosx_10_9_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp310-cp310-macosx_10_9_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 369.1 kB
- Tags: CPython 3.10, macOS 10.9+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp310-cp310-macosx_10_9_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | d1ee1e296209fdce05b81b663250eefa02213a2da7b41bf26f7829b8ba3545aa | |
| MD5 | a27b82e6da07a255fcee8e96ccf24d65 | |
| BLAKE2b-256 | 71aa554e2614f38fc34c58ff1d0911ae8535ad2516440d5482d76fe59f1088b0 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp310-cp310-macosx_10_9_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp310-cp310-macosx_10_9_universal2.whl
 - Subject digest: d1ee1e296209fdce05b81b663250eefa02213a2da7b41bf26f7829b8ba3545aa
 - Sigstore transparency entry: 2474081110
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 185.5 kB
- Tags: CPython 3.9, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 29880d17a8eb0b5cfdfd8944b468322928059aa35f1f5fa8ff22b149ec0b42f8 | |
| MD5 | dde87de94dead032d5d9a7cb908fa73a | |
| BLAKE2b-256 | c458c9295c61e3f826ba7d874f0fd1c5e335dbec928d7b9146b33b48d14a25f1 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-win_arm64.whl
 - Subject digest: 29880d17a8eb0b5cfdfd8944b468322928059aa35f1f5fa8ff22b149ec0b42f8
 - Sigstore transparency entry: 2474059055
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 206.4 kB
- Tags: CPython 3.9, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 012a22b88a77ca2e59b98ac5889b0deb604147666032f45e6d6e217634d2550d | |
| MD5 | dda25c498a02b5d80885145c419db21a | |
| BLAKE2b-256 | 53317f79c671d827080d6eecd697fbbeb4f0f6f8507bf4c5625b5f6398ec5876 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-win_amd64.whl
 - Subject digest: 012a22b88a77ca2e59b98ac5889b0deb604147666032f45e6d6e217634d2550d
 - Sigstore transparency entry: 2474091173
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 182.4 kB
- Tags: CPython 3.9, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 56490c595a28b1bb27dfc583e816152a9767721ef58b2c03b13f954d2f707420 | |
| MD5 | 9a6939a4416c56b39985b4ba00bc3bbc | |
| BLAKE2b-256 | d191249943372195935ff7393eae5842c7dae6fd04401e512bbd69dab1aae40b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-win32.whl
 - Subject digest: 56490c595a28b1bb27dfc583e816152a9767721ef58b2c03b13f954d2f707420
 - Sigstore transparency entry: 2474078887
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 264.5 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | eb12fb2ba69ffa05f8695f61c69e591dc4b4a12ac3757ac8af8adb259bf56d17 | |
| MD5 | 27023b83e5bb84186f8d075715c2449e | |
| BLAKE2b-256 | 64779ae101cb33bd9f681551e82a2b9e08eec99ff715458340931370f4228de9 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_x86_64.whl
 - Subject digest: eb12fb2ba69ffa05f8695f61c69e591dc4b4a12ac3757ac8af8adb259bf56d17
 - Sigstore transparency entry: 2474079943
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 278.9 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 13e3afe97712e8887cd516e960c63f0b93122971e5b5e4b2622fe7701771e838 | |
| MD5 | f488bc2b9900331445a966fbf48f8d23 | |
| BLAKE2b-256 | 79716ee3a48a21e844e5079d8e9b2e91c641da5a7912a748e9e94c9e3ab9ce1c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_s390x.whl
 - Subject digest: 13e3afe97712e8887cd516e960c63f0b93122971e5b5e4b2622fe7701771e838
 - Sigstore transparency entry: 2474049193
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 259.2 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 433c5a81eade63b47e522303bad236f59dba55ea6951746f5558355eeed8c75d | |
| MD5 | 484024977cc6089e3caaf7864845700f | |
| BLAKE2b-256 | 02fc0d9ab98fa7a61394353e8acd0f5f60fc6e94a4615f574af8be0eca14a7ef | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_riscv64.whl
 - Subject digest: 433c5a81eade63b47e522303bad236f59dba55ea6951746f5558355eeed8c75d
 - Sigstore transparency entry: 2474092951
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 282.1 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 2e9cf9253119d8e5d111f05d71626786fd3d6193817316eab1ca088cdb8593cf | |
| MD5 | 1515ac717ddd96feafa65e3b3a5d09af | |
| BLAKE2b-256 | c08c58efc6393e405a8d52b241d31dd9118352c247e4017110c3edfdb4618f0d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_ppc64le.whl
 - Subject digest: 2e9cf9253119d8e5d111f05d71626786fd3d6193817316eab1ca088cdb8593cf
 - Sigstore transparency entry: 2474053410
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 242.9 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 5ca0555312ae2fe82715cada7fac375530c2f3349e1eaa1bcb33d0283ac79a18 | |
| MD5 | c84f0363664127b0416c1acc805d008a | |
| BLAKE2b-256 | d3bcf528dfb78d3bfdc8ee6aeea81eb22e6918d03e4442d373a79717f17de45e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_armv7l.whl
 - Subject digest: 5ca0555312ae2fe82715cada7fac375530c2f3349e1eaa1bcb33d0283ac79a18
 - Sigstore transparency entry: 2474052430
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 253.3 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 55261ac0d2941c42f196dd576f543d87a8ee03cd6f5e30dfb4d807b2e3b9121a | |
| MD5 | e51fc2e4cf75c87bf585056560af80c9 | |
| BLAKE2b-256 | b2e0489aa2a33b944077d4c2c705c245d833dc12cd571a52fc67eaf273f5373a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-musllinux_1_2_aarch64.whl
 - Subject digest: 55261ac0d2941c42f196dd576f543d87a8ee03cd6f5e30dfb4d807b2e3b9121a
 - Sigstore transparency entry: 2474093580
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 260.4 kB
- Tags: CPython 3.9, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | a951ad59cad9145664a730d3036b40b844e74d2d3683da40111463cd3a83845d | |
| MD5 | d6d3c3455c15320c6c4cd3da6590a17a | |
| BLAKE2b-256 | faec3a616c3806ec3f957337e6bf874ae7d64693185039edfbbf87103b8c8631 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: a951ad59cad9145664a730d3036b40b844e74d2d3683da40111463cd3a83845d
 - Sigstore transparency entry: 2474055975
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 262.7 kB
- Tags: CPython 3.9, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 789b8982559ae28dad2356519f841655756cdcd96616410590ae0b17454ee64f | |
| MD5 | 808cd9e8d9322c4f7a50a2be00b1e742 | |
| BLAKE2b-256 | 9fcf7568d8c1c9100b7c8bab9035215a6b36b32b39bb50cabaee9389c4606887 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 789b8982559ae28dad2356519f841655756cdcd96616410590ae0b17454ee64f
 - Sigstore transparency entry: 2474069135
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 278.4 kB
- Tags: CPython 3.9, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 994e883d17c559cdfd38c84003c8b27d25424a1077272a17e7cd27bfe0bf57b2 | |
| MD5 | 0d89911560a9bf0a4196682160c9ebc7 | |
| BLAKE2b-256 | 64607c5469f455f4fa65d39da9f088dffc1a586560bfb9e3279441eed78bd469 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: 994e883d17c559cdfd38c84003c8b27d25424a1077272a17e7cd27bfe0bf57b2
 - Sigstore transparency entry: 2474079485
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 281.9 kB
- Tags: CPython 3.9, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | e06efa066f7dbadbc84ebc126a97c452a6451dfcf589d89d788484949e1cf795 | |
| MD5 | 4d729a997167ffddca35a24ca816af32 | |
| BLAKE2b-256 | 8479a88c181e7f4a7579696fedb34fa63844ede2ff7caf44c5f321cec57d92fb | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: e06efa066f7dbadbc84ebc126a97c452a6451dfcf589d89d788484949e1cf795
 - Sigstore transparency entry: 2474087894
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 241.3 kB
- Tags: CPython 3.9, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 5e2d0e146dcb57034f8b97dc58d2d512cb90aba253960ce449f695fec6a82c6f | |
| MD5 | da918c72bfc3e01ed2546a0773d3ad9d | |
| BLAKE2b-256 | a42d64a13610fd28c80f97aff0ea5cf31cf255d220a8243ac0c78c66fd3d874d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: 5e2d0e146dcb57034f8b97dc58d2d512cb90aba253960ce449f695fec6a82c6f
 - Sigstore transparency entry: 2474073759
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 251.7 kB
- Tags: CPython 3.9, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 3e5e1224c0a6a90e05843e07adfec669edebec17801c67072f51e59561d63c0b | |
| MD5 | b42b88c2b7d1d66840ed2b13ec88d48b | |
| BLAKE2b-256 | 586762df6a907162461f372e95cbbc1bc64c7457e86abcc851feb84409a11eff | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 3e5e1224c0a6a90e05843e07adfec669edebec17801c67072f51e59561d63c0b
 - Sigstore transparency entry: 2474086100
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp39-cp39-macosx_10_9_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp39-cp39-macosx_10_9_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 368.8 kB
- Tags: CPython 3.9, macOS 10.9+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp39-cp39-macosx_10_9_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | 85de3134b5379856e323ba37c19c9256d39425f7b76a63af52b09fb4664c2e8f | |
| MD5 | 009b1cd4d93100baab51117d1f88fb65 | |
| BLAKE2b-256 | d091bc145e42f93d6601b9a26f5421af2d7c3093ae6e6d03b8e583c9cebbf530 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp39-cp39-macosx_10_9_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp39-cp39-macosx_10_9_universal2.whl
 - Subject digest: 85de3134b5379856e323ba37c19c9256d39425f7b76a63af52b09fb4664c2e8f
 - Sigstore transparency entry: 2474064496
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-win_arm64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-win_arm64.whl
- Upload date:
 Aug 15, 2026
- Size: 287.3 kB
- Tags: CPython 3.7+, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 87e4f41d375c0b9be2fb5251aee4b8a689169e134535aed81bf085c3b647451e | |
| MD5 | 1ef94aa55d2edab069a58e0d55677953 | |
| BLAKE2b-256 | f0a7920baf467bfd9bf689f3b318340f37aee4572a71f162bd8db51da55ba4fa | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-win_arm64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-win_arm64.whl
 - Subject digest: 87e4f41d375c0b9be2fb5251aee4b8a689169e134535aed81bf085c3b647451e
 - Sigstore transparency entry: 2474075329
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-win_amd64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-win_amd64.whl
- Upload date:
 Aug 15, 2026
- Size: 199.8 kB
- Tags: CPython 3.7+, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 70055ff39b97c99e7ae40ea3e393fb62aa2e44dbd9b29f8d14f42fb0025c3959 | |
| MD5 | cc384a73feaec5bf7f91a7b20c2357c8 | |
| BLAKE2b-256 | 354fb911ed898b26a09789eba9c9200c999aff6c61b4bafaf4838e56d1a1e1a3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-win_amd64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-win_amd64.whl
 - Subject digest: 70055ff39b97c99e7ae40ea3e393fb62aa2e44dbd9b29f8d14f42fb0025c3959
 - Sigstore transparency entry: 2474073660
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-win32.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-win32.whl
- Upload date:
 Aug 15, 2026
- Size: 174.2 kB
- Tags: CPython 3.7+, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-win32.whl
| Algorithm | Hash digest | |
| SHA256 | dd732602a7009217f658d5863d12d79d373a4de0eebc111094bcdd3bb8e0a6cc | |
| MD5 | 2a43185e4561a64363ba8a58737503b3 | |
| BLAKE2b-256 | 0165d43b714731bb2f40d4053dfa00ecfc1c5a301f8e3316c5db3a09af59fe94 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-win32.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-win32.whl
 - Subject digest: dd732602a7009217f658d5863d12d79d373a4de0eebc111094bcdd3bb8e0a6cc
 - Sigstore transparency entry: 2474071831
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 254.8 kB
- Tags: CPython 3.7+, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | e199fb99720074809a7720f1c0b4d919eea8b87e88713e0f8f602f7bef543d9d | |
| MD5 | 7e4e5d5152c1206d657e791f1dfec460 | |
| BLAKE2b-256 | 80c2a7379b840292d0c1ab9fbd17d1f3967aa81794dc95bc74be8999d7fedcf7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_x86_64.whl
 - Subject digest: e199fb99720074809a7720f1c0b4d919eea8b87e88713e0f8f602f7bef543d9d
 - Sigstore transparency entry: 2474096147
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 256.9 kB
- Tags: CPython 3.7+, musllinux: musl 1.2+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 3588e376b3ea2eea84976f67273d679f229e24c66dce7b82ae45aef04ff6e072 | |
| MD5 | d83721f02990dcc8087606dc6ffae8f0 | |
| BLAKE2b-256 | 358a3d130aeabcaf3d2466af76b7b141c08d9e89c9016ab4b7cdd0f7dc2d1c62 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_s390x.whl
 - Subject digest: 3588e376b3ea2eea84976f67273d679f229e24c66dce7b82ae45aef04ff6e072
 - Sigstore transparency entry: 2474063665
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 247.2 kB
- Tags: CPython 3.7+, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 2f293479cce755c75f1697e87c409b7ae4c555c7dfecb6e988ad13abba943031 | |
| MD5 | d135abb1f996111b222ed90a312c2a84 | |
| BLAKE2b-256 | d6aaa69a2028e8bd052476c245460ab19d7de595de084dd968f2d75cd50c3e25 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_riscv64.whl
 - Subject digest: 2f293479cce755c75f1697e87c409b7ae4c555c7dfecb6e988ad13abba943031
 - Sigstore transparency entry: 2474056506
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 260.3 kB
- Tags: CPython 3.7+, musllinux: musl 1.2+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | 4c4fb141a727957c93edfe5c32a26ceb6b5f6461d67146e2d39f51e16170bea8 | |
| MD5 | 06f12825f1f76c23437a623cce06606c | |
| BLAKE2b-256 | 18962b3a21492d9f65171ac75d872f5018260013d00bfa0ff70ec9f179148cbd | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_ppc64le.whl
 - Subject digest: 4c4fb141a727957c93edfe5c32a26ceb6b5f6461d67146e2d39f51e16170bea8
 - Sigstore transparency entry: 2474083879
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 232.5 kB
- Tags: CPython 3.7+, musllinux: musl 1.2+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 36047af20e17097c3bb9476c2b7655f2f7aa51322c0ba58c07695bedf755a950 | |
| MD5 | 2b07724280f6d68521cc38655373e1ca | |
| BLAKE2b-256 | 2bb811d4840bfc99330cc7fbcc2681ee5a044553a6e77655508d8f9b2bff7b34 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_armv7l.whl
 - Subject digest: 36047af20e17097c3bb9476c2b7655f2f7aa51322c0ba58c07695bedf755a950
 - Sigstore transparency entry: 2474060377
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 241.8 kB
- Tags: CPython 3.7+, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | a2028475ba855475b8b4d3cfeb4994269c967aea8b9892dfba907f4263a863a3 | |
| MD5 | edfec6934354aafe8db9634269826220 | |
| BLAKE2b-256 | 759c019fbb9f4834491a160951349b1a3714439376f66e5f7cf18b4f18f0c7aa | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-musllinux_1_2_aarch64.whl
 - Subject digest: a2028475ba855475b8b4d3cfeb4994269c967aea8b9892dfba907f4263a863a3
 - Sigstore transparency entry: 2474082518
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Aug 15, 2026
- Size: 250.2 kB
- Tags: CPython 3.7+, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | b39b69b347e5e47a3b5b8cfc005c68c1ba347474e3960236c4944a8ecd174962 | |
| MD5 | 593e864c85eb618330ec734803509fce | |
| BLAKE2b-256 | f57bade0a122600319dfa0b1000ab0f9731c94a817904cf3c5de408c73a4ede7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: b39b69b347e5e47a3b5b8cfc005c68c1ba347474e3960236c4944a8ecd174962
 - Sigstore transparency entry: 2474077179
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
- Upload date:
 Aug 15, 2026
- Size: 255.1 kB
- Tags: CPython 3.7+, manylinux: glibc 2.17+ s390x, manylinux: glibc 2.28+ s390x
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
| Algorithm | Hash digest | |
| SHA256 | 4b599739b93b2cbeded49645ae3c8d1405c29ddfbceac1545c87a3f9580a9e96 | |
| MD5 | b91d9adc3e9cb8457541a449bb5ed21d | |
| BLAKE2b-256 | c392de7e32ed05341e7a9c4c877c318418197b7f2d66a3b68d561bf2ac57ca3e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl
 - Subject digest: 4b599739b93b2cbeded49645ae3c8d1405c29ddfbceac1545c87a3f9580a9e96
 - Sigstore transparency entry: 2474060122
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
- Upload date:
 Aug 15, 2026
- Size: 260.0 kB
- Tags: CPython 3.7+, manylinux: glibc 2.17+ ppc64le, manylinux: glibc 2.28+ ppc64le
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
| Algorithm | Hash digest | |
| SHA256 | ae4a097991662cd4fff0ddc74e0fe7874f82e00042fa0ea00855645ed0c79598 | |
| MD5 | d954942f170817173967eb4c2f9c3881 | |
| BLAKE2b-256 | d30571bfc5caa0abcc45aea1f6a4d50ac68e59605ddc7666fe8494f4cd229665 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl
 - Subject digest: ae4a097991662cd4fff0ddc74e0fe7874f82e00042fa0ea00855645ed0c79598
 - Sigstore transparency entry: 2474058894
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
- Upload date:
 Aug 15, 2026
- Size: 230.8 kB
- Tags: CPython 3.7+, manylinux: glibc 2.17+ ARMv7l, manylinux: glibc 2.31+ ARMv7l
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
| Algorithm | Hash digest | |
| SHA256 | 343fb4f2821043bd87095f7b08a1a181febc8e36ac64212143bbfd0a0e1bc235 | |
| MD5 | 0cabe7f040ee61f35727b205c2a0acc7 | |
| BLAKE2b-256 | 49e0716601f3cc69be7b198951150c75ead1ece33c3c8036ff6ffa46029659a0 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl
 - Subject digest: 343fb4f2821043bd87095f7b08a1a181febc8e36ac64212143bbfd0a0e1bc235
 - Sigstore transparency entry: 2474087211
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Aug 15, 2026
- Size: 240.9 kB
- Tags: CPython 3.7+, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | cee5dd7c6fb5dd52a0fe2a740f9bc6e3593f5f8b1788bde49de02086f30182b2 | |
| MD5 | bd83c40fa62aad6dd43fa26d31d95e11 | |
| BLAKE2b-256 | d7c79e48cee5c161fe24da823b61bf381921d77cb994a0a4de148e95018c1984 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: cee5dd7c6fb5dd52a0fe2a740f9bc6e3593f5f8b1788bde49de02086f30182b2
 - Sigstore transparency entry: 2474070902
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl
- Upload date:
 Aug 15, 2026
- Size: 253.1 kB
- Tags: CPython 3.7+, manylinux: glibc 2.28+ x86-64, manylinux: glibc 2.5+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | a6dac12ff6b846103483683f60c5f8fee205121adc58ffd87e90a90a3af69e99 | |
| MD5 | 084bac39b7f0475fbca5c22c77d70d1b | |
| BLAKE2b-256 | 9f2ffe3f187327aac18e2d54e9d2b08e15d27bf9b642d9e51c219f130fc34d1a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl
 - Subject digest: a6dac12ff6b846103483683f60c5f8fee205121adc58ffd87e90a90a3af69e99
 - Sigstore transparency entry: 2474067560
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## File details

Details for the file charset_normalizer-3.5.1-cp37-abi3-macosx_10_9_universal2.whl.

### File metadata

- Download URL: charset_normalizer-3.5.1-cp37-abi3-macosx_10_9_universal2.whl
- Upload date:
 Aug 15, 2026
- Size: 331.5 kB
- Tags: CPython 3.7+, macOS 10.9+ universal2 (ARM64, x86-64)
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.13

### File hashes

Hashes for charset_normalizer-3.5.1-cp37-abi3-macosx_10_9_universal2.whl
| Algorithm | Hash digest | |
| SHA256 | 41876ee62a3dddf48ff1121ad8f0798032aa03f2fd35f21f34a4cab14f18d8d2 | |
| MD5 | cb6e5096d0c20de8abeb4b542ff65ee7 | |
| BLAKE2b-256 | 5b97fb4e82231aba271ffd775a1b4993b0defc4e3059f286ae41d9433409fe85 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for charset_normalizer-3.5.1-cp37-abi3-macosx_10_9_universal2.whl:

Publisher: cd.yml on jawah/charset_normalizer

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: charset_normalizer-3.5.1-cp37-abi3-macosx_10_9_universal2.whl
 - Subject digest: 41876ee62a3dddf48ff1121ad8f0798032aa03f2fd35f21f34a4cab14f18d8d2
 - Sigstore transparency entry: 2474047623
 - Sigstore integration time:
 Aug 15, 2026
 Source repository:

 - Permalink: jawah/charset_normalizer@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Branch / Tag: refs/tags/3.5.1
 - Owner: https://github.com/jawah
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 cd.yml@e239bdc5cc1eb1f0db08d4046ad531f805dbea71
 - Trigger Event: release

## Release history Release notifications |
 RSS feed

This release

3.5.1 This release

Aug 15, 2026
 172 files

3.5.0

Aug 12, 2026
 172 files

3.4.9

Jul 7, 2026
 93 files

Yanked

3.4.8

Jul 6, 2026
 105 files

3.4.7

Apr 2, 2026
 129 files

3.4.6

Mar 15, 2026
 129 files

3.4.5

Mar 6, 2026
 113 files

3.4.4

Oct 14, 2025
 113 files

3.4.3

Aug 9, 2025
 79 files

3.4.2

May 2, 2025
 92 files

3.4.1

Dec 24, 2024
 92 files

3.4.0

Oct 9, 2024
 105 files

3.3.2

Nov 1, 2023
 90 files

3.3.1

Oct 22, 2023
 90 files

3.3.0

Sep 30, 2023
 90 files

3.2.0

Jul 7, 2023
 75 files

3.1.0

Mar 6, 2023
 75 files

3.0.1

Nov 18, 2022
 88 files

3.0.0

Oct 20, 2022
 88 files

Pre-release

3.0.0rc1

Oct 20, 2022
 88 files

Pre-release

3.0.0b2

Aug 21, 2022
 73 files

Pre-release

3.0.0b1

Aug 16, 2022
 73 files

2.1.1

Aug 19, 2022
 2 files

2.1.0

Jun 19, 2022
 2 files

2.0.12

Feb 12, 2022
 2 files

2.0.11

Jan 30, 2022
 2 files

2.0.10

Jan 4, 2022
 2 files

2.0.9

Dec 3, 2021
 2 files

2.0.8

Nov 24, 2021
 2 files

2.0.7

Oct 11, 2021
 2 files

2.0.6

Sep 17, 2021
 2 files

2.0.5

Sep 14, 2021
 2 files

2.0.4

Jul 30, 2021
 2 files

2.0.3

Jul 16, 2021
 2 files

2.0.2

Jul 14, 2021
 2 files

2.0.1

Jul 13, 2021
 2 files

2.0.0

Jul 2, 2021
 2 files

1.4.1

May 28, 2021
 2 files

1.4.0

May 21, 2021
 2 files

1.3.9

May 13, 2021
 2 files

1.3.8

May 12, 2021
 2 files

1.3.7

May 12, 2021
 2 files

1.3.6

Feb 9, 2021
 2 files

1.3.5

Feb 8, 2021
 2 files

1.3.4

Dec 16, 2019
 1 file

1.3.3

Dec 16, 2019
 1 file

1.3.2

Dec 13, 2019
 1 file

1.3.1

Oct 11, 2019
 1 file

1.3.0

Sep 30, 2019
 1 file

1.2.0

Sep 28, 2019
 1 file

1.1.1

Sep 23, 2019
 1 file

1.1.0

Sep 21, 2019
 1 file

1.0.0

Sep 17, 2019
 1 file

0.3.0

Sep 12, 2019
 1 file

0.2.3

Sep 6, 2019
 1 file

0.2.2

Sep 4, 2019
 1 file

0.2.1

Sep 3, 2019
 1 file

0.2.0

Aug 31, 2019
 1 file

0.1.8

Aug 28, 2019
 1 file

0.1.7

Aug 27, 2019
 1 file

Pre-release

0.1.5b0

Aug 8, 2019
 1 file

Pre-release

0.1.4b0

Aug 8, 2019
 1 file

Pre-release

0.1.2b0

Aug 7, 2019
 1 file

Pre-release

0.1.1a0

Aug 3, 2019
 1 file

Pre-release

0.1a0

Aug 2, 2019
 1 file