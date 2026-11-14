"""Issue 2: response of the guild-regulated temperature to imposed warming F (a rigid shift of the climate curve).

F enters only through the climate curve: T_clim(r) -> T_clim(r) + F, implemented by replacing
methane_budget.temperature_k (and every module-level alias of it) with a wrapper that adds F.
Tests dT/dF = |S|/(k E) with E = 1 (dT/dF = |S|/k) on exact, spread, strong-exchange, off-reference
and acetate-feedback (D1) states; maps the F window of the exact mixed state; repeats the exact state
for Arney cases A, C, D at F = 0.
"""

import csv
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ.setdefault(_v, '1')

import numpy as np
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from terra_prisca.haze_world import continuum_core as model
from terra_prisca.haze_world import continuum_experiments as ce
from terra_prisca.haze_world import dynamic_core as ref
from terra_prisca.haze_world import graded_acetate as ga
from terra_prisca.haze_world import graded_dials as gd
from terra_prisca.haze_world import methane_budget as mb
from terra_prisca.haze_world import population_coupling as core
import issue1_spread_response as i1

STEM = HERE / 'issue2_forcing'
FORCING = [0.]
ORIGINAL = mb.temperature_k


def shifted(r, p, extend=True):
    return ORIGINAL(r, p, extend) + FORCING[0]


PATCHED = []
for _name, _mod in sorted(sys.modules.items()):
    if _name.startswith('terra_prisca') and _mod is not None and getattr(_mod, 'temperature_k', None) is ORIGINAL:
        setattr(_mod, 'temperature_k', shifted)
        PATCHED.append(_name)


def set_forcing(F):
    FORCING[0] = float(F)
    ref.single_equilibria.cache_clear()
    ref._jacobian_blocks_cached.cache_clear()


STATE_FORCINGS = (-3., -1., 0., 1., 3.)
H = .1
KAPPA_D1 = .14401879292147662
D_HOM = 1e-4


def climate_k(y, p):
    r = float(y[-1])
    slope = ref.climate_slope(r, p)
    return abs(slope) * r, slope


def relation(S, k, T):
    dT = (T[+H] - T[-H]) / (2 * H)
    ratio = dT * k / abs(S) if abs(S) > 1e-12 else None
    E = -S / (k * dT) if abs(dT) > 1e-6 and k > 0 else None
    d1 = (T[1.] - T[-1.]) / 2 if (1. in T and -1. in T) else None
    return dict(dTdF_central=dT, abs_S_over_k=abs(S) / k if k > 0 else None, ratio_dTdF_k_over_absS=ratio, E=E,
                dTdF_central_pm1K=d1)


def tau_summary(lag):
    return dict(status=lag['status'], tau_c_yr=lag['tau_c'])


# ---------------------------------------------------------------- spread states (c, d, e)

def solve_state(sigma, P, F):
    """Spread state from scratch (homogeneous seed, spread homotopy, logit mesh, panel doubling) at forcing F."""
    set_forcing(F)
    p = i1.params_at(sigma, P)
    if sigma == 0:
        y = model.homogeneous_seeds(p)[0]['y']
        return dict(y=y, p=p, m=i1.cheap_measure(y, p), doublings=0), 'qualified'
    res = model.adaptive_equilibrium(p, max_levels=32)
    if res.get('status') != 'logit_resolved':
        return None, res.get('status')
    return i1.accept(res['y'], res['p'])


def spread_job(args):
    label, sigma, f, d, P = args
    t0 = time.time()
    i1.F, i1.D = f, d
    T, states, failed = {}, {}, {}
    st0 = None
    for F in (0., H, -H, 1., -1., 3., -3.):
        st, why = solve_state(sigma, P, F)
        if st is None:
            failed[f'{F:g}'] = why
            continue
        m = st['m']
        T[F] = m['T']
        states[f'{F:g}'] = dict(T_K=m['T'], r=m['r'], S=m['Sc'], S0=m['S0'], nodes=m['nodes'], doublings=st['doublings'])
        if F == 0.:
            st0 = st
    set_forcing(0.)
    if st0 is None:
        return dict(label=label, status='reference_unresolved', failed=failed)
    m0 = st0['m']
    k, slope = climate_k(st0['y'], st0['p'])
    out = dict(label=label, status='ok', sigma_K=sigma, f=f, d_per_yr=d, P=P, S=m0['Sc'], S0=m0['S0'], k=k,
               climate_slope=slope, T0=m0['T'], r0=m0['r'], nodes=m0['nodes'],
               T_of_F={f'{F:g}': T[F] for F in sorted(T)}, states=dict(sorted(states.items(), key=lambda kv: float(kv[0]))),
               failed=failed, seconds=time.time() - t0)
    if all(x in T for x in (H, -H)):
        out.update(relation(m0['Sc'], k, T))
    return out


