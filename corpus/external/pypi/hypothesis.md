---
date: 2026-08-16T22:54:18+0000
source: https://pypi.org/project/hypothesis/
---
# Hypothesis

- Website
- Documentation
- Source code
- Contributing
- Community

Hypothesis is the property-based testing library for Python. With Hypothesis, you write tests which should pass for all inputs in whatever range you describe, and let Hypothesis randomly choose which of those inputs to check - including edge cases you might not have thought about. For example:

```
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_matches_builtin(ls):
    assert sorted(ls) == my_sort(ls)
```

This randomized testing can catch bugs and edge cases that you didn't think of and wouldn't have found. In addition, when Hypothesis does find a bug, it doesn't just report any failing test case — it reports the simplest possible one. This makes property-based tests a powerful tool for debugging, as well as testing.

For instance,

```
def my_sort(ls):
    return sorted(set(ls))
```

fails with the simplest possible failing test case:

```
Failing test case: test_matches_builtin(ls=[0, 0])
```

### Installation

To install Hypothesis:

```
pip install hypothesis
```

There are also optional extras available.
