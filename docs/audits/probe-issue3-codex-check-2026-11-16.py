"""Bounded Issue 3 review: methane scaling and stored persistence counts.

No integrations or production outputs are written. Run with --output PATH.
"""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "models/haze_world/review"))
from issue3_assembly import Speeded
from terra_prisca.haze_world import dynamic_transients as dt
from terra_prisca.haze_world import population_coupling as core


def read(name):
    with (ROOT / name).open() as fh:
        return list(csv.DictReader(fh))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    p = dt.parameters(dt.Case("review", "B3", "fixed", .5, 0.))
    states = core.equilibrium_states(p)
    mixed = next(x for x in states if x["kind"] == "mixed")
    ceiling = (core.atmosphere(p.climate.case)["flux_to_ratio_per_yr"] * p.climate.abiotic_flux
               + core.inventory_to_ratio(p) * core.supply_h2(p) * core.HOURS_PER_YEAR / 4)
    bounds = {str(lifetime): ceiling * lifetime for lifetime in (10, 1000)}
    assert all(r < mixed["r"] for r in bounds.values())

    jacobians = []
    for tau in (0., 3.):
        ordinary = dt.Coordinates(mixed["y"], p, tau, mixed["t_k"])
        scaled = Speeded(mixed["y"], p, tau, mixed["t_k"])
        scaled.scale = 1000.
        z = ordinary.encode(mixed["y"], mixed["t_k"])
        z[0] *= 1.01
        z[4] *= 1.001
        base = ordinary.derivative(0., z)
        expected = base.copy()
        expected[4] *= scaled.scale
        np.testing.assert_allclose(scaled.derivative(0., z), expected)
        actual = scaled.jacobian(0., z)
        finite = np.zeros_like(actual)
        for j in range(len(z)):
            h = 1e-5 * max(1., abs(z[j]))
            step = np.zeros_like(z)
            step[j] = h
            finite[:, j] = (scaled.derivative(0., z + step) - scaled.derivative(0., z - step)) / (2 * h)
        error = float(np.max(abs(actual - finite) / (1 + abs(actual))))
        assert error < 1e-5, error
        jacobians.append(dict(tau_yr=tau, methane_speed=scaled.scale, normalized_max_error=error))

    trajectories = json.loads((ROOT / "models/haze_world/review/issue3_assembly.json").read_text())
    speed = [r for r in trajectories if r["check"] == "methane_speed"]
    assert len(speed) == 16 and len(trajectories) == 19
    accelerated = [r for r in speed if r["speed"] == 1000 and r["endpoint"] == "both"]
    assert {(r["fraction"], r["direction"]) for r in accelerated} == {(0., "A_into_M"), (.5, "A_into_M")}
    imm = read("models/haze_world/figures/finite_populations/attained_endpoints.csv")
    immigration = []
    for fraction in (0., .5):
        selected = [r for r in imm if float(r["fraction"]) == fraction and float(r["relative_immigration_yr"]) > 0]
        assert len(selected) == 36
        assert all(r["settling_status"] == "census_stationary" for r in selected)
        assert all(min(float(r["catabolic_share_a"]), float(r["catabolic_share_m"])) >= .01 for r in selected)
        assert all(r["immigration_supported_sink_a"] == r["immigration_supported_sink_m"] == "False" for r in selected)
        immigration.append(dict(fraction=fraction, both_material=len(selected),
                                temperature_range_k=[min(float(r["temperature_k"]) for r in selected),
                                                     max(float(r["temperature_k"]) for r in selected)]))

    buffered = read("models/haze_world/figures/buffered_refuges/selected_main.csv")
    keys = [r for r in buffered if r["configuration"] == "both" and float(r["fraction"]) in (0., .5)
            and float(r["dispersal_yr"]) in (1e-9, 1e-6, 1e-3)]
    assert len(keys) == 12
    assert all(r["settling_status"] == "census_stationary" and r["material_both"] == "True" for r in keys)
    tracking = read("models/haze_world/figures/refuge_coupling/direction_comparisons.csv")
    matches = [r for r in tracking if float(r["fraction"]) == .9 and r["matching_endpoint"] == "True"
               and r["class_a"] in ("spatial_coexistence", "pure_partition") and r["class_m"] == r["class_a"]]
    assert len(matches) == 9
    assert sum(float(r["dispersal_yr"]) > 0 for r in matches) == 7

    inputs = ["models/haze_world/review/issue3_assembly.py", "models/haze_world/review/issue3_assembly.json",
              "src/terra_prisca/haze_world/dynamic_transients.py", "src/terra_prisca/haze_world/population_coupling.py",
              "models/haze_world/figures/finite_populations/attained_endpoints.csv",
              "models/haze_world/figures/buffered_refuges/selected_main.csv",
              "models/haze_world/figures/refuge_coupling/direction_comparisons.csv"]
    out = dict(commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
               input_sha256={name: sha256((ROOT / name).read_bytes()).hexdigest() for name in inputs},
               max_steady_methane_source_ratio_per_yr=ceiling,
               physical_lifetime_upper_ratio=bounds, reference_mixed_ratio=mixed["r"],
               jacobians=jacobians, accelerated_mixed_cases=[r["direction"] + "_f" + str(r["fraction"]) for r in accelerated],
               immigration=immigration, key_buffered_runs=len(keys),
               buffered_temperature_range_k=[min(float(r["global_temperature_k"]) for r in keys),
                                            max(float(r["global_temperature_k"]) for r in keys)],
               tracking_matching_coexisting_pairs=len(matches),
               tracking_matching_positive_exchange_pairs=sum(float(r["dispersal_yr"]) > 0 for r in matches))
    args.output.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("input_sha256",)}, indent=2))


if __name__ == "__main__":
    main()
