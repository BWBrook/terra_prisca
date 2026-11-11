"""Static equilibria and linear response for the named Stage-B variants."""

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from scipy.optimize import brentq, root

from . import population_coupling as core
from .two_guilds import guilds

YEAR = core.HOURS_PER_YEAR
CHEMISTRIES = ("fixed", "products", "acetate_only", "methane_only")


@dataclass(frozen=True)
class DynamicParams:
    base: core.Coupled
    chemistry: str = "fixed"
    sigma_k: float = 0.
    n_habitats: int = 9
    dispersal_yr: float = .001
    slope_multiplier: float = 1.

    def __post_init__(self):
        if self.chemistry not in CHEMISTRIES:
            raise ValueError("Unknown Stage-B chemistry")
        if not isinstance(self.n_habitats, int) or self.n_habitats < 1:
            raise ValueError("The habitat count must be a positive integer")
        if not all(np.isfinite(x) and x >= 0 for x in (self.sigma_k, self.dispersal_yr)):
            raise ValueError("Spread and dispersal must be finite and nonnegative")
        if not np.isfinite(self.slope_multiplier) or self.slope_multiplier <= 0:
            raise ValueError("Climate slope multiplier must be positive")

    @property
    def n(self):
        return 1 if self.sigma_k == 0 else self.n_habitats

    @property
    def offsets(self):
        return self.sigma_k * (2*(np.arange(self.n)+.5)/self.n-1)

    @property
    def state_size(self):
        return 4*self.n+1

    @property
    def acetate_feedback(self):
        return self.chemistry in ("products", "acetate_only")

    @property
    def methane_feedback(self):
        return self.chemistry in ("products", "methane_only")


def temperature(ratio, p):
    return float(core.temperature_k(ratio, p.base.climate))


def climate_slope(ratio, p, side=0):
    curve = core.response(p.base.climate.case)
    if ratio < curve.ratios[0]:
        q = p.base.climate
        return p.slope_multiplier*(curve.temperatures_k[0]-q.t_zero_k)/((q.bridge_scale+max(ratio, 0.))*np.log1p(curve.ratios[0]/q.bridge_scale))
    if ratio > curve.ratios[-1]:
        return 0.
    index = np.searchsorted(curve.ratios, ratio, side="left" if side < 0 else "right")-1
    if index < 0:
        return climate_slope(np.nextafter(curve.ratios[0], 0.), p)
    if index >= len(curve.ratios)-1:
        return 0.
    return float(p.slope_multiplier*np.diff(curve.temperatures_k)[index]/np.diff(curve.ratios)[index])


def temperature_status(y, p):
    ts = temperature(y[-1], p)+p.offsets
    support = temperature(y[-1], p)+np.array([-p.sigma_k, p.sigma_k])
    low = 277.15 if p.base.biology.low_temperature_variant == "none" else 273.
    valid = bool(np.all((support >= low-1e-10) & (support <= 303.15+1e-10)))
    return dict(physiology_status="in_domain" if valid else "domain_censored",
                local_min_k=float(min(ts)), local_max_k=float(max(ts)),
                support_min_k=float(support[0]), support_max_k=float(support[1]),
                climate_domain=str(core.domain(y[-1], p.base.climate)))


def local_guilds(stocks, ratio, t_k, p):
    pair = guilds(float(t_k)-273.15, p.base.biology)
    factors = (max(float(stocks[3]), 0.)/p.base.acetate_reference_mol_l if p.acetate_feedback else 1.,
               max(float(ratio), 0.)*core.co2_pressure_pa(p.base.climate.case)/p.base.methane_reference_pa if p.methane_feedback else 1.)
    return tuple(replace(g, threshold_pa=g.threshold_pa*f**.25) for g, f in zip(pair, factors))


