"""Equilibrium candidates for the explicit two-habitat methane model.

The fixed-product, zero-dispersal branches are reduced algebraically. Positive
dispersal uses continuation in a total-biomass/allocation representation. Finite
root searches do not establish a globally exhaustive inventory of attractors.
"""

from dataclasses import replace
from itertools import product

import numpy as np
from scipy.optimize import brentq, least_squares
from scipy.special import expit

from . import population_coupling as core
from . import refuge_coupling as model
from .methane_budget import response, temperature_k

BIOMASS_SCALE = 1e-3
ACETATE_SCALE = 1e-3


def ratio_grid(p, n_grid=301):
    grid = core._ratio_grid(p.base, n_grid)
    hi = float(grid[-1])
    knots = np.unique(np.r_[0., response(p.base.climate.case).ratios, hi])
    temperatures = np.array([float(temperature_k(r, p.base.climate)) for r in knots])
    additions = []
    local_knots = [*model.physiology_bounds(p), 277.15, 283.15, 288.15, 293.15, 298.15,
                   *core.switch_temperatures(p.base.biology)]
    for offset, weight in zip(p.offsets, p.weights):
        if weight == 0:
            continue
        for local in local_knots:
            target = local - offset
            for a, b, ta, tb in zip(knots[:-1], knots[1:], temperatures[:-1], temperatures[1:]):
                if a > hi or b <= a:
                    continue
                if ta == target:
                    additions.append(a)
                if tb == target:
                    additions.append(b)
                if (ta - target) * (tb - target) < 0:
                    additions.append(brentq(lambda r: float(temperature_k(r, p.base.climate)) - target,
                                            a, b, xtol=1e-14))
    return np.unique(np.r_[grid, additions])


def _safe_temperatures(r, p):
    ts = float(temperature_k(r, p.base.climate)) + p.offsets
    low, high = model.physiology_bounds(p)
    if any(w > 0 and not low <= t <= high for t, w in zip(ts, p.weights)):
        return None
    return ts


def _local_fixed(r, temperature, p, kind):
    base = p.base
    p0 = base.biology.atmosphere_pa + core.supply_h2(base) / base.biology.exchange_mol_l_h_pa
    if kind == "empty":
        return np.array([p0, 0., 0., 0.])
    index = 0 if kind == "acetogen" else 1
    if not base.enabled[index]:
        return None
    guild = core.guilds(float(temperature - 273.15), base.biology)[index]
    pressure = guild.rstar(base.biology.loss_h)
    captured = core.supply_h2(base) - base.biology.exchange_mol_l_h_pa * (pressure - base.biology.atmosphere_pa)
    if not np.isfinite(pressure) or captured <= 0:
        return None
    biomass = np.zeros(2)
    biomass[index] = captured / float(guild.uptake(pressure))
    state = np.r_[pressure, biomass, 0., r]
    local = core.fluxes_at_temperature(state, base, float(temperature))
    state[3] = local["acetate_production_mol_l_yr"] / (local["k_rec_yr"] + local["k_other_yr"])
    return state[:4]


def _branch(r, p, kinds):
    temperatures = _safe_temperatures(r, p)
    if temperatures is None:
        return None
    blocks = []
    for j, (weight, kind) in enumerate(zip(p.weights, kinds)):
        block = np.zeros(4) if weight == 0 else _local_fixed(r, temperatures[j], p, kind)
        if block is None:
            return None
        blocks.append(block)
    return np.r_[*blocks, r]


def _temperature_roots(target, p, grid):
    return core._roots(lambda r: float(temperature_k(r, p.base.climate)) - target, grid, 1e-10)


def _mixed_patch(r, temperature, p, share):
    base = p.base
    pair = core.guilds(float(temperature - 273.15), base.biology)
    pressure = pair[0].rstar(base.biology.loss_h)
    if abs(pressure - pair[1].rstar(base.biology.loss_h)) > 1e-6:
        return None
    captured = core.supply_h2(base) - base.biology.exchange_mol_l_h_pa * (pressure - base.biology.atmosphere_pa)
    if captured <= 0:
        return None
    uptake = np.array([g.maintenance + base.biology.loss_h / g.yield_g_mol for g in pair])
    state = np.r_[pressure, captured * np.array([share, 1 - share]) / uptake, 0., r]
    f = core.fluxes_at_temperature(state, base, float(temperature))
    state[3] = f["acetate_production_mol_l_yr"] / (f["k_rec_yr"] + f["k_other_yr"])
    return state[:4]


