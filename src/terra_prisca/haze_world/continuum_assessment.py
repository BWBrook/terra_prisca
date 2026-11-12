"""Qualified PC1–PC6 assessment of weighted-habitat experiments."""

import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from . import continuum_experiments as runs

ROOT=Path(__file__).resolve().parents[3]


def read(path):
    with path.open() as stream:return list(csv.DictReader(stream))


def number(row,key):
    value=row.get(key)
    return None if value in (None,'') else float(value)


def identity(row):
    fields=('chemistry','fraction','sigma_k','dispersal_yr','nominal_potential','Sc','S0','G_loc','critical_lag_status','critical_lag_yr')
    return {k:row.get(k) for k in fields}


def stable_margin(row,threshold=30.):
    return row.get('critical_lag_status')=='not_detected_through_10000' or (
        row.get('critical_lag_status')=='finite_crossing' and float(row['critical_lag_yr'])>threshold)


def resolved(row):
    return row.get('status') in ('homogeneous','converged') and row.get('gain_status')=='defined' and row.get('frozen_fd_agrees')=='True'


def prepare_inputs(output):
    rows=read(output/'c1_resolved.csv')
    states=json.loads((output/'characteristic_states.json').read_text())
    for state in states:
        matches=[r for r in rows if r['chemistry']==state['chemistry'] and all(
            float(r[k])==float(state[k]) for k in ('fraction','sigma_k','dispersal_yr')) and float(r['nominal_potential'])==.3]
        if len(matches)!=1:raise ArithmeticError('Independent-check state has ambiguous metadata')
        for key in ('Sc','S0','G_loc'):state[key]=float(matches[0][key])
    (output/'characteristic_inputs.json').write_text(json.dumps(states,indent=2,allow_nan=False)+'\n')


def assess(c0,c1,audit):
    base=[r for r in c1 if float(r['nominal_potential'])==.3]
    good=[r for r in c0+c1 if resolved(r)]
    escapes=[r for r in good if abs(float(r['G_loc']))<.05 and stable_margin(r)]
    width=[];connectivity=[];low_d=[];gain_fail=[];gain_order=[];products=[]
    for chemistry in ('fixed','products'):
        for fraction in (0.,.5):
            for sigma in (1.,3.,6.):
                group=sorted([r for r in base if r['chemistry']==chemistry and float(r['fraction'])==fraction and float(r['sigma_k'])==sigma],
                             key=lambda r:float(r['dispersal_yr']))
                anchor=next((r for r in group if float(r['dispersal_yr'])==1e-4 and r['status']=='converged'),None)
                if anchor and number(anchor,'mixed_width_k') not in (None,0.):
                    for row in group:
                        if float(row['dispersal_yr'])>1e-2 or row['status']!='converged':continue
                        ratio=float(row['mixed_width_k'])/(float(anchor['mixed_width_k'])*float(row['dispersal_yr'])/1e-4)
                        width.append(dict(chemistry=chemistry,fraction=fraction,sigma_k=sigma,dispersal_yr=float(row['dispersal_yr']),
                                          width_k=float(row['mixed_width_k']),linear_ratio=ratio,within_factor_1_5=1/1.5<=ratio<=1.5))
                if chemistry=='fixed':
                    for low,high in zip(group[:-1],group[1:]):
                        a,b=number(low,'critical_lag_yr'),number(high,'critical_lag_yr')
                        decrease=(a is not None and b is not None and b<.98*a) or (
                            low.get('critical_lag_status')=='not_detected_through_10000' and high.get('critical_lag_status')=='finite_crossing')
                        connectivity.append(dict(fraction=fraction,sigma_k=sigma,low_d=float(low['dispersal_yr']),high_d=float(high['dispersal_yr']),
                                                 low_tau=a,high_tau=b,resolved_pair=low['status']==high['status']=='converged',decrease=decrease))
                    low_d += [identity(r) for r in group if r['status']=='converged' and float(r['dispersal_yr'])==1e-4 and r['critical_lag_status']=='not_detected_through_10000']
    fixed=[r for r in base if r['chemistry']=='fixed' and resolved(r)]
    gain_fail=[identity(r) for r in fixed if not .05<=float(r['G_loc'])<=1.]
    for f in (0.,.5):
        for d in (1e-4,1e-3,1e-2,1e-1):
            group=sorted([r for r in fixed if float(r['fraction'])==f and float(r['dispersal_yr'])==d],key=lambda r:float(r['sigma_k']))
            gain_order += [dict(fraction=f,dispersal_yr=d,low_sigma=float(a['sigma_k']),high_sigma=float(b['sigma_k']),
                                low_gain=float(a['G_loc']),high_gain=float(b['G_loc'])) for a,b in zip(group[:-1],group[1:]) if float(b['G_loc'])<float(a['G_loc'])-.001]
    for row in [r for r in c1 if r['chemistry']=='products' and resolved(r)]:
        choices=[r for r in c0 if r['chemistry']=='products' and float(r['fraction'])==float(row['fraction']) and
                 float(r['loss_h'])==.001 and float(r['nominal_potential'])==float(row['nominal_potential']) and resolved(r)]
        baseline=min(choices,key=lambda r:abs(float(r['ratio'])-float(row['ratio']))) if choices else None
        products.append(dict(identity(row),homogeneous_gain=float(baseline['G_loc']) if baseline else None,
            gain_at_least_homogeneous=float(row['G_loc'])>=float(baseline['G_loc'])-.001 if baseline else None,
            censored=row['critical_lag_status']=='not_detected_through_10000'))
    checks=audit.get('selected',[])
    return dict(counts=dict(C0=len(c0),C1=len(c1),C1_converged=sum(r['status']=='converged' for r in c1),
                           independent_checks=len(checks),independent_passes=sum(bool(r['passed']) for r in checks)),
        PC1=dict(status='supported_on_sampled_branches' if len(c1)==80 and all(r['status']=='converged' for r in c1) and len(checks)>=6 and all(r['passed'] for r in checks) else 'unresolved',
                 limitation='Finite branch seeds, collocation doubling and selected independent checks; not an interval certificate for all roots.'),
        PC2=dict(status='refuted' if any(not r['within_factor_1_5'] for r in width) else 'supported_on_assessed_widths' if len(width)==36 else 'unassessed',
                 failure_count=sum(not r['within_factor_1_5'] for r in width),comparisons=width),
        PC3=dict(status='refuted_in_declared_local_metric' if escapes else 'no_qualified_counterexample_found',counterexample_count=len(escapes),
                 homogeneous_counterexamples=sum(r['status']=='homogeneous' for r in escapes),spatial_counterexamples=sum(r['status']=='converged' for r in escapes),
                 counterexamples=[identity(r) for r in escapes],limit='Raw Sc remains nonzero. A small ratio is not exact pinning or a new physical response.'),
        PC4=dict(status='refuted' if low_d or any(r['decrease'] and r['resolved_pair'] for r in connectivity) else 'supported_on_assessed_pairs' if len(connectivity)==18 else 'unassessed',
                 monotonic_pairs=connectivity,low_d_finiteness_failures=low_d,
                 limit='Failure of one clause does not establish robustness at every connectivity.'),
        PC5=dict(status='refuted' if gain_fail or gain_order else 'supported_on_assessed_comparisons' if len(fixed)==24 else 'unassessed',
                 interval_failure_count=len(gain_fail),outside_gain_interval=gain_fail,decreasing_with_sigma=gain_order),
        PC6=dict(status='refuted' if any(not r['censored'] or r['gain_at_least_homogeneous'] is False for r in products) else 'supported_on_assessed_comparisons' if len(products)==40 else 'unassessed',
                 censored_count=sum(r['censored'] for r in products),gain_failure_count=sum(r['gain_at_least_homogeneous'] is False for r in products),comparisons=products))


