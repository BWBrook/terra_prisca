"""Independent fixed-product partition and conservation checks; no trajectories.

uv run python models/haze_world/review/check_refuge_design.py
"""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, root

from terra_prisca.haze_world.population_coupling import (
    HOURS_PER_YEAR, inventory_to_ratio, reference, supply_h2, switch_temperatures,
)
from terra_prisca.haze_world.methane_budget import atmosphere, response, temperature_k
from terra_prisca.haze_world.two_guilds import HENRY_30C_MOL_L_PA, guilds

BASE = reference()
H = HOURS_PER_YEAR
GAMMA = inventory_to_ratio(BASE)
J = supply_h2(BASE)
ABIOTIC = atmosphere(BASE.climate.case)["flux_to_ratio_per_yr"] * BASE.climate.abiotic_flux
SWITCH = switch_temperatures(BASE.biology)[0]
LOW, HIGH = 277.15, 303.15


def local(y, t, f):
    pressure, xa, xm, acetate = y
    pair = guilds(float(t - 273.15), BASE.biology)
    biomass = np.array([xa, xm])
    uptake = np.array([g.uptake(pressure) for g in pair])
    synthesis = np.array([g.yield_g_mol * (q - g.maintenance) for g, q in zip(pair, uptake)])
    allocation = np.array([g.assimilation_mol_g for g in pair])
    used = H * uptake * biomass
    catabolic = used - H * allocation * np.maximum(synthesis, 0) * biomass
    outlet = H * BASE.biology.exchange_mol_l_h_pa * (pressure - BASE.biology.atmosphere_pa)
    recycle = f * acetate / BASE.acetate_lifetime_yr
    export = (1 - f) * acetate / BASE.acetate_lifetime_yr
    derivative = np.r_[(H * J - sum(used) - outlet) / HENRY_30C_MOL_L_PA,
                       H * (synthesis - BASE.biology.loss_h) * biomass,
                       catabolic[0] / 4 - recycle - export]
    return dict(rhs=derivative, methane=catabolic[1] / 4 + recycle, allocation=allocation,
                outlet=outlet, acetate_export=export,
                biomass_export=H * allocation * (BASE.biology.loss_h + np.maximum(-synthesis, 0)) * biomass)


def rhs(y, f, warm, contrast, dispersal):
    weights = np.array([1 - warm, warm])
    t = float(temperature_k(y[8], BASE.climate))
    temperatures = t + np.array([-warm, 1 - warm]) * contrast
    details = [local(y[4*j:4*j+4], temperatures[j], f) for j in range(2)]
    derivative = np.r_[details[0]["rhs"], details[1]["rhs"],
                       GAMMA * sum(w*x["methane"] for w, x in zip(weights, details)) + ABIOTIC - BASE.loss.rate(y[8])]
    for i in (1, 2):
        difference = y[i + 4] - y[i]
        derivative[i] += dispersal * warm * difference
        derivative[i + 4] -= dispersal * (1 - warm) * difference
    return derivative


def redox(y, f, warm, contrast, dispersal):
    t = float(temperature_k(y[8], BASE.climate))
    weights = np.array([1 - warm, warm])
    temperatures = t + np.array([-warm, 1 - warm]) * contrast
    derivative = rhs(y, f, warm, contrast, dispersal)
    stored, external = 4 * derivative[8] / GAMMA, 4 * (ABIOTIC - BASE.loss.rate(y[8])) / GAMMA
    for j, weight in enumerate(weights):
        details = local(y[4*j:4*j+4], temperatures[j], f)
        dy = derivative[4*j:4*j+4]
        stored += weight * (HENRY_30C_MOL_L_PA * dy[0] + details["allocation"] @ dy[1:3] + 4 * dy[3])
        external += weight * (H * J - details["outlet"] - 4 * details["acetate_export"] - sum(details["biomass_export"]))
    return float(stored - external)


def resident(t, index, f):
    g = guilds(float(t - 273.15), BASE.biology)[index]
    pressure = g.rstar(BASE.biology.loss_h)
    q = g.maintenance + BASE.biology.loss_h / g.yield_g_mol
    captured = J - BASE.biology.exchange_mol_l_h_pa * (pressure - BASE.biology.atmosphere_pa)
    if not np.isfinite(pressure) or captured <= 0:
        raise ValueError("Resident is not viable")
    biomass = np.zeros(2)
    biomass[index] = captured / q
    factor = 1 - g.assimilation_mol_g * BASE.biology.loss_h / q
    acetate = H * captured * factor * BASE.acetate_lifetime_yr / 4 if index == 0 else 0.
    return np.r_[pressure, biomass, acetate]