def _zero_dispersal(p, n_grid):
    if p.base.activity_feedback != "fixed":
        raise ValueError("The algebraic zero-dispersal enumeration requires fixed activities")
    grid = ratio_grid(p, n_grid)
    modes = ["empty", *[name for name, enabled in zip(("acetogen", "methanogen"), p.base.enabled) if enabled]]
    candidates = []
    choices = [modes if w > 0 else ["empty"] for w in p.weights]
    for kinds in product(*choices):
        def balance(r):
            y = _branch(r, p, kinds)
            return model.rhs(y, p)[8] if y is not None else np.nan

        for r in core._roots(balance, grid, 1e-14):
            state = _branch(r, p, kinds)
            if state is not None:
                candidates.append((state, False))
    if all(p.base.enabled):
        for mixed, weight in enumerate(p.weights):
            if weight == 0:
                continue
            other = 1 - mixed
            for switch in core.switch_temperatures(p.base.biology):
                for r in _temperature_roots(switch - p.offsets[mixed], p, grid):
                    ts = _safe_temperatures(r, p)
                    if ts is None:
                        continue
                    for other_kind in (modes if p.weights[other] else ["empty"]):
                        block_other = (np.zeros(4) if p.weights[other] == 0 else
                                       _local_fixed(r, ts[other], p, other_kind))
                        if block_other is None:
                            continue
                        endpoints = []
                        for share in (0., 1.):
                            mixed_block = _mixed_patch(r, ts[mixed], p, share)
                            if mixed_block is None:
                                break
                            blocks = [None, None]
                            blocks[mixed], blocks[other] = mixed_block, block_other
                            endpoints.append(np.r_[*blocks, r])
                        if len(endpoints) != 2:
                            continue
                        left, right = [model.rhs(y, p)[8] for y in endpoints]
                        if abs(right - left) < 1e-16:
                            continue
                        share = -left / (right - left)
                        if 0 <= share <= 1:
                            candidates.append((endpoints[0] + share * (endpoints[1] - endpoints[0]), False))
        if p.contrast_k == 0:
            for e in core.equilibrium_states(p.base, n_grid=n_grid):
                if e["kind"] == "mixed":
                    candidates.append((model.embed_single(e["y"], p), bool(np.all(p.weights > 0))))
            if np.all(p.weights > 0):
                switches = core.switch_temperatures(p.base.biology)
                candidates = [(y, family or bool(np.all(p.weights @ y[model.BIOMASS_INDICES] > 0)
                               and any(abs(float(temperature_k(y[8], p.base.climate)) - switch) < 1e-7
                                       for switch in switches))) for y, family in candidates]
    return _deduplicate(candidates)


def _deduplicate(candidates):
    kept = []
    scales = np.array([100., BIOMASS_SCALE, BIOMASS_SCALE, ACETATE_SCALE,
                       100., BIOMASS_SCALE, BIOMASS_SCALE, ACETATE_SCALE, .2])
    for y, family in candidates:
        if any(np.max(abs(y - old) / scales) < 1e-7 for old, _ in kept):
            continue
        if np.any(y < 0) or not np.all(np.isfinite(y)):
            continue
        kept.append((y, family))
    return kept


def scaled_residual(y, p):
    rates = model.rhs(y, p)
    supply = core.supply_h2(p.base) * core.HOURS_PER_YEAR
    scales = np.array([supply / core.HENRY_30C_MOL_L_PA, BIOMASS_SCALE * core.HOURS_PER_YEAR * p.base.biology.loss_h,
                       BIOMASS_SCALE * core.HOURS_PER_YEAR * p.base.biology.loss_h, supply / 4] * 2
                      + [core.inventory_to_ratio(p.base) * supply / 4])
    return rates / scales


