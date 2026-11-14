"""Issue 1: finite steady temperature response T*(P) to supply under habitat spread.

Continues the f=0.5, fixed-products, ell=0.001 /h, d=1e-4 /yr spread state in the
supply potential P outward from P=0.30, with the archived adaptive-quadrature
and doubling acceptance. Compares each curve with the weak-mixing reduced model
(flux balance r = kappa P g(phi_M), T = T_clim(r), phi_M = (T+sigma-T*)/(2 sigma)).
"""

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

from terra_prisca.haze_world import continuum_core as model
from terra_prisca.haze_world import continuum_experiments as ce
from terra_prisca.haze_world import dynamic_core as ref
from terra_prisca.haze_world import dynamic_realisation as b1
from terra_prisca.haze_world import population_coupling as core

HERE = Path(__file__).resolve().parent
STEM = HERE / 'issue1_spread_response'
F, D = .5, 1e-4
P_REF, P_LO_HOM, P_HI_HOM = .30, .229178, .457327
SIGMAS = (0., 1., 3., 6., 8.)
TAU_SIGMAS = (1., 3., 6., 8.)
TAU_P = (.24, .30, .36, .42)
P_MIN, P_MAX, STEP = .20, .55, .01
ETA_A, ETA_M = .894871, .941322
MIN_GAP = 1e-4


def params_at(sigma, P, mesh=None):
    return ce.parameters('fixed', F, sigma, D, P, mesh)


def cheap_measure(y, p):
    g = ce.gain_check(y, p)
    return dict(T=ref.temperature(y[-1], p), r=float(y[-1]), Sc=g.get('Sc'), S0=g.get('S0'),
                G_loc=g.get('G_loc'), fd_ok=g.get('frozen_fd_agrees', False), nodes=p.n)


def agree(a, b):
    return (abs(a['T']-b['T']) < 1e-5 and ce.slopes_agree(a, b))


def accept(y, p, measure=cheap_measure, same=agree, max_iter=7):
    """Logit-resolve, then double mixed panels until slopes (and T) agree."""
    res = model.adaptive_equilibrium(p, seed=y, max_levels=32, max_nodes=4096)
    if res.get('status') != 'logit_resolved':
        return None, res.get('status')
    p, y = res['p'], res['y']
    prev = measure(y, p)
    for it in range(max_iter):
        mesh, _ = model.refine_panels(y, p, force_mixed=True)
        if len(mesh.nodes) == p.n:
            e = np.asarray(p.mesh.panels)
            mesh = model.gauss_mesh(p.sigma_k, np.sort(np.r_[e, (e[:-1]+e[1:])/2]))
        if len(mesh.nodes) > 4096:
            return None, 'node_limit'
        q = replace(p, mesh=mesh)
        found = model.equilibrium(model.interpolate_state(y, p, q), q)
        if found is None:
            return None, 'doubling_root_unresolved'
        _, chk = model.refine_panels(found['y'], q)
        if chk['status'] != 'logit_resolved':
            found = model.adaptive_equilibrium(q, seed=found['y'], max_levels=32, max_nodes=4096)
            if found.get('status') != 'logit_resolved':
                return None, found.get('status')
            q = found['p']
        cur = measure(found['y'], q)
        ok = same(prev, cur) and cur.get('fd_ok', True)
        p, y, prev = q, found['y'], cur
        if ok:
            return dict(y=y, p=p, m=cur, doublings=it+1), 'qualified'
    return None, 'doubling_unresolved'


def record(sigma, P, st, direction, status='accepted'):
    m, p = st['m'], st['p']
    ts = ref.temperature_status(st['y'], p)
    x = st['y'][:-1].reshape(p.n, 4)
    mean = p.weights @ x[:, 1:3]
    return dict(sigma_K=sigma, P=P, direction=direction, status=status, T_K=m['T'], r=m['r'],
                mean_acetogen=float(mean[0]), mean_methanogen=float(mean[1]),
                S_K_per_efold=m['Sc'], S0=m['S0'], G_loc=m['G_loc'], nodes=m['nodes'],
                doublings=st['doublings'], support_min_K=ts['support_min_k'],
                support_max_K=ts['support_max_k'])


