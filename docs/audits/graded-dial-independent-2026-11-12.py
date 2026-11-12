"""Independent recount and physical-derivative checks of the graded dials."""

import argparse
import csv
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.linalg import eigvals
from scipy.stats import spearmanr

from terra_prisca.haze_world import continuum_characteristic as characteristic
from terra_prisca.haze_world import continuum_core as parameters
from terra_prisca.haze_world import dynamic_core as historical
from terra_prisca.haze_world import population_coupling as physical
from terra_prisca.haze_world.two_guilds import guilds

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def recount():
    records = []
    sources = {}
    for name, stage in (('c0_local_gain.csv', 'C0'), ('c1_resolved.csv', 'C1')):
        path = ROOT/'models/haze_world/figures/continuum_habitats'/name
        sources[str(path.relative_to(ROOT))] = digest(path)
        with path.open() as stream:
            for row in csv.DictReader(stream):
                if row['gain_status'] != 'defined':
                    continue
                status = row['critical_lag_status']
                if status not in ('finite_crossing', 'already_unstable', 'not_detected_through_10000'):
                    raise ValueError('An unknown spectral status cannot be replaced by zero lag')
                records.append(dict(stage=stage, Sc=float(row['Sc']), S0=float(row['S0']), status=status,
                                    tau=float(row['critical_lag_yr']) if status == 'finite_crossing' else None))
    pinned = [r for r in records if abs(r['Sc']) < 3e-10]
    ordinary = [r for r in records if abs(r['Sc']) >= 3e-10 and r['S0'] < 0]
    excluded = [r for r in records if r not in pinned and r not in ordinary]
    finite = [r for r in ordinary if r['stage'] == 'C1' and r['status'] == 'finite_crossing']
    return dict(total=len(records), pinned_count=len(pinned),
                pinned_finite=sum(r['status'] == 'finite_crossing' for r in pinned),
                pinned_already_unstable=sum(r['status'] == 'already_unstable' for r in pinned),
                pinned_max_abs_Sc=max(abs(r['Sc']) for r in pinned),
                pinned_max_finite_tau=max(r['tau'] for r in pinned if r['tau'] is not None),
                ordinary_count=len(ordinary), ordinary_censored=sum(r['tau'] is None for r in ordinary),
                ordinary_min_Sc=min(abs(r['Sc']) for r in ordinary),
                ordinary_min_finite_tau=min(r['tau'] for r in ordinary if r['tau'] is not None),
                excluded_count=len(excluded), excluded_all_unstable=all(r['status'] == 'already_unstable' for r in excluded),
                spatial_finite_count=len(finite),
                spatial_spearman=float(spearmanr([abs(r['Sc']) for r in finite], [r['tau'] for r in finite]).statistic),
                spatial_loglog_slope=float(np.polyfit(np.log([abs(r['Sc']) for r in finite]), np.log([r['tau'] for r in finite]), 1)[0]),
                input_sha256=sources,
                limit='Descriptive committed sample; no universal trade-off theorem, causal ordering or mathematical singularity.')


def local_flow(stocks, ratio, temperature, p, kappa):
    pair = list(guilds(float(temperature)-273.15, p.base.biology))
    factor = (float(stocks[3])/p.base.acetate_reference_mol_l)**(kappa/4)
    pair[0] = replace(pair[0], threshold_pa=pair[0].threshold_pa*factor)
    q = np.array([g.uptake(stocks[0]) for g in pair])
    ys = np.array([g.yield_g_mol for g in pair])
    synthesis = ys*(q-np.array([g.maintenance for g in pair]))
    catabolic = q-np.array([g.assimilation_mol_g for g in pair])*np.maximum(synthesis, 0)
    recycling, export = physical.recycling_rates(temperature, p.base)
    year = physical.HOURS_PER_YEAR
    flow = np.r_[year/physical.HENRY_30C_MOL_L_PA*(physical.supply_h2(p.base)-q@stocks[1:3]
                     -p.base.biology.exchange_mol_l_h_pa*(stocks[0]-p.base.biology.atmosphere_pa)),
                 year*stocks[1:3]*(synthesis-p.base.biology.loss_h)-p.dispersal_yr*stocks[1:3],
                 year*catabolic[0]*stocks[1]/4-(recycling+export)*stocks[3]]
    emission = physical.inventory_to_ratio(p.base)*(year*catabolic[1]*stocks[2]/4+recycling*stocks[3])
    return np.r_[flow, emission]


