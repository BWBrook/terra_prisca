"""Bounded independent clamped-temperature derivatives for Issue 2."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'models/haze_world/review'))
import issue2_forcing as f


def checked(label, y, p, b, archived):
    forcing = np.zeros((p.n, 4))
    forcing[:, 0] = f.model.YEAR / f.core.HENRY_30C_MOL_L_PA * f.core.supply_h2(p.base)
    supply, condition = f.model.block_solve(b, -forcing, 0., climate=False)
    thermal, _ = f.model.block_solve(b, -b.temperature, -b.emission_temperature, climate=False)
    forced, _ = f.model.block_solve(b, -b.temperature, -b.emission_temperature)
    closed_supply, _ = f.model.block_solve(b, -forcing, 0.)
    k = -b.climate_slope * y[-1]
    E_total = supply[-1] / y[-1]
    G_total = thermal[-1] / y[-1]
    H = 1. / (1. + k * G_total)
    S = b.climate_slope * closed_supply[-1]
    D = 1. + b.climate_slope * forced[-1]
    assert E_total > 0
    assert np.isclose(D, H, rtol=1e-8, atol=1e-10)
    assert np.isclose(S / (-k * E_total), H, rtol=1e-8, atol=1e-10)
    assert np.isclose(D, archived['dTdF_central'], rtol=1e-5, atol=1e-9)
    abiotic = f.core.atmosphere(p.base.climate.case)['flux_to_ratio_per_yr'] * p.base.climate.abiotic_flux
    fraction = abiotic / p.base.loss.rate(y[-1])
    return dict(label=label, nodes=p.n, E_total_fixed_actual_T=float(E_total),
                E_biological_fixed_actual_T=float(E_total / (1. - fraction)),
                abiotic_source_fraction=float(fraction), G_total_per_K=float(G_total),
                fixed_T_schur_condition=condition,
                methane_loss_elasticity=float(p.base.loss.slope(y[-1]) * y[-1] / p.base.loss.rate(y[-1])),
                methane_product_feedback=p.methane_feedback,
                S_closed=float(S), supply_open_loop_S=float(-k * E_total),
                normalized_supply_response=float(S / (-k * E_total)),
                forcing_closed_response=float(D), normalized_response_H=float(H),
                dTdF_from_independent_E=float(abs(S) / (k * E_total)),
                archive_inferred_E=archived['E'], archive_dTdF=archived['dTdF_central'])


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
start = time.time()
arch = json.loads((ROOT / 'models/haze_world/review/issue2_forcing.json').read_text())
states = {r['label']: r for r in arch['states']}
f.set_forcing(0.)
d1 = f.gd.d1_point(f.KAPPA_D1, 0.)
if d1['status'] != 'accepted':
    raise RuntimeError(d1['status'])
p = f.ga.parameters(f.KAPPA_D1, 0.)
y = np.asarray(d1['y'])
rows = [checked('b_D1_f0', y, p, f.ga.blocks(y, p), states['b_D1_f0'])]
Ts = []
for F in (-.03, .03):
    f.set_forcing(F)
    found = f.ga.equilibrium(y, p)
    if found is None:
        raise RuntimeError('D1 independent .03-K forcing root unresolved')
    Ts.append(found['t_k'])
rows[0]['dTdF_finite_difference_step_0p03K'] = (Ts[1] - Ts[0]) / .06
f.set_forcing(0.)
spread, why = f.solve_state(1., .3, 0.)
if spread is None:
    raise RuntimeError(why)
y, p = spread['y'], spread['p']
rows.append(checked('c_sigma1', y, p, f.model.local_blocks(y, p), states['c_sigma1']))
rec = f.exists(.5, 0., .195)
p = f.hom_params(.5)
q = f.dyn_params(p)
Tstar = rec['t_k']
y = np.asarray(rec['y'])
b = f.model.local_blocks(y, p)
J = f.model.dense_matrix(y, p, blocks=b)
J0 = J - np.outer(np.r_[b.temperature.ravel(), b.emission_temperature],
                  np.r_[np.zeros(4), b.climate_slope])
scale = f.ref.state_scales(y, p)
exact = dict(fixed_T_scaled_singular_values=np.linalg.svd(J0 * scale[None, :] / scale[:, None], compute_uv=False).tolist(),
             warning='M(P,T) is not single-valued at exact fixed-product coexistence: guild allocation adjusts methane at fixed P and T. Do not apply the regular M(P,T) derivative closure here.',
             example_states=[])
for r in (.19, .20):
    F = Tstar - f.ORIGINAL(r, p.base.climate)
    f.set_forcing(F)
    yy = f.ref._single_mixture(r, q)
    exact['example_states'].append(dict(P=.3, T=f.ref.temperature(r, q), r=r, F=F,
        total_methane_source_ratio_per_yr=float(p.base.loss.rate(r)),
        residual=float(np.max(abs(f.ref.physical_rhs(yy, q) / f.ref.state_scales(yy, q)))),
        state=yy.tolist()))
f.set_forcing(0.)
paths = [Path(f.__file__), Path(f.model.__file__), Path(f.ref.__file__), Path(f.ga.__file__),
         Path(f.gd.__file__), Path(f.ce.__file__), Path(f.mb.__file__), Path(f.core.__file__)]
out = dict(git_head=subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
           source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
           definition='A is the physical Jacobian at clamped actual temperature; v_P=-A^-1 f_lnP and v_T=-A^-1 f_T. For linear methane removal and no methane product feedback, E_total=v_P[r]/r and G_total=v_T[r]/r are derivatives of TOTAL methane source, including abiotic input. E_biological=E_total/(1-abiotic source fraction).',
           normalization='Supply S divided by its clamped-temperature open-loop -k E_total equals H=1/(1+k G_total), the same dimensionless response as dT/dF. This is not G_loc=Sc/S0 from the frozen-composition control.',
           states=rows, exact_state=exact, injection=f.injection_check(), seconds=time.time()-start)
destination = args.output
destination.write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
print(destination)
print(json.dumps(dict(states=rows, seconds=out['seconds']), indent=2))
