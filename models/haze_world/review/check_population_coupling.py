"""Independent equilibrium, Jacobian and invasion-path audit.

uv run python models/haze_world/review/check_population_coupling.py

Rare-invasion failures are recorded explicitly so this audit also records
whether a later integrator repair resolves them. No source output is changed.
"""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import warnings

import numpy as np

from terra_prisca.haze_world.darwinian import climate_slopes
from terra_prisca.haze_world.methane_budget import response
from terra_prisca.haze_world.population_coupling import (
    HOURS_PER_YEAR, equilibrium_states, fluxes, integrate, inventory_to_ratio,
    jacobian, recycling_rates, reference, rhs,
)
from terra_prisca.haze_world.two_guilds import HENRY_30C_MOL_L_PA, guilds

ROOT = Path(__file__).resolve().parents[3]


def independent_jacobian(y, p, slope):
    """Explicit physical balance derivatives; only thermal rates use differencing."""
    pressure, xa, xm, acetate, ratio = y
    temperature = fluxes(y, p)["temperature_k"]
    pair = guilds(temperature - 273.15, p.biology)
    plus = guilds(temperature - 273.15 + 1e-4, p.biology)
    minus = guilds(temperature - 273.15 - 1e-4, p.biology)
    biomass = np.array([xa, xm]) * p.enabled
    yields = np.array([g.yield_g_mol for g in pair])
    uptake = np.array([g.uptake(pressure) for g in pair])
    maintenance = np.array([g.maintenance for g in pair])
    a = np.array([g.assimilation_mol_g for g in pair])
    qp = np.array([g.rate_scale / g.km_pa if g.kinetics == "first_order" else
                   g.rate_scale * g.km_pa / (g.km_pa + pressure - g.threshold_pa) ** 2
                   if pressure > g.threshold_pa else 0. for g in pair])
    qt = np.array([(g.uptake(pressure) - h.uptake(pressure)) / 2e-4 for g, h in zip(plus, minus)])
    mt = np.array([(g.maintenance - h.maintenance) / 2e-4 for g, h in zip(plus, minus)])
    gross = yields * (uptake - maintenance)
    coefficients = 1 - a * yields * (gross > 0)
    catabolic = uptake - a * np.maximum(gross, 0)
    cp = qp * coefficients
    ct = qt - a * yields * (qt - mt) * (gross > 0)
    kr, ko = recycling_rates(temperature, p)
    inhibition = kr * p.acetate_lifetime_yr / p.acetate_fraction if p.acetate_fraction else 0.
    krt = kr * (1 - inhibition) / p.width_k if p.recycling_variant == "cold_limited" else 0.
    h, conversion = HOURS_PER_YEAR, inventory_to_ratio(p)
    matrix = np.zeros((5, 5))
    matrix[0, 0] = -h * (p.biology.exchange_mol_l_h_pa + qp @ biomass) / HENRY_30C_MOL_L_PA
    matrix[0, 1:3] = -h * uptake * p.enabled / HENRY_30C_MOL_L_PA
    matrix[0, 4] = -h * (qt @ biomass) * slope / HENRY_30C_MOL_L_PA
    for i in range(2):
        if p.enabled[i]:
            matrix[i + 1, 0] = h * biomass[i] * yields[i] * qp[i]
            matrix[i + 1, i + 1] = h * (gross[i] - p.biology.loss_h)
            matrix[i + 1, 4] = h * biomass[i] * yields[i] * (qt[i] - mt[i]) * slope
    matrix[3, 0] = h * biomass[0] * cp[0] / 4
    matrix[3, 1] = h * catabolic[0] * p.enabled[0] / 4
    matrix[3, 3] = -kr - ko
    matrix[3, 4] = (h * biomass[0] * ct[0] / 4 - krt * acetate) * slope
    matrix[4, 0] = conversion * h * biomass[1] * cp[1] / 4
    matrix[4, 2] = conversion * h * catabolic[1] * p.enabled[1] / 4
    matrix[4, 3] = conversion * kr
    matrix[4, 4] = conversion * (h * biomass[1] * ct[1] / 4 + krt * acetate) * slope - p.loss.slope(ratio)
    scales = np.maximum(np.abs(y), [10., 1e-4, 1e-4, 1e-5, .01])
    matrix = matrix * scales[np.newaxis, :] / scales[:, np.newaxis]
    active = [0, *[i + 1 for i, enabled in enumerate(p.enabled) if enabled], 3, 4]
    return matrix[np.ix_(active, active)]