def assemble(p, y, kappa=0., log_step=1e-4, temperature_step=1e-4):
    """Finite physical derivatives, independent of every production Jacobian."""
    y = np.asarray(y, float)
    stock = y[:-1].reshape(-1, 4)
    if np.any(y <= 0):
        raise ValueError('Strictly positive mixed states are required')
    n = len(stock)
    temperature = float(physical.temperature_k(y[-1], p.base.climate))
    scales = np.maximum(stock, [10., 1e-5, 1e-5, 1e-6])
    globalscale = np.r_[np.maximum(p.weights@stock[:, 1:3], 1e-5), max(y[-1], .01), 1.]
    local = np.zeros((n, 4, 4)); injection = np.zeros((n, 4, 4))
    emission = np.zeros((n, 4)); selector = np.zeros((n, 2, 4))
    direct_r = []; direct_t = []
    for j, (x, offset) in enumerate(zip(stock, p.offsets)):
        t = temperature+offset
        derivatives = np.zeros((5, 5))
        for coordinate in range(5):
            values = []
            for factor in (-2., -1., 1., 2.):
                varied = np.r_[x, y[-1]]
                varied[coordinate] *= np.exp(factor*log_step)
                values.append(local_flow(varied[:4], varied[4], t, p, kappa))
            derivatives[:, coordinate] = (values[0]-8*values[1]+8*values[2]-values[3])/(12*log_step*np.r_[x, y[-1]][coordinate])
        values = [local_flow(x, y[-1], t+factor*temperature_step, p, kappa) for factor in (-2., -1., 1., 2.)]
        thermal = (values[0]-8*values[1]+8*values[2]-values[3])/(12*temperature_step)
        local[j] = derivatives[:4, :4]*scales[j][None, :]/scales[j][:, None]
        injection[j, 1, 0] = p.dispersal_yr*globalscale[0]/scales[j, 1]
        injection[j, 2, 1] = p.dispersal_yr*globalscale[1]/scales[j, 2]
        injection[j, :, 2] = derivatives[:4, 4]*globalscale[2]/scales[j]
        injection[j, :, 3] = thermal[:4]*globalscale[3]/scales[j]
        emission[j] = derivatives[4, :4]*scales[j]/globalscale[2]
        selector[j, 0, 1] = scales[j, 1]/globalscale[0]
        selector[j, 1, 2] = scales[j, 2]/globalscale[1]
        direct_r.append(derivatives[4, 4]); direct_t.append(thermal[4]/globalscale[2])
    slope = characteristic._climate_slope(y[-1], p)*globalscale[2]
    return characteristic.CharacteristicBlocks(local, injection, emission, selector, p.weights,
        float(p.weights@direct_r-p.base.loss.slope(y[-1])), float(p.weights@direct_t),
        slope, scales, globalscale)


def instantaneous(blocks):
    lagged = characteristic.dense_matrix(blocks, 1.)
    a = lagged[:-1, :-1].copy()
    a[:, -1] += lagged[:-1, -1]*blocks.climate_slope
    return a


def responses(p, y, blocks):
    jacobian = instantaneous(blocks)
    count = blocks.n; size = 4*count+1
    forcing = np.zeros(size)
    forcing[0:-1:4] = physical.HOURS_PER_YEAR/physical.HENRY_30C_MOL_L_PA*physical.supply_h2(p.base)/blocks.local_scales[:, 0]
    dy = np.linalg.solve(jacobian, -forcing)
    sc = float(blocks.climate_slope*dy[-1])
    lift = np.zeros((size, 3*count+1)); project = np.zeros((3*count+1, size))
    stock = np.asarray(y[:-1]).reshape(count, 4)
    for j, x in enumerate(stock):
        share = x[1]/(x[1]+x[2]); bscale = max(x[1]+x[2], 1e-5)
        lift[4*j, 3*j] = project[3*j, 4*j] = 1.
        lift[4*j+3, 3*j+2] = project[3*j+2, 4*j+3] = 1.
        lift[4*j+1, 3*j+1] = share*bscale/blocks.local_scales[j, 1]
        lift[4*j+2, 3*j+1] = (1-share)*bscale/blocks.local_scales[j, 2]
        project[3*j+1, 4*j+1:4*j+3] = blocks.local_scales[j, 1:3]/bscale
    lift[-1, -1] = project[-1, -1] = 1.
    frozen = project@jacobian@lift
    frozen_dy = np.linalg.solve(frozen, -project@forcing)
    s0 = float(blocks.climate_slope*frozen_dy[-1])
    return dict(Sc=sc, S0=s0, G_loc=sc/s0 if s0 else None,
                jacobian_condition=float(np.linalg.cond(jacobian)), frozen_condition=float(np.linalg.cond(frozen)),
                frozen_leading_real_yr=float(max(eigvals(frozen).real)))


