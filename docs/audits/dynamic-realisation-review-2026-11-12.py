"""Independent selected B1 algebra/finite-difference audit; no production grid."""
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import argparse
import json

import numpy as np
from scipy.optimize import brentq, root

from terra_prisca.haze_world import population_coupling as pc, two_guilds as tg

ROOT = Path(__file__).resolve().parents[2]


def abiotic(parameters):
    return pc.atmosphere(parameters.climate.case)['flux_to_ratio_per_yr']*parameters.climate.abiotic_flux


def traits_at(y, temperature, parameters, chemistry):
    pair = tg.guilds(float(temperature - 273.15), parameters.biology)
    h = np.array([g.threshold_pa for g in pair])
    if chemistry in ('products', 'acetate_only'):
        h[0] *= (y[3]/parameters.acetate_reference_mol_l)**.25
    if chemistry in ('products', 'methane_only'):
        h[1] *= (y[4]*pc.co2_pressure_pa(parameters.climate.case)/parameters.methane_reference_pa)**.25
    return pair, h


def physical(y, temperature, parameters, chemistry):
    pressure, xa, xm, acetate, ratio = np.asarray(y, float)
    pair, thresholds = traits_at(y, temperature, parameters, chemistry)
    available = np.maximum(pressure-thresholds, 0.)
    capacity = np.array([g.rate_scale for g in pair])
    km = np.array([g.km_pa for g in pair])
    maintenance = np.array([g.maintenance for g in pair])
    yields = np.array([g.yield_g_mol for g in pair])
    coefficients = np.array([g.assimilation_mol_g for g in pair])
    uptake = capacity*available/(km+available)
    synthesis = yields*(uptake-maintenance)
    stocks = np.array([xa, xm])*parameters.enabled
    catabolic = (uptake-coefficients*np.maximum(synthesis, 0.))*stocks*pc.HOURS_PER_YEAR
    rec, other = pc.recycling_rates(temperature, parameters)
    conversion = pc.inventory_to_ratio(parameters)
    return np.r_[
        (pc.supply_h2(parameters)-uptake@stocks-parameters.biology.exchange_mol_l_h_pa*(pressure-parameters.biology.atmosphere_pa))*pc.HOURS_PER_YEAR/pc.HENRY_30C_MOL_L_PA,
        stocks*(synthesis-parameters.biology.loss_h)*pc.HOURS_PER_YEAR,
        catabolic[0]/4-(rec+other)*acetate,
        conversion*(catabolic[1]/4+rec*acetate)+abiotic(parameters)-parameters.loss.rate(ratio),
    ]


def material(temperature, ratio, parameters, chemistry):
    pair = tg.guilds(float(temperature - 273.15), parameters.biology)
    needed = np.array([g.maintenance+parameters.biology.loss_h/g.yield_g_mol for g in pair])
    capacity = np.array([g.rate_scale for g in pair])
    if np.any(needed >= capacity):
        return None
    h = np.array([g.threshold_pa for g in pair])
    if chemistry in ('products', 'methane_only'):
        h[1] *= (ratio*pc.co2_pressure_pa(parameters.climate.case)/parameters.methane_reference_pa)**.25
    kinetic_pressure = np.array([g.km_pa for g in pair])*needed/(capacity-needed)
    pressure = h[1]+kinetic_pressure[1]
    captured = pc.supply_h2(parameters)-parameters.biology.exchange_mol_l_h_pa*(pressure-parameters.biology.atmosphere_pa)
    catabolic = needed-np.array([g.assimilation_mol_g for g in pair])*parameters.biology.loss_h
    rec, other = pc.recycling_rates(temperature, parameters)
    a_per_x = catabolic[0]*pc.HOURS_PER_YEAR/(4*(rec+other))
    methane_needed = (parameters.loss.rate(ratio)-abiotic(parameters))/pc.inventory_to_ratio(parameters)/pc.HOURS_PER_YEAR
    if chemistry in ('products', 'acetate_only'):
        if pressure <= kinetic_pressure[0] or h[0] <= 0:
            return None
        xa = parameters.acetate_reference_mol_l/a_per_x*((pressure-kinetic_pressure[0])/h[0])**4
        xm = (captured-needed[0]*xa)/needed[1]
        acetate = a_per_x*xa
        residual = catabolic[1]*xm/4+rec*acetate/pc.HOURS_PER_YEAR-methane_needed
    else:
        conversion = np.array([[needed[0], needed[1]],
                               [parameters.acetate_fraction*catabolic[0]/4, catabolic[1]/4]])
        xa, xm = np.linalg.solve(conversion, [captured, methane_needed])
        acetate = a_per_x*xa
        residual = h[0]+kinetic_pressure[0]-pressure
    return np.array([pressure, xa, xm, acetate, ratio]), float(residual)