def main():
    source = ROOT / "src/terra_prisca/haze_world/population_coupling.py"
    initial_hash = sha256(source.read_bytes()).hexdigest()
    p = reference()
    configurations = {
        "reference": p,
        "methanogen_only": replace(p, enabled=(False, True)),
        "no_recycling": replace(p, acetate_fraction=0.),
        "full_recycling": replace(p, acetate_fraction=1.),
        "cold_limited": replace(p, recycling_variant="cold_limited"),
        "long_lag": replace(p, acetate_lifetime_yr=1e4),
    }
    records = []
    for label, config in configurations.items():
        for state in equilibrium_states(config):
            y = state["y"]
            slopes = climate_slopes(state["r"], config.climate)
            at_vertex = np.any(np.isclose(state["r"], response(config.climate.case).ratios, rtol=0, atol=1e-10))
            eigenvalues = []
            differences = []
            for side, slope in ((-1, slopes[0]), (1, slopes[1])) if at_vertex else ((0, slopes[0]),):
                explicit = independent_jacobian(y, config, slope)
                numerical = jacobian(y, config, r_side=side)
                assert np.allclose(explicit, numerical, rtol=2e-5, atol=1e-7)
                eigenvalues.extend(np.linalg.eigvals(explicit))
                differences.append(float(np.max(np.abs(explicit - numerical) / (1e-7 + np.abs(explicit)))))
            maximum = float(max(np.asarray(eigenvalues).real))
            assert (maximum < 0) == state["stable"]
            invader = None
            if state["kind"] in ("acetogen", "methanogen") and all(config.enabled):
                i = 1 if state["kind"] == "acetogen" else 0
                invader = float(fluxes(y, config)["net_growth_yr"][i])
                assert min(abs(state["eigenvalues"] - invader)) < 1e-7
            rates = rhs(y, config)
            assert abs(rates[0]) < 1e-6 and max(abs(rates[1:])) < 1e-10
            records.append(dict(configuration=label, kind=state["kind"], temperature_k=state["t_k"],
                                ratio=state["r"], stable=state["stable"],
                                source_max_real_yr=state["max_real_yr"], independent_max_real_yr=maximum,
                                maximum_normalized_jacobian_difference=max(differences),
                                invader_growth_yr=invader, physical_rhs=list(rates)))

    resolution = []
    for n in (101, 501, 2001):
        resolution.append(dict(n_grid=n, states=[dict(kind=e["kind"], ratio=e["r"], stable=e["stable"])
                                                 for e in equilibrium_states(p, n)]))
    assert all([e["kind"] for e in item["states"]] == [e["kind"] for e in resolution[0]["states"]]
               for item in resolution)
    target = next(e for e in equilibrium_states(p) if e["kind"] == "mixed")
    control = next(e for e in equilibrium_states(configurations["methanogen_only"])
                   if e["kind"] == "methanogen" and e["stable"])
    invasions = []
    for seed in (1e-100,):
        y = control["y"].copy()
        y[1] = seed
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter("always")
            try:
                solution = integrate(y, p, 2000.)
            except (ValueError, RuntimeError) as error:
                item = dict(seed_gdw_l=seed, success=False, error=str(error))
            else:
                final = solution.y[:, -1]
                item = dict(seed_gdw_l=seed, duration_yr=2000., success=True, final_temperature_k=fluxes(final, p)["temperature_k"],
                            target_temperature_k=target["t_k"],
                            convergence_required=False,
                            minimum_log_biomass=list(np.min(solution.log_biomass, axis=1)),
                            log_coordinates_retained_finite=bool(np.all(np.isfinite(solution.log_biomass))),
                            maximum_final_relative_error=float(max(abs((final - target["y"]) / target["y"]))))
            item["warnings"] = sorted({str(message.message) for message in messages})
            invasions.append(item)
    assert initial_hash == sha256(source.read_bytes()).hexdigest(), "Source changed during audit; rerun against one version"
    files = (Path(__file__), source, ROOT / "src/terra_prisca/haze_world/two_guilds.py",
             ROOT / "src/terra_prisca/haze_world/darwinian.py",
             ROOT / "src/terra_prisca/haze_world/methane_budget.py",
             ROOT / "src/terra_prisca/haze_world/hydrogen_uptake.py",
             ROOT / "src/terra_prisca/haze_world/woodii1998.py",
             ROOT / "models/haze_world/evidence/kotsyurbenko2001_table2.csv",
             ROOT / "models/haze_response/arney2016/cases.csv",
             ROOT / "models/haze_response/arney2016/figure4.csv")
    result = dict(equilibrium_and_jacobian_checks=records, root_resolution_check=resolution,
                  rare_invasion_checks=invasions,
                  source_sha256={str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in files},
                  scope="Smooth/one-sided climate reference checks; no global root completeness or finite-population persistence claim")
    Path(__file__).with_name("population_coupling_review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(states_checked=len(records), rare_invasion_checks=invasions), indent=2))


if __name__ == "__main__":
    main()
