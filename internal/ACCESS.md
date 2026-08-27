# Access capability report

Generated: 2026-08-27 15:03:08Z  
Probe duration: 2.96s  
Summary: 4 blocked, 1 degraded, 5 ok

## Environment

- **anthropic_key**: `absent`
- **github_token**: `present`
- **hostname**: `vm`
- **https_proxy**: `http://127.0.0.1:37597`
- **numpy**: `absent (pure-python scoring)`
- **proxy_enabled**: `True`
- **voyage_key**: `absent`

## Probes

| Capability | Kind | Target | Status | Latency | Detail |
|---|---|---|---|---|---|
| github_api | github | `api.github.com` | ok | 579ms | 15000/15000 requests remaining |
| github_raw | github | `raw.githubusercontent.com` | ok | 430ms | 8912 bytes |
| github_repo_scope | github | `turkertekten-ship-it/claude,turkertekten-ship-it/...` | degraded | 2956ms | 2 readable, 1 denied |
| filesystem_write | local | `.oodarag` | ok | 5ms | writable, 30625 MB free |
| pypi | packages | `pypi.org` | ok | 48ms | pip 26.2.1 visible |
| web_arxiv | web | `arxiv.org` | **blocked** | 539ms | proxy refused CONNECT (403) |
| web_ibm | web | `www.ibm.com` | **blocked** | 371ms | proxy refused CONNECT (403) |
| web_pypi | web | `pypi.org` | ok | 37ms | HTTP 200, 246270 bytes |
| web_wikipedia | web | `en.wikipedia.org` | **blocked** | 486ms | proxy refused CONNECT (403) |
| web_youtube | web | `www.youtube.com` | **blocked** | 335ms | proxy refused CONNECT (403) |

## Required degradations

1. Some web hosts are blocked (en.wikipedia.org, www.youtube.com, www.ibm.com, arxiv.org). Seed the crawler only with reachable hosts; a blocked seed is a silent empty crawl otherwise.
