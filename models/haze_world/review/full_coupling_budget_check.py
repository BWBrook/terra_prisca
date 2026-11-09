"""Independent annual-rate budget and Jacobian check; no model parameters fitted.

uv run python models/haze_world/review/full_coupling_budget_check.py
"""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import population_coupling as model
from terra_prisca.haze_world.methane_budget import AVOGADRO, atmosphere, temperature_k
from terra_prisca.haze_world.two_guilds import HENRY_30C_MOL_L_PA, guilds

H = 365.25 * 24


def independently_derived(y, p):
    pressure, xa, xm, acetate, ratio = y
    t = float(temperature_k(ratio, p.climate))
    pair = guilds(t - 273.15, p.biology)
    x = np.array([xa, xm]) * p.enabled
    q = np.array([g.uptake(pressure) for g in pair])
    mu = np.array([g.yield_g_mol * (qi - g.maintenance) for g, qi in zip(pair, q)])
    a = np.array([g.assimilation_mol_g for g in pair])
    use = H * q * x
    synthesis = H * np.maximum(mu, 0) * x
    cat = use - a * synthesis
    sigma = 1. if p.recycling_variant == "constant" else 1 / (1 + np.exp((p.recycling_midpoint_k - t) / p.width_k))
    kr = p.acetate_fraction * sigma / p.acetate_lifetime_yr
    ko = (1 - p.acetate_fraction) / p.acetate_lifetime_yr
    air = atmosphere(p.climate.case)
    nco2 = air["column"] * air["f_co2"]
    gamma = AVOGADRO * p.habitat_l_cm2 / nco2
    j = 4 * p.climate.donor_flux * (H * 3600) / (AVOGADRO * p.habitat_l_cm2)
    outlet = H * p.biology.exchange_mol_l_h_pa * (pressure - p.biology.atmosphere_pa)
    ab = H * 3600 / nco2 * p.climate.abiotic_flux
    loss = float(p.loss.rate(ratio))
    dx = H * (mu - p.biology.loss_h) * x
    dy = np.r_[(j - sum(use) - outlet) / HENRY_30C_MOL_L_PA,
               dx, cat[0] / 4 - (kr + ko) * acetate,
               gamma * (cat[1] / 4 + kr * acetate) + ab - loss]
    biomass_export = H * sum(a * (p.biology.loss_h + np.maximum(-mu, 0)) * x)
    external = j - outlet - 4 * ko * acetate - biomass_export + 4 / gamma * (ab - loss)
    weights = np.r_[HENRY_30C_MOL_L_PA, a, 4., 4 / gamma]
    return dy, weights, external, dict(kr=kr, ko=ko, gamma=gamma, q=q, mu=mu)


def finite_jacobian(y, p):
    scales = np.maximum(np.abs(y), [10., 1e-4, 1e-4, 1e-5, .01])
    jac = np.empty((5, 5))
    for j in range(5):
        h = scales[j] * 1e-4
        delta = np.eye(5)[j] * h
        vals = [independently_derived(y + k * delta, p)[0] for k in (2, 1, -1, -2)]
        derivative = (-vals[0] + 8 * vals[1] - 8 * vals[2] + vals[3]) / (12 * h)
        jac[:, j] = derivative * scales[j] / scales
    return jac, scales


def main():
    reference = model.reference()
    mixed = next(e for e in model.equilibrium_states(reference) if e["kind"] == "mixed")
    y = np.asarray(mixed["y"])
    checks = []
    for label, params, state in (
        ("mixed_reference", reference, y),
        ("starvation", reference, np.r_[0., y[1:3], y[3:]]),
        ("stored_acetate_release", reference, np.array([10., 0., 0., .01, y[4]])),
        ("no_recycling", replace(reference, acetate_fraction=0.), y),
        ("complete_recycling", replace(reference, acetate_fraction=1.), y),
        ("cold_limited", replace(reference, recycling_variant="cold_limited"), y),
        ("cold_limited_complete", replace(reference, recycling_variant="cold_limited", acetate_fraction=1.), y),
        ("zero_M_assimilation", replace(reference, biology=replace(reference.biology, assimilation_m=0.)), y),
    ):
        derived, weights, external, _ = independently_derived(state, params)
        actual = model.rhs(state, params)
        scale = np.maximum(np.abs(derived), 1e-12)
        error = float(np.max(np.abs(derived - actual) / scale))
        residual = float(weights @ actual - external)
        assert error < 1e-11 and abs(residual) < 1e-14
        checks.append(dict(case=label, maximum_relative_rhs_difference=error,
                           independent_inventory_residual_mol_h2_l_yr=residual,
                           model_redox_residual=model.redox_residual(state, params)))
    jchecks = []
    for label, params in (("constant", reference), ("cold_limited", replace(reference, recycling_variant="cold_limited"))):
        jf, scales = finite_jacobian(y, params)
        jm = model.jacobian(y, params)
        relative = float(np.linalg.norm(jm - jf) / np.linalg.norm(jf))
        _, _, _, terms = independently_derived(y, params)
        physical = jm * scales[:, None] / scales[None, :]
        exact = {(3, 3): -(terms["kr"] + terms["ko"]),
                 (4, 3): terms["gamma"] * terms["kr"],
                 (0, 1): -H * terms["q"][0] / HENRY_30C_MOL_L_PA,
                 (1, 1): H * (terms["mu"][0] - params.biology.loss_h)}
        errors = {f"{i},{j}": float(physical[i, j] - value) for (i, j), value in exact.items()}
        relative_errors = {f"{i},{j}": float(abs(physical[i, j] - value) / max(abs(value), 1.))
                           for (i, j), value in exact.items()}
        reference_eigenvalues = np.linalg.eigvals(jf)
        eigen_pairs = [dict(real_per_yr=float(a.real), imaginary_per_yr=float(a.imag),
                            absolute_difference_per_yr=float(min(abs(a - b) for b in reference_eigenvalues)))
                       for a in np.linalg.eigvals(jm)]
        eigen_error = max(e["absolute_difference_per_yr"] for e in eigen_pairs)
        assert relative < 1e-7 and max(relative_errors.values()) < 1e-7, (relative, errors)
        jchecks.append(dict(variant=label, scaled_jacobian_relative_difference=relative,
                            maximum_matched_eigenvalue_difference_per_yr=eigen_error,
                            matched_eigenvalues=eigen_pairs,
                            analytic_physical_entry_errors=errors,
                            analytic_entry_relative_errors=relative_errors))
    air = atmosphere(reference.climate.case)
    gamma = AVOGADRO * reference.habitat_l_cm2 / (air["column"] * air["f_co2"])
    ideal_source = gamma * H * model.supply_h2(reference) / 4
    expected = air["flux_to_ratio_per_yr"] * reference.climate.donor_flux
    assert np.isclose(ideal_source, expected, rtol=1e-14)
    result = dict(scope="Independent dimensional/budget/Jacobian audit; not full bifurcation or attractor validation",
                  audited_population_coupling_sha256=sha256(Path(model.__file__).read_bytes()).hexdigest(),
                  hours_per_year=H, reference_state=y.tolist(), budget_checks=checks,
                  jacobian_checks=jchecks, ideal_direct_source_ratio_per_yr=ideal_source,
                  expected_column_source_ratio_per_yr=expected,
                  acetate_molarity_at_constant_rate_equilibria={str(tau): float(y[3] * tau) for tau in (1, 100, 1000, 10000)})
    output = Path(__file__).with_name("full_coupling_budget_check.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