def predictors(st, q, notes):
    """Tangent in r, previous biomass profile re-solved node by node (local manifold), on a fresh mesh."""
    p, y = st['p'], st['y']
    b = model.local_blocks(y, p)
    forcing = np.zeros((p.n, 4))
    forcing[:, 0] = model.YEAR/core.HENRY_30C_MOL_L_PA*core.supply_h2(p.base)
    dv, _ = model.block_solve(b, -forcing, 0.)
    r = y[-1]+dv[-1]*np.log(q.base.climate.donor_flux/p.base.climate.donor_flux)
    means = p.weights @ y[:-1].reshape(p.n, 4)[:, 1:3]
    for panels in (8, 12, 16, 6, 24, 4):
        mesh = model.gauss_mesh(q.sigma_k, np.linspace(-q.sigma_k, q.sigma_k, panels+1))
        qc = replace(q, mesh=mesh)
        seed = model.interpolate_state(y, p, qc)
        seed[-1] = max(r, 1e-6)
        try:
            seed = model.local_profile_correction(seed, qc, means)
        except ValueError:
            notes.append('domain_censored: predicted habitat temperature outside 273-303.15 K')
            return
        if seed is None:
            continue
        found = model.equilibrium(seed, qc)
        if found is not None:
            yield found['y'], qc


def advance(sigma, st, P, direction, out, depth=0):
    """Move the accepted state st to supply P, bisecting the P step on failure."""
    prev_P = st['P']
    q = params_at(sigma, P)
    new, why, notes = None, 'predictor_unresolved', []
    for y0, qc in predictors(st, q, notes):
        new, why = accept(y0, qc)
        if new is not None:
            break
    if new is not None:
        new['P'] = P
        out.append(record(sigma, P, new, direction))
        return new, None
    if notes and why == 'predictor_unresolved':
        why = notes[0]
    if abs(P-prev_P) <= MIN_GAP:
        return None, why
    mid = (P+prev_P)/2
    st2, why2 = advance(sigma, st, mid, direction, out, depth+1)
    if st2 is None:
        return None, why2
    return advance(sigma, st2, P, direction, out, depth+1)


def reference_state(sigma):
    p = params_at(sigma, P_REF)
    if sigma == 0:
        seeds = model.homogeneous_seeds(p)
        y = seeds[0]['y']
        st = dict(y=y, p=p, m=cheap_measure(y, p), doublings=0, P=P_REF)
        return st, 'qualified'
    res = model.adaptive_equilibrium(p, max_levels=32)
    if res.get('status') != 'logit_resolved':
        return None, res.get('status')
    st, why = accept(res['y'], res['p'])
    if st is not None:
        st['P'] = P_REF
    return st, why


def pack(st):
    p = st['p']
    return dict(y=[float(v) for v in st['y']], offsets=list(p.mesh.nodes), weights=list(p.mesh.weights),
                panels=list(p.mesh.panels))


def last_accepted(rows):
    acc = [r for r in rows if r['status'] == 'accepted']
    r = acc[-1]
    return dict(last_P=r['P'], last_T=r['T_K'], support_min_K=r['support_min_K'], support_max_K=r['support_max_K'])


def branch_job(args):
    sigma, direction = args
    t0 = time.time()
    st0, why = reference_state(sigma)
    if st0 is None:
        return dict(sigma=sigma, direction=direction, rows=[], end=dict(reason='reference_unresolved:'+str(why)), seconds=time.time()-t0)
    rows = []
    rows.append(record(sigma, P_REF, st0, 'ref'))
    targets = (np.arange(P_REF+STEP, P_MAX+1e-9, STEP) if direction > 0
               else np.arange(P_REF-STEP, P_MIN-1e-9, -STEP))
    st, end = st0, None
    saved = {}
    saved[P_REF] = pack(st0)
    for P in targets:
        P = round(float(P), 6)
        new, why = advance(sigma, st, P, 'up' if direction > 0 else 'down', rows)
        if new is None:
            end = dict(reason=why, failed_target=P, **last_accepted(rows))
            break
        st = new
        if P in TAU_P:
            saved[P] = pack(st)
    return dict(sigma=sigma, direction=direction, rows=rows, end=end, seconds=time.time()-t0, saved=saved)


def full_measure(y, p):
    m = ce.measure(y, p)
    return dict(T=m['temperature_k'], r=m['ratio'], Sc=m['Sc'], S0=m['S0'], G_loc=m['G_loc'], nodes=p.n,
                fd_ok=m['gain'].get('frozen_fd_agrees', False), lag=m['lag'])


def full_agree(a, b):
    return agree(a, b) and ce.lag_agrees(a['lag'], b['lag'])