def physical_rhs(y, p, temperature_k=None):
    y = np.asarray(y, dtype=float)
    if y.shape != (p.state_size,):
        raise ValueError("Wrong Stage-B state size")
    t = temperature(y[-1], p) if temperature_k is None else float(temperature_k)
    stocks = y[:-1].reshape(p.n, 4)
    out = np.zeros_like(y); local = out[:-1].reshape(p.n, 4)
    enabled = np.asarray(p.base.enabled)
    mean = stocks[:, 1:3].mean(axis=0)
    methane = 0.
    for j, (state, offset) in enumerate(zip(stocks, p.offsets)):
        pair = local_guilds(state, y[-1], t+offset, p)
        uptake = np.array([g.uptake(state[0]) for g in pair])
        growth = np.array([g.yield_g_mol*(q-g.maintenance) for g, q in zip(pair, uptake)])
        biomass = state[1:3]*enabled
        catabolic = uptake-np.array([g.assimilation_mol_g for g in pair])*np.maximum(growth, 0.)
        rec, export = core.recycling_rates(t+offset, p.base)
        local[j, 0] = YEAR/core.HENRY_30C_MOL_L_PA*(core.supply_h2(p.base)-uptake@biomass-p.base.biology.exchange_mol_l_h_pa*(state[0]-p.base.biology.atmosphere_pa))
        local[j, 1:3] = (YEAR*biomass*(growth-p.base.biology.loss_h)+p.dispersal_yr*(mean-state[1:3])*enabled)
        local[j, 3] = YEAR*catabolic[0]*biomass[0]/4-(rec+export)*state[3]
        methane += (YEAR*catabolic[1]*biomass[1]/4+rec*state[3])/p.n
    abiotic = core.atmosphere(p.base.climate.case)["flux_to_ratio_per_yr"]*p.base.climate.abiotic_flux
    out[-1] = core.inventory_to_ratio(p.base)*methane+abiotic-p.base.loss.rate(y[-1])
    return out


def state_scales(y, p):
    return np.maximum(np.abs(y), np.r_[np.tile([10., 1e-5, 1e-5, 1e-6], p.n), .01])


def active_indices(p):
    return np.array([i for i in range(p.state_size) if i == p.state_size-1 or i % 4 not in (1, 2) or p.base.enabled[i % 4-1]], dtype=int)


def biomass_per_capita(y, p):
    """Active biomass equations divided by the actual stock, without a floor."""
    y = np.asarray(y, dtype=float)
    stocks = y[:-1].reshape(p.n, 4)
    t = temperature(y[-1], p)
    mean = stocks[:, 1:3].mean(axis=0)
    result = np.zeros((p.n, 2))
    for j, offset in enumerate(p.offsets):
        pair = local_guilds(stocks[j], y[-1], t+offset, p)
        for k, g in enumerate(pair):
            if not p.base.enabled[k]:
                continue
            x = stocks[j, k+1]
            if x <= 0:
                result[j, k] = np.inf
            else:
                with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                    result[j, k] = YEAR*(g.yield_g_mol*(g.uptake(stocks[j, 0])-g.maintenance)-p.base.biology.loss_h)+p.dispersal_yr*(mean[k]/x-1)
    return result


def jacobian_blocks(y, p, temperature_step=1e-4):
    """Physical fixed-T state matrix, common-temperature column and climate slope."""
    matrix, column, slope = _jacobian_blocks_cached(tuple(np.asarray(y, dtype=float)), p, float(temperature_step))
    return matrix.copy(), column.copy(), slope


