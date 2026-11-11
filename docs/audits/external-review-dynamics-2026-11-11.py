"""Independent equation-level checks of external triage X1, X2, X3 and X10.

This audit does not overwrite the reviewers' outputs or change production code.
Run from the repository root with ``uv run python <this path>``.
"""
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq, root

from terra_prisca.haze_world import population_coupling as pc
from terra_prisca.haze_world import two_guilds as tg
from terra_prisca.haze_world import evolved_kinetics as ek

OUT = Path(__file__).with_suffix('.json')
YEAR = pc.HOURS_PER_YEAR


def physical(y, t, p, pair=None):
    """Reassemble flows directly from guild uptake, yield and assimilation."""
    press, xa, xm, acetate, ratio = y
    pair = pc.activity_guilds_at_temperature(y, p, t) if pair is None else pair
    x = np.array([xa, xm])
    uptake = np.array([g.uptake(press) for g in pair])
    growth = np.array([g.yield_g_mol*(v-g.maintenance) for g, v in zip(pair, uptake)])
    cat = uptake-np.array([g.assimilation_mol_g for g in pair])*np.maximum(growth, 0)
    rec, export = pc.recycling_rates(t, p)
    ab = pc.atmosphere(p.climate.case)['flux_to_ratio_per_yr']*p.climate.abiotic_flux
    return np.r_[YEAR/pc.HENRY_30C_MOL_L_PA*(pc.supply_h2(p)-uptake@x-p.biology.exchange_mol_l_h_pa*(press-p.biology.atmosphere_pa)),
                 YEAR*x*(growth-p.biology.loss_h), YEAR*cat[0]*xa/4-(rec+export)*acetate,
                 pc.inventory_to_ratio(p)*(YEAR*cat[1]*xm/4+rec*acetate)+ab-p.loss.rate(ratio)]


def analytic_state_jacobian(y, t, p, pair=None):
    """Exact state derivatives on a positive-uptake, positive-synthesis segment."""
    pair = pc.activity_guilds_at_temperature(y, p, t) if pair is None else pair
    press, xa, xm, acetate, ratio = y
    x = np.array([xa, xm]); h = np.array([g.assimilation_mol_g for g in pair])
    yields = np.array([g.yield_g_mol for g in pair])
    v = np.array([g.uptake(press) for g in pair])
    synthesis = np.array([g.yield_g_mol*(q-g.maintenance) for g, q in zip(pair, v)])
    assert np.all(synthesis > 0)
    available = np.array([press-g.threshold_pa for g in pair]); assert np.all(available > 0)
    slope = np.array([g.rate_scale*g.km_pa/(g.km_pa+z)**2 for g, z in zip(pair, available)])
    dq = np.zeros((2, 5)); dq[:, 0] = slope
    if p.activity_feedback == 'products':
        if acetate > 0:
            dq[0, 3] = -slope[0]*pair[0].threshold_pa/(4*acetate)
        elif xa != 0:
            raise ValueError('Acetogen product derivative is singular at zero acetate')
        dq[1, 4] = -slope[1]*pair[1].threshold_pa/(4*ratio)
    a = np.zeros((5, 5))
    a[0] = -YEAR/pc.HENRY_30C_MOL_L_PA*(x@dq)
    a[0, 0] -= YEAR/pc.HENRY_30C_MOL_L_PA*p.biology.exchange_mol_l_h_pa
    a[0, 1:3] = -YEAR/pc.HENRY_30C_MOL_L_PA*v
    for i in (0, 1):
        a[i+1] = YEAR*x[i]*yields[i]*dq[i]
        a[i+1, i+1] += YEAR*(synthesis[i]-p.biology.loss_h)
    cat = v-h*synthesis
    rec, export = pc.recycling_rates(t, p); conv = pc.inventory_to_ratio(p)
    a[3] = YEAR/4*x[0]*(1-h[0]*yields[0])*dq[0]
    a[3, 1] += YEAR/4*cat[0]; a[3, 3] -= rec+export
    a[4] = conv*YEAR/4*x[1]*(1-h[1]*yields[1])*dq[1]
    a[4, 2] += conv*YEAR/4*cat[1]; a[4, 3] += conv*rec
    a[4, 4] -= p.loss.slope(ratio)
    return a


