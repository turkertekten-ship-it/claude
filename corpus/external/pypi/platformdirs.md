# platformdirs

[image: PyPI version] [image: Python versions] [image: CI] [image: Downloads]

A Python package for determining platform-specific directories (e.g. user data, config, cache, logs). Handles the
differences between macOS, Windows, Linux/Unix, and Android so you don't have to.

## Quick start

```
from platformdirs import PlatformDirs

dirs = PlatformDirs("MyApp", "MyCompany")
dirs.user_data_dir  # ~/.local/share/MyApp (Linux)
dirs.user_config_dir  # ~/.config/MyApp (Linux)
dirs.user_cache_dir  # ~/.cache/MyApp (Linux)
dirs.user_state_dir  # ~/.local/state/MyApp (Linux)
dirs.user_log_dir  # ~/.local/state/MyApp/log (Linux)
dirs.user_documents_dir  # ~/Documents
dirs.user_downloads_dir  # ~/Downloads
dirs.user_runtime_dir  # /run/user/<uid>/MyApp (Linux)
```

For Path objects instead of strings:

```
from platformdirs import PlatformDirs

dirs = PlatformDirs("MyApp", "MyCompany")
dirs.user_data_path  # pathlib.Path('~/.local/share/MyApp')
dirs.user_config_path  # pathlib.Path('~/.config/MyApp')
```

Convenience functions for quick access:

```
from platformdirs import user_data_dir, user_config_path

user_data_dir("MyApp", "MyCompany")  # returns str
user_config_path("MyApp", "MyCompany")  # returns pathlib.Path
```

## Directory types

Application directories — scoped to your app name and version:

- Data: Persistent application data (user_data_dir, site_data_dir)
- Config: Configuration files and settings (user_config_dir, site_config_dir)
- Preference: User preferences, distinct from config on macOS (user_preference_dir)
- Cache: Cached data that can be regenerated (user_cache_dir, site_cache_dir)
- State: Non-essential runtime state like window positions (user_state_dir, site_state_dir)
- Logs: Log files (user_log_dir, site_log_dir)
- Runtime: Runtime files like sockets and PIDs (user_runtime_dir, site_runtime_dir)

App dirs have both user_* (per-user, writable) and site_* (system-wide, read-only) variants where applicable.

User media directories — standard user-facing folders, not scoped to app name:

- Documents (user_documents_dir), Downloads (user_downloads_dir)
- Pictures (user_pictures_dir), Videos (user_videos_dir), Music (user_music_dir)
- Desktop (user_desktop_dir), Projects (user_projects_dir)
- Public share (user_publicshare_dir), Templates (user_templates_dir)
- Fonts (user_fonts_dir) — user-writable font installation directory
- Executable (user_bin_dir, site_bin_dir), Applications (user_applications_dir, site_applications_dir)

## Documentation

Full documentation is available at platformdirs.readthedocs.io:

- Getting started tutorial -- learn core concepts
through real-world examples
- How-to guides -- recipes for common tasks and
platform-specific tips
- API reference -- complete list of functions and classes
- Platform details -- default paths for each
operating system

Contributions are welcome! See CONTRIBUTING.md for
details.

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about installing packages.

### Source Distribution

platformdirs-4.11.5.tar.gz
 (34.8 kB
 view details)

Uploaded
 Aug 27, 2026
 Source

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about wheel file names.

Copy a direct link to the current filters

platformdirs-4.11.5-py3-none-any.whl
 (23.9 kB
 view details)

Uploaded
 Aug 27, 2026
 Python 3

## File details

Details for the file platformdirs-4.11.5.tar.gz.

### File metadata

- Download URL: platformdirs-4.11.5.tar.gz
- Upload date:
 Aug 27, 2026
- Size: 34.8 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for platformdirs-4.11.5.tar.gz
| Algorithm | Hash digest | |
| SHA256 | e8b31f4f8bcbbedef91a6b57a706255e4f148d2a4e01648382a0a47342539173 | |
| MD5 | f5203ede5814c9fccd5db7c86c0d9252 | |
| BLAKE2b-256 | ea06cf1564dcc2e2261c8c8c6c05628dc8b418943bdae2a4e58640ceb2f770fa | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for platformdirs-4.11.5.tar.gz:

Publisher: release.yaml on tox-dev/platformdirs

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: platformdirs-4.11.5.tar.gz
 - Subject digest: e8b31f4f8bcbbedef91a6b57a706255e4f148d2a4e01648382a0a47342539173
 - Sigstore transparency entry: 2619059692
 - Sigstore integration time:
 Aug 27, 2026
 Source repository:

 - Permalink: tox-dev/platformdirs@bd77b0dc378e5e12a1085db1ef9987d074e07880
 - Branch / Tag: refs/tags/4.11.5
 - Owner: https://github.com/tox-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 release.yaml@bd77b0dc378e5e12a1085db1ef9987d074e07880
 - Trigger Event: push

## File details

Details for the file platformdirs-4.11.5-py3-none-any.whl.

### File metadata

- Download URL: platformdirs-4.11.5-py3-none-any.whl
- Upload date:
 Aug 27, 2026
- Size: 23.9 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/7.0.0 CPython/3.13.14

### File hashes

