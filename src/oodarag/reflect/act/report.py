"""The one artefact of the whole loop a person actually reads.

Everything upstream of this module is invisible. A night's run is worth exactly
as much as the thirty seconds someone spends over coffee deciding whether to
trust it, which makes the report a safety mechanism rather than a formatting
concern: a change nobody noticed is indistinguishable from a change nobody
consented to.

So the layout is ordered by what the reader has to *do*, not by how the pipeline
ran. What already changed comes first, because that is the only part they cannot
undo by inaction and the only part where finding out late is expensive. What is
waiting on them comes second, with the accept/dismiss command spelled out in
full - a queue you have to look up the syntax for is a queue that never empties.
Observations come third, and what the loop learned about itself last - useful,
never urgent.

Two rules hold the whole thing to thirty seconds. **Empty sections are omitted
entirely**, so a quiet night is three lines and a busy one is long for a reason;
a fixed skeleton printing "None" four times teaches people to skim past the
headings, including on the night one of them is not empty. **Nothing is ever
dropped silently**: every skipped proposal, failed edit and policy refusal
appears somewhere, because a report that only lists successes is how an
autonomous process quietly stops working without anyone noticing.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from oodarag.reflect.models import CycleReport, Finding, Proposal, day_key
from oodarag.util.logging import get_logger

if TYPE_CHECKING:  # only for the annotation - see `_results_by_path`
    from oodarag.reflect.act.edits import ApplyReport

log = get_logger("reflect.report")

#: Short handle used in every user-facing command. Must match the queue's.
PREFIX_LEN = 8

#: How much of one night fits in a briefing. These are not correctness limits;
#: they are attention limits. A 4 MB diff pasted into a markdown file is not a
#: report, and the full text is always on disk in the backup and the queue.
MAX_EVIDENCE_PER_ITEM = 3
MAX_QUOTE_CHARS = 220
MAX_DIFF_LINES = 200
MAX_OBSERVATIONS_PER_RULE = 8
MAX_NOTES = 40

_UNSAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
_LATEST = "latest.md"


def render_markdown(
    report: CycleReport,
    apply_report: ApplyReport | None = None,
    decision_notes: list[str] | None = None,
    priors_explain: dict[str, dict[str, Any]] | None = None,
) -> str:
    """The nightly briefing, as GitHub-flavoured markdown."""
    notes = list(decision_notes or [])
    priors = dict(priors_explain or {})
    by_fingerprint = {p.fingerprint: p for p in report.proposals}
    results = _results_by_path(apply_report)

    queued_fps = set(report.queued)
    applied_fps = set(report.applied)
    applied = [by_fingerprint[fp] for fp in report.applied if fp in by_fingerprint]
    queued = [by_fingerprint[fp] for fp in report.queued if fp in by_fingerprint]
    # Proposals the loop meant to apply and did not: a dry run, or an edit whose
    # precondition had moved. Neither is "queued" and neither is "applied", so
    # without this they would appear in no section at all - and a dry run is the
    # default, which would make the default report the misleading one.
    intended = [
        p
        for p in report.proposals
        if p.fingerprint not in queued_fps and p.fingerprint not in applied_fps
    ]
    proposed = {p.finding.fingerprint for p in report.proposals}
    observations = [f for f in report.findings if f.fingerprint not in proposed]

    lines: list[str] = [
        f"# Nightly review - {day_key(report.started_at)}",
        "",
        _verdict(report),
    ]

    lines += _applied_section(report, applied + intended if report.dry_run else applied, results)
    lines += _queue_section(queued)
    lines += _observations_section(observations)
    lines += _learned_section(priors, notes)
    lines += _errors_section(report, apply_report, intended, results)

    return "\n".join(_tidy(lines)) + "\n"


def _tidy(lines: list[str]) -> list[str]:
    """Collapse the blank lines the sections leave between them.

    Each section is written to stand alone - it opens and closes with a blank
    line so it can be reordered or omitted without its neighbours knowing - which
    leaves double gaps at every seam. Markdown renders them identically; a person
    reading the raw file in a terminal, which is how most of these are read, does
    not.
    """
    out: list[str] = []
    for line in lines:
        if not line.strip() and (not out or not out[-1].strip()):
            continue
        out.append(line.rstrip())
    while out and not out[-1].strip():
        out.pop()
    return out


def render_json(
    report: CycleReport,
    apply_report: ApplyReport | None = None,
    decision_notes: list[str] | None = None,
    priors_explain: dict[str, dict[str, Any]] | None = None,
) -> str:
    """The same night, for something that is not a person.

    A superset of `CycleReport.to_json`: the extras (what the policy refused,
    what the loop believes about each rule, which files actually changed) are
    the parts a human reads in prose, and a machine consumer that has to
    re-derive them from the markdown would be parsing a layout that is allowed
    to change.
    """
    payload: dict[str, Any] = report.as_dict(include_detail=True)
    payload["decision_notes"] = list(decision_notes or [])
    payload["priors"] = dict(priors_explain or {})
    payload["changed_files"] = [
        {"path": path, "applied": bool(getattr(result, "applied", False)),
         "reason": str(getattr(result, "reason", "") or "")}
        for path, result in sorted(_results_by_path(apply_report).items())
    ]
    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)


def write_report(directory: str | Path, report: CycleReport, markdown: str) -> Path:
    """Write `<cycle_id>.md` and refresh `latest.md`, returning the cycle's path.

    `latest.md` is a copy rather than a symlink on purpose: symlinks do not
    survive a zip, a rsync without `-l`, a Windows checkout, or most editors'
    "save as", and this file is the one people wire into a launchd notification
    or an email body. A duplicated few kilobytes a night is a cheap price for a
    path that always resolves to text.

    Never raises. A report that cannot be written is logged and the intended
    path is returned anyway - the edits it describes have already happened, and
    losing the description must not also lose the run.
    """
    directory = Path(directory)
    target = directory / f"{_safe_name(report.cycle_id)}.md"
    try:
        directory.mkdir(parents=True, exist_ok=True)
        _atomic_write(target, markdown)
        _atomic_write(directory / _LATEST, markdown)
    except OSError as e:
        log.error("could not write report", path=str(target), err=str(e)[:200])
    return target


# -- sections ----------------------------------------------------------------


def _verdict(report: CycleReport) -> str:
    """One line that has to be worth reading on its own, because on most
    mornings it is the only line that gets read."""
    parts = [
        f"{report.signals} signals observed",
        f"{len(report.findings)} {_plural(len(report.findings), 'finding')}",
        f"{len(report.applied)} applied",
        f"{len(report.queued)} awaiting your call",
    ]
    line = ", ".join(parts) + "."
    if report.dry_run:
        line += " (Dry run - nothing was written. Re-run with `--apply`.)"
    return line


def _applied_section(
    report: CycleReport, applied: list[Proposal], results: dict[str, Any]
) -> list[str]:
    """What changed, first, because it is the only part inaction cannot undo.

    On a dry run this is the same list with the tense changed. It is not folded
    into the queue section: "the loop will do this by itself tomorrow night"
    and "the loop is waiting for you" are opposite states, and a report that
    renders them the same is a report that teaches people to ignore the first.
    """
    if not applied:
        return []
    heading = "## Applied" if not report.dry_run else "## Would apply (dry run)"
    lines = ["", heading, ""]
    for proposal in applied:
        lines += _proposal_header(proposal)
        for path in proposal.paths:
            lines += _diff_block(path, results.get(path))
        lines.append("")
    if not report.dry_run:
        lines += [f"Undo everything above with `ooda reflect revert {report.cycle_id}`.", ""]
    return lines


def _queue_section(queued: list[Proposal]) -> list[str]:
    if not queued:
        return []
    lines = ["", "## Awaiting your call", ""]
    for proposal in queued:
        short = proposal.fingerprint[:PREFIX_LEN]
        lines += _proposal_header(proposal)
        lines += _evidence_lines(proposal.finding)
        lines += [
            f"`ooda reflect accept {short}` to apply it, "
            f"`ooda reflect dismiss {short}` to never see it again.",
            "",
        ]
    return lines


def _observations_section(findings: list[Finding]) -> list[str]:
    """Findings nobody proposed a fix for. Grouped by rule and kept to one line
    each: they are context, and context that takes a paragraph is not read."""
    if not findings:
        return []
    by_rule: dict[str, list[Finding]] = {}
    for finding in findings:
        by_rule.setdefault(finding.rule_id or "unattributed", []).append(finding)

    lines = ["", "## Observations", ""]
    for rule_id in sorted(by_rule):
        group = sorted(by_rule[rule_id], key=lambda f: (-f.severity_rank, f.title))
        lines.append(f"**{rule_id}**")
        lines.append("")
        for finding in group[:MAX_OBSERVATIONS_PER_RULE]:
            where = f" - `{finding.targets[0]}`" if finding.targets else ""
            lines.append(f"- [{finding.severity}] {_one_line(finding.title, 120)}{where}")
        hidden = len(group) - MAX_OBSERVATIONS_PER_RULE
        if hidden > 0:
            lines.append(f"- ...and {hidden} more from this rule")
        lines.append("")
    return lines


def _learned_section(priors: dict[str, dict[str, Any]], notes: list[str]) -> list[str]:
    if not priors and not notes:
        return []
    lines = ["", "## What the loop learned", ""]
    if priors:
        lines += ["| rule | confidence | verdicts so far |", "| --- | --- | --- |"]
        for rule_id in sorted(priors):
            explain = priors.get(rule_id) or {}
            confidence = explain.get("confidence", 0.5)
            verdicts = explain.get("verdicts") or {}
            summary = ", ".join(f"{k} {v}" for k, v in sorted(verdicts.items())) or "no history yet"
            lines.append(f"| `{rule_id}` | {_as_float(confidence, 0.5):.2f} | {summary} |")
        lines.append("")
    if notes:
        # The policy's refusals live here rather than under Errors: nothing went
        # wrong, the loop declined on purpose, and the user is owed the reason.
        lines.append("Decisions taken tonight:")
        lines.append("")
        for note in notes[:MAX_NOTES]:
            lines.append(f"- {_one_line(str(note), 300)}")
        if len(notes) > MAX_NOTES:
            lines.append(f"- ...and {len(notes) - MAX_NOTES} more")
        lines.append("")
    return lines


def _errors_section(
    report: CycleReport,
    apply_report: ApplyReport | None,
    intended: list[Proposal],
    results: dict[str, Any],
) -> list[str]:
    """Everything that went wrong, including the parts nothing else claims.

    An edit the actuator declined is reported against its *proposal* rather than
    only against its path, because "anchor no longer present" tells the user
    nothing without the suggestion it belonged to.
    """
    problems = [str(e) for e in report.errors]
    covered: set[str] = set()
    if not report.dry_run:
        for proposal in intended:
            covered.update(proposal.paths)
            reason = next(
                (
                    str(getattr(results.get(path), "reason", "") or "")
                    for path in proposal.paths
                    if not getattr(results.get(path), "applied", False)
                    and getattr(results.get(path), "reason", "")
                ),
                "no result was recorded for it",
            )
            problems.append(
                f"`{proposal.fingerprint[:PREFIX_LEN]}` {_one_line(proposal.title, 120)} "
                f"did not apply: {reason}"
            )
    for result in _results(apply_report):
        if getattr(result, "applied", False):
            continue
        path = str(getattr(result, "path", "") or "")
        reason = str(getattr(result, "reason", "") or "")
        # A dry run is not a failure, and neither is a path already explained
        # above by the proposal it belongs to.
        if path in covered or reason.strip().lower() == "dry run":
            continue
        problems.append(f"`{path or '?'}`: {reason or 'edit did not apply'}")
    if not problems:
        return []
    lines = ["", "## Errors", ""]
    for problem in problems[:MAX_NOTES]:
        lines.append(f"- {_one_line(problem, 300)}")
    if len(problems) > MAX_NOTES:
        lines.append(f"- ...and {len(problems) - MAX_NOTES} more")
    lines.append("")
    return lines


# -- pieces ------------------------------------------------------------------


def _proposal_header(proposal: Proposal) -> list[str]:
    short = proposal.fingerprint[:PREFIX_LEN]
    where = ", ".join(f"`{p}`" for p in proposal.paths) or "no files"
    lines = [f"### {_one_line(proposal.title, 140)}", ""]
    lines.append(
        f"`{short}` - {proposal.finding.rule_id or 'unattributed'} - "
        f"risk {proposal.risk} - score {proposal.score:.2f} - {where}"
    )
    lines.append("")
    rationale = _one_line(proposal.rationale or proposal.finding.detail, 400)
    if rationale:
        lines += [rationale, ""]
    return lines


def _evidence_lines(finding: Finding) -> list[str]:
    """The quotes behind a finding, verbatim.

    These are what make the queue reviewable in a glance instead of on trust:
    the user recognises their own words far faster than they can evaluate a
    rule's reasoning about them.
    """
    if not finding.evidence:
        return []
    lines: list[str] = []
    for item in finding.evidence[:MAX_EVIDENCE_PER_ITEM]:
        quote = _one_line(getattr(item, "quote", "") or "", MAX_QUOTE_CHARS)
        if not quote:
            continue
        where = getattr(item, "uri", "") or getattr(item, "source", "")
        suffix = f" - {_one_line(str(where), 80)}" if where else ""
        lines.append(f"> {quote}{suffix}")
        lines.append(">")
    if lines:
        lines.pop()  # the trailing blockquote spacer
        lines.append("")
    hidden = len(finding.evidence) - MAX_EVIDENCE_PER_ITEM
    if hidden > 0:
        lines += [f"...and {hidden} more like it.", ""]
    return lines


def _diff_block(path: str, result: Any) -> list[str]:
    """One file's change, folded away.

    Collapsed because the diff is the thing you want present but not in the way:
    the header line already says which file changed, and a briefing whose first
    screen is a patch is a briefing that gets closed.
    """
    diff = _diff_text(result)
    if not diff:
        return [f"- `{path}` (no diff recorded)", ""]
    body, truncated = _clip_lines(diff, MAX_DIFF_LINES)
    fence = _fence_for(body)
    lines = [
        f"<details><summary><code>{path}</code></summary>",
        "",
        f"{fence}diff",
        body,
        fence,
        "",
    ]
    if truncated:
        lines += [f"_Diff truncated at {MAX_DIFF_LINES} lines._", ""]
    lines.append("</details>")
    lines.append("")
    return lines


# -- helpers -----------------------------------------------------------------


def _results(apply_report: ApplyReport | None) -> list[Any]:
    """The per-file results, or nothing.

    Read through `getattr` rather than a typed field because the report is the
    last stage of the night: if `act.edits` grows or renames something, the cost
    should be a missing diff in one section, not a traceback that costs the user
    the whole briefing for edits that have already been made.
    """
    if apply_report is None:
        return []
    results = getattr(apply_report, "results", None)
    return list(results) if isinstance(results, (list, tuple)) else []


def _results_by_path(apply_report: ApplyReport | None) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for result in _results(apply_report):
        path = str(getattr(result, "path", "") or "")
        if path:
            out[path] = result
    return out


def _diff_text(result: Any) -> str:
    for attr in ("diff", "patch", "unified_diff"):
        value = getattr(result, attr, "")
        if isinstance(value, str) and value.strip():
            return value.replace("\r\n", "\n").rstrip("\n")
    return ""


def _clip_lines(text: str, limit: int) -> tuple[str, bool]:
    lines = text.split("\n")
    if len(lines) <= limit:
        return text, False
    return "\n".join(lines[:limit]), True


def _fence_for(text: str) -> str:
    """A code fence longer than the longest backtick run inside the text.

    Diffs of markdown files contain fences of their own, and a three-backtick
    fence around them closes early - which in a report about editing markdown is
    the common case, not the exotic one.
    """
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def _one_line(text: str, limit: int) -> str:
    flat = " ".join(str(text or "").split())
    if len(flat) <= limit:
        return flat
    return flat[: max(0, limit - 3)].rstrip() + "..."


def _plural(count: int, word: str) -> str:
    return word if count == 1 else word + "s"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_name(cycle_id: str) -> str:
    """A cycle id is a timestamp, but it reaches here as a string from the
    journal and ends up as a filename; a stray separator would write outside
    the reports directory."""
    cleaned = _UNSAFE_NAME_RE.sub("-", str(cycle_id or "")).strip("-.")
    return cleaned or time.strftime("%Y%m%d-%H%M%S")


def _atomic_write(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