def derivative_t(fun, t, h):
    return (fun(t-2*h)-8*fun(t-h)+8*fun(t+h)-fun(t+2*h))/(12*h)


def lead(mat):
    eig = np.linalg.eigvals(mat); v = eig[np.argmax(eig.real)]
    return float(v.real), float(abs(v.imag))


def lag_checks():
    result = []
    for activity in ('fixed', 'products'):
        for fraction in (0., .5):
            p = replace(pc.reference(), activity_feedback=activity, acetate_fraction=fraction)
            state = next(e for e in pc.equilibrium_states(p) if e['kind']=='mixed' and e['stable'])
            y, t = state['y'], state['t_k']
            a = analytic_state_jacobian(y, t, p)
            scale = np.maximum(abs(y), [10, 1e-4, 1e-4, 1e-5, .01])
            a = a*scale[None, :]/scale[:, None]
            curve = pc.response(p.climate.case)
            j = np.searchsorted(curve.ratios, y[4])-1
            climate_slope = (curve.temperatures_k[j+1]-curve.temperatures_k[j])/(curve.ratios[j+1]-curve.ratios[j])
            for step in (1e-3, 1e-4, 1e-5):
                b = derivative_t(lambda temp: physical(y, temp, p), t, step)/scale
                reduced = a.copy(); reduced[:, 4] += b*climate_slope*scale[4]
                r, omega = lead(reduced)
                def matrix(tau):
                    z = np.zeros((6, 6)); z[:5, :5] = a; z[:5, 5] = b
                    z[5, 4] = climate_slope*scale[4]/tau; z[5, 5] = -1/tau
                    return z
                times = np.geomspace(1e-5, 1e4, 16)
                leading = [lead(matrix(tau)) for tau in times]
                crossings = [brentq(lambda tau: lead(matrix(tau))[0], ta, tb, xtol=1e-11)
                             for ta, tb, va, vb in zip(times[:-1], times[1:], leading[:-1], leading[1:]) if va[0]*vb[0]<0]
                result.append(dict(activity=activity, fraction=fraction, temperature_derivative_step_k=step,
                    equilibrium_temperature_k=t, flow_relative_residual=float(np.max(abs(physical(y, t, p))/scale)),
                    static_leading_real=r, static_leading_imag=omega,
                    critical_lags_years=crossings, two_mode_formula_years=-2*r/(omega**2-3*r*r),
                    lag_grid_years=times.tolist(), leading_real=[v[0] for v in leading]))
    return result


def product_gain():
    """Implicit equilibrium response; no perturbed equilibrium root finder."""
    p = replace(pc.reference(), activity_feedback='products')
    rows = []
    for enabled in ((True, True), (False, True)):
        q = replace(p, enabled=enabled)
        e = next(e for e in pc.equilibrium_states(q) if e['stable'] and e['kind']!='lifeless')
        y, t = e['y'], e['t_k']; a = analytic_state_jacobian(y, t, q)
        curve = pc.response(q.climate.case); j = np.searchsorted(curve.ratios, y[4])-1
        slope = np.diff(curve.temperatures_k)[j]/np.diff(curve.ratios)[j]
        bt = derivative_t(lambda temp: physical(y, temp, q), t, 1e-4)
        a[:, 4] += bt*slope
        # The absent acetogen has zero forcing and is excluded from the resident derivative.
        active = [0, 1, 2, 3, 4] if enabled[0] else [0, 2, 3, 4]
        forcing = np.zeros(5); forcing[0] = YEAR/pc.HENRY_30C_MOL_L_PA*pc.supply_h2(q)
        deriv = np.linalg.solve(a[np.ix_(active, active)], -forcing[active])
        rows.append(dict(control='community' if enabled[0] else 'methanogen_only', temperature_k=t,
                         dT_dlog_supply=float(slope*deriv[active.index(4)])))
    return dict(rows=rows, signed_gain=rows[0]['dT_dlog_supply']/rows[1]['dT_dlog_supply'])


