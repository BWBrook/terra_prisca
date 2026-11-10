"""Accepted-step continuum trajectories and finite censuses for N habitats.

No external immigrants are added. Dense-output minima describe this numerical
trajectory; after a census changes it, later minima depend on that census rule.
"""

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from numpy.polynomial import Polynomial
from scipy.integrate import LSODA
from scipy.optimize import brentq, minimize_scalar
from scipy.special import expit, logsumexp

from . import habitat_coupling as model

SCALE = 1e-3
ACETATE_SCALE = 1e-3
GUILDS = ("acetogen", "methanogen")


@dataclass(frozen=True)
class Census:
    minimum_cells: float = 1.
    census_yr: float = 10.
    cell_mass_gdw: float = 3e-13
    surface_cm2: float = 5.1e18

    def __post_init__(self):
        if not np.isfinite(self.minimum_cells) or self.minimum_cells < 0:
            raise ValueError("The census floor must be finite and nonnegative")
        if not all(np.isfinite(v) and v > 0 for v in (self.census_yr, self.cell_mass_gdw, self.surface_cm2)):
            raise ValueError("Census interval, cell mass and area must be positive")


@dataclass
class HabitatResult:
    t: np.ndarray
    y: np.ndarray
    log_biomass: np.ndarray
    log_acetate: np.ndarray
    temperatures_k: np.ndarray
    physiology_domains: np.ndarray
    climate_domains: np.ndarray
    success: bool
    status: str
    domain_exit: dict | None
    census_times: np.ndarray
    census_activity: np.ndarray
    extinction_events: list[dict]
    continuous_min_log_biomass: np.ndarray
    continuous_min_times_yr: np.ndarray
    pre_removal_min_log_biomass: np.ndarray
    pre_removal_min_times_yr: np.ndarray
    after_census_min_log_biomass: np.ndarray
    global_continuous_min_log_biomass: np.ndarray
    global_continuous_min_times_yr: np.ndarray
    global_pre_extinction_min_log_biomass: np.ndarray
    global_pre_extinction_min_times_yr: np.ndarray
    global_after_census_min_log_biomass: np.ndarray
    ledger: dict
    metadata: dict


def _inverse(value):
    return value + np.log(-np.expm1(-value))


def _log_softplus(value, scale=SCALE):
    return np.log(scale) + (value if value < -30 else np.log(np.logaddexp(0., value)))


def _array_log_softplus(value):
    value=np.asarray(value)
    result=value.copy()
    mask=value>=-30
    result[mask]=np.log(np.logaddexp(0.,value[mask]))
    return np.log(SCALE)+result


def _log_softplus_derivative(value):
    value=np.asarray(value)
    result=np.ones_like(value)
    np.divide(expit(value),np.logaddexp(0.,value),out=result,where=value>=-30)
    return result


