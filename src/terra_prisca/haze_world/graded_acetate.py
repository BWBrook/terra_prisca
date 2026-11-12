"""Homogeneous acetate-exponent dial, a named Stage B double-prime variant."""

from dataclasses import dataclass, replace

import numpy as np

from . import continuum_core as weighted
from . import dynamic_core as reference
from . import population_coupling as core
from .two_guilds import guilds

YEAR = core.HOURS_PER_YEAR


@dataclass(frozen=True)
class Params(weighted.WeightedParams):
    chemistry: str = 'acetate_only'
    kappa: float = 0.

    def __post_init__(self):
        super().__post_init__()
        if self.chemistry != 'acetate_only' or self.sigma_k != 0 or self.n != 1:
            raise ValueError('The acetate-exponent dial is homogeneous with methane activity fixed')
        if not np.isfinite(self.kappa) or not 0 <= self.kappa <= 1:
            raise ValueError('Acetate exponent strength must lie between zero and one')
        if not all(self.base.enabled):
            raise ValueError('The graded dial follows positive two-guild states')


def parameters(kappa, fraction, potential=.3):
    return Params(replace(core.reference(potential), acetate_fraction=fraction), kappa=float(kappa))


def pair(y, temperature_k, p):
    result = guilds(float(temperature_k)-273.15, p.base.biology)
    if y[3] < 0:
        raise ValueError('Acetate concentration must be nonnegative')
    factor = 1. if p.kappa == 0 else (y[3]/p.base.acetate_reference_mol_l)**(p.kappa/4)
    return replace(result[0], threshold_pa=result[0].threshold_pa*factor), result[1]


def _at_temperature(y, p, temperature_k, derivatives=True):
    y = np.asarray(y, float)
    pressure, xa, xm, acetate, _ = y
    gs = pair(y, temperature_k, p)
    biomass = np.array([xa, xm])
    uptake = np.array([float(g.uptake(pressure)) for g in gs])
    yields = np.array([g.yield_g_mol for g in gs])
    synthesis = yields*(uptake-np.array([g.maintenance for g in gs]))
    assimilation = np.array([g.assimilation_mol_g for g in gs])
    catabolism = uptake-assimilation*np.maximum(synthesis, 0.)
    rec, export = core.recycling_rates(temperature_k, p.base)
    local = np.r_[YEAR/core.HENRY_30C_MOL_L_PA*(core.supply_h2(p.base)-uptake@biomass
                    -p.base.biology.exchange_mol_l_h_pa*(pressure-p.base.biology.atmosphere_pa)),
                  YEAR*biomass*(synthesis-p.base.biology.loss_h),
                  YEAR*catabolism[0]*xa/4-(rec+export)*acetate]
    conversion = core.inventory_to_ratio(p.base)
    emitted = conversion*(YEAR*catabolism[1]*xm/4+rec*acetate)
    dq = np.zeros((2, 4))
    dq[:, 0] = [g.rate_scale*g.km_pa/(g.km_pa+pressure-g.threshold_pa)**2
                if pressure > g.threshold_pa else 0. for g in gs]
    if p.kappa and derivatives:
        if acetate <= 0:
            raise ValueError('The acetate derivative requires a positive product stock')
        dq[0, 3] = -dq[0, 0]*gs[0].threshold_pa*p.kappa/(4*acetate)
    matrix = np.zeros((4, 4))
    matrix[0] = -YEAR/core.HENRY_30C_MOL_L_PA*(biomass@dq)
    matrix[0, 0] -= YEAR/core.HENRY_30C_MOL_L_PA*p.base.biology.exchange_mol_l_h_pa
    matrix[0, 1:3] = -YEAR/core.HENRY_30C_MOL_L_PA*uptake
    for k in (0, 1):
        matrix[1+k] = YEAR*biomass[k]*yields[k]*dq[k]
        matrix[1+k, 1+k] += YEAR*(synthesis[k]-p.base.biology.loss_h)-p.dispersal_yr
    dcat = (1-assimilation*yields*(synthesis > 0.))[:, None]*dq
    matrix[3] = YEAR/4*xa*dcat[0]
    matrix[3, 1] += YEAR/4*catabolism[0]
    matrix[3, 3] -= rec+export
    emission_row = conversion*YEAR/4*xm*dcat[1]
    emission_row[2] += conversion*YEAR/4*catabolism[1]
    emission_row[3] += conversion*rec
    return local, float(emitted), matrix, emission_row, YEAR*(synthesis-p.base.biology.loss_h)


def physical_rhs(y, p, temperature_k=None):
    y = np.asarray(y, float)
    if y.shape != (5,):
        raise ValueError('Use the five homogeneous physical stocks')
    t = reference.temperature(y[-1], p) if temperature_k is None else float(temperature_k)
    local, emitted, *_ = _at_temperature(y, p, t, derivatives=False)
    abiotic = core.atmosphere(p.base.climate.case)['flux_to_ratio_per_yr']*p.base.climate.abiotic_flux
    return np.r_[local, emitted+abiotic-p.base.loss.rate(y[-1])]


def per_capita(y, p):
    return _at_temperature(np.asarray(y), p, reference.temperature(y[-1], p), derivatives=False)[-1]


