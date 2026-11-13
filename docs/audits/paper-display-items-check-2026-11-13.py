"""Recount Figure 3 and C56 without using their plotting/assessment routines."""

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "models/haze_world/figures"
PAPER = ROOT / "models/haze_world/paper"
INPUTS = []


def read(path):
    INPUTS.append(path)
    with path.open() as handle:
        return list(csv.DictReader(handle))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    states = read(FIG / "continuum_habitats/c0_local_gain.csv")
    states += read(FIG / "continuum_habitats/c1_resolved.csv")
    states = [r for r in states if r["gain_status"] == "defined"]
    exact = [r for r in states if abs(float(r["Sc"])) < 1e-6]
    ordinary = [r for r in states if abs(float(r["Sc"])) >= 1e-6 and float(r["S0"]) < 0]
    excluded = [r for r in states if abs(float(r["Sc"])) >= 1e-6 and float(r["S0"]) > 0]
    counts = dict(total=len(states), exact=len(exact), ordinary_graded=len(ordinary),
                  excluded_graded=len(excluded),
                  exact_finite=sum(r["critical_lag_status"] == "finite_crossing" for r in exact),
                  graded_finite=sum(r["critical_lag_status"] == "finite_crossing" for r in ordinary),
                  graded_lower_bounds=sum(r["critical_lag_status"].startswith("not_detected") for r in ordinary))
    assert counts == dict(total=170, exact=42, ordinary_graded=122, excluded_graded=6,
                          exact_finite=36, graded_finite=9, graded_lower_bounds=113)
    plotted = read(PAPER / "figures/data/fig3_states.csv")
    assert len(plotted) == len(exact) + len(ordinary)
    assert sum(r["group"] == "exact_bridge_unstable" for r in plotted) == 6
    assert sum(r["tau_status"] == "censored_at_1e4" for r in plotted) == 113

    dials = read(FIG / "graded_dials/dials.csv")
    reported = {r["branch"]: r for r in read(PAPER / "esm/s5_power_law_fits.csv")}
    fits = []
    for branch in sorted({r["branch_id"] for r in dials}):
        chosen = [r for r in dials if r["branch_id"] == branch and
                  r["critical_lag_status"] == "finite_crossing" and
                  2 < float(r["critical_lag_yr"]) < 1000 and abs(float(r["Sc"])) > 0]
        x = [math.log(abs(float(r["Sc"]))) for r in chosen]
        y = [math.log(float(r["critical_lag_yr"])) for r in chosen]
        xbar, ybar = sum(x) / len(x), sum(y) / len(y)
        slope = sum((a - xbar) * (b - ybar) for a, b in zip(x, y)) / sum((a - xbar)**2 for a in x)
        intercept = ybar - slope * xbar
        r_squared = 1 - sum((b - intercept - slope * a)**2 for a, b in zip(x, y)) / sum((b - ybar)**2 for b in y)
        assert int(reported[branch]["points"]) == len(x)
        assert float(reported[branch]["slope"]) == float(format(slope, ".4g"))
        assert (reported[branch]["slope in 1 to 2.5"] == "True") == (1 <= slope <= 2.5)
        fits.append(dict(branch=branch, points=len(x), slope=slope, r_squared=r_squared,
                         slope_in_band=1 <= slope <= 2.5))
    assert [r["branch"] for r in fits if not r["slope_in_band"]] == ["D1_f0.5", "D2_d0.0001"]

    path = FIG / "graded_dials/threshold_refinement/thresholds.json"
    INPUTS.append(path)
    brackets = json.loads(path.read_text())["branches"]
    exported = {r["branch_id"]: r for r in read(PAPER / "figures/data/fig3_thresholds.csv")}
    for row in brackets:
        actual = exported[row["branch_id"]]
        for source, target in (("price_low", "price_low_K"), ("price_high", "price_high_K"),
                               ("low_tau", "tau_low_yr"), ("high_tau", "tau_high_yr")):
            assert math.isclose(row[source], float(actual[target]), rel_tol=1e-12)
        assert row["low_tau"] < 30 < row["high_tau"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = dict(counts=counts, per_branch_prescribed_fits=fits,
                  threshold_brackets_match=True,
                  source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in INPUTS})
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
