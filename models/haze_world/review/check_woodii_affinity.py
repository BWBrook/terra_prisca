"""Audit the conditional affinity fits, preserving the faithful benchmark.

uv run python models/haze_world/review/check_woodii_affinity.py

Fits are descriptive sensitivities, not estimates with measured error bars.
"""

import csv
from hashlib import sha256
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "evidence/peters1998_chemostat.csv"
ROWS = list(csv.DictReader(DATA.open()))
D = np.array([float(r["dilution_h^-1"]) for r in ROWS])
H = np.array([float(r["residual_H2_Pa"]) for r in ROWS])
Y, M, MU_MAX = 1.7, 1.6, 0.024


def fit(pressures, *, pstar=0., objective="log", free_capacity=True, mask=None, mu_max=MU_MAX):
    if mask is None:
        mask = np.ones(len(D), dtype=bool)
    q = M + D[mask] / Y * 1000
    observed = np.asarray(pressures)[mask]
    capacity = M + mu_max / Y * 1000

    def residual(parameters):
        k, s = parameters if free_capacity else (parameters[0], capacity)
        predicted = pstar + k * q / (s - q)
        return np.log(predicted) - np.log(observed) if objective == "log" else predicted - observed

    if free_capacity:
        bounds = ([1., max(q) + .001], [5000., 100.])
        starts = ([100., max(15., max(q) + .1)], [500., max(25., max(q) + .1)])
    else:
        bounds, starts = ([1.], [5000.]), ([100.],)
    results = [least_squares(residual, start, bounds=bounds, x_scale="jac",
                             ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=3000)
               for start in starts]
    result = min(results, key=lambda item: sum(item.fun ** 2))
    assert result.success
    k = float(result.x[0])
    capacity = float(result.x[1]) if free_capacity else capacity
    prediction = pstar + k * q / (capacity - q)
    return dict(pstar_pa=pstar, objective=objective, free_capacity=free_capacity,
                K_pa=k, capacity_mmol_gdw_h=capacity,
                implied_maximum_net_growth_h=(capacity - M) * Y / 1000,
                log_rmse=float(np.sqrt(np.mean((np.log(prediction / observed)) ** 2))),
                pressure_rmse_pa=float(np.sqrt(np.mean((prediction - observed) ** 2))),
                predicted_pa=list(prediction))


def main():
    fits = [fit(H, pstar=pstar, objective=objective, free_capacity=free)
            for pstar, objective, free in itertools.product((0., 20.), ("log", "linear"), (True, False))]
    old = json.loads((HERE / "woodii_affinity_check.json").read_text())
    for prior in old["fits"]:
        match = next(r for r in fits if r["pstar_pa"] == prior["pstar_pa"]
                     and r["free_capacity"] == prior["free_capacity"] and r["objective"] == "log")
        assert np.isclose(match["K_pa"], prior["K_pa"], rtol=1e-5)
        assert np.isclose(match["capacity_mmol_gdw_h"], prior["s_mmol_gdw_h"], rtol=1e-6)

    sensitivity = []
    for pstar, objective, free in itertools.product((0., 20.), ("log", "linear"), (True, False)):
        corners = [fit(H + np.array(offset), pstar=pstar, objective=objective, free_capacity=free)
                   for offset in itertools.product((-.5, .5), repeat=4)]
        sensitivity.append(dict(pstar_pa=pstar, objective=objective, free_capacity=free,
                                scenario="Independent +/-0.5 Pa changes to printed residuals; rounding sensitivity, not confidence bounds",
                                K_min_pa=min(r["K_pa"] for r in corners),
                                K_max_pa=max(r["K_pa"] for r in corners)))
    leave_one_out = []
    for omitted, objective, free in itertools.product(range(4), ("log", "linear"), (True, False)):
        result = fit(H, objective=objective, free_capacity=free, mask=np.arange(4) != omitted)
        result["omitted_growth_h"] = float(D[omitted])
        result["omitted_pressure_pa"] = float(H[omitted])
        result["omitted_point_has_finite_positive_prediction"] = bool(
            result["capacity_mmol_gdw_h"] > M + D[omitted] / Y * 1000)
        leave_one_out.append(result)

    q = M + D / Y * 1000
    capacity = M + MU_MAX / Y * 1000
    per_point = [dict(pstar_pa=pstar, K_from_each_point_pa=list((H - pstar) * (capacity - q) / q))
                 for pstar in (0., 20.)]
    half_growth = [dict(pstar_pa=pstar, source_half_growth_pressure_pa=94.,
                        implied_uptake_K_pa=(94. - pstar) * (capacity - M) / (capacity + M))
                   for pstar in (0., 20.)]
    files = (Path(__file__), DATA, HERE / "woodii_affinity_check.py", HERE / "woodii_affinity_check.json")
    result = dict(
        conditioning=dict(yield_h2_gdw_mol=Y, maintenance_h2_mmol_gdw_h=M,
                          measured_maximum_growth_h=MU_MAX, observed_growth_h=list(D), observed_pa=list(H),
                          source_doi="10.1111/j.1574-6941.1998.tb00516.x"),
        fits=fits, rounding_sensitivity=sensitivity, leave_one_out=leave_one_out,
        fixed_capacity_pointwise_K=per_point, source_half_growth_translation=half_growth,
        maximum_growth_rounding_sensitivity=[fit(H, free_capacity=False, mu_max=mu)
                                            for mu in (.0235, .0245)],
        file_sha256={str(path.relative_to(HERE.parents[2])): sha256(path.read_bytes()).hexdigest()
                     for path in files},
        interpretation="Conditional mismatch supports K sensitivities; not a cold-strain calibration or identification of gas-transfer bias",
    )
    (HERE / "woodii-affinity-audit.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(fits=fits, rounding_sensitivity=sensitivity,
                         fixed_capacity_pointwise_K=per_point,
                         source_half_growth_translation=half_growth), indent=2))


if __name__ == "__main__":
    main()