def tau_job(args):
    sigma, P, y, offsets, weights, panels = args
    t0 = time.time()
    mesh = model.Mesh(tuple(offsets), tuple(weights), tuple(panels))
    p = params_at(sigma, P, mesh)
    st, why = accept(np.asarray(y), p, measure=full_measure, same=full_agree)
    if st is None:
        return dict(sigma_K=sigma, P=P, status=why, tau_c_status=None, tau_c_yr=None, seconds=time.time()-t0)
    lag = st['m']['lag']
    return dict(sigma_K=sigma, P=P, status='accepted', T_K=st['m']['T'], S_K_per_efold=st['m']['Sc'],
                nodes=st['m']['nodes'], tau_c_status=lag['status'], tau_c_yr=lag['tau_c'],
                crossings=lag.get('crossings'), seconds=time.time()-t0)


def homogeneous_curves(Ps):
    mixed, meth = [], []
    for P in Ps:
        p0 = b1.parameters('fixed', F, .001, P)
        for r in ref.single_equilibria(p0, 401):
            if r['kind'] == 'mixed':
                mixed.append((float(P), ref.temperature(r['r'], p0), float(r['r'])))
        q = replace(p0, base=replace(p0.base, enabled=(False, True)))
        for r in ref.single_equilibria(q, 401):
            if r['kind'] == 'methanogen':
                meth.append((float(P), ref.temperature(r['r'], q), float(r['r'])))
    return mixed, meth


def has_mixed(P):
    p0 = b1.parameters('fixed', F, .001, P)
    return any(r['kind'] == 'mixed' for r in ref.single_equilibria(p0, 401))


def reduced_T(sigma, P, Tstar, kappa, g, clim):
    def phi(T):
        return min(1., max(0., (T+sigma-Tstar)/(2*sigma)))
    def resid(T):
        return core.temperature_k(kappa*P*g(phi(T)), clim)-T
    T = brentq(resid, Tstar-sigma-60, Tstar+sigma+60, xtol=1e-10)
    return float(T), phi(T)


