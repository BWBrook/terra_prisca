"""Bounded Issue 1 recount; --predictor-checks requalifies three existing points.

No new supply grid, lag sweep, or physiology extension is computed.
"""

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "models/haze_world/review"
SOURCE = REVIEW / "issue1_spread_response.json"
ARNEY = ROOT / "models/haze_response/arney2016/figure4.csv"
S4 = ROOT / "models/haze_world/paper/esm/s4_states.csv"
S8 = ROOT / "models/haze_world/paper/esm/s8_coexistence_interval.csv"


def predictor_checks(data):
    import numpy as np
    from terra_prisca.haze_world import continuum_core as model
    from terra_prisca.haze_world import dynamic_core as reference

    spec = importlib.util.spec_from_file_location("issue1_probe", REVIEW / "issue1_spread_response.py")
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    results = []
    for sigma in (1., 3., 8.):
        rows = [r for r in data["rows"] if r["sigma_K"] == sigma]
        row = next(r for r in rows if r["direction"] == "ref") if sigma == 1 else max(rows, key=lambda r: r["P"])
        means = np.array([row["mean_acetogen"], row["mean_methanogen"]])
        qualified = None
        for panels in (8, 12, 16, 6, 24, 4):
            p = probe.params_at(sigma, row["P"], model.gauss_mesh(sigma, np.linspace(-sigma, sigma, panels + 1)))
            seed = np.ones(p.state_size)
            seed[-1] = row["r"]
            seed = model.local_profile_correction(seed, p, means)
            if seed is None:
                continue
            initial = model.equilibrium(seed, p)
            if initial is None:
                continue
            qualified, _ = probe.accept(initial["y"], p)
            if qualified is not None:
                break
        assert qualified is not None, (sigma, row["P"])
        y, p = qualified["y"], qualified["p"]
        residual = float(abs(model.physical_rhs(y, p) / reference.state_scales(y, p)).max())
        percapita = float(abs(model.per_capita(y, p)).max())
        t_error = reference.temperature(y[-1], p) - row["T_K"]
        s_error = qualified["m"]["Sc"] - row["S_K_per_efold"]
        assert residual < 1e-8 and percapita < 1e-8 and abs(t_error) < 1e-5 and abs(s_error) < 1e-4
        results.append(dict(sigma=sigma, P=row["P"], fresh_panels=panels, nodes=p.n,
                            temperature_error_k=t_error, slope_error_k=s_error,
                            scaled_rhs_max=residual, per_capita_max=percapita))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--predictor-checks", action="store_true")
    args = parser.parse_args()
    data = json.loads(SOURCE.read_text())
    with ARNEY.open() as handle:
        vertices = [r for r in csv.DictReader(handle) if r["case"] == "B"]
    points = sorted((float(r["ch4_co2_ratio"]), float(r["temperature_k"])) for r in vertices)
    rstar = data["meta"]["r_star"]
    a, b = next((a, b) for a, b in zip(points, points[1:]) if a[0] <= rstar <= b[0])
    k = abs((b[1] - a[1]) / (b[0] - a[0])) * rstar
    with S8.open() as handle:
        bounds = {float(r["f"]): r for r in csv.DictReader(handle)}
    with S4.open() as handle:
        source_states = list(csv.DictReader(handle))
    geometry_rows = []
    for row in source_states:
        sigma = float(row["sigma_K"] or 0)
        if row["chemistry"] != "fixed" or sigma <= 0 or not row["S"]:
            continue
        f, potential = float(row["f"]), float(row["supply_potential"])
        low = float(bounds[f]["lower end, methanogens alone"])
        factor = 1 if f == 0 else 1 / (1 - low / float(bounds[f]["upper end, acetogens alone"]))
        geometric = 2 * sigma * low / potential * factor
        predicted = 1 / (1 / k + 1 / geometric)
        geometry_rows.append(dict(rate=float(row["d_per_yr"]), ratio=abs(float(row["S"])) / predicted))
    intervals = {}
    for rate in (1e-4, 1e-3, 1e-2, .1):
        ratios = [r["ratio"] for r in geometry_rows if r["rate"] == rate]
        intervals[str(rate)] = dict(n=len(ratios), computed_over_predicted_min=min(ratios),
                                   computed_over_predicted_max=max(ratios))
    widths = []
    for r in source_states:
        if r["chemistry"] == "fixed" and float(r["f"]) == .5 and float(r["supply_potential"]) == .3 and float(r["sigma_K"] or 0) == 3:
            widths.append(dict(d_per_yr=float(r["d_per_yr"]), S=float(r["S"]), S0=float(r["S0"]),
                               G_loc=float(r["G_loc"]), abs_S_over_k=abs(float(r["S"])) / k))
    finite = []
    for sigma in (1, 3, 6, 8):
        s = data["summary"][str(sigma)]
        finite.append(dict(sigma=sigma, P_min=s["P_min"], P_max=s["P_max"],
                           fixed_interval_span_k=s["span_K"], full_spread_k=2 * sigma,
                           fixed_interval_fully_covered=s["covers_P_lo"] and s["covers_P_hi"],
                           accepted_extreme_warm_error_k=s["max_T_K"] - s["T_pred_lo"],
                           accepted_extreme_cold_error_k=s["min_T_K"] - s["T_pred_hi"]))
    mismatch = []
    for name, end in data["meta"]["branch_ends"].items():
        sigma = float(name.split("_")[0].removeprefix("sigma"))
        rows = [r for r in data["rows"] if r["sigma_K"] == sigma]
        actual = max(r["P"] for r in rows) if name.endswith("up") else min(r["P"] for r in rows)
        if actual != end["last_P"]:
            mismatch.append(dict(branch=name, reported_last_P=end["last_P"], accepted_last_P=actual,
                                 reported_reason=end["reason"]))
    hi = max(float(r["ch4_co2_ratio"]) for r in vertices)
    meth = [r for r in data["methanogen_only"] if data["meta"]["P_lo"] <= r[0] <= data["meta"]["P_hi"]]
    plateau = [r for r in meth if r[2] > hi]
    supported = [r for r in meth if r[2] <= hi]
    extrapolation = []
    for sigma in (15, 21):
        geo = 2 * sigma * data["meta"]["P_lo"] / .3 * data["meta"]["Q"] / (data["meta"]["Q"] - 1)
        sensitivity = 1 / (1 / k + 1 / geo)
        extrapolation.append(dict(sigma=sigma, S_magnitude=sensitivity,
                                  bare_haze_attenuation=k / sensitivity,
                                  status="unsupported-width reduced-model extrapolation; not G_loc"))
    result = dict(bare_haze_sensitivity_k=k, geometry_ratio_intervals=intervals, matched_sigma3_gains=widths,
                  finite_branch_recount=finite, stop_metadata_mismatches=mismatch,
                  homogeneous_methanogen_comparator=dict(samples=len(meth), extrapolated_samples=len(plateau),
                    first_extrapolated=plateau[0], last_supported=supported[-1], last_source_ratio=hi,
                    reference_P_point=next(r for r in meth if math.isclose(r[0], .3))),
                  unsupported_surface_extrapolations=extrapolation)
    if args.predictor_checks:
        result["fresh_mesh_predictor_checks"] = predictor_checks(data)
    inputs = (SOURCE, ARNEY, S4, S8, REVIEW / "issue1_spread_response.py")
    result["input_sha256"] = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
