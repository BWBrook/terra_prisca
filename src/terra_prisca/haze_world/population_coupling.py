"""Physical two-guild, acetate and atmospheric-methane budget, in years.

State: p [Pa], X_A/X_M [gDW/L], acetate [mol/L], atmospheric CH4/CO2 ratio.
An explicit effective habitat volume connects local inventories to columns.
This is a named conditional model, not an Archean calibration.
"""

from dataclasses import dataclass, replace
from functools import lru_cache
import csv

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
from scipy.special import expit

from .darwinian import Loss
from .methane_budget import (ARNEY_DIR, AVOGADRO, SECONDS_PER_YEAR, Params, atmosphere,
                             domain, response, temperature_k)
from .two_guilds import (ASSIMILATION_A, Competition, FIRST_ORDER_LIMIT_MOL_L,
                         HENRY_30C_MOL_L_PA, guilds)

HOURS_PER_YEAR = SECONDS_PER_YEAR / 3600


@dataclass(frozen=True)
class Coupled:
    climate: Params
    biology: Competition
    loss: Loss
    habitat_l_cm2: float
    acetate_lifetime_yr: float = 1.
    acetate_fraction: float = .5
    recycling_variant: str = "constant"
    recycling_midpoint_k: float = 280.
    width_k: float = 2.
    enabled: tuple[bool, bool] = (True, True)
    activity_feedback: str = "fixed"
    acetate_reference_mol_l: float = .5e-3
    methane_reference_pa: float = 350.

    def __post_init__(self):
        if not all(np.isfinite(v) and v > 0 for v in (self.habitat_l_cm2, self.acetate_lifetime_yr, self.width_k)):
            raise ValueError("Habitat volume, acetate lifetime and recycling width must be positive")
        if not 0 <= self.acetate_fraction <= 1 or not np.isfinite(self.recycling_midpoint_k):
            raise ValueError("Invalid recycling fraction or midpoint")
        if self.recycling_variant not in ("constant", "cold_limited"):
            raise ValueError("Unknown recycling variant")
        if self.biology.exchange_mol_l_h_pa <= 0:
            raise ValueError("Population coupling requires a finite hydrogen outlet")
        if len(self.enabled) != 2 or any(not isinstance(v, (bool, np.bool_)) for v in self.enabled):
            raise ValueError("Explicitly enable or disable the two guilds")
        if self.activity_feedback not in ("fixed", "products"):
            raise ValueError("Unknown product-activity variant")
        if not all(np.isfinite(v) and v > 0 for v in (self.acetate_reference_mol_l, self.methane_reference_pa)):
            raise ValueError("Product reference activities must be positive")


def reference(potential=.3):
    """Fix habitat and exchange once; varying supply thereafter keeps both fixed.

    The 283 K methane-free bridge and cold capacity continuation are assumptions.
    The volume normalizes J=1e-6 mol H2/L/h at reference potential 0.3.
    """
    q = Params(t_zero_k=283.)
    conversion = atmosphere(q.case)["flux_to_ratio_per_yr"]
    flux_ref = .3 / (q.lifetime_yr * conversion)
    volume = 4 * flux_ref * 3600 / (AVOGADRO * 1e-6)
    q = replace(q, donor_flux=float(potential / (q.lifetime_yr * conversion)))
    bio = Competition(threshold_shape="fixed_energy", assimilation_m=ASSIMILATION_A,
                      exchange_mol_l_h_pa=1e-6 / 300, low_temperature_variant="constant_shape")
    return Coupled(q, bio, Loss(.3, q.lifetime_yr), volume)


def inventory_to_ratio(p):
    air = atmosphere(p.climate.case)
    return p.habitat_l_cm2 * AVOGADRO / (air["column"] * air["f_co2"])


def supply_h2(p):
    return 4 * p.climate.donor_flux * 3600 / (AVOGADRO * p.habitat_l_cm2)


def recycling_rates(t_k, p):
    inhibition = 1. if p.recycling_variant == "constant" else float(expit((t_k - p.recycling_midpoint_k) / p.width_k))
    return p.acetate_fraction * inhibition / p.acetate_lifetime_yr, (1 - p.acetate_fraction) / p.acetate_lifetime_yr


@lru_cache(maxsize=None)
def co2_pressure_pa(case):
    with (ARNEY_DIR / "cases.csv").open() as handle:
        row = next(row for row in csv.DictReader(handle) if row["case"] == case)
    return float(row["p_co2_bar"]) * 1e5