Hashes for platformdirs-4.11.5-py3-none-any.whl
| Algorithm | Hash digest | |
| SHA256 | 89f8d42695853b89c7170bd49bc3dc593f98a71e695ede88e06a3b247bc4563b | |
| MD5 | 44f5b765f4c9182a859f7f34040b1a97 | |
| BLAKE2b-256 | c7126f3fcd5067a9cbf4f8664b32957973498da8b083455203c8d9cab83a725c | |

See more details on using hashes here.

### Provenance

The following attestation bundles were made for platformdirs-4.11.5-py3-none-any.whl:

Publisher: release.yaml on tox-dev/platformdirs

 Attestations:
 Values shown here reflect the state when the release was signed and may no longer be current.

- Statement:

 - Statement type: https://in-toto.io/Statement/v1
 - Predicate type: https://docs.pypi.org/attestations/publish/v1
 - Subject name: platformdirs-4.11.5-py3-none-any.whl
 - Subject digest: 89f8d42695853b89c7170bd49bc3dc593f98a71e695ede88e06a3b247bc4563b
 - Sigstore transparency entry: 2619059767
 - Sigstore integration time:
 Aug 27, 2026
 Source repository:

 - Permalink: tox-dev/platformdirs@bd77b0dc378e5e12a1085db1ef9987d074e07880
 - Branch / Tag: refs/tags/4.11.5
 - Owner: https://github.com/tox-dev
 - Access: public
 Publication detail:

 - Token Issuer: https://token.actions.githubusercontent.com
 - Runner Environment: github-hosted
 - Publication workflow:
 release.yaml@bd77b0dc378e5e12a1085db1ef9987d074e07880
 - Trigger Event: push

## Release history Release notifications |
 RSS feed

This release

4.11.5 This release

Aug 27, 2026
 2 files

4.11.4

Aug 24, 2026
 2 files

4.11.3

Aug 13, 2026
 2 files

4.11.2

Aug 10, 2026
 2 files

4.11.1

Aug 7, 2026
 2 files

4.11.0

Jul 21, 2026
 2 files

4.10.1

Jul 18, 2026
 2 files

4.10.0

May 28, 2026
 2 files

4.9.6

Apr 9, 2026
 2 files

4.9.4

Mar 5, 2026
 2 files

4.9.2

Feb 16, 2026
 2 files

4.9.1

Feb 14, 2026
 2 files

4.9.0

Feb 14, 2026
 2 files

4.8.0

Feb 14, 2026
 2 files

4.7.1

Feb 13, 2026
 2 files

4.7.0

Feb 12, 2026
 2 files

4.6.0

Feb 12, 2026
 2 files

4.5.1

Dec 5, 2025
 2 files

4.5.0

Oct 8, 2025
 2 files

4.4.0

Aug 26, 2025
 2 files

4.3.8

May 7, 2025
 2 files

4.3.7

Mar 19, 2025
 2 files

4.3.6

Sep 17, 2024
 2 files

4.3.5

Sep 17, 2024
 2 files

4.3.4

Sep 17, 2024
 2 files

4.3.3

Sep 13, 2024
 2 files

4.3.2

Sep 8, 2024
 2 files

4.3.1

Sep 7, 2024
 2 files

4.3.0

Sep 7, 2024
 2 files

4.2.2

May 15, 2024
 2 files

4.2.1

Apr 23, 2024
 2 files

4.2.0

Jan 31, 2024
 2 files

4.1.0

Dec 4, 2023
 2 files

4.0.0

Nov 10, 2023
 2 files

3.11.0

Oct 2, 2023
 2 files

3.10.0

Jul 29, 2023
 2 files

3.9.1

Jul 15, 2023
 2 files

3.9.0

Jul 15, 2023
 2 files

3.8.1

Jul 6, 2023
 2 files

3.8.0

Jun 23, 2023
 2 files

3.7.0

Jun 21, 2023
 2 files

3.6.0

Jun 18, 2023
 2 files

3.5.3

Jun 10, 2023
 2 files

3.5.2

Jun 10, 2023
 2 files

3.5.1

May 11, 2023
 2 files

3.5.0

Apr 27, 2023
 2 files

3.4.0

Apr 26, 2023
 2 files

3.3.0

Apr 25, 2023
 2 files

3.2.0

Mar 25, 2023
 2 files

3.1.1

Mar 10, 2023
 2 files

3.1.0

Mar 3, 2023
 2 files

3.0.0

Feb 6, 2023
 2 files

2.6.2

Dec 28, 2022
 2 files

2.6.1

Dec 28, 2022
 2 files

2.6.0

Dec 7, 2022
 2 files

2.5.4

Nov 13, 2022
 2 files

2.5.3

Nov 6, 2022
 2 files

2.5.2

Apr 18, 2022
 2 files

2.5.1

Feb 19, 2022
 2 files

2.5.0

Feb 9, 2022
 2 files

2.4.1

Dec 26, 2021
 2 files

2.4.0

Sep 25, 2021
 2 files

2.3.0

Aug 30, 2021
 2 files

2.2.0

Jul 29, 2021
 2 files

2.1.0

Jul 25, 2021
 2 files

2.0.2

Jul 13, 2021
 2 files

2.0.0

Jul 12, 2021
 2 files

Pre-release

2.0.0a3

May 14, 2021
 2 files

Pre-release

2.0.0a2

May 13, 2021
 2 files

Pre-release

2.0.0a1

May 13, 2021
 2 files