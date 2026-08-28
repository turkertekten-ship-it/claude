# MarkupSafe

MarkupSafe implements a text object that escapes characters so it is
safe to use in HTML and XML. Characters that have special meanings are
replaced so that they display as the actual characters. This mitigates
injection attacks, meaning untrusted user input can safely be displayed
on a page.

## Examples

```
>>> from markupsafe import Markup, escape

>>> # escape replaces special characters and wraps in Markup
>>> escape("<script>alert(document.cookie);</script>")
Markup('&lt;script&gt;alert(document.cookie);&lt;/script&gt;')

>>> # wrap in Markup to mark text "safe" and prevent escaping
>>> Markup("<strong>Hello</strong>")
Markup('<strong>hello</strong>')

>>> escape(Markup("<strong>Hello</strong>"))
Markup('<strong>hello</strong>')

>>> # Markup is a str subclass
>>> # methods and operators escape their arguments
>>> template = Markup("Hello <em>{name}</em>")
>>> template.format(name='"World"')
Markup('Hello <em>&#34;World&#34;</em>')
```

## Donate

The Pallets organization develops and supports MarkupSafe and other
popular packages. In order to grow the community of contributors and
users, and allow the maintainers to devote more time to the projects,
please donate today.

## Contributing

See our detailed contributing documentation for many ways to
contribute, including reporting issues, requesting features, asking or answering
questions, and making PRs.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

markupsafe-3.0.3.tar.gz
 (80.3 kB
 view details)

Uploaded
 Sep 27, 2025
 Source

### Built Distributions

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