class _Coordinates:
    def __init__(self, initial, p):
        self.p = p
        self.n = p.n_patches
        self.m = p.state_size
        self.indices = p.biomass_indices
        self.shared = bool(p.dispersal_yr > 0 and np.count_nonzero(p.weights) > 1)
        self.present = initial[self.indices] > 0
        self.global_present = p.weights @ self.present.astype(float) > 0
        self.acetate_positive = (initial[3:self.m-1:4] > 0) & (p.weights > 0)

    def encode(self, physical):
        state = np.r_[physical, [0., 0.]] if self.shared else physical.copy()
        if self.shared:
            for i in range(2):
                total = float(self.p.weights @ physical[self.indices[:, i]])
                if total > 0:
                    state[self.m+i] = _inverse(total / SCALE)
                    state[self.indices[:, i]] = self.p.weights * physical[self.indices[:, i]] / total
                else:
                    if np.any(physical[self.indices[:, i]] > 0):
                        raise ValueError("Weighted initial biomass is below numerical representation")
                    state[self.m+i] = 0.
                    state[self.indices[:, i]] = self.p.weights
        else:
            for j, w in enumerate(self.p.weights):
                for i in range(2):
                    k = 4*j+1+i
                    state[k] = _inverse(physical[k]/SCALE) if w and self.present[j,i] else 0.
        for j in range(self.n):
            if self.acetate_positive[j]:
                state[4*j+3] = _inverse(physical[4*j+3]/ACETATE_SCALE)
        return state

    def decode(self, internal):
        physical = np.asarray(internal[:self.m]).copy()
        logs = np.full((self.n,2), -np.inf)
        if self.shared:
            for i in range(2):
                if not self.global_present[i]:
                    physical[self.indices[:,i]] = 0.
                    continue
                z = internal[self.m+i]
                h = internal[self.indices[:,i]]
                normalizer = float(sum(h))
                if normalizer <= 0:
                    raise RuntimeError("Allocation normalizer must remain positive")
                total = SCALE*np.logaddexp(0.,z)
                log_total = _log_softplus(z)
                for j,w in enumerate(self.p.weights):
                    if not w:
                        physical[4*j+1+i] = 0.
                        continue
                    physical[4*j+1+i] = total*h[j]/(normalizer*w)
                    if h[j] > 0:
                        logs[j,i] = log_total+np.log(h[j])-np.log(normalizer)-np.log(w)
        else:
            for j,w in enumerate(self.p.weights):
                for i in range(2):
                    k = 4*j+1+i
                    if w and self.present[j,i]:
                        physical[k] = SCALE*np.logaddexp(0.,internal[k])
                        logs[j,i] = _log_softplus(internal[k])
                    else:
                        physical[k] = 0.
        for j in range(self.n):
            if self.acetate_positive[j]:
                physical[4*j+3] = ACETATE_SCALE*np.logaddexp(0.,internal[4*j+3])
        return physical,logs

    def acetate_logs(self, internal):
        return np.array([_log_softplus(internal[4*j+3],ACETATE_SCALE) if self.acetate_positive[j]
                         else np.log(internal[4*j+3]) if internal[4*j+3] > 0 else -np.inf
                         for j in range(self.n)])

    def derivative(self, _, internal):
        physical,biomass_logs = self.decode(internal)
        rates = model.rhs(physical,self.p,trial_extension=True)
        if self.shared:
            rates = np.r_[rates, [0.,0.]]
        f = model.fluxes(physical,self.p,trial_extension=True)
        growth = np.zeros((self.n,2))
        for j,local in enumerate(f["local"]):
            if local is None:
                continue
            growth[j] = local["net_growth_yr"]
            if self.acetate_positive[j]:
                z = internal[4*j+3]
                production = local["acetate_production_mol_l_yr"]
                coefficient = local["acetate_production_per_gdw_yr"]
                log_production = (np.log(production) if production > 0 else
                                  np.log(coefficient)+biomass_logs[j,0]
                                  if coefficient > 0 and np.isfinite(biomass_logs[j,0]) else -np.inf)
                log_denominator = np.log(ACETATE_SCALE)-np.logaddexp(0.,-z)
                difference = log_production-log_denominator
                if difference > np.log(np.finfo(float).max):
                    raise RuntimeError("Acetate source exceeds the representable coordinate range")
                source = np.exp(difference) if np.isfinite(difference) else 0.
                factor = 1. if z < -30 else np.logaddexp(0.,z)/expit(z)
                rates[4*j+3] = source-(local["k_rec_yr"]+local["k_other_yr"])*factor
        if self.shared:
            for i in range(2):
                if not self.global_present[i]:
                    rates[self.indices[:,i]] = 0.
                    rates[self.m+i] = 0.
                    continue
                h = internal[self.indices[:,i]]
                normalizer = float(sum(h))
                mean = float(h @ growth[:,i] / normalizer)
                z = internal[self.m+i]
                factor = 1. if z < -30 else np.logaddexp(0.,z)/expit(z)
                rates[self.m+i] = mean*factor
                rates[self.indices[:,i]] = (h*(growth[:,i]-mean)
                    +self.p.dispersal_yr*(self.p.weights*normalizer-h))
        else:
            for j,w in enumerate(self.p.weights):
                for i in range(2):
                    k = 4*j+1+i
                    if w and self.present[j,i]:
                        z = internal[k]
                        rates[k] = growth[j,i]*(1. if z < -30 else np.logaddexp(0.,z)/expit(z))
                    else:
                        rates[k] = 0.
        return rates

    def global_logs(self, internal):
        if self.shared:
            return np.array([_log_softplus(internal[self.m+i]) if self.global_present[i] else -np.inf
                             for i in range(2)])
        return _global_logs(self.decode(internal)[1],self.p.weights)


def _global_logs(local_logs, weights):
    active = weights > 0
    return logsumexp(local_logs[active] + np.log(weights[active, None]), axis=0)


