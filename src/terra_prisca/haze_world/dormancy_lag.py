"""Directional dormancy-at-equilibrium diagnostic for Stage B4.

The clipped linear ramp has no ordinary Jacobian at zero net growth.
Sector eigenvalues are diagnostics, not a nonsmooth stability certificate.
"""

import argparse
import csv
from dataclasses import replace
from hashlib import sha256
import itertools
import json
from pathlib import Path

import numpy as np

from . import dormancy
from . import habitat_coupling as habitat
from . import population_coupling as core


ROOT = Path(__file__).resolve().parents[3]
ACTIVE = np.array([0, 1, 2, 3, 6])
BANK = np.array([4, 5])


def mixed_reference(loss_h=.001):
    base = replace(core.reference(), acetate_fraction=0.)
    base = replace(base, biology=replace(base.biology, loss_h=loss_h))
    roots = [row for row in core.equilibrium_states(base)
             if row['kind'] == 'mixed' and row['stable']]
    if len(roots) != 1:
        raise ArithmeticError('Expected one stable instantaneous mixed reference')
    return base, np.asarray(roots[0]['y'])


def coefficients(base, state, relative_step=1e-5):
    state = np.asarray(state, dtype=float)
    if state.shape != (5,) or np.any(state <= 0) or base.activity_feedback != 'fixed':
        raise ValueError('B4 requires a positive five-stock fixed-product reference')
    scales = np.maximum(abs(state), [10., 1e-4, 1e-4, 1e-5, .01])
    steps = scales * relative_step
    jac = np.empty((5, 5))
    gradient = np.empty((2, 5))
    for j, step in enumerate(steps):
        delta = np.eye(5)[j] * step
        jac[:, j] = (core.rhs(state + delta, base) - core.rhs(state - delta, base)) / (2*step)
        gradient[:, j] = (core.fluxes(state + delta, base)['net_growth_yr']
                           - core.fluxes(state - delta, base)['net_growth_yr']) / (2*step)
    return dict(jacobian=jac*scales[None, :]/scales[:, None],
                net_gradient=gradient*scales[None, :], scales=scales,
                state=state, base=base)


def sector_matrix(data, epsilon, entering=(False, False), *, switching_factor=10., ramp='linear'):
    if not np.isfinite(epsilon) or epsilon <= 0 or ramp not in ('linear', 'cubic'):
        raise ValueError('Use a positive finite epsilon and a named ramp')
    if len(entering) != 2:
        raise ValueError('Choose the directional entry sector for both guilds')
    jac = np.zeros((7, 7))
    jac[np.ix_(ACTIVE, ACTIVE)] = data['jacobian']
    for guild, bank in enumerate(BANK):
        jac[bank, bank] = -epsilon*data['base'].biology.loss_h*core.HOURS_PER_YEAR
        if ramp == 'linear' and entering[guild]:
            gradient = switching_factor*data['state'][guild+1]/data['scales'][guild+1]*data['net_gradient'][guild]
            jac[guild+1, ACTIVE] += gradient
            jac[bank, ACTIVE] -= gradient
    return jac


def directional_derivative(data, direction, epsilon, *, switching_factor=10., ramp='linear'):
    direction = np.asarray(direction, dtype=float)
    if direction.shape != (7,):
        raise ValueError('The scaled dormant state has seven components')
    entering = data['net_gradient'] @ direction[ACTIVE] < 0
    return sector_matrix(data, epsilon, entering, switching_factor=switching_factor, ramp=ramp) @ direction


def scaled_physical_state(data):
    scales = np.r_[data['scales'][:4], data['scales'][1:3], data['scales'][4]]
    state = np.r_[data['state'][:4], 0., 0., data['state'][4]]
    return state, scales


def dormancy_parameters(base, epsilon, ramp='linear', switching_factor=10.):
    return dormancy.Dormancy(habitat.Habitats(base=base), epsilon, switching_factor, ramp)


def spectrum_record(matrix):
    eigenvalues = np.linalg.eigvals(matrix)
    leading = eigenvalues[np.argmax(eigenvalues.real)]
    complex_values = eigenvalues[abs(eigenvalues.imag) > 1e-8]
    complex_leading = complex_values[np.argmax(complex_values.real)] if complex_values.size else None
    return dict(leading_real_yr=float(leading.real), leading_imag_yr=float(abs(leading.imag)),
                complex_leading_real_yr=float(complex_leading.real) if complex_leading is not None else None,
                complex_period_yr=float(2*np.pi/abs(complex_leading.imag)) if complex_leading is not None else None,
                eigenvalues=[[float(v.real), float(v.imag)] for v in eigenvalues])


def lag_matrix(data, tau_yr):
    if not np.isfinite(tau_yr) or tau_yr <= 0:
        raise ValueError('Thermal lag must be positive and finite')
    base, y = data['base'], data['state']
    t = float(core.temperature_k(y[4], base.climate))
    step = 1e-4
    b = (fixed_temperature_rhs(y, base, t+step)-fixed_temperature_rhs(y, base, t-step))/(2*step)
    response = core.response(base.climate.case)
    j = np.searchsorted(response.ratios, y[4])-1
    slope = np.diff(response.temperatures_k)[j] / np.diff(response.ratios)[j]
    climate_chain = b*data['scales'][4]*slope/data['scales']
    fixed_jac = data['jacobian'].copy()
    fixed_jac[:, 4] -= climate_chain
    matrix = np.zeros((6, 6))
    matrix[:5, :5] = fixed_jac
    matrix[:5, 5] = b/data['scales']
    matrix[5, 4] = slope*data['scales'][4]/tau_yr
    matrix[5, 5] = -1/tau_yr
    return matrix