def main():
    t0 = time.time()
    jobs = [(s, d) for s in SIGMAS if s > 0 for d in (1, -1)]
    jobs.sort(key=lambda j: -j[0])
    with ProcessPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(branch_job, jobs))
    t_branch = time.time()-t0
    rows, ends, secs, saved = [], {}, {}, {}
    for r in results:
        rows += r['rows']
        key = f"sigma{r['sigma']:g}_{'up' if r['direction'] > 0 else 'down'}"
        ends[key] = r['end']
        secs[key] = r['seconds']
        for P, v in r['saved'].items():
            saved[(r['sigma'], P)] = v
        print(key, len(r['rows']), 'points', r['end'], round(r['seconds']), 's', flush=True)
    rows = sorted({(r['sigma_K'], r['P']): r for r in rows}.values(), key=lambda r: (r['sigma_K'], r['P']))

    # sigma = 0 reference and homogeneous curves
    p_ref0 = params_at(0., P_REF)
    y0 = model.homogeneous_seeds(p_ref0)[0]['y']
    ref0 = cheap_measure(y0, p_ref0)
    Tstar, rstar = ref0['T'], ref0['r']
    Pgrid = np.round(np.arange(P_MIN, P_MAX+1e-9, .005), 6)
    mixed, meth = homogeneous_curves(Pgrid)
    edges_ok = dict(P_lo_below=has_mixed(P_LO_HOM-2e-6), P_lo_above=has_mixed(P_LO_HOM+2e-6),
                    P_hi_below=has_mixed(P_HI_HOM-2e-6), P_hi_above=has_mixed(P_HI_HOM+2e-6))
    rows0 = [dict(sigma_K=0., P=P, direction='hom', status='accepted', T_K=T, r=r) for P, T, r in mixed]
    rows0.append(dict(sigma_K=0., P=P_REF, direction='ref', status='accepted', T_K=Tstar, r=rstar,
                      S_K_per_efold=ref0['Sc'], S0=ref0['S0'], G_loc=ref0['G_loc'], nodes=1))
    rows = rows0 + rows

    # reduced model
    clim = p_ref0.base.climate
    Q = P_HI_HOM/P_LO_HOM
    gg = lambda f: F*ETA_A+f*(ETA_M-F*ETA_A)
    kA = rstar/np.sqrt(P_LO_HOM*gg(1.)*P_HI_HOM*gg(0.))
    kB = rstar/P_LO_HOM
    gB = lambda f: 1.+(1./Q-1.)*(1-f)
    reds = dict(A=(kA, gg), B=(kB, gB))
    kslope = 140.7
    for r in rows:
        sg = r['sigma_K']
        if sg > 0:
            for key, (k, g) in reds.items():
                T, ph = reduced_T(sg, r['P'], Tstar, k, g, clim)
                r['T_red_'+key], r['phi_red_'+key] = T, ph
            sgeo = 2*sg*(P_LO_HOM/r['P'])*Q/(Q-1)
            r['S_hyp'] = -1/(1/kslope+1/sgeo)

    # tau_c
    tau_jobs = []
    for sg in TAU_SIGMAS:
        for P in TAU_P:
            v = saved.get((sg, P))
            if v:
                tau_jobs.append((sg, P, v['y'], v['offsets'], v['weights'], v['panels']))
    t1 = time.time()
    with ProcessPoolExecutor(max_workers=8) as pool:
        taus = list(pool.map(tau_job, sorted(tau_jobs, key=lambda j: -j[0])))
    t_tau = time.time()-t1
    taus.sort(key=lambda r: (r['sigma_K'], r['P']))
    for r in taus:
        print('tau', r['sigma_K'], r['P'], r.get('status'), r.get('tau_c_status'), r.get('tau_c_yr'), round(r['seconds']), 's', flush=True)

    # summaries
    summary = {}
    for sg in SIGMAS:
        sub = [r for r in rows if r['sigma_K'] == sg and r['direction'] != 'hom']
        if sg == 0:
            hom = [r for r in rows if r['sigma_K'] == 0 and r['direction'] == 'hom']
            summary['0'] = dict(T_min=min(r['T_K'] for r in hom), T_max=max(r['T_K'] for r in hom),
                                P_first=hom[0]['P'], P_last=hom[-1]['P'])
            continue
        P = np.array([r['P'] for r in sub]); T = np.array([r['T_K'] for r in sub])
        info = dict(P_min=float(P.min()), P_max=float(P.max()), T_at_Pmin=float(T[P.argmin()]),
                    T_at_Pmax=float(T[P.argmax()]), T_pred_lo=Tstar+sg, T_pred_hi=Tstar-sg)
        cov_lo, cov_hi = P.min() <= P_LO_HOM+1e-9, P.max() >= P_HI_HOM-1e-9
        info.update(covers_P_lo=bool(cov_lo), covers_P_hi=bool(cov_hi))
        lo, hi = max(P_LO_HOM, P.min()), min(P_HI_HOM, P.max())
        info.update(T_at_lo_edge=float(np.interp(lo, P, T)), T_at_hi_edge=float(np.interp(hi, P, T)),
                    P_lo_used=float(lo), P_hi_used=float(hi),
                    span_K=float(np.interp(lo, P, T)-np.interp(hi, P, T)), span_hypothesis_K=2*sg,
                    support_min_K_over_branch=float(min(r['support_min_K'] for r in sub)),
                    max_T_K=float(T.max()), min_T_K=float(T.min()))
        for key in ('A', 'B'):
            dev = np.array([r['T_K']-r['T_red_'+key] for r in sub])
            i = int(np.abs(dev).argmax())
            info['max_abs_dev_'+key] = float(abs(dev[i])); info['at_P_'+key] = float(P[i])
            info['rms_dev_'+key] = float(np.sqrt((dev**2).mean()))
            inside = np.array([(r['P'] >= lo-1e-9) and (r['P'] <= hi+1e-9) for r in sub])
            info['max_abs_dev_inrange_'+key] = float(np.abs(dev[inside]).max()) if inside.any() else None
            Tr_lo, _ = reduced_T(sg, P_LO_HOM, Tstar, *reds[key][:1], reds[key][1], clim)
            Tr_hi, _ = reduced_T(sg, P_HI_HOM, Tstar, *reds[key][:1], reds[key][1], clim)
            info['red_T_at_P_lo_'+key] = Tr_lo; info['red_T_at_P_hi_'+key] = Tr_hi
        Sref = next(r for r in sub if r['direction'] == 'ref')
        info['S_ref_computed'] = Sref['S_K_per_efold']; info['S_ref_hypothesis'] = Sref['S_hyp']
        sd = np.array([r['S_K_per_efold']-r['S_hyp'] for r in sub]); rel = sd/np.array([r['S_K_per_efold'] for r in sub])
        info['S_rel_dev_max'] = float(np.abs(rel).max()); info['S_rel_dev_median'] = float(np.median(np.abs(rel)))
        summary[f'{sg:g}'] = info

    meta = dict(T_star_K=Tstar, r_star=rstar, kappa_A=kA, kappa_B=kB, Q=Q, P_lo=P_LO_HOM, P_hi=P_HI_HOM,
                homogeneous_mixed_edge_check=edges_ok, branch_ends=ends, branch_seconds=secs,
                branch_wall_seconds=t_branch, tau_wall_seconds=t_tau, total_wall_seconds=time.time()-t0,
                f=F, d_per_yr=D, loss_per_h=.001, chemistry='fixed',
                acceptance='adaptive logit-resolved mesh; panel doubling until T (1e-5 K), Sc, S0 (slopes_agree) and frozen finite-difference agree; tau_c points also require lag_agrees')
    out = dict(meta=meta, summary=summary, tau_c=taus, rows=rows, methanogen_only=meth)
    STEM.with_suffix('.json').write_text(json.dumps(ce.clean(out), indent=1, allow_nan=False)+'\n')
    write_csv(rows, taus)
    plot(rows, meth, summary, Tstar)
    print(json.dumps(ce.clean(dict(meta=meta, summary=summary)), indent=1))


