"""Reproduce the opening-kernel controls without physical trajectory runs."""

from hashlib import sha256
from importlib.util import module_from_spec, spec_from_loader
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.special import gammainc

from terra_prisca.haze_world import dormancy_branching as current

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = Path(__file__).with_suffix('.json')
SOURCE = 'src/terra_prisca/haze_world/dormancy_branching.py'
OLD_COMMIT = '0455d15'
OLD_SHA256 = '3e423ee451d46b1f5ec269047513751d109cb365b97d34b174898fce405f6405'


def old_source():
    source = subprocess.check_output(['git', 'show', f'{OLD_COMMIT}:{SOURCE}'], cwd=ROOT)
    if sha256(source).hexdigest() != OLD_SHA256:
        raise RuntimeError('Changed historical opening-kernel source')
    module = module_from_spec(spec_from_loader('terra_prisca.haze_world._opening_review_old', loader=None))
    exec(compile(source, '<historical_opening_kernel>', 'exec'), module.__dict__)
    return module


def chain(module, duration, affine):
    q = np.zeros((6, 6))
    for i in range(1, 6):
        q[i, i-1] = 1.
    factor = (lambda t: .5+.5*t/duration) if affine else (lambda t: 1.)
    rates = lambda t: (np.zeros(6), np.zeros(6), q*factor(t))
    initial = np.r_[0., np.full(5, -1000.)]
    coarse = module._positive_step(initial, duration, duration, rates)
    half = module._positive_step(initial, duration, duration/2, rates)
    fine = module._positive_step(half, duration/2, duration/2, rates)
    probability = gammainc(5, duration*(.75 if affine else 1.))
    exact = float(np.logaddexp(np.log(probability), np.log1p(-probability)-1000.))
    return dict(coarse_log_survival=float(coarse[-1]), fine_log_survival=float(fine[-1]),
                analytic_log_survival=exact, coarse_absolute_log_error=abs(float(coarse[-1])-exact),
                fine_absolute_log_error=abs(float(fine[-1])-exact))


def boundary(module):
    random = np.random.default_rng(831)
    for _ in range(2):
        start, end = random.random((6, 6)), random.random((6, 6))
        np.fill_diagonal(start, 0.); np.fill_diagonal(end, 0.)
    duration = .3/max(start.sum(axis=1).max(), end.sum(axis=1).max())
    rates = lambda t: (np.zeros(6), np.full(6, 1e-20), start+(t/duration)*(end-start))
    value = module._positive_step(np.zeros(6), duration, duration, rates)
    scalar = module._birth_death_step(np.zeros(1), np.array([3.1622776601683794e-12]),
                                     np.zeros(1), 1e-12)
    return dict(maximum_log_survival=float(max(value)), minimum_log_survival=float(min(value)),
                analytic_common_death_log_survival=-1e-20*duration,
                scalar_zero_death_log_survival=float(scalar[0]))


def captured_opening(old):
    path = ROOT/'local/haze/probability_pilots/conversion0006_probe/report.json'
    if not path.exists():
        return dict(status='capture_not_available')
    record = json.loads(path.read_text())
    trace = record['final_opening_trace']
    attempt = trace['attempts'][-1]
    start, duration = trace['start'], attempt['duration']
    knots = np.array([start-duration, start-duration/2, start])
    arrays = [np.asarray(attempt[key][j]) for j in range(3)
              for key in ('rates_at_end', 'rates_at_midpoint', 'rates_at_start')]
    rates = [np.array(arrays[k:k+3]) for k in range(0, 9, 3)]

    def interpolate(time):
        k = min(max(int(np.searchsorted(knots, time))-1, 0), 1)
        fraction = min(max((time-knots[k])/(knots[k+1]-knots[k]), 0.), 1.)
        return tuple(array[k]+fraction*(array[k+1]-array[k]) for array in rates)

    answers = {}
    for name, module in [('old', old), ('repaired', current)]:
        accepted = np.array(trace['accepted'])
        coarse = module._positive_step(accepted, start, duration, interpolate)
        half = module._positive_step(accepted, start, duration/2, interpolate)
        fine = module._positive_step(half, start-duration/2, duration/2, interpolate)
        error = max(abs(fine-coarse)/(trace['atol']+trace['rtol']*np.maximum(1., abs(fine))))
        answers[name] = dict(fine=fine.tolist(), error=float(error), maximum_fine=float(max(fine)))
    difference = max(abs(np.array(answers['old']['fine'])-answers['repaired']['fine']))
    if difference > 1e-10 or answers['repaired']['error'] > 1. or answers['repaired']['maximum_fine'] > 0.:
        raise RuntimeError('Captured resolved opening changed outside its control tolerance')
    return dict(status='captured_resolved_opening_only', report_sha256=sha256(path.read_bytes()).hexdigest(),
                physical_raw_sha256=record['raw_sha256'], start_yr=start, duration_yr=duration,
                old_and_repaired=answers, maximum_fine_log_difference=float(difference),
                qualification='The 60-second old-source probe did not reach the later terminal failure. This replay uses its captured affine rate arrays only, not a physical reintegration.')


def main():
    old = old_source()
    rows = []
    for affine in (False, True):
        for duration in (1e-6, 1e-8, 1e-10):
            before, after = chain(old, duration, affine), chain(current, duration, affine)
            if max(after['coarse_absolute_log_error'], after['fine_absolute_log_error']) > 2*duration:
                raise RuntimeError('Five-hop analytic control failed')
            rows.append(dict(affine=affine, duration_yr=duration, old=before, repaired=after))
    old_boundary, new_boundary = boundary(old), boundary(current)
    if new_boundary['maximum_log_survival'] > 0. or new_boundary['scalar_zero_death_log_survival'] != 0.:
        raise RuntimeError('Survival-one boundary control failed')
    result = dict(old_source_commit=OLD_COMMIT, old_source_sha256=OLD_SHA256,
        source_sha256={name: sha256((ROOT/name).read_bytes()).hexdigest() for name in
            (SOURCE, 'tests/test_dormancy_branching.py', str(Path(__file__).relative_to(ROOT)))},
        five_hop_controls=rows, survival_one_boundary=dict(old=old_boundary, repaired=new_boundary),
        captured_opening=captured_opening(old),
        scope='Positive scalar odds and normalized probability mixtures preserve exact survival boundaries; at least n-1 Poisson terms preserve representable leading simple paths. The absolute tail criterion is not an entrywise relative-error or global survival-probability guarantee. Adaptive coarse/fine refinement and rare-window scope are unchanged. Full expanded-grid rescoring remains separate.')
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(output=str(OUTPUT.relative_to(ROOT)), output_sha256=sha256(OUTPUT.read_bytes()).hexdigest(),
                         chain_controls=len(rows), captured_opening=result['captured_opening']['status'])))


if __name__ == '__main__':
    main()