# ---------------------------------------------------------------- homogeneous exact states

def hom_params(f, P=.3, case='B'):
    p = ce.parameters('fixed', f, 0., D_HOM, P)
    if case != 'B':
        p = replace(p, base=replace(p.base, climate=replace(p.base.climate, case=case)))
    return p


def dyn_params(pw):
    return ref.DynamicParams(pw.base, pw.chemistry, dispersal_yr=pw.dispersal_yr)


def mixed_candidates(f, F, P=.3, case='B'):
    set_forcing(F)
    pw = hom_params(f, P, case)
    q = dyn_params(pw)
    recs = [r for r in ref.single_equilibria(q, 401) if r['kind'] == 'mixed']
    return pw, q, recs


def cooling(recs, q):
    return [r for r in recs if r['status'] == 'accepted' and ref.climate_slope(r['r'], q) < 0]


def describe(pw, q, rec, lag=True):
    y = np.asarray(rec['y'])
    k, slope = climate_k(y, pw)
    sl = model.slopes(y, pw)
    spec = ce.spectrum(y, pw)
    row = dict(T_K=rec['t_k'], r=float(rec['r']), domain=rec['climate_domain'], climate_slope=slope, k=k,
               S=sl.get('Sc'), S0=sl.get('S0'), leading_real_yr=spec['leading_real'], leading_imag_yr=spec['leading_imag'],
               stable=bool(spec['leading_real'] < 0), xa=float(y[1]), xm=float(y[2]), acetate=float(y[3]), pressure_pa=float(y[0]))
    if lag:
        lg = ce.lag_check(y, pw)
        row.update(tau_c_status=lg['status'], tau_c_yr=lg['tau_c'])
    return row


def diagnose(f, F, P=.3):
    """All roots of T_clim(r) + F = T* and why each is or is not a mixed state."""
    Tstar = exists(f, 0., .195)['t_k']
    pw, q, recs = mixed_candidates(f, F, P)
    grid = ref.ratio_grid(q, 2001)
    g = np.array([ref.temperature(r, q) - Tstar for r in grid])
    rows = []
    for a, b, ga_, gb in zip(grid[:-1], grid[1:], g[:-1], g[1:]):
        if ga_ * gb < 0:
            r = brentq(lambda x: ref.temperature(x, q) - Tstar, a, b, xtol=1e-14)
            y = ref._single_mixture(r, q)
            rows.append(dict(r=float(r), domain=str(core.domain(r, q.base.climate)), climate_slope=ref.climate_slope(r, q),
                             mixture_found=y is not None, xa=None if y is None else float(y[1]), xm=None if y is None else float(y[2]),
                             mixed_state_accepted=any(abs(x['r'] - r) < 1e-9 and x['status'] == 'accepted' for x in recs)))
    return dict(F=F, curve_min_minus_Tstar=float(g.min()), curve_max_minus_Tstar=float(g.max()), roots=rows)


def exists(f, F, r_prev, P=.3, case='B'):
    pw, q, recs = mixed_candidates(f, F, P, case)
    c = cooling(recs, q)
    if not c:
        return None
    return min(c, key=lambda x: abs(x['r'] - r_prev))


def find_end(f, F_in, F_out, r_in):
    lo, hi, r = F_in, F_out, r_in
    while abs(hi - lo) > 2e-4:
        mid = (lo + hi) / 2
        rec = exists(f, mid, r)
        if rec is None:
            hi = mid
        else:
            lo, r = mid, rec['r']
    return lo, hi