def equilibria(parameters, chemistry):
    curve = pc.response(parameters.climate.case)
    rows = []
    for a, b, ta, tb in zip(curve.ratios[:-1], curve.ratios[1:], curve.temperatures_k[:-1], curve.temperatures_k[1:]):
        if tb >= ta:
            continue
        def evaluate(r):
            t = float(pc.temperature_k(r, parameters.climate))
            value = material(t, r, parameters, chemistry)
            return value[1] if value is not None else np.nan
        grid = np.linspace(a, b, 25)
        for lo, hi in zip(grid[:-1], grid[1:]):
            flo, fhi = evaluate(lo), evaluate(hi)
            if np.isfinite(flo) and np.isfinite(fhi) and flo*fhi < 0:
                root = brentq(evaluate, lo, hi, xtol=1e-14)
                temp = float(pc.temperature_k(root, parameters.climate))
                y, residual = material(temp, root, parameters, chemistry)
                if min(y) > 0 and not any(abs(root-r['ratio']) < 1e-9 for r in rows):
                    rows.append(dict(y=y, temperature_k=temp, ratio=float(root), scalar_residual=residual))
    return rows


def derivative(fun, y, scales, step):
    result = []
    for i, scale in enumerate(scales):
        shift = np.eye(len(y))[i]*scale*step
        result.append((-fun(y+2*shift)+8*fun(y+shift)-8*fun(y-shift)+fun(y-2*shift))/(12*scale*step))
    return np.array(result).T


def methanogen_control(parameters, chemistry, step):
    control = replace(parameters, enabled=(False, True))
    def state(r):
        temp = float(pc.temperature_k(r, control.climate))
        pair = tg.guilds(temp-273.15, control.biology)
        g = pair[1]
        needed = g.maintenance+control.biology.loss_h/g.yield_g_mol
        if needed >= g.rate_scale:
            return None
        h = g.threshold_pa
        if chemistry in ('products', 'methane_only'):
            h *= (r*pc.co2_pressure_pa(control.climate.case)/control.methane_reference_pa)**.25
        pressure = h+g.km_pa*needed/(g.rate_scale-needed)
        captured = pc.supply_h2(control)-control.biology.exchange_mol_l_h_pa*(pressure-control.biology.atmosphere_pa)
        xm = captured/needed
        y = np.array([pressure, 0., xm, 0., r])
        return y, temp, float(physical(y, temp, control, chemistry)[-1])
    ratios = np.unique(np.r_[np.geomspace(1e-7, 2., 600), pc.response(control.climate.case).ratios])
    out = []
    for lo, hi in zip(ratios[:-1], ratios[1:]):
        a, b = state(lo), state(hi)
        if a is None or b is None or a[-1]*b[-1] >= 0:
            continue
        root = brentq(lambda r: state(r)[-1], lo, hi, xtol=1e-14)
        y, temp, _ = state(root)
        if y[2] <= 0:
            continue
        indices = [0, 2, 4]
        def flow(z):
            embedded = np.array([z[0], 0., z[1], 0., z[2]])
            return physical(embedded, float(pc.temperature_k(z[-1], control.climate)), control, chemistry)[indices]
        scales = np.maximum(abs(y[indices]), [10., 1e-4, .01])
        jac = derivative(flow, y[indices], scales, step)
        eig = np.linalg.eigvals(jac*scales[None, :]/scales[:, None])
        if max(eig.real) >= 0:
            continue
        forcing = np.r_[pc.supply_h2(control)*pc.HOURS_PER_YEAR/pc.HENRY_30C_MOL_L_PA, 0., 0.]
        response = np.linalg.solve(jac, -forcing)
        dr = 1e-6
        slope = float((pc.temperature_k(root+dr, control.climate)-pc.temperature_k(root-dr, control.climate))/(2*dr))
        out.append(dict(temperature_k=temp, ratio=root, state=y.tolist(),
                        derivative_k_per_log_supply=float(slope*response[-1]),
                        leading_real_yr=float(max(eig.real))))
    return out