def mode_diagnostic(blocks):
    matrix = instantaneous(blocks)
    values = eigvals(matrix)
    complex_values = values[values.imag > 1e-8]
    leading = values[np.argmax(values.real)]
    if not len(complex_values):
        return dict(status='no_complex_pair', leading=[float(leading.real), float(leading.imag)])
    pair = complex_values[np.argmax(complex_values.real)]
    gamma = -float(pair.real); omega = float(pair.imag)
    return dict(status='damped' if gamma > 0 else 'not_damped',
                leading=[float(leading.real), float(leading.imag)],
                complex_pair=[float(pair.real), float(pair.imag)],
                period_yr=2*np.pi/omega, damping_time_yr=1/gamma if gamma > 0 else None,
                weak_tau_yr=2*gamma/omega**2 if gamma > 0 else None,
                weak_damping_ratio=gamma/omega)


def source_hashes():
    paths = [Path(__file__), ROOT/'models/haze_world/graded-dial-spec.md', ROOT/'models/haze_world/graded-dial-methods.md',
             ROOT/'uv.lock', Path(characteristic.__file__), Path(physical.__file__), Path(historical.__file__)]
    paths += [ROOT/'src/terra_prisca/haze_world'/name for name in ('two_guilds.py', 'hydrogen_uptake.py', 'woodii1998.py',
                                                               'methane_budget.py', 'darwinian.py', 'continuum_core.py')]
    paths += [ROOT/'models/haze_response/arney2016'/name for name in ('cases.csv', 'figure4.csv')]
    return {str(path.relative_to(ROOT)): digest(path) for path in paths}


def baseline_conditions():
    records = []
    for fraction in (0., .5):
        base = replace(physical.reference(), acetate_fraction=fraction)
        p = parameters.WeightedParams(base, 'fixed')
        old = historical.DynamicParams(base, 'fixed')
        y = next(row['y'] for row in historical.equilibrium_states(old) if row['kind'] == 'mixed')
        blocks = assemble(p, y)
        matrix = instantaneous(blocks)
        spectrum = eigvals(matrix)
        lag = characteristic.critical_lags(blocks, frequencies=721)
        root = lag['crossings'][0]
        critical_spectrum = eigvals(characteristic.dense_matrix(blocks, root['tau_yr']))
        target = root['omega_yr']*1j
        distances = np.sort(abs(critical_spectrum-target))
        records.append(dict(fraction=fraction, positive_equilibrium=bool(np.all(y > 0)),
            scaled_static_condition=float(np.linalg.cond(matrix)),
            scaled_static_min_singular=float(np.linalg.svd(matrix, compute_uv=False)[-1]),
            largest_static_real=float(max(spectrum.real)),
            critical_lag_yr=root['tau_yr'], critical_frequency_yr=root['omega_yr'],
            critical_eigenvalue_residual=float(distances[0]), next_eigenvalue_distance=float(distances[1]),
            crossing_real_speed_per_tau=root['real_speed_per_tau'],
            backsubstitution_residual=root['backsubstitution_residual'],
            regular_simple_transversal=bool(np.linalg.cond(matrix) < 1e12 and distances[1] > 1e-6
                                            and root['real_speed_per_tau'] > 0 and root['accepted']),
            mode=mode_diagnostic(blocks)))
    return records


def check_state(record):
    stage = record['stage']
    fraction = float(record['fraction'])
    base = replace(physical.reference(), acetate_fraction=fraction)
    offsets = np.asarray(record.get('offsets', [0.]), float)
    weights = np.asarray(record.get('weights', [1.]), float)
    p = SimpleNamespace(base=base, offsets=offsets, weights=weights, dispersal_yr=float(record.get('dispersal_yr', .001)),
                        slope_multiplier=1., sigma_k=float(record.get('sigma_k', 0.)))
    kappa = float(record.get('kappa', 0.)) if stage == 'D1' else 0.
    y = np.asarray(record['y'], float)
    assembled = assemble(p, y, kappa)
    lag = characteristic.critical_lags(assembled, frequencies=721)
    fine = characteristic.critical_lags(assembled, frequencies=1441)
    response = responses(p, y, assembled)
    modes = mode_diagnostic(assembled)
    primary_tau = record.get('critical_lag_yr')
    comparison = dict(Sc_absolute_error=response['Sc']-record['Sc'],
                      S0_relative_error=response['S0']/record['S0']-1.,
                      finite_tau_relative_error=(lag['critical_lag_yr']/primary_tau-1.
                           if lag['critical_lag_yr'] is not None and primary_tau not in (None, 0.) else None),
                      frequency_refinement_relative_error=(fine['critical_lag_yr']/lag['critical_lag_yr']-1.
                           if fine['critical_lag_yr'] is not None and lag['critical_lag_yr'] is not None else None),
                      censor_classification_agrees=(lag['critical_lag_yr'] is None)==(primary_tau is None))
    main_pair = record.get('zero_lag_modes', {}).get('selected_pair')
    if main_pair and modes.get('complex_pair'):
        comparison.update(complex_real_absolute_error=modes['complex_pair'][0]-main_pair['real_yr'],
                          complex_frequency_relative_error=modes['complex_pair'][1]/main_pair['omega_yr']-1.)
    return dict(stage=stage, fraction=fraction, kappa=kappa, sigma_k=p.sigma_k, dispersal_yr=p.dispersal_yr,
                branch_id=record.get('branch_id'), dial=record.get('dial'), kind=record.get('kind'),
                independent_slopes=response, independent_mode=modes, independent_lag=lag, frequency_refinement=fine,
                comparison=comparison,
                reported_primary={k: record[k] for k in ('Sc', 'S0', 'critical_lag_yr', 'critical_lag_status') if k in record})