def activity_guilds(y, p):
    """Normalized ideal-product correction; reference pH and CO2 stay fixed."""
    temperature = float(temperature_k(y[4], p.climate))
    pair = guilds(temperature - 273.15, p.biology)
    if p.activity_feedback == "fixed":
        return pair
    methane_pa = max(float(y[4]), 0.) * co2_pressure_pa(p.climate.case)
    factors = ((max(float(y[3]), 0.) / p.acetate_reference_mol_l) ** .25,
               (methane_pa / p.methane_reference_pa) ** .25)
    return tuple(replace(g, threshold_pa=g.threshold_pa * factor) for g, factor in zip(pair, factors))


def fluxes(y, p):
    """Local flows in mol/L/year; atmospheric source/loss in ratio/year.

    The algebra also extends linearly to small negative biomasses for Jacobians.
    Physical trajectories use positive coordinates for initially present populations.
    """
    pressure, xa, xm, acetate, r = np.asarray(y, dtype=float)
    temperature = float(temperature_k(r, p.climate))
    pair = activity_guilds(y, p)
    if p.biology.kinetics == "first_order" and p.enabled[0] and pressure * HENRY_30C_MOL_L_PA > FIRST_ORDER_LIMIT_MOL_L:
        raise ValueError("Outside the declared first-order H2 concentration domain")
    biomass = np.array([xa, xm]) * np.array(p.enabled)
    uptake = np.array([g.uptake(pressure) for g in pair])
    synthesis_h = np.array([g.yield_g_mol * (q - g.maintenance) for g, q in zip(pair, uptake)])
    coefficients = np.array([g.assimilation_mol_g for g in pair])
    used = uptake * biomass * HOURS_PER_YEAR
    assimilation = coefficients * np.maximum(synthesis_h, 0) * biomass * HOURS_PER_YEAR
    catabolic = used - assimilation
    krec, kother = recycling_rates(temperature, p)
    recycled, exported = krec * acetate, kother * acetate
    methane = catabolic[1] / 4 + recycled
    conversion = inventory_to_ratio(p)
    abiotic = atmosphere(p.climate.case)["flux_to_ratio_per_yr"] * p.climate.abiotic_flux
    return dict(temperature_k=temperature, climate_domain=str(domain(r, p.climate)),
        supply_h2_mol_l_yr=supply_h2(p) * HOURS_PER_YEAR,
        uptake_h2_mol_l_yr=used, assimilation_h2_mol_l_yr=assimilation,
        catabolic_h2_mol_l_yr=catabolic,
        outlet_h2_mol_l_yr=p.biology.exchange_mol_l_h_pa * (pressure - p.biology.atmosphere_pa) * HOURS_PER_YEAR,
        acetate_production_mol_l_yr=catabolic[0] / 4,
        acetate_recycling_mol_l_yr=recycled, acetate_export_mol_l_yr=exported,
        biomass_export_h2_mol_l_yr=coefficients * (p.biology.loss_h + np.maximum(-synthesis_h, 0)) * biomass * HOURS_PER_YEAR,
        methane_local_mol_l_yr=methane, methane_source_ratio_yr=conversion * methane + abiotic,
        methane_loss_ratio_yr=float(p.loss.rate(r)), abiotic_ratio_yr=abiotic,
        net_growth_yr=(synthesis_h - p.biology.loss_h) * HOURS_PER_YEAR,
        k_rec_yr=krec, k_other_yr=kother)


def rhs(y, p):
    f = fluxes(y, p)
    return np.r_[
        (f["supply_h2_mol_l_yr"] - sum(f["uptake_h2_mol_l_yr"]) - f["outlet_h2_mol_l_yr"]) / HENRY_30C_MOL_L_PA,
        np.asarray(y)[1:3] * f["net_growth_yr"] * p.enabled,
        f["acetate_production_mol_l_yr"] - f["acetate_recycling_mol_l_yr"] - f["acetate_export_mol_l_yr"],
        f["methane_source_ratio_yr"] - f["methane_loss_ratio_yr"],
    ]