def _positive_root(seed, p):
    active = np.flatnonzero(p.weights > 0)
    if len(active) == 1:
        return None
    present = [i for i, enabled in enumerate(p.base.enabled)
               if enabled and np.dot(p.weights, seed[model.BIOMASS_INDICES[:, i]]) > 1e-18]
    if not present:
        return None
    has_acetate = 0 in present
    wc, ww = p.weights
    d = p.dispersal_yr
    stocks = seed[model.BIOMASS_INDICES].copy()
    local = model.fluxes(seed, replace(p, dispersal_yr=0.))["local"]
    for i in present:
        for j in (0, 1):
            if stocks[j, i] == 0:
                growth = local[j]["net_growth_yr"][i]
                stocks[j, i] = max(d * p.weights[1 - j] * stocks[1 - j, i] /
                                   max(abs(growth) + d * p.weights[1 - j], 1e-3), 1e-16)
    acetate_seeds = seed[[3, 7]].copy()
    if has_acetate:
        for j in (0, 1):
            state = np.r_[seed[4 * j], stocks[j], 0., seed[8]]
            temperature = float(model.temperatures(seed, p)[j])
            def acetate_balance(value):
                state[3] = value
                f = core.fluxes_at_temperature(state, p.base, temperature)
                return value - f["acetate_production_mol_l_yr"] / (f["k_rec_yr"] + f["k_other_yr"])
            maximum = -acetate_balance(0.)
            acetate_seeds[j] = (brentq(acetate_balance, 0., maximum, xtol=1e-20)
                                 if maximum > 0 else 0.)
    values = [seed[0] / 100., seed[4] / 100.]
    for i in present:
        total = float(np.dot(p.weights, stocks[:, i]))
        scaled = total / BIOMASS_SCALE
        values.append(scaled + np.log(-np.expm1(-scaled)))
        values.append(np.log(wc * stocks[0, i]) - np.log(ww * stocks[1, i]))
    if has_acetate:
        for acetate in acetate_seeds:
            scaled = acetate / ACETATE_SCALE
            values.append(scaled + np.log(-np.expm1(-scaled)) if p.base.activity_feedback == "products" else scaled)
    values.append(seed[8] / .2)

    def decode(z):
        y = np.zeros(9)
        y[0], y[4], y[8] = z[0] * 100., z[1] * 100., z[-1] * .2
        index = 2
        fractions = []
        for guild in present:
            total = BIOMASS_SCALE * np.logaddexp(0., z[index])
            cold, warm = float(expit(z[index + 1])), float(expit(-z[index + 1]))
            y[model.BIOMASS_INDICES[0, guild]] = total * cold / wc
            y[model.BIOMASS_INDICES[1, guild]] = total * warm / ww
            fractions.append((cold, warm))
            index += 2
        if has_acetate:
            if p.base.activity_feedback == "products":
                y[3], y[7] = np.logaddexp(0., z[index:index + 2]) * ACETATE_SCALE
            else:
                y[3], y[7] = z[index:index + 2] * ACETATE_SCALE
        return y, fractions

    supply = core.supply_h2(p.base) * core.HOURS_PER_YEAR
    scale_growth = core.HOURS_PER_YEAR * p.base.biology.loss_h

    def equations(z):
        y, allocations = decode(z)
        f = model.fluxes(y, p, trial_extension=True)
        equations = [(f["local"][j]["supply_h2_mol_l_yr"] -
                      sum(f["local"][j]["uptake_h2_mol_l_yr"]) -
                      f["local"][j]["outlet_h2_mol_l_yr"]) / supply for j in (0, 1)]
        for i, (cold, warm) in zip(present, allocations):
            gc, gw = [local["net_growth_yr"][i] for local in f["local"]]
            equations.extend([(cold * gc + warm * gw) / scale_growth,
                              cold * warm * (gc - gw) / d + wc - cold])
        if has_acetate:
            equations.extend([(local["acetate_production_mol_l_yr"] - local["acetate_recycling_mol_l_yr"]
                               - local["acetate_export_mol_l_yr"]) / (supply / 4) for local in f["local"]])
        equations.append((f["methane_source_ratio_yr"] - f["methane_loss_ratio_yr"]) /
                         (core.inventory_to_ratio(p.base) * supply / 4))
        return np.asarray(equations)

    solution = least_squares(equations, np.asarray(values), jac="3-point", diff_step=1e-5,
                             x_scale="jac", ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=300)
    y, _ = decode(solution.x)
    if (not np.all(np.isfinite(y)) or np.any(y < 0)
            or "unsupported" in model.temperature_flags(y, p)):
        return None
    if np.max(np.abs(equations(solution.x))) > 2e-7:
        return None
    if any(np.dot(p.weights, y[model.BIOMASS_INDICES[:, i]]) < 1e-14 for i in present):
        return None
    if np.max(np.abs(scaled_residual(y, p))) > 2e-7:
        return None
    return y


