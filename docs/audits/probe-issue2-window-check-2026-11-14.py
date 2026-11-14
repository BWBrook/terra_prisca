"""Bounded Issue 2 roots and corner spectra; no integrations or grids."""
import argparse
import os
import sys
import time
import json
import hashlib
from pathlib import Path

for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
os.environ.setdefault('MPLCONFIGDIR', '/tmp/terra-prisca-mpl')

import numpy as np
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'models/haze_world/review'))
import issue2_forcing as probe

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
started = time.process_time()
ref = probe.ref
q0 = probe.dyn_params(probe.hom_params(.5))

def equality(t):
    a, m = ref.guilds(t - 273.15, q0.base.biology)
    return a.rstar(q0.base.biology.loss_h) - m.rstar(q0.base.biology.loss_h)

tstar = float(brentq(equality, 281., 282., xtol=1e-12))

def checks(y, q):
    record = ref._record(y, q, 'mixed')
    assert record['status'] == 'accepted' and record['physiology_status'] == 'in_domain'
    assert record['residual'] < 1e-6 and min(y[1:3]) > 0
    return dict(
        status=record['status'],
        physiology_status=record['physiology_status'],
        climate_domain=record['climate_domain'],
        rhs=ref.physical_rhs(y, q).tolist(),
        maximum_scaled_rhs=record['residual'],
        per_capita_residual_yr=ref.biomass_per_capita(y, q).tolist(),
        min_guild_biomass=float(min(y[1:3])),
        temperature_k=record['t_k'],
        temperature_minus_switch_k=record['t_k'] - tstar,
    )

probe.set_forcing(0.)
p = probe.hom_params(.5, .3, 'D')
q = probe.dyn_params(p)
curve = probe.mb.response('D')
ratio = float(brentq(lambda r: probe.ORIGINAL(r, p.base.climate) - tstar,
                     0., float(curve.ratios[0]), xtol=1e-15))
at_zero = ref._single_mixture(ratio, probe.dyn_params(probe.hom_params(.5, 0., 'D')))
at_one = ref._single_mixture(ratio, probe.dyn_params(probe.hom_params(.5, 1., 'D')))
derivative = at_one - at_zero
edges = [float(-at_zero[j] / derivative[j]) for j in (1, 2)]
potential = sum(edges) / 2
p = probe.hom_params(.5, potential, 'D')
q = probe.dyn_params(p)
y = ref._single_mixture(ratio, q)
out = dict(
    scope='Selected exact roots and 5x5 linear algebra only; no integration or sweep',
    T_star_K=tstar,
    Rstar_difference_pa=equality(tstar),
    D_bridge=dict(
        f=.5, P=potential, ratio=ratio,
        P_positive_mixture_interval=sorted(edges),
        y=y.tolist(), checks=checks(y, q),
        spectrum=probe.ce.spectrum(y, p),
    ),
    B_corners=[],
)
for fraction in (0., .5):
    p = probe.hom_params(fraction)
    q = probe.dyn_params(p)
    curve = probe.mb.response('B')
    for end, index in (('cold', 2), ('warm', 7)):
        ratio = float(curve.ratios[index])
        forcing = tstar - float(curve.temperatures_k[index])
        probe.set_forcing(forcing)
        y = ref._single_mixture(ratio, q)
        sides = {}
        for label, side in (('left', -1), ('right', 1)):
            matrix = ref.reduced_matrix(y, q, side=side)
            vals, vecs = np.linalg.eig(matrix)
            leading_index = int(np.argmax(vals.real))
            value = vals[leading_index]
            sides[label] = dict(
                climate_slope=ref.climate_slope(ratio, q, side=side),
                leading_real_yr=float(value.real),
                leading_abs_imag_yr=float(abs(value.imag)),
                ratio_eigenvector_component_abs=float(abs(vecs[-1, leading_index])),
            )
        out['B_corners'].append(dict(
            f=fraction, end=end, F=forcing, ratio=ratio,
            y=y.tolist(), checks=checks(y, q), one_sided_spectra=sides,
        ))
probe.set_forcing(0.)
files = [
    'models/haze_world/review/issue2_forcing.py',
    'src/terra_prisca/haze_world/dynamic_core.py',
    'src/terra_prisca/haze_world/continuum_core.py',
    'src/terra_prisca/haze_world/continuum_experiments.py',
    'src/terra_prisca/haze_world/methane_budget.py',
    'models/haze_response/arney2016/figure4.csv',
    'models/haze_response/arney2016/cases.csv',
]
out['source_sha256'] = {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in files}
out['process_cpu_seconds_after_import'] = time.process_time() - started
destination = args.output
destination.write_text(json.dumps(out, indent=2) + '\n')
print(destination)
print(json.dumps(out, indent=2))