def nonlinear_lag_kick():
    """Own six-state integration; rare biomass remains represented as log mass."""
    p = replace(pc.reference(), acetate_fraction=0.)
    e = next(e for e in pc.equilibrium_states(p) if e['kind']=='mixed' and e['stable'])
    y = e['y']; initial = np.r_[y, e['t_k']]
    initial[1:3] = np.log(initial[1:3]); initial[1] += .001
    def rhs(_, z):
        y = z[:5].copy(); y[1:3] = np.exp(z[1:3])
        pair = tg.guilds(z[5]-273.15, p.biology)
        flows = physical(y, z[5], p, pair)
        flows[1:3] = [YEAR*(g.yield_g_mol*(g.uptake(y[0])-g.maintenance)-p.biology.loss_h) for g in pair]
        return np.r_[flows, (float(pc.temperature_k(y[4], p.climate))-z[5])/3.]
    sol = solve_ivp(rhs, (0., 12000.), initial, method='LSODA', first_step=1e-6,
                    rtol=2e-9, atol=[1e-9, 1e-9, 1e-9, 1e-12, 1e-12, 1e-9], t_eval=np.arange(12001.))
    if not sol.success or np.any(~np.isfinite(sol.y)):
        raise RuntimeError(sol.message)
    cell = 3e-13/(p.habitat_l_cm2*5.1e18)
    counts = (sol.y[1:3]-np.log(cell))/np.log(10)
    return dict(success=bool(sol.success), years=12000., sample_spacing_yr=1., thermal_lag_yr=3., fraction=0.,
                initial_log_acetogen_kick=.001, min_log10_cells=counts.min(axis=1).tolist(),
                time_min_log10_cells_yr=[float(sol.t[i]) for i in np.argmin(counts, axis=1)],
                temperature_range_k=[float(sol.y[5].min()), float(sol.y[5].max())],
                limitation='Continuous trajectory diagnostic; no physical extinction/removal or coupled demographic events applied.')


def unequal_evolution():
    p = pc.reference(); energies = (.65, .10); results = []
    for interpolation in ek.INTERPOLATIONS:
        def responses(t):
            calls = [ek.best_response(t, p.biology, energy, interpolation) for energy in energies]
            return np.array([calls[i]['rstars_pa'][i] for i in (0, 1)]), tuple(calls[i]['positions_c'][i] for i in (0, 1))
        def diff(t):
            rstar, _ = responses(t); return rstar[0]-rstar[1]
        temp = brentq(diff, 283.15, 288.15, xtol=1e-11)
        rstar, positions = responses(temp)
        def pair(t):
            return tuple(ek.guilds(t, p.biology, ek.Traits(positions, energies[i], interpolation))[i] for i in (0, 1))
        curve = pc.response(p.climate.case)
        k = next(j for j in range(len(curve.ratios)-1) if curve.temperatures_k[j] >= temp > curve.temperatures_k[j+1])
        r = float(np.interp(temp, curve.temperatures_k[k:k+2][::-1], curve.ratios[k:k+2][::-1]))
        gs = pair(temp); pressure = np.mean(rstar)
        req = np.array([g.maintenance+p.biology.loss_h/g.yield_g_mol for g in gs])
        cat = req-np.array([g.assimilation_mol_g for g in gs])*p.biology.loss_h
        ecology = []
        for fraction in (0., .5):
            q = replace(p, acetate_fraction=fraction); rec, export = pc.recycling_rates(temp, q)
            captured = pc.supply_h2(q)-q.biology.exchange_mol_l_h_pa*(pressure-q.biology.atmosphere_pa)
            ab = pc.atmosphere(q.climate.case)['flux_to_ratio_per_yr']*q.climate.abiotic_flux
            biomass = np.linalg.solve(np.array([req, cat*np.array([fraction, 1.])]),
                [captured, 4*(q.loss.rate(r)-ab)/(pc.inventory_to_ratio(q)*YEAR)])
            acetate = YEAR*cat[0]*biomass[0]/(4*(rec+export)); y = np.r_[pressure, biomass, acetate, r]
            assert np.all(y>0)
            a = analytic_state_jacobian(y, temp, q, gs)
            bt = derivative_t(lambda t: physical(y, t, q, pair(t)), temp, 1e-4)
            cslope = np.diff(curve.temperatures_k)[k]/np.diff(curve.ratios)[k]
            a[:, 4] += bt*cslope
            scale = np.maximum(abs(y), [10, 1e-4, 1e-4, 1e-5, .01])
            ecology.append(dict(fraction=fraction, positive_state=True, leading_real_per_yr=lead(a*scale[None, :]/scale[:, None])[0],
                                 flow_relative_residual=float(np.max(abs(physical(y, temp, q, gs))/scale))))
        results.append(dict(energies_ev=energies, interpolation=interpolation, temperature_k=temp,
                            trait_positions_c=positions, crossing_slope_pa_k=(diff(temp+.0001)-diff(temp-.0001))/.0002,
                            cooling_communities=ecology))
    return results