@lru_cache(maxsize=512)
def _jacobian_blocks_cached(y, p, temperature_step):
    y = np.asarray(y, dtype=float)
    t = temperature(y[-1], p)
    matrix = np.zeros((p.state_size, p.state_size))
    enabled = np.asarray(p.base.enabled)
    conv = core.inventory_to_ratio(p.base)
    for j, offset in enumerate(p.offsets):
        start = 4*j; state = y[start:start+4]; press, xa, xm, acetate = state
        pair = local_guilds(state, y[-1], t+offset, p)
        x = state[1:3]*enabled
        uptake = np.array([g.uptake(press) for g in pair])
        synth = np.array([g.yield_g_mol*(q-g.maintenance) for g, q in zip(pair, uptake)])
        coeff = np.array([g.assimilation_mol_g for g in pair])
        yields = np.array([g.yield_g_mol for g in pair])
        slopes = np.array([g.rate_scale*g.km_pa/(g.km_pa+press-g.threshold_pa)**2 if press > g.threshold_pa else 0. for g in pair])
        dq = np.zeros((2, p.state_size)); dq[:, start] = slopes
        if p.acetate_feedback and acetate > 0:
            dq[0, start+3] = -slopes[0]*pair[0].threshold_pa/(4*acetate)
        elif p.acetate_feedback and xa*enabled[0] != 0:
            raise ValueError("Product derivative is singular at zero acetate with positive acetogens")
        if p.methane_feedback and y[-1] > 0:
            dq[1, -1] = -slopes[1]*pair[1].threshold_pa/(4*y[-1])
        elif p.methane_feedback and xm*enabled[1] != 0:
            raise ValueError("Product derivative is singular at zero methane with positive methanogens")
        matrix[start] = -YEAR/core.HENRY_30C_MOL_L_PA*(x@dq)
        matrix[start, start] -= YEAR/core.HENRY_30C_MOL_L_PA*p.base.biology.exchange_mol_l_h_pa
        matrix[start, start+1:start+3] = -YEAR/core.HENRY_30C_MOL_L_PA*uptake*enabled
        for k in (0, 1):
            row = start+1+k
            matrix[row] = YEAR*x[k]*yields[k]*dq[k]
            matrix[row, row] += YEAR*(synth[k]-p.base.biology.loss_h)*enabled[k]
            if enabled[k]:
                for other in range(p.n):
                    matrix[row, 4*other+1+k] += p.dispersal_yr/p.n
                matrix[row, row] -= p.dispersal_yr
        cat = uptake-coeff*np.maximum(synth, 0.)
        cat_deriv = (1-coeff*yields*(synth > 0.))[:, None]*dq
        rec, export = core.recycling_rates(t+offset, p.base)
        matrix[start+3] = YEAR/4*x[0]*cat_deriv[0]
        matrix[start+3, start+1] += YEAR/4*cat[0]*enabled[0]
        matrix[start+3, start+3] -= rec+export
        matrix[-1] += conv*YEAR/4/p.n*x[1]*cat_deriv[1]
        matrix[-1, start+2] += conv*YEAR/4/p.n*cat[1]*enabled[1]
        matrix[-1, start+3] += conv*rec/p.n
    if y[-1] > 0:
        matrix[-1, -1] -= p.base.loss.slope(float(y[-1]))
    else:
        matrix[-1, -1] -= 1/p.base.loss.lifetime_yr
    h = float(temperature_step)
    # The domain boundary has no outside physiology; use an inward stencil.
    low = 277.15 if p.base.biology.low_temperature_variant == "none" else 273.
    lower_margin = t-p.sigma_k-low
    upper_margin = 303.15-t-p.sigma_k
    if lower_margin < 2*h:
        column = (-3*physical_rhs(y, p, t)+4*physical_rhs(y, p, t+h)-physical_rhs(y, p, t+2*h))/(2*h)
    elif upper_margin < 2*h:
        column = (3*physical_rhs(y, p, t)-4*physical_rhs(y, p, t-h)+physical_rhs(y, p, t-2*h))/(2*h)
    else:
        column = (physical_rhs(y, p, t-2*h)-8*physical_rhs(y, p, t-h)+8*physical_rhs(y, p, t+h)-physical_rhs(y, p, t+2*h))/(12*h)
    return matrix, column, climate_slope(y[-1], p)


