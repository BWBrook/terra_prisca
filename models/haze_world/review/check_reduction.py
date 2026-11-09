"""Audit the equilibrium elimination and its dynamical limits.

uv run python models/haze_world/review/check_reduction.py OUTPUT_JSON
The reviewed 4070dc3 abiotic source is frozen for the historical counterexample.
"""

from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np
from scipy.integrate import solve_ivp

from terra_prisca.haze_world.experiments import domain_invariant, flux_for_potential, cold_edge_k
from terra_prisca.haze_world.methane_budget import (
    Params, atmosphere, equilibria, full_derivatives, integrate_full, response, tendency,
)


def living(p):
    return [e for e in equilibria(p) if e["stable"] and e["eta"] > 0][-1]


def check(p):
    c = atmosphere(p.case)["flux_to_ratio_per_yr"]
    e = living(p)
    uptake = e["r"] / p.lifetime_yr - c * p.abiotic_flux
    y = np.array([(c * p.donor_flux - uptake) / 0.1, uptake, e["r"]])
    columns = []
    for i in range(3):
        step = max(abs(y[i]) * 1e-5, 1e-10)
        delta = np.eye(3)[i] * step
        columns.append((full_derivatives(y + delta, p) - full_derivatives(y - delta, p)) / (2 * step))
    jacobian = np.column_stack(columns)
    eigen = np.linalg.eigvals(jacobian)
    bio_eigen = np.linalg.eigvals(jacobian[:2, :2])
    eps = 1e-8
    scalar_rate = float((tendency(e["r"] + eps, p) - tendency(e["r"] - eps, p)) / (2 * eps))
    u, h, k, death, loss = jacobian[1, 0], -jacobian[1, 2], 0.1, 1.0, 1 / p.lifetime_yr
    coefficients = np.array([k + u + h + loss,
                             death * u + (k + u) * loss + (k + death) * h,
                             death * u * loss + k * death * h])
    np.testing.assert_allclose(np.poly(jacobian)[1:], coefficients, rtol=1e-5)
    lo, _ = response(p.case).ratios[[0, -1]]
    boundary = np.array([c * p.donor_flux / k, 1e-12, lo])
    return dict(equilibrium=e, full_state=y.tolist(),
                full_equilibrium_residual=float(abs(full_derivatives(y, p)).max()),
                reduced_rate_per_yr=scalar_rate,
                full_eigenvalues_per_yr=[[float(v.real), float(v.imag)] for v in eigen],
                frozen_biology_eigenvalues_per_yr=[[float(v.real), float(v.imag)] for v in bio_eigen],
                characteristic_coefficients=coefficients.tolist(),
                routh_hurwitz=bool((coefficients > 0).all() and coefficients[0] * coefficients[1] > coefficients[2]),
                reduced_interval_invariant=domain_invariant(p),
                boundary_full_methane_rate=float(full_derivatives(boundary, p)[2]),
                boundary_reduced_methane_rate=float(tendency(lo, p)))


def main(path):
    original = Params(abiotic_flux=1.3e9)
    original = replace(original, donor_flux=float(flux_for_potential(0.3, original)))
    earth = Params()
    earth = replace(earth, donor_flux=float(flux_for_potential(0.3, earth)))
    c = atmosphere(original.case)["flux_to_ratio_per_yr"]
    initial = np.array([c * original.donor_flux / 0.1, 1e-6, response("B").ratios[-1]])
    legacy = solve_ivp(lambda _t, y: full_derivatives(y, original), (0, 3e5), initial,
                       method="LSODA", rtol=1e-9, atol=1e-14)
    if not legacy.success:
        raise RuntimeError(legacy.message)
    fixed = integrate_full(initial, original, 3e5)
    q = replace(earth, donor_flux=float(flux_for_potential(0.22, earth)))
    passive = replace(q, thermal=False)
    a, b = living(q), living(passive)
    result = dict(reviewed_4070dc3=check(original), corrected_Earth_source=check(earth),
                  rare_biomass=dict(initial=initial.tolist(), legacy_final=legacy.y[:, -1].tolist(),
                                    log_biomass_final=fixed.tolist()),
                  source_contained_control=dict(potential_ratio=0.22, cold_edge_k=cold_edge_k(q),
                                                thermal=a, passive=b, difference_k=a["t_k"] - b["t_k"],
                                                both_reduced_intervals_invariant=domain_invariant(q) and domain_invariant(passive)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