def habitat_check():
    """Nine-box local-stability control, equations assembled independently.

    Direct positive biomasses are used in the root solve; no temperature clipping.
    Continuation from the homogeneous equilibrium follows the coexistence branch.
    """
    p = replace(pc.reference(), acetate_fraction=0.)
    e = next(e for e in pc.equilibrium_states(p) if e['kind']=='mixed' and e['stable'])
    n, exchange = 9, .001
    conversion = pc.inventory_to_ratio(p)
    scale = np.r_[np.tile(np.maximum(e['y'][:4], [10., 1e-4, 1e-4, 1e-5]), n), .1]
    initial = np.r_[np.tile(e['y'][:4], n), e['r']]/scale
    def vector_rhs(v, offsets, supplied_t=None):
        yy = v*scale; ratio = yy[-1]
        t = float(pc.temperature_k(ratio, p.climate)) if supplied_t is None else supplied_t
        locals_ = yy[:-1].reshape(n, 4); out = np.zeros_like(yy); dx = out[:-1].reshape(n, 4)
        mean = locals_[:, 1:3].mean(0); methane = 0.
        for j, local in enumerate(locals_):
            stocks = np.r_[local, ratio]; flows = physical(stocks, t+offsets[j], p)
            dx[j] = flows[:4]; dx[j, 1:3] += exchange*(mean-local[1:3])
            methane += flows[4]/n
        out[-1] = methane
        return out/scale
    rows = []
    state = initial
    root_weights = np.r_[np.tile([1e-7, 1., 1., 1.], n), 1e4]
    def log_rhs(logv, offsets):
        v = np.exp(logv)
        return vector_rhs(v, offsets)/v*root_weights
    snapshots = []
    for spread in (.001, .003, .01, .03, .1, .3, 1., 2., 3., 4., 5., 6.):
        offsets = np.linspace(-spread, spread, n)
        sol = root(lambda v: log_rhs(v, offsets), np.log(state), method='hybr', options={'xtol':1e-10})
        trial = np.exp(sol.x)
        residual = float(np.max(abs(log_rhs(sol.x, offsets))))
        if not np.all(np.isfinite(trial)) or residual>1e-7:
            return dict(qualified=False, stopped_spread_k=float(spread), residual=residual, message=sol.message,
                        last_temperature_k=float(pc.temperature_k(state[-1]*scale[-1], p.climate)))
        state = trial
        if spread in (3., 6.):
            t = float(pc.temperature_k(state[-1]*scale[-1], p.climate))
            def lag_rhs(z, tau):
                return np.r_[vector_rhs(z[:-1], offsets, z[-1]), (float(pc.temperature_k(z[-2]*scale[-1], p.climate))-z[-1])/tau]
            z = np.r_[state, t]; rows = []
            for tau in (3., 30., 300.):
                for h in (1e-4, 1e-5):
                    jac = np.column_stack([(lag_rhs(z+np.eye(len(z))[j]*h, tau)-lag_rhs(z-np.eye(len(z))[j]*h, tau))/(2*h) for j in range(len(z))])
                    maximum, omega = lead(jac)
                    rows.append(dict(thermal_lag_yr=tau, derivative_step=h, leading_real_per_yr=maximum,
                                     leading_imag_per_yr=omega))
            snapshots.append(dict(spread_k=spread, temperature_k=t, habitat_temperature_bounds_k=[t-spread, t+spread],
                                  weighted_root_residual=residual, eigenvalues=rows))
    return dict(qualified=True, exchange_per_yr=exchange, boxes=n, snapshots=snapshots,
                limitation='Local equilibrium/stability only; no independent invasion minimum or continuum-spread qualification.')


