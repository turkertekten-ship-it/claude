"""Failure modes, named.

Every error here is something a user can fix. Anything that is not one of
these is a bug in the workbench and should surface with its traceback intact
rather than being flattened into a friendly message.
"""


class WorkbenchError(Exception):
    """Base class for every error this package raises on purpose."""


class SpecError(WorkbenchError):
    """A suite file is malformed, incomplete, or self-contradictory."""


class RenderError(WorkbenchError):
    """A template referenced a variable that was not supplied."""


class BackendError(WorkbenchError):
    """The execution backend could not produce a completion."""


class BackendUnavailable(BackendError):
    """The requested backend cannot run in this environment at all."""


class GraderError(WorkbenchError):
    """A grader was configured in a way it cannot honour."""