def choose(record):
    if record['stage'] == 'D1':
        return float(record.get('kappa', 0.)) in (0., .01, 1.)
    return ((float(record.get('sigma_k', 0.)), float(record.get('dispersal_yr', 0.))) in ((.1, 1e-4), (1., .001)))


def grid_recount(records):
    summaries = []
    for branch in sorted({row['branch_id'] for row in records}):
        rows = sorted([row for row in records if row['branch_id'] == branch], key=lambda row: row['dial'])
        finite_pairs = []; censor_bounds = []
        for left, right in zip(rows[:-1], rows[1:]):
            a, b = left.get('critical_lag_yr'), right.get('critical_lag_yr')
            if left['critical_lag_status'] == right['critical_lag_status'] == 'finite_crossing':
                finite_pairs.append(dict(lower_dial=left['dial'], upper_dial=right['dial'], tau_ratio=b/a))
            elif left['critical_lag_status'] == 'finite_crossing' and right['critical_lag_status'] == 'not_detected_through_10000':
                censor_bounds.append(dict(lower_dial=left['dial'], upper_dial=right['dial'], tau_ratio_lower_bound=1e4/a))
        fit_rows = [row for row in rows if row['critical_lag_status'] == 'finite_crossing'
                    and 2 < row['critical_lag_yr'] < 1000 and abs(row['Sc']) > 0]
        fit = dict(count=len(fit_rows), slope=None, R_squared=None, residuals=None,
                   linearity_status='No prospective residual tolerance; descriptive only')
        if len(fit_rows) >= 2:
            x = np.log([abs(row['Sc']) for row in fit_rows]); y = np.log([row['critical_lag_yr'] for row in fit_rows])
            coefficients = np.polyfit(x, y, 1); residuals = y-np.polyval(coefficients, x)
            fit.update(slope=float(coefficients[0]), R_squared=float(1-sum(residuals**2)/sum((y-y.mean())**2)),
                       residuals=residuals.tolist(), residual_degrees_of_freedom=len(fit_rows)-2,
                       slope_in_band=bool(1 <= coefficients[0] <= 2.5))
        eligible = [row for row in rows if row['critical_lag_status'] == 'finite_crossing' and row['critical_lag_yr'] < 100]
        weak_ratios = [row['weak_mode_tau_yr']/row['critical_lag_yr'] for row in eligible if row.get('weak_mode_tau_yr') is not None]
        summaries.append(dict(branch_id=branch, finite_pairs=finite_pairs, first_censored_transition_bounds=censor_bounds,
                              loglog_fit=fit, weak_mode_eligible=len(eligible), weak_mode_evaluated=len(weak_ratios),
                              weak_ratio_min=min(weak_ratios) if weak_ratios else None,
                              weak_ratio_max=max(weak_ratios) if weak_ratios else None,
                              weak_factor_two_failures=sum(not .5 <= ratio <= 2 for ratio in weak_ratios)))
    return dict(branches=summaries, records=len(records),
                prescribed_records=sum(row.get('kind') == 'prescribed' for row in records),
                interpretation='Finite adjacent ratios, censor-transition lower bounds and continuous mathematical behavior are separate estimands.')


