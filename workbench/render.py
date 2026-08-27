"""``{{variable}}`` templating, deliberately strict.

The Console Workbench fills ``{{placeholders}}`` from a variables panel. The
same idea, with one rule added: an unfilled placeholder is an error, not an
empty string. Silently rendering ``{{expected_answer}}`` to nothing produces a
prompt that still looks plausible and evaluates to nonsense, which is exactly
the class of mistake an eval harness exists to catch.
"""

from __future__ import annotations

import re
from typing import Iterable, Mapping

from .errors import RenderError

#: ``{{ name }}`` -- letters, digits, underscore, dot and dash inside.
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_.\-]*)\s*\}\}")


def variables_in(template: str) -> list[str]:
    """Return the placeholder names used in ``template``, in first-use order."""
    seen: list[str] = []
    for match in PLACEHOLDER.finditer(template):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def render(template: str, variables: Mapping[str, object]) -> str:
    """Substitute ``{{name}}`` from ``variables``.

    Raises :class:`RenderError` naming *every* missing placeholder at once,
    rather than stopping at the first -- a suite with four unbound variables
    should take one run to diagnose, not four.
    """
    missing = [name for name in variables_in(template) if name not in variables]
    if missing:
        raise RenderError(
            "template references undefined variable(s): "
            + ", ".join(sorted(missing))
            + ". Define them under the case's `vars:` or the suite's `vars:`."
        )

    def substitute(match: re.Match[str]) -> str:
        return str(variables[match.group(1)])

    return PLACEHOLDER.sub(substitute, template)


def render_all(templates: Iterable[str], variables: Mapping[str, object]) -> list[str]:
    """Render several templates against one variable set."""
    return [render(t, variables) for t in templates]
