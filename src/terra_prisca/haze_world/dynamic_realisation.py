"""B1 stability/gain maps and bounded equilibrium-branch continuation."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from dataclasses import replace
from hashlib import sha256
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigvals
from scipy.optimize import brentq

from . import dynamic_core as model
from . import population_coupling as core

ROOT = Path(__file__).resolve().parents[3]
LAGS = (0., .03, .1, .3, 1., 3., 10., 30., 100., 300., 1000.)
LOSSES = (.0005, .001, .002)
SUPPLIES = (.24, .30, .36)
SPREADS = (0., 1., 3., 6.)


def parameters(chemistry, fraction, loss_h, potential, sigma=0., n=9, lifetime=10000., slope=1.):
    base = core.reference(potential)
    base = replace(base, acetate_fraction=fraction,
                   biology=replace(base.biology, loss_h=loss_h),
                   climate=replace(base.climate, lifetime_yr=lifetime),
                   loss=replace(base.loss, lifetime_yr=lifetime))
    return model.DynamicParams(base, chemistry, sigma, n, slope_multiplier=slope)


def source_hashes():
    files = [Path(__file__), Path(model.__file__), Path(core.__file__),
             *[Path(core.__file__).with_name(name) for name in
               ('two_guilds.py','methane_budget.py','darwinian.py','hydrogen_uptake.py','woodii1998.py')],
             ROOT/'models/haze_world/dynamic-realisation-spec.md',
             ROOT/'models/haze_world/dynamic-realisation-methods.md',
             ROOT/'models/haze_response/arney2016/figure4.csv',
             ROOT/'models/haze_response/arney2016/cases.csv',
             ROOT/'models/haze_world/evidence/kotsyurbenko2001_table2.csv',
             ROOT/'models/haze_world/evidence/peters1998_chemostat.csv', ROOT/'uv.lock']
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}


def leading(matrix):
    values = eigvals(matrix, check_finite=True)
    value = values[np.argmax(values.real)]
    return float(value.real), float(abs(value.imag))


def thermal_builder(y, p, side=0, two_layer=False):
    a, b, _ = model.jacobian_blocks(y, p)
    scales = model.state_scales(y, p)
    indices = model.active_indices(p)
    a = (a*scales[None, :]/scales[:, None])[np.ix_(indices, indices)]
    b = (b/scales)[indices]
    column = int(np.flatnonzero(indices == p.state_size-1)[0])
    slope = model.climate_slope(y[-1], p, side)*scales[-1]
    reduced = a.copy(); reduced[:, column] += b*slope
    def build(tau):
        if tau == 0:
            return reduced
        n = len(indices)
        out = np.zeros((n+(2 if two_layer else 1),)*2)
        out[:n, :n] = a; out[:n, n] = b
        out[n, column] = slope/tau
        out[n, n] = -1/tau
        if two_layer:
            out[n, n] = -2/tau; out[n, n+1] = 1/tau
            out[n+1, n] = 1/(100*tau); out[n+1, n+1] = -1/(100*tau)
        return out
    return build


def lag_spectrum(builder):
    cache = {}
    def value(tau):
        if tau not in cache:
            cache[tau] = leading(builder(tau))
        return cache[tau][0]
    rows = {f'lambda_real_tau_{tau:g}': value(tau) for tau in LAGS}
    rows.update({f'lambda_imag_tau_{tau:g}': cache[tau][1] for tau in LAGS})
    if value(0.) >= -1e-9:
        status, critical = ('already_unstable' if value(0.) > 1e-9 else 'neutral'), 0.
    else:
        status, critical = 'not_detected_through_10000', None
    grid = np.unique(np.r_[LAGS[1:], np.geomspace(.001, 1e4, 29)])
    transitions = []
    left = 0.; fl = value(left)
    for right in grid:
        fr = value(float(right))
        if fl*fr < 0:
            root = brentq(value, left, float(right), xtol=1e-8)
            transitions.append(dict(tau_yr=float(root), direction='loss' if fl < 0 else 'restabilisation'))
        left, fl = float(right), fr
    if status not in ('already_unstable', 'neutral'):
        losses = [r['tau_yr'] for r in transitions if r['direction'] == 'loss']
        if losses:
            status, critical = 'finite_crossing', losses[0]
    return dict(rows, critical_lag_status=status, critical_lag_yr=critical,
                crossing_list=json.dumps(transitions), lambda_real_tau_10000=value(1e4))


def is_corner(y, p):
    return bool(np.any(np.isclose(y[-1], core.response(p.base.climate.case).ratios, rtol=0., atol=1e-9)))


def control_records(p, seeds=()):
    control = replace(p, base=replace(p.base, enabled=(False, True)))
    records = model.equilibrium_states(control, seeds=seeds)
    for record in records:
        if record['status'] == 'accepted' and record['physiology_status'] == 'in_domain':
            record['max_real_yr'] = leading(model.reduced_matrix(record['y'], control))[0]
    return control, records


def gain_record(equilibrium, p, control, controls, side=0):
    response = model.implicit_response(equilibrium['y'], p, side)
    out = dict(community_slope_k=response['dtemperature_dlog_supply'],
               community_condition=response['condition_number'], control_slope_k=None,
               gain=None, gain_status='no_admissible_control', control_temperature_k=None,
               control_ratio=None, control_max_real_yr=None)
    admissible = [r for r in controls if r['kind'] == 'methanogen' and r['status'] == 'accepted'
                  and r['physiology_status'] == 'in_domain' and r.get('max_real_yr', 0.) < -1e-9]
    if len(admissible) != 1:
        if len(admissible) > 1:
            out['gain_status'] = 'ambiguous_control'
        return out
    c = admissible[0]
    out.update(control_temperature_k=c['t_k'], control_ratio=c['r'], control_max_real_yr=c['max_real_yr'])
    if is_corner(c['y'], control):
        out['gain_status'] = 'control_climate_corner'
        return out
    cr = model.implicit_response(c['y'], control)
    out['control_slope_k'] = cr['dtemperature_dlog_supply']
    if response['status'] != 'defined' or cr['status'] != 'defined':
        out['gain_status'] = 'singular_response'
    elif abs(out['control_slope_k']) < 1e-10:
        out['gain_status'] = 'zero_control_slope'
    else:
        out.update(gain=float(out['community_slope_k']/out['control_slope_k']), gain_status='defined')
    return out


def describe(equilibrium, p, control, controls, two_layer=False):
    if equilibrium['status'] != 'accepted' or equilibrium['physiology_status'] != 'in_domain':
        return [dict(status='domain_or_residual_unresolved', temperature_k=equilibrium['t_k'], ratio=equilibrium['r'])]
    rows = []
    for side in (-1, 1) if is_corner(equilibrium['y'], p) else (0,):
        spectrum = lag_spectrum(thermal_builder(equilibrium['y'], p, side, two_layer))
        row = dict(status='accepted', kind=equilibrium['kind'], temperature_k=equilibrium['t_k'],
                   ratio=equilibrium['r'], climate_side=side, residual=equilibrium['residual'],
                   support_min_k=equilibrium['support_min_k'], support_max_k=equilibrium['support_max_k'],
                   minimum_local_biomass=float(np.min(equilibrium['y'][:-1].reshape(p.n, 4)[:, 1:3])),
                   mean_biomass_a=float(equilibrium['y'][:-1].reshape(p.n,4)[:,1].mean()),
                   mean_biomass_m=float(equilibrium['y'][:-1].reshape(p.n,4)[:,2].mean()),
                   per_capita_residual_yr=float(np.max(np.abs(model.biomass_per_capita(equilibrium['y'],p)))),
                   **gain_record(equilibrium, p, control, controls, side), **spectrum)
        rows.append(row)
    return rows


def resample_seed(y, old, new):
    stocks = np.asarray(y[:-1]).reshape(old.n, 4)
    out = np.stack([np.interp(new.offsets, old.offsets, stocks[:, j]) for j in range(4)], axis=1)
    return np.r_[out.ravel(), y[-1]]


def grid_job(setting):
    chemistry, fraction, loss_h, potential = setting
    result, raw, inventory = [], [], []
    previous = {}
    for sigma in SPREADS:
        for n in (1,) if sigma == 0 else (9, 17, 33):
            p = parameters(chemistry, fraction, loss_h, potential, sigma, n)
            seeds = []
            if sigma and (sigma, 9) in previous and n != 9:
                old, records = previous[sigma, 9]
                seeds = [resample_seed(r['y'], old, p) for r in records]
            records = model.equilibrium_states(p, seeds=seeds)
            mixed = [r for r in records if r['kind'] == 'mixed']
            previous[sigma, n] = p, mixed
            control, controls = control_records(p)
            common = dict(chemistry=chemistry, fraction=fraction, loss_h=loss_h,
                          nominal_potential=potential, sigma_k=sigma, n_habitats=p.n,
                          lifetime_yr=10000., slope_multiplier=1., two_layer=False)
            if not controls:
                inventory.append(dict(common, control_status='no_control_root_found',
                                      interpretation='finite_spread_search_unresolved'))
            for c in controls:
                inventory.append(dict(common, control_kind=c['kind'], control_status=c['status'],
                    physiology_status=c['physiology_status'], temperature_k=c['t_k'], ratio=c['r'],
                    residual=c['residual'], support_min_k=c['support_min_k'], support_max_k=c['support_max_k'],
                    max_real_yr=c.get('max_real_yr')))
            if sigma:
                for c in model.equilibrium_states(replace(control, sigma_k=0.)):
                    if c['kind']=='methanogen':
                        inventory.append(dict(common, control_kind='homogeneous_seed_only',
                            control_status='seed_diagnostic_not_spread_equilibrium', temperature_k=c['t_k'],
                            support_min_k=c['t_k']-sigma, support_max_k=c['t_k']+sigma))
            if not mixed:
                result.append(dict(common, status='no_detected_mixed' if not sigma else 'spread_search_unresolved'))
            for branch, equilibrium in enumerate(mixed):
                for row in describe(equilibrium, p, control, controls):
                    result.append(dict(common, branch=branch, **row))
                raw.append(dict(common, branch=branch, y=equilibrium['y'].tolist(),
                                status=equilibrium['status'], residual=equilibrium['residual']))
    return dict(settings=setting, rows=result, states=raw, controls=inventory)


def sensitivity_jobs():
    for chemistry, fraction, loss_h, potential, lifetime in itertools.product(
            ('fixed', 'products'), (0., .5), LOSSES, SUPPLIES, (6000., 10000., 19000.)):
        p = parameters(chemistry, fraction, loss_h, potential, lifetime=lifetime)
        records = model.equilibrium_states(p)
        control, controls = control_records(p)
        for slope in (.5, 1., 2.):
            q = replace(p, slope_multiplier=slope)
            qc = replace(control, slope_multiplier=slope)
            qualified_controls = [dict(c, max_real_yr=leading(model.reduced_matrix(c['y'], qc))[0])
                                  for c in controls if c['status'] == 'accepted']
            for equilibrium in [r for r in records if r['kind'] == 'mixed']:
                for row in describe(equilibrium, q, qc, qualified_controls):
                    yield dict(chemistry=chemistry, fraction=fraction, loss_h=loss_h,
                               nominal_potential=potential, lifetime_yr=lifetime,
                               slope_multiplier=slope, sigma_k=0., n_habitats=1, **row)


def two_layer_rows(states):
    for item in states:
        if item['chemistry'] not in ('fixed', 'products') or item['fraction'] != .5 or item['loss_h'] != .001:
            continue
        if item['sigma_k'] not in (0., 3.) or item['n_habitats'] not in (1, 33):
            continue
        p = parameters(item['chemistry'], item['fraction'], item['loss_h'], item['nominal_potential'], item['sigma_k'], item['n_habitats'])
        y = np.array(item['y']); e = model._record(y, p, 'mixed')
        control, controls = control_records(p)
        for row in describe(e, p, control, controls, two_layer=True):
            yield dict({k:v for k,v in item.items() if k != 'y'}, two_layer=True, **row)


def exact_homogeneous_band(p, y):
    if p.n != 1 or p.acetate_feedback:
        return None
    pair = model.local_guilds(y[:4], y[-1], model.temperature(y[-1], p), p)
    q = np.array([g.maintenance+p.base.biology.loss_h/g.yield_g_mol for g in pair])
    efficiency = 1-np.array([g.assimilation_mol_g for g in pair])*p.base.biology.loss_h/q
    abiotic = core.atmosphere(p.base.climate.case)['flux_to_ratio_per_yr']*p.base.climate.abiotic_flux
    needed = 4*(p.base.loss.rate(y[-1])-abiotic)/(core.inventory_to_ratio(p.base)*model.YEAR)
    outlet = p.base.biology.exchange_mol_l_h_pa*(y[0]-p.base.biology.atmosphere_pa)
    scale = .3/core.supply_h2(core.reference())
    f = p.base.acetate_fraction
    jm = outlet+needed/efficiency[1]
    ja = outlet+needed/(f*efficiency[0]) if f else None
    return dict(lower_potential=jm*scale, upper_potential=ja*scale if ja is not None else None,
                lower_status='exact_pure_m_endpoint', upper_status='exact_pure_a_endpoint' if f else 'unbounded_in_fixed_background_algebra',
                abiotic_ratio_yr=abiotic, method='homogeneous_fixed_allocation_algebra')


def branch_band(p, y, nominal, lower=.03, upper=1.2):
    exact = exact_homogeneous_band(p, y)
    if exact is not None:
        return exact
    endpoints = {}
    for direction, limit in ((-1, lower), (1, upper)):
        phi, state = nominal, y
        status = 'supply_window_censored'
        for _ in range(24):
            trial = max(limit, phi/1.25) if direction < 0 else min(limit, phi*1.25)
            if trial == phi:
                break
            q = replace(p, base=replace(p.base, climate=replace(p.base.climate,
                        donor_flux=p.base.climate.donor_flux*trial/nominal)))
            found = model.continue_equilibrium(state, q)
            if found is None:
                status = 'continuation_loss_or_domain_unresolved'
                break
            phi, state = trial, found['y']
            if phi == limit:
                break
        name = 'lower' if direction < 0 else 'upper'
        endpoints[name+'_potential'] = float(phi)
        endpoints[name+'_status'] = status
    return dict(endpoints, method='resolved_branch_segment_not_global_band')


def supply_bands(states):
    chosen = {}
    for item in sorted(states, key=lambda r:abs(r['nominal_potential']-.3)):
        if item['n_habitats'] not in (1, 33) or item['status'] != 'accepted':
            continue
        key = tuple(item[k] for k in ('chemistry', 'fraction', 'loss_h', 'sigma_k', 'n_habitats'))
        # Different starting roots are retained unless their ratios coincide;
        # slope sign alone cannot establish that two branches connect.
        key += (round(item['y'][-1], 10),)
        if key not in chosen:
            chosen[key] = item
    result = []
    for key, item in chosen.items():
        p = parameters(item['chemistry'], item['fraction'], item['loss_h'], item['nominal_potential'], item['sigma_k'], item['n_habitats'])
        result.append(dict(chemistry=item['chemistry'], fraction=item['fraction'], loss_h=item['loss_h'],
                           sigma_k=item['sigma_k'], n_habitats=item['n_habitats'], start_ratio=item['y'][-1],
                           start_potential=item['nominal_potential'], **branch_band(p, np.array(item['y']), item['nominal_potential'])))
    return result


def write_csv(path, rows):
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, columns, lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def run(output, cache, workers=2, limit=None):
    output.mkdir(parents=True, exist_ok=True); cache.mkdir(parents=True, exist_ok=True)
    hashes = source_hashes()
    stamp = sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    jobs = list(itertools.product(model.CHEMISTRIES, (0., .5, .9), LOSSES, SUPPLIES))
    if limit is not None:
        jobs = jobs[:limit]
    rows, states, inventory, pending = [], [], [], []
    for setting in jobs:
        name = sha256(json.dumps([stamp, setting]).encode()).hexdigest()[:20]+'.json'
        path = cache/name
        if path.exists():
            record = json.loads(path.read_text())
            rows += record['rows']; states += record['states']; inventory += record['controls']
        else:
            pending.append((setting, path))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        future_paths = {pool.submit(grid_job, setting):path for setting, path in pending}
        for count, future in enumerate(as_completed(future_paths), 1):
            record = future.result()
            future_paths[future].write_text(json.dumps(record, allow_nan=False)+'\n')
            rows += record['rows']; states += record['states']; inventory += record['controls']
            if count % 10 == 0:
                print(f'completed {count}/{len(pending)} new families', flush=True)
    rows.sort(key=lambda r:tuple(str(r.get(k,'')) for k in ('chemistry','fraction','loss_h','nominal_potential','sigma_k','n_habitats','ratio')))
    paths = []
    for n, name in ((9,'stability_gain.csv'), (17,'resolution_17.csv'), (33,'resolution_33.csv')):
        selected = [r for r in rows if r['n_habitats'] in ((1,9) if n == 9 else (n,))]
        path = output/name; write_csv(path, selected); paths.append(path)
    sensitivity = list(sensitivity_jobs()) if limit is None else []
    layers = list(two_layer_rows(states))
    bands = supply_bands(states)
    for name, data in (('closure_sensitivity.csv', sensitivity), ('two_layer.csv', layers), ('supply_bands.csv', bands)):
        path=output/name; write_csv(path, data); paths.append(path)
    path=output/'control_inventory.csv';write_csv(path,inventory);paths.append(path)
    manifest = dict(source_sha256=hashes, method_freeze_commit='db09eea', families=len(jobs), rows=len(rows),
                    accepted_rows=sum(r['status']=='accepted' for r in rows), state_records=len(states),
                    missing_rows=sum(r['status']!='accepted' for r in rows), workers=workers,
                    definition='All roots found by algebra and declared homotopy; finite searches are not complete certificates.',
                    outputs_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in paths})
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    (cache/f'states-{stamp[:16]}.json').write_text(json.dumps(states, allow_nan=False)+'\n')
    print(json.dumps(manifest, indent=2), flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'models/haze_world/figures/dynamic_realisation')
    parser.add_argument('--cache', type=Path, default=ROOT/'local/haze/dynamic_realisation')
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--limit', type=int)
    args=parser.parse_args()
    run(args.output, args.cache, args.workers, args.limit)


if __name__ == '__main__':
    main()