def partition(r, f, warm, contrast):
    t = float(temperature_k(r, BASE.climate))
    cold, hot = t - warm * contrast, t + (1 - warm) * contrast
    return np.r_[resident(cold, 0, f), resident(hot, 1, f), r]


def equivalent_ratio(t, index):
    y = resident(t, index, 0.)
    g = guilds(float(t - 273.15), BASE.biology)[index]
    q = g.maintenance + BASE.biology.loss_h / g.yield_g_mol
    return float(GAMMA * H * q * y[index + 1] * (1 - g.assimilation_mol_g * BASE.biology.loss_h / q) * BASE.loss.lifetime_yr / 4)


def eigenvalues(y, f, warm, contrast, dispersal):
    scales = np.maximum(np.abs(y), [10., 1e-4, 1e-4, 1e-5, 10., 1e-4, 1e-4, 1e-5, .01])
    jac = np.empty((9, 9))
    for j in range(9):
        h = scales[j] * 1e-5
        delta = np.eye(9)[j] * h
        jac[:, j] = (rhs(y + delta, f, warm, contrast, dispersal) - rhs(y - delta, f, warm, contrast, dispersal)) / (2*h) * scales[j] / scales
    return np.linalg.eigvals(jac)


def source_lower_bound(index, low, high):
    knots = np.unique(np.r_[np.arange(low, high, .025), low, high,
                            np.array([277.15, 283.15, 288.15, 293.15, 298.15, 303.15])])
    knots = knots[(knots >= low) & (knots <= high)]
    result = np.inf
    for a, b in zip(knots[:-1], knots[1:]):
        pair = [guilds(float(t - 273.15), BASE.biology)[index] for t in (a, b)]
        q = [g.maintenance + BASE.biology.loss_h / g.yield_g_mol for g in pair]
        # Within source interpolation segments capacities/Km are linear, and
        # maintenance/thresholds monotone; endpoint enclosures are conservative.
        rate_min = min(g.rate_scale for g in pair)
        q_max, q_min = max(q), min(q)
        assert rate_min > q_max
        rstar_upper = max(g.threshold_pa for g in pair) + max(g.km_pa for g in pair) * q_max / (rate_min - q_max)
        captured_lower = J - BASE.biology.exchange_mol_l_h_pa * (rstar_upper - BASE.biology.atmosphere_pa)
        b_lower = 1 - pair[0].assimilation_mol_g * BASE.biology.loss_h / q_min
        result = min(result, GAMMA * H * captured_lower * b_lower * BASE.loss.lifetime_yr / 4)
    return float(result)