def redox_residual(y, p):
    """Combined H2-equivalent inventory derivative minus all external flows."""
    f, dy = fluxes(y, p), rhs(y, p)
    a = [g.assimilation_mol_g for g in guilds(f["temperature_k"] - 273.15, p.biology)]
    conversion = inventory_to_ratio(p)
    stored = HENRY_30C_MOL_L_PA * dy[0] + np.dot(a, dy[1:3]) + 4 * dy[3] + 4 * dy[4] / conversion
    external = (f["supply_h2_mol_l_yr"] - f["outlet_h2_mol_l_yr"] -
                4 * f["acetate_export_mol_l_yr"] - sum(f["biomass_export_h2_mol_l_yr"]) +
                4 * (f["abiotic_ratio_yr"] - f["methane_loss_ratio_yr"]) / conversion)
    return float(stored - external)


def jacobian(y, p, *, r_side=0):
    """Jacobian in scaled physical coordinates; retain invasion at absent guilds."""
    y = np.asarray(y, dtype=float)
    scales = np.maximum(np.abs(y), [10., 1e-4, 1e-4, 1e-5, .01])
    center = rhs(y, p)
    jac = np.empty((5, 5))
    for j in range(5):
        h = scales[j] * 1e-5
        delta = np.eye(5)[j] * h
        if j == 4 and r_side:
            derivative = (rhs(y + r_side * delta, p) - center) / (r_side * h)
        else:
            derivative = (rhs(y + delta, p) - rhs(y - delta, p)) / (2 * h)
        jac[:, j] = derivative * scales[j] / scales
    active = [0, *[i + 1 for i, enabled in enumerate(p.enabled) if enabled], 3, 4]
    return jac[np.ix_(active, active)]


def _describe(kind, y, p):
    f = fluxes(y, p)
    vertices = response(p.climate.case).ratios
    side_options = (-1, 1) if np.any(np.isclose(y[4], vertices, rtol=0, atol=1e-10)) else (0,)
    eigenvalues = np.concatenate([np.linalg.eigvals(jacobian(y, p, r_side=side)) for side in side_options])
    maximum = float(max(eigenvalues.real))
    stability = "stable" if maximum < -1e-9 else "unstable" if maximum > 1e-9 else "marginal"
    return dict(kind=kind, y=np.asarray(y), r=float(y[4]), t_k=f["temperature_k"],
                domain=f["climate_domain"], stable=stability == "stable", stability=stability,
                max_real_yr=maximum, eigenvalues=eigenvalues,
                redox_residual=redox_residual(y, p))


def _roots(function, grid, zero_atol):
    values = np.array([function(float(x)) for x in grid])
    roots = [float(x) for x, v in zip(grid, values) if np.isfinite(v) and abs(v) <= zero_atol]
    for a, b, fa, fb in zip(grid[:-1], grid[1:], values[:-1], values[1:]):
        if np.isfinite(fa) and np.isfinite(fb) and fa * fb < 0:
            roots.append(float(brentq(function, a, b, xtol=1e-13)))
    unique = []
    for x in sorted(roots):
        if not unique or x - unique[-1] > 1e-8:
            unique.append(x)
    return unique