def blocks(y, p, temperature_step=1e-4, side=0):
    y = np.asarray(y, float)
    t = reference.temperature(y[-1], p)
    _, _, matrix, emission, _ = _at_temperature(y, p, t)
    step = float(temperature_step)
    lower = 277.15 if p.base.biology.low_temperature_variant == 'none' else 273.
    if t-lower < 2*step:
        points, coefficients, denominator = (0, 1, 2), (-3, 4, -1), 2*step
    elif 303.15-t < 2*step:
        points, coefficients, denominator = (0, -1, -2), (3, -4, 1), 2*step
    else:
        points, coefficients, denominator = (-2, -1, 1, 2), (1, -8, 8, -1), 12*step
    thermal = np.zeros(5)
    for offset, coefficient in zip(points, coefficients):
        flow = _at_temperature(y, p, t+offset*step, derivatives=False)
        thermal += coefficient*np.r_[flow[0], flow[1]]/denominator
    injection = np.zeros((1, 4, 2))
    injection[0, 1, 0] = injection[0, 2, 1] = p.dispersal_yr
    return weighted.Blocks(matrix[None, :, :], injection, np.zeros((1, 4)), thermal[:4][None, :],
        emission[None, :], -float(p.base.loss.slope(y[-1])), float(thermal[-1]),
        np.array([[0., 1., 0., 0.], [0., 0., 1., 0.]]), p.weights,
        reference.climate_slope(y[-1], p, side))


def local_blocks(y, p, temperature_step=1e-4, side=0):
    return blocks(y, p, temperature_step, side)


def _projection(share):
    expand = np.zeros((5, 4)); collapse = np.zeros((4, 5))
    expand[0, 0] = expand[3, 2] = expand[4, 3] = 1.
    expand[1, 1] = share; expand[2, 1] = 1-share
    collapse[0, 0] = collapse[2, 3] = collapse[3, 4] = 1.
    collapse[1, 1:3] = 1.
    return expand, collapse


def equilibrium(seed, p, tolerance=1e-10, max_steps=80, frozen_share=None):
    y = np.asarray(seed, float).copy()
    if y.shape != (5,) or np.any(y <= 0):
        return None
    if frozen_share is None:
        expand = collapse = np.eye(5)
    else:
        if not 0 < frozen_share < 1:
            raise ValueError('The frozen local share must be strictly mixed')
        expand, collapse = _projection(float(frozen_share))
        y = expand@(collapse@y)
    def score(state):
        if np.any(state <= 0) or reference.temperature_status(state, p)['physiology_status'] != 'in_domain':
            return np.inf
        f = physical_rhs(state, p)
        if frozen_share is None:
            return max(float(np.max(abs(f/reference.state_scales(state, p)))), float(max(abs(per_capita(state, p)))))
        total = state[1]+state[2]
        reduced = collapse@f
        scales = np.r_[max(state[0], 10.), max(total, 1e-5), max(state[3], 1e-6), max(state[4], .01)]
        return max(float(max(abs(reduced/scales))), float(abs(reduced[1]/total)))
    value = score(y)
    iteration = 0
    for iteration in range(max_steps):
        if value < tolerance:
            break
        b = blocks(y, p); b.climate_slope /= p.slope_multiplier
        matrix = collapse@weighted.dense_matrix(y, p, blocks=b)@expand
        try:
            delta = expand@np.linalg.solve(matrix, -collapse@physical_rhs(y, p))
        except np.linalg.LinAlgError:
            return None
        fraction = min(1., float(.7/max(np.max(abs(delta/y)), .7)))
        accepted = False
        for _ in range(24):
            trial = y+fraction*delta
            trial_value = score(trial)
            if trial_value < value:
                y, value, accepted = trial, trial_value, True
                break
            fraction /= 2
        if not accepted:
            return None
    if value >= tolerance:
        return None
    return dict(y=y, r=float(y[-1]), t_k=reference.temperature(y[-1], p), residual=value,
                iterations=iteration, status='accepted', **reference.temperature_status(y, p))


def slopes(y, p, side=0):
    b = blocks(y, p, side=side)
    if b.climate_slope == 0:
        return dict(status='climate_insensitive', Sc=0., S0=0., G_loc=None)
    forcing = np.zeros((1, 4))
    forcing[0, 0] = YEAR/core.HENRY_30C_MOL_L_PA*core.supply_h2(p.base)
    result = {}
    for name, matrix, source in (('Sc', b, forcing), ('S0', weighted.frozen_blocks(y, p, b), forcing[:, [0, 1, 3]])):
        try:
            derivative, condition = weighted.block_solve(matrix, -source, 0.)
            result[name] = float(b.climate_slope*derivative[-1])
            result[name+'_schur_condition'] = condition
        except np.linalg.LinAlgError:
            result[name] = result[name+'_schur_condition'] = None
    status = ('singular_response' if result['Sc'] is None or result['S0'] is None else
              'zero_frozen_slope' if abs(result['S0']) < 1e-10 else 'defined')
    return dict(result, status=status, G_loc=result['Sc']/result['S0'] if status == 'defined' else None)


def frozen_supply_check(y, p, step=1e-4):
    y = np.asarray(y)
    share = float(y[1]/(y[1]+y[2])); points = []
    for offset in (-step, step):
        climate = replace(p.base.climate, donor_flux=p.base.climate.donor_flux*np.exp(offset))
        q = replace(p, base=replace(p.base, climate=climate))
        found = equilibrium(y, q, frozen_share=share)
        if found is None:
            return dict(status='unresolved', S0_finite_difference=None, points=points)
        state = found['y']
        points.append(dict(log_input_offset=float(offset), y=state, residual=found['residual'],
                           maximum_ratio_error=float(abs(state[1]/(state[1]+state[2])-share)),
                           temperature_k=found['t_k']))
    slope = (points[1]['temperature_k']-points[0]['temperature_k'])/(2*step)
    return dict(status='passed', S0_finite_difference=float(slope), points=points)