def write_csv(rows, taus):
    import csv
    cols = ['sigma_K', 'P', 'direction', 'status', 'T_K', 'r', 'mean_acetogen', 'mean_methanogen', 'S_K_per_efold',
            'S0', 'G_loc', 'S_hyp', 'T_red_A', 'T_red_B', 'phi_red_A', 'phi_red_B', 'nodes', 'doublings',
            'support_min_K', 'support_max_K']
    tau_at = {(t['sigma_K'], t['P']): t for t in taus}
    cols += ['tau_c_status', 'tau_c_yr', 'tau_nodes']
    with STEM.with_suffix('.csv').open('w', newline='') as h:
        w = csv.DictWriter(h, cols, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            r = dict(r)
            t = tau_at.get((r['sigma_K'], r['P']))
            if t and r['direction'] != 'hom':
                r.update(tau_c_status=t.get('tau_c_status') or t.get('status'), tau_c_yr=t.get('tau_c_yr'), tau_nodes=t.get('nodes'))
            w.writerow(ce.clean(r))
    # tau points that fell between stored rows (none expected) are in the json


def plot(rows, meth, summary, Tstar):
    import matplotlib.pyplot as plt
    from terra_prisca.haze_world.paper_figures import style
    style.apply()
    fig, ax = plt.subplots(figsize=(style.DOUBLE, style.DOUBLE*.62))
    ax.axvspan(P_LO_HOM, P_HI_HOM, color=style.GRID, zorder=0, lw=0)
    ax.axhline(Tstar, color=style.MUTED, lw=.5, ls=':')
    ax.plot([m[0] for m in meth], [m[1] for m in meth], color=style.METHANOGEN, ls='--', lw=1, label='methanogens alone')
    shades = {1.: '#9ecae1', 3.: '#4292c6', 6.: '#2171b5', 8.: '#08306b'}
    for sg in (1., 3., 6., 8.):
        sub = [r for r in rows if r['sigma_K'] == sg and r['direction'] != 'hom']
        if not sub:
            continue
        P = np.array([r['P'] for r in sub]); T = np.array([r['T_K'] for r in sub])
        ax.plot(P, T, color=shades[sg], lw=1.2, label=f'$\\sigma$ = {sg:g} K')
        ax.plot(P, [r['T_red_B'] for r in sub], color=shades[sg], lw=.5, ls=(0, (1, 1.5)))
        ax.plot([P[0], P[-1]], [T[0], T[-1]], ls='none', marker='o', ms=2.5, color=shades[sg])
    hom = [r for r in rows if r['sigma_K'] == 0 and r['direction'] == 'hom']
    ax.plot([r['P'] for r in hom], [r['T_K'] for r in hom], color=style.INK, lw=1.4, label='$\\sigma$ = 0 (coexistence)')
    ax.plot([], [], color=style.INK_2, lw=.5, ls=(0, (1, 1.5)), label='reduced model B')
    ax.set_xlabel('hydrogen supply potential $P$')
    ax.set_ylabel('steady surface temperature $T^*$ (K)')
    ax.set_xlim(P_MIN, P_MAX)
    ax.legend(frameon=False, ncol=2, loc='upper right')
    ax.text(.5*(P_LO_HOM+P_HI_HOM), ax.get_ylim()[0]+.4, 'homogeneous coexistence range', ha='center', fontsize=6, color=style.INK_2)
    fig.tight_layout()
    fig.savefig(STEM.with_suffix('.png'), dpi=300)


if __name__ == '__main__':
    main()