def _product_zero_root(seed, p):
    active = np.flatnonzero(p.weights > 0)
    present = {j: [i for i, enabled in enumerate(p.base.enabled)
                   if enabled and seed[model.BIOMASS_INDICES[j, i]] > 1e-18] for j in active}
    values = []
    for j in active:
        values.append(seed[4 * j] / 100.)
        for i in present[j]:
            stock = seed[model.BIOMASS_INDICES[j, i]] / BIOMASS_SCALE
            values.append(stock + np.log(-np.expm1(-stock)))
        if 0 in present[j]:
            values.append(seed[4 * j + 3] / ACETATE_SCALE)
    values.append(seed[8] / .2)

    def decode(z):
        y = np.zeros(9)
        k = 0
        for j in active:
            y[4 * j] = z[k] * 100.
            k += 1
            for i in present[j]:
                y[model.BIOMASS_INDICES[j, i]] = BIOMASS_SCALE * np.logaddexp(0., z[k])
                k += 1
            if 0 in present[j]:
                y[4 * j + 3] = z[k] * ACETATE_SCALE
                k += 1
        y[8] = z[-1] * .2
        return y

    supply = core.supply_h2(p.base) * core.HOURS_PER_YEAR
    rate_scale = core.HOURS_PER_YEAR * p.base.biology.loss_h

    def equations(z):
        y = decode(z)
        f = model.fluxes(y, p, trial_extension=True)
        values = []
        for j in active:
            local = f["local"][j]
            values.append((local["supply_h2_mol_l_yr"] - sum(local["uptake_h2_mol_l_yr"])
                           - local["outlet_h2_mol_l_yr"]) / supply)
            values.extend(local["net_growth_yr"][i] / rate_scale for i in present[j])
            if 0 in present[j]:
                values.append((local["acetate_production_mol_l_yr"] - local["acetate_recycling_mol_l_yr"]
                               - local["acetate_export_mol_l_yr"]) / (supply / 4))
        values.append((f["methane_source_ratio_yr"] - f["methane_loss_ratio_yr"]) /
                      (core.inventory_to_ratio(p.base) * supply / 4))
        return np.asarray(values)

    solution = least_squares(equations, np.asarray(values), jac="3-point", diff_step=1e-5,
                             x_scale="jac", ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=300)
    y = decode(solution.x)
    if (np.any(y < 0) or not np.all(np.isfinite(y)) or "unsupported" in model.temperature_flags(y, p)
            or np.max(abs(equations(solution.x))) > 2e-7):
        return None
    if any(y[model.BIOMASS_INDICES[j, i]] < 1e-14 for j in active for i in present[j]):
        return None
    if np.max(abs(scaled_residual(y, p))) > 2e-7:
        return None
    return y


def _kind(y, p):
    stocks = y[model.BIOMASS_INDICES]
    totals = p.weights @ stocks
    present = totals > 1e-14
    if not np.any(present):
        return "lifeless"
    if not all(present):
        return "acetogen" if present[0] else "methanogen"
    shares = []
    for local in model.fluxes(y, p)["local"]:
        if local is None:
            shares.append(np.zeros(2))
        else:
            catabolic = local["catabolic_h2_mol_l_yr"]
            shares.append(catabolic / sum(catabolic) if sum(catabolic) > 0 else np.zeros(2))
    if p.dispersal_yr == 0 and stocks[0, 1] == 0 and stocks[1, 0] == 0:
        return "pure_partition"
    if p.dispersal_yr == 0 and stocks[0, 0] == 0 and stocks[1, 1] == 0:
        return "reverse_partition"
    if p.dispersal_yr == 0 and (np.all(stocks[0] > 0) or np.all(stocks[1] > 0)):
        return "locally_mixed"
    if all(s[0 if j == 0 else 1] >= .99 for j, s in enumerate(shares)):
        return "partition_with_sinks"
    return "spatial_coexistence"


