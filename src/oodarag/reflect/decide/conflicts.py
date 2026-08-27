"""Deciding which proposals may touch the same file on the same night.

Ranking says what is worth doing and gating says what is allowed; this says what
can be done *together*. Two rules can independently conclude the same file needs
to exist - a repeated instruction and a correction both wanting to start a
memory file - and nothing upstream stops them, because neither rule can see the
other.

Left alone, the collision resolves itself in the worst possible place: inside
the actuator, where the second `create` finds the file already there, fails its
precondition, and the finding behind it disappears for the night with nothing
said about it anywhere. Silent loss is the failure the nightly report exists to
prevent, so the collision is settled here instead, in the open and with a
reason attached.
"""

from __future__ import annotations

from oodarag.reflect.models import Proposal

#: Edit operations that cannot share a file with another proposal in one cycle.
#: `create` because the second one finds the file already there; `replace`
#: because the first one may have moved the text the second is anchored to.
#: `append` and `ensure_section` are additive and idempotent, so several rules
#: may contribute to one file in one night without stepping on each other.
EXCLUSIVE_OPS = frozenset({"create", "replace"})


def resolve_edit_conflicts(proposals: list[Proposal]) -> tuple[list[Proposal], list[str]]:
    """Keep one proposal per contended file, defer the rest with a stated reason.

    Deferring costs nothing, which is what makes this the right resolution
    rather than a compromise: once the winner has run, the file exists, so
    tomorrow the same finding proposes an `ensure_section` against it and
    applies cleanly. Nothing is lost but a day, and the report says so.

    `proposals` must already be in the order the loop intends to apply them -
    the first claimant of a contended path wins, and the loop hands them over in
    descending score order.
    """
    claimed: dict[str, Proposal] = {}
    kept: list[Proposal] = []
    notes: list[str] = []

    for proposal in proposals:
        exclusive_here = {edit.path for edit in proposal.edits if edit.op in EXCLUSIVE_OPS}
        blocking = next(
            (
                path
                for path in proposal.paths
                if path in claimed
                and (
                    path in exclusive_here
                    or any(
                        edit.op in EXCLUSIVE_OPS and edit.path == path
                        for edit in claimed[path].edits
                    )
                )
            ),
            None,
        )
        if blocking is not None:
            winner = claimed[blocking]
            notes.append(
                f"deferred {proposal.fingerprint[:8]} ({proposal.finding.rule_id}): "
                f"{blocking} is already being created or rewritten this cycle by "
                f"{winner.fingerprint[:8]} ({winner.finding.rule_id}); it will apply "
                f"cleanly against the existing file next run"
            )
            continue
        kept.append(proposal)
        for path in proposal.paths:
            claimed.setdefault(path, proposal)

    return kept, notes