def fixed_supply_endpoints():
    parameters = pc.reference()
    state = equilibria(parameters, 'fixed')[0]
    y, temp = state['y'], state['temperature_k']
    pair = tg.guilds(temp-273.15, parameters.biology)
    q = np.array([g.maintenance+parameters.biology.loss_h/g.yield_g_mol for g in pair])
    eta = 1-np.array([g.assimilation_mol_g for g in pair])*parameters.biology.loss_h/q
    outlet = parameters.biology.exchange_mol_l_h_pa*(y[0]-parameters.biology.atmosphere_pa)
    demand = 4*(parameters.loss.rate(y[-1])-abiotic(parameters))/(pc.inventory_to_ratio(parameters)*pc.HOURS_PER_YEAR)
    potential_scale = .3/pc.supply_h2(parameters)
    lower = (outlet+demand/eta[1])*potential_scale
    return dict(abiotic_ratio_per_year=float(abiotic(parameters)), lower_potential=float(lower),
                endpoints=[dict(fraction=f, upper_potential=float((outlet+demand/(f*eta[0]))*potential_scale),
                                ratio=float((outlet+demand/(f*eta[0]))*potential_scale/lower)) for f in (.5, .9, .98, 1.)])


def compare_production(rows):
    from terra_prisca.haze_world import dynamic_core as dc
    out = []
    for record in rows:
        if record['step'] != 1e-5:
            continue
        base = replace(pc.reference(), acetate_fraction=record['fraction'])
        p = dc.DynamicParams(base, chemistry=record['chemistry'])
        states = [s for s in dc.equilibrium_states(p) if s['kind']=='mixed' and s['status']=='accepted']
        if not states:
            raise AssertionError('Production solver missed the independently qualified mixture')
        state = min(states, key=lambda s: abs(s['r']-record['state'][-1]))
        y = np.asarray(record['state'])
        scales = np.maximum(abs(y), [10., 1e-4, 1e-4, 1e-5, .01])
        own_jac = derivative(lambda v: physical(v, record['temperature_k'], base, record['chemistry']), y, scales, 1e-5)
        production_jac, _, _ = dc.jacobian_blocks(y, p)
        delta = (own_jac-production_jac)*scales[None, :]/scales[:, None]
        production_response = dc.implicit_response(y, p)
        row = dict(chemistry=record['chemistry'], fraction=record['fraction'],
                   state_max_scaled_difference=float(max(abs(y-state['y'])/scales)),
                   fixed_temperature_matrix_max_scaled_difference=float(max(abs(delta).ravel())),
                   implicit_slope_difference=float(production_response['dtemperature_dlog_supply']-record['community_slope_k_per_log_supply']))
        if row['state_max_scaled_difference']>1e-7 or row['fixed_temperature_matrix_max_scaled_difference']>1e-4 or abs(row['implicit_slope_difference'])>1e-5:
            raise AssertionError(f'Independent homogeneous comparison failed: {row}')
        if record.get('two_layer') and record['two_layer']['critical_fast_coefficients_yr']:
            tau = record['two_layer']['critical_fast_coefficients_yr'][0]
            maximum = float(max(np.linalg.eigvals(dc.thermal_matrix(y, p, tau, two_layer=True)).real))
            row['production_two_layer_leading_at_independent_crossing'] = maximum
            if abs(maximum)>1e-7:
                raise AssertionError('Independent two-layer crossing disagrees with production')
        out.append(row)
    return out