def plots(output,c0,c1):
    fig,axes=plt.subplots(1,2,figsize=(10.3,4.4),layout='constrained')
    for chemistry,colour in (('fixed','#444444'),('products','#217d91')):
        rows=[r for r in c1 if r['chemistry']==chemistry and float(r['nominal_potential'])==.3 and resolved(r)]
        finite=[r for r in rows if r['critical_lag_status']=='finite_crossing']
        censored=[r for r in rows if r['critical_lag_status']=='not_detected_through_10000']
        axes[0].scatter([float(r['G_loc']) for r in finite],[float(r['critical_lag_yr']) for r in finite],c=colour,s=28,label=chemistry)
        axes[0].scatter([float(r['G_loc']) for r in censored],np.full(len(censored),1e4),c=colour,s=33,marker='^')
        ref=[r for r in rows if float(r['fraction'])==.5 and float(r['sigma_k'])==1.]
        ref.sort(key=lambda r:float(r['dispersal_yr']))
        axes[1].plot([float(r['dispersal_yr']) for r in ref],[float(r['Sc']) for r in ref],'o-',color=colour,label=chemistry)
    axes[0].axvline(.05,color='.5',ls='--',lw=.8);axes[0].axhline(30,color='.5',ls='--',lw=.8)
    axes[0].set(yscale='log',xlabel='Local gain G_loc',ylabel='First thermal delay margin (years)',title='Reference-input resolved continuum states')
    axes[0].text(.02,.02,'Triangles: no crossing through 10,000 years',transform=axes[0].transAxes,fontsize=8)
    axes[1].set(xscale='log',xlabel='Cell exchange d (per year)',ylabel='Sc: K per e-fold of input',title='Raw response: f=.5, spread ±1 K')
    for ax in axes:ax.grid(alpha=.15);ax.legend(fontsize=8)
    fig.savefig(output/'local_gain_connectivity.png',dpi=180);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=runs.OUTPUT)
    parser.add_argument('--prepare-inputs',action='store_true')
    parser.add_argument('--audit',type=Path,default=ROOT/'docs/audits/continuum-characteristic-main-map-2026-11-12.json')
    args=parser.parse_args();output=args.output
    if args.prepare_inputs:prepare_inputs(output);return
    c0,c1=read(output/'c0_local_gain.csv'),read(output/'c1_resolved.csv')
    audit=json.loads(args.audit.read_text())
    result=assess(c0,c1,audit);plots(output,c0,c1)
    result['input_sha256']={name:digest for name,digest in ((name,runs.digest(output/name)) for name in ('c0_local_gain.csv','c1_resolved.csv','characteristic_inputs.json'))}
    result['audit_sha256']=runs.digest(args.audit)
    result['assessor_sha256']=runs.digest(Path(__file__))
    result['figure_sha256']=runs.digest(output/'local_gain_connectivity.png')
    (output/'prediction_assessment.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v['status'] for k,v in result.items() if isinstance(v,dict) and 'status'in v},indent=2))


if __name__=='__main__':main()
