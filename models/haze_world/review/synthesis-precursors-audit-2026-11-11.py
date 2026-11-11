"""Independent closed-form/recount audit of synthesis claims C01-C04."""

import csv
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize_scalar

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent


def rows(path):
    with (ROOT/path).open() as stream:
        return list(csv.DictReader(stream))


def main():
    climate_file = 'models/haze_response/arney2016/figure4.csv'
    cases_file = 'models/haze_response/arney2016/cases.csv'
    setpoint_file = 'models/haze_world/figures/setpoint.csv'
    evolution_file = 'models/haze_world/figures/darwinian_endpoints.csv'
    rescue_file = 'models/haze_world/figures/strains_rescue.csv'
    series_file = 'models/haze_world/figures/strains_series.csv'
    climate, cases = rows(climate_file), {r['case']: r for r in rows(cases_file)}
    curves = {}
    for case in cases:
        data = [r for r in climate if r['case'] == case]
        curves[case] = (np.array([float(r['ch4_co2_ratio']) for r in data]),
                        np.array([float(r['temperature_k']) for r in data]))
    coefficients = {case: 3.15576e7/(float(r['p_co2_bar'])*1e5/(.028*9.81)*6.02214076e23/1e4)
                    for case, r in cases.items()}
    selected = [r for r in rows(setpoint_file) if r['domain_invariant'] == 'True' and r['domain'] == 'arney']
    checks = []
    for row in selected:
        case = row['case']
        x, t = curves[case]
        potential, pk, ra = .4*x[-1]/.2333, 1e4*coefficients[case]*1e10, 1e4*coefficients[case]*6.8e8
        theta = float(row['cold_edge_k'])+20*np.sqrt(1-(1+pk/potential)/10)

        def balance(r):
            rho = 10*max(0., 1-((np.interp(r, x, t)-theta)/20)**2)
            eta = max(0., 1-pk/(potential*(rho-1))) if rho > 1 else 0.
            return r-ra-potential*eta

        r = brentq(balance, float(row['r'])-1e-5, float(row['r'])+1e-5, xtol=1e-14)
        temp = float(np.interp(r, x, t))
        i = np.searchsorted(x, r)-1
        t_r = (t[i+1]-t[i])/(x[i+1]-x[i])
        rho = 10*(1-((temp-theta)/20)**2)
        rho_t = -20*(temp-theta)/20**2
        derivative = 1-pk*rho_t*t_r/(rho-1)**2
        assert balance(x[0]) < 0 < balance(x[-1])
        assert x[0] < r < x[-1] and t_r < 0 and derivative > 0
        assert abs(temp-float(row['t_k'])) < .000501
        checks.append(dict(case=case, edge_k=float(row['cold_edge_k']), temperature_k=temp,
                           temperature_minus_edge_k=temp-float(row['cold_edge_k']),
                           csv_temperature_error_k=temp-float(row['t_k']), stable_scalar_balance_slope=float(derivative)))
    c01 = dict(cases=len(checks), by_atmosphere={case: sum(r['case'] == case for r in checks) for case in cases},
               minimum_offset_k=min(r['temperature_minus_edge_k'] for r in checks),
               maximum_offset_k=max(r['temperature_minus_edge_k'] for r in checks),
               displayed_offset_k=[.015, .037], roots=checks,
               scope='High-supply scalar equilibria across A-D, not case B alone; no dynamical elimination theorem')
    evolution = rows(evolution_file)
    pk, ra, potential = 1e4*coefficients['B']*1e10, 1e4*coefficients['B']*6.8e8, .22
    anchor = potential-pk/9+ra
    expected_t = float(np.interp(anchor, *curves['B']))
    unconstrained = [r for r in evolution if r['constraint'] == 'U']
    for row in unconstrained:
        assert abs(float(row['r'])-anchor) < 5.1e-8
        assert abs(float(row['t_k'])-expected_t) < 5.1e-5
        assert row['theta_k'] == row['t_k'] and float(row['regulation_local']) == 1.
        assert float(row['t_minus_control10_k']) == 0.
    c02 = dict(loss_shapes=len(unconstrained), fixed_peak_growth=10., regulation_ratio=1.,
               methane_ratio_from_constant_capture=anchor, temperature_from_constant_capture_k=expected_t,
               maximum_recorded_control_contrast_k=max(abs(float(r['t_minus_control10_k'])) for r in unconstrained),
               argument='At E=0 and an interior singularity theta=T, rho=10 and rho_T=0. Both source and local response equal the temperature-independent control.',
               scope='Fixed-peak U scenario at a feasible interior singularity; not a theorem for H trade-offs or an arbitrary two-guild evolutionary model')
    floors = []
    for loss in dict.fromkeys(r['loss'] for r in evolution):
        selected_f = [r for r in evolution if r['constraint'].startswith('F') and r['loss'] == loss and float(r['regulation_local']) < .3]
        first = min(selected_f, key=lambda r: float(r['floor_k']))
        theta = float(first['floor_k'])
        assert first['at_floor'] == 'True'
        x, t = curves['B']
        def loss_rate(r):
            if loss.startswith('power'):
                return anchor/1e4*(r/anchor)**float(loss.split('=')[1])
            return anchor/1e4*np.log1p(r/.001)/np.log1p(anchor/.001)
        def balance(r):
            rho = 10*max(0., 1-((np.interp(r, x, t)-theta)/20)**2)
            source = (potential-pk/(rho-1)+ra)/1e4 if rho > 1+pk/potential else ra/1e4
            return float(loss_rate(r)-source)
        r = brentq(balance, float(first['r'])-1e-5, float(first['r'])+1e-5, xtol=1e-14)
        temp = float(np.interp(r, x, t))
        i = np.searchsorted(x, r)-1
        t_r = (t[i+1]-t[i])/(x[i+1]-x[i])
        rho = 10*(1-((temp-theta)/20)**2)
        rho_t = -20*(temp-theta)/20**2
        elasticity = float(loss.split('=')[1]) if loss.startswith('power') else None
        loss_prime = elasticity*loss_rate(r)/r if elasticity else anchor/1e4/((.001+r)*np.log1p(anchor/.001))
        ratio = loss_prime/(loss_prime-pk/1e4*rho_t*t_r/(rho-1)**2)
        assert abs(ratio-float(first['regulation_local'])) < 1e-6
        floors.append(dict(loss=loss, first_floor_k=float(first['floor_k']), independently_recomputed_ratio=ratio,
                           minimum_strong_buffering_edge_offset_k=min(float(r['t_k'])-float(r['cold_edge_k']) for r in selected_f),
                           maximum_strong_buffering_edge_offset_k=max(float(r['t_k'])-float(r['cold_edge_k']) for r in selected_f)))
    hot = [r for r in evolution if r['constraint'].startswith('H') and float(r['regulation_local']) < .5]
    offset_min = min(r['minimum_strong_buffering_edge_offset_k'] for r in floors)
    offset_max = max(r['maximum_strong_buffering_edge_offset_k'] for r in floors)
    assert round(offset_min, 2) == .14 and round(offset_max, 1) == 2.4
    c03 = dict(floors=floors,
               first_floor_range_k=[min(r['first_floor_k'] for r in floors), max(r['first_floor_k'] for r in floors)],
               minimum_edge_offset_k=offset_min, maximum_edge_offset_k=offset_max,
               displayed_offset_range_k=[round(offset_min, 2), round(offset_max, 1)],
               hotter_is_better_rows_below_half_response=len(hot),
               minimum_hotter_is_better_ratio=min(float(r['regulation_local']) for r in hot),
               scope='The 291-293 K threshold concerns sampled F floors only. H trade-offs retain regulation without an optimum floor under shallow loss.')
    rescue = rows(rescue_file)
    frozen_u = [r for r in rescue if r['constraint'] == 'U' and float(r['mutation']) == 0.]
    assert len(frozen_u) == 18 and all(r['survived'] == 'False' for r in frozen_u)
    assert all(r['frozen_viable'] == 'True' for r in frozen_u)
    viable_thresholds = []
    for t0 in (265., 283.):
        x, t = curves['B']
        def temperature(r):
            return np.where(r < x[0], t0+(t[0]-t0)*np.log1p(r/.01)/np.log1p(x[0]/.01), np.interp(r, x, t))
        def required(r):
            rho = 10*max(0., 1-((float(temperature(r))-273.5)/20)**2)
            return r-ra+pk/(rho-1) if rho > 1 else np.inf
        grid = ra+np.geomspace(1e-9, .5, 100001)
        values = np.array([required(r) for r in grid])
        best = int(np.argmin(values))
        fit = minimize_scalar(required, bounds=(grid[max(0,best-1)],grid[min(len(grid)-1,best+1)]),method='bounded',options={'xatol':1e-14})
        assert float(fit.fun) < .02
        viable_thresholds.append(dict(t_zero_k=t0, independently_minimized_supply=float(fit.fun), frozen_optimum_k=273.5))
    series = [r for r in rows(series_file) if r['constraint'] == 'U' and float(r['mutation']) == 0.]
    living = [r for r in series if float(r['total_biomass']) > 0]
    first_dead = next(r for r in series if float(r['total_biomass']) == 0.)
    c04 = dict(frozen_unconstrained_cases=len(frozen_u), extinct_cases=sum(r['survived']=='False' for r in frozen_u),
               minimum_death_after_decline_yr=min(float(r['extinct_after_decline_yr']) for r in frozen_u),
               maximum_death_after_decline_yr=max(float(r['extinct_after_decline_yr']) for r in frozen_u),
               warming_peak_k=float(max(curves['B'][1])), independently_minimized_viability=viable_thresholds,
               example_last_living_sample=dict(time_yr=float(living[-1]['t_yr']), temperature_k=float(living[-1]['t_k'])),
               example_first_dead_sample=dict(time_yr=float(first_dead['t_yr']), temperature_k=float(first_dead['t_k'])),
               scope='Deaths in the warming excursion toward the 297 K maximum, for fixed-optimum U/no-mutation runs; not all methanogens and not death exactly at the peak. Census timing and extinction law are uncalibrated.')
    paths=[climate_file,cases_file,setpoint_file,evolution_file,rescue_file,series_file,
           'src/terra_prisca/haze_world/methane_budget.py','src/terra_prisca/haze_world/darwinian.py',
           'src/terra_prisca/haze_world/strains.py']
    result=dict(C01=c01,C02=c02,C03=c03,C04=c04,
                input_sha256={p:sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
                checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                scope='Independent algebra, selected-root recomputation and frozen-table recount; no new trajectories or calibration')
    HERE.joinpath('synthesis-precursors-audit-2026-11-11.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:{j:v for j,v in value.items() if j not in ('roots','floors')} for k,value in result.items() if k.startswith('C')},indent=2))


if __name__ == '__main__':
    main()