def reduced_matrix(y, p, side=0):
    matrix, column, _ = jacobian_blocks(y, p)
    matrix[:, -1] += column*climate_slope(y[-1], p, side)
    scale = state_scales(y, p); active = active_indices(p)
    matrix = matrix*scale[None, :]/scale[:, None]
    return matrix[np.ix_(active, active)]


def thermal_matrix(y, p, tau, two_layer=False, side=0):
    if tau == 0:
        return reduced_matrix(y, p, side)
    if not np.isfinite(tau) or tau <= 0:
        raise ValueError("Thermal lag must be positive or the zero-lag limit")
    a, b, _ = jacobian_blocks(y, p)
    scale = state_scales(y, p); active = active_indices(p)
    a = (a*scale[None, :]/scale[:, None])[np.ix_(active, active)]
    b = (b/scale)[active]
    size = len(active); matrix = np.zeros((size+(2 if two_layer else 1),)*2)
    matrix[:size, :size] = a; matrix[:size, size] = b
    ratio = int(np.flatnonzero(active == p.state_size-1)[0])
    matrix[size, ratio] = climate_slope(y[-1], p, side)*scale[-1]/tau
    matrix[size, size] = -1/tau
    if two_layer:
        matrix[size, size] = -2/tau
        matrix[size, size+1] = 1/tau
        matrix[size+1, size] = 1/(100*tau)
        matrix[size+1, size+1] = -1/(100*tau)
    return matrix


def implicit_response(y, p, side=0):
    matrix = reduced_matrix(y, p, side)
    active = active_indices(p); scale = state_scales(y, p)
    forcing = np.zeros(p.state_size)
    forcing[np.arange(p.n)*4] = YEAR/core.HENRY_30C_MOL_L_PA*core.supply_h2(p.base)
    try:
        derivative = np.linalg.solve(matrix, -(forcing/scale)[active])
    except np.linalg.LinAlgError:
        return dict(status="singular", dtemperature_dlog_supply=None, condition_number=None)
    result = float(climate_slope(y[-1], p, side)*derivative[-1]*scale[-1])
    return dict(status="defined" if np.isfinite(result) else "nonfinite",
                dtemperature_dlog_supply=result if np.isfinite(result) else None,
                condition_number=float(np.linalg.cond(matrix)))


def _bracket_roots(fun, grid, atol=1e-12):
    values = np.array([fun(float(x)) for x in grid])
    candidates = [float(x) for x, value in zip(grid, values) if np.isfinite(value) and abs(value) < atol]
    for a, b, fa, fb in zip(grid[:-1], grid[1:], values[:-1], values[1:]):
        if np.isfinite(fa) and np.isfinite(fb) and fa*fb < 0:
            try:
                value = float(brentq(fun, a, b, xtol=1e-13))
            except ValueError:
                continue
            if np.isfinite(fun(value)) and abs(fun(value)) < max(1e-8, 100*atol):
                candidates.append(value)
    unique = []
    for value in sorted(candidates):
        if not unique or value-unique[-1] > 1e-8:
            unique.append(value)
    return unique


def ratio_grid(p, n=401):
    grid = core._ratio_grid(p.base, n)
    return grid


