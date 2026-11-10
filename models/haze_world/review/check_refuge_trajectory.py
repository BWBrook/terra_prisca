"""Bounded Radau check using independent local log-biomass coordinates.

uv run python models/haze_world/review/check_refuge_trajectory.py

No censuses, auxiliary numerical seeds, clipping or refuge_integration
coordinate helpers are used inside the independent solve. The stated initial
invader inoculum is retained. Checks stop at ten years.
"""

from dataclasses import asdict, replace
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform

import numpy as np
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import population_coupling as single
from terra_prisca.haze_world import refuge_coupling as model
from terra_prisca.haze_world import refuge_equilibria as equilibria
from terra_prisca.haze_world import refuge_integration as production

ROOT = Path(__file__).resolve().parents[3]
BIOMASS = np.array([1, 2, 5, 6])
YEARS = 10.
TOLERANCES = dict(max_scaled_endpoint_difference=1e-4,
                  max_log_biomass_difference=1e-3,
                  max_instantaneous_redox_residual_mol_l_yr=1e-12,
                  max_integrated_redox_error_mol_l=1e-9)


def source_hashes():
    paths = [Path(__file__), *[ROOT / name for name in (
        "src/terra_prisca/haze_world/refuge_coupling.py",
        "src/terra_prisca/haze_world/refuge_equilibria.py",
        "src/terra_prisca/haze_world/refuge_integration.py",
        "src/terra_prisca/haze_world/population_coupling.py",
        "src/terra_prisca/haze_world/two_guilds.py",
        "src/terra_prisca/haze_world/hydrogen_uptake.py",
        "src/terra_prisca/haze_world/woodii1998.py",
        "src/terra_prisca/haze_world/methane_budget.py",
        "src/terra_prisca/haze_world/darwinian.py",
        "src/terra_prisca/haze_response/arney2016.py",
        "models/haze_response/arney2016/cases.csv",
        "models/haze_response/arney2016/figure4.csv",
        "models/haze_world/evidence/peters1998_chemostat.csv",
        "models/haze_world/evidence/kotsyurbenko2001_table2.csv")]]
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths}


def external_inventory_rate(y, p):
    f = model.fluxes(y, p)
    total = 4 * (f["abiotic_ratio_yr"] - f["methane_loss_ratio_yr"]) / single.inventory_to_ratio(p.base)
    for w, local in zip(p.weights, f["local"]):
        if w:
            total += w * (local["supply_h2_mol_l_yr"] - local["outlet_h2_mol_l_yr"]
                          - 4 * local["acetate_export_mol_l_yr"] - sum(local["biomass_export_h2_mol_l_yr"]))
    return float(total)


def initial_state(p):
    conditional = replace(p, base=replace(p.base, enabled=(False, True)))
    roots = equilibria.equilibrium_states(conditional, n_grid=201, stability=True)
    candidates = [e for e in roots if e["stability"] == "stable"
                  and all(e["y"][4*j+2] > 0 for j, w in enumerate(p.weights) if w)]
    if not candidates:
        raise RuntimeError("No supported conditional methanogen start for the bounded check")
    selected = max(candidates, key=lambda e: e["r"])
    y = selected["y"].copy()
    y[[1, 5]] = 1e-12
    return y, dict(qualifying_ratios=[e["r"] for e in candidates], selected_ratio=selected["r"],
                   protocol="Highest-r stable pure M control; A added at1e-12gDW/L in each habitat")


def decode(internal):
    physical = np.asarray(internal[:9], dtype=float).copy()
    physical[BIOMASS] = np.exp(physical[BIOMASS])
    return physical