def _real_roots(poly, lo, hi):
    roots = poly.roots()
    return [float(z.real) for z in roots if abs(z.imag) < 1e-8 and lo <= z.real <= hi]


def _accepted_state(dense, time, start_state):
    return start_state if time == dense.t_old else dense(time)


def _ratio_interval(initial,p):
    for bounds in model.supported_ratio_intervals(p):
        if bounds[0]-1e-12 <= initial[-1] <= bounds[1]+1e-12:
            return bounds
    if all(flag != "unsupported" for flag in model.temperature_flags(initial,p)):
        return [float(initial[-1]),float(initial[-1])]
    return None


def _exit_time(dense, left, right, interval, p):
    lo = (left - dense.t) / dense.h
    hi = (right - dense.t) / dense.h
    ratio = Polynomial(dense.yh[p.state_size-1])
    points = [lo, hi]
    for boundary in interval:
        if np.isfinite(boundary):
            points.extend(_real_roots(ratio - boundary, lo, hi))
    points = np.unique(points)
    for a, b in zip(points[:-1], points[1:]):
        r = float(ratio((a + b) / 2))
        if not interval[0] <= r <= interval[1]:
            return float(dense.t + dense.h * a)
    return None


def _negative_allocations(dense,left,right,coordinates,start_state):
    if not coordinates.shared:
        return False
    lo,hi=(left-dense.t)/dense.h,(right-dense.t)/dense.h
    for i in range(2):
        if not coordinates.global_present[i]:
            continue
        for j,w in enumerate(coordinates.p.weights):
            if not w:
                continue
            k=4*j+1+i
            poly=Polynomial(dense.yh[k])
            values=[start_state[k],poly(hi)]
            values.extend(poly(x) for x in _real_roots(poly.deriv(),lo,hi) if lo<x<hi)
            if min(values)<0:
                return True
    return False


def _bracketed_candidates(derivative,stock,lo,hi):
    grid=np.linspace(lo,hi,17)
    values=np.asarray(derivative(grid))
    points=[]
    for k,(a,b) in enumerate(zip(grid[:-1],grid[1:])):
        if values[k]*values[k+1]<0:
            points.append(brentq(derivative,a,b,xtol=1e-13))
        elif values[k]==0 and values[k+1]!=0:
            points.append(float(a))
    samples=np.array([stock(x) for x in grid])
    index=int(np.argmin(samples))
    if hi>lo and 0<index<len(grid)-1:
        points.append(float(minimize_scalar(stock,bounds=(grid[index-1],grid[index+1]),method="bounded",
                                            options={"xatol":1e-12}).x))
    return points


def _dense_minima(dense,left,right,coordinates,start_state):
    lo,hi=(left-dense.t)/dense.h,(right-dense.t)/dense.h
    n=coordinates.n
    values,times=np.full((n,2),-np.inf),np.full((n,2),left)
    if _negative_allocations(dense,left,right,coordinates,start_state):
        raise RuntimeError("Accepted dense allocation left the nonnegative domain")
    for i in range(2):
        if coordinates.shared:
            if not coordinates.global_present[i]:
                continue
            z=Polynomial(dense.yh[coordinates.m+i])
            z_checks=[lo,hi,*_real_roots(z.deriv(),lo,hi)]
            h_polys=[Polynomial(dense.yh[4*j+1+i]) for j in range(n)]
            normalizer=sum(h_polys,Polynomial([0.]))
            rare=max(z(x) for x in z_checks)<-30
            for j,w in enumerate(coordinates.p.weights):
                if not w:
                    continue
                h=h_polys[j]
                points=[*z_checks,*_real_roots(h.deriv(),lo,hi),*_real_roots(normalizer.deriv(),lo,hi)]
                def stock(x):
                    if x==lo:
                        return coordinates.decode(start_state)[1][j,i]
                    allocation=float(h(x))
                    if allocation<=0:
                        return -np.inf
                    return _log_softplus(float(z(x)))+np.log(allocation)-np.log(normalizer(x))-np.log(w)
                h_min=min(start_state[4*j+1+i] if x==lo else float(h(x)) for x in points)
                if h_min>0:
                    if rare:
                        polynomial=z.deriv()*h*normalizer+h.deriv()*normalizer-h*normalizer.deriv()
                        points+=_real_roots(polynomial,lo,hi)
                    else:
                        def derivative(x):
                            v=z(x)
                            factor=_log_softplus_derivative(v)
                            return factor*z.deriv()(x)+h.deriv()(x)/h(x)-normalizer.deriv()(x)/normalizer(x)
                        points+=_bracketed_candidates(derivative,stock,lo,hi)
                stocks=[stock(x) for x in points]
                k=int(np.argmin(stocks))
                values[j,i]=stocks[k]
                times[j,i]=left if points[k]==lo else dense.t+dense.h*points[k]
        else:
            for j,w in enumerate(coordinates.p.weights):
                if not w or not coordinates.present[j,i]:
                    continue
                z=Polynomial(dense.yh[4*j+1+i])
                points=[lo,hi,*_real_roots(z.deriv(),lo,hi)]
                stocks=[coordinates.decode(start_state)[1][j,i] if x==lo else _log_softplus(float(z(x))) for x in points]
                k=int(np.argmin(stocks))
                values[j,i]=stocks[k]
                times[j,i]=left if points[k]==lo else dense.t+dense.h*points[k]
    return values,times