def _single_resident(r, p, index):
    t = temperature(r, p)
    try:
        g = guilds(t-273.15, p.base.biology)[index]
    except ValueError:
        return None
    required = g.maintenance+p.base.biology.loss_h/g.yield_g_mol
    kinetic = g.rstar(p.base.biology.loss_h)-g.threshold_pa
    if not np.isfinite(kinetic):
        return None
    p0 = p.base.biology.atmosphere_pa+core.supply_h2(p.base)/p.base.biology.exchange_mol_l_h_pa
    rec, export = core.recycling_rates(t, p.base)
    if index == 0 and p.acetate_feedback:
        if kinetic >= p0:
            return None
        def stock(pressure):
            captured = max(0., core.supply_h2(p.base)-p.base.biology.exchange_mol_l_h_pa*(pressure-p.base.biology.atmosphere_pa))
            return YEAR*captured*(1-g.assimilation_mol_g*p.base.biology.loss_h/required)/(4*(rec+export))
        def balance(pressure):
            return pressure-kinetic-g.threshold_pa*(stock(pressure)/p.base.acetate_reference_mol_l)**.25
        pressure = brentq(balance, kinetic, p0, xtol=1e-12)
    elif index == 1 and p.methane_feedback:
        pressure = local_guilds([0., 0., 0., 0.], r, t, p)[1].rstar(p.base.biology.loss_h)
    else:
        pressure = g.rstar(p.base.biology.loss_h)
    captured = core.supply_h2(p.base)-p.base.biology.exchange_mol_l_h_pa*(pressure-p.base.biology.atmosphere_pa)
    if not np.isfinite(pressure) or captured <= 0:
        return None
    biomass = np.zeros(2); biomass[index] = captured/required
    acetate = YEAR*captured*(1-g.assimilation_mol_g*p.base.biology.loss_h/required)/(4*(rec+export)) if index == 0 else 0.
    return np.r_[pressure, biomass, acetate, r]


def _single_mixture(r, p):
    t = temperature(r, p)
    try:
        a, m = local_guilds([0., 0., 0., 0.], r, t, p)
    except ValueError:
        return None
    required = np.array([g.maintenance+p.base.biology.loss_h/g.yield_g_mol for g in (a, m)])
    cat = required-np.array([g.assimilation_mol_g for g in (a, m)])*p.base.biology.loss_h
    pressure = m.rstar(p.base.biology.loss_h)
    if not np.isfinite(pressure):
        return None
    captured = core.supply_h2(p.base)-p.base.biology.exchange_mol_l_h_pa*(pressure-p.base.biology.atmosphere_pa)
    rec, export = core.recycling_rates(t, p.base)
    if p.acetate_feedback:
        original_a = guilds(t-273.15, p.base.biology)[0]
        kinetic = original_a.rstar(p.base.biology.loss_h)-original_a.threshold_pa
        if not np.isfinite(kinetic):
            return None
        acetate = p.base.acetate_reference_mol_l*(max(pressure-kinetic, 0.)/original_a.threshold_pa)**4
        xa = 4*(rec+export)*acetate/(YEAR*cat[0])
        xm = (captured-required[0]*xa)/required[1]
    else:
        abiotic = core.atmosphere(p.base.climate.case)["flux_to_ratio_per_yr"]*p.base.climate.abiotic_flux
        needed = 4*(p.base.loss.rate(r)-abiotic)/(core.inventory_to_ratio(p.base)*YEAR)
        determinant = required[0]*cat[1]-required[1]*cat[0]*rec/(rec+export)
        if abs(determinant) < 1e-18:
            return None
        xa, xm = np.linalg.solve(np.array([required, cat*np.array([rec/(rec+export), 1.])]), [captured, needed])
        acetate = YEAR*cat[0]*xa/(4*(rec+export))
    return np.r_[pressure, xa, xm, acetate, r]


def _record(y, p, kind, solver="algebra"):
    scale = state_scales(y, p)
    residual = float(max(abs(physical_rhs(y, p)/scale)))
    result = dict(kind=kind, y=np.asarray(y), r=float(y[-1]), t_k=temperature(y[-1], p),
                  residual=residual, solver=solver, **temperature_status(y, p))
    result["status"] = "accepted" if residual < 1e-6 and result["physiology_status"] == "in_domain" else "unresolved"
    return result


