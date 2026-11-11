"""A named kinetic-position variant; reference physiology remains unchanged.

Traits translate only the measured V/K shapes. Thresholds, maintenance and
biomass yield remain properties of the actual temperature unless an explicit
S2 freeze is requested. Trait temperatures are degrees C; local T is kelvin.
"""
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import minimize_scalar

from . import two_guilds as reference

KB_EV = 8.617333e-5
NODES_C = np.asarray(reference.TEMPERATURES_C)
TRAIT_GRID_C = np.round(np.arange(4., 30.0001, .01), 2)
INTERPOLATIONS = ('linear_shape', 'smooth_shape')


@dataclass(frozen=True)
class Traits:
    positions_c: tuple[float, float]
    energy_ev: float
    interpolation: str = 'linear_shape'
    freeze_thresholds: bool = False
    freeze_maintenance: bool = False

    def __post_init__(self):
        if len(self.positions_c) != 2 or not all(np.isfinite(t) and 4. <= t <= 30. for t in self.positions_c):
            raise ValueError('Kinetic positions must lie in the measured 4–30 C interval')
        if not np.isfinite(self.energy_ev) or self.energy_ev < 0:
            raise ValueError('Energy must be finite and nonnegative, in eV')
        if self.interpolation not in INTERPOLATIONS:
            raise ValueError('Unknown kinetic interpolation')


@lru_cache(maxsize=128)
def profiles(biology):
    pair = [reference.guilds(t, biology) for t in NODES_C]
    v = np.array([[g[i].rate_scale for g in pair] for i in range(2)])
    k = np.array([[g[i].km_pa for g in pair] for i in range(2)])
    if np.any(v <= 0) or np.any(k <= 0):
        raise ValueError('Log-shape interpolation requires positive measured V and K')
    return v, k, tuple(PchipInterpolator(NODES_C, np.log(x)) for x in v), tuple(PchipInterpolator(NODES_C, np.log(x)) for x in k)


def shape(positions_c, biology, interpolation='linear_shape'):
    u = np.asarray(positions_c, dtype=float)
    if np.any(~np.isfinite(u)) or np.any((u < 4.) | (u > 30.)):
        raise ValueError('No kinetic extrapolation beyond measured 4–30 C')
    v, k, pv, pk = profiles(biology)
    if interpolation == 'linear_shape':
        return np.array([np.interp(u, NODES_C, x) for x in v]), np.array([np.interp(u, NODES_C, x) for x in k])
    if interpolation == 'smooth_shape':
        return np.array([np.exp(x(u)) for x in pv]), np.array([np.exp(x(u)) for x in pk])
    raise ValueError('Unknown kinetic interpolation')


def local_guilds(t_k, biology, *, freeze_thresholds=False, freeze_maintenance=False):
    actual = reference.guilds(float(t_k)-273.15, biology)
    if not (freeze_thresholds or freeze_maintenance):
        return actual
    warm = reference.guilds(30., biology)
    return tuple(replace(g, threshold_pa=w.threshold_pa if freeze_thresholds else g.threshold_pa,
                         maintenance=w.maintenance if freeze_maintenance else g.maintenance)
                 for g, w in zip(actual, warm))


def guilds(t_k, biology, traits):
    local = local_guilds(t_k, biology, freeze_thresholds=traits.freeze_thresholds,
                         freeze_maintenance=traits.freeze_maintenance)
    values_v, values_k = shape(np.asarray(traits.positions_c), biology, traits.interpolation)
    factors = np.exp(-traits.energy_ev/KB_EV*(1/float(t_k)-1/(np.asarray(traits.positions_c)+273.15)))
    return tuple(replace(g, rate_scale=float(values_v[i, i]*factors[i]), km_pa=float(values_k[i, i]))
                 for i, g in enumerate(local))


@lru_cache(maxsize=256)
def grid_profiles(biology, energy_ev, interpolation):
    if not np.isfinite(energy_ev) or energy_ev < 0:
        raise ValueError('Energy must be finite and nonnegative, in eV')
    v, k = shape(TRAIT_GRID_C, biology, interpolation)
    return v*np.exp(energy_ev/KB_EV/(TRAIT_GRID_C+273.15)), k