def _dense_global_minima(dense,left,right,coordinates,start_state):
    lo,hi=(left-dense.t)/dense.h,(right-dense.t)/dense.h
    values,times=np.full(2,-np.inf),np.full(2,left)
    for i in range(2):
        if not coordinates.global_present[i]:
            continue
        points=[lo,hi]
        if coordinates.shared:
            z=Polynomial(dense.yh[coordinates.m+i])
            points+=_real_roots(z.deriv(),lo,hi)
            def stock(x):
                return _log_softplus(float(z(x)))
        else:
            patches=[j for j,w in enumerate(coordinates.p.weights) if w and coordinates.present[j,i]]
            polys=[Polynomial(dense.yh[4*j+1+i]) for j in patches]
            log_weights=np.log(coordinates.p.weights[patches])
            for poly in polys:
                points+=_real_roots(poly.deriv(),lo,hi)
            def stock(x):
                return float(logsumexp(log_weights+np.array([_log_softplus(float(z(x))) for z in polys])))
            if len(polys)>1:
                def derivative(x):
                    x=np.asarray(x)
                    z_values=np.array([z(x) for z in polys])
                    logs=log_weights.reshape((-1,)+(1,)*x.ndim)+_array_log_softplus(z_values)
                    fractions=np.exp(logs-logsumexp(logs,axis=0))
                    factors=_log_softplus_derivative(z_values)
                    return np.sum(fractions*factors*np.array([z.deriv()(x) for z in polys]),axis=0)
                points+=_bracketed_candidates(derivative,stock,lo,hi)
        stocks=[coordinates.global_logs(start_state)[i] if x==lo else stock(x) for x in points]
        k=int(np.argmin(stocks))
        values[i]=stocks[k]
        times[i]=left if points[k]==lo else dense.t+dense.h*points[k]
    return values,times


def _negative_initial_acetate(dense,left,right,coordinates,start_state):
    lo,hi=(left-dense.t)/dense.h,(right-dense.t)/dense.h
    for j,w in enumerate(coordinates.p.weights):
        if not w or coordinates.acetate_positive[j]:
            continue
        poly=Polynomial(dense.yh[4*j+3])
        values=[start_state[4*j+3],poly(hi)]
        values.extend(poly(x) for x in _real_roots(poly.deriv(),lo,hi) if lo<x<hi)
        if min(values)<0:
            return True
    return False


def _dense_temperature_range(dense,left,right,p):
    lo,hi=(left-dense.t)/dense.h,(right-dense.t)/dense.h
    ratio=Polynomial(dense.yh[p.state_size-1])
    values=[ratio(x) for x in (lo,hi,*_real_roots(ratio.deriv(),lo,hi))]
    rmin,rmax=min(values),max(values)
    vertices=model.core.response(p.base.climate.case).ratios
    candidates=np.r_[rmin,rmax,vertices[(vertices>=rmin)&(vertices<=rmax)]]
    ts=np.asarray(model.core.temperature_k(candidates,p.base.climate))
    return float(min(ts)),float(max(ts))