@lru_cache(maxsize=2048)
def single_equilibria(p, n_grid=401):
    if p.n != 1:
        raise ValueError("Use homogeneous parameters for the algebraic scanner")
    grid = ratio_grid(p, n_grid); result = []
    abiotic = core.atmosphere(p.base.climate.case)["flux_to_ratio_per_yr"]*p.base.climate.abiotic_flux
    r0 = float(p.base.loss.inverse(abiotic))
    p0 = p.base.biology.atmosphere_pa+core.supply_h2(p.base)/p.base.biology.exchange_mol_l_h_pa
    lifeless = np.r_[p0, 0., 0., 0., r0]
    if temperature_status(lifeless, p)["physiology_status"] == "in_domain":
        result.append(_record(lifeless, p, "lifeless"))
    for index, kind in enumerate(("acetogen", "methanogen")):
        if not p.base.enabled[index]:
            continue
        def balance(r):
            y = _single_resident(r, p, index)
            return physical_rhs(y, p)[-1] if y is not None else np.nan
        for r in _bracket_roots(balance, grid, 1e-14):
            y = _single_resident(r, p, index)
            if y is not None:
                result.append(_record(y, p, kind))
    if all(p.base.enabled):
        if p.acetate_feedback:
            def balance(r):
                y = _single_mixture(r, p)
                return physical_rhs(y, p)[-1] if y is not None else np.nan
        else:
            def balance(r):
                try:
                    t = temperature(r, p); a, m = local_guilds([0., 0., 0., 0.], r, t, p)
                    return a.rstar(p.base.biology.loss_h)-m.rstar(p.base.biology.loss_h)
                except ValueError:
                    return np.nan
        for r in _bracket_roots(balance, grid, 1e-14 if p.acetate_feedback else 1e-10):
            y = _single_mixture(r, p)
            if y is not None and np.all(y[1:4] > 0):
                result.append(_record(y, p, "mixed"))
    return tuple(sorted(result, key=lambda e:(e["r"], e["kind"])))


def _spread_root(seed, p):
    scale = state_scales(seed, p)
    active = active_indices(p)
    if not p.base.enabled[0]:
        active = active[(active == p.state_size-1) | (active % 4 != 3)]
    initial = np.asarray(seed).copy()
    positive = np.maximum(initial[active]/scale[active], 1e-12)
    equation_weights = np.ones(p.state_size)
    equation_weights[np.arange(p.n)*4] = 1e-7
    equation_weights[-1] = 1e4
    biomass = np.array([4*j+1+k for j in range(p.n) for k in (0, 1) if p.base.enabled[k]])
    def decode(z):
        y = np.zeros(p.state_size)
        y[active] = np.exp(np.clip(z, -700, 100))*scale[active]
        return y
    def equations(z):
        y = decode(z)
        if temperature_status(y, p)["physiology_status"] != "in_domain":
            # Outside-domain iterates are rejected, never evaluated with clipped physiology.
            return np.full(len(active), 1e3)+z-np.log(positive)
        values = physical_rhs(y, p)/np.maximum(y, scale*1e-12)*equation_weights
        values[biomass] = biomass_per_capita(y, p)[:, np.asarray(p.base.enabled)].reshape(-1)
        return np.nan_to_num(values[active], nan=1e100, posinf=1e100, neginf=-1e100)
    def derivative(z):
        y = decode(z)
        if temperature_status(y, p)["physiology_status"] != "in_domain":
            return np.eye(len(active))
        a, b, _ = jacobian_blocks(y, p)
        a[:, -1] += b*climate_slope(y[-1], p)/p.slope_multiplier
        f = physical_rhs(y, p)
        denominator = np.maximum(y, scale*1e-12)
        denominator[biomass] = y[biomass]
        result = a*y[None, :]/denominator[:, None]
        result[np.diag_indices_from(result)] -= f/denominator
        result *= equation_weights[:, None]
        return result[np.ix_(active, active)]
    sol = root(equations, np.log(positive), jac=derivative, method="hybr", options={"xtol":1e-11, "maxfev":1500})
    state = decode(sol.x)
    if temperature_status(state, p)["physiology_status"] != "in_domain":
        return None
    for _ in range(3):
        a, b, _ = jacobian_blocks(state, p)
        a[:, -1] += b*climate_slope(state[-1], p)/p.slope_multiplier
        scales = state_scales(state, p)
        try:
            delta = np.linalg.solve((a*scales[None, :]/scales[:, None])[np.ix_(active, active)],
                                    -(physical_rhs(state, p)/scales)[active])*scales[active]
        except np.linalg.LinAlgError:
            break
        trial = state.copy(); trial[active] += delta
        if np.any(trial[active] <= 0) or temperature_status(trial, p)["physiology_status"] != "in_domain":
            break
        if max(abs(physical_rhs(trial, p)/scales)) >= max(abs(physical_rhs(state, p)/scales)):
            break
        state = trial
    kind = "mixed" if all(p.base.enabled) else "methanogen" if p.base.enabled[1] else "acetogen"
    result = _record(state, p, kind, "positive_coordinate_root")
    values = physical_rhs(state, p)/np.maximum(state, scale*1e-12)*equation_weights
    active_growth = biomass_per_capita(state, p)
    values[biomass] = active_growth[:, np.asarray(p.base.enabled)].reshape(-1)
    percapita = max(abs(values[active]))
    result["root_relative_residual"] = float(percapita)
    result["biomass_per_capita_residual_yr"] = float(np.max(np.abs(active_growth)))
    if result["status"] != "accepted" or not np.isfinite(percapita) or percapita > 1e-7:
        return None
    stocks = state[:-1].reshape(p.n, 4)
    means = stocks[:, 1:3].mean(axis=0)
    result["numerical_small_stock"] = bool(all(p.base.enabled) and min(means) < 1e-12)
    if all(p.base.enabled) and np.any(means <= 0):
        return None
    return result