def rstar_grid(t_k, biology, energy_ev, interpolation='linear_shape', *, freeze_thresholds=False, freeze_maintenance=False):
    local = local_guilds(t_k, biology, freeze_thresholds=freeze_thresholds, freeze_maintenance=freeze_maintenance)
    weighted, k = grid_profiles(biology, float(energy_ev), interpolation)
    v = weighted*np.exp(-energy_ev/KB_EV/float(t_k))
    values=[]
    for i, g in enumerate(local):
        q=g.maintenance+biology.loss_h/g.yield_g_mol
        if g.kinetics == 'first_order':
            r=g.threshold_pa+k[i]*q/v[i]
        else:
            r=g.threshold_pa+np.divide(k[i]*q,v[i]-q,out=np.full_like(v[i],np.inf),where=v[i]>q)
        values.append(r)
    return np.asarray(values)


def uptake_grid(pressure_pa, t_k, biology, energy_ev, interpolation='linear_shape', *, freeze_thresholds=False, freeze_maintenance=False):
    local=local_guilds(t_k, biology, freeze_thresholds=freeze_thresholds, freeze_maintenance=freeze_maintenance)
    weighted,k=grid_profiles(biology,float(energy_ev),interpolation)
    v=weighted*np.exp(-energy_ev/KB_EV/float(t_k))
    growth=[]
    for i,g in enumerate(local):
        available=max(float(pressure_pa)-g.threshold_pa,0.)
        uptake=v[i]*available/(k[i]+available) if g.kinetics=='saturating' else v[i]*available/k[i]
        growth.append(g.yield_g_mol*(uptake-g.maintenance)-biology.loss_h)
    return TRAIT_GRID_C.copy(),np.asarray(growth)


def best_response(t_k, biology, energy_ev, interpolation='linear_shape', *, freeze_thresholds=False, freeze_maintenance=False, refine=True):
    values=rstar_grid(t_k,biology,energy_ev,interpolation,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance)
    local=local_guilds(t_k,biology,freeze_thresholds=freeze_thresholds,freeze_maintenance=freeze_maintenance)
    details=[]
    for i,g in enumerate(local):
        grid_index=int(np.argmin(values[i])); grid_value=float(values[i,grid_index]); grid_position=float(TRAIT_GRID_C[grid_index])
        if not np.isfinite(grid_value):
            details.append(dict(position_c=None,rstar_pa=np.inf,grid_position_c=None,grid_rstar_pa=np.inf,kind='infeasible',tied_positions_c=[]));continue
        def objective(u):
            vv,kk=shape(float(u),biology,interpolation)
            vv=float(vv[i])*np.exp(-energy_ev/KB_EV*(1/float(t_k)-1/(float(u)+273.15)))
            return replace(g,rate_scale=vv,km_pa=float(kk[i])).rstar(biology.loss_h)
        candidates=[(grid_value,grid_position)]
        if refine:
            for j in np.flatnonzero((values[i,1:-1]<=values[i,:-2])&(values[i,1:-1]<=values[i,2:]))+1:
                if not np.isfinite(values[i,j]) or values[i,j]>grid_value+max(1e-8,abs(grid_value)*1e-4):continue
                left,right=TRAIT_GRID_C[j-1],TRAIT_GRID_C[j+1]
                result=minimize_scalar(objective,bounds=(left,right),method='bounded',options={'xatol':1e-10})
                candidates.append((float(result.fun),float(result.x)))
            candidates.extend((float(objective(u)),float(u)) for u in NODES_C)
        best=min(candidates,key=lambda z:(z[0],z[1])); position=best[1]
        near=NODES_C[np.argmin(abs(NODES_C-position))]
        if abs(position-near)<2e-7 and objective(float(near))<=best[0]+max(1e-10,abs(best[0])*1e-11):
            position=float(near);best=(float(objective(position)),position)
        kind='lower_bound' if position==4. else 'upper_bound' if position==30. else 'corner' if interpolation=='linear_shape' and np.min(abs(NODES_C-position))<1e-7 else 'interior'
        tolerance=max(1e-10,abs(best[0])*1e-10)
        ties=sorted(set(u for value,u in candidates if np.isfinite(value) and abs(value-best[0])<=tolerance))
        details.append(dict(position_c=position,rstar_pa=best[0],grid_position_c=grid_position,grid_rstar_pa=grid_value,kind=kind,at_shape_node=bool(np.min(abs(NODES_C-position))<1e-7),tied_positions_c=ties))
    return dict(positions_c=tuple(r['position_c'] for r in details),rstars_pa=tuple(r['rstar_pa'] for r in details),guild_results=details,
                trait_grid_step_c=.01,continuous_refinement=bool(refine))