def window_job(f):
    t0 = time.time()
    rows, ends = [], {}
    rec0 = exists(f, 0., 0.195)
    pw, q, _ = mixed_candidates(f, 0.)
    r_start = rec0['r']
    for direction in (1, -1):
        F, r, last = 0., r_start, None
        path = []
        while True:
            rec = exists(f, F, r)
            if rec is None:
                break
            r = rec['r']
            last = F
            path.append(F)
            F += direction * 1.
            if abs(F) > 30:
                break
        lo, hi = find_end(f, last, last + direction, r)
        pts = sorted(set(path + [lo, lo - direction * .01, lo - direction * .1]), reverse=(direction < 0))
        pts = [x for x in pts if x * direction >= 0 or x == 0.]
        end_inside = exists(f, lo, r)
        ends['up' if direction > 0 else 'down'] = dict(
            F_last_exists=lo, F_first_missing=hi, T_K=end_inside['t_k'], r=end_inside['r'], domain=end_inside['climate_domain'],
            climate_slope=ref.climate_slope(end_inside['r'], q), diagnosis_beyond=diagnose(f, hi),
            state_at_end=None)
        for x in pts:
            rec = exists(f, x, r_start)
            if rec is None:
                continue
            pwx = pw
            row = describe(pwx, q, rec)
            row.update(f=f, F=x, branch='up' if direction > 0 else 'down')
            rows.append(row)
        ends['up' if direction > 0 else 'down']['state_at_end'] = next(r_ for r_ in rows if r_['F'] == lo and r_['branch'] == ('up' if direction > 0 else 'down'))
    rows = sorted({round(r_['F'], 9): r_ for r_ in rows}.values(), key=lambda r_: r_['F'])
    set_forcing(0.)
    return dict(f=f, rows=rows, ends=ends, seconds=time.time() - t0)


def exact_job(f):
    """Exact homogeneous state: S, k and T(F) at the requested forcings (T pinned at T*)."""
    t0 = time.time()
    rec0 = exists(f, 0., 0.195)
    pw, q, _ = mixed_candidates(f, 0.)
    base = describe(pw, q, rec0)
    T = {}
    for F in sorted(set(STATE_FORCINGS) | {H, -H}):
        rec = exists(f, F, rec0['r'])
        T[F] = None if rec is None else rec['t_k']
    set_forcing(0.)
    out = dict(label=f'a_exact_f{f:g}', status='ok', f=f, sigma_K=0., S=base['S'], k=base['k'], climate_slope=base['climate_slope'],
               T0=base['T_K'], r0=base['r'], tau_c_status=base['tau_c_status'], tau_c_yr=base['tau_c_yr'],
               T_of_F={f'{F:g}': v for F, v in T.items()}, seconds=time.time() - t0)
    out.update(dTdF_central=(T[H] - T[-H]) / (2 * H), abs_S_over_k=abs(base['S']) / base['k'],
               max_abs_T_minus_T0=max(abs(v - base['T_K']) for v in T.values()))
    return out


# ---------------------------------------------------------------- D1 (acetate feedback)