def continue_equilibrium(seed, p):
    """Correct a supplied same-geometry state; failure is unresolved, not absence."""
    y = seed["y"] if isinstance(seed, dict) else np.asarray(seed, dtype=float)
    if y.shape != (p.state_size,):
        raise ValueError("Continuation seed has another habitat geometry")
    return _spread_root(y, p)


def _spread_step(y, p, previous, target, depth=0):
    found = _spread_root(y, replace(p, sigma_k=float(target)))
    if found is not None or depth >= 8 or target-previous < .002:
        return found
    midpoint = (previous+target)/2
    middle = _spread_step(y, p, previous, midpoint, depth+1)
    return None if middle is None else _spread_step(middle["y"], p, midpoint, target, depth+1)


def equilibrium_states(p, seeds=(), n_grid=401):
    """All candidates found by algebra and declared spread homotopies, not a completeness proof."""
    if p.n == 1:
        return list(single_equilibria(p, n_grid))
    result = []
    for seed in seeds:
        y = seed["y"] if isinstance(seed, dict) else np.asarray(seed)
        if len(y) == p.state_size:
            found = _spread_root(y, p)
            if found is not None:
                result.append(found)
    homogeneous = replace(p, sigma_k=0.)
    starts = list(single_equilibria(homogeneous, n_grid))
    for start in starts:
        if all(p.base.enabled) and start["kind"] != "mixed":
            continue
        if not all(p.base.enabled) and start["kind"] != ("methanogen" if p.base.enabled[1] else "acetogen"):
            continue
        y = np.r_[np.tile(start["y"][:4], p.n), start["r"]]
        found = None
        previous = 0.
        steps = np.unique(np.r_[np.geomspace(.001, min(1., p.sigma_k), 8), np.arange(1., p.sigma_k, .5), p.sigma_k])
        for spread in steps:
            found = _spread_step(y, p, previous, float(spread))
            if found is None:
                break
            y = found["y"]
            previous = float(spread)
        if found is not None:
            result.append(found)
    unique = []
    for record in sorted(result, key=lambda e:e["r"]):
        if not any(abs(record["r"]-old["r"]) < 1e-7 for old in unique):
            unique.append(record)
    return unique
