"""Compare the frozen K1–K5 predictions with the qualified bottleneck tables."""

import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import bottleneck_runs as runs
from . import buffered_experiments as e


def read(name):
    with (runs.OUTPUT/name).open() as stream:
        return list(csv.DictReader(stream))


def main():
    planned, exchange = read("survival.csv"), read("exchange_continuation.csv")
    thresholds = json.loads((runs.OUTPUT/"exchange_thresholds.json").read_text())
    if len(planned) != 384 or len(exchange) != 196:
        raise RuntimeError("Incomplete prediction assessment")
    target = sorted([r for r in exchange if float(r["fraction"]) == 0 and float(r["refuge_fraction"]) == .02],
                    key=lambda r:float(r["dispersal_yr"]))
    x = np.log10([float(r["dispersal_yr"]) for r in target]); y = np.array([float(r["log10_min_cells"]) for r in target])
    fit = x <= -4+1e-12
    slope, intercept = np.polyfit(x[fit], y[fit], 1)
    residual = y[fit]-(slope*x[fit]+intercept)
    matched = []
    for f in (0., .5):
        curves = []
        for w in (.005, .02):
            rows = sorted([r for r in exchange if float(r["fraction"]) == f and float(r["refuge_fraction"]) == w],
                          key=lambda r:float(r["dispersal_yr"]))
            curves.append((np.log10([float(r["dispersal_yr"])*w for r in rows]),
                           np.array([float(r["log10_min_cells"]) for r in rows])))
        grid = np.unique(np.concatenate([a for a,b in curves]))
        grid = grid[(grid >= max(a[0] for a,b in curves)) & (grid <= min(a[-1] for a,b in curves))]
        difference = np.interp(grid,*curves[0])-np.interp(grid,*curves[1])
        matched.append(dict(fraction=f, maximum_log10_cell_difference=float(max(abs(difference))),
                            within_one_decade=bool(max(abs(difference)) <= 1.)))
    crossings = []
    for group in thresholds["groups"]:
        t = group["transitions"]
        if all(len(t[name]) == 1 for name in ("one_year_floor", "ten_year_floor", "half_survival")):
            one, ten, half = (t[name][0]["interpolated_yr"] for name in ("one_year_floor", "ten_year_floor", "half_survival"))
            crossings.append(dict(fraction=group["fraction"], refuge_fraction=group["refuge_fraction"],
                one_year_floor_exchange=one, ten_year_floor_exchange=ten, half_survival_exchange=half,
                half_over_one_year_floor=half/one, half_over_ten_year_floor=half/ten,
                census_threshold_ratio=max(one,ten)/min(one,ten)))
    contenders = [dict(case_id=r["base_case_id"], guild=r["guild"], probability=float(r["survival_probability"]),
        downstream_of_prior_strong_loss=r["downstream_of_other_guild_strong_loss"] == "True")
        for r in planned if r["classification"] == "contingent"]
    changed_survivors = [r for r in planned if r["census_global_present"] == "True" and r["classification"] != "robust_persistence"]
    half = [r for r in exchange if float(r["fraction"]) == .5]
    paths = [runs.OUTPUT/n for n in ("survival.csv", "exchange_continuation.csv", "exchange_thresholds.json")]
    report = dict(
        inputs={p.name:sha256(p.read_bytes()).hexdigest() for p in paths},
        K1=dict(contingent_guilds=contenders, census_survivors_not_robust_in_uncensored_environment=len(changed_survivors),
            downstream_of_prior_strong_loss=sum(r["downstream_of_other_guild_strong_loss"] == "True" for r in changed_survivors),
            zero_exchange_spatially_unresolved=sum(float(r["dispersal_yr"]) == 0 and r["configuration"] != "none"
                and r["downstream_of_other_guild_strong_loss"] != "True" for r in changed_survivors),
            interpretation="Conditional diagnostics cannot assign joint endpoints after a prior guild would disappear; global survival does not determine zero-exchange patch occupancy"),
        K2=dict(fit_log10_exchange_range=[float(min(x[fit])),float(max(x[fit]))], points=int(sum(fit)),
            log_log_slope=float(slope), slope_in_predicted_range=bool(4.1 <= slope <= 4.7),
            maximum_log10_fit_residual=float(max(abs(residual))),
            high_exchange_secant_slope=float((y[-1]-y[-9])/(x[-1]-x[-9]))),
        K3=dict(transitions=crossings, interpretation="Interpolations retain the grid brackets in exchange_thresholds.json"),
        K4=dict(aligned_curves=matched),
        K5=dict(cases=len(half), minimum_log10_acetogen_cells=min(float(r["log10_min_cells"]) for r in half),
            above_predicted_1e12_floor=all(float(r["log10_min_cells"]) > 12 for r in half),
            all_first_window_robust_persistence=all(r["classification"] == "robust_persistence" for r in half)),
        source_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    (runs.OUTPUT/"prediction_assessment.json").write_text(e.dumps(report)+"\n")
    print(json.dumps(report,indent=2))


if __name__ == "__main__": main()