def semantic_review(path, records, refinements):
    assessment = json.loads(path.read_text())
    for field in ('source_sha256', 'input_sha256'):
        for name, expected in assessment[field].items():
            if digest(ROOT/name) != expected:
                raise ArithmeticError('Assessor identity changed: '+name)
    expected = grid_recount(records)
    assert assessment['counts']['prescribed'] == expected['prescribed_records']
    assert assessment['counts']['baseline_controls'] == sum(row['kind'] == 'baseline' for row in records)
    for fit in assessment['PD2']['branches']:
        own = next(row['loglog_fit'] for row in expected['branches'] if row['branch_id'] == fit['branch_id'])
        assert fit['n'] == own['count'] and abs(fit['slope']-own['slope']) < 1e-12
    eligible = [row for row in records if row['critical_lag_status'] == 'finite_crossing' and row['critical_lag_yr'] < 100]
    extra = [row for row in refinements if row['critical_lag_status'] == 'finite_crossing' and row['critical_lag_yr'] < 100]
    failures = [row for row in extra if row.get('weak_mode_ratio') is None or not .5 <= row['weak_mode_ratio'] <= 2]
    assert len(assessment['PD4']['comparisons']) == len(eligible)
    assert len(assessment['PD4']['refinement_comparisons']) == len(extra)
    assert sum(not row['passed'] for row in assessment['PD4']['refinement_comparisons']) == len(failures)
    return dict(assessment_sha256=digest(path), assessor_sources=assessment['source_sha256'],
                all_assessor_input_hashes_match=True, grid_and_fit_recount_agrees=True,
                prescribed_weak_mode_eligible=sum(row['kind'] == 'prescribed' for row in eligible),
                baseline_weak_mode_eligible=sum(row['kind'] == 'baseline' for row in eligible),
                refinement_weak_mode_eligible=len(extra), refinement_weak_mode_failures=len(failures),
                accepted_statuses={key: assessment[key]['status'] for key in ('PD1', 'PD2', 'PD3', 'PD4')},
                limitation='PD1 supports finite pairs only and retains censored-transition bounds; PD2 linearity lacks a prospective tolerance.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--states', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'docs/audits/graded-dial-independent-2026-11-12.json')
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--threshold-states', type=Path)
    parser.add_argument('--threshold-brackets', type=Path)
    parser.add_argument('--assessment', type=Path)
    args = parser.parse_args()
    result = dict(C54=recount(), zero_dial_regularity=baseline_conditions(), source_sha256=source_hashes())
    if args.states:
        records = json.loads(args.states.read_text())
        if isinstance(records, dict):
            records = records.get('states', records.get('records'))
        result['states_sha256'] = digest(args.states)
        result['grid_recount'] = grid_recount(records)
        result['selected'] = [check_state(row) for row in records if args.all or choose(row)]
    if args.threshold_states:
        if args.threshold_brackets is None:
            raise ValueError('Threshold diagnostics require the final bracket manifest')
        threshold_records = json.loads(args.threshold_states.read_text())
        brackets = json.loads(args.threshold_brackets.read_text())
        if digest(args.threshold_states) != brackets['threshold_states_sha256']:
            raise ArithmeticError('Threshold state identity differs from bracket manifest')
        diagnostic = []; chosen = set()
        for bracket in brackets['branches']:
            keys = ('low_dial', 'high_dial') if bracket['stage'] == 'D1' else ('high_dial',)
            for key in keys:
                matches = [row for row in threshold_records if row['branch_id'] == bracket['branch_id'] and row['dial'] == bracket[key]]
                if len(matches) != 1:
                    raise ArithmeticError('Threshold endpoint must have exactly one state')
                diagnostic.append(check_state(matches[0]))
                chosen.add((matches[0]['branch_id'], matches[0]['dial']))
        for row in threshold_records:
            if row['critical_lag_status'] == 'finite_crossing' and row['critical_lag_yr'] < 100 \
                    and row.get('weak_mode_ratio') is not None and not .5 <= row['weak_mode_ratio'] <= 2:
                if (row['branch_id'], row['dial']) not in chosen:
                    diagnostic.append(check_state(row))
                    chosen.add((row['branch_id'], row['dial']))
        result['threshold_diagnostics'] = diagnostic
        result['threshold_selection_scope'] = 'Final D1 bracket endpoints, final D2 upper endpoints, plus already-computed weak-mode counterexamples selected after diagnosis.'
        result['threshold_input_sha256'] = {str(args.threshold_states): digest(args.threshold_states),
                                            str(args.threshold_brackets): digest(args.threshold_brackets)}
    if args.assessment:
        result['semantic_review'] = semantic_review(args.assessment, records, threshold_records)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(C54=result['C54'], selected_count=len(result.get('selected', []))), indent=2))


if __name__ == '__main__':
    main()