def fixed_temperature_rhs(y, p, t):
    f = core.fluxes_at_temperature(y, p, t)
    return np.r_[(f['supply_h2_mol_l_yr']-sum(f['uptake_h2_mol_l_yr'])-f['outlet_h2_mol_l_yr'])/core.HENRY_30C_MOL_L_PA,
                 np.asarray(y)[1:3]*f['net_growth_yr'],
                 f['acetate_production_mol_l_yr']-f['acetate_recycling_mol_l_yr']-f['acetate_export_mol_l_yr'],
                 f['methane_source_ratio_yr']-f['methane_loss_ratio_yr']]


def recorded_period_comparisons():
    rows = []
    files = ('dormancy126_cycle_0024.json', 'dormancy126_cycle_0126.json', 'dormancy0012_cycle_check.json')
    for filename in files:
        path = ROOT/'models/haze_world/review'/filename
        record = json.loads(path.read_text())
        case = record['protocol']['case']
        tau = 1/(case['epsilon']*case['loss_h']*core.HOURS_PER_YEAR)
        base, state = mixed_reference(case['loss_h'])
        spectrum = spectrum_record(lag_matrix(coefficients(base, state), tau))
        period = record['control_window']['period_yr']
        rows.append(dict(case_id=case['case_id'], configuration=case['configuration'],
                         loss_h=case['loss_h'], epsilon=case['epsilon'],
                         switching_factor=case['switching_factor'], fraction=case['fraction'],
                         matched_well_mixed_geometry=case['configuration']=='none',
                         bank_lifetime_yr=tau, recorded_period_yr=period,
                         thermal_period_yr=spectrum['complex_period_yr'],
                         ratio_recorded_to_thermal=period/spectrum['complex_period_yr'] if spectrum['complex_period_yr'] else None,
                         within_30_percent=abs(period/spectrum['complex_period_yr']-1) <= .3 if spectrum['complex_period_yr'] and case['configuration']=='none' else None,
                         thermal_leading_real_yr=spectrum['leading_real_yr'],
                         source=str(path.relative_to(ROOT)), source_sha256=sha256(path.read_bytes()).hexdigest(),
                         comparison_scope='Recorded cubic finite trajectory versus linear thermal mode; warm-refuge case is not a matched well-mixed geometry'))
    return rows


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    base, y = mixed_reference()
    data = coefficients(base, y)
    rows, spectra = [], []
    for epsilon in np.geomspace(1e-4, .1, 13):
        for ramp, entering in [('cubic', (False, False)), *[('linear', s) for s in itertools.product((False, True), repeat=2)]]:
            spectrum = spectrum_record(sector_matrix(data, float(epsilon), entering, ramp=ramp))
            row = dict(epsilon=float(epsilon), loss_h=base.biology.loss_h,
                       loss_yr=base.biology.loss_h*core.HOURS_PER_YEAR,
                       bank_lifetime_yr=1/(epsilon*base.biology.loss_h*core.HOURS_PER_YEAR),
                       ramp=ramp, entry_a=entering[0], entry_m=entering[1],
                       interpretation='directional_sector_not_stability_certificate' if ramp=='linear' else 'ordinary_jacobian',
                       **{k:v for k,v in spectrum.items() if k!='eigenvalues'})
            rows.append(row)
            spectra.append(row | dict(eigenvalues=spectrum['eigenvalues']))
    comparisons = recorded_period_comparisons()
    for name, records in (('dormancy_lag.csv', rows), ('dormancy_cycle_comparison.csv', comparisons)):
        with (output/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, list(records[0]), lineterminator='\n')
            writer.writeheader(); writer.writerows(records)
    sources = [Path(__file__), Path(dormancy.__file__), Path(core.__file__), Path(habitat.__file__),
               *[Path(__file__).with_name(name+'.py') for name in
                 ('two_guilds', 'methane_budget', 'darwinian', 'hydrogen_uptake', 'woodii1998')],
               ROOT/'models/haze_world/dynamic-realisation-spec.md',
               ROOT/'models/haze_world/dynamic-realisation-methods.md', ROOT/'uv.lock',
               *[ROOT/path for path in ('models/haze_response/arney2016/figure4.csv',
                                         'models/haze_response/arney2016/cases.csv',
                                         'models/haze_world/evidence/kotsyurbenko2001_table2.csv',
                                         'models/haze_world/evidence/peters1998_chemostat.csv')]]
    manifest = dict(scope='B4 directional derivative diagnostic, not a smooth Hopf or nonsmooth stability certificate',
                    status_pb7='refuted_local_epsilon_Hopf_mechanism_and_matched_period_clause',
                    local_mechanism='Active directional subsystem is independent of epsilon; banks have no first-order return coupling at zero bank equilibrium',
                    matched_period_tests=sum(r['matched_well_mixed_geometry'] for r in comparisons),
                    matched_period_failures=sum(r['matched_well_mixed_geometry'] and not r['within_30_percent'] for r in comparisons),
                    reference_state=y.tolist(), temperature_k=float(core.temperature_k(y[4], base.climate)),
                    source_sha256={str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in sources},
                    rows=len(rows), spectra=spectra, cycle_comparisons=comparisons,
                    output_sha256={name:sha256((output/name).read_bytes()).hexdigest() for name in ('dormancy_lag.csv', 'dormancy_cycle_comparison.csv')})
    (output/'dormancy_lag_manifest.json').write_text(json.dumps(manifest, indent=2, allow_nan=False)+'\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'models/haze_world/figures/dynamic_realisation')
    args = parser.parse_args()
    report = run(args.output)
    print(json.dumps(dict(rows=report['rows'], pb7=report['status_pb7'])))


if __name__ == '__main__':
    main()
