"""Reports that say how much of the result is a judgement call.

A single pass rate hides the thing a reader most needs: whether the number
came from a regex or from a model's opinion. So every table here splits
verdicts by grader kind, and the blind section leads with the position-bias
rate -- because if swapping the presentation order flips most verdicts, the
comparison below it is not a measurement and should not be read as one.
"""

from __future__ import annotations

import json
from typing import Any, Sequence

from .blind import PairJudgement, position_bias_rate
from .graders import DETERMINISTIC, ENVIRONMENTAL, MODEL
from .runner import CaseRun, RunResult
from .stats import bradley_terry, paired_table, summarise_pairwise, wilson_interval


def _pct(numerator: float, denominator: float) -> str:
    return f"{100 * numerator / denominator:.0f}%" if denominator else "n/a"


def variant_rollup(result: RunResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for vid in result.variant_ids:
        runs = result.by_variant(vid)
        passed = sum(1 for r in runs if r.passed)
        interval = wilson_interval(passed, len(runs))
        kinds = {DETERMINISTIC: [0, 0], ENVIRONMENTAL: [0, 0], MODEL: [0, 0]}
        for run in runs:
            for verdict in run.verdicts:
                if verdict.advisory:
                    continue
                bucket = kinds.setdefault(verdict.kind, [0, 0])
                bucket[1] += 1
                bucket[0] += 1 if verdict.passed else 0
        rows.append({
            "variant": vid,
            "runs": len(runs),
            "passed": passed,
            "pass_rate": passed / len(runs) if runs else 0.0,
            "ci95": str(interval),
            "mean_score": sum(r.score for r in runs) / len(runs) if runs else 0.0,
            "cost_usd": sum(r.cost_usd for r in runs),
            "by_kind": {k: v for k, v in kinds.items() if v[1]},
        })
    return rows


def failing_verdicts(result: RunResult, limit: int = 25) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for run in result.runs:
        for verdict in run.verdicts:
            if verdict.passed or verdict.advisory:
                continue
            rows.append({
                "variant": run.variant_id, "case": run.case_id,
                "grader": verdict.grader, "kind": verdict.kind,
                "detail": verdict.detail.replace("\n", " ")[:220],
            })
            if len(rows) >= limit:
                return rows
    return rows


def pairwise_tables(judgements: Sequence[PairJudgement]) -> list[dict[str, Any]]:
    pairs: dict[tuple[str, str], list[str]] = {}
    for j in judgements:
        key = (j.left, j.right)
        pairs.setdefault(key, []).append(j.winner)
    return [summarise_pairwise(outcomes, a, b) for (a, b), outcomes in pairs.items()]


def markdown(result: RunResult) -> str:
    """Render a full run as a report a person can act on."""
    out: list[str] = []
    add = out.append

    add(f"# Workbench run — {result.suite}")
    add("")
    add(f"- Run id: `{result.run_id}`")
    add(f"- Backend: `{result.backend}`")
    add(f"- Started: {result.started_at} (took {result.duration_s:.1f}s)")
    add(f"- Total cost: **${result.cost_usd:.4f}** (backend-reported, not estimated)")
    add("")

    add("## Pass rate by variant")
    add("")
    add("| Variant | Runs | Passed | Rate | 95% CI | Mean score | Cost |")
    add("|---|---:|---:|---:|---|---:|---:|")
    rows = variant_rollup(result)
    for row in rows:
        add(f"| `{row['variant']}` | {row['runs']} | {row['passed']} | "
            f"{100 * row['pass_rate']:.0f}% | {row['ci95']} | "
            f"{row['mean_score']:.2f} | ${row['cost_usd']:.4f} |")
    add("")
    add("The interval is a Wilson score interval. On a suite this small it is "
        "wide on purpose: it is the honest width, not a defect in the report.")
    add("")

    add("## Where the verdicts came from")
    add("")
    add("| Variant | Deterministic | Environmental | Model-judged |")
    add("|---|---|---|---|")
    for row in rows:
        cells = []
        for kind in (DETERMINISTIC, ENVIRONMENTAL, MODEL):
            bucket = row["by_kind"].get(kind)
            cells.append(f"{bucket[0]}/{bucket[1]} ({_pct(bucket[0], bucket[1])})"
                         if bucket else "—")
        add(f"| `{row['variant']}` | " + " | ".join(cells) + " |")
    add("")
    add("A result carried by the deterministic column is evidence. One carried "
        "by the model column is a second opinion, and should be read as one.")
    add("")

    failures = failing_verdicts(result)
    if failures:
        add("## Failing checks")
        add("")
        add("| Variant | Case | Grader | Kind | Detail |")
        add("|---|---|---|---|---|")
        for f in failures:
            detail = f["detail"].replace("|", "\\|")
            add(f"| `{f['variant']}` | `{f['case']}` | {f['grader']} | "
                f"{f['kind']} | {detail} |")
        add("")

    # Paired case-by-case comparison: every variant answered the same cases, so
    # two independent pass rates is the wrong comparison to make.
    variants = result.variant_ids
    if len(variants) == 2:
        a, b = variants
        a_results = {r.case_id: r.passed for r in result.by_variant(a) if r.repeat == 0}
        b_results = {r.case_id: r.passed for r in result.by_variant(b) if r.repeat == 0}
        table = paired_table(a_results, b_results)
        add("## Paired outcome comparison (McNemar, exact)")
        add("")
        add(f"| | `{b}` passed | `{b}` failed |")
        add("|---|---:|---:|")
        add(f"| **`{a}` passed** | {table['both_pass']} | {table['a_only']} |")
        add(f"| **`{a}` failed** | {table['b_only']} | {table['both_fail']} |")
        add("")
        add(f"Discordant cases: **{table['discordant']}** of {table['cases']}. "
            f"p = {table['p_value_exact']} "
            f"({'significant' if table['significant_at_0.05'] else 'not significant'} "
            f"at 0.05).")
        add("")
        add(f"{table['note'].capitalize()}. Cases both variants passed, or both "
            f"failed, carry no information about which is better — only the "
            f"off-diagonal cells do.")
        add("")

    if result.controls:
        add("## Blinding control")
        add("")
        for control in result.controls:
            mark = "PASS" if control["passed"] else "**FAIL**"
            add(f"- {mark} — {control['control']}: {control['detail']}")
        add("")
        add("The control shows the judge one answer twice, as both candidates. "
            "A judge with nothing to distinguish them must return a tie; if it "
            "picks a winner, it is reading position or residual identity rather "
            "than content.")
        add("")
        if any(not c["passed"] for c in result.controls):
            add("> **The blinding control failed. Every comparison below is "
                "unsafe to quote.** Fix the leak or change the judge before "
                "reading anything into the win rates.")
            add("")

    if result.lengths:
        add("## Output length by variant")
        add("")
        add("| Variant | Mean output characters |")
        add("|---|---:|")
        for vid, chars in result.lengths.items():
            add(f"| `{vid}` | {chars} |")
        add("")
        add("Judges are measured to prefer longer answers regardless of "
            "content, so a win rate should be read next to this table. If the "
            "winner is also consistently the longest, length is a live "
            "confound and the criterion needs to rule it out explicitly.")
        add("")

    if result.judgements:
        bias = position_bias_rate(result.judgements)
        errors = sum(1 for j in result.judgements if j.winner == "ERROR")
        add("## Blind pairwise comparison")
        add("")
        if errors:
            add(f"- Unreadable judge verdicts: **{errors}** — recorded as "
                f"errors, not silently counted as ties.")
        add(f"- Pairs judged: **{len(result.judgements)}**, each in both "
            f"presentation orders ({2 * len(result.judgements)} judge calls).")
        add(f"- Order-disagreement rate: **{100 * bias:.0f}%** — pairs where "
            f"swapping which candidate came first changed the verdict. Those "
            f"are recorded as ties.")
        total_redactions = sum(j.redactions for j in result.judgements)
        add(f"- Identity strings redacted before judging: **{total_redactions}**.")
        if bias > 0.4:
            add("")
            add("> **The judge is reading position, not content.** With "
                "disagreement this high the comparison below does not support "
                "a conclusion. Sharpen the criterion or use a stronger judge "
                "model before quoting these numbers.")
        add("")
        add("| A | B | A wins | B wins | Ties | Win rate (excl. ties) | 95% CI | p | Significant |")
        add("|---|---|---:|---:|---:|---:|---|---:|---|")
        for table in pairwise_tables(result.judgements):
            rate = table["win_rate_a_excluding_ties"]
            add(f"| `{table['a']}` | `{table['b']}` | {table['wins_a']} | "
                f"{table['wins_b']} | {table['ties']} | "
                f"{'—' if rate is None else f'{100 * rate:.0f}%'} | "
                f"{table['ci95_win_rate_a']} | {table['p_value_sign_test']} | "
                f"{'yes' if table['significant_at_0.05'] else 'no'} |")
        add("")
        decided = sum(t["decided"] for t in pairwise_tables(result.judgements))
        needed = pairwise_tables(result.judgements)[0]["pairs_needed_for_70pct_effect"]
        add(f"p is a two-sided exact sign test over non-tied pairs. This run "
            f"decided {decided} pair(s); detecting a genuine 70/30 preference "
            f"at 80% power needs roughly {needed}. Treat anything short of "
            f"that as directional, not settled.")
        add("")

        wins = [(j.winner, j.left if j.winner == j.right else j.right)
                for j in result.judgements if j.winner != "TIE"]
        if len({w for w, _ in wins}) > 1:
            strengths = bradley_terry([(w, loser) for w, loser in wins])
            add("### Bradley-Terry strengths")
            add("")
            add("| Variant | Strength |")
            add("|---|---:|")
            for variant, strength in strengths.items():
                add(f"| `{variant}` | {strength:.3f} |")
            add("")
            add("Strengths are shares summing to 1, fitted from pairwise "
                "outcomes so that variants facing different opponents remain "
                "comparable.")
            add("")

    if result.notes:
        add("## Notes")
        add("")
        for note in result.notes:
            add(f"- {note}")
        add("")

    add("## What this run did not establish")
    add("")
    add("- Sampling parameters were not varied: `temperature`, `top_p` and "
        "`top_k` are deprecated on current models and rejected outright on the "
        "newest ones, so there is no sweep to run.")
    if not result.judgements:
        add("- No blind comparison was run, so nothing here ranks the variants "
            "against each other; the pass rates are independent measurements.")
    add("- Pass rates measure the graders that were written, not correctness "
        "in general. A case with no grader for a failure mode cannot detect it.")
    if result.judgements:
        add("- The judge was not validated against human labels on this task. "
            "Published agreement between a strong judge and human experts is "
            "around 85% with ties excluded, against 81% between humans — so a "
            "judge verdict is a second opinion of roughly human quality, not a "
            "ground truth.")
    return "\n".join(out)


def to_json(result: RunResult) -> str:
    return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)