def d1_job(_):
    t0 = time.time()
    set_forcing(0.)
    rec = gd.d1_point(KAPPA_D1, 0.)
    if rec['status'] != 'accepted':
        return dict(label='b_D1_f0', status=rec['status'])
    p = ga.parameters(KAPPA_D1, 0.)
    y0 = np.asarray(rec['y'])
    k, slope = climate_k(y0, p)
    T, states, failed = {0.: rec['temperature_k']}, {}, {}

    def solve(seed, F, F_from, depth=0):
        set_forcing(F)
        found = ga.equilibrium(seed, p)
        if found is not None:
            return found
        if depth > 6 or abs(F - F_from) < 1e-3:
            return None
        mid = (F + F_from) / 2
        a = solve(seed, mid, F_from, depth + 1)
        return None if a is None else solve(a['y'], F, mid, depth + 1)

    def at(found, F):
        yy = np.asarray(found['y'])
        sl = ga.slopes(yy, p)
        lg = ce.lag_check(yy, p, blocks=ga.blocks(yy, p))
        states[f'{F:g}'] = dict(T_K=found['t_k'], r=float(yy[-1]), S=sl['Sc'], tau_c=lg['tau_c'], tau_status=lg['status'],
                               k=climate_k(yy, p)[0], stable_leading_real=ce.spectrum(yy, p, blocks=ga.blocks(yy, p))['leading_real'])

    at(dict(y=y0, t_k=rec['temperature_k']), 0.)
    for chain in ((.1,), (1., 2., 3.), (-.1,), (-1., -2., -3.)):
        cur, F_prev = y0, 0.
        for F in chain:
            found = solve(cur, F, F_prev)
            if found is None:
                failed[f'{F:g}'] = 'unresolved'
                break
            T[F] = found['t_k']
            at(found, F)
            if len(chain) > 1:
                cur, F_prev = found['y'], F
    set_forcing(0.)
    supply = gd.raw_supply_check(y0, p, 'D1', rec['Sc'])
    out = dict(label='b_D1_f0', status='ok', kappa=KAPPA_D1, f=0., sigma_K=0., S=rec['Sc'], S0=rec['S0'], k=k, climate_slope=slope,
               T0=rec['temperature_k'], r0=float(y0[-1]), tau_c_status=rec['lag']['status'], tau_c_yr=rec['lag']['tau_c'],
               supply_fd_check=supply, T_of_F={f'{F:g}': T[F] for F in sorted(T)}, states=states, failed=failed,
               seconds=time.time() - t0)
    if all(x in T for x in (H, -H)):
        out.update(relation(rec['Sc'], k, T))
    return out


# ---------------------------------------------------------------- cross-case

CASE_P = np.round(np.geomspace(.05, 2.0, 121), 5)


def case_job(case):
    t0 = time.time()
    set_forcing(0.)
    rows = []
    for P in CASE_P:
        pw = hom_params(.5, float(P), case)
        q = dyn_params(pw)
        recs = [r for r in ref.single_equilibria(q, 401) if r['kind'] == 'mixed']
        for rec in recs:
            row = dict(case=case, P=float(P), status=rec['status'], T_K=rec['t_k'], r=float(rec['r']), domain=rec['climate_domain'],
                       climate_slope=ref.climate_slope(rec['r'], q), k=abs(ref.climate_slope(rec['r'], q)) * rec['r'])
            if rec['status'] == 'accepted':
                row.update(describe(pw, q, rec, lag=True))
            rows.append(row)
    resp = mb.response(case)
    curve = dict(vertices_r=[float(x) for x in resp.ratios], vertices_T=[float(x) for x in resp.temperatures_k],
                 max_T=float(max(resp.temperatures_k)), min_T=float(min(resp.temperatures_k)))
    p = hom_params(.5, .3, case)
    zero_ratio = float(ORIGINAL(0., p.base.climate))
    return dict(case=case, rows=rows, curve=curve, T_at_r0_bridge=zero_ratio, seconds=time.time() - t0)


# ---------------------------------------------------------------- checks

def injection_check():
    p = hom_params(.5)
    q = dyn_params(p)
    clim = p.base.climate
    rs = [0., .05, .0999, .1, .1667, .195, .2, .2222, .2333, .3, .5]
    out = dict(patched_modules=PATCHED)
    unpatched = [n for n, m in sys.modules.items() if n.startswith('terra_prisca') and m is not None
                 and any(v is ORIGINAL for v in vars(m).values())]
    out['modules_still_holding_original'] = unpatched
    res = []
    for F in (0., 2.5, -4.):
        set_forcing(F)
        diffs = [ref.temperature(r, q) - float(ORIGINAL(r, clim)) - F for r in rs]
        pc = [float(core.temperature_k(r, clim)) - float(ORIGINAL(r, clim)) - F for r in rs]
        slope_fd = [(ref.temperature(r + 1e-6, q) - ref.temperature(max(r - 1e-6, 0.), q)) / (r + 1e-6 - max(r - 1e-6, 0.)) for r in (.12, .18, .21)]
        slope_ref = [ref.climate_slope(r, q) for r in (.12, .18, .21)]
        res.append(dict(F=F, max_abs_dev_dynamic_core=float(np.max(np.abs(diffs))), max_abs_dev_population_coupling=float(np.max(np.abs(pc))),
                        slope_fd=slope_fd, slope_reference=slope_ref))
    set_forcing(0.)
    out['shift_checks'] = res
    return out