markupsafe-3.0.3-cp314-cp314t-win_arm64.whl
 (14.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tWindows ARM64

markupsafe-3.0.3-cp314-cp314t-win_amd64.whl
 (15.4 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tWindows x86-64

markupsafe-3.0.3-cp314-cp314t-win32.whl
 (14.8 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tWindows x86

markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl
 (23.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmusllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_riscv64.whl
 (22.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmusllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl
 (24.8 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmusllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (23.3 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmanylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (23.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmanylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (25.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmanylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp314-cp314t-macosx_11_0_arm64.whl
 (12.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmacOS 11.0+ ARM64

markupsafe-3.0.3-cp314-cp314t-macosx_10_13_x86_64.whl
 (11.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14tmacOS 10.13+ x86-64

markupsafe-3.0.3-cp314-cp314-win_arm64.whl
 (14.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14Windows ARM64

markupsafe-3.0.3-cp314-cp314-win_amd64.whl
 (15.3 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14Windows x86-64

markupsafe-3.0.3-cp314-cp314-win32.whl
 (14.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14Windows x86

markupsafe-3.0.3-cp314-cp314-musllinux_1_2_x86_64.whl
 (23.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14musllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp314-cp314-musllinux_1_2_riscv64.whl
 (21.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14musllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp314-cp314-musllinux_1_2_aarch64.whl
 (23.8 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14musllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (22.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (23.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (24.4 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp314-cp314-macosx_11_0_arm64.whl
 (12.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14macOS 11.0+ ARM64

markupsafe-3.0.3-cp314-cp314-macosx_10_13_x86_64.whl
 (11.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.14macOS 10.13+ x86-64

markupsafe-3.0.3-cp313-cp313t-win_arm64.whl
 (14.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tWindows ARM64

markupsafe-3.0.3-cp313-cp313t-win_amd64.whl
 (15.2 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tWindows x86-64

markupsafe-3.0.3-cp313-cp313t-win32.whl
 (14.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tWindows x86

markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_x86_64.whl
 (23.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmusllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_riscv64.whl
 (22.8 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmusllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_aarch64.whl
 (24.8 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmusllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp313-cp313t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (23.3 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmanylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp313-cp313t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (23.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmanylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp313-cp313t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (25.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmanylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp313-cp313t-macosx_11_0_arm64.whl
 (12.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmacOS 11.0+ ARM64

markupsafe-3.0.3-cp313-cp313t-macosx_10_13_x86_64.whl
 (11.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13tmacOS 10.13+ x86-64

markupsafe-3.0.3-cp313-cp313-win_arm64.whl
 (13.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13Windows ARM64

markupsafe-3.0.3-cp313-cp313-win_amd64.whl
 (15.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13Windows x86-64

markupsafe-3.0.3-cp313-cp313-win32.whl
 (14.5 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13Windows x86

markupsafe-3.0.3-cp313-cp313-musllinux_1_2_x86_64.whl
 (23.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13musllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp313-cp313-musllinux_1_2_riscv64.whl
 (21.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13musllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp313-cp313-musllinux_1_2_aarch64.whl
 (23.8 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13musllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (22.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (23.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (24.4 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl
 (12.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13macOS 11.0+ ARM64

markupsafe-3.0.3-cp313-cp313-macosx_10_13_x86_64.whl
 (11.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.13macOS 10.13+ x86-64

markupsafe-3.0.3-cp312-cp312-win_arm64.whl
 (13.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12Windows ARM64

markupsafe-3.0.3-cp312-cp312-win_amd64.whl
 (15.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12Windows x86-64

markupsafe-3.0.3-cp312-cp312-win32.whl
 (14.5 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12Windows x86

markupsafe-3.0.3-cp312-cp312-musllinux_1_2_x86_64.whl
 (23.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12musllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp312-cp312-musllinux_1_2_riscv64.whl
 (21.5 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12musllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp312-cp312-musllinux_1_2_aarch64.whl
 (23.8 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12musllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (22.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (22.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (24.3 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp312-cp312-macosx_11_0_arm64.whl
 (12.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12macOS 11.0+ ARM64

markupsafe-3.0.3-cp312-cp312-macosx_10_13_x86_64.whl
 (11.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.12macOS 10.13+ x86-64

markupsafe-3.0.3-cp311-cp311-win_arm64.whl
 (13.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11Windows ARM64

markupsafe-3.0.3-cp311-cp311-win_amd64.whl
 (15.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11Windows x86-64

markupsafe-3.0.3-cp311-cp311-win32.whl
 (14.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11Windows x86

markupsafe-3.0.3-cp311-cp311-musllinux_1_2_x86_64.whl
 (22.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11musllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp311-cp311-musllinux_1_2_riscv64.whl
 (21.5 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11musllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp311-cp311-musllinux_1_2_aarch64.whl
 (23.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11musllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (21.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (22.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (24.3 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl
 (12.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11macOS 11.0+ ARM64

markupsafe-3.0.3-cp311-cp311-macosx_10_9_x86_64.whl
 (11.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.11macOS 10.9+ x86-64

markupsafe-3.0.3-cp310-cp310-win_arm64.whl
 (13.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10Windows ARM64

markupsafe-3.0.3-cp310-cp310-win_amd64.whl
 (15.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10Windows x86-64

markupsafe-3.0.3-cp310-cp310-win32.whl
 (14.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10Windows x86

markupsafe-3.0.3-cp310-cp310-musllinux_1_2_x86_64.whl
 (20.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10musllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp310-cp310-musllinux_1_2_riscv64.whl
 (20.3 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10musllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp310-cp310-musllinux_1_2_aarch64.whl
 (21.5 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10musllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (20.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (20.7 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (22.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp310-cp310-macosx_11_0_arm64.whl
 (12.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10macOS 11.0+ ARM64

markupsafe-3.0.3-cp310-cp310-macosx_10_9_x86_64.whl
 (11.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.10macOS 10.9+ x86-64

markupsafe-3.0.3-cp39-cp39-win_arm64.whl
 (13.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9Windows ARM64

markupsafe-3.0.3-cp39-cp39-win_amd64.whl
 (15.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9Windows x86-64

markupsafe-3.0.3-cp39-cp39-win32.whl
 (14.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9Windows x86

markupsafe-3.0.3-cp39-cp39-musllinux_1_2_x86_64.whl
 (20.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9musllinux: musl 1.2+ x86-64

markupsafe-3.0.3-cp39-cp39-musllinux_1_2_riscv64.whl
 (20.1 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9musllinux: musl 1.2+ riscv64

markupsafe-3.0.3-cp39-cp39-musllinux_1_2_aarch64.whl
 (21.4 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9musllinux: musl 1.2+ ARM64

markupsafe-3.0.3-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 (20.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9manylinux: glibc 2.31+ riscv64manylinux: glibc 2.39+ riscv64

markupsafe-3.0.3-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 (20.5 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9manylinux: glibc 2.17+ x86-64manylinux: glibc 2.28+ x86-64

markupsafe-3.0.3-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 (21.9 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9manylinux: glibc 2.17+ ARM64manylinux: glibc 2.28+ ARM64

markupsafe-3.0.3-cp39-cp39-macosx_11_0_arm64.whl
 (12.0 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9macOS 11.0+ ARM64

markupsafe-3.0.3-cp39-cp39-macosx_10_9_x86_64.whl
 (11.6 kB
 view details)

Uploaded
 Sep 27, 2025
 CPython 3.9macOS 10.9+ x86-64

## File details

Details for the file markupsafe-3.0.3.tar.gz.

### File metadata

- Download URL: markupsafe-3.0.3.tar.gz
- Upload date:
 Sep 27, 2025
- Size: 80.3 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3.tar.gz
| Algorithm | Hash digest | |
| SHA256 | 722695808f4b6457b320fdc131280796bdceb04ab50fe1795cd540799ebe1698 | |
| MD5 | 13a73126d25afa72a1ff0daed072f5fe | |
| BLAKE2b-256 | 7e997690b6d4034fffd95959cbe0c02de8deb3098cc577c67bb6a24fe5d7caa7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3.tar.gz:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3.tar.gz
 - Subject digest: 722695808f4b6457b320fdc131280796bdceb04ab50fe1795cd540799ebe1698
 - Sigstore transparency entry: 565627678
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 14.1 kB
- Tags: CPython 3.14t, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 32001d6a8fc98c8cb5c947787c5d08b0a50663d139f1305bac5885d98d9b40fa | |
| MD5 | 4dd6b134f5ffd4ac161abc425cb60789 | |
| BLAKE2b-256 | 70bc6f1c2f612465f5fa89b95bead1f44dcb607670fd42891d8fdcd5d039f4f4 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-win_arm64.whl
 - Subject digest: 32001d6a8fc98c8cb5c947787c5d08b0a50663d139f1305bac5885d98d9b40fa
 - Sigstore transparency entry: 565627854
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.4 kB
- Tags: CPython 3.14t, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 4faffd047e07c38848ce017e8725090413cd80cbc23d86e55c587bf979e579c9 | |
| MD5 | 2323f8379a0d7c2e847cb901d07e2102 | |
| BLAKE2b-256 | 1a8a0402ba61a2f16038b48b39bccca271134be00c5c9f0f623208399333c448 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-win_amd64.whl
 - Subject digest: 4faffd047e07c38848ce017e8725090413cd80cbc23d86e55c587bf979e579c9
 - Sigstore transparency entry: 565627797
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.8 kB
- Tags: CPython 3.14t, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 915c04ba3851909ce68ccc2b8e2cd691618c4dc4c4232fb7982bca3f41fd8c3d | |
| MD5 | 74b11ed65b0e7b57753b396db5ecc59d | |
| BLAKE2b-256 | fbdf5bd7a48c256faecd1d36edc13133e51397e41b73bb77e1a69deab746ebac | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-win32.whl
 - Subject digest: 915c04ba3851909ce68ccc2b8e2cd691618c4dc4c4232fb7982bca3f41fd8c3d
 - Sigstore transparency entry: 565627719
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.7 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 5678211cb9333a6468fb8d8be0305520aa073f50d17f089b5b4b477ea6e67fdc | |
| MD5 | f70279ecb8f657703ba306dfab7772ed | |
| BLAKE2b-256 | 14c7ca723101509b518797fedc2fdf79ba57f886b4aca8a7d31857ba3ee8281f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl
 - Subject digest: 5678211cb9333a6468fb8d8be0305520aa073f50d17f089b5b4b477ea6e67fdc
 - Sigstore transparency entry: 565627955
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.7 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | f3e98bb3798ead92273dc0e5fd0f31ade220f59a266ffd8a4f6065e0a3ce0523 | |
| MD5 | 3e59f558528cd0bf7808aadbe40f3cd6 | |
| BLAKE2b-256 | 266a4bf6d0c97c4920f1597cc14dd720705eca0bf7c787aebc6bb4d1bead5388 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_riscv64.whl
 - Subject digest: f3e98bb3798ead92273dc0e5fd0f31ade220f59a266ffd8a4f6065e0a3ce0523
 - Sigstore transparency entry: 565627973
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 24.8 kB
- Tags: CPython 3.14t, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | e56b7d45a839a697b5eb268c82a71bd8c7f6c94d6fd50c3d577fa39a9f1409f5 | |
| MD5 | 6315df288c04b989d0d2c6a3057f5ced | |
| BLAKE2b-256 | 5f571b0b3f100259dc9fffe780cfb60d4be71375510e435efec3d116b6436d43 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl
 - Subject digest: e56b7d45a839a697b5eb268c82a71bd8c7f6c94d6fd50c3d577fa39a9f1409f5
 - Sigstore transparency entry: 565627979
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.3 kB
- Tags: CPython 3.14t, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | f190daf01f13c72eac4efd5c430a8de82489d9cff23c364c3ea822545032993e | |
| MD5 | 259544f7198c6aa6d01ec0dbb9fb45ac | |
| BLAKE2b-256 | 2244a0681611106e0b2921b3033fc19bc53323e0b50bc70cffdd19f7d679bb66 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: f190daf01f13c72eac4efd5c430a8de82489d9cff23c364c3ea822545032993e
 - Sigstore transparency entry: 565628056
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.6 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | fed51ac40f757d41b7c48425901843666a6677e3e8eb0abcff09e4ba6e664f50 | |
| MD5 | 0b1c3ff7a235bbf68466a5d1dea38bff | |
| BLAKE2b-256 | 5009c419f6f5a92e5fadde27efd190eca90f05e1261b10dbd8cbcb39cd8ea1dc | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: fed51ac40f757d41b7c48425901843666a6677e3e8eb0abcff09e4ba6e664f50
 - Sigstore transparency entry: 565627724
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 25.7 kB
- Tags: CPython 3.14t, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 1b52b4fb9df4eb9ae465f8d0c228a00624de2334f216f178a995ccdcf82c4634 | |
| MD5 | 61a59296186e8a6418433b20ca601634 | |
| BLAKE2b-256 | f000be561dce4e6ca66b15276e184ce4b8aec61fe83662cce2f7d72bd3249d28 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 1b52b4fb9df4eb9ae465f8d0c228a00624de2334f216f178a995ccdcf82c4634
 - Sigstore transparency entry: 565627705
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.1 kB
- Tags: CPython 3.14t, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 1085e7fbddd3be5f89cc898938f42c0b3c711fdcb37d75221de2666af647c175 | |
| MD5 | 0008679f373d0016c37791ff89cd753e | |
| BLAKE2b-256 | 89c32e67a7ca217c6912985ec766c6393b636fb0c2344443ff9d91404dc4c79f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-macosx_11_0_arm64.whl
 - Subject digest: 1085e7fbddd3be5f89cc898938f42c0b3c711fdcb37d75221de2666af647c175
 - Sigstore transparency entry: 565627690
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314t-macosx_10_13_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314t-macosx_10_13_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.7 kB
- Tags: CPython 3.14t, macOS 10.13+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314t-macosx_10_13_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 1353ef0c1b138e1907ae78e2f6c63ff67501122006b0f9abad68fda5f4ffc6ab | |
| MD5 | ddc8ae8e702a03b2e3d3bf000aa46253 | |
| BLAKE2b-256 | 3cf057689aa4076e1b43b15fdfa646b04653969d50cf30c32a102762be2485da | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314t-macosx_10_13_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314t-macosx_10_13_x86_64.whl
 - Subject digest: 1353ef0c1b138e1907ae78e2f6c63ff67501122006b0f9abad68fda5f4ffc6ab
 - Sigstore transparency entry: 565627848
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 14.1 kB
- Tags: CPython 3.14, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 5a7d5dc5140555cf21a6fefbdbf8723f06fcd2f63ef108f2854de715e4422cb4 | |
| MD5 | d8f5d585834925802aac80e51a710f5b | |
| BLAKE2b-256 | 6f18acf23e91bd94fd7b3031558b1f013adfa21a8e407a3fdb32745538730382 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-win_arm64.whl
 - Subject digest: 5a7d5dc5140555cf21a6fefbdbf8723f06fcd2f63ef108f2854de715e4422cb4
 - Sigstore transparency entry: 565627921
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.3 kB
- Tags: CPython 3.14, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | bdc919ead48f234740ad807933cdf545180bfbe9342c2bb451556db2ed958581 | |
| MD5 | f85cc52572f23beafb27d04c3baacc83 | |
| BLAKE2b-256 | 2852182836104b33b444e400b14f797212f720cbc9ed6ba34c800639d154e821 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-win_amd64.whl
 - Subject digest: bdc919ead48f234740ad807933cdf545180bfbe9342c2bb451556db2ed958581
 - Sigstore transparency entry: 565627816
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.7 kB
- Tags: CPython 3.14, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 729586769a26dbceff69f7a7dbbf59ab6572b99d94576a5592625d5b411576b9 | |
| MD5 | 4f12dcc2d1d1caa9c98a84199dd74f6a | |
| BLAKE2b-256 | 4611f333a06fc16236d5238bfe74daccbca41459dcd8d1fa952e8fbd5dccfb70 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-win32.whl
 - Subject digest: 729586769a26dbceff69f7a7dbbf59ab6572b99d94576a5592625d5b411576b9
 - Sigstore transparency entry: 565627810
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.0 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 2713baf880df847f2bece4230d4d094280f4e67b1e813eec43b4c0e144a34ffe | |
| MD5 | db8099f16ecf225d7f0f549c5eb9a6ab | |
| BLAKE2b-256 | ff0e53dfaca23a69fbfbbf17a4b64072090e70717344c52eaaaa9c5ddff1e5f0 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-musllinux_1_2_x86_64.whl
 - Subject digest: 2713baf880df847f2bece4230d4d094280f4e67b1e813eec43b4c0e144a34ffe
 - Sigstore transparency entry: 565627959
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.6 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 0eb9ff8191e8498cca014656ae6b8d61f39da5f95b488805da4bb029cccbfbaf | |
| MD5 | 24771f808ed82b9ce5b5c593280a5919 | |
| BLAKE2b-256 | 7d3345b24e4f44195b26521bc6f1a82197118f74df348556594bd2262bda1038 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-musllinux_1_2_riscv64.whl
 - Subject digest: 0eb9ff8191e8498cca014656ae6b8d61f39da5f95b488805da4bb029cccbfbaf
 - Sigstore transparency entry: 565627819
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.8 kB
- Tags: CPython 3.14, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | ec15a59cf5af7be74194f7ab02d0f59a62bdcf1a537677ce67a2537c9b87fcda | |
| MD5 | 45695a9ce6d6d3dbf208294640251198 | |
| BLAKE2b-256 | 9aa7591f592afdc734f47db08a75793a55d7fbcc6902a723ae4cfbab61010cc5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-musllinux_1_2_aarch64.whl
 - Subject digest: ec15a59cf5af7be74194f7ab02d0f59a62bdcf1a537677ce67a2537c9b87fcda
 - Sigstore transparency entry: 565627945
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.0 kB
- Tags: CPython 3.14, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | e8afc3f2ccfa24215f8cb28dcf43f0113ac3c37c2f0f0806d8c70e4228c5cf4d | |
| MD5 | ba0ba1f41f6a39abbc2e21f681538ead | |
| BLAKE2b-256 | bc20b7fdf89a8456b099837cd1dc21974632a02a999ec9bf7ca3e490aacd98e7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: e8afc3f2ccfa24215f8cb28dcf43f0113ac3c37c2f0f0806d8c70e4228c5cf4d
 - Sigstore transparency entry: 565628033
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.0 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 457a69a9577064c05a97c41f4e65148652db078a3a509039e64d3467b9e7ef97 | |
| MD5 | 76ca02c288755ae6328a721353eaa27b | |
| BLAKE2b-256 | 413ca36c2450754618e62008bf7435ccb0f88053e07592e6028a34776213d877 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 457a69a9577064c05a97c41f4e65148652db078a3a509039e64d3467b9e7ef97
 - Sigstore transparency entry: 565627899
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 24.4 kB
- Tags: CPython 3.14, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | f34c41761022dd093b4b6896d4810782ffbabe30f2d443ff5f083e0cbbb8c737 | |
| MD5 | 42808c3b9f1fc2fa4641bea6e4bcd426 | |
| BLAKE2b-256 | daefe648bfd021127bef5fa12e1720ffed0c6cbb8310c8d9bea7266337ff06de | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: f34c41761022dd093b4b6896d4810782ffbabe30f2d443ff5f083e0cbbb8c737
 - Sigstore transparency entry: 565627845
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.0 kB
- Tags: CPython 3.14, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | c47a551199eb8eb2121d4f0f15ae0f923d31350ab9280078d1e5f12b249e0026 | |
| MD5 | 7c0e6182016e91e058bc2a231a732e61 | |
| BLAKE2b-256 | b5647660f8a4a8e53c924d0fa05dc3a55c9cee10bbd82b11c5afb27d44b096ce | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-macosx_11_0_arm64.whl
 - Subject digest: c47a551199eb8eb2121d4f0f15ae0f923d31350ab9280078d1e5f12b249e0026
 - Sigstore transparency entry: 565628005
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp314-cp314-macosx_10_13_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp314-cp314-macosx_10_13_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.6 kB
- Tags: CPython 3.14, macOS 10.13+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp314-cp314-macosx_10_13_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | eaa9599de571d72e2daf60164784109f19978b327a3910d3e9de8c97b5b70cfe | |
| MD5 | 06528f1b515460dc49b8b829e408acff | |
| BLAKE2b-256 | 338a8e42d4838cd89b7dde187011e97fe6c3af66d8c044997d2183fbd6d31352 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp314-cp314-macosx_10_13_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp314-cp314-macosx_10_13_x86_64.whl
 - Subject digest: eaa9599de571d72e2daf60164784109f19978b327a3910d3e9de8c97b5b70cfe
 - Sigstore transparency entry: 565628042
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 14.0 kB
- Tags: CPython 3.13t, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | ad2cf8aa28b8c020ab2fc8287b0f823d0a7d8630784c31e9ee5edea20f406287 | |
| MD5 | c92be29878a821015564fdd6e11ab313 | |
| BLAKE2b-256 | 0e72e3cc540f351f316e9ed0f092757459afbc595824ca724cbc5a5d4263713f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-win_arm64.whl
 - Subject digest: ad2cf8aa28b8c020ab2fc8287b0f823d0a7d8630784c31e9ee5edea20f406287
 - Sigstore transparency entry: 565627708
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.2 kB
- Tags: CPython 3.13t, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 1b4b79e8ebf6b55351f0d91fe80f893b4743f104bff22e90697db1590e47a218 | |
| MD5 | d5c92d85c98157fc35e9bab285a26860 | |
| BLAKE2b-256 | 2b98e48a4bfba0a0ffcf9925fe2d69240bfaa19c6f7507b8cd09c70684a53c1e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-win_amd64.whl
 - Subject digest: 1b4b79e8ebf6b55351f0d91fe80f893b4743f104bff22e90697db1590e47a218
 - Sigstore transparency entry: 565627738
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.6 kB
- Tags: CPython 3.13t, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 69c0b73548bc525c8cb9a251cddf1931d1db4d2258e9599c28c07ef3580ef354 | |
| MD5 | 568420ce37d5a21d4ebe570ac67e4a58 | |
| BLAKE2b-256 | 80d62d1b89f6ca4bff1036499b1e29a1d02d282259f3681540e16563f27ebc23 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-win32.whl
 - Subject digest: 69c0b73548bc525c8cb9a251cddf1931d1db4d2258e9599c28c07ef3580ef354
 - Sigstore transparency entry: 565628017
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.6 kB
- Tags: CPython 3.13t, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 8f71bc33915be5186016f675cd83a1e08523649b0e33efdb898db577ef5bb009 | |
| MD5 | 07f8cf72b08dca99f9ef1c074c90ce58 | |
| BLAKE2b-256 | 98c5c03c7f4125180fc215220c035beac6b9cb684bc7a067c84fc69414d315f5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_x86_64.whl
 - Subject digest: 8f71bc33915be5186016f675cd83a1e08523649b0e33efdb898db577ef5bb009
 - Sigstore transparency entry: 565627883
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.8 kB
- Tags: CPython 3.13t, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 12c63dfb4a98206f045aa9563db46507995f7ef6d83b2f68eda65c307c6829eb | |
| MD5 | 953bd9869070d958440a96a8447004bc | |
| BLAKE2b-256 | 6a703780e9b72180b6fecb83a4814d84c3bf4b4ae4bf0b19c27196104149734c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_riscv64.whl
 - Subject digest: 12c63dfb4a98206f045aa9563db46507995f7ef6d83b2f68eda65c307c6829eb
 - Sigstore transparency entry: 565627925
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 24.8 kB
- Tags: CPython 3.13t, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 9b79b7a16f7fedff2495d684f2b59b0457c3b493778c9eed31111be64d58279f | |
| MD5 | 6b291b75ae3d8db5c81e4bd3df5b386b | |
| BLAKE2b-256 | 58474a0ccea4ab9f5dcb6f79c0236d954acb382202721e704223a8aafa38b5c8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-musllinux_1_2_aarch64.whl
 - Subject digest: 9b79b7a16f7fedff2495d684f2b59b0457c3b493778c9eed31111be64d58279f
 - Sigstore transparency entry: 565627828
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.3 kB
- Tags: CPython 3.13t, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | b8512a91625c9b3da6f127803b166b629725e68af71f8184ae7e7d54686a56d6 | |
| MD5 | bc811a17607dc8dbf6a4c5f53d37a7a4 | |
| BLAKE2b-256 | 4b306f2fce1f1f205fc9323255b216ca8a235b15860c34b6798f810f05828e32 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: b8512a91625c9b3da6f127803b166b629725e68af71f8184ae7e7d54686a56d6
 - Sigstore transparency entry: 565627863
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.6 kB
- Tags: CPython 3.13t, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 8709b08f4a89aa7586de0aadc8da56180242ee0ada3999749b183aa23df95025 | |
| MD5 | 0c8b61e407a7ce06245852877b4eee5f | |
| BLAKE2b-256 | 96ec2102e881fe9d25fc16cb4b25d5f5cde50970967ffa5dddafdb771237062d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 8709b08f4a89aa7586de0aadc8da56180242ee0ada3999749b183aa23df95025
 - Sigstore transparency entry: 565627781
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 25.6 kB
- Tags: CPython 3.13t, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 4e885a3d1efa2eadc93c894a21770e4bc67899e3543680313b09f139e149ab19 | |
| MD5 | 480a95174d6a8837e488181975a0d7de | |
| BLAKE2b-256 | bce6fa0ffcda717ef64a5108eaa7b4f5ed28d56122c9a6d70ab8b72f9f715c80 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 4e885a3d1efa2eadc93c894a21770e4bc67899e3543680313b09f139e149ab19
 - Sigstore transparency entry: 565627712
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.1 kB
- Tags: CPython 3.13t, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 3524b778fe5cfb3452a09d31e7b5adefeea8c5be1d43c4f810ba09f2ceb29d37 | |
| MD5 | 0a830365d0864e91e4e144b21c5d1366 | |
| BLAKE2b-256 | 999ee412117548182ce2148bdeacdda3bb494260c0b0184360fe0d56389b523b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-macosx_11_0_arm64.whl
 - Subject digest: 3524b778fe5cfb3452a09d31e7b5adefeea8c5be1d43c4f810ba09f2ceb29d37
 - Sigstore transparency entry: 565627917
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313t-macosx_10_13_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313t-macosx_10_13_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.7 kB
- Tags: CPython 3.13t, macOS 10.13+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313t-macosx_10_13_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 218551f6df4868a8d527e3062d0fb968682fe92054e89978594c28e642c43a73 | |
| MD5 | 50be11c16c5c6303c62ffe48e37ee558 | |
| BLAKE2b-256 | e4d7e05cd7efe43a88a17a37b3ae96e79a19e846f3f456fe79c57ca61356ef01 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313t-macosx_10_13_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313t-macosx_10_13_x86_64.whl
 - Subject digest: 218551f6df4868a8d527e3062d0fb968682fe92054e89978594c28e642c43a73
 - Sigstore transparency entry: 565627702
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 13.9 kB
- Tags: CPython 3.13, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 7e68f88e5b8799aa49c85cd116c932a1ac15caaa3f5db09087854d218359e485 | |
| MD5 | 04ba29977bf1de22f74a39e72de367cb | |
| BLAKE2b-256 | f03afa34a0f7cfef23cf9500d68cb7c32dd64ffd58a12b09225fb03dd37d5b80 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-win_arm64.whl
 - Subject digest: 7e68f88e5b8799aa49c85cd116c932a1ac15caaa3f5db09087854d218359e485
 - Sigstore transparency entry: 565627825
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.1 kB
- Tags: CPython 3.13, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5 | |
| MD5 | d8d34aa05e0c14e2ed46cc8c5ddd029b | |
| BLAKE2b-256 | 0573c4abe620b841b6b791f2edc248f556900667a5a1cf023a6646967ae98335 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-win_amd64.whl
 - Subject digest: 9a1abfdc021a164803f4d485104931fb8f8c1efd55bc6b748d2f5774e78b62c5
 - Sigstore transparency entry: 565627877
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.5 kB
- Tags: CPython 3.13, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-win32.whl
| Algorithm | Hash digest | |
| SHA256 | bdd37121970bfd8be76c5fb069c7751683bdf373db1ed6c010162b2a130248ed | |
| MD5 | 06d7dbbb3a8ab69f7f73405a271c4b7d | |
| BLAKE2b-256 | 19bce7140ed90c5d61d77cea142eed9f9c303f4c4806f60a1044c13e3f1471d0 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-win32.whl
 - Subject digest: bdd37121970bfd8be76c5fb069c7751683bdf373db1ed6c010162b2a130248ed
 - Sigstore transparency entry: 565627696
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.0 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 8485f406a96febb5140bfeca44a73e3ce5116b2501ac54fe953e488fb1d03b12 | |
| MD5 | de5ba9b4b5422e609751c129278a3c0c | |
| BLAKE2b-256 | b59916a5eb2d140087ebd97180d95249b00a03aa87e29cc224056274f2e45fd6 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-musllinux_1_2_x86_64.whl
 - Subject digest: 8485f406a96febb5140bfeca44a73e3ce5116b2501ac54fe953e488fb1d03b12
 - Sigstore transparency entry: 565627746
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.6 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 795e7751525cae078558e679d646ae45574b47ed6e7771863fcc079a6171a0fc | |
| MD5 | c97b1d6bc3a55399dc0d72aa797137a8 | |
| BLAKE2b-256 | ed76104b2aa106a208da8b17a2fb72e033a5a9d7073c68f7e508b94916ed47a9 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-musllinux_1_2_riscv64.whl
 - Subject digest: 795e7751525cae078558e679d646ae45574b47ed6e7771863fcc079a6171a0fc
 - Sigstore transparency entry: 565627723
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.8 kB
- Tags: CPython 3.13, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | a4afe79fb3de0b7097d81da19090f4df4f8d3a2b3adaa8764138aac2e44f3af1 | |
| MD5 | c281e14077483234ed6857d9e542968a | |
| BLAKE2b-256 | c228b50fc2f74d1ad761af2f5dcce7492648b983d00a65b8c0e0cb457c82ebbe | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-musllinux_1_2_aarch64.whl
 - Subject digest: a4afe79fb3de0b7097d81da19090f4df4f8d3a2b3adaa8764138aac2e44f3af1
 - Sigstore transparency entry: 565627762
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.0 kB
- Tags: CPython 3.13, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 509fa21c6deb7a7a273d629cf5ec029bc209d1a51178615ddf718f5918992ab9 | |
| MD5 | 063639d2e8a3cda0f2bd91147bc7bcb4 | |
| BLAKE2b-256 | 7f71544260864f893f18b6827315b988c146b559391e6e7e8f7252839b1b846a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 509fa21c6deb7a7a273d629cf5ec029bc209d1a51178615ddf718f5918992ab9
 - Sigstore transparency entry: 565627840
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.0 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | ccfcd093f13f0f0b7fdd0f198b90053bf7b2f02a3927a30e63f3ccc9df56b676 | |
| MD5 | c05c37ed90dd571df4f146632b52c884 | |
| BLAKE2b-256 | a9219b05698b46f218fc0e118e1f8168395c65c8a2c750ae2bab54fc4bd4e0e8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: ccfcd093f13f0f0b7fdd0f198b90053bf7b2f02a3927a30e63f3ccc9df56b676
 - Sigstore transparency entry: 565627698
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 24.4 kB
- Tags: CPython 3.13, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 133a43e73a802c5562be9bbcd03d090aa5a1fe899db609c29e8c8d815c5f6de6 | |
| MD5 | 3dba43257ba4d70ac12b2ac371d30632 | |
| BLAKE2b-256 | 0007575a68c754943058c78f30db02ee03a64b3c638586fba6a6dd56830b30a3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 133a43e73a802c5562be9bbcd03d090aa5a1fe899db609c29e8c8d815c5f6de6
 - Sigstore transparency entry: 565628036
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.0 kB
- Tags: CPython 3.13, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 116bb52f642a37c115f517494ea5feb03889e04df47eeff5b130b1808ce7c219 | |
| MD5 | 8b3d9ec4ee1ae3d6f46f8efe9057d555 | |
| BLAKE2b-256 | 9cd95f7756922cdd676869eca1c4e3c0cd0df60ed30199ffd775e319089cb3ed | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-macosx_11_0_arm64.whl
 - Subject digest: 116bb52f642a37c115f517494ea5feb03889e04df47eeff5b130b1808ce7c219
 - Sigstore transparency entry: 565628010
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp313-cp313-macosx_10_13_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp313-cp313-macosx_10_13_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.6 kB
- Tags: CPython 3.13, macOS 10.13+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp313-cp313-macosx_10_13_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | e1cf1972137e83c5d4c136c43ced9ac51d0e124706ee1c8aa8532c1287fa8795 | |
| MD5 | 0d7f15d256829d0d3f14aee8bbdff2f8 | |
| BLAKE2b-256 | 382f907b9c7bbba283e68f20259574b13d005c121a0fa4c175f9bed27c4597ff | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp313-cp313-macosx_10_13_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp313-cp313-macosx_10_13_x86_64.whl
 - Subject digest: e1cf1972137e83c5d4c136c43ced9ac51d0e124706ee1c8aa8532c1287fa8795
 - Sigstore transparency entry: 565627695
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 13.9 kB
- Tags: CPython 3.12, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 35add3b638a5d900e807944a078b51922212fb3dedb01633a8defc4b01a3c85f | |
| MD5 | 23ccba9662cf6a52c391bb67604b7c04 | |
| BLAKE2b-256 | e5f1216fc1bbfd74011693a4fd837e7026152e89c4bcf3e77b6692fba9923123 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-win_arm64.whl
 - Subject digest: 35add3b638a5d900e807944a078b51922212fb3dedb01633a8defc4b01a3c85f
 - Sigstore transparency entry: 565627907
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.1 kB
- Tags: CPython 3.12, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 26a5784ded40c9e318cfc2bdb30fe164bdb8665ded9cd64d500a34fb42067b1c | |
| MD5 | 2a1376ead47461d91373005bf78fa316 | |
| BLAKE2b-256 | aa5bbec5aa9bbbb2c946ca2733ef9c4ca91c91b6a24580193e891b5f7dbe8e1e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-win_amd64.whl
 - Subject digest: 26a5784ded40c9e318cfc2bdb30fe164bdb8665ded9cd64d500a34fb42067b1c
 - Sigstore transparency entry: 565627934
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.5 kB
- Tags: CPython 3.12, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-win32.whl
| Algorithm | Hash digest | |
| SHA256 | d88b440e37a16e651bda4c7c2b930eb586fd15ca7406cb39e211fcff3bf3017d | |
| MD5 | b50a1632de5d50b82c96072c69ed5fe6 | |
| BLAKE2b-256 | 2fe178ee7a023dac597a5825441ebd17170785a9dab23de95d2c7508ade94e0e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-win32.whl
 - Subject digest: d88b440e37a16e651bda4c7c2b930eb586fd15ca7406cb39e211fcff3bf3017d
 - Sigstore transparency entry: 565627984
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.0 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 77f0643abe7495da77fb436f50f8dab76dbc6e5fd25d39589a0f1fe6548bfa2b | |
| MD5 | 2dbc367518f2e2f0d843aa9f532d631d | |
| BLAKE2b-256 | 89e04486f11e51bbba8b0c041098859e869e304d1c261e59244baa3d295d47b7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-musllinux_1_2_x86_64.whl
 - Subject digest: 77f0643abe7495da77fb436f50f8dab76dbc6e5fd25d39589a0f1fe6548bfa2b
 - Sigstore transparency entry: 565627715
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.5 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 83891d0e9fb81a825d9a6d61e3f07550ca70a076484292a70fde82c4b807286f | |
| MD5 | 458322b1110e64d68d387e9d3a66786b | |
| BLAKE2b-256 | 324367935f2b7e4982ffb50a4d169b724d74b62a3964bc1a9a527f5ac4f1ee2b | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-musllinux_1_2_riscv64.whl
 - Subject digest: 83891d0e9fb81a825d9a6d61e3f07550ca70a076484292a70fde82c4b807286f
 - Sigstore transparency entry: 565627757
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.8 kB
- Tags: CPython 3.12, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | be8813b57049a7dc738189df53d69395eba14fb99345e0a5994914a3864c8a4b | |
| MD5 | 383cddf2e8c8e0cc01d12d8d6078db04 | |
| BLAKE2b-256 | c92f336b8c7b6f4a4d95e91119dc8521402461b74a485558d8f238a68312f11c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-musllinux_1_2_aarch64.whl
 - Subject digest: be8813b57049a7dc738189df53d69395eba14fb99345e0a5994914a3864c8a4b
 - Sigstore transparency entry: 565627801
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.0 kB
- Tags: CPython 3.12, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 94c6f0bb423f739146aec64595853541634bde58b2135f27f61c1ffd1cd4d16a | |
| MD5 | ea58cadd5b4bf5d9ca669dddac32fdb3 | |
| BLAKE2b-256 | 2c54887f3092a85238093a0b2154bd629c89444f395618842e8b0c41783898ea | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 94c6f0bb423f739146aec64595853541634bde58b2135f27f61c1ffd1cd4d16a
 - Sigstore transparency entry: 565627873
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.9 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | d6dd0be5b5b189d31db7cda48b91d7e0a9795f31430b7f271219ab30f1d3ac9d | |
| MD5 | fcd28e22417988c5b5916dbff4f791a1 | |
| BLAKE2b-256 | 3c2e8d0c2ab90a8c1d9a24f0399058ab8519a3279d1bd4289511d74e909f060e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: d6dd0be5b5b189d31db7cda48b91d7e0a9795f31430b7f271219ab30f1d3ac9d
 - Sigstore transparency entry: 565627680
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 24.3 kB
- Tags: CPython 3.12, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 3a7e8ae81ae39e62a41ec302f972ba6ae23a5c5396c8e60113e9066ef893da0d | |
| MD5 | a7e82e2718ab572d1060b385103d4590 | |
| BLAKE2b-256 | 1e2c799f4742efc39633a1b54a92eec4082e4f815314869865d876824c257c1e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 3a7e8ae81ae39e62a41ec302f972ba6ae23a5c5396c8e60113e9066ef893da0d
 - Sigstore transparency entry: 565627832
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.0 kB
- Tags: CPython 3.12, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 1872df69a4de6aead3491198eaf13810b565bdbeec3ae2dc8780f14458ec73ce | |
| MD5 | 06843eff5ffe519f2ad13143a70a50f6 | |
| BLAKE2b-256 | 9a817e4e08678a1f98521201c3079f77db69fb552acd56067661f8c2f534a718 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-macosx_11_0_arm64.whl
 - Subject digest: 1872df69a4de6aead3491198eaf13810b565bdbeec3ae2dc8780f14458ec73ce
 - Sigstore transparency entry: 565627885
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp312-cp312-macosx_10_13_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp312-cp312-macosx_10_13_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.6 kB
- Tags: CPython 3.12, macOS 10.13+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp312-cp312-macosx_10_13_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | d53197da72cc091b024dd97249dfc7794d6a56530370992a5e1a08983ad9230e | |
| MD5 | 5e6e0fa3bd5c2ed6dfb7aee4f017a457 | |
| BLAKE2b-256 | 5a72147da192e38635ada20e0a2e1a51cf8823d2119ce8883f7053879c2199b5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp312-cp312-macosx_10_13_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp312-cp312-macosx_10_13_x86_64.whl
 - Subject digest: d53197da72cc091b024dd97249dfc7794d6a56530370992a5e1a08983ad9230e
 - Sigstore transparency entry: 565627778
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 13.9 kB
- Tags: CPython 3.11, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 3b562dd9e9ea93f13d53989d23a7e775fdfd1066c33494ff43f5418bc8c58a5c | |
| MD5 | aaf43408cd0d0fd6806dc70791ba2bf0 | |
| BLAKE2b-256 | 3573893072b42e6862f319b5207adc9ae06070f095b358655f077f69a35601f0 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-win_arm64.whl
 - Subject digest: 3b562dd9e9ea93f13d53989d23a7e775fdfd1066c33494ff43f5418bc8c58a5c
 - Sigstore transparency entry: 565628048
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.1 kB
- Tags: CPython 3.11, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | de8a88e63464af587c950061a5e6a67d3632e36df62b986892331d4620a35c01 | |
| MD5 | 02e3d025fea204cbe5d5b6ccfb4ca902 | |
| BLAKE2b-256 | 838a4414c03d3f891739326e1783338e48fb49781cc915b2e0ee052aa490d586 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-win_amd64.whl
 - Subject digest: de8a88e63464af587c950061a5e6a67d3632e36df62b986892331d4620a35c01
 - Sigstore transparency entry: 565627860
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.6 kB
- Tags: CPython 3.11, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 0db14f5dafddbb6d9208827849fad01f1a2609380add406671a26386cdf15a19 | |
| MD5 | 3b778d58a7f2f6bc6b73d9a6e6a47f76 | |
| BLAKE2b-256 | 0f62d9c46a7f5c9adbeeeda52f5b8d802e1094e9717705a645efc71b0913a0a8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-win32.whl
 - Subject digest: 0db14f5dafddbb6d9208827849fad01f1a2609380add406671a26386cdf15a19
 - Sigstore transparency entry: 565628050
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.9 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | f9e130248f4462aaa8e2552d547f36ddadbeaa573879158d721bbd33dfe4743a | |
| MD5 | 5e7d03c2abc41cc9418c76b40299b387 | |
| BLAKE2b-256 | 627ea145f36a5c2945673e590850a6f8014318d5577ed7e5920a4b3448e0865d | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-musllinux_1_2_x86_64.whl
 - Subject digest: f9e130248f4462aaa8e2552d547f36ddadbeaa573879158d721bbd33dfe4743a
 - Sigstore transparency entry: 565627729
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.5 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 7be7b61bb172e1ed687f1754f8e7484f1c8019780f6f6b0786e76bb01c2ae115 | |
| MD5 | db34a6eab86518ee6095c28dc66dd618 | |
| BLAKE2b-256 | a4286e74cdd26d7514849143d69f0bf2399f929c37dc2b31e6829fd2045b2765 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-musllinux_1_2_riscv64.whl
 - Subject digest: 7be7b61bb172e1ed687f1754f8e7484f1c8019780f6f6b0786e76bb01c2ae115
 - Sigstore transparency entry: 565627790
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 23.7 kB
- Tags: CPython 3.11, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 068f375c472b3e7acbe2d5318dea141359e6900156b5b2ba06a30b169086b91a | |
| MD5 | 023feb818f4d144595eec60738558485 | |
| BLAKE2b-256 | b2767edcab99d5349a4532a459e1fe64f0b0467a3365056ae550d3bcf3f79e1e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-musllinux_1_2_aarch64.whl
 - Subject digest: 068f375c472b3e7acbe2d5318dea141359e6900156b5b2ba06a30b169086b91a
 - Sigstore transparency entry: 565627896
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.9 kB
- Tags: CPython 3.11, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | bc51efed119bc9cfdf792cdeaa4d67e8f6fcccab66ed4bfdd6bde3e59bfcbb2f | |
| MD5 | 4493d5a45ad443dd34574f6bf43ca2b7 | |
| BLAKE2b-256 | 19ae31c1be199ef767124c042c6c3e904da327a2f7f0cd63a0337e1eca2967a8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: bc51efed119bc9cfdf792cdeaa4d67e8f6fcccab66ed4bfdd6bde3e59bfcbb2f
 - Sigstore transparency entry: 565627744
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.9 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 0bf2a864d67e76e5c9a34dc26ec616a66b9888e25e7b9460e1c76d3293bd9dbf | |
| MD5 | 767b1fa0e89c012ef36e0b9e05ab7d1d | |
| BLAKE2b-256 | 30ac0273f6fcb5f42e314c6d8cd99effae6a5354604d461b8d392b5ec9530a54 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: 0bf2a864d67e76e5c9a34dc26ec616a66b9888e25e7b9460e1c76d3293bd9dbf
 - Sigstore transparency entry: 565627908
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 24.3 kB
- Tags: CPython 3.11, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 6b5420a1d9450023228968e7e6a9ce57f65d148ab56d2313fcd589eee96a7a50 | |
| MD5 | 294e7f97198c2d36497b6b7d1694fdc0 | |
| BLAKE2b-256 | 1d09adf2df3699d87d1d8184038df46a9c80d78c0148492323f4693df54e17bb | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 6b5420a1d9450023228968e7e6a9ce57f65d148ab56d2313fcd589eee96a7a50
 - Sigstore transparency entry: 565627952
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.1 kB
- Tags: CPython 3.11, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 4bd4cd07944443f5a265608cc6aab442e4f74dff8088b0dfc8238647b8f6ae9a | |
| MD5 | 5237d8b039e8b33fa685098327c9b81a | |
| BLAKE2b-256 | e12e5898933336b61975ce9dc04decbc0a7f2fee78c30353c5efba7f2d6ff27a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl
 - Subject digest: 4bd4cd07944443f5a265608cc6aab442e4f74dff8088b0dfc8238647b8f6ae9a
 - Sigstore transparency entry: 565627964
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp311-cp311-macosx_10_9_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp311-cp311-macosx_10_9_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.6 kB
- Tags: CPython 3.11, macOS 10.9+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp311-cp311-macosx_10_9_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 1cc7ea17a6824959616c525620e387f6dd30fec8cb44f649e31712db02123dad | |
| MD5 | d0db4a2a5bab31e44b4d133b512cbd23 | |
| BLAKE2b-256 | 08dbfefacb2136439fc8dd20e797950e749aa1f4997ed584c62cfb8ef7c2be0e | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp311-cp311-macosx_10_9_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp311-cp311-macosx_10_9_x86_64.whl
 - Subject digest: 1cc7ea17a6824959616c525620e387f6dd30fec8cb44f649e31712db02123dad
 - Sigstore transparency entry: 565628046
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 13.9 kB
- Tags: CPython 3.10, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | e2103a929dfa2fcaf9bb4e7c091983a49c9ac3b19c9061b6d5427dd7d14d81a1 | |
| MD5 | c32c889fdd964df96252f59a4c434b9d | |
| BLAKE2b-256 | d09e0a02226640c255d1da0b8d12e24ac2aa6734da68bff14c05dd53b94a0fc3 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-win_arm64.whl
 - Subject digest: e2103a929dfa2fcaf9bb4e7c091983a49c9ac3b19c9061b6d5427dd7d14d81a1
 - Sigstore transparency entry: 565627775
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.1 kB
- Tags: CPython 3.10, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | c4ffb7ebf07cfe8931028e3e4c85f0357459a3f9f9490886198848f4fa002ec8 | |
| MD5 | cc9392951ba1859589bb6fcd5f9446da | |
| BLAKE2b-256 | d62555dc3ab959917602c96985cb1253efaa4ff42f71194bddeb61eb7278b8be | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-win_amd64.whl
 - Subject digest: c4ffb7ebf07cfe8931028e3e4c85f0357459a3f9f9490886198848f4fa002ec8
 - Sigstore transparency entry: 565627932
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.6 kB
- Tags: CPython 3.10, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-win32.whl
| Algorithm | Hash digest | |
| SHA256 | 2a15a08b17dd94c53a1da0438822d70ebcd13f8c3a95abe3a9ef9f11a94830aa | |
| MD5 | c5adc353241627f2e26a55f780a021c0 | |
| BLAKE2b-256 | 8799faba9369a7ad6e4d10b6a5fbf71fa2a188fe4a593b15f0963b73859a1bbd | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-win32.whl
 - Subject digest: 2a15a08b17dd94c53a1da0438822d70ebcd13f8c3a95abe3a9ef9f11a94830aa
 - Sigstore transparency entry: 565627736
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.7 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 177b5253b2834fe3678cb4a5f0059808258584c559193998be2601324fdeafb1 | |
| MD5 | fa64516a9d05a06dd4eb24c307f621a0 | |
| BLAKE2b-256 | 5621dca11354e756ebd03e036bd8ad58d6d7168c80ce1fe5e75218e4945cbab7 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-musllinux_1_2_x86_64.whl
 - Subject digest: 177b5253b2834fe3678cb4a5f0059808258584c559193998be2601324fdeafb1
 - Sigstore transparency entry: 565627858
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.3 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | d2ee202e79d8ed691ceebae8e0486bd9a2cd4794cec4824e1c99b6f5009502f6 | |
| MD5 | 38771321fade055a5f76294a78944f4a | |
| BLAKE2b-256 | bc3623578f29e9e582a4d0278e009b38081dbe363c5e7165113fad546918a232 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-musllinux_1_2_riscv64.whl
 - Subject digest: d2ee202e79d8ed691ceebae8e0486bd9a2cd4794cec4824e1c99b6f5009502f6
 - Sigstore transparency entry: 565628027
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.5 kB
- Tags: CPython 3.10, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 0303439a41979d9e74d18ff5e2dd8c43ed6c6001fd40e5bf2e43f7bd9bbc523f | |
| MD5 | 4062452b0a207c9b1ce0789ae2d0e3c3 | |
| BLAKE2b-256 | cfe39427a68c82728d0a88c50f890d0fc072a1484de2f3ac1ad0bfc1a7214fd5 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-musllinux_1_2_aarch64.whl
 - Subject digest: 0303439a41979d9e74d18ff5e2dd8c43ed6c6001fd40e5bf2e43f7bd9bbc523f
 - Sigstore transparency entry: 565627956
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.7 kB
- Tags: CPython 3.10, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | c0c0b3ade1c0b13b936d7970b1d37a57acde9199dc2aecc4c336773e1d86049c | |
| MD5 | a8e172aa6d83495d270601ef5060f71d | |
| BLAKE2b-256 | c92ab5c12c809f1c3045c4d580b035a743d12fcde53cf685dbc44660826308da | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: c0c0b3ade1c0b13b936d7970b1d37a57acde9199dc2aecc4c336773e1d86049c
 - Sigstore transparency entry: 565628060
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.7 kB
- Tags: CPython 3.10, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | f42d0984e947b8adf7dd6dde396e720934d12c506ce84eea8476409563607591 | |
| MD5 | f0b62676dd5a7af5eeacdefb58a5784d | |
| BLAKE2b-256 | afcdce6e848bbf2c32314c9b237839119c5a564a59725b53157c856e90937b7a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: f42d0984e947b8adf7dd6dde396e720934d12c506ce84eea8476409563607591
 - Sigstore transparency entry: 565627988
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 22.1 kB
- Tags: CPython 3.10, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 1ba88449deb3de88bd40044603fafffb7bc2b055d626a330323a9ed736661695 | |
| MD5 | 309889a2e8c4bb45f1ef8bc66319b915 | |
| BLAKE2b-256 | 4001e560d658dc0bb8ab762670ece35281dec7b6c1b33f5fbc09ebb57a185519 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 1ba88449deb3de88bd40044603fafffb7bc2b055d626a330323a9ed736661695
 - Sigstore transparency entry: 565627869
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.1 kB
- Tags: CPython 3.10, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | e1c1493fb6e50ab01d20a22826e57520f1284df32f2d8601fdd90b6304601419 | |
| MD5 | 34e76ed392b542183edd5a6b23b8aa60 | |
| BLAKE2b-256 | 981bfbd8eed11021cabd9226c37342fa6ca4e8a98d8188a8d9b66740494960e4 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-macosx_11_0_arm64.whl
 - Subject digest: e1c1493fb6e50ab01d20a22826e57520f1284df32f2d8601fdd90b6304601419
 - Sigstore transparency entry: 565628059
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp310-cp310-macosx_10_9_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp310-cp310-macosx_10_9_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.6 kB
- Tags: CPython 3.10, macOS 10.9+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp310-cp310-macosx_10_9_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 2f981d352f04553a7171b8e44369f2af4055f888dfb147d55e42d29e29e74559 | |
| MD5 | 08f3e9158c7069aacb94c60746ad0cd0 | |
| BLAKE2b-256 | e84b3541d44f3937ba468b75da9eebcae497dcf67adb65caa16760b0a6807ebb | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp310-cp310-macosx_10_9_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp310-cp310-macosx_10_9_x86_64.whl
 - Subject digest: 2f981d352f04553a7171b8e44369f2af4055f888dfb147d55e42d29e29e74559
 - Sigstore transparency entry: 565627684
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-win_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-win_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 13.9 kB
- Tags: CPython 3.9, Windows ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-win_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | 38664109c14ffc9e7437e86b4dceb442b0096dfe3541d7864d9cbe1da4cf36c8 | |
| MD5 | 4063c9aa33dc0425b163eb572bada116 | |
| BLAKE2b-256 | 4ed3fe08482b5cd995033556d45041a4f4e76e7f0521112a9c9991d40d39825f | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-win_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-win_arm64.whl
 - Subject digest: 38664109c14ffc9e7437e86b4dceb442b0096dfe3541d7864d9cbe1da4cf36c8
 - Sigstore transparency entry: 565627687
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-win_amd64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-win_amd64.whl
- Upload date:
 Sep 27, 2025
- Size: 15.1 kB
- Tags: CPython 3.9, Windows x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-win_amd64.whl
| Algorithm | Hash digest | |
| SHA256 | 7c3fb7d25180895632e5d3148dbdc29ea38ccb7fd210aa27acbd1201a1902c6e | |
| MD5 | 63d73f55afd0ca654801b4704bba2a68 | |
| BLAKE2b-256 | 181f8d9c20e1c9440e215a44be5ab64359e207fcb4f675543f1cf9a2a7f648d0 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-win_amd64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-win_amd64.whl
 - Subject digest: 7c3fb7d25180895632e5d3148dbdc29ea38ccb7fd210aa27acbd1201a1902c6e
 - Sigstore transparency entry: 565627894
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-win32.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-win32.whl
- Upload date:
 Sep 27, 2025
- Size: 14.6 kB
- Tags: CPython 3.9, Windows x86
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-win32.whl
| Algorithm | Hash digest | |
| SHA256 | df2449253ef108a379b8b5d6b43f4b1a8e81a061d6537becd5582fba5f9196d7 | |
| MD5 | b6454d81bda225cf7c4751d3d457664c | |
| BLAKE2b-256 | cd1ba7782984844bd519ad4ffdbebbba2671ec5d0ebbeac34736c15fb86399e8 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-win32.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-win32.whl
 - Subject digest: df2449253ef108a379b8b5d6b43f4b1a8e81a061d6537becd5582fba5f9196d7
 - Sigstore transparency entry: 565627904
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-musllinux_1_2_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-musllinux_1_2_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.6 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-musllinux_1_2_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | a320721ab5a1aba0a233739394eb907f8c8da5c98c9181d1161e77a0c8e36f2d | |
| MD5 | b0968a316b360cb0ebf0d927eaad3d1e | |
| BLAKE2b-256 | dc0ac3cf2b4fef5f0426e8a6d7fce3cb966a17817c568ce59d76b92a233fdbec | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-musllinux_1_2_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-musllinux_1_2_x86_64.whl
 - Subject digest: a320721ab5a1aba0a233739394eb907f8c8da5c98c9181d1161e77a0c8e36f2d
 - Sigstore transparency entry: 565627912
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-musllinux_1_2_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-musllinux_1_2_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.1 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-musllinux_1_2_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 591ae9f2a647529ca990bc681daebdd52c8791ff06c2bfa05b65163e28102ef2 | |
| MD5 | 3bc8869252d59ca1d2866a15297c049f | |
| BLAKE2b-256 | c825651753ef4dea08ea790f4fbb65146a9a44a014986996ca40102e237aa49a | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-musllinux_1_2_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-musllinux_1_2_riscv64.whl
 - Subject digest: 591ae9f2a647529ca990bc681daebdd52c8791ff06c2bfa05b65163e28102ef2
 - Sigstore transparency entry: 565627768
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-musllinux_1_2_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-musllinux_1_2_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.4 kB
- Tags: CPython 3.9, musllinux: musl 1.2+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-musllinux_1_2_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 3537e01efc9d4dccdf77221fb1cb3b8e1a38d5428920e0657ce299b20324d758 | |
| MD5 | 9c6fd59711e3d378d3f854ad74e952de | |
| BLAKE2b-256 | f6f6e0e5a3d3ae9c4020f696cd055f940ef86b64fe88de26f3a0308b9d3d048c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-musllinux_1_2_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-musllinux_1_2_aarch64.whl
 - Subject digest: 3537e01efc9d4dccdf77221fb1cb3b8e1a38d5428920e0657ce299b20324d758
 - Sigstore transparency entry: 565627941
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.6 kB
- Tags: CPython 3.9, manylinux: glibc 2.31+ riscv64, manylinux: glibc 2.39+ riscv64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
| Algorithm | Hash digest | |
| SHA256 | 949b8d66bc381ee8b007cd945914c721d9aba8e27f71959d750a46f7c282b20b | |
| MD5 | 9705d1384a40856b541aa5122805449a | |
| BLAKE2b-256 | 896e5fe81fbcfba4aef4093d5f856e5c774ec2057946052d18d168219b7bd9f9 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl
 - Subject digest: 949b8d66bc381ee8b007cd945914c721d9aba8e27f71959d750a46f7c282b20b
 - Sigstore transparency entry: 565627880
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 20.5 kB
- Tags: CPython 3.9, manylinux: glibc 2.17+ x86-64, manylinux: glibc 2.28+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | e8fc20152abba6b83724d7ff268c249fa196d8259ff481f3b1476383f8f24e42 | |
| MD5 | c68b42fe169380144314e48de3c6b4be | |
| BLAKE2b-256 | 6fbc4dc914ead3fe6ddaef035341fee0fc956949bbd27335b611829292b89ee2 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl
 - Subject digest: e8fc20152abba6b83724d7ff268c249fa196d8259ff481f3b1476383f8f24e42
 - Sigstore transparency entry: 565627740
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
- Upload date:
 Sep 27, 2025
- Size: 21.9 kB
- Tags: CPython 3.9, manylinux: glibc 2.17+ ARM64, manylinux: glibc 2.28+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
| Algorithm | Hash digest | |
| SHA256 | 0f4b68347f8c5eab4a13419215bdfd7f8c9b19f2b25520968adfad23eb0ce60c | |
| MD5 | c3816875dba56fda42b3783e1159b9af | |
| BLAKE2b-256 | bce46be85eb81503f8e11b61c0b6369b6e077dcf0a74adbd9ebf6b349937b4e9 | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl
 - Subject digest: 0f4b68347f8c5eab4a13419215bdfd7f8c9b19f2b25520968adfad23eb0ce60c
 - Sigstore transparency entry: 565627751
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-macosx_11_0_arm64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-macosx_11_0_arm64.whl
- Upload date:
 Sep 27, 2025
- Size: 12.0 kB
- Tags: CPython 3.9, macOS 11.0+ ARM64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-macosx_11_0_arm64.whl
| Algorithm | Hash digest | |
| SHA256 | f71a396b3bf33ecaa1626c255855702aca4d3d9fea5e051b41ac59a9c1c41edc | |
| MD5 | c1083afd278eaf9cf2cee21068ba5214 | |
| BLAKE2b-256 | fd2307a2cb9a8045d5f3f0890a8c3bc0859d7a47bfd9a560b563899bec7b72ed | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-macosx_11_0_arm64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-macosx_11_0_arm64.whl
 - Subject digest: f71a396b3bf33ecaa1626c255855702aca4d3d9fea5e051b41ac59a9c1c41edc
 - Sigstore transparency entry: 565627998
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## File details

Details for the file markupsafe-3.0.3-cp39-cp39-macosx_10_9_x86_64.whl.

### File metadata

- Download URL: markupsafe-3.0.3-cp39-cp39-macosx_10_9_x86_64.whl
- Upload date:
 Sep 27, 2025
- Size: 11.6 kB
- Tags: CPython 3.9, macOS 10.9+ x86-64
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.1.0 CPython/3.13.7

### File hashes

Hashes for markupsafe-3.0.3-cp39-cp39-macosx_10_9_x86_64.whl
| Algorithm | Hash digest | |
| SHA256 | 15d939a21d546304880945ca1ecb8a039db6b4dc49b2c5a400387cdae6a62e26 | |
| MD5 | d22176ece70d568df8d0541a22cc4725 | |
| BLAKE2b-256 | 56230d8c13a44bde9154821586520840643467aee574d8ce79a17da539ee7fed | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for markupsafe-3.0.3-cp39-cp39-macosx_10_9_x86_64.whl:

Publisher: publish.yaml on pallets/markupsafe

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: markupsafe-3.0.3-cp39-cp39-macosx_10_9_x86_64.whl
 - Subject digest: 15d939a21d546304880945ca1ecb8a039db6b4dc49b2c5a400387cdae6a62e26
 - Sigstore transparency entry: 565627991
 - Sigstore integration time:
 Sep 27, 2025
 Source repository:

 - Permalink: pallets/markupsafe@297fc8e356e6836a62087949245d09a28e9f1b13
 - Branch / Tag: refs/tags/3.0.3
 - Owner: https://github.com/pallets
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 publish.yaml@297fc8e356e6836a62087949245d09a28e9f1b13
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

3.0.3 This release

Sep 27, 2025
 89 files

3.0.2

Oct 18, 2024
 61 files

3.0.1

Oct 8, 2024
 61 files

3.0.0

Oct 7, 2024
 61 files

2.1.5

Feb 2, 2024
 60 files

2.1.4

Jan 19, 2024
 60 files

2.1.3

Jun 2, 2023
 60 files

2.1.2

Jan 17, 2023
 50 files

2.1.1

Mar 15, 2022
 40 files

2.1.0

Feb 18, 2022
 40 files

2.0.1

May 18, 2021
 69 files

2.0.0

May 11, 2021
 34 files

Pre-release

2.0.0rc2

Apr 16, 2021
 34 files

Pre-release

2.0.0rc1

Feb 15, 2021
 34 files

Pre-release

2.0.0a1

Apr 10, 2020
 22 files

1.1.1

Feb 24, 2019
 52 files

1.1.0

Nov 5, 2018
 28 files

1.0

Mar 7, 2017
 1 file

0.23

May 8, 2014
 1 file

0.22

May 8, 2014
 1 file

0.21

Apr 17, 2014
 1 file

0.20

Apr 17, 2014
 1 file

0.19

Mar 6, 2014
 1 file

0.18

May 22, 2013
 1 file

0.17

May 21, 2013
 1 file

0.16

May 20, 2013
 1 file

0.15

Jul 20, 2011
 1 file

0.14

Jul 20, 2011
 1 file

0.13

Jul 20, 2011
 1 file

0.12

Feb 17, 2011
 1 file

0.11

Sep 7, 2010
 1 file

0.9.3

Aug 11, 2010
 1 file

0.9.2

Jun 22, 2010
 1 file

0.9.1

Jun 22, 2010
 1 file

0.9

Jun 22, 2010
 1 file