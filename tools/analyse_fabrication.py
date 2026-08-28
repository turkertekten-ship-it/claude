#!/usr/bin/env python3
"""Pre-specified analysis for the powered fabrication test.

Written and committed BEFORE the run it analyses, because the alternative is
choosing the test after seeing which one gives the answer you wanted. Six
previous runs on this question came back small-or-absent; the temptation to go
looking for a slice where it did not is exactly what a pre-registered analysis
exists to remove.

**The estimand.** For each case and each arm, the fabrication rate over K
samples. For each case, the paired difference between arms. The headline is the
mean of those differences, negative meaning the operating prompt fabricated
less.

**Why paired.** Both arms answer the same forty traps, so the case is the unit
and its difficulty cancels. Published work calls the correlation between arms a
free variance reduction, roughly a third at rho = 0.5.

**Why repeated.** A single sample per case gives a binary outcome and a minimum
detectable effect around 13%; three samples give a rate per case and a
materially tighter one. That is the whole reason this run costs what it does.

**Why clustered.** The forty cases sit in six families, and cases in a family
are variations on one trap rather than independent draws. Ignoring that inflates
significance -- measured elsewhere at up to 3x too narrow. So the standard error
is cluster-robust by family, and the bootstrap resamples families, not cases.

Reported either way, and the confidence interval is the answer whether or not
it excludes zero.

Usage: python3 tools/analyse_fabrication.py .workbench/<run-id>
"""

from __future__ import annotations

import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

DOCTRINE, PLAIN = "full-doctrine", "plain-assistant"


def family_of(case_id: str) -> str:
    """`h-spec-02` and `spec-02` are the same family: the h- prefix is a stratum."""
    return case_id.removeprefix("h-").rsplit("-", 1)[0]


def stratum_of(note: str) -> str:
    return "heldout" if "stratum:heldout" in note else "tuned"