def reproduction_check(results):
    arch = json.loads((HERE / 'issue1_spread_response.json').read_text())
    rows = arch['rows']
    taus = arch['tau_c']
    out = []
    for r in results:
        if r.get('status') != 'ok' or r['label'][0] in 'abd':
            continue
        row = next((x for x in rows if x['sigma_K'] == r['sigma_K'] and abs(x['P'] - r['P']) < 1e-9 and x['direction'] != 'hom'), None)
        if row is None:
            continue
        out.append(dict(label=r['label'], T_now=r['T0'], T_archive=row['T_K'], S_now=r['S'], S_archive=row['S_K_per_efold'],
                        S0_now=r['S0'], S0_archive=row['S0']))
    ref_hom = next(x for x in rows if x['sigma_K'] == 0 and x['direction'] == 'ref')
    out.append(dict(label='sigma0_f0.5_P0.30', T_archive=ref_hom['T_K'], r_archive=ref_hom['r'], S_archive=ref_hom['S_K_per_efold']))
    return out


def clean(x):
    return ce.clean(x)


def main(only=None):
    t0 = time.time()
    set_forcing(0.)
    rec = exists(.5, 0., .195)
    TSTAR = rec['t_k']
    inj = injection_check()
    spread = [('c_sigma1', 1., .5, 1e-4, .30), ('c_sigma3', 3., .5, 1e-4, .30), ('d_strong_exchange', 3., .5, 1e-1, .30),
              ('e_P0.24', 3., .5, 1e-4, .24), ('e_P0.42', 3., .5, 1e-4, .42)]
    with ProcessPoolExecutor(max_workers=9) as pool:
        fut_spread = [pool.submit(spread_job, a) for a in spread]
        fut_d1 = pool.submit(d1_job, None)
        fut_win = [pool.submit(window_job, f) for f in (0., .5)]
        fut_case = [pool.submit(case_job, c) for c in ('A', 'B', 'C', 'D')]
        fut_exact = [pool.submit(exact_job, f) for f in (0., .5)]
        exact = [x.result() for x in fut_exact]
        d1 = fut_d1.result()
        spreads = [x.result() for x in fut_spread]
        windows = [x.result() for x in fut_win]
        cases = [x.result() for x in fut_case]
    states = exact + [d1] + spreads
    out = dict(meta=dict(T_star_K=TSTAR, forcing_definition='T_clim(r) -> T_clim(r) + F, rigid shift; F=0 leaves everything unchanged',
                         central_difference_step_K=H, seconds=time.time() - t0, case_P_grid=[float(x) for x in CASE_P]),
               injection=inj, reproduction=reproduction_check(states), states=states,
               window={f"f{w['f']:g}": dict(ends=w['ends'], seconds=w['seconds']) for w in windows},
               cases=cases)
    STEM.with_suffix('.json').write_text(json.dumps(clean(out), indent=1, allow_nan=False) + '\n')
    cols = ['f', 'F', 'branch', 'T_K', 'r', 'domain', 'climate_slope', 'k', 'S', 'S0', 'leading_real_yr', 'leading_imag_yr', 'stable',
            'tau_c_status', 'tau_c_yr', 'xa', 'xm', 'acetate', 'pressure_pa']
    with STEM.with_name('issue2_forcing_window.csv').open('w', newline='') as h:
        w = csv.DictWriter(h, cols, extrasaction='ignore')
        w.writeheader()
        for win in windows:
            for row in win['rows']:
                w.writerow(clean(row))
    print(json.dumps(clean(dict(states=states, ends={f"f{w['f']:g}": w['ends'] for w in windows})), indent=1)[:20000])
    print('total seconds', round(time.time() - t0))


if __name__ == '__main__':
    main()
