"""Bounded Issue 2 counterexample and recount; no integrations or supply grid."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / 'models/haze_world/review'
sys.path.insert(0, str(REVIEW))
import issue2_forcing as probe

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()

p = probe.hom_params(.5)
p = probe.ref.DynamicParams(p.base, 'methane_only', dispersal_yr=p.dispersal_yr)
points = []
for forcing in (0., .1, -.1):
    probe.set_forcing(forcing)
    roots = [r for r in probe.ref.single_equilibria(p, 401)
             if r['kind'] == 'mixed' and r['status'] == 'accepted'
             and probe.ref.climate_slope(r['r'], p) < 0]
    assert len(roots) == 1
    r = roots[0]
    points.append(dict(F=forcing, temperature_k=r['t_k'], ratio=r['r'],
                       scaled_residual=r['residual'], state=np.asarray(r['y']).tolist(), status=r['status']))
probe.set_forcing(0.)
weighted = probe.ce.parameters('methane_only', .5, 0., 1e-4, .3)
slopes = probe.model.slopes(np.asarray(points[0]['state']), weighted)
derivative = (points[1]['temperature_k'] - points[2]['temperature_k']) / .2
blocks = probe.model.local_blocks(np.asarray(points[0]['state']), weighted)
forced, _ = probe.model.block_solve(blocks, -blocks.temperature, -blocks.emission_temperature)
linear_derivative = 1 + blocks.climate_slope * forced[-1]
assert abs(slopes['Sc']) < 1e-8 and derivative > 1e-5
assert np.isclose(derivative, linear_derivative, rtol=1e-3)

source = REVIEW / 'issue2_forcing.json'
archive = json.loads(source.read_text())
responses = [r for r in archive['states'] if r.get('dTdF_central') is not None]
maximum = max(responses, key=lambda r: r['dTdF_central'])
window_path = REVIEW / 'issue2_forcing_window.csv'
with window_path.open() as handle:
    window = list(csv.DictReader(handle))
window_summary = []
for fraction in (0., .5):
    rows = [r for r in window if float(r['f']) == fraction]
    reference = next(float(r['tau_c_yr']) for r in rows if float(r['F']) == 0)
    central = [r for r in rows if float(r['F']) <= 6]
    window_summary.append(dict(f=fraction, reference_tau_yr=reference,
        largest_relative_change_sampled_F_le_6=max(abs(float(r['tau_c_yr']) / reference - 1) for r in central),
        largest_tau_yr=max(float(r['tau_c_yr']) for r in rows),
        largest_tau_relative_to_reference=max(float(r['tau_c_yr']) for r in rows) / reference))
case_c = [r for c in archive['cases'] if c['case'] == 'C' for r in c['rows']
          if r['status'] == 'accepted' and r['domain'] == 'arney' and r['climate_slope'] < 0]
inputs = [source, window_path, Path(probe.__file__), Path(probe.ref.__file__), Path(probe.model.__file__)]
out = dict(methane_feedback_counterexample=dict(f=.5, nominal_potential=.3,
    supply_sensitivity_k_per_efold=slopes['Sc'], imposed_warming_derivative=derivative,
    imposed_warming_derivative_linear=float(linear_derivative),
    warning='Pinned against supply does not imply pinned against imposed warming under direct methane-product feedback.',
    points=points),
    largest_archived_forcing_response=dict(label=maximum['label'], response=maximum['dTdF_central']),
    fixed_product_window_samples=window_summary,
    case_C_cooling_tau_range=[min(r['tau_c_yr'] for r in case_c), max(r['tau_c_yr'] for r in case_c)],
    source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs})
args.output.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(args.output)