def selected_spread_comparison(sigma=3., n=9, refine_independently=False, scan_critical=False):
    from terra_prisca.haze_world import dynamic_core as dc
    p = dc.DynamicParams(pc.reference(), chemistry='fixed', sigma_k=sigma, n_habitats=n)
    states = [s for s in dc.equilibrium_states(p) if s['kind']=='mixed' and s['status']=='accepted']
    if not states:
        raise AssertionError('Selected spread mixture not found')
    state = min(states, key=lambda s: abs(s['t_k']-281.5))
    y, temp = state['y'].copy(), state['t_k']
    def flow(v, fixed_temperature):
        local_stocks = v[:-1].reshape(p.n, 4)
        mean = local_stocks[:, 1:3].mean(axis=0)
        derivative = np.zeros_like(v)
        methane = 0.
        for j, offset in enumerate(p.offsets):
            local = np.r_[local_stocks[j], v[-1]]
            rates = physical(local, fixed_temperature+offset, p.base, p.chemistry)
            derivative[4*j:4*j+4] = rates[:4]
            derivative[4*j+1:4*j+3] += p.dispersal_yr*(mean-local_stocks[j, 1:3])
            methane += rates[-1]/p.n
        derivative[-1] = methane
        return derivative
    initial = y.copy()
    refinement = None
    if refine_independently:
        def equations(z):
            stocks = np.exp(z)
            common_temperature = float(pc.temperature_k(stocks[-1], p.base.climate))
            weights = np.r_[np.tile([1e-6, 1., 1., 1.], p.n), 1e4]
            denominator = stocks.copy()
            denominator[np.arange(p.n)*4] = 1.
            return flow(stocks, common_temperature)*weights/denominator
        solution = root(equations, np.log(y), method='hybr', options={'xtol':1e-10})
        candidate = np.exp(solution.x)
        residual = float(max(abs(equations(solution.x))))
        if not np.isfinite(candidate).all() or residual>1e-7:
            raise AssertionError('Independent distributed root refinement failed')
        y = candidate
        temp = float(pc.temperature_k(y[-1], p.base.climate))
        refinement = dict(solver_success=bool(solution.success), scaled_equation_residual=residual,
                          evaluations=int(solution.nfev),
                          maximum_relative_stock_shift=float(max(abs(y-initial)/initial)))
    scale = np.maximum(abs(y), np.r_[np.tile([10., 1e-4, 1e-4, 1e-5], p.n), .01])
    steps = []
    for step in (1e-4, 1e-5):
        jac = derivative(lambda v: flow(v, temp), y, scale, step)
        h = 1e-3
        column = (-flow(y, temp+2*h)+8*flow(y, temp+h)-8*flow(y, temp-h)+flow(y, temp-2*h))/(12*h)
        dr = 1e-6
        slope = float((pc.temperature_k(y[-1]+dr, p.base.climate)-pc.temperature_k(y[-1]-dr, p.base.climate))/(2*dr))
        reduced = jac.copy(); reduced[:, -1] += column*slope
        forcing = np.r_[np.tile([pc.supply_h2(p.base)*pc.HOURS_PER_YEAR/pc.HENRY_30C_MOL_L_PA, 0., 0., 0.], p.n), 0.]
        response = np.linalg.solve(reduced, -forcing)
        raw_slope = float(slope*response[-1])
        a = jac*scale[None, :]/scale[:, None]; b = column/scale
        lags = []
        def matrix_at(tau):
            if tau:
                matrix = np.zeros((len(y)+1, len(y)+1))
                matrix[:-1, :-1] = a; matrix[:-1, -1] = b
                matrix[-1, len(y)-1] = slope*scale[-1]/tau; matrix[-1, -1] = -1/tau
            else:
                matrix = reduced*scale[None, :]/scale[:, None]
            return matrix
        def leading_at(tau):
            return float(max(np.linalg.eigvals(matrix_at(tau)).real))
        critical = []
        if scan_critical:
            points = np.unique(np.r_[0., np.geomspace(.001, 1e4, 40), 3., 30., 100., 300.])
            values = [leading_at(tau) for tau in points]
            critical = [float(brentq(leading_at, lo, hi, xtol=1e-6)) for lo, hi, aa, bb in
                        zip(points[:-1], points[1:], values[:-1], values[1:]) if aa*bb<0]
        for tau in (0., 3., 30., 100., 300.):
            matrix = matrix_at(tau)
            leading = float(max(np.linalg.eigvals(matrix).real))
            production_leading = float(max(np.linalg.eigvals(dc.thermal_matrix(y, p, tau)).real))
            if abs(production_leading-leading)>1e-7:
                raise AssertionError('Independent distributed spectrum disagrees with production')
            lags.append(dict(lag_yr=tau, leading_real_yr=leading,
                             production_difference=float(production_leading-leading)))
        production = dc.implicit_response(y, p)['dtemperature_dlog_supply']
        if abs(production-raw_slope)>1e-5:
            raise AssertionError('Independent distributed gain numerator disagrees with production')
        steps.append(dict(step=step, raw_slope_k_per_log_supply=raw_slope,
                          production_slope_difference=float(production-raw_slope), lags=lags,
                          detected_critical_lags_yr=critical))
    return dict(scope='Selected midpoint habitat mixture. Production seed independently checked/refined by reassembled flows and finite-difference matrices, not an independent completeness search.',
                chemistry=p.chemistry, fraction=p.base.acetate_fraction, sigma_k=p.sigma_k, n_habitats=p.n,
                temperature_k=temp, local_temperature_range_k=[float(temp+min(p.offsets)), float(temp+max(p.offsets))],
                scaled_flow_residual=float(max(abs(flow(y,temp))/scale)), independent_refinement=refinement, steps=steps)