def attrition_check(payload: dict, threshold: float = 0.10) -> str:
    """Warn if the arms did not answer at comparable rates. Empty when fine.

    Imported from the workbench rather than reimplemented, so the analysis and
    the runner cannot drift into disagreeing about what counts as an answer.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from workbench.validity import AnswerRates, unanswered
    except ImportError:                                   # pragma: no cover
        return ""
    counts: dict[str, list[int]] = {}
    for run in payload.get("runs", []):
        slot = counts.setdefault(run["variant_id"], [0, 0])
        slot[1] += 1
        if unanswered(run.get("output") or ""):
            slot[0] += 1
    rates = AnswerRates({v: (u, t) for v, (u, t) in counts.items()}, threshold)
    if rates.passed:
        return ""
    return ("THIS RUN IS NOT A VALID COMPARISON.\n\n" + rates.detail +
            "\n\nThe numbers below are printed because refusing to print them "
            "would hide\nthe evidence, not because they mean anything. Do not "
            "quote them.")


def strata_for(payload: dict, case_ids) -> dict[str, str]:
    """Label each case tuned or heldout, and never guess silently.

    An adversarial review found this was broken from the first run. The notes
    came from `payload["cases"]`, `RunResult.to_dict()` never wrote that key,
    so the mapping was empty for every run this workbench could produce. The
    fallback then passed the bare case id to `stratum_of`, which returns
    "tuned" for anything not containing "stratum:heldout" -- so all 40 cases
    were labelled tuned, the held-out block never printed, and the "stratum:
    tuned" section reproduced the ALL CASES numbers exactly. The pre-registered
    held-out check had not run once, and nothing said so.

    The lesson is not the missing key. It is that the fallback was a plausible
    answer instead of an admission, so a broken stratification looked exactly
    like a stratification where every case happened to be tuned.

    Two sources now, in order, and the second is announced rather than assumed:

    1. `payload["cases"]` notes, when the run recorded them.
    2. Failing that, the `h-` id prefix, which `family_of` already documents as
       marking the held-out stratum. Runs written before the fix have no notes,
       and this recovers them rather than discarding the experiment.

    If neither yields both strata, the caller is told the stratification is
    unavailable and no stratum block is printed at all.
    """
    notes = {c["id"]: c.get("note", "") for c in payload.get("cases", []) or []}
    if notes:
        return {cid: stratum_of(notes.get(cid, "")) for cid in case_ids}
    return {cid: ("heldout" if cid.startswith("h-") else "tuned") for cid in case_ids}


def load(run_dir: Path) -> tuple[dict, dict, dict]:
    """Return (rates, families, strata) keyed by case id then arm."""
    payload = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    fabricated: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for run in payload["runs"]:
        # A run the backend never answered is excluded, not scored as a failure.
        completion = run.get("completion") or {}
        if completion.get("error") or not (run.get("output") or "").strip():
            continue
        blocking = [v for v in run["verdicts"] if not v["advisory"]]
        if not blocking:
            continue
        fabricated[run["case_id"]][run["variant_id"]].append(
            0 if all(v["passed"] for v in blocking) else 1)

    rates, families = {}, {}
    for case_id, arms in fabricated.items():
        if DOCTRINE not in arms or PLAIN not in arms:
            continue
        rates[case_id] = {a: sum(v) / len(v) for a, v in arms.items()}
        families[case_id] = family_of(case_id)
    strata = strata_for(payload, rates)
    return rates, families, strata


def clustered_se(diffs: dict[str, float], families: dict[str, str]) -> float:
    """Cluster-robust standard error of the mean, clustering by family."""
    n = len(diffs)
    if n < 2:
        return float("nan")
    mean = sum(diffs.values()) / n
    by_family: dict[str, float] = defaultdict(float)
    for case_id, d in diffs.items():
        by_family[families[case_id]] += d - mean
    return math.sqrt(sum(v * v for v in by_family.values())) / n


def naive_se(diffs: dict[str, float]) -> float:
    n = len(diffs)
    if n < 2:
        return float("nan")
    mean = sum(diffs.values()) / n
    var = sum((d - mean) ** 2 for d in diffs.values()) / (n - 1)
    return math.sqrt(var / n)


def cluster_bootstrap(diffs: dict[str, float], families: dict[str, str],
                      iterations: int = 10000, seed: int = 0) -> tuple[float, float]:
    """Percentile CI, resampling FAMILIES so the clustering is respected."""
    groups: dict[str, list[float]] = defaultdict(list)
    for case_id, d in diffs.items():
        groups[families[case_id]].append(d)
    keys = list(groups)
    rng = random.Random(seed)
    means = []
    for _ in range(iterations):
        drawn: list[float] = []
        for _ in range(len(keys)):
            drawn.extend(groups[keys[rng.randrange(len(keys))]])
        means.append(sum(drawn) / len(drawn))
    means.sort()
    return means[int(0.025 * iterations)], means[int(0.975 * iterations)]


def sign_test(pos: int, neg: int) -> float:
    n = pos + neg
    if n == 0:
        return 1.0
    obs = max(pos, neg)
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(obs, n + 1)) / 2 ** n)


def report(rates, families, strata, label: str, keep=None) -> dict:
    chosen = {c: r for c, r in rates.items() if keep is None or keep(c)}
    if not chosen:
        return {}
    diffs = {c: r[DOCTRINE] - r[PLAIN] for c, r in chosen.items()}
    fams = {c: families[c] for c in chosen}
    mean = sum(diffs.values()) / len(diffs)
    cse, nse = clustered_se(diffs, fams), naive_se(diffs)
    lo, hi = cluster_bootstrap(diffs, fams)
    better = sum(1 for d in diffs.values() if d < 0)
    worse = sum(1 for d in diffs.values() if d > 0)
    same = sum(1 for d in diffs.values() if d == 0)
    p = sign_test(better, worse)

    d_rate = sum(r[DOCTRINE] for r in chosen.values()) / len(chosen)
    p_rate = sum(r[PLAIN] for r in chosen.values()) / len(chosen)

    print(f"\n{label}  ({len(chosen)} cases, {len(set(fams.values()))} families)")
    print("-" * 72)
    print(f"  fabrication rate   doctrine {d_rate:6.1%}   plain {p_rate:6.1%}")
    print(f"  mean paired diff   {mean:+.4f}   (negative = doctrine fabricates less)")
    print(f"  95% CI (clustered bootstrap over families)   [{lo:+.4f}, {hi:+.4f}]")
    inflation = f"   inflation {cse / nse:.2f}x" if nse else ""
    print(f"  clustered SE {cse:.4f}   naive SE {nse:.4f}{inflation}")
    print(f"  cases better {better}, worse {worse}, tied {same}   sign test p = {p:.4f}")
    excludes = (lo < 0 and hi < 0) or (lo > 0 and hi > 0)
    print(f"  -> {'SIGNIFICANT: interval excludes zero' if excludes else 'not significant: the interval spans zero'}")
    return {"label": label, "n": len(chosen), "mean_diff": mean,
            "ci": [lo, hi], "clustered_se": cse, "naive_se": nse,
            "better": better, "worse": worse, "tied": same, "p": p,
            "doctrine_rate": d_rate, "plain_rate": p_rate, "significant": excludes}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    run_dir = Path(argv[1])
    if not (run_dir / "result.json").is_file():
        print(f"no result.json in {run_dir}", file=sys.stderr)
        return 2

    rates, families, strata = load(run_dir)
    if not rates:
        print("no paired cases found", file=sys.stderr)
        return 2

    print("Powered fabrication test — pre-specified analysis")
    print("=" * 72)
    print("Estimand: mean paired difference in per-case fabrication rate.")
    print("Negative favours the operating prompt. Clustered by trap family.")

    # Before any number: did both arms answer? A paired comparison where one
    # arm produced no answer in a large share of runs is not a weak result, it
    # is not a result. This is printed first and loudly, because the numbers
    # below are computed either way and look exactly like a finding.
    payload = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
    verdict = attrition_check(payload)
    if verdict:
        print()
        print("!" * 72)
        print(verdict)
        print("!" * 72)

    results = [report(rates, families, strata, "ALL CASES")]
    present = sorted(set(strata.values()))
    if len(present) < 2:
        print()
        print("STRATIFICATION UNAVAILABLE — every case labelled "
              f"{present[0] if present else 'nothing'!r}.")
        print("No stratum block is printed, because one stratum containing all")
        print("the cases is not a stratified analysis. It reproduces the ALL")
        print("CASES numbers exactly and reads like a second, agreeing result.")
        print()
    else:
        for name in ("tuned", "heldout"):
            results.append(report(rates, families, strata, f"stratum: {name}",
                                  keep=lambda c, n=name: strata[c] == n))

    print("\n" + "=" * 72)
    head = results[0]
    print("The interval is the answer. A CI spanning zero at this sample size")
    print("means the effect, if any, is smaller than this experiment can see —")
    print("which is a result about the prompt AND about the experiment, and the")
    print("width says which.")
    return 0 if head else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
