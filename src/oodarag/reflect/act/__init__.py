"""Everything that changes state: file edits, the review queue, the report."""

from oodarag.reflect.act.edits import ApplyReport, EditApplier, EditResult
from oodarag.reflect.act.queue import ReviewQueue, proposal_from_dict
from oodarag.reflect.act.report import render_json, render_markdown, write_report

__all__ = [
    "ApplyReport",
    "EditApplier",
    "EditResult",
    "ReviewQueue",
    "proposal_from_dict",
    "render_json",
    "render_markdown",
    "write_report",
]