def describe(y, p, *, nonisolated=False):
    f = model.fluxes(y, p)
    vertices = response(p.base.climate.case).ratios
    sides = (-1, 1) if np.any(np.isclose(y[8], vertices, rtol=0, atol=1e-10)) else (0,)
    spectra = []
    for side in sides:
        try:
            spectra.extend(np.linalg.eigvals(model.jacobian(y, p, r_side=side)))
        except ValueError:
            continue
    eigenvalues = np.asarray(spectra, dtype=complex)
    maximum = float(max(eigenvalues.real)) if len(eigenvalues) else np.nan
    stability = ("unresolved" if not np.isfinite(maximum) else "unstable" if maximum > 1e-8
                 else "marginal" if maximum >= -1e-8 or nonisolated else "stable")
    return dict(y=np.asarray(y), r=float(y[8]), kind=_kind(y, p),
                global_temperature_k=f["global_temperature_k"], temperatures_k=f["temperatures_k"],
                climate_domain=f["climate_domain"], physiology_domains=f["physiology_domains"],
                measured=all(flag in ("measured", "inactive") for flag in f["physiology_domains"]),
                stable=stability == "stable", stability=stability, max_real_yr=maximum,
                eigenvalues=eigenvalues, nonisolated=nonisolated,
                max_scaled_residual=float(np.max(abs(scaled_residual(y, p)))),
                redox_residual=model.redox_residual(y, p))


def equilibrium_states(p, n_grid=301, *, seeds=(), stability=True):
    """Find branch-supported candidates; a finite search is not exhaustive.

    Positive dispersal continues zero-dispersal candidates. For product
    feedback, fixed-activity candidates initialize a local-product solve first.
    Nonisolated d=0 families have representative states.
    """
    if not isinstance(n_grid, int) or n_grid < 21:
        raise ValueError("Use at least 21 ratio-grid points")
    fixed = replace(p, base=replace(p.base, activity_feedback="fixed"), dispersal_yr=0.)
    candidates = _zero_dispersal(fixed, n_grid)
    if p.base.activity_feedback != "fixed":
        result = []
        for seed, _ in candidates:
            state = _product_zero_root(seed, replace(p, dispersal_yr=0.))
            if state is not None:
                result.append((state, False))
        candidates = _deduplicate(result)
    if p.dispersal_yr > 0 or p.base.activity_feedback != "fixed":
        if p.dispersal_yr == 0:
            pass
        elif np.any(p.weights == 0):
            active = int(p.weights[0] == 0)
            result = []
            for e in core.equilibrium_states(p.base, n_grid=n_grid):
                y = np.zeros(9)
                y[4 * active:4 * active + 4], y[8] = e["y"][:4], e["y"][4]
                result.append((y, False))
            candidates = result
        else:
            result = []
            for seed in seeds:
                state = _positive_root(np.asarray(seed), p)
                if state is not None:
                    result.append((state, False))
            for seed, _ in candidates:
                if not np.any(seed[model.BIOMASS_INDICES] > 0):
                    result.append((seed, False))
                    continue
                current = seed
                for d in np.unique(np.r_[np.geomspace(min(1e-6, p.dispersal_yr), p.dispersal_yr, 7),
                                         p.dispersal_yr]):
                    current = _positive_root(current, replace(p, dispersal_yr=float(d)))
                    if current is None:
                        break
                if current is not None:
                    result.append((current, False))
            candidates = _deduplicate(result)
    if stability:
        return sorted([describe(y, p, nonisolated=family) for y, family in candidates],
                      key=lambda e: (e["r"], e["kind"]))
    return [dict(y=y, r=float(y[8]), kind=_kind(y, p), nonisolated=family,
                 max_scaled_residual=float(np.max(abs(scaled_residual(y, p)))))
            for y, family in candidates]


def search_coverage(p, n_grid=301):
    """Report supported ratio intervals, independently of finding an equilibrium."""
    grid = ratio_grid(p, n_grid)
    intervals = []
    for left, right in zip(grid[:-1], grid[1:]):
        if _safe_temperatures((left + right) / 2, p) is None:
            continue
        if intervals and abs(left - intervals[-1][1]) < 1e-12:
            intervals[-1][1] = float(right)
        else:
            intervals.append([float(left), float(right)])
    low, high = model.physiology_bounds(p)
    active_offsets = p.offsets[p.weights > 0]
    return dict(n_grid=n_grid, ratio_grid_size=len(grid), ratio_ceiling=float(grid[-1]),
                global_temperature_bounds_k=[float(low - min(active_offsets)), float(high - max(active_offsets))],
                supported_ratio_intervals=intervals,
                status="supported_search_interval" if intervals else "no_supported_ratio_interval",
                completeness="Finite branch/root search; no root found is not a global nonexistence proof",
                biomass_root_numerical_zero_gdw_l=1e-14)
