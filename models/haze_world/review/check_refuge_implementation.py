"""Compare the implemented nine-state budget with the independent design RHS."""

from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world import refuge_coupling as model
from terra_prisca.haze_world import refuge_equilibria as equilibria

ROOT = Path(__file__).resolve().parents[3]


def main():
    path = Path(__file__).with_name("check_refuge_design.py")
    spec = importlib.util.spec_from_file_location("independent_refuge_design", path)
    independent = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(independent)
    records = []
    for fraction, warm, contrast in ((0., .74, 1.), (.5, .51, 8.)):
        for dispersal in (0., .001):
            p = model.Refuge(replace(core.reference(), acetate_fraction=fraction), warm, contrast, dispersal)
            candidates = equilibria.equilibrium_states(p, n_grid=201)
            chosen = next(e for e in candidates if e["stable"] and
                          np.all(p.weights @ e["y"][model.BIOMASS_INDICES] > 1e-6))
            y = chosen["y"]
            perturbed = y * np.array([1.001, .999, 1.001, 1.002, .999, 1.002, .999, .999, 1.000001])
            actual = model.rhs(perturbed, p)
            expected = independent.rhs(perturbed, fraction, warm, contrast, dispersal)
            scale = np.maximum(abs(expected), [1., 1e-5, 1e-5, 1e-5, 1., 1e-5, 1e-5, 1e-5, 1e-6])
            error = float(max(abs(actual - expected) / scale))
            assert error < 1e-10
            first = np.linalg.eigvals(model.jacobian(y, p))
            second = independent.eigenvalues(y, fraction, warm, contrast, dispersal)
            cost = abs(first[:, None] - second[None, :]) / np.maximum(1., abs(second[None, :]))
            rows, columns = linear_sum_assignment(cost)
            spectral_error = float(max(cost[rows, columns]))
            assert spectral_error < 1e-6
            assert max(first.real) < 0 and max(second.real) < 0
            residual = model.redox_residual(perturbed, p)
            assert abs(residual) < 1e-14
            records.append(dict(fraction=fraction, warm_fraction=warm, contrast_k=contrast,
                                dispersal_yr=dispersal, global_temperature_k=chosen["global_temperature_k"],
                                temperatures_k=chosen["temperatures_k"].tolist(),
                                maximum_scaled_rhs_difference=error, matched_spectral_error=spectral_error,
                                redox_residual=residual, maximum_real_eigenvalue_yr=float(max(first.real))))
    names = ("population_coupling.py", "refuge_coupling.py", "refuge_equilibria.py")
    sources = [path, Path(__file__), *[ROOT / "src/terra_prisca/haze_world" / name for name in names]]
    output = dict(scope="Independent algebraic RHS and numerical spectra at four measured fixed-product reference equilibria; not independent empirical validation",
                  checks=records, source_sha256={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sources})
    Path(__file__).with_name("refuge_implementation_check.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(records, indent=2))


if __name__ == "__main__":
    main()
