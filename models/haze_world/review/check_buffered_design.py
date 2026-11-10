"""Independent three-habitat equilibrium, budget and Jacobian check.

Shares published/interpolated guild primitives and radiative inputs, but does not
call habitat_coupling's RHS or an equilibrium finder to construct the anchor.
"""

from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path
import platform

import numpy as np
import scipy
from scipy.optimize import least_squares, linear_sum_assignment

from terra_prisca.haze_world import population_coupling as source
from terra_prisca.haze_world.two_guilds import HENRY_30C_MOL_L_PA, guilds

ROOT = Path(__file__).resolve().parents[3]
WEIGHTS = np.array([.96, .02, .02])
RULES = (("tracking", 0.), ("buffered", 286.), ("buffered", 278.))
DISPERSAL = .001


def source_hashes():
    paths=[Path(__file__), *[ROOT/name for name in (
        "src/terra_prisca/haze_world/habitat_coupling.py",
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
        "models/haze_world/evidence/kotsyurbenko2001_table2.csv", "uv.lock")]]
    return {str(path.relative_to(ROOT)):sha256(path.read_bytes()).hexdigest() for path in paths}


def local_temperatures(r, base, rules=RULES):
    global_temperature = float(source.temperature_k(r, base.climate))
    return np.array([global_temperature + value if rule == "tracking" else value for rule, value in rules])


def primitive_flows(y, base, weights=WEIGHTS, rules=RULES, dispersal=DISPERSAL):
    n = len(weights)
    state = np.asarray(y, dtype=float).reshape(-1)
    stocks = state[:-1].reshape(n, 4)
    r = float(state[-1])
    ts = local_temperatures(r, base, rules)
    biomass = stocks[:, 1:3] * base.enabled
    uptake = np.empty((n, 2))
    synthesis = np.empty((n, 2))
    allocation = np.empty((n, 2))
    krec = np.empty(n)
    kother = np.empty(n)
    for j, t in enumerate(ts):
        pair = guilds(float(t - 273.15), base.biology)
        if base.activity_feedback == "products":
            factors = ((max(stocks[j, 3], 0.) / base.acetate_reference_mol_l) ** .25,
                       (max(r, 0.) * source.co2_pressure_pa(base.climate.case) / base.methane_reference_pa) ** .25)
            pair = tuple(replace(g, threshold_pa=g.threshold_pa * factor) for g, factor in zip(pair, factors))
        uptake[j] = [g.uptake(stocks[j, 0]) for g in pair]
        synthesis[j] = [g.yield_g_mol * (u - g.maintenance) for g, u in zip(pair, uptake[j])]
        allocation[j] = [g.assimilation_mol_g for g in pair]
        krec[j], kother[j] = source.recycling_rates(float(t), base)
    hours = source.HOURS_PER_YEAR
    used = uptake * biomass * hours
    catabolic = used - allocation * np.maximum(synthesis, 0.) * biomass * hours
    growth = (synthesis - base.biology.loss_h) * hours
    exchange = dispersal * (weights @ biomass - biomass)
    input_h = source.supply_h2(base) * hours
    outlet = base.biology.exchange_mol_l_h_pa * (stocks[:, 0] - base.biology.atmosphere_pa) * hours
    recycled = krec * stocks[:, 3]
    exported = kother * stocks[:, 3]
    derivative = np.zeros_like(state)
    blocks = derivative[:-1].reshape(n, 4)
    blocks[:, 0] = (input_h - used.sum(axis=1) - outlet) / HENRY_30C_MOL_L_PA
    blocks[:, 1:3] = growth * biomass + exchange
    blocks[:, 3] = catabolic[:, 0] / 4 - recycled - exported
    conversion = source.inventory_to_ratio(base)
    abiotic = source.atmosphere(base.climate.case)["flux_to_ratio_per_yr"] * base.climate.abiotic_flux
    loss = float(base.loss.rate(r))
    methane = catabolic[:, 1] / 4 + recycled
    derivative[-1] = conversion * (weights @ methane) + abiotic - loss
    biomass_export = (allocation * (base.biology.loss_h + np.maximum(-synthesis, 0.)) * biomass * hours).sum(axis=1)
    inventory_rate = weights @ (HENRY_30C_MOL_L_PA * blocks[:, 0] +
        (allocation * blocks[:, 1:3]).sum(axis=1) + 4 * blocks[:, 3]) + 4 * derivative[-1] / conversion
    external_rate = weights @ (input_h - outlet - 4 * exported - biomass_export) + 4 * (abiotic - loss) / conversion
    return dict(rhs=derivative, temperatures_k=ts, growth_yr=growth, exchange=exchange,
                uptake_per_gdw_h=uptake, catabolic_h2_yr=catabolic, k_total=krec+kother,
                inventory_rate=float(inventory_rate), external_rate=float(external_rate),
                redox_residual=float(inventory_rate-external_rate))


def rhs(y, base):
    return primitive_flows(y, base)["rhs"]