def describe(parameters, chemistry, state, step):
    y, temperature = state['y'], state['temperature_k']
    scales = np.maximum(abs(y), [10., 1e-4, 1e-4, 1e-5, .01])
    jac = derivative(lambda v: physical(v, temperature, parameters, chemistry), y, scales, step)
    dt = 1e-3
    thermal = (-physical(y, temperature+2*dt, parameters, chemistry)+8*physical(y, temperature+dt, parameters, chemistry)
               -8*physical(y, temperature-dt, parameters, chemistry)+physical(y, temperature-2*dt, parameters, chemistry))/(12*dt)
    curve = pc.response(parameters.climate.case)
    i = np.searchsorted(curve.ratios, y[-1])-1
    slope = (curve.temperatures_k[i+1]-curve.temperatures_k[i])/(curve.ratios[i+1]-curve.ratios[i])
    matrix = jac.copy()
    matrix[:, -1] += thermal*slope
    scaled = matrix*scales[None, :]/scales[:, None]
    forcing = np.r_[pc.supply_h2(parameters)*pc.HOURS_PER_YEAR/pc.HENRY_30C_MOL_L_PA, 0., 0., 0., 0.]
    state_response = np.linalg.solve(matrix, -forcing)
    own_slope = float(slope*state_response[-1])
    finite = []
    for delta in (-1e-4, 1e-4):
        perturbed = replace(parameters, climate=replace(parameters.climate, donor_flux=parameters.climate.donor_flux*np.exp(delta)))
        candidates = equilibria(perturbed, chemistry)
        if candidates:
            chosen = min(candidates, key=lambda r: abs(r['ratio']-y[-1]))
            finite.append(chosen['temperature_k'])
    finite_slope = (finite[1]-finite[0])/2e-4 if len(finite)==2 else None
    lag_rows = []
    a = jac*scales[None, :]/scales[:, None]
    b = thermal/scales
    def lag_matrix(tau):
        mat = np.zeros((6, 6)); mat[:5, :5] = a; mat[:5, -1] = b
        mat[-1, 4] = slope*scales[4]/tau; mat[-1, -1] = -1/tau
        return mat
    tau_grid = np.r_[np.geomspace(1e-5, 1e4, 90), .03, .1, .3, 1., 3., 10., 30., 100., 300., 1000.]
    tau_grid = np.unique(tau_grid)
    values = [float(max(np.linalg.eigvals(lag_matrix(t)).real)) for t in tau_grid]
    critical = [float(brentq(lambda t: max(np.linalg.eigvals(lag_matrix(t)).real), lo, hi, xtol=1e-9))
                for lo, hi, a0, b0 in zip(tau_grid[:-1], tau_grid[1:], values[:-1], values[1:]) if a0*b0 < 0]
    for tau in (.03, .1, .3, 1., 3., 10., 30., 100., 300., 1000., 10000.):
        eig = np.linalg.eigvals(lag_matrix(tau)); lead = eig[np.argmax(eig.real)]
        lag_rows.append(dict(lag_yr=tau, leading_real_yr=float(lead.real), leading_imag_yr=float(lead.imag)))
    two_layer = None
    if chemistry == 'fixed' and parameters.acetate_fraction == .5:
        def matrix_two(tau):
            mat = np.zeros((7, 7)); mat[:5, :5] = a; mat[:5, 5] = b
            mat[5, 4] = slope*scales[4]/tau
            mat[5, 5] = -2/tau; mat[5, 6] = 1/tau
            mat[6, 5] = 1/(100*tau); mat[6, 6] = -1/(100*tau)
            return mat
        values_two = [float(max(np.linalg.eigvals(matrix_two(t)).real)) for t in tau_grid]
        roots_two = [float(brentq(lambda t: max(np.linalg.eigvals(matrix_two(t)).real), lo, hi, xtol=1e-11))
                     for lo, hi, aa, bb in zip(tau_grid[:-1], tau_grid[1:], values_two[:-1], values_two[1:]) if aa*bb<0]
        two_layer = dict(critical_fast_coefficients_yr=roots_two,
                         first_to_one_layer_ratio=float(roots_two[0]/critical[0]) if roots_two and critical else None,
                         effective_low_frequency_lag_factor=101,
                         scope='Named coupled two-layer diagnostic: Ts receives Teq−2Ts+Td; tau_s=100tau_f. Equation coefficients are not calibrated ocean response times.')
    controls = methanogen_control(parameters, chemistry, step)
    control = min(controls, key=lambda c: abs(c['ratio']-y[-1])) if controls else None
    gain = own_slope/control['derivative_k_per_log_supply'] if control and abs(control['derivative_k_per_log_supply'])>1e-8 else None
    return dict(chemistry=chemistry, fraction=parameters.acetate_fraction, step=step,
                state=y.tolist(), temperature_k=temperature,
                max_flow_scaled=float(np.max(abs(physical(y, temperature, parameters, chemistry))/scales)),
                instantaneous_leading_real_yr=float(max(np.linalg.eigvals(scaled).real)),
                community_slope_k_per_log_supply=own_slope,
                finite_difference_slope_k_per_log_supply=finite_slope,
                critical_lags_yr=critical, lag_rows=lag_rows, selected_control=control,
                stable_controls=controls, gain=gain, two_layer=two_layer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--compare-production', action='store_true')
    args = parser.parse_args()
    rows = []
    for fraction in (0., .5):
        parameters = replace(pc.reference(), acetate_fraction=fraction)
        for chemistry in ('fixed', 'products', 'acetate_only', 'methane_only'):
            found = equilibria(parameters, chemistry)
            for state in found:
                for step in (1e-4, 1e-5, 1e-6):
                    rows.append(describe(parameters, chemistry, state, step))
    sources = ['docs/audits/dynamic-realisation-review-2026-11-12.py',
               'src/terra_prisca/haze_world/population_coupling.py', 'src/terra_prisca/haze_world/two_guilds.py',
               'src/terra_prisca/haze_world/methane_budget.py', 'src/terra_prisca/haze_world/darwinian.py',
               'src/terra_prisca/haze_world/hydrogen_uptake.py', 'src/terra_prisca/haze_world/woodii1998.py',
               'models/haze_world/dynamic-realisation-spec.md', 'models/haze_world/dynamic-realisation-methods.md',
               'models/haze_world/evidence/kotsyurbenko2001_table2.csv',
               'models/haze_response/arney2016/figure4.csv', 'models/haze_response/arney2016/cases.csv']
    report = dict(scope='Selected homogeneous algebra and finite-difference check; no B2/B3 claims and no interval certificate.',
                  rows=rows, fixed_supply_endpoints=fixed_supply_endpoints(),
                  source_sha256={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in sources})
    if args.compare_production:
        report['production_comparison'] = compare_production(rows)
        report['selected_spread_comparison'] = selected_spread_comparison()
        report['sigma1_resolution_checks'] = [selected_spread_comparison(1., n, True, True) for n in (9, 17, 33)]
        path = 'src/terra_prisca/haze_world/dynamic_core.py'
        report['source_sha256'][path] = sha256((ROOT/path).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps([dict(chemistry=r['chemistry'], fraction=r['fraction'], temperature_k=r['temperature_k'],
                           slope=r['community_slope_k_per_log_supply'], critical_lags_yr=r['critical_lags_yr'])
                      for r in rows if r['step']==1e-5], indent=2))


if __name__ == '__main__':
    main()
