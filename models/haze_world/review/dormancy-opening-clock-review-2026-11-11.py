"""Replay the captured failed opening using immutable recorded rate arrays."""

from hashlib import sha256
from importlib.util import module_from_spec, spec_from_loader
import json
from pathlib import Path
import subprocess

import numpy as np

from terra_prisca.haze_world import dormancy_branching as current

ROOT = Path(__file__).resolve().parents[3]
SOURCE = 'src/terra_prisca/haze_world/dormancy_branching.py'
PREDECESSOR = 'c5568cf81b53156cac7dc5aa1f8d6649ca697e8c'
PREDECESSOR_SHA = 'c754e3feac7baf81feb8bf2ffb353f488e06632586b06bb82f96c7969f6293df'
DATA = ROOT/'local/haze/dormancy_branching_failure_review'
QUALIFICATION = ROOT/'local/haze/dormancy_opening_clock_review/official0006_qualification.json'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def predecessor():
    source = subprocess.check_output(['git', 'show', f'{PREDECESSOR}:{SOURCE}'], cwd=ROOT)
    if sha256(source).hexdigest() != PREDECESSOR_SHA:
        raise RuntimeError('Changed predecessor probability source')
    module = module_from_spec(spec_from_loader('terra_prisca.haze_world._opening_clock_old', loader=None))
    exec(compile(source, '<predecessor_opening_clock>', 'exec'), module.__dict__)
    return module


def main():
    report = DATA/'official0006_failure.json'
    raw = DATA/'recovered_failure_rates_and_state.npz'
    expected = {'official0006_failure.json': '49c1cc7d19ba737f2fe4742c93d9cd804b9d9e2afdcccae3ceddf0de9b66cb25',
                'recovered_failure_rates_and_state.npz': '73275a79445983e5454a9cc2e8d58de7e2e3f154d212e1b07a898931f5793ba8'}
    if any(digest(DATA/name) != value for name, value in expected.items()):
        raise RuntimeError('Changed captured failure fixture')
    record = json.loads(report.read_text())
    payload = np.load(raw)
    times = payload['times']
    arrays = tuple(payload[key] for key in ('birth', 'death', 'transition'))
    accepted = payload['accepted']
    scalars = record['failure_scalars']
    scalar = lambda key: float.fromhex(scalars[key]['hex'])
    start, rate, rtol, atol = map(scalar, ('start', 'rate', 'rtol', 'atol'))
    knot = scalars['knot']
    initial = min(scalar('max_step'), start-times[knot], start-scalar('t0'), 1/rate)

    def absolute(time):
        k = min(max(int(np.searchsorted(times, time))-1, 0), len(times)-2)
        fraction = min(max((time-times[k])/(times[k+1]-times[k]), 0.), 1.)
        return tuple(a[k]+fraction*(a[k+1]-a[k]) for a in arrays)

    old = predecessor()
    results = {}
    for label, module in [('predecessor', old), ('local_clock', current)]:
        duration = initial
        local = current._local_rates(times, arrays, knot, start)
        for attempt in range(30):
            if label == 'predecessor':
                endpoint = start-duration
                coarse = module._positive_step(accepted, start, duration, absolute)
                half = module._positive_step(accepted, start, duration/2, absolute)
                fine = module._positive_step(half, start-duration/2, duration/2, absolute)
            else:
                endpoint, duration = current._backward_interval(start, duration)
                coarse = module._positive_step(accepted, 0., duration, local)
                half = module._positive_step(accepted, 0., duration/2, local)
                fine = module._positive_step(half, -duration/2, duration/2, local)
            error = float(max(abs(fine-coarse)/(atol+rtol*np.maximum(1., abs(fine)))))
            resolved = error <= 1. and np.all(fine <= 0.)
            if resolved or attempt == 29:
                break
            duration /= 2
        results[label] = dict(resolved=bool(resolved), attempt=attempt, error=error,
            duration_yr=duration, endpoint_yr=endpoint, coarse=coarse.tolist(), fine=fine.tolist(),
            maximum_fine=float(max(fine)), all_finite=bool(np.all(np.isfinite(fine))))
        if label == 'predecessor':
            if resolved or not np.array_equal(coarse, payload['coarse']) or not np.array_equal(fine, payload['fine']):
                raise RuntimeError('Actual predecessor failure was not reproduced exactly')
        elif not resolved:
            raise RuntimeError('Repaired captured opening did not resolve')
    old_duration = results['predecessor']['duration_yr']
    coarse_end = start-old_duration
    half_start = start-old_duration/2
    fine_end = half_start-old_duration/2
    endpoint, duration = current._backward_interval(start, old_duration)
    shifted = current._local_rates(times-start, arrays, knot, 0.)
    local = current._local_rates(times, arrays, knot, start)
    invariant = all(np.array_equal(a, b) for offset in np.linspace(-duration, 0., 9)
                    for a, b in zip(local(offset), shifted(offset)))
    if not invariant:
        raise RuntimeError('Local rate interpolation changed under a clock translation')
    qualified = dict(status='pending')
    if QUALIFICATION.exists():
        value = json.loads(QUALIFICATION.read_text())
        if value['source_sha256'].get(SOURCE) != digest(ROOT/SOURCE):
            raise RuntimeError('Official task used a different probability source')
        qualified = dict(status=value['status'], path=str(QUALIFICATION.relative_to(ROOT)),
            sha256=digest(QUALIFICATION), wall_seconds=value['wall_seconds'],
            sources_unchanged=value['sources_unchanged'], inputs_unchanged=value['inputs_unchanged'],
            selected_profile_fingerprint=value['inputs']['profile']['fingerprint'],
            official_rows_sha256=value.get('official_rows_sha256'))
    answer = dict(predecessor_commit=PREDECESSOR, predecessor_sha256=PREDECESSOR_SHA,
        source_sha256={name: digest(ROOT/name) for name in (SOURCE, 'tests/test_dormancy_branching.py', str(Path(__file__).relative_to(ROOT)))},
        input_sha256=expected, captured_case='dormancy_0006', guild='methanogen',
        window_scope=record['analyze_context'], start_yr=start, time_ulp_yr=float(np.spacing(start)),
        old_endpoint_clock_steps=dict(coarse=(start-coarse_end)/np.spacing(start),
            half_start=(start-half_start)/np.spacing(start), fine=(start-fine_end)/np.spacing(start)),
        aligned_endpoint_yr=endpoint, aligned_duration_yr=duration,
        clock_translation_bitwise=invariant, replay=results, official_complete_task=qualified,
        scope='Same recorded piecewise-affine rates, original30-attempt coarse/fine tolerance and probability bounds. A representable whole-step endpoint fixes actual duration before local-offset quadrature. No probability clipping, time fabrication, rate/window change, physical reintegration or general global-tail accuracy claim.')
    output = Path(__file__).with_suffix('.json')
    output.write_text(json.dumps(answer, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(output=str(output.relative_to(ROOT)), output_sha256=digest(output),
                         repaired_error=results['local_clock']['error'], official_complete_task=qualified['status'])))


if __name__ == '__main__':
    main()