def main():
    tgrid = np.linspace(LOW, HIGH, 5201)
    sources = np.array([[equivalent_ratio(t, i) for i in (0, 1)] for t in tgrid])
    ratios = np.unique(np.r_[np.linspace(0, .31, 1001), response(BASE.climate.case).ratios])
    temperatures = temperature_k(ratios, BASE.climate)
    detected, coarse, examples = {}, {}, {}
    for f in (0., .5, .9):
        count = coarse_count = 0
        best = None
        for warm in np.arange(.01, 1., .01):
            for contrast in np.arange(.5, 30.01, .5):
                cold = temperatures - warm * contrast
                hot = temperatures + (1 - warm) * contrast
                valid = (cold >= LOW) & (hot <= HIGH) & (cold < SWITCH) & (hot > SWITCH)
                values = (f * (1-warm) * np.interp(cold, tgrid, sources[:, 0]) +
                          warm * np.interp(hot, tgrid, sources[:, 1]) + ABIOTIC * BASE.loss.lifetime_yr - ratios)
                brackets = np.flatnonzero(valid[:-1] & valid[1:] & (values[:-1] * values[1:] < 0))
                for j in brackets:
                    balance = lambda r: rhs(partition(r, f, warm, contrast), f, warm, contrast, 0.)[8]
                    r = brentq(balance, ratios[j], ratios[j+1], xtol=1e-14)
                    y = partition(r, f, warm, contrast)
                    global_t = float(temperature_k(r, BASE.climate))
                    cold, hot = global_t - warm * contrast, global_t + (1-warm) * contrast
                    if not LOW <= cold < SWITCH < hot <= HIGH:
                        continue
                    count += 1
                    if np.any(np.isclose(warm, [.1, .5, .9])) and np.any(np.isclose(contrast, [0, 5, 10, 15, 20, 30])):
                        coarse_count += 1
                    if best is None or abs(global_t - 282) < abs(best["global_k"] - 282):
                        best = dict(fraction=f, warm_fraction=float(warm), contrast_k=float(contrast),
                                    ratio=float(r), global_k=global_t, cold_k=float(cold), warm_k=float(hot), state=y.tolist())
        detected[str(f)], coarse[str(f)], examples[str(f)] = count, coarse_count, best
    for example in [x for x in examples.values() if x is not None]:
        f, warm, contrast = example["fraction"], example["warm_fraction"], example["contrast_k"]
        y = np.array(example["state"])
        eig = eigenvalues(y, f, warm, contrast, 0.)
        assert max(eig.real) < 0
        example["max_real_eigenvalue_yr"] = float(max(eig.real))
        example["max_absolute_rhs"] = float(max(abs(rhs(y, f, warm, contrast, 0.))))
        scales = np.array([30., .001, .001, .001, 30., .001, .001, .001, .2])
        residual_scales = np.array([H*J/HENRY_30C_MOL_L_PA, .001*H*BASE.biology.loss_h, .001*H*BASE.biology.loss_h, .001,
                                   H*J/HENRY_30C_MOL_L_PA, .001*H*BASE.biology.loss_h, .001*H*BASE.biology.loss_h, .001, .3/BASE.loss.lifetime_yr])
        solution = root(lambda z: rhs(z*scales, f, warm, contrast, 1e-3) / residual_scales, y/scales, tol=1e-10)
        state = solution.x * scales
        eig_d = eigenvalues(state, f, warm, contrast, 1e-3)
        assert solution.success and np.all(state > 0) and max(abs(solution.fun)) < 1e-9 and max(eig_d.real) < 0
        example["dispersal_1e3"] = dict(success=bool(solution.success), positive_state=bool(np.all(state > 0)),
            max_scaled_residual=float(max(abs(solution.fun))), state=state.tolist(),
            max_real_eigenvalue_yr=float(max(eig_d.real)))
        perturbed = state * [1.1, .9, 1.2, .8, .9, 1.1, .8, 1.2, 1.00001]
        example["independent_redox_residual"] = redox(perturbed, f, warm, contrast, .1)
        assert abs(example["independent_redox_residual"]) < 1e-12
    bound_a = source_lower_bound(0, LOW, SWITCH)
    bound_m = source_lower_bound(1, SWITCH, HIGH)
    ratio_lower = min(.9*bound_a, bound_m) + ABIOTIC*BASE.loss.lifetime_yr
    knots = np.r_[ratio_lower, .31, response(BASE.climate.case).ratios]
    knots = knots[knots >= ratio_lower]
    upper_global_t = float(max(temperature_k(knots, BASE.climate)))
    growth = lambda t: np.array([g.net_growth(30., BASE.biology.loss_h)*H for g in guilds(t-273.15, BASE.biology)])
    result = dict(switch_k=SWITCH, detected_measured_protected_partitions=detected,
                  detected_on_coarse_invasion_grid=coarse, examples=examples,
                  scan=dict(warm_fraction="0.01:0.01:0.99", contrast_k="0.5:0.5:30", ratio_bracket_points=len(ratios),
                            scope="Detected exact-refined roots after interpolated screening; not an exhaustive root census"),
                  f09_measured_exclusion_bound=dict(dispersal_yr=0.,
                      scope="Pure protected partition at zero dispersal; not a general exclusion theorem for finite-d coexistence",
                      acetogen_cold_ratio_source_lower=bound_a,
                      methanogen_warm_ratio_source_lower=bound_m, global_ratio_lower=ratio_lower,
                      global_temperature_upper_k=upper_global_t, measured_minimum_k=LOW,
                      protected_partition_inside_measured_range_impossible=upper_global_t < LOW),
                  large_d_counterexample=dict(global_temperature_k=290., local_temperatures_k=[285.,295.],
                      same_pressure_pa=30., mean_local_growth_yr=((growth(285.)+growth(295.))/2).tolist(),
                      growth_at_mean_temperature_yr=growth(290.).tolist()),
                  source_sha256={str(p.relative_to(Path(__file__).resolve().parents[3])):sha256(p.read_bytes()).hexdigest()
                      for p in [Path(__file__), *[Path(__file__).resolve().parents[3]/name for name in (
                          "src/terra_prisca/haze_world/two_guilds.py", "src/terra_prisca/haze_world/methane_budget.py",
                          "src/terra_prisca/haze_world/population_coupling.py", "src/terra_prisca/haze_world/hydrogen_uptake.py",
                          "src/terra_prisca/haze_world/woodii1998.py", "src/terra_prisca/haze_response/arney2016.py",
                          "models/haze_response/arney2016/cases.csv", "models/haze_response/arney2016/figure4.csv",
                          "models/haze_world/evidence/peters1998_chemostat.csv", "models/haze_world/evidence/kotsyurbenko2001_table2.csv")]]})
    Path(__file__).with_name("refuge_design_check.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({k:result[k] for k in ("detected_measured_protected_partitions","detected_on_coarse_invasion_grid","examples","f09_measured_exclusion_bound","large_d_counterexample")},indent=2))


if __name__ == "__main__":
    main()