def alternate_climates():
    """Keep physiology and T* fixed; choose supply inside each feasible band."""
    result = []
    base = pc.reference()
    t = pc.switch_temperatures(base.biology)[0]
    for case in ('A', 'B', 'C'):
        p = replace(base, climate=replace(base.climate, case=case))
        curve = pc.response(case)
        j = next(j for j in range(len(curve.ratios)-1) if curve.temperatures_k[j] >= t > curve.temperatures_k[j+1])
        ratio = float(np.interp(t, curve.temperatures_k[j:j+2][::-1], curve.ratios[j:j+2][::-1]))
        gs = tg.guilds(t-273.15, p.biology); press = gs[0].rstar(p.biology.loss_h)
        required = np.array([g.maintenance+p.biology.loss_h/g.yield_g_mol for g in gs])
        eta = 1-np.array([g.assimilation_mol_g for g in gs])*p.biology.loss_h/required
        ab = pc.atmosphere(case)['flux_to_ratio_per_yr']*p.climate.abiotic_flux
        capture = 4*(p.loss.rate(ratio)-ab)/(pc.inventory_to_ratio(p)*YEAR*np.mean(eta*np.array([p.acetate_fraction, 1.])))
        supply = capture+p.biology.exchange_mol_l_h_pa*(press-p.biology.atmosphere_pa)
        donor = supply*pc.AVOGADRO*p.habitat_l_cm2/(4*3600)
        p = replace(p, climate=replace(p.climate, donor_flux=donor))
        x = .5*capture/required; rec, export = pc.recycling_rates(t, p)
        acetate = YEAR*eta[0]*required[0]*x[0]/(4*(rec+export))
        y = np.r_[press, x, acetate, ratio]
        a = analytic_state_jacobian(y, t, p)
        slope = np.diff(curve.temperatures_k)[j]/np.diff(curve.ratios)[j]
        a[:, 4] += derivative_t(lambda temp: physical(y, temp, p), t, 1e-4)*slope
        scale = np.maximum(abs(y), [10, 1e-4, 1e-4, 1e-5, .01])
        result.append(dict(case=case, temperature_k=t, ratio=ratio, supply_h2_mol_l_h=supply,
                           h2_allocation_each_guild=.5, instantaneous_leading_real_per_yr=lead(a*scale[None, :]/scale[:, None])[0],
                           relative_flow_residual=float(np.max(abs(physical(y, t, p))/scale))))
    p = replace(base, biology=replace(base.biology, methanogen=tg.MSP))
    e = next(e for e in pc.equilibrium_states(p) if e['kind']=='mixed' and e['stable'])
    y, t = e['y'], e['t_k']; curve = pc.response(p.climate.case)
    j = np.searchsorted(curve.ratios, y[4])-1
    a = analytic_state_jacobian(y, t, p)
    a[:, 4] += derivative_t(lambda temp: physical(y, temp, p), t, 1e-4)*np.diff(curve.temperatures_k)[j]/np.diff(curve.ratios)[j]
    scale = np.maximum(abs(y), [10, 1e-4, 1e-4, 1e-5, .01])
    result.append(dict(strain='MSP', case='B', temperature_k=t,
                       instantaneous_leading_real_per_yr=lead(a*scale[None, :]/scale[:, None])[0]))
    return result


if __name__ == '__main__':
    result = dict(lag_checks=lag_checks(), product_buffering=product_gain(), nonlinear_lag_kick=nonlinear_lag_kick(), unequal_evolution=unequal_evolution(), habitat_spread=habitat_check(), alternate_climates=alternate_climates())
    result['provenance'] = {str(path.resolve().relative_to(Path.cwd())):sha256(path.read_bytes()).hexdigest() for path in
        [Path(__file__), Path(pc.__file__), Path(tg.__file__), Path(ek.__file__)]}
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result, indent=2, allow_nan=False))