def _temperature_metadata(temperature_range,p):
    low,high=temperature_range
    patch_low=np.array([low+patch.value if patch.rule=="tracking" else patch.value for patch in p.patches])
    patch_high=np.array([high+patch.value if patch.rule=="tracking" else patch.value for patch in p.patches])
    tracking=sum(patch.weight for patch in p.patches if patch.rule=="tracking")
    constant=sum(patch.weight*patch.value for patch in p.patches)
    departures=(tracking-1)*np.array([low,high])+constant
    means=tracking*np.array([low,high])+constant
    return dict(global_min_temperature_k=float(low),global_max_temperature_k=float(high),
                patch_min_temperature_k=np.where(p.weights>0,patch_low,np.nan),
                patch_max_temperature_k=np.where(p.weights>0,patch_high,np.nan),
                mean_habitat_min_temperature_k=float(min(means)),mean_habitat_max_temperature_k=float(max(means)),
                temperature_mean_departure_min_k=float(min(departures)),temperature_mean_departure_max_k=float(max(departures)),
                maximum_abs_temperature_mean_departure_k=float(max(abs(departures))))


def integrate(y0, p, years, *, census=None, sample_every_censuses=100, rtol=2e-8, max_step=np.inf):
    """Integrate the continuum, or the stated per-habitat finite census model.

    Continuum output uses accepted step endpoints. Finite output is thinned by
    census stride, retaining all removal states and the terminal/domain state.
    Continuous-piece minima include zero states after removal; pre-removal
    minima stop updating separately for each local lineage at its first cull.
    """
    initial = np.asarray(y0, dtype=float).copy()
    if initial.shape != (p.state_size,) or np.any(~np.isfinite(initial)) or np.any(initial < 0):
        raise ValueError("Provide state_size finite nonnegative physical stocks")
    if not np.isfinite(years) or years < 0:
        raise ValueError("Duration must be finite and nonnegative")
    if not np.isfinite(rtol) or rtol <= 0 or not max_step > 0:
        raise ValueError("Numerical tolerances must be positive")
    if not isinstance(sample_every_censuses, (int, np.integer)) or sample_every_censuses < 1:
        raise ValueError("Sampling stride must be a positive integer")
    if census is not None and not isinstance(census, Census):
        raise ValueError("Use the explicit per-habitat Census process")
    for j, w in enumerate(p.weights):
        if w == 0 and np.any(initial[4 * j:4 * j + 4] != 0):
            raise ValueError("Inactive habitats must have zero local stocks")
        if any(not enabled and initial[4 * j + 1 + i] != 0 for i, enabled in enumerate(p.base.enabled)):
            raise ValueError("Disabled guilds must start absent in all habitats")
    started = perf_counter()
    coordinates = _Coordinates(initial, p)
    allocation_tolerance=(min(1e-14,p.dispersal_yr*min(p.weights[p.weights>0])*1e-7)
                          if coordinates.shared else None)
    initial_internal = coordinates.encode(initial)
    _, initial_logs = coordinates.decode(initial_internal)
    initial_acetate_logs = coordinates.acetate_logs(initial_internal)
    continuum_min, continuum_time = initial_logs.copy(), np.zeros((p.n_patches, 2))
    pre_min, pre_time = initial_logs.copy(), np.zeros((p.n_patches, 2))
    jump_min = initial_logs.copy()
    removed = np.zeros((p.n_patches, 2), dtype=bool)
    global_continuum_min = _global_logs(initial_logs, p.weights)
    global_continuum_time = np.zeros(2)
    global_pre_min, global_pre_time = global_continuum_min.copy(), np.zeros(2)
    global_jump_min = global_continuum_min.copy()
    globally_removed = np.zeros(2, dtype=bool)
    events, census_times, activity = [], [], []
    ledger = {key: np.zeros((p.n_patches, 2)) for key in ("culled_cells", "culled_gdw", "culled_h2_mol", "inventory_jump_h2_mol_l")}
    times, samples, logs, acetate_logs = [], [], [], []
    nfev = steps = resets = 0
    acetate_resets = positivity_retries = allocation_retries = retry_streak = 0
    acetate_switches = []
    domain_exit = None
    initial_temperature = float(model.core.temperature_k(initial[-1], p.base.climate))
    temperature_range = np.array([initial_temperature, initial_temperature])
    interval = (_ratio_interval(initial, p) if all(flag != "unsupported" for flag in model.temperature_flags(initial, p))
                else None)
    status = "completed" if interval is not None else "initial_unsupported"
    conversion = np.full(p.n_patches, -np.inf)
    volumes = np.zeros(p.n_patches)
    if census is not None:
        volumes = p.base.habitat_l_cm2 * census.surface_cm2 * p.weights
        conversion[p.weights > 0] = np.log(volumes[p.weights > 0]) - np.log(census.cell_mass_gdw)
    allocation = np.array([model.core.ASSIMILATION_A, p.base.biology.assimilation_m])

    def append(time, physical, log_stocks, log_acetate):
        if times and abs(times[-1] - time) <= 1e-12 * max(1., abs(time)):
            samples[-1], logs[-1] = physical.copy(), log_stocks.copy()
            acetate_logs[-1] = log_acetate.copy()
        else:
            times.append(float(time)); samples.append(physical.copy()); logs.append(log_stocks.copy())
            acetate_logs.append(log_acetate.copy())

    def perform_census(time, physical, log_stocks):
        changed = False
        guild_culled = np.zeros(2, dtype=bool)
        if census.minimum_cells:
            threshold = np.log(census.minimum_cells) - conversion
            for j, w in enumerate(p.weights):
                if not w:
                    continue
                for i in range(2):
                    if np.isfinite(log_stocks[j, i]) and log_stocks[j, i] < threshold[j] - 1e-12:
                        stock = physical[4 * j + 1 + i]
                        mass = stock * volumes[j]
                        cells = float(np.exp(log_stocks[j, i] + conversion[j]))
                        jump = w * allocation[i] * stock
                        events.append(dict(time_yr=float(time), patch=p.patch_names[j], guild=GUILDS[i],
                                           removed_cells=cells, log_removed_cells=float(log_stocks[j, i] + conversion[j]),
                                           removed_gdw=float(mass), removed_h2_mol=float(mass * allocation[i]),
                                           inventory_jump_h2_mol_l=float(jump)))
                        for key, value in zip(ledger, (cells, mass, mass * allocation[i], jump)):
                            ledger[key][j, i] += value
                        physical[4 * j + 1 + i], log_stocks[j, i] = 0., -np.inf
                        removed[j, i] = True
                        guild_culled[i] = True
                        changed = True
        jump_min[:] = np.minimum(jump_min, log_stocks)
        global_after = _global_logs(log_stocks, p.weights)
        global_jump_min[:] = np.minimum(global_jump_min, global_after)
        globally_removed[:] |= guild_culled & ~np.isfinite(global_after)
        census_times.append(float(time))
        activity.append(sum(int(np.isfinite(log_stocks[j, i])) << (2 * j + i)
                            for j in range(p.n_patches) for i in range(2)))
        return changed

    def update_minima(dense, left, right):
        values, at = _dense_minima(dense, left, right, coordinates, start_state)
        lower = values < continuum_min
        continuum_min[lower], continuum_time[lower] = values[lower], at[lower]
        lower = (values < pre_min) & ~removed
        pre_min[lower], pre_time[lower] = values[lower], at[lower]
        global_values, global_at = _dense_global_minima(dense, left, right, coordinates, start_state)
        lower = global_values < global_continuum_min
        global_continuum_min[lower], global_continuum_time[lower] = global_values[lower], global_at[lower]
        lower = (global_values < global_pre_min) & ~globally_removed
        global_pre_min[lower], global_pre_time[lower] = global_values[lower], global_at[lower]
        low, high = _dense_temperature_range(dense, left, right, p)
        temperature_range[0] = min(temperature_range[0], low)
        temperature_range[1] = max(temperature_range[1], high)

    def from_internal(internal, time, step_limit=max_step):
        atol = np.r_[np.tile([1e-7,1e-8,1e-8,1e-11],p.n_patches),1e-11]
        if coordinates.shared:
            atol=np.r_[atol,[1e-8,1e-8]]
            atol[p.biomass_indices]=allocation_tolerance
        for j in range(p.n_patches):
            if coordinates.acetate_positive[j]:
                atol[4*j+3]=1e-8
        zero_start = any(w and not coordinates.acetate_positive[j] for j, w in enumerate(p.weights))
        first_step = min(1e-6*p.base.acetate_lifetime_yr, years-time, step_limit) if zero_start else None
        return LSODA(coordinates.derivative, time, internal, years, rtol=rtol, atol=atol,
                     max_step=step_limit, first_step=first_step)

    def make_solver(physical, time, previous_internal=None, *, preserve_biomass=False):
        nonlocal coordinates
        old_coordinates = coordinates
        coordinates = _Coordinates(physical, p)
        internal = coordinates.encode(physical)
        if previous_internal is not None:
            for j in range(p.n_patches):
                if old_coordinates.acetate_positive[j]:
                    coordinates.acetate_positive[j] = True
                    internal[4*j+3] = previous_internal[4*j+3]
            if preserve_biomass:
                coordinates.present = old_coordinates.present.copy()
                coordinates.global_present = old_coordinates.global_present.copy()
                internal[p.biomass_indices] = previous_internal[p.biomass_indices]
                if coordinates.shared:
                    internal[p.state_size:]=previous_internal[p.state_size:]
        return from_internal(internal, time)

    if status == "initial_unsupported":
        domain_exit = dict(time_yr=0., temperatures_k=model.temperatures(initial, p),
                           physiology_domains=model.temperature_flags(initial, p))
        append(0., initial, initial_logs, initial_acetate_logs)
    else:
        if census is not None:
            perform_census(0., initial, initial_logs)
        append(0., initial, initial_logs, initial_acetate_logs)
        solver = make_solver(initial, 0.) if years else None
        next_census = census.census_yr if census is not None else np.inf
        census_number = 1
        while solver is not None and solver.status == "running":
            start_state, start_time = solver.y.copy(), float(solver.t)
            message = solver.step()
            if solver.status == "failed":
                raise RuntimeError(f"Refuge integration failed: {message}")
            dense = solver.dense_output()
            left, right = float(dense.t_old), float(dense.t)
            exit_at = _exit_time(dense, left, right, interval, p)
            end = right if exit_at is None else min(right, max(left, exit_at))
            negative_acetate=_negative_initial_acetate(dense,left,end,coordinates,start_state)
            negative_allocation=_negative_allocations(dense,left,end,coordinates,start_state)
            if negative_acetate or negative_allocation:
                positivity_retries+=int(negative_acetate)
                allocation_retries+=int(negative_allocation)
                retry_streak+=1
                if retry_streak>20:
                    raise RuntimeError("Cannot retain nonnegative accepted inventories with step refinement")
                nfev+=solver.nfev
                solver=from_internal(start_state,start_time,(right-left)/2)
                continue
            retry_streak=0
            steps += 1
            restarted = False
            while next_census <= end + 16 * np.finfo(float).eps * max(1., end):
                time = min(next_census, end)
                accepted = _accepted_state(dense, time, start_state)
                physical, log_stocks = coordinates.decode(accepted)
                if np.any(physical[p.biomass_indices] < 0):
                    raise RuntimeError("Accepted population left its physical domain")
                will_cull = (census.minimum_cells > 0 and np.any(np.isfinite(log_stocks)
                             & (log_stocks < (np.log(census.minimum_cells) - conversion)[:, None] - 1e-12)))
                if will_cull:
                    update_minima(dense, left, time)
                changed = perform_census(time, physical, log_stocks)
                if changed or census_number % sample_every_censuses == 0 or time == years:
                    append(time, physical, log_stocks, coordinates.acetate_logs(accepted))
                census_number += 1
                next_census = census_number * census.census_yr
                if changed:
                    for j, w in enumerate(p.weights):
                        if w and not coordinates.acetate_positive[j] and physical[4*j+3] > 0:
                            acetate_switches.append(dict(time_yr=time, patch=p.patch_names[j],
                                acetate_mol_l=float(physical[4*j+3]),
                                source="Positive accepted census state; coordinate conversion shares the census reset"))
                    nfev += solver.nfev
                    solver = make_solver(physical, time, accepted) if time < years else None
                    resets += 1
                    restarted = True
                    break
            if restarted:
                continue
            update_minima(dense, left, end)
            accepted = _accepted_state(dense, end, start_state)
            physical, log_stocks = coordinates.decode(accepted)
            if np.any(physical[p.biomass_indices] < 0):
                raise RuntimeError("Accepted population left its physical domain")
            if census is None or end == years or exit_at is not None:
                append(end, physical, log_stocks, coordinates.acetate_logs(accepted))
            if exit_at is not None:
                status = "domain_exit"
                domain_exit = dict(time_yr=end, temperatures_k=model.temperatures(physical, p),
                                   physiology_domains=model.temperature_flags(physical, p), ratio_interval=interval)
                break
            switching = [j for j, w in enumerate(p.weights) if w and not coordinates.acetate_positive[j]
                         and physical[4*j+3] > 0]
            if switching and end < years:
                for j in switching:
                    acetate_switches.append(dict(time_yr=end, patch=p.patch_names[j], acetate_mol_l=float(physical[4*j+3]),
                                                  source="First positive accepted endpoint; no inventory added"))
                nfev += solver.nfev
                solver = make_solver(physical, end, accepted, preserve_biomass=True)
                acetate_resets += 1
        if solver is not None:
            nfev += solver.nfev
    return HabitatResult(np.asarray(times), np.asarray(samples).T,
                        np.moveaxis(np.asarray(logs), 0, -1),
                        np.asarray(acetate_logs).T,
                        np.asarray([model.temperatures(y, p) for y in samples]).T,
                        np.asarray([model.temperature_flags(y, p) for y in samples]).T,
                        np.asarray([str(model.core.domain(y[-1], p.base.climate)) for y in samples]),
                        status == "completed", status, domain_exit,
                        np.asarray(census_times), np.asarray(activity, dtype=object), events,
                        continuum_min, continuum_time, pre_min, pre_time, jump_min,
                        global_continuum_min, global_continuum_time, global_pre_min, global_pre_time,
                        global_jump_min, ledger,
                        dict(nfev=nfev, accepted_steps=steps, solver_resets=resets+acetate_resets+positivity_retries+allocation_retries,
                             relative_tolerance=rtol,allocation_absolute_tolerance=allocation_tolerance,
                             census_solver_resets=resets, acetate_coordinate_resets=acetate_resets,
                             acetate_positivity_retries=positivity_retries, allocation_positivity_retries=allocation_retries, acetate_coordinate_switches=acetate_switches,
                             initial_acetate_coordinate=["inactive" if not w else "softplus" if initial[4*j+3] > 0
                                                         else "zero_linear" for j, w in enumerate(p.weights)],
                             wall_seconds=perf_counter() - started,
                             n_censuses=len(census_times),
                             last_physical_time_yr=float(times[-1]),
                             census=None if census is None else dict(minimum_cells=census.minimum_cells,
                                census_yr=census.census_yr, cell_mass_gdw=census.cell_mass_gdw, surface_cm2=census.surface_cm2),
                             patch_volume_l=None if census is None else volumes, external_immigration="none",
                             global_log_cell_conversion=(None if census is None else
                                np.log(p.base.habitat_l_cm2 * census.surface_cm2) - np.log(census.cell_mass_gdw)),
                             supported_ratio_interval=interval,
                             minimum_scope="Extrema of accepted LSODA dense flow pieces; full piece minima include zeros after removals; pre-removal minima freeze per lineage at first local removal",
                             extrema_search="Polynomial stationary points for independent stocks and rare total-biomass tails; 17-node derivative bracketing and detected-basin bounded refinement otherwise, not interval-certified",
                             global_minimum_scope="Simultaneous area-weighted B=sum(w_j X_j), in gDW/L; pre-extinction flow minima freeze only when a census removes the final surviving patch of that guild; post-census jumps are separate; do not sum local minima",
                             global_extrema_search="Total-softplus polynomial extrema for positive dispersal; weighted logsumexp with17-node derivative bracketing and bounded refinement otherwise, not interval-certified",
                             **_temperature_metadata(temperature_range,p),
                             temperature_range_scope="Initial state and accepted dense flow pieces, using r-polynomial extrema and radiative vertices; no Newton trials or discarded future after a census",
                             after_census_scope="Minimum of initial and post-census states; zeroing is an explicit jump; with n_censuses=0 this field describes only the initial state",
                             numerical_trial_extension="Boundary physiology frozen for internal trials only; accepted trajectory stops at connected supported-r boundary",
                             dense_boundary_scope="At each step's left boundary use the saved accepted internal state, avoiding Nordsieck endpoint roundoff; interior polynomial extrema remain strictly checked",
                             allocation_coordinate="Weighted total-guild softplus and all N explicit nonnegative allocations normalized by their actual sum; independent positive patch stocks at zero dispersal",
                             underflow_scope="Logarithmic stocks remain finite below physical floating-point representation; only explicit censuses remove lineages",
                             acetate_coordinate="Positive inventory softplus; exact-zero starts linear until a positive accepted endpoint, then changes coordinates without adding inventory; zero-production rare tails decay at -k",
                             acetate_zero_start_first_step_max_yr=1e-6*p.base.acetate_lifetime_yr,
                             sampling="Accepted step endpoints for continuum; census-stride, removal and terminal states for finite runs",
                             final_temperatures_k=model.temperatures(samples[-1], p),
                             final_physiology_domains=model.temperature_flags(samples[-1], p)))


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