def check_case(name, warm_fraction, contrast, dispersal):
    p = model.Refuge(replace(single.reference(), acetate_fraction=.5), warm_fraction, contrast, dispersal)
    initial, start = initial_state(p)
    internal = np.r_[initial, 0.]
    internal[BIOMASS] = np.log(initial[BIOMASS])

    def derivative(_, state):
        y = decode(state)
        rates = model.rhs(y, p)
        rates[BIOMASS] /= y[BIOMASS]
        return np.r_[rates, external_inventory_rate(y, p)]

    independent = solve_ivp(derivative, (0., YEARS), internal, method="Radau",
                            rtol=2e-10, atol=[1e-9,1e-10,1e-10,1e-20,1e-9,1e-10,1e-10,1e-20,1e-13,1e-13],
                            first_step=1e-5, max_step=.05, dense_output=True)
    if not independent.success:
        raise RuntimeError(f"Independent Radau failed for {name}: {independent.message}")
    physical = np.column_stack([decode(z) for z in independent.y.T])
    if np.any(~np.isfinite(physical)) or np.any(physical < 0):
        raise RuntimeError(f"Independent Radau accepted nonphysical stocks in {name}")
    if any("unsupported" in model.temperature_flags(y,p) for y in physical.T):
        raise RuntimeError(f"Independent Radau left supported physiology in {name}")
    result = production.integrate(initial,p,YEARS,census=None)
    if not result.success or result.status != "completed":
        raise RuntimeError(f"Production continuum check did not complete for {name}: {result.status}")
    if np.any(~np.isfinite(result.y)) or np.any(result.y < 0):
        raise RuntimeError(f"Production check accepted nonphysical stocks in {name}")
    before, after = physical[:,-1], result.y[:,-1]
    scales = np.maximum(np.maximum(abs(initial),abs(before)),[10.,1e-12,1e-12,1e-10,10.,1e-12,1e-12,1e-10,.01])
    difference = abs(after-before)
    scaled = float(np.max(difference/scales))
    log_difference = abs(result.log_biomass[:,:,-1].ravel()-independent.y[BIOMASS,-1])
    maximum_redox = float(max(abs(model.redox_residual(y,p)) for y in physical.T))
    inventory_delta = model.inventory(before,p)-model.inventory(initial,p)
    integrated_error = float(abs(inventory_delta-independent.y[9,-1]))
    assert scaled < TOLERANCES["max_scaled_endpoint_difference"],(name,scaled)
    assert max(log_difference) < TOLERANCES["max_log_biomass_difference"],(name,log_difference)
    assert maximum_redox < TOLERANCES["max_instantaneous_redox_residual_mol_l_yr"]
    assert integrated_error < TOLERANCES["max_integrated_redox_error_mol_l"]
    return dict(name=name, parameters=asdict(p), initial_y=initial.tolist(), start=start,
                independent_method="Radau; four separate local log-biomass coordinates, physical p/A/r and one observer integral",
                independent_rtol=2e-10, independent_max_step_yr=.05,
                independent_nfev=independent.nfev, independent_njev=independent.njev, independent_nlu=independent.nlu,
                production_nfev=result.metadata["nfev"], production_accepted_steps=result.metadata["accepted_steps"],
                independent_final_y=before.tolist(), production_final_y=after.tolist(),
                absolute_endpoint_difference=difference.tolist(), endpoint_scales=scales.tolist(),
                max_scaled_endpoint_difference=scaled, log_biomass_difference=log_difference.tolist(),
                max_log_biomass_difference=float(max(log_difference)),
                nonnegative_accepted_physical_stocks=True, strictly_positive_accepted_biomasses=True,
                supported_sampled_physiology=True,
                max_instantaneous_redox_residual_mol_l_yr=maximum_redox,
                integrated_external_inventory_mol_l=float(independent.y[9,-1]),
                physical_inventory_change_mol_l=float(inventory_delta),
                integrated_redox_error_mol_l=integrated_error)


def main():
    sources = source_hashes()
    cases = [check_case("warm_refuge",.05,8.6,1e-3),
             check_case("zero_dispersal_refuge",.05,8.6,0.),
             check_case("identical_zero_dispersal",.5,0.,0.)]
    if source_hashes() != sources:
        raise RuntimeError("Source changed during independent trajectory check; rerun after freeze")
    report = dict(duration_yr=YEARS, census="none; ten-year prefix before any census intervention",
                  tolerances=TOLERANCES, cases=cases, source_sha256=sources,
                  environment=dict(python=platform.python_version(), numpy=importlib.metadata.version("numpy"),
                                   scipy=importlib.metadata.version("scipy")),
                  scope="Bounded comparison of accepted positive continuum trajectories with an independent numerical method/coordinate system; not a full-grid or long-time qualification")
    Path(__file__).with_name("refuge_trajectory_check.json").write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    print(json.dumps([dict(name=r["name"],max_scaled_endpoint_difference=r["max_scaled_endpoint_difference"],
                          max_log_biomass_difference=r["max_log_biomass_difference"],
                          integrated_redox_error_mol_l=r["integrated_redox_error_mol_l"]) for r in cases],indent=2))


if __name__ == "__main__":
    main()