def equilibrium_anchor(base):
    def decode(z):
        y = np.zeros(13)
        blocks = y[:-1].reshape(3, 4)
        blocks[:, 0] = z[:3] * 100.
        blocks[:, 1:3] = np.exp(z[3:9].reshape(3, 2))
        y[-1] = z[-1] * .2
        first = primitive_flows(y, base)
        blocks[:, 3] = first["catabolic_h2_yr"][:, 0] / (4 * first["k_total"])
        return y

    def residual(z):
        y = decode(z)
        f = primitive_flows(y, base)
        blocks = f["rhs"][:-1].reshape(3, 4)
        x = y[:-1].reshape(3, 4)[:, 1:3]
        return np.r_[blocks[:, 0] * HENRY_30C_MOL_L_PA / (source.supply_h2(base) * source.HOURS_PER_YEAR),
                     (blocks[:, 1:3] / x / (base.biology.loss_h * source.HOURS_PER_YEAR)).reshape(-1),
                     f["rhs"][-1] / 3e-5]

    initial = np.r_[np.array([22.4863, 19.977, 27.615]) / 100.,
                    np.log(np.array([[.0006, .00033], [1e-7, .0006325], [.001256, 1e-7]])).reshape(-1),
                    .195 / .2]
    result = least_squares(residual, initial, bounds=(np.r_[np.zeros(3), np.full(6, -80.), 1e-10],
        np.r_[np.full(3, 3.1), np.full(6, 0.), 1.8]),
        xtol=2e-14, ftol=2e-14, gtol=2e-14, max_nfev=3000)
    error = float(max(abs(residual(result.x))))
    if not result.success or error > 1e-9:
        raise RuntimeError(f"Independent equilibrium root failed: {result.message}, residual={error}")
    return decode(result.x), error, result.nfev


def jacobian(y, base):
    scales = np.maximum(abs(y), [10., 1e-4, 1e-4, 1e-5] * 3 + [.01])
    result = np.empty((13, 13))
    for j in range(13):
        step = scales[j] * 3e-6
        delta = np.eye(13)[j] * step
        result[:, j] = (rhs(y+delta, base)-rhs(y-delta, base))/(2*step)*scales[j]/scales
    return result


def main():
    before=source_hashes()
    from terra_prisca.haze_world import habitat_coupling as implemented
    base = replace(source.reference(), acetate_fraction=.5)
    y, residual, nfev = equilibrium_anchor(base)
    p = implemented.Habitats(base, tuple(implemented.Patch(name, float(w), rule, value)
        for name, w, (rule, value) in zip(("bulk", "warm", "cold"), WEIGHTS, RULES)), DISPERSAL)
    perturbation = np.array([1.001, .999, 1.002, .998] * 3 + [1.000001])
    perturbed = y * perturbation
    checks=[]
    for activity in ("fixed", "products"):
        variant=replace(base, activity_feedback=activity)
        variant_p=replace(p, base=variant)
        expected=primitive_flows(perturbed,variant)
        observed=implemented.rhs(perturbed,variant_p)
        scales=np.maximum(abs(expected["rhs"]), [1.,1e-5,1e-5,1e-5]*3+[1e-6])
        difference=float(max(abs(observed-expected["rhs"])/scales))
        assert difference<1e-10
        assert abs(expected["redox_residual"])<1e-14
        assert np.max(abs(WEIGHTS @ expected["exchange"]))<1e-18
        checks.append(dict(activity=activity, maximum_scaled_rhs_difference=difference,
                           redox_residual=expected["redox_residual"],
                           maximum_weighted_exchange_residual=float(np.max(abs(WEIGHTS @ expected["exchange"])))))
    expected_eigenvalues=np.linalg.eigvals(jacobian(y,base))
    observed_eigenvalues=np.linalg.eigvals(implemented.jacobian(y,p))
    cost=abs(expected_eigenvalues[:,None]-observed_eigenvalues[None,:])/np.maximum(1.,abs(expected_eigenvalues[:,None]))
    rows,cols=linear_sum_assignment(cost)
    spectral_error=float(max(cost[rows,cols]));assert spectral_error<1e-5
    assert max(expected_eigenvalues.real)<0
    assert source_hashes()==before, "Inputs changed during the independent check"
    report=dict(scope="Independent algebraic three-patch equilibrium, perturbed RHS, redox and full13D spectra; common source kinetics, constants and radiative interpolation; no independent empirical calibration",
        parameters=asdict(p),state_y=y.tolist(),global_temperature_k=float(source.temperature_k(y[-1],base.climate)),
        temperatures_k=local_temperatures(y[-1],base).tolist(),root_scaled_residual=residual,root_nfev=nfev,
        maximum_real_eigenvalue_yr=float(max(expected_eigenvalues.real)),matched_spectral_error=spectral_error,
        checks=checks,source_sha256=before,
        versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__))
    Path(__file__).with_name('buffered_design_check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