def _ratio_grid(p, n):
    conversion = inventory_to_ratio(p)
    max_input = supply_h2(p) + p.biology.exchange_mol_l_h_pa * p.biology.atmosphere_pa
    ceiling = conversion * HOURS_PER_YEAR * max_input / 4 + atmosphere(p.climate.case)["flux_to_ratio_per_yr"] * p.climate.abiotic_flux
    hi = max(float(p.loss.inverse(ceiling)) * 1.01, 1e-8)
    return np.unique(np.r_[np.linspace(0, hi, n), np.geomspace(1e-12, hi, n // 2),
                           response(p.climate.case).ratios[response(p.climate.case).ratios < hi]])


def _resident(r, p, index):
    if p.activity_feedback == "products":
        return _product_resident(r, p, index)
    t = float(temperature_k(r, p.climate))
    pair = guilds(t - 273.15, p.biology)
    g = pair[index]
    pressure = g.rstar(p.biology.loss_h)
    captured = supply_h2(p) - p.biology.exchange_mol_l_h_pa * (pressure - p.biology.atmosphere_pa)
    if not np.isfinite(pressure) or captured <= 0:
        return None
    biomass = np.zeros(2)
    biomass[index] = captured / float(g.uptake(pressure))
    y = np.r_[pressure, biomass, 0., r]
    f = fluxes(y, p)
    y[3] = f["acetate_production_mol_l_yr"] / (f["k_rec_yr"] + f["k_other_yr"])
    return y


def _product_resident(r, p, index):
    t = float(temperature_k(r, p.climate))
    base = guilds(t - 273.15, p.biology)[index]
    required = base.maintenance + p.biology.loss_h / base.yield_g_mol
    kinetic = base.rstar(p.biology.loss_h) - base.threshold_pa
    if not np.isfinite(kinetic):
        return None
    p0 = p.biology.atmosphere_pa + supply_h2(p) / p.biology.exchange_mol_l_h_pa
    krec, kother = recycling_rates(t, p)
    if index == 1:
        actual = activity_guilds([0., 0., 0., 0., r], p)[1]
        pressure = actual.rstar(p.biology.loss_h)
    else:
        if kinetic >= p0:
            return None
        b = 1 - base.assimilation_mol_g * p.biology.loss_h / required

        def stock(pressure):
            captured = max(0., supply_h2(p) - p.biology.exchange_mol_l_h_pa * (pressure - p.biology.atmosphere_pa))
            return HOURS_PER_YEAR * captured * b / (4 * (krec + kother))

        def balance(pressure):
            return pressure - kinetic - base.threshold_pa * (stock(pressure) / p.acetate_reference_mol_l) ** .25

        pressure = brentq(balance, kinetic, p0, xtol=1e-12) if base.threshold_pa else kinetic
    captured = supply_h2(p) - p.biology.exchange_mol_l_h_pa * (pressure - p.biology.atmosphere_pa)
    if not np.isfinite(pressure) or captured <= 0:
        return None
    biomass = np.zeros(2)
    biomass[index] = captured / required
    y = np.r_[pressure, biomass, 0., r]
    if index == 0:
        y[3] = HOURS_PER_YEAR * captured * (1 - base.assimilation_mol_g * p.biology.loss_h / required) / (4 * (krec + kother))
    return y


def _product_mixture(r, p):
    t = float(temperature_k(r, p.climate))
    base_a, _ = guilds(t - 273.15, p.biology)
    m = activity_guilds([0., 0., 0., 0., r], p)[1]
    qa = base_a.maintenance + p.biology.loss_h / base_a.yield_g_mol
    qm = m.maintenance + p.biology.loss_h / m.yield_g_mol
    pressure = m.rstar(p.biology.loss_h)
    kinetic_a = base_a.rstar(p.biology.loss_h) - base_a.threshold_pa
    if not np.isfinite(pressure) or not np.isfinite(kinetic_a):
        return None
    if base_a.threshold_pa <= 0:
        raise ValueError("Product-mixture roots require a positive acetogen reference threshold")
    acetate = p.acetate_reference_mol_l * (max(pressure - kinetic_a, 0.) / base_a.threshold_pa) ** 4
    krec, kother = recycling_rates(t, p)
    xa = 4 * (krec + kother) * acetate / (HOURS_PER_YEAR * (qa - base_a.assimilation_mol_g * p.biology.loss_h))
    captured = supply_h2(p) - p.biology.exchange_mol_l_h_pa * (pressure - p.biology.atmosphere_pa)
    xm = (captured - qa * xa) / qm
    return np.array([pressure, xa, xm, acetate, r])


@lru_cache(maxsize=None)
def switch_temperatures(biology):
    low = 4. if biology.low_temperature_variant == "none" else -.15
    grid = np.unique(np.r_[np.arange(low, 30., .25), low, 4., 10., 15., 20., 25., 30.])

    def difference(t):
        a, m = [g.rstar(biology.loss_h) for g in guilds(t, biology)]
        return a - m if np.isfinite(a) and np.isfinite(m) else np.nan

    return tuple(x + 273.15 for x in _roots(difference, grid, 1e-10))


def equilibrium_states(p, n_grid=501):
    """Pure and mixed equilibrium candidates with full local stability.

    Grid-supported roots include exact vertices; finite sampling is not a
    proof excluding every tangent root or an unsupported cold-climate branch.
    """
    grid, result = _ratio_grid(p, n_grid), []
    abiotic = atmosphere(p.climate.case)["flux_to_ratio_per_yr"] * p.climate.abiotic_flux
    r0 = float(p.loss.inverse(abiotic))
    p0 = p.biology.atmosphere_pa + supply_h2(p) / p.biology.exchange_mol_l_h_pa
    try:
        result.append(_describe("lifeless", np.array([p0, 0., 0., 0., r0]), p))
    except ValueError:
        pass
    for index, name in enumerate(("acetogen", "methanogen")):
        if not p.enabled[index]:
            continue

        def balance(r):
            try:
                state = _resident(r, p, index)
                return rhs(state, p)[4] if state is not None else np.nan
            except ValueError:
                return np.nan

        for r in _roots(balance, grid, 1e-14):
            y = _resident(r, p, index)
            if y is not None:
                result.append(_describe(name, y, p))
    if all(p.enabled) and p.activity_feedback == "products":
        def product_balance(r):
            try:
                y = _product_mixture(r, p)
                return rhs(y, p)[4] if y is not None else np.nan
            except ValueError:
                return np.nan

        for r in _roots(product_balance, grid, 1e-14):
            y = _product_mixture(r, p)
            if y is not None and np.all(y[1:4] > 0) and np.max(np.abs(rhs(y, p)[1:])) < 1e-9:
                result.append(_describe("mixed", y, p))
    elif all(p.enabled):
        for ts in switch_temperatures(p.biology):
            def t_difference(r):
                return float(temperature_k(r, p.climate)) - ts

            for r in _roots(t_difference, grid, 1e-10):
                pair = guilds(ts - 273.15, p.biology)
                pressure = pair[0].rstar(p.biology.loss_h)
                captured = supply_h2(p) - p.biology.exchange_mol_l_h_pa * (pressure - p.biology.atmosphere_pa)
                if captured <= 0:
                    continue
                required = np.array([g.maintenance + p.biology.loss_h / g.yield_g_mol for g in pair])
                b = 1 - np.array([g.assimilation_mol_g for g in pair]) * p.biology.loss_h / required
                krec, kother = recycling_rates(ts, p)
                effective = krec / (krec + kother)
                needed = (float(p.loss.rate(r)) - abiotic) / (inventory_to_ratio(p) * captured * HOURS_PER_YEAR / 4)
                denominator = effective * b[0] - b[1]
                if abs(denominator) < 1e-12:
                    continue
                share = (needed - b[1]) / denominator
                if not 0 < share < 1:
                    continue
                y = np.r_[pressure, captured * np.array([share, 1 - share]) / required,
                           captured * HOURS_PER_YEAR * share * b[0] / (4 * (krec + kother)), r]
                result.append(_describe("mixed", y, p))
    return sorted(result, key=lambda e: (e["r"], e["kind"]))


def integrate(y0, p, years, sample_times=None):
    initial = np.asarray(y0, dtype=float)
    if initial.shape != (5,) or np.any(~np.isfinite(initial)) or np.any(initial < 0) or years <= 0:
        raise ValueError("Provide five nonnegative physical stocks and a positive duration")
    if any(not enabled and initial[i + 1] != 0 for i, enabled in enumerate(p.enabled)):
        raise ValueError("Disabled guilds must start absent")
    positive_indices = [i for i in (1, 2) if initial[i] > 0]
    biomass_scale = 1e-3
    internal = initial.copy()
    for i in positive_indices:
        scaled = initial[i] / biomass_scale
        internal[i] = scaled + np.log(-np.expm1(-scaled))

    def derivatives(_, state):
        physical = state.copy()
        physical[positive_indices] = biomass_scale * np.logaddexp(0., state[positive_indices])
        rates = rhs(physical, p)
        net = fluxes(physical, p)["net_growth_yr"]
        for i in positive_indices:
            z = state[i]
            # B = scale*softplus(z): log-like when rare, linear for large trials.
            factor = 1. if z < -30 else np.logaddexp(0., z) / expit(z)
            rates[i] = net[i - 1] * factor
        return rates

    result = solve_ivp(derivatives, (0., years), internal, method="LSODA", rtol=2e-8,
                       atol=[1e-7, 1e-10 if 1 not in positive_indices else 1e-8,
                             1e-10 if 2 not in positive_indices else 1e-8, 1e-11, 1e-11],
                       t_eval=sample_times)
    if not result.success:
        raise RuntimeError(result.message)
    result.positive_coordinates = result.y.copy()
    result.log_biomass = np.full((2, result.y.shape[1]), -np.inf)
    for i in positive_indices:
        z = result.y[i].copy()
        log_stock = z.copy()
        moderate = z >= -30
        log_stock[moderate] = np.log(np.logaddexp(0., z[moderate]))
        result.log_biomass[i - 1] = np.log(biomass_scale) + log_stock
        result.y[i] = biomass_scale * np.logaddexp(0., z)
    return result
